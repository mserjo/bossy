# backend/app/src/services/groups/settings.py
# import logging # Замінено на централізований логер
from typing import List, Optional, Dict, Any # Dict, List не використовуються, можна прибрати
from uuid import UUID
from datetime import datetime, timezone # Додано для updated_at

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
# from sqlalchemy.orm import selectinload # Якщо налаштування мають зв'язані об'єкти для завантаження
from sqlalchemy.exc import IntegrityError

# Повні шляхи імпорту
from backend.app.src.services.base import BaseService
from backend.app.src.models.groups.settings import GroupSetting # Модель SQLAlchemy GroupSetting
from backend.app.src.models.groups.group import Group # Для зв'язку налаштування з групою
from backend.app.src.models.auth.user import User # Для поля updated_by_user_id / created_by_user_id
from backend.app.src.schemas.groups.settings import ( # Схеми Pydantic GroupSetting
    GroupSettingCreate, # Може не використовуватися напряму, якщо є upsert
    GroupSettingUpdate,
    GroupSettingResponse
)
from backend.app.src.config.logging import logger # Централізований логер
from backend.app.src.config import settings as global_settings # Для доступу до конфігурацій (наприклад, DEBUG)

class GroupSettingService(BaseService):
    """
    Сервіс для управління налаштуваннями, специфічними для окремих груп.
    Кожна група може мати власний набір конфігурацій, таких як назва валюти бонусів,
    ліміти боргу, політики перевірки завдань тощо.
    Передбачається, що для кожної групи існує не більше одного запису налаштувань.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        logger.info("GroupSettingService ініціалізовано.")

    async def get_settings_for_group(self, group_id: UUID) -> Optional[GroupSettingResponse]:
        """
        Отримує налаштування для конкретної групи.
        Зазвичай група має один запис налаштувань.

        :param group_id: ID групи.
        :return: Pydantic схема GroupSettingResponse або None, якщо налаштування не знайдено.
        """
        logger.debug(f"Спроба отримання налаштувань для групи ID: {group_id}")

        stmt = select(GroupSetting).where(GroupSetting.group_id == group_id)
        # TODO: Додати selectinload, якщо GroupSetting має зв'язані сутності, які потрібно відображати.
        # Наприклад: .options(selectinload(GroupSetting.default_role_for_member))

        settings_db = (await self.db_session.execute(stmt)).scalar_one_or_none()

        if settings_db:
            logger.info(f"Налаштування для групи ID '{group_id}' знайдено.")
            return GroupSettingResponse.model_validate(settings_db) # Pydantic v2
        else:
            logger.info(f"Запис налаштувань для групи ID '{group_id}' не знайдено.")
            # TODO: Розглянути політику створення налаштувань за замовчуванням, якщо їх не існує.
            #  Можна викликати create_or_update_group_settings з порожнім GroupSettingUpdate,
            #  щоб створити запис з системними значеннями за замовчуванням, визначеними в моделі GroupSetting.
            return None

    async def create_or_update_group_settings(
        self,
        group_id: UUID,
        settings_data: GroupSettingUpdate, # Використовуємо GroupSettingUpdate, оскільки дозволяє часткові оновлення
        current_user_id: Optional[UUID] = None # Опціонально: для журналу аудиту
    ) -> GroupSettingResponse:
        """
        Створює налаштування групи, якщо вони не існують, або оновлює їх, якщо існують.
        Це операція типу "upsert", специфічна для запису налаштувань групи.

        :param group_id: ID групи, чиї налаштування конфігуруються.
        :param settings_data: Дані для налаштувань.
        :param current_user_id: ID користувача, що виконує операцію (для аудиту).
        :return: Pydantic схема GroupSettingResponse створених або оновлених налаштувань.
        :raises ValueError: Якщо вказана група не існує. # i18n
        """
        log_actor = f"користувачем ID '{current_user_id}'" if current_user_id else "системою"
        logger.debug(f"Спроба створення/оновлення налаштувань для групи ID: {group_id} {log_actor}.")

        group_db = await self.db_session.get(Group, group_id)
        if not group_db:
            msg = f"Групу з ID '{group_id}' не знайдено." # i18n
            logger.error(msg + " Неможливо створити/оновити налаштування.")
            raise ValueError(msg)

        settings_db = (await self.db_session.execute(
            select(GroupSetting).where(GroupSetting.group_id == group_id)
        )).scalar_one_or_none()

        update_data_dict = settings_data.model_dump(exclude_unset=True) # Pydantic v2
        current_time = datetime.now(timezone.utc)

        if settings_db: # Оновлення існуючих налаштувань
            logger.info(f"Знайдено існуючі налаштування для групи ID '{group_id}'. Оновлення.")
            for field, value in update_data_dict.items():
                if hasattr(settings_db, field):
                    setattr(settings_db, field, value)
                else:
                    logger.warning(f"Поле '{field}' не знайдено в моделі GroupSetting під час оновлення для групи ID '{group_id}'.")

            if hasattr(settings_db, 'updated_by_user_id') and current_user_id:
                settings_db.updated_by_user_id = current_user_id
            # `updated_at` має оновлюватися автоматично моделлю, або так:
            if hasattr(settings_db, 'updated_at'):
                settings_db.updated_at = current_time
        else: # Створення нового запису налаштувань
            logger.info(f"Існуючі налаштування для групи ID '{group_id}' не знайдено. Створення нового запису.")
            # TODO: Застосувати системні значення за замовчуванням для полів, не наданих в settings_data,
            #  якщо це визначено в `technical_task.txt` або логіці моделі GroupSetting.
            create_data = update_data_dict.copy()
            create_data['group_id'] = group_id # Обов'язково встановлюємо group_id

            if hasattr(GroupSetting, 'created_by_user_id') and current_user_id:
                 create_data['created_by_user_id'] = current_user_id
            if hasattr(GroupSetting, 'updated_by_user_id') and current_user_id:
                 create_data['updated_by_user_id'] = current_user_id
            # `created_at` та `updated_at` (при створенні) мають встановлюватися моделлю

            settings_db = GroupSetting(**create_data)
            self.db_session.add(settings_db)

        try:
            await self.commit()
            await self.db_session.refresh(settings_db) # Оновлюємо для отримання будь-яких значень БД за замовчуванням
        except IntegrityError as e: # Наприклад, якщо group_id не унікальний (хоча логіка вище має це запобігти)
            await self.rollback()
            logger.error(f"Помилка цілісності при збереженні налаштувань для групи ID '{group_id}': {e}", exc_info=global_settings.DEBUG)
            # i18n
            raise ValueError(f"Не вдалося зберегти налаштування для групи ID '{group_id}' через конфлікт даних.")

        logger.info(f"Налаштування для групи ID '{group_id}' успішно збережено.")
        return GroupSettingResponse.model_validate(settings_db) # Pydantic v2

    async def update_group_currency(self, group_id: UUID, currency_name: str, current_user_id: Optional[UUID] = None) -> GroupSettingResponse:
        """Оновлює тільки назву валюти для налаштувань групи."""
        log_actor = f"користувачем ID '{current_user_id}'" if current_user_id else "системою"
        logger.debug(f"Оновлення назви валюти для групи ID {group_id} на '{currency_name}' {log_actor}.")
        # Використовуємо GroupSettingUpdate для часткового оновлення
        update_payload = GroupSettingUpdate(currency_name=currency_name)
        return await self.create_or_update_group_settings(group_id, update_payload, current_user_id)

    async def get_group_setting_value(self, group_id: UUID, setting_key: str, default: Optional[Any] = None) -> Optional[Any]:
        """
        Допоміжний метод для отримання значення конкретного налаштування для групи.

        :param group_id: ID групи.
        :param setting_key: Назва поля налаштування (наприклад, 'currency_name', 'max_debt_amount').
        :param default: Значення за замовчуванням, якщо налаштування або ключ не знайдено.
        :return: Значення налаштування або значення за замовчуванням.
        """
        logger.debug(f"Отримання значення налаштування за ключем '{setting_key}' в групі ID '{group_id}'.")
        group_settings_response = await self.get_settings_for_group(group_id)

        if group_settings_response:
            # Перевіряємо, чи Pydantic модель має такий атрибут
            if hasattr(group_settings_response, setting_key):
                value = getattr(group_settings_response, setting_key)
                logger.info(f"Знайдено значення '{value}' для ключа '{setting_key}' в групі ID '{group_id}'.")
                return value
            else:
                logger.warning(f"Ключ налаштування '{setting_key}' не знайдено в налаштуваннях групи ID '{group_id}'. Повернення значення за замовчуванням.")
        else: # Налаштування для групи взагалі не знайдено
            logger.info(f"Запис налаштувань для групи ID '{group_id}' не знайдено. Повернення значення за замовчуванням для ключа '{setting_key}'.")
        return default

    # TODO: Розглянути метод для видалення налаштувань групи, якщо це дозволено бізнес-логікою.
    # Зазвичай налаштування існують, поки існує група, або скидаються до значень за замовчуванням.
    # async def delete_group_settings(self, group_id: UUID) -> bool: ...

logger.debug(f"{GroupSettingService.__name__} (сервіс налаштувань груп) успішно визначено.")
