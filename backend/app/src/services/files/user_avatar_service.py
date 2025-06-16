# backend/app/src/services/files/user_avatar_service.py
"""
Сервіс для управління аватарами користувачів.

Обробляє логіку зв'язування користувачів з файлами-аватарами,
встановлення активного аватара та отримання інформації про аватари.
"""
from typing import List, Optional, Dict, Any # Відновлено Dict, Any
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select # Оновлено імпорт
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from backend.app.src.services.base import BaseService
from backend.app.src.models.files.avatar import UserAvatar
from backend.app.src.models.files.file import FileRecord
from backend.app.src.repositories.files.user_avatar_repository import UserAvatarRepository # Імпорт репозиторію
from backend.app.src.models.auth.user import User

from backend.app.src.schemas.files.avatar import UserAvatarResponse
# UserAvatarCreate, UserAvatarUpdate не імпортуються, оскільки дані для них формуються в сервісі
from backend.app.src.config import logger  # Використання спільного логера з конфігу
from backend.app.src.config import settings


class UserAvatarService(BaseService): # type: ignore видалено
    """
    Сервіс для управління аватарами користувачів.
    Обробляє зв'язування користувачів з їхніми зображеннями-аватарами (FileRecords)
    та управління тим, який аватар є активним на даний момент.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        self.user_avatar_repo = UserAvatarRepository() # Ініціалізація репозиторію
        logger.info("UserAvatarService ініціалізовано.")

    async def _get_user_avatar_link_by_id_orm(self, user_avatar_id: int) -> Optional[UserAvatar]: # user_avatar_id: UUID -> int
        """Внутрішній метод для отримання ORM моделі UserAvatar з усіма зв'язками."""
        stmt = select(UserAvatar).options(
            selectinload(UserAvatar.user).options(selectinload(User.user_type)),
            selectinload(UserAvatar.file).options(
                selectinload(FileRecord.uploader_user).options(selectinload(User.user_type)),
                selectinload(FileRecord.group)
            )
        ).where(UserAvatar.id == user_avatar_id)
        try:
            result = await self.db_session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Помилка при отриманні UserAvatar link ID {user_avatar_id}: {e}", exc_info=settings.DEBUG)
            return None

    async def set_user_avatar(
            self,
            user_id: int, # UUID -> int
            file_id: int, # UUID -> int (FileRecord.id is int)
            set_by_user_id: Optional[int] = None # Optional[UUID] -> Optional[int]
    ) -> UserAvatarResponse: # type: ignore видалено
        """
        Встановлює або змінює активний аватар для користувача.
        Деактивує попередні активні аватари.

        :param user_id: ID користувача (int), для якого встановлюється аватар.
        :param file_id: ID запису файлу (FileRecord) (int), який буде аватаром.
        :param set_by_user_id: ID користувача (int), що виконує операцію (за замовчуванням = user_id).
        :return: Pydantic схема UserAvatarResponse для активного зв'язку аватара.
        :raises ValueError: Якщо користувача, файл не знайдено, або файл не є зображенням. # i18n
        """
        actor_user_id = set_by_user_id if set_by_user_id is not None else user_id
        logger.debug(
            f"Користувач ID '{actor_user_id}' намагається встановити аватар для користувача ID '{user_id}' використовуючи файл ID '{file_id}'.")

        user = await self.db_session.get(User, user_id) # Перевірка залишається в сервісі
        if not user:
            raise ValueError(f"Користувача з ID '{user_id}' не знайдено.")

        file_record = await self.db_session.get(FileRecord, file_id) # Перевірка залишається в сервісі
        if not file_record:
            raise ValueError(f"Запис файлу з ID '{file_id}' не знайдено.")

        if not file_record.mime_type or not file_record.mime_type.startswith("image/"):
            logger.warning(
                f"Файл ID '{file_id}' (MIME: {file_record.mime_type}) не є зображенням. Неможливо встановити як аватар.")
            raise ValueError(f"Файл '{file_record.file_name}' не є дійсним зображенням для аватара.")

        try:
            # Делегуємо основну логіку репозиторію
            # updated_by_user_id для deactivate_all_for_user та potentially для create/update в set_active_avatar
            # наразі не передається, оскільки модель UserAvatar не має цих полів.
            # Якщо б вони були, то actor_user_id передавався б у repo.set_active_avatar.
            avatar_link_db = await self.user_avatar_repo.set_active_avatar(
                session=self.db_session,
                user_id=user_id,
                file_record_id=file_id
                # updated_by_user_id=actor_user_id # Якщо б поле було в моделі
            )

            if not avatar_link_db: # Якщо репозиторій повернув None (помилка всередині репо)
                 logger.error(f"Не вдалося встановити аватар для користувача ID {user_id} через помилку в репозиторії.")
                 raise RuntimeError("Помилка встановлення аватара на рівні репозиторію.")

            await self.commit() # Коміт операцій, виконаних репозиторієм

            # Отримуємо оновлений/створений запис з усіма зв'язками для відповіді
            # _get_user_avatar_link_by_id_orm використовує прямий запит для selectinload
            refreshed_avatar_link_db = await self._get_user_avatar_link_by_id_orm(avatar_link_db.id)
            if not refreshed_avatar_link_db:
                logger.error(f"Не вдалося отримати зв'язок аватара ID {avatar_link_db.id} після коміту.")
                raise RuntimeError("Помилка встановлення аватара: не вдалося отримати запис після збереження.")

        except IntegrityError as e: # Ця помилка може прийти з repo.set_active_avatar
            await self.rollback()
            logger.error(f"Помилка цілісності при встановленні аватара для ID '{user_id}': {e}",
                         exc_info=settings.DEBUG)
            raise ValueError(f"Не вдалося встановити аватар через конфлікт даних: {e}")
        except Exception as e: # Інші можливі винятки
            await self.rollback()
            logger.error(f"Неочікувана помилка при встановленні аватара для ID '{user_id}': {e}", exc_info=settings.DEBUG)
            raise

        logger.info(
            f"Аватар (Файл ID: '{file_id}') успішно встановлено як активний для користувача ID '{user_id}'. ID Зв'язку: {refreshed_avatar_link_db.id}")
        return UserAvatarResponse.model_validate(refreshed_avatar_link_db)

    async def get_active_user_avatar(self, user_id: int) -> Optional[UserAvatarResponse]: # user_id: UUID -> int
        """Отримує активний аватар для вказаного користувача."""
        logger.debug(f"Спроба отримання активного аватара для користувача ID: {user_id}")

        # Використовуємо репозиторій, але потім _get_user_avatar_link_by_id_orm для завантаження зв'язків
        # Це можна оптимізувати, якщо репозиторій буде підтримувати завантаження зв'язків.
        active_avatar_link_orm = await self.user_avatar_repo.get_active_avatar_for_user(session=self.db_session, user_id=user_id)

        if active_avatar_link_orm:
            # Перезавантажуємо з потрібними зв'язками через _get_user_avatar_link_by_id_orm
            # Це не дуже ефективно, краще б репозиторій одразу завантажував все необхідне.
            # Наразі залишаємо так для збереження логіки завантаження зв'язків.
            # В ідеалі: `get_active_avatar_for_user` в репозиторії має параметр `load_relations=True`.
            detailed_avatar_link_orm = await self._get_user_avatar_link_by_id_orm(active_avatar_link_orm.id)

            if detailed_avatar_link_orm and detailed_avatar_link_orm.file:
                 logger.info(
                    f"Активний аватар знайдено для користувача ID '{user_id}' (Файл ID: {detailed_avatar_link_orm.file_id}).")
                 return UserAvatarResponse.model_validate(detailed_avatar_link_orm)
            elif detailed_avatar_link_orm and not detailed_avatar_link_orm.file:
                 logger.error(
                    f"Активний зв'язок аватара ID '{detailed_avatar_link_orm.id}' для користувача '{user_id}' не має пов'язаного запису файлу. Неузгодженість даних.")
                 return None
            # Якщо detailed_avatar_link_orm is None, хоча active_avatar_link_orm був знайдений - це дивно.
            logger.warning(f"Не вдалося перезавантажити активний аватар ID {active_avatar_link_orm.id} зі зв'язками.")

        logger.info(f"Активний аватар для користувача ID '{user_id}' не знайдено.")
        return None

    async def list_user_avatars(self, user_id: int, skip: int = 0, limit: int = 10) -> List[UserAvatarResponse]: # user_id: UUID -> int
        """Перелічує всі аватари (активні та неактивні) для вказаного користувача."""
        logger.debug(f"Перелік всіх аватарів для користувача ID: {user_id}, пропустити={skip}, ліміт={limit}")

        # Використовуємо репозиторій
        # Знову ж таки, завантаження зв'язків - це питання.
        # list_by_user_id в репозиторії не має selectinload за замовчуванням.
        # Для збереження поведінки, залишимо поки прямий запит.
        stmt = select(UserAvatar).where(UserAvatar.user_id == user_id) \
            .options(
                selectinload(UserAvatar.user).selectinload(User.user_type),
                selectinload(UserAvatar.file).options(
                    selectinload(FileRecord.uploader_user).selectinload(User.user_type),
                    # selectinload(FileRecord.group) # FileRecord не має прямого зв'язку group
                )
            ) \
            .order_by(UserAvatar.is_active.desc(), UserAvatar.created_at.desc()) \
            .offset(skip).limit(limit)

        avatars_db_list = (await self.db_session.execute(stmt)).scalars().all()

        response_list = [UserAvatarResponse.model_validate(ua) for ua in avatars_db_list]
        logger.info(f"Отримано {len(response_list)} записів аватарів для користувача ID '{user_id}'.")
        return response_list

    async def deactivate_user_avatar(self, user_avatar_id: int, current_user_id: int) -> bool: # ID змінено на int
        """
        Деактивує конкретний зв'язок аватара користувача.
        Користувач може деактивувати тільки власний аватар, якщо не має адмінських прав.
        """
        logger.debug(f"Користувач ID '{current_user_id}' намагається деактивувати зв'язок аватара ID: {user_avatar_id}")

        user_avatar_db = await self.user_avatar_repo.get(session=self.db_session, id=user_avatar_id)
        if not user_avatar_db:
            logger.warning(f"Зв'язок аватара UserAvatar ID '{user_avatar_id}' не знайдено.")
            return False

        # TODO: [Authorization] Розширити логіку авторизації: адміністратор (перевіряючи права `current_user_id`) повинен мати можливість деактивувати чужий аватар.
        if user_avatar_db.user_id != current_user_id: # Перевірка авторизації залишається в сервісі
            logger.error(
                f"Користувач ID '{current_user_id}' не авторизований для деактивації зв'язку аватара ID '{user_avatar_id}', що належить користувачу ID '{user_avatar_db.user_id}'.")
            raise PermissionError("Ви не маєте дозволу на деактивацію цього аватара.")

        if not user_avatar_db.is_active:
            logger.info(f"Зв'язок аватара UserAvatar ID '{user_avatar_id}' вже неактивний.")
            return True

        # Оновлюємо поле напряму і зберігаємо через репозиторій update
        # Або репозиторій може мати спеціальний метод deactivate(id)
        # Наразі UserAvatarUpdateSchema порожня, тому repo.update не підходить без її зміни.
        # Залишаємо пряме оновлення поля та коміт через сервіс.
        user_avatar_db.is_active = False
        # updated_at оновлюється автоматично через TimestampedMixin

        self.db_session.add(user_avatar_db) # Додаємо змінений об'єкт до сесії
        await self.commit() # Комітимо зміни

        logger.info(
            f"Зв'язок аватара UserAvatar ID '{user_avatar_id}' для користувача ID '{user_avatar_db.user_id}' деактивовано.")
        return True


logger.debug(f"{UserAvatarService.__name__} (сервіс аватарів користувачів) успішно визначено.")
