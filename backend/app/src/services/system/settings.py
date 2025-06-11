# backend/app/src/services/system/settings.py
# import logging # Замінено на централізований логер
import json  # Для десеріалізації JSON значень
from typing import List, Optional, Any, Dict
from uuid import UUID
from datetime import datetime, timezone  # Додано timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
# from sqlalchemy.orm import selectinload # Якщо є зв'язки для завантаження
from sqlalchemy.exc import IntegrityError  # Для обробки помилок унікальності

# Повні шляхи імпорту
from backend.app.src.services.base import BaseService
from backend.app.src.models.system.settings import SystemSetting  # Модель SQLAlchemy
from backend.app.src.schemas.system.settings import (  # Схеми Pydantic
    SystemSettingCreate,
    SystemSettingUpdate,
    SystemSettingResponse,
)
from backend.app.src.config.logging import logger  # Централізований логер
from backend.app.src.config import settings as global_settings  # Для доступу до конфігурацій (наприклад, DEBUG)


class SystemSettingService(BaseService):
    """
    Сервіс для управління загальносистемними налаштуваннями.
    Дозволяє отримувати, створювати та оновлювати налаштування, що впливають на поведінку застосунку.
    Кожне налаштування ідентифікується унікальним ключем (`key`) і має значення (`value`),
    тип значення (`value_type`) та опис.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        logger.info("SystemSettingService ініціалізовано.")

    async def get_setting_by_key(self, key: str) -> Optional[SystemSettingResponse]:
        """
        Отримує конкретне системне налаштування за його ключем.

        :param key: Унікальний ключ системного налаштування.
        :return: Pydantic схема SystemSettingResponse, якщо знайдено, інакше None.
        """
        logger.debug(f"Спроба отримання системного налаштування за ключем: {key}")
        stmt = select(SystemSetting).where(SystemSetting.key == key)
        setting_db = (await self.db_session.execute(stmt)).scalar_one_or_none()

        if setting_db:
            logger.info(f"Системне налаштування з ключем '{key}' знайдено.")
            return SystemSettingResponse.model_validate(setting_db)  # Pydantic v2

        logger.info(f"Системне налаштування з ключем '{key}' не знайдено.")
        return None

    async def get_all_settings(self, skip: int = 0, limit: int = 100) -> List[SystemSettingResponse]:
        """
        Отримує список всіх системних налаштувань з пагінацією.

        :param skip: Кількість налаштувань для пропуску.
        :param limit: Максимальна кількість налаштувань для повернення.
        :return: Список Pydantic схем SystemSettingResponse.
        """
        logger.debug(f"Спроба отримання всіх системних налаштувань: skip={skip}, limit={limit}")
        stmt = select(SystemSetting).order_by(SystemSetting.key).offset(skip).limit(limit)
        settings_db = (await self.db_session.execute(stmt)).scalars().all()

        response_list = [SystemSettingResponse.model_validate(s) for s in settings_db]  # Pydantic v2
        logger.info(f"Отримано {len(response_list)} системних налаштувань.")
        return response_list

    async def create_setting(self, setting_data: SystemSettingCreate,
                             creator_id: Optional[UUID] = None) -> SystemSettingResponse:
        """
        Створює нове системне налаштування.
        Переконується, що налаштування з таким ключем ще не існує.

        :param setting_data: Дані для нового системного налаштування.
        :param creator_id: ID користувача, що створює налаштування (для аудиту).
        :return: Pydantic схема створеного SystemSettingResponse.
        :raises ValueError: Якщо налаштування з таким ключем вже існує. # i18n
        """
        logger.debug(f"Спроба створення нового системного налаштування з ключем: {setting_data.key}")
        existing_setting = await self.get_setting_by_key(setting_data.key)
        if existing_setting:
            msg = f"Системне налаштування з ключем '{setting_data.key}' вже існує."  # i18n
            logger.warning(msg + " Створення скасовано.")
            raise ValueError(msg)

        create_dict = setting_data.model_dump()  # Pydantic v2
        # TODO: Додати created_by_user_id, updated_by_user_id, якщо вони є в моделі SystemSetting
        # if creator_id and hasattr(SystemSetting, 'created_by_user_id'):
        #     create_dict['created_by_user_id'] = creator_id
        # if creator_id and hasattr(SystemSetting, 'updated_by_user_id'):
        #     create_dict['updated_by_user_id'] = creator_id

        new_setting_db = SystemSetting(**create_dict)
        # `created_at`, `updated_at` мають встановлюватися автоматично моделлю

        self.db_session.add(new_setting_db)
        try:
            await self.commit()
            await self.db_session.refresh(new_setting_db)
        except IntegrityError as e:  # На випадок паралельного створення
            await self.rollback()
            logger.error(f"Помилка цілісності при створенні налаштування '{setting_data.key}': {e}",
                         exc_info=global_settings.DEBUG)
            # i18n
            raise ValueError(f"Не вдалося створити налаштування '{setting_data.key}' через конфлікт даних.")

        logger.info(f"Системне налаштування '{new_setting_db.key}' ID: {new_setting_db.id} успішно створено.")
        return SystemSettingResponse.model_validate(new_setting_db)  # Pydantic v2

    async def update_setting(self, setting_id: UUID, setting_update_data: SystemSettingUpdate,
                             updater_id: Optional[UUID] = None) -> Optional[SystemSettingResponse]:
        """
        Оновлює існуюче системне налаштування за його ID.

        :param setting_id: ID системного налаштування для оновлення.
        :param setting_update_data: Дані для оновлення.
        :param updater_id: ID користувача, що оновлює налаштування (для аудиту).
        :return: Pydantic схема оновленого SystemSettingResponse, або None, якщо не знайдено.
        :raises ValueError: Якщо відбувається спроба оновити ключ на той, що вже існує для іншого налаштування. # i18n
        """
        logger.debug(f"Спроба оновлення системного налаштування з ID: {setting_id}")

        setting_db = await self.db_session.get(SystemSetting, setting_id)
        if not setting_db:
            logger.warning(f"Системне налаштування з ID '{setting_id}' не знайдено для оновлення.")
            return None

        update_data = setting_update_data.model_dump(exclude_unset=True)  # Pydantic v2

        if 'key' in update_data and update_data['key'] != setting_db.key:
            existing_key_setting = await self.get_setting_by_key(update_data['key'])
            if existing_key_setting and existing_key_setting.id != setting_id:
                msg = f"Інше системне налаштування з ключем '{update_data['key']}' вже існує."  # i18n
                logger.warning(
                    f"Неможливо оновити ключ для ID '{setting_id}' на '{update_data['key']}', оскільки він використовується ID '{existing_key_setting.id}'. {msg}")
                raise ValueError(msg)

        for field, value in update_data.items():
            setattr(setting_db, field, value)

        # TODO: Додати updated_by_user_id, якщо є в моделі
        # if updater_id and hasattr(setting_db, 'updated_by_user_id'):
        #    setting_db.updated_by_user_id = updater_id
        if hasattr(setting_db, 'updated_at'):  # Модель має автоматично оновлювати це поле
            setting_db.updated_at = datetime.now(timezone.utc)

        self.db_session.add(setting_db)
        try:
            await self.commit()
            await self.db_session.refresh(setting_db)
        except IntegrityError as e:  # На випадок паралельного оновлення, що спричиняє конфлікт
            await self.rollback()
            logger.error(f"Помилка цілісності при оновленні налаштування ID '{setting_id}': {e}",
                         exc_info=global_settings.DEBUG)
            # i18n
            raise ValueError(f"Не вдалося оновити налаштування '{setting_db.key}' через конфлікт даних.")

        logger.info(f"Системне налаштування з ID '{setting_id}' (ключ: {setting_db.key}) успішно оновлено.")
        return SystemSettingResponse.model_validate(setting_db)  # Pydantic v2

    async def delete_setting(self, setting_id: UUID) -> bool:
        """
        Видаляє системне налаштування за його ID.

        :param setting_id: ID системного налаштування для видалення.
        :return: True, якщо видалення успішне, False - якщо налаштування не знайдено.
        """
        logger.debug(f"Спроба видалення системного налаштування з ID: {setting_id}")
        setting_db = await self.db_session.get(SystemSetting, setting_id)

        if not setting_db:
            logger.warning(f"Системне налаштування з ID '{setting_id}' не знайдено для видалення.")
            return False

        # TODO: Додати перевірку `is_editable_by_admin` або інші бізнес-правила перед видаленням, якщо потрібно.
        # Наприклад, деякі системні налаштування можуть бути незмінними.

        await self.db_session.delete(setting_db)
        await self.commit()
        logger.info(f"Системне налаштування з ID '{setting_id}' (ключ: {setting_db.key}) успішно видалено.")
        return True

    def _deserialize_setting_value(self, value_str: str, value_type: str) -> Any:
        """Допоміжний метод для десеріалізації значення налаштування на основі його типу."""
        logger.debug(f"Десеріалізація значення '{value_str}' як тип '{value_type}'")
        try:
            if value_type == 'string':
                return value_str
            elif value_type == 'integer':
                return int(value_str)
            elif value_type == 'float':  # Або Decimal, якщо використовується
                return float(value_str)
            elif value_type == 'boolean':
                return value_str.lower() in ('true', '1', 'yes', 'on')
            elif value_type == 'json':
                return json.loads(value_str)
            # TODO: Додати інші типи, такі як 'date', 'datetime', 'list_str', 'list_int'
            else:
                logger.warning(f"Невідомий тип значення '{value_type}' для десеріалізації. Повернення як рядок.")
                return value_str
        except Exception as e:
            logger.error(f"Помилка десеріалізації значення '{value_str}' як '{value_type}': {e}",
                         exc_info=global_settings.DEBUG)
            return None  # Або кинути виняток, або повернути як є

    async def get_setting_value(self, key: str, default: Optional[Any] = None) -> Optional[Any]:
        """
        Допоміжний метод для отримання десеріалізованого значення налаштування за ключем.

        :param key: Ключ налаштування.
        :param default: Значення за замовчуванням, якщо налаштування не знайдено або помилка десеріалізації.
        :return: Десеріалізоване значення налаштування або значення за замовчуванням.
        """
        setting_response = await self.get_setting_by_key(key)
        if setting_response and setting_response.value is not None and setting_response.value_type is not None:
            # `value` в SystemSettingResponse вже має бути правильного типу завдяки Pydantic моделі,
            # якщо модель SystemSetting.value є JSONB/JSON і SystemSettingResponse.value має тип Any/Dict/List/etc.
            # Якщо SystemSetting.value є просто TEXT, то потрібна десеріалізація тут.
            # Припускаємо, що SystemSettingResponse.value вже є Python-типом.
            # Якщо ні, то треба десеріалізувати:
            # return self._deserialize_setting_value(str(setting_response.value), setting_response.value_type)
            # Для Pydantic v2, якщо value є Json[Any] в моделі, то воно вже буде десеріалізоване.
            logger.debug(f"Значення для ключа '{key}': {setting_response.value} (тип: {type(setting_response.value)})")
            return setting_response.value

        logger.info(
            f"Системне налаштування '{key}' не знайдено або значення/тип не встановлено. Повернення значення за замовчуванням: {default}")
        return default


logger.debug(f"{SystemSettingService.__name__} (сервіс системних налаштувань) успішно визначено.")
