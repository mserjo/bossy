# backend/app/src/services/system/system_settings_service.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає сервіс `SystemSettingsService` для управління
глобальними системними налаштуваннями.
"""
from typing import List, Optional, Any, Dict
import uuid
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore

from backend.app.src.models.system.settings import SystemSettingModel
from backend.app.src.models.auth.user import UserModel
from backend.app.src.schemas.system.settings import SystemSettingCreateSchema, SystemSettingUpdateSchema, SystemSettingSchema
from backend.app.src.repositories.system.settings_repository import SystemSettingRepository # Змінено імпорт
from backend.app.src.services.base import BaseService
from backend.app.src.core.exceptions import NotFoundException, ForbiddenException, BadRequestException
from backend.app.src.core.constants import USER_TYPE_SUPERADMIN
from backend.app.src.config.logging import logger
import json

class SystemSettingsService(BaseService[SystemSettingRepository]):
    """
    Сервіс для управління глобальними системними налаштуваннями.
    Доступ до зміни налаштувань зазвичай має лише супер-адміністратор.
    """
    def __init__(self, db_session: AsyncSession): # Приймаємо сесію
        super().__init__(SystemSettingRepository(db_session)) # Ініціалізуємо репозиторій з сесією

    async def get_setting_by_key(self, key: str) -> SystemSettingModel:
        """Отримує налаштування за ключем."""
        setting = await self.repository.get_by_key(key=key)
        if not setting:
            logger.warning(f"Системне налаштування з ключем '{key}' не знайдено.")
            raise NotFoundException(f"Системне налаштування з ключем '{key}' не знайдено.")
        return setting

    async def get_setting_value_typed(self, key: str, default: Any = None) -> Any:
        """
        Отримує значення системного налаштування за ключем,
        конвертуючи його до відповідного типу.
        Повертає `default`, якщо ключ не знайдено або значення None.
        TODO: Реалізувати кешування для цього методу.
        """
        value = await self.repository.get_setting_value(key=key)
        return value if value is not None else default

    async def get_all_settings_as_dict(self, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Отримує всі системні налаштування у вигляді словника {ключ: значення}
        з конвертованими типами. Опціонально фільтрує за категорією.
        TODO: Реалізувати кешування для цього методу.
        """
        return await self.repository.get_all_settings_as_dict(category=category)

    async def get_all_settings_full(self, category: Optional[str] = None) -> List[SystemSettingModel]:
        """
        Отримує повні моделі всіх системних налаштувань.
        Опціонально фільтрує за категорією.
        """
        return await self.repository.get_all_by_category(category=category)


    async def create_setting(
        self, *, obj_in: SystemSettingCreateSchema, current_user: UserModel
    ) -> SystemSettingModel:
        """Створює нове системне налаштування. Доступно лише супер-адміністратору."""
        if current_user.user_type_code != USER_TYPE_SUPERADMIN:
            logger.warning(f"Користувач {current_user.email} (не супер-адмін) спробував створити системне налаштування.")
            raise ForbiddenException("Лише супер-адміністратор може створювати системні налаштування.")

        existing_setting = await self.repository.get_by_key(key=obj_in.key)
        if existing_setting:
            logger.warning(f"Спроба створити існуюче системне налаштування з ключем '{obj_in.key}'.")
            raise BadRequestException(f"Системне налаштування з ключем '{obj_in.key}' вже існує.")

        # `obj_in` вже містить `value` як рядок, завдяки валідатору в схемі.
        new_setting = await self.repository.create(obj_in=obj_in)
        logger.info(f"Супер-адміністратор {current_user.email} створив системне налаштування '{new_setting.key}'.")
        # TODO: Скинути кеш налаштувань після створення.
        return new_setting

    async def update_setting(
        self, *, key: str, obj_in: SystemSettingUpdateSchema, current_user: UserModel
    ) -> SystemSettingModel:
        db_setting = await self.get_setting_by_key(key=key)

        if current_user.user_type_code != USER_TYPE_SUPERADMIN:
            if not db_setting.is_editable_by_user: # Використовуємо поле з моделі
                logger.warning(f"Користувач {current_user.email} спробував оновити нередаговане налаштування '{key}'.")
                raise ForbiddenException(f"Налаштування '{key}' не може бути змінене звичайним користувачем.")
        # Супер-адмін може редагувати будь-яке налаштування, навіть якщо is_editable_by_user=False

        update_data_dict = obj_in.model_dump(exclude_unset=True)

        if "value" in update_data_dict and update_data_dict["value"] is not None:
            new_value_raw = update_data_dict["value"] # Це значення з Pydantic схеми, може бути будь-якого типу
            value_type = db_setting.value_type

            # Серіалізація значення в рядок відповідно до value_type
            try:
                if value_type == 'integer':
                    serialized_value = str(int(new_value_raw))
                elif value_type == 'float':
                    serialized_value = str(float(new_value_raw))
                elif value_type == 'boolean':
                    if isinstance(new_value_raw, str):
                        serialized_value = new_value_raw.lower()
                        if serialized_value not in ['true', 'false']:
                             raise ValueError("Булеве значення має бути 'true' або 'false'")
                    else:
                        serialized_value = str(bool(new_value_raw)).lower()
                elif value_type == 'json':
                    serialized_value = json.dumps(new_value_raw)
                elif value_type == 'list_string':
                    if not (isinstance(new_value_raw, list) and all(isinstance(item, str) for item in new_value_raw)):
                        raise ValueError("Значення має бути списком рядків")
                    serialized_value = ",".join(new_value_raw) # Або інший розділювач, або json.dumps
                elif value_type == 'string':
                    serialized_value = str(new_value_raw)
                else:
                    logger.warning(f"Спроба оновити значення для невідомого типу '{value_type}' налаштування '{key}'. Значення не буде змінено.")
                    if "value" in update_data_dict: del update_data_dict["value"]
                    serialized_value = None # Щоб уникнути помилки UnboundLocalError

                if serialized_value is not None: # Якщо тип був оброблений
                    update_data_dict["value"] = serialized_value

            except (ValueError, TypeError, json.JSONDecodeError) as e:
                logger.error(f"Помилка валідації або серіалізації нового значення для '{key}' (тип: {value_type}): {e}", exc_info=True)
                raise BadRequestException(f"Некоректне значення для типу '{value_type}' налаштування '{key}': {e}")

        if not update_data_dict:
            return db_setting

        updated_setting = await self.repository.update(db_obj=db_setting, obj_in=update_data_dict)
        logger.info(f"Користувач {current_user.email} оновив системне налаштування '{key}'.")
        # TODO: Скинути кеш налаштувань після оновлення.
        return updated_setting

    async def delete_setting(self, *, key: str, current_user: UserModel) -> SystemSettingModel:
        """Видаляє системне налаштування. Доступно лише супер-адміністратору."""
        if current_user.user_type_code != USER_TYPE_SUPERADMIN:
            logger.warning(f"Користувач {current_user.email} (не супер-адмін) спробував видалити системне налаштування '{key}'.")
            raise ForbiddenException("Лише супер-адміністратор може видаляти системні налаштування.")

        setting_to_delete = await self.get_setting_by_key(key=key)

        # TODO: Додати перевірку, чи можна видаляти це налаштування (наприклад, поле `is_deletable` в моделі)
        # if not setting_to_delete.is_deletable:
        #     logger.warning(f"Спроба видалити не видаляєме системне налаштування '{key}'.")
        #     raise ForbiddenException(f"Системне налаштування '{key}' не може бути видалене.")

        deleted_setting_id = await self.repository.delete(id=setting_to_delete.id) # delete повертає ID
        if not deleted_setting_id: # Малоймовірно, якщо get_by_key спрацював
            raise NotFoundException(f"Системне налаштування '{key}' не знайдено під час спроби видалення.")

        logger.info(f"Супер-адміністратор {current_user.email} видалив системне налаштування '{key}'.")
        # TODO: Скинути кеш налаштувань після видалення.
        return setting_to_delete # Повертаємо модель видаленого об'єкта

# Екземпляр сервісу не створюємо тут глобально, а в залежностях FastAPI або де потрібно.
# system_settings_service = SystemSettingsService(system_setting_repository) # Видалено, так як репо тепер ініціалізується з сесією в конструкторі.
