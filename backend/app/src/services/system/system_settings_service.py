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
from backend.app.src.models.auth.user import UserModel # Для перевірки прав (superuser)
from backend.app.src.schemas.system.settings import SystemSettingCreateSchema, SystemSettingUpdateSchema, SystemSettingSchema
from backend.app.src.repositories.system.settings import SystemSettingRepository, system_setting_repository
from backend.app.src.services.base import BaseService
from backend.app.src.core.exceptions import NotFoundException, ForbiddenException, BadRequestException
from backend.app.src.core.constants import USER_TYPE_SUPERADMIN
import json # Для перетворення типів

class SystemSettingsService(BaseService[SystemSettingRepository]):
    """
    Сервіс для управління глобальними системними налаштуваннями.
    Доступ до зміни налаштувань зазвичай має лише супер-адміністратор.
    """

    async def get_setting_by_key(self, db: AsyncSession, key: str) -> SystemSettingModel:
        """Отримує налаштування за ключем."""
        setting = await self.repository.get_by_key(db, key=key)
        if not setting:
            raise NotFoundException(f"Системне налаштування з ключем '{key}' не знайдено.")
        return setting

    async def get_setting_value_typed(self, db: AsyncSession, key: str, default: Any = None) -> Any:
        """
        Отримує значення системного налаштування за ключем,
        конвертуючи його до відповідного типу.
        Повертає `default`, якщо ключ не знайдено або значення None.
        """
        # Використовуємо метод репозиторію, який вже робить конвертацію
        value = await self.repository.get_setting_value(db, key=key)
        return value if value is not None else default

    async def get_all_settings(self, db: AsyncSession, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Отримує всі системні налаштування у вигляді словника {ключ: значення}
        з конвертованими типами. Опціонально фільтрує за категорією.
        """
        return await self.repository.get_all_settings_as_dict(db, category=category)

    async def create_setting(
        self, db: AsyncSession, *, obj_in: SystemSettingCreateSchema, current_user: UserModel
    ) -> SystemSettingModel:
        """Створює нове системне налаштування. Доступно лише супер-адміністратору."""
        if current_user.user_type_code != USER_TYPE_SUPERADMIN:
            raise ForbiddenException("Лише супер-адміністратор може створювати системні налаштування.")

        # Перевірка унікальності ключа (вже є в моделі, але можна і тут)
        existing_setting = await self.repository.get_by_key(db, key=obj_in.key)
        if existing_setting:
            raise BadRequestException(f"Системне налаштування з ключем '{obj_in.key}' вже існує.")

        # Схема SystemSettingCreateSchema вже має валідатор, який перетворює `value` на рядок
        # на основі `value_type` перед передачею в репозиторій.
        # Репозиторій `create` приймає цю схему.
        return await self.repository.create(db, obj_in=obj_in)

    async def update_setting(
        self, db: AsyncSession, *, key: str, obj_in: SystemSettingUpdateSchema, current_user: UserModel
    ) -> SystemSettingModel:
        """
        Оновлює значення існуючого системного налаштування.
        Доступно лише супер-адміністратору (або якщо `is_editable=True` для налаштування).
        """
        db_setting = await self.get_setting_by_key(db, key=key) # Перевіряє існування

        if current_user.user_type_code != USER_TYPE_SUPERADMIN and not db_setting.is_editable:
            raise ForbiddenException(f"Налаштування '{key}' не може бути змінене.")
        elif current_user.user_type_code != USER_TYPE_SUPERADMIN and db_setting.is_editable == False: # Явна перевірка False
             raise ForbiddenException(f"Налаштування '{key}' не може бути змінене (is_editable=False).")


        # Потрібно підготувати дані для оновлення: конвертувати нове `value` в рядок
        # на основі `db_setting.value_type`.
        update_data_dict = obj_in.model_dump(exclude_unset=True)

        if "value" in update_data_dict and update_data_dict["value"] is not None:
            new_value = update_data_dict["value"]
            value_type = db_setting.value_type # Беремо тип з існуючого налаштування
            try:
                if value_type == 'integer':
                    if not isinstance(new_value, int): raise ValueError("Значення має бути цілим числом")
                    update_data_dict["value"] = str(new_value)
                elif value_type == 'float':
                    if not isinstance(new_value, (int, float)): raise ValueError("Значення має бути числом (float)")
                    update_data_dict["value"] = str(new_value)
                elif value_type == 'boolean':
                    if not isinstance(new_value, bool): raise ValueError("Значення має бути булевим (true/false)")
                    update_data_dict["value"] = str(new_value).lower()
                elif value_type == 'json':
                    update_data_dict["value"] = json.dumps(new_value)
                elif value_type == 'list_string':
                    if not (isinstance(new_value, list) and all(isinstance(item, str) for item in new_value)):
                        raise ValueError("Значення має бути списком рядків")
                    update_data_dict["value"] = ",".join(new_value)
                elif value_type == 'string':
                    if not isinstance(new_value, str): raise ValueError("Значення має бути рядком")
                    # Залишається як є
                else:
                    # Якщо тип невідомий, не змінюємо або кидаємо помилку
                    self.logger.warning(f"Спроба оновити значення для невідомого типу '{value_type}' налаштування '{key}'.")
                    # Можна видалити 'value' з update_data_dict, щоб воно не оновлювалося
                    if "value" in update_data_dict: del update_data_dict["value"]

            except (ValueError, TypeError, json.JSONDecodeError) as e:
                raise BadRequestException(f"Помилка валідації або серіалізації нового значення для '{key}' (тип: {value_type}): {e}")

        if not update_data_dict: # Якщо нічого не оновлюється (наприклад, лише value було None)
            return db_setting

        return await self.repository.update(db, db_obj=db_setting, obj_in=update_data_dict)


    async def delete_setting(self, db: AsyncSession, *, key: str, current_user: UserModel) -> Optional[SystemSettingModel]:
        """Видаляє системне налаштування. Доступно лише супер-адміністратору."""
        if current_user.user_type_code != USER_TYPE_SUPERADMIN:
            raise ForbiddenException("Лише супер-адміністратор може видаляти системні налаштування.")

        setting_to_delete = await self.get_setting_by_key(db, key=key) # Перевіряє існування
        # TODO: Перевірити, чи налаштування `is_editable` або чи є воно критично важливим
        #       перед видаленням (наприклад, деякі системні налаштування можуть бути незмінними).
        #       Поки що дозволяємо видалення будь-якого.
        return await self.repository.delete(db, id=setting_to_delete.id)

system_settings_service = SystemSettingsService(system_setting_repository)

# TODO: Переконатися, що `SystemSettingCreateSchema` та `SystemSettingUpdateSchema`
#       коректно обробляють значення `value` та його тип.
#       `SystemSettingCreateSchema` вже має валідатор, що серіалізує `value` в рядок.
#       `SystemSettingUpdateSchema` потребує логіки серіалізації в сервісі (додано).
#
# TODO: Розглянути механізм кешування для системних налаштувань,
#       оскільки вони можуть часто читатися і рідко змінюватися.
#
# Все виглядає як хороший початок для SystemSettingsService.
# Основні CRUD операції з перевіркою прав супер-адміністратора.
# Методи для отримання значення з конвертацією типу та всіх налаштувань.
# Обробка серіалізації/десеріалізації значення на основі `value_type`.
