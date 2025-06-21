# backend/app/src/services/system/settings.py
import json
from typing import List, Optional, Any, Dict
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select # sqlalchemy.future тепер select
from sqlalchemy.exc import IntegrityError

from backend.app.src.services.base import BaseService
from backend.app.src.models.system.settings import SystemSetting
from backend.app.src.repositories.system.settings_repository import SystemSettingRepository # Імпорт репозиторію
from backend.app.src.schemas.system.settings import (
    SystemSettingCreateSchema,
    SystemSettingUpdateSchema,
    SystemSettingResponseSchema,
)
from backend.app.src.core.dicts import SettingValueType
from backend.app.src.config import settings as global_settings
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)


class SystemSettingService(BaseService):
    """
    Сервіс для управління загальносистемними налаштуваннями.
    Дозволяє отримувати, створювати та оновлювати налаштування, що впливають на поведінку застосунку.
    Кожне налаштування ідентифікується унікальним ключем (`key`) і має значення (`value`),
    тип значення (`value_type`) та опис.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        self.setting_repo = SystemSettingRepository() # Ініціалізація репозиторію
        logger.info("SystemSettingService ініціалізовано.")

    async def get_setting_by_key(self, key: str) -> Optional[SystemSettingResponseSchema]:
        """
        Отримує конкретне системне налаштування за його ключем.
        """
        logger.debug(f"Спроба отримання системного налаштування за ключем: {key}")
        setting_db = await self.setting_repo.get_by_key(session=self.db_session, key=key)

        if setting_db:
            logger.info(f"Системне налаштування з ключем '{key}' знайдено.")
            return SystemSettingResponseSchema.model_validate(setting_db)

        logger.info(f"Системне налаштування з ключем '{key}' не знайдено.")
        return None

    async def get_all_settings(self, skip: int = 0, limit: int = 100) -> List[SystemSettingResponseSchema]:
        """
        Отримує список всіх системних налаштувань з пагінацією.
        """
        logger.debug(f"Спроба отримання всіх системних налаштувань: skip={skip}, limit={limit}")
        settings_db_list, _ = await self.setting_repo.get_multi_with_total_count( # Використовуємо get_multi_with_total_count
            session=self.db_session, skip=skip, limit=limit, sort_by="key"
        )
        # total_count тут не використовується, але метод get_multi_with_total_count його повертає

        response_list = [SystemSettingResponseSchema.model_validate(s) for s in settings_db_list]
        logger.info(f"Отримано {len(response_list)} системних налаштувань.")
        return response_list

    async def create_setting(self, setting_data: SystemSettingCreateSchema,
                             creator_id: Optional[int] = None) -> SystemSettingResponseSchema: # Змінено UUID на int
        """
        Створює нове системне налаштування.
        Переконується, що налаштування з таким ключем ще не існує.
        """
        logger.debug(f"Спроба створення нового системного налаштування з ключем: {setting_data.key}")
        existing_setting = await self.setting_repo.get_by_key(session=self.db_session, key=setting_data.key)
        if existing_setting:
            msg = f"Системне налаштування з ключем '{setting_data.key}' вже існує."
            logger.warning(msg + " Створення скасовано.")
            raise ValueError(msg)

        # Модель SystemSetting не має created_by_user_id, updated_by_user_id
        # kwargs_for_repo: Dict[str, Any] = {}
        # if creator_id:
        #     kwargs_for_repo['created_by_user_id'] = creator_id # Якщо б поле існувало
        #     kwargs_for_repo['updated_by_user_id'] = creator_id # Якщо б поле існувало

        try:
            new_setting_db = await self.setting_repo.create(
                session=self.db_session,
                obj_in=setting_data
                # **kwargs_for_repo
            )
            await self.commit()
            # await self.db_session.refresh(new_setting_db) # Не завжди потрібно після repo.create
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Помилка цілісності при створенні налаштування '{setting_data.key}': {e}",
                         exc_info=global_settings.DEBUG)
            raise ValueError(f"Не вдалося створити налаштування '{setting_data.key}' через конфлікт даних.")

        logger.info(f"Системне налаштування '{new_setting_db.key}' ID: {new_setting_db.id} успішно створено.")
        return SystemSettingResponseSchema.model_validate(new_setting_db)

    async def update_setting(self, setting_id: int, setting_update_data: SystemSettingUpdateSchema, # Змінено UUID на int
                             updater_id: Optional[int] = None) -> Optional[SystemSettingResponseSchema]: # Змінено UUID на int
        """
        Оновлює існуюче системне налаштування за його ID.
        """
        logger.debug(f"Спроба оновлення системного налаштування з ID: {setting_id}")

        setting_db = await self.setting_repo.get(session=self.db_session, id=setting_id)
        if not setting_db:
            logger.warning(f"Системне налаштування з ID '{setting_id}' не знайдено для оновлення.")
            return None

        update_data_dict = setting_update_data.model_dump(exclude_unset=True)

        if 'key' in update_data_dict and update_data_dict['key'] != setting_db.key:
            existing_key_setting = await self.setting_repo.get_by_key(session=self.db_session, key=update_data_dict['key'])
            if existing_key_setting and existing_key_setting.id != setting_id:
                msg = f"Інше системне налаштування з ключем '{update_data_dict['key']}' вже існує."
                logger.warning(
                    f"Неможливо оновити ключ для ID '{setting_id}' на '{update_data_dict['key']}', оскільки він використовується ID '{existing_key_setting.id}'. {msg}")
                raise ValueError(msg)

        # Модель SystemSetting не має updated_by_user_id. updated_at оновлюється автоматично.
        # kwargs_for_repo: Dict[str, Any] = {}
        # if updater_id and hasattr(SystemSetting, 'updated_by_user_id'):
        #    kwargs_for_repo['updated_by_user_id'] = updater_id

        try:
            updated_setting_db = await self.setting_repo.update(
                session=self.db_session,
                db_obj=setting_db,
                obj_in=setting_update_data # Передаємо Pydantic схему
                # **kwargs_for_repo
            )
            await self.commit()
            # await self.db_session.refresh(updated_setting_db) # Не завжди потрібно
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Помилка цілісності при оновленні налаштування ID '{setting_id}': {e}",
                         exc_info=global_settings.DEBUG)
            raise ValueError(f"Не вдалося оновити налаштування '{setting_db.key}' через конфлікт даних.")
        except Exception as e: # Обробка інших можливих помилок
            await self.rollback()
            logger.error(f"Неочікувана помилка при оновленні налаштування ID '{setting_id}': {e}", exc_info=global_settings.DEBUG)
            raise


        logger.info(f"Системне налаштування з ID '{updated_setting_db.id}' (ключ: {updated_setting_db.key}) успішно оновлено.")
        return SystemSettingResponseSchema.model_validate(updated_setting_db)

    async def delete_setting(self, setting_id: int) -> bool: # Змінено UUID на int
        """
        Видаляє системне налаштування за його ID.
        """
        logger.debug(f"Спроба видалення системного налаштування з ID: {setting_id}")
        setting_to_delete = await self.setting_repo.get(session=self.db_session, id=setting_id)

        if not setting_to_delete:
            logger.warning(f"Системне налаштування з ID '{setting_id}' не знайдено для видалення.")
            return False

        # TODO: Додати перевірку `is_editable_by_admin` або інші бізнес-правила
        # if not setting_to_delete.is_editable:
        #     raise ValueError(f"Налаштування '{setting_to_delete.key}' не може бути видалене.")

        deleted_setting = await self.setting_repo.remove(session=self.db_session, id=setting_id)
        if deleted_setting: # remove повертає видалений об'єкт або None
            await self.commit()
            logger.info(f"Системне налаштування з ID '{setting_id}' (ключ: {deleted_setting.key}) успішно видалено.")
            return True
        # Якщо remove повернув None, але get знайшов об'єкт, це дивно, але обробляємо як помилку
        logger.error(f"Не вдалося видалити налаштування ID '{setting_id}' через репозиторій.")
        return False


    def _deserialize_setting_value(self, value_str: str, value_type: SettingValueType) -> Any: # value_type тепер Enum
        """Допоміжний метод для десеріалізації значення налаштування на основі його типу."""
        logger.debug(f"Десеріалізація значення '{value_str}' як тип '{value_type.value}'")
        try:
            if value_type == SettingValueType.STRING:
                return value_str
            elif value_type == SettingValueType.INTEGER:
                return int(value_str)
            elif value_type == SettingValueType.FLOAT:
                return float(value_str)
            elif value_type == SettingValueType.BOOLEAN:
                return value_str.lower() in ('true', '1', 'yes', 'on', 't')
            elif value_type == SettingValueType.JSON:
                return json.loads(value_str)
            # TODO: Додати типи 'DATE', 'DATETIME', 'LIST_STR', 'LIST_INT'
            else: # За замовчуванням або якщо тип невідомий
                logger.warning(f"Невідомий або необроблений тип значення '{value_type.value}' для десеріалізації. Повернення як рядок.")
                return value_str
        except Exception as e:
            logger.error(f"Помилка десеріалізації значення '{value_str}' як '{value_type.value}': {e}",
                         exc_info=global_settings.DEBUG)
            return None # Або кинути виняток

    async def get_setting_value(self, key: str, default: Optional[Any] = None) -> Optional[Any]:
        """
        Допоміжний метод для отримання десеріалізованого значення налаштування за ключем.

        :param key: Ключ налаштування.
        :param default: Значення за замовчуванням, якщо налаштування не знайдено або помилка десеріалізації.
        :return: Десеріалізоване значення налаштування або значення за замовчуванням.
        """
        setting_response = await self.get_setting_by_key(key)
        if setting_response and setting_response.value is not None and setting_response.value_type is not None:
            # `value` в SystemSettingResponseSchema вже має бути правильного типу завдяки Pydantic моделі,
            # якщо модель SystemSetting.value є JSONB/JSON і SystemSettingResponseSchema.value має тип Any/Dict/List/etc.
            # Якщо SystemSetting.value є просто TEXT, то потрібна десеріалізація тут.
            # Припускаємо, що SystemSettingResponseSchema.value вже є Python-типом.
            # Якщо ні, то треба десеріалізувати:
            # return self._deserialize_setting_value(str(setting_response.value), setting_response.value_type)
            # Для Pydantic v2, якщо value є Json[Any] в моделі, то воно вже буде десеріалізоване.
            logger.debug(f"Значення для ключа '{key}': {setting_response.value} (тип: {type(setting_response.value)})")
            return setting_response.value

        logger.info(
            f"Системне налаштування '{key}' не знайдено або значення/тип не встановлено. Повернення значення за замовчуванням: {default}")
        return default


logger.debug(f"{SystemSettingService.__name__} (сервіс системних налаштувань) успішно визначено.")
