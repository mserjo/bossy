# backend/app/src/services/files/user_avatar_service.py
# import logging # Замінено на централізований логер
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload  # , joinedload # joinedload не використовується
from sqlalchemy.exc import IntegrityError

from backend.app.src.services.base import BaseService  # Повний шлях
from backend.app.src.models.files.avatar import UserAvatar  # Модель SQLAlchemy UserAvatar
from backend.app.src.models.files.file import FileRecord  # Для зв'язку з фактичним файлом
from backend.app.src.models.auth.user import User  # Для контексту користувача

from backend.app.src.schemas.files.avatar import (  # Схеми Pydantic
    # UserAvatarCreate, # Не використовується прямо як тип параметра, але концептуально для file_id
    # UserAvatarUpdate, # Не використовується прямо як тип параметра для зміни is_active
    UserAvatarResponse
)
# from backend.app.src.schemas.files.file import FileRecordResponse # Для вкладених деталей файлу у відповіді (вже є в UserAvatarResponse)
from backend.app.src.config.logging import logger  # Централізований логер
from backend.app.src.config import settings  # Для доступу до конфігурацій (наприклад, DEBUG)


class UserAvatarService(BaseService):
    """
    Сервіс для управління аватарами користувачів.
    Обробляє зв'язування користувачів з їхніми зображеннями-аватарами (FileRecords)
    та управління тим, який аватар є активним на даний момент.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        logger.info("UserAvatarService ініціалізовано.")

    async def _get_user_avatar_link_by_id_orm(self, user_avatar_id: UUID) -> Optional[UserAvatar]:
        """Внутрішній метод для отримання ORM моделі UserAvatar з усіма зв'язками."""
        stmt = select(UserAvatar).options(
            selectinload(UserAvatar.user).options(selectinload(User.user_type)),
            selectinload(UserAvatar.file).options(
                selectinload(FileRecord.uploader_user).options(selectinload(User.user_type)),
                selectinload(FileRecord.group)  # Якщо FileRecord має зв'язок з групою
            )
        ).where(UserAvatar.id == user_avatar_id)
        return (await self.db_session.execute(stmt)).scalar_one_or_none()

    async def set_user_avatar(
            self,
            user_id: UUID,
            file_id: UUID,
            set_by_user_id: Optional[UUID] = None  # ID користувача, який виконує дію (для аудиту)
    ) -> UserAvatarResponse:
        """
        Встановлює або змінює активний аватар для користувача.
        Деактивує попередні активні аватари.

        :param user_id: ID користувача, для якого встановлюється аватар.
        :param file_id: ID запису файлу (FileRecord), який буде аватаром.
        :param set_by_user_id: ID користувача, що виконує операцію (за замовчуванням = user_id).
        :return: Pydantic схема UserAvatarResponse для активного зв'язку аватара.
        :raises ValueError: Якщо користувача, файл не знайдено, або файл не є зображенням. # i18n
        """
        actor_user_id = set_by_user_id if set_by_user_id is not None else user_id
        logger.debug(
            f"Користувач ID '{actor_user_id}' намагається встановити аватар для користувача ID '{user_id}' використовуючи файл ID '{file_id}'.")

        user = await self.db_session.get(User, user_id)
        if not user:
            # i18n
            raise ValueError(f"Користувача з ID '{user_id}' не знайдено.")

        file_record = await self.db_session.get(FileRecord, file_id)
        if not file_record:
            # i18n
            raise ValueError(f"Запис файлу з ID '{file_id}' не знайдено.")

        if not file_record.mime_type or not file_record.mime_type.startswith("image/"):
            logger.warning(
                f"Файл ID '{file_id}' (MIME: {file_record.mime_type}) не є зображенням. Неможливо встановити як аватар.")
            # i18n
            raise ValueError(f"Файл '{file_record.file_name}' не є дійсним зображенням для аватара.")

        # Атомарна деактивація існуючих активних аватарів для цього користувача
        update_values: Dict[str, Any] = {"is_active": False, "updated_at": datetime.now(timezone.utc)}
        if hasattr(UserAvatar, 'updated_by_user_id'):  # Перевірка наявності поля перед додаванням
            update_values["updated_by_user_id"] = actor_user_id

        stmt_deactivate = UserAvatar.__table__.update().where(
            UserAvatar.user_id == user_id,
            UserAvatar.is_active == True
        ).values(**update_values)
        await self.db_session.execute(stmt_deactivate)

        # Перевірка, чи існує вже зв'язок цього користувача з цим файлом
        stmt_existing_link = select(UserAvatar).where(
            UserAvatar.user_id == user_id,
            UserAvatar.file_id == file_id
        )
        avatar_link_db = (await self.db_session.execute(stmt_existing_link)).scalar_one_or_none()

        current_time = datetime.now(timezone.utc)
        if avatar_link_db:  # Якщо зв'язок існує, активуємо його
            logger.info(
                f"Повторна активація існуючого зв'язку аватара між користувачем ID '{user_id}' та файлом ID '{file_id}'.")
            avatar_link_db.is_active = True
            avatar_link_db.updated_at = current_time
            if hasattr(UserAvatar, 'updated_by_user_id'):
                avatar_link_db.updated_by_user_id = actor_user_id
        else:  # Створюємо новий зв'язок
            logger.info(f"Створення нового зв'язку аватара для користувача ID '{user_id}' з файлом ID '{file_id}'.")
            create_data: Dict[str, Any] = {
                "user_id": user_id,
                "file_id": file_id,
                "is_active": True,
                # created_at та updated_at встановлюються моделлю або БД за замовчуванням
            }
            if hasattr(UserAvatar, 'created_by_user_id'):
                create_data['created_by_user_id'] = actor_user_id
            if hasattr(UserAvatar, 'updated_by_user_id'):
                create_data['updated_by_user_id'] = actor_user_id  # Також встановлюємо при створенні

            avatar_link_db = UserAvatar(**create_data)
            self.db_session.add(avatar_link_db)

        try:
            await self.commit()  # Зберігаємо деактивацію старих та активацію/створення нового зв'язку
            # Отримуємо оновлений/створений запис з усіма зв'язками для відповіді
            refreshed_avatar_link_db = await self._get_user_avatar_link_by_id_orm(avatar_link_db.id)
            if not refreshed_avatar_link_db:  # Малоймовірно
                logger.error(f"Не вдалося отримати зв'язок аватара ID {avatar_link_db.id} після коміту.")
                # i18n
                raise RuntimeError("Помилка встановлення аватара: не вдалося отримати запис після збереження.")

        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Помилка цілісності при встановленні аватара для ID '{user_id}': {e}",
                         exc_info=settings.DEBUG)
            # i18n
            raise ValueError(f"Не вдалося встановити аватар через конфлікт даних: {e}")

        logger.info(
            f"Аватар (Файл ID: '{file_id}') успішно встановлено як активний для користувача ID '{user_id}'. ID Зв'язку: {refreshed_avatar_link_db.id}")
        return UserAvatarResponse.model_validate(refreshed_avatar_link_db)  # Pydantic v2

    async def get_active_user_avatar(self, user_id: UUID) -> Optional[UserAvatarResponse]:
        """Отримує активний аватар для вказаного користувача."""
        logger.debug(f"Спроба отримання активного аватара для користувача ID: {user_id}")

        stmt = select(UserAvatar).options(
            selectinload(UserAvatar.user).options(selectinload(User.user_type)),  # Завантажуємо тип користувача
            selectinload(UserAvatar.file).options(
                selectinload(FileRecord.uploader_user).options(selectinload(User.user_type)),  # Тип завантажувача
                selectinload(FileRecord.group)  # Група файлу, якщо є
            )
        ).where(
            UserAvatar.user_id == user_id,
            UserAvatar.is_active == True
        )
        active_avatar_db = (await self.db_session.execute(stmt)).scalar_one_or_none()

        if active_avatar_db:
            if not active_avatar_db.file:  # Перевірка цілісності даних
                logger.error(
                    f"Активний зв'язок аватара ID '{active_avatar_db.id}' для користувача '{user_id}' не має пов'язаного запису файлу. Неузгодженість даних.")
                return None  # Або кинути виняток про пошкоджені дані
            logger.info(
                f"Активний аватар знайдено для користувача ID '{user_id}' (Файл ID: {active_avatar_db.file_id}).")
            return UserAvatarResponse.model_validate(active_avatar_db)  # Pydantic v2

        logger.info(f"Активний аватар для користувача ID '{user_id}' не знайдено.")
        return None

    async def list_user_avatars(self, user_id: UUID, skip: int = 0, limit: int = 10) -> List[UserAvatarResponse]:
        """Перелічує всі аватари (активні та неактивні) для вказаного користувача."""
        logger.debug(f"Перелік всіх аватарів для користувача ID: {user_id}, пропустити={skip}, ліміт={limit}")

        stmt = select(UserAvatar).options(
            selectinload(UserAvatar.user).options(selectinload(User.user_type)),
            selectinload(UserAvatar.file).options(
                selectinload(FileRecord.uploader_user).options(selectinload(User.user_type)),
                selectinload(FileRecord.group)
            )
        ).where(UserAvatar.user_id == user_id) \
            .order_by(UserAvatar.is_active.desc(), UserAvatar.created_at.desc()) \
            .offset(skip).limit(limit)

        avatars_db = (await self.db_session.execute(stmt)).scalars().all()

        response_list = [UserAvatarResponse.model_validate(ua) for ua in avatars_db]  # Pydantic v2
        logger.info(f"Отримано {len(response_list)} записів аватарів для користувача ID '{user_id}'.")
        return response_list

    async def deactivate_user_avatar(self, user_avatar_id: UUID, current_user_id: UUID) -> bool:
        """
        Деактивує конкретний зв'язок аватара користувача.
        Користувач може деактивувати тільки власний аватар, якщо не має адмінських прав.
        """
        # TODO: Розширити логіку авторизації: адміністратор може деактивувати чужий аватар.
        #  Наразі користувач може деактивувати лише власний аватар через user_avatar_id.
        #  Потрібно перевіряти, що user_avatar_id належить current_user_id.
        logger.debug(f"Користувач ID '{current_user_id}' намагається деактивувати зв'язок аватара ID: {user_avatar_id}")

        user_avatar_db = await self.db_session.get(UserAvatar, user_avatar_id)
        if not user_avatar_db:
            logger.warning(f"Зв'язок аватара UserAvatar ID '{user_avatar_id}' не знайдено.")
            return False

        # Перевірка авторизації: користувач може деактивувати тільки свій зв'язок аватара
        if user_avatar_db.user_id != current_user_id:
            # TODO: Додати перевірку, чи є `current_user_id` адміністратором/суперкористувачем,
            #  який може мати право деактивувати чужі аватари.
            logger.error(
                f"Користувач ID '{current_user_id}' не авторизований для деактивації зв'язку аватара ID '{user_avatar_id}', що належить користувачу ID '{user_avatar_db.user_id}'.")
            # i18n
            raise PermissionError("Ви не маєте дозволу на деактивацію цього аватара.")

        if not user_avatar_db.is_active:
            logger.info(f"Зв'язок аватара UserAvatar ID '{user_avatar_id}' вже неактивний.")
            return True  # Вже в бажаному стані

        user_avatar_db.is_active = False
        user_avatar_db.updated_at = datetime.now(timezone.utc)
        if hasattr(user_avatar_db, 'updated_by_user_id'):
            user_avatar_db.updated_by_user_id = current_user_id

        self.db_session.add(user_avatar_db)
        await self.commit()
        logger.info(
            f"Зв'язок аватара UserAvatar ID '{user_avatar_id}' для користувача ID '{user_avatar_db.user_id}' деактивовано.")
        return True


logger.debug(f"{UserAvatarService.__name__} (сервіс аватарів користувачів) успішно визначено.")
