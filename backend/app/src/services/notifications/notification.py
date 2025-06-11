# backend/app/src/services/notifications/notification.py
# import logging # Замінено на централізований логер
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, noload
from sqlalchemy.exc import IntegrityError

# Повні шляхи імпорту
from backend.app.src.services.base import BaseService
from backend.app.src.models.notifications.notification import Notification # Модель SQLAlchemy
from backend.app.src.models.auth.user import User # Для user_id
from backend.app.src.models.notifications.template import NotificationTemplate # Для використання шаблонів

from backend.app.src.schemas.notifications.notification import ( # Схеми Pydantic
    NotificationCreateInternal, # Для створення на рівні сервісу
    NotificationUpdate, # Для змін статусу, наприклад, позначити як прочитане
    NotificationResponse
)
from backend.app.src.services.notifications.template import NotificationTemplateService # Для отримання/рендерингу шаблонів
# from backend.app.src.services.notifications.delivery import NotificationDeliveryService # Для запуску доставки (буде викликано тут)
from backend.app.src.config.logging import logger # Централізований логер
from backend.app.src.config import settings # Для доступу до конфігурацій (наприклад, DEBUG)


class NotificationService(BaseService):
    """
    Сервіс для управління сповіщеннями користувачів у застосунку.
    Обробляє створення (потенційно з шаблонів), отримання та оновлення статусу
    (наприклад, позначення як прочитане/непрочитане).
    Фактичне надсилання сповіщень (email, SMS, push) зазвичай делегується
    NotificationDeliveryService.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        self.template_service = NotificationTemplateService(db_session)
        # self.delivery_service = NotificationDeliveryService(db_session) # Ініціалізуємо, якщо потрібно тут
        logger.info("NotificationService ініціалізовано.")

    async def get_notification_by_id(self, notification_id: UUID, user_id: Optional[UUID] = None) -> Optional[NotificationResponse]:
        """
        Отримує сповіщення за його ID.
        Якщо надано `user_id`, перевіряє, чи належить сповіщення цьому користувачеві.

        :param notification_id: ID сповіщення.
        :param user_id: Опціональний ID користувача для перевірки власності.
        :return: Pydantic схема NotificationResponse або None.
        """
        log_ctx_parts = [f"сповіщення ID '{notification_id}'"]
        if user_id: log_ctx_parts.append(f"для користувача ID '{user_id}'")
        log_ctx = " ".join(log_ctx_parts)
        logger.debug(f"Спроба отримання {log_ctx}.")

        stmt = select(Notification).options(
            selectinload(Notification.user).options(selectinload(User.user_type)) # Завантажуємо користувача та його тип
            # TODO: Додати selectinload(Notification.template), якщо є зв'язок і він потрібен у відповіді.
        ).where(Notification.id == notification_id)

        if user_id: # Якщо вказано user_id, фільтруємо за ним для безпеки
            stmt = stmt.where(Notification.user_id == user_id)

        notification_db = (await self.db_session.execute(stmt)).scalar_one_or_none()

        if notification_db:
            logger.info(f"Сповіщення з ID '{notification_id}' знайдено.")
            return NotificationResponse.model_validate(notification_db) # Pydantic v2

        logger.info(f"Сповіщення з ID '{notification_id}' не знайдено (або не належить користувачеві).")
        return None

    async def create_notification(
        self,
        notification_data: NotificationCreateInternal, # Вхідні дані для створення
        trigger_delivery: bool = True # За замовчуванням намагаємося доставити
    ) -> NotificationResponse:
        """
        Створює новий запис сповіщення в БД.
        Опціонально ініціює процес доставки через NotificationDeliveryService.

        :param notification_data: Дані для створення сповіщення.
        :param trigger_delivery: Якщо True, ініціює доставку сповіщення.
        :return: Pydantic схема створеного NotificationResponse.
        :raises ValueError: Якщо користувача не знайдено або конфлікт даних. # i18n
        """
        logger.debug(f"Спроба створення сповіщення для користувача ID '{notification_data.user_id}', назва: '{notification_data.title}'.")

        # Перевірка існування користувача
        if not await self.db_session.get(User, notification_data.user_id):
            msg = f"Користувача з ID '{notification_data.user_id}' не знайдено." # i18n
            logger.error(msg + " Неможливо створити сповіщення.")
            raise ValueError(msg)

        # Перевірка існування шаблону, якщо template_id надано
        if notification_data.template_id and not await self.db_session.get(NotificationTemplate, notification_data.template_id):
            msg = f"Шаблон сповіщення з ID '{notification_data.template_id}' не знайдено." # i18n
            logger.error(msg)
            raise ValueError(msg)

        # `created_at` встановлюється автоматично моделлю
        new_notification_db = Notification(**notification_data.model_dump()) # Pydantic v2

        self.db_session.add(new_notification_db)
        try:
            await self.commit()
            # Оновлюємо для завантаження зв'язків (наприклад, user)
            await self.db_session.refresh(new_notification_db, attribute_names=['user'])
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Помилка цілісності '{notification_data.user_id}': {e}", exc_info=settings.DEBUG)
            # i18n
            raise ValueError(f"Не вдалося створити сповіщення через конфлікт даних: {e}")

        logger.info(f"Сповіщення ID '{new_notification_db.id}' успішно створено для користувача ID '{new_notification_db.user_id}'.")

        if trigger_delivery:
            logger.info(f"Ініціювання доставки для сповіщення ID '{new_notification_db.id}'.")
            # TODO: Реалізувати виклик NotificationDeliveryService.
            # from backend.app.src.services.notifications.delivery import NotificationDeliveryService
            # delivery_service = NotificationDeliveryService(self.db_session)
            # await delivery_service.queue_notification_for_delivery(new_notification_db.id)
            logger.warning(f"[ЗАГЛУШКА] Ініціювання доставки для сповіщення ID '{new_notification_db.id}'. Потребує реалізації.")

        return NotificationResponse.model_validate(new_notification_db) # Pydantic v2

    async def create_notification_from_template(
        self,
        template_name: str, # Унікальне ім'я шаблону
        user_id: UUID,
        context_data: Dict[str, Any], # Дані для заповнення шаблону
        notification_type_override: Optional[str] = None, # Перевизначити тип сповіщення з шаблону
        payload_override: Optional[Dict[str, Any]] = None, # Перевизначити/додати payload
        trigger_delivery: bool = True
    ) -> NotificationResponse: # Не Optional, бо помилки рендерингу/пошуку кидають винятки
        """
        Створює сповіщення на основі існуючого шаблону.

        :param template_name: Унікальне ім'я шаблону.
        :param user_id: ID користувача-одержувача.
        :param context_data: Дані для рендерингу шаблону.
        :param notification_type_override: Опціонально перевизначає тип сповіщення, вказаний у шаблоні.
        :param payload_override: Опціонально перевизначає/доповнює дані payload з шаблону.
        :param trigger_delivery: Якщо True, ініціює доставку сповіщення.
        :return: Pydantic схема створеного NotificationResponse.
        :raises ValueError: Якщо шаблон не знайдено або помилка рендерингу. # i18n
        """
        logger.debug(f"Створення сповіщення для користувача ID '{user_id}' з шаблону '{template_name}'.")

        template = await self.template_service.get_template_by_name(template_name)
        if not template:
            msg = f"Шаблон сповіщення '{template_name}' не знайдено." # i18n
            logger.error(msg + " Неможливо створити сповіщення.")
            raise ValueError(msg)

        try:
            # render_template тепер може кидати ValueError або KeyError
            rendered_subject, rendered_body = self.template_service.render_template(template, context_data)
        except (ValueError, KeyError) as e: # Обробка помилок рендерингу, які ми кидаємо
            logger.error(f"Помилка рендерингу шаблону '{template_name}' для користувача '{user_id}': {e}", exc_info=settings.DEBUG)
            raise ValueError(f"Не вдалося відрендерити шаблон сповіщення '{template_name}': {e}") # i18n
        except Exception as e: # Інші непередбачені помилки рендерингу
            logger.error(f"Неочікувана помилка рендерингу '{template_name}': {e}", exc_info=settings.DEBUG)
            raise ValueError(f"Неочікувана помилка рендерингу шаблону '{template_name}'.") # i18n


        final_payload = template.default_vars.copy() if template.default_vars else {}
        if payload_override:
            final_payload.update(payload_override)

        final_notification_type = notification_type_override or template.template_type

        create_data = NotificationCreateInternal(
            user_id=user_id,
            title=rendered_subject or template.name, # Якщо тема не відрендерена, використовуємо ім'я шаблону
            message=rendered_body,
            notification_type=final_notification_type,
            status="unread", # Статус за замовчуванням для нових сповіщень
            payload=final_payload if final_payload else None,
            template_id=template.id # Зберігаємо ID шаблону, якщо модель це підтримує
        )

        return await self.create_notification(create_data, trigger_delivery=trigger_delivery)


    async def mark_notifications_as_status(
        self, notification_ids: List[UUID], user_id: UUID, status: str
    ) -> int:
        """
        Встановлює вказаний статус для списку сповіщень, що належать користувачеві.
        Оновлює `read_at`, якщо статус встановлено на 'read'.

        :param notification_ids: Список ID сповіщень для оновлення.
        :param user_id: ID користувача, якому належать сповіщення.
        :param status: Новий статус (наприклад, 'read', 'archived').
        :return: Кількість успішно оновлених сповіщень.
        """
        # TODO: Перевірити, чи `status` є валідним значенням з enum/дозволених.
        logger.info(f"Користувач ID '{user_id}' намагається позначити {len(notification_ids)} сповіщень як '{status}'.")
        if not notification_ids: return 0

        # Вибираємо тільки ті сповіщення, які належать користувачеві і ще не мають цільового статусу
        stmt = select(Notification).where(
            Notification.id.in_(notification_ids),
            Notification.user_id == user_id,
            Notification.status != status
        )
        notifications_to_update_db = (await self.db_session.execute(stmt)).scalars().all()

        if not notifications_to_update_db:
            logger.info(f"Не знайдено сповіщень для користувача ID '{user_id}', що відповідають ID {notification_ids} та потребують оновлення статусу на '{status}'.")
            return 0

        updated_count = 0
        current_time = datetime.now(timezone.utc)
        for notification_db in notifications_to_update_db:
            notification_db.status = status
            if status == "read" and hasattr(notification_db, 'read_at'): # Перевірка наявності поля
                notification_db.read_at = current_time
            # `updated_at` оновлюється автоматично моделлю
            self.db_session.add(notification_db)
            updated_count += 1

        if updated_count > 0:
            await self.commit()
            logger.info(f"Успішно позначено {updated_count} сповіщень як '{status}' для користувача ID '{user_id}'.")
        return updated_count

    async def get_user_notifications(
        self, user_id: UUID, status: Optional[str] = None,
        notification_type: Optional[str] = None,
        skip: int = 0, limit: int = 20
    ) -> List[NotificationResponse]:
        """Перелічує сповіщення для користувача з фільтрами та пагінацією."""
        logger.debug(f"Перелік сповіщень для користувача ID: {user_id}, статус: {status}, тип: {notification_type}, пропустити={skip}, ліміт={limit}")

        stmt = select(Notification).options(
            selectinload(Notification.user).options(noload("*")) # Завантажуємо тільки ID користувача, якщо UserResponse не потрібен повністю
            # TODO: selectinload(Notification.template), якщо потрібно
        ).where(Notification.user_id == user_id)

        if status:
            stmt = stmt.where(Notification.status == status)
        if notification_type:
            stmt = stmt.where(Notification.notification_type == notification_type)

        stmt = stmt.order_by(Notification.created_at.desc()).offset(skip).limit(limit)
        notifications_db = (await self.db_session.execute(stmt)).scalars().all()

        response_list = [NotificationResponse.model_validate(n) for n in notifications_db] # Pydantic v2
        logger.info(f"Отримано {len(response_list)} сповіщень для користувача ID '{user_id}'.")
        return response_list

    async def delete_notification(self, notification_id: UUID, user_id: UUID) -> bool:
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
            logger.error(f"Користувач ID '{user_id}' не авторизований для видалення сповіщення ID '{notification_id}' (власник: {notification_db.user_id}).")
            # Можна кинути PermissionError або просто повернути False
            return False

        await self.db_session.delete(notification_db)
        await self.commit()
        logger.info(f"Сповіщення ID '{notification_id}' успішно видалено користувачем ID '{user_id}'.")
        return True

logger.debug(f"{NotificationService.__name__} (сервіс сповіщень) успішно визначено.")
