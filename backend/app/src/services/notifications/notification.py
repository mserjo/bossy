# backend/app/src/services/notifications/notification.py
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select # sqlalchemy.future тепер select
from sqlalchemy.orm import selectinload, noload
from sqlalchemy.exc import IntegrityError

from backend.app.src.services.base import BaseService
from backend.app.src.models.notifications.notification import Notification
from backend.app.src.repositories.notifications.notification_repository import NotificationRepository # Імпорт репозиторію
from backend.app.src.models.auth.user import User
from backend.app.src.models.notifications.template import NotificationTemplate

from backend.app.src.schemas.notifications.notification import (
    NotificationCreateInternal,
    NotificationUpdate,
    NotificationResponse
)
from backend.app.src.services.notifications.template import NotificationTemplateService
from backend.app.src.services.notifications.delivery import NotificationDeliveryService # Розкоментовано
from backend.app.src.services.cache.base_cache import BaseCacheService # Потрібно для NotificationTemplateService
from backend.app.src.core.dicts import NotificationType as NotificationTypeEnum # Імпорт Enum
# Припускаємо, що NotificationStatusType буде визначено або імпортовано, поки що використовуємо рядки.

from backend.app.src.config import settings
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)


class NotificationService(BaseService):
    """
    Сервіс для управління сповіщеннями користувачів у застосунку.
    Обробляє створення (потенційно з шаблонів), отримання та оновлення статусу
    (наприклад, позначення як прочитане/непрочитане).
    Фактичне надсилання сповіщень (email, SMS, push) зазвичай делегується
    NotificationDeliveryService.
    """

    def __init__(self, db_session: AsyncSession, cache_service: BaseCacheService):
        super().__init__(db_session)
        self.notification_repo = NotificationRepository() # Ініціалізація репозиторію
        # NotificationTemplateService тепер вимагає cache_service
        self.template_service = NotificationTemplateService(db_session, cache_service)
        self.delivery_service = NotificationDeliveryService(db_session) # Розкоментовано та ініціалізовано
        logger.info("NotificationService ініціалізовано.")

    async def get_notification_by_id(self, notification_id: int, user_id: Optional[int] = None) -> Optional[ # Змінено UUID на int
        NotificationResponse]:
        """
        Отримує сповіщення за його ID.
        Якщо надано `user_id`, перевіряє, чи належить сповіщення цьому користувачеві.
        """
        log_ctx_parts = [f"сповіщення ID '{notification_id}'"]
        if user_id: log_ctx_parts.append(f"для користувача ID '{user_id}'")
        log_ctx = " ".join(log_ctx_parts)
        logger.debug(f"Спроба отримання {log_ctx}.")

        # Залишаємо прямий запит для гнучкого selectinload
        stmt = select(Notification).options(
            selectinload(Notification.user).options(selectinload(User.user_type)),
            selectinload(Notification.template) # Завантажуємо шаблон, якщо він є
        ).where(Notification.id == notification_id)

        if user_id:
            stmt = stmt.where(Notification.user_id == user_id)

        notification_db = (await self.db_session.execute(stmt)).scalar_one_or_none()

        if notification_db:
            logger.info(f"Сповіщення з ID '{notification_id}' знайдено.")
            return NotificationResponse.model_validate(notification_db)

        logger.info(f"Сповіщення з ID '{notification_id}' не знайдено (або не належить користувачеві).")
        return None

    async def create_notification(
            self,
            notification_data: NotificationCreateInternal,
            trigger_delivery: bool = True
    ) -> NotificationResponse:
        """
        Створює новий запис сповіщення в БД.
        Опціонально ініціює процес доставки через NotificationDeliveryService.
        """
        logger.debug(
            f"Спроба створення сповіщення для користувача ID '{notification_data.user_id}', назва: '{notification_data.title}'.")

        if not await self.db_session.get(User, notification_data.user_id): # Перевірка залишається в сервісі
            # msg = f"Користувача з ID '{notification_data.user_id}' не знайдено." # Original log
            logger.error(f"Користувача з ID '{notification_data.user_id}' не знайдено. Неможливо створити сповіщення.")
            raise ValueError(_("user.errors.not_found_by_id", id=notification_data.user_id))

        if notification_data.template_id and \
           not await self.db_session.get(NotificationTemplate, notification_data.template_id): # Перевірка залишається в сервісі
            # msg = f"Шаблон сповіщення з ID '{notification_data.template_id}' не знайдено." # Original log
            logger.error(f"Шаблон сповіщення з ID '{notification_data.template_id}' не знайдено.")
            raise ValueError(_("notification.errors.template.not_found_by_id", template_id=notification_data.template_id))

        # Створюємо NotificationCreateSchema з NotificationCreateInternal
        # NotificationCreateSchema - це те, що очікує repo.create.
        # notification_data вже є NotificationCreateInternal, який є Pydantic моделлю.
        # BaseRepository.create очікує CreateSchemaType, що є BaseModel.
        # Тому можна передати notification_data напряму, якщо він сумісний.
        # Припускаємо, що NotificationCreateInternal сумісний з NotificationCreateSchema.
        # Якщо ні, то тут потрібне явне перетворення.

        try:
            new_notification_db = await self.notification_repo.create(
                session=self.db_session, obj_in=notification_data # Передаємо NotificationCreateInternal
            )
            await self.commit()
            # Перезавантажуємо зі зв'язками для відповіді
            refreshed_notification = await self.get_notification_by_id(new_notification_db.id) # Викликаємо get_notification_by_id для завантаження зв'язків
            if not refreshed_notification: # Малоймовірно
                raise RuntimeError(_("notification.errors.critical_create_failed_relations"))

        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Помилка цілісності для user ID '{notification_data.user_id}': {e}", exc_info=settings.DEBUG)
            raise ValueError(_("notification.errors.create_conflict", error_message=str(e)))
        except Exception as e: # Обробка інших можливих помилок
            await self.rollback()
            logger.error(f"Неочікувана помилка при створенні сповіщення для user ID '{notification_data.user_id}': {e}", exc_info=settings.DEBUG)
            raise


        logger.info(
            f"Сповіщення ID '{refreshed_notification.id}' успішно створено для користувача ID '{refreshed_notification.user_id}'.")

        if trigger_delivery and self.delivery_service: # Перевіряємо, чи delivery_service ініціалізовано
            logger.info(f"Ініціювання доставки для сповіщення ID '{refreshed_notification.id}'.")
            await self.delivery_service.queue_notification_for_delivery(
                notification_id=refreshed_notification.id, # type: ignore
                user_id=refreshed_notification.user_id # type: ignore
            )
            # logger.warning(
            #     f"[ЗАГЛУШКА] Ініціювання доставки для сповіщення ID '{new_notification_db.id}'. Потребує реалізації.")

        return refreshed_notification

    async def create_notification_from_template(
            self,
            template_name: str,
            user_id: int, # Змінено UUID на int
            context_data: Dict[str, Any],
            notification_type_override: Optional[NotificationTypeEnum] = None, # Використовуємо Enum
            payload_override: Optional[Dict[str, Any]] = None,
            trigger_delivery: bool = True
    ) -> NotificationResponse:
        """
        Створює сповіщення на основі існуючого шаблону.
        """
        logger.debug(f"Створення сповіщення для користувача ID '{user_id}' з шаблону '{template_name}'.")

        # template_service.get_template_by_name вже використовує репозиторій (якщо реалізовано)
        template = await self.template_service.get_template_by_name(template_name)
        if not template:
            # msg = f"Шаблон сповіщення '{template_name}' не знайдено." # Original log
            logger.error(f"Шаблон сповіщення '{template_name}' не знайдено. Неможливо створити сповіщення.")
            raise ValueError(_("notification.errors.template.not_found_by_name", template_name=template_name))

        try:
            rendered_subject, rendered_body = self.template_service.render_template(template, context_data)
        except (ValueError, KeyError) as e: # These are often programming errors or bad context data
            logger.error(f"Помилка рендерингу шаблону '{template_name}' для користувача '{user_id}': {e}",
                         exc_info=settings.DEBUG)
            # Use specific error key for known render issues (like missing context keys)
            raise ValueError(_("notification.errors.template.render_failed", template_name=template_name, error_message=str(e)))
        except Exception as e: # Catch-all for other render exceptions
            logger.error(f"Неочікувана помилка рендерингу '{template_name}': {e}", exc_info=settings.DEBUG)
            raise ValueError(_("notification.errors.template.render_unexpected_error", template_name=template_name))

        final_payload = template.default_vars.copy() if template.default_vars else {}
        if payload_override:
            final_payload.update(payload_override)

        # template.template_type є NotificationChannelType, а NotificationCreateInternal.notification_type - NotificationTypeEnum
        # Це різні Enum. Потрібно узгодити. Припускаємо, що template.template_type - це канал, а не тип сповіщення.
        # Тип сповіщення (NotificationTypeEnum) має визначатися на основі події, а не каналу.
        # Тут потрібна логіка для визначення NotificationTypeEnum.
        # Поки що, якщо override не надано, використовуємо GENERAL.
        final_notification_type_enum = notification_type_override if notification_type_override else NotificationTypeEnum.GENERAL

        create_data = NotificationCreateInternal(
            user_id=user_id,
            title=rendered_subject or template.name,
            message=rendered_body,
            notification_type=final_notification_type_enum, # Використовуємо Enum
            status="unread", # TODO: Використовувати NotificationStatusType.UNREAD Enum
            payload=final_payload if final_payload else None,
            template_id=template.id
        )

        return await self.create_notification(create_data, trigger_delivery=trigger_delivery)

    async def mark_notifications_as_status(
            self, notification_ids: List[int], user_id: int, status: str # Змінено UUID на int
    ) -> int:
        """
        Встановлює вказаний статус для списку сповіщень, що належать користувачеві.
        Оновлює `read_at`, якщо статус встановлено на 'read'.
        """
        # TODO: Використовувати NotificationStatusType Enum для параметра status
        logger.info(f"Користувач ID '{user_id}' намагається позначити {len(notification_ids)} сповіщень як '{status}'.")
        if not notification_ids: return 0

        # Використовуємо repo.update_many або цикл з repo.get + repo.update
        # Для простоти, поки що цикл з repo.get + оновлення ORM об'єкта
        updated_count = 0
        current_time = datetime.now(timezone.utc)

        # Отримуємо об'єкти через репозиторій по одному (менш ефективно для багатьох ID)
        # Або отримуємо список і фільтруємо в пам'яті (якщо їх не надто багато)
        # Або розширюємо репозиторій методом update_many_by_ids_and_user
        notifications_to_update_db: List[Notification] = []
        for nid in notification_ids:
            n_db = await self.notification_repo.get(session=self.db_session, id=nid)
            if n_db and n_db.user_id == user_id and n_db.status != status:
                 notifications_to_update_db.append(n_db)

        if not notifications_to_update_db:
            logger.info(
                f"Не знайдено сповіщень для користувача ID '{user_id}', що відповідають ID {notification_ids} та потребують оновлення статусу на '{status}'.")
            return 0

        for notification_db in notifications_to_update_db:
            notification_db.status = status # Тут status має бути Enum або значення, що відповідає моделі
            if status == "read" and hasattr(notification_db, 'read_at'): # TODO: "read" -> NotificationStatusType.READ.value
                notification_db.read_at = current_time
            self.db_session.add(notification_db) # Додаємо до сесії для відстеження
            updated_count += 1

        if updated_count > 0:
            try:
                await self.commit()
                logger.info(f"Успішно позначено {updated_count} сповіщень як '{status}' для користувача ID '{user_id}'.")
            except Exception as e:
                await self.rollback()
                logger.error(f"Помилка коміту при оновленні статусу сповіщень для user ID {user_id}: {e}", exc_info=True)
                return 0 # Повертаємо 0, якщо коміт не вдався
        return updated_count

    async def get_user_notifications(
            self, user_id: int, status: Optional[str] = None, # Змінено UUID на int, TODO: status -> Enum
            notification_type: Optional[NotificationTypeEnum] = None, # Використовуємо Enum
            skip: int = 0, limit: int = 20
    ) -> List[NotificationResponse]:
        """Перелічує сповіщення для користувача з фільтрами та пагінацією."""
        logger.debug(
            f"Перелік сповіщень для користувача ID: {user_id}, статус: {status}, тип: {notification_type.value if notification_type else None}, пропустити={skip}, ліміт={limit}")

        # Використовуємо метод репозиторію
        # is_read фільтр в репозиторії очікує bool. Потрібно конвертувати status="read"/'unread' в bool.
        is_read_filter: Optional[bool] = None
        if status == "read": is_read_filter = True
        elif status == "unread": is_read_filter = False
        # TODO: Якщо status може мати інші значення (напр. "archived"), це не обробляється get_notifications_for_user

        notifications_db_list, _ = await self.notification_repo.get_notifications_for_user(
            session=self.db_session,
            user_id=user_id,
            is_read=is_read_filter,
            notification_type=notification_type, # Передаємо Enum
            skip=skip,
            limit=limit
        )

        # TODO: Переконатися, що репозиторій завантажує зв'язки, якщо вони потрібні для NotificationResponse
        # Наразі get_notifications_for_user не має selectinload.
        # Для збереження поведінки (якщо NotificationResponse їх потребує), може знадобитися перезавантаження.
        # Або, якщо model_validate може впоратися з лінивим завантаженням.
        response_list = [NotificationResponse.model_validate(n) for n in notifications_db_list]
        logger.info(f"Отримано {len(response_list)} сповіщень для користувача ID '{user_id}'.")
        return response_list

    async def delete_notification(self, notification_id: int, user_id: int) -> bool: # Змінено UUID на int
        """
        Видаляє сповіщення користувача.
        Припускає жорстке видалення.
        """
        # TODO: Уточнити політику видалення (жорстке/м'яке) з technical_task.txt.
        logger.debug(f"Користувач ID '{user_id}' намагається видалити сповіщення ID '{notification_id}'.")

        # Отримуємо сповіщення, щоб перевірити власника перед видаленням
        notification_db = await self.db_session.get(Notification, notification_id)
        if not notification_db:
            logger.warning(f"Сповіщення ID '{notification_id}' не знайдено для видалення.")
            return False

        if notification_db.user_id != user_id:
            # i18n
            logger.error(
                f"Користувач ID '{user_id}' не авторизований для видалення сповіщення ID '{notification_id}' (власник: {notification_db.user_id}).")
            # Можна кинути PermissionError або просто повернути False
            return False

        await self.db_session.delete(notification_db)
        await self.commit()
        logger.info(f"Сповіщення ID '{notification_id}' успішно видалено користувачем ID '{user_id}'.")
        return True


logger.debug(f"{NotificationService.__name__} (сервіс сповіщень) успішно визначено.")
