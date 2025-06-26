# backend/app/src/repositories/system/settings.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає репозиторій для моделі `SystemSettingModel`.
Надає методи для управління глобальними системними налаштуваннями.
"""

from typing import Optional, List, Any, Dict
from sqlalchemy import select # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore
import json

from backend.app.src.models.system.settings import SystemSettingModel
from backend.app.src.schemas.system.settings import SystemSettingCreateSchema, SystemSettingUpdateSchema
from backend.app.src.repositories.base import BaseRepository

class SystemSettingRepository(BaseRepository[SystemSettingModel, SystemSettingCreateSchema, SystemSettingUpdateSchema]):
    """
    Репозиторій для роботи з моделлю системних налаштувань (`SystemSettingModel`).
    Кожне налаштування зберігається як окремий запис ключ-значення.
    """

    async def get_by_key(self, db: AsyncSession, *, key: str) -> Optional[SystemSettingModel]:
        """
        Отримує системне налаштування за його унікальним ключем.

        :param db: Асинхронна сесія бази даних.
        :param key: Унікальний ключ налаштування.
        :return: Об'єкт SystemSettingModel або None, якщо налаштування не знайдено.
        """
        statement = select(self.model).where(self.model.key == key)
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_setting_value(self, db: AsyncSession, *, key: str) -> Any:
        """
        Отримує значення системного налаштування за ключем, автоматично
        конвертуючи його до відповідного типу на основі `value_type`.
        Повертає None, якщо ключ не знайдено.
        """
        setting = await self.get_by_key(db, key=key)
        if not setting or setting.value is None:
            return None

        try:
            if setting.value_type == 'integer':
                return int(setting.value)
            elif setting.value_type == 'float':
                return float(setting.value)
            elif setting.value_type == 'boolean':
                return setting.value.lower() in ['true', '1', 'yes', 'on']
            elif setting.value_type == 'json':
                return json.loads(setting.value)
            elif setting.value_type == 'list_string':
                return [item.strip() for item in setting.value.split(',') if item.strip()]
            elif setting.value_type == 'string':
                return str(setting.value) # Явне перетворення, хоча воно вже рядок
            else: # Невідомий тип, повертаємо як рядок
                return setting.value
        except (ValueError, TypeError, json.JSONDecodeError):
            # Помилка конвертації, повертаємо сире значення або None/кидаємо виняток
            # from backend.app.src.config.logging import logger
            # logger.error(f"Помилка конвертації значення для системного налаштування '{key}' (тип: {setting.value_type}, значення: '{setting.value[:50]}...')")
            return setting.value # Повертаємо сире значення, якщо не вдалося розпарсити

    async def get_all_settings_as_dict(self, db: AsyncSession, *, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Отримує всі системні налаштування у вигляді словника {ключ: значення},
        з конвертацією значень до їх типів.
        Опціонально фільтрує за категорією.
        """
        statement = select(self.model)
        if category:
            statement = statement.where(self.model.category == category)

        result = await db.execute(statement)
        settings_list = result.scalars().all()

        settings_dict: Dict[str, Any] = {}
        for setting in settings_list:
            if setting.value is not None:
                try:
                    if setting.value_type == 'integer':
                        settings_dict[setting.key] = int(setting.value)
                    elif setting.value_type == 'float':
                        settings_dict[setting.key] = float(setting.value)
                    elif setting.value_type == 'boolean':
                        settings_dict[setting.key] = setting.value.lower() in ['true', '1', 'yes', 'on']
                    elif setting.value_type == 'json':
                        settings_dict[setting.key] = json.loads(setting.value)
                    elif setting.value_type == 'list_string':
                        settings_dict[setting.key] = [item.strip() for item in setting.value.split(',') if item.strip()]
                    else: # string та інші
                        settings_dict[setting.key] = setting.value
                except (ValueError, TypeError, json.JSONDecodeError):
                    settings_dict[setting.key] = setting.value # Залишаємо як рядок у випадку помилки
            else:
                settings_dict[setting.key] = None
        return settings_dict

    # `create` успадкований. `SystemSettingCreateSchema` використовується.
    # Важливо, щоб `SystemSettingCreateSchema` мала валідатор, який перетворює
    # `value` в рядок на основі `value_type` перед збереженням.
    # (Такий валідатор є в схемі).

    # `update` успадкований. `SystemSettingUpdateSchema` використовується.
    # Аналогічно, сервіс або схема оновлення мають забезпечити правильну
    # серіалізацію `value` в рядок перед передачею в репозиторій.
    # (Схема `SystemSettingUpdateSchema` проста, тому це робить сервіс).

system_setting_repository = SystemSettingRepository(SystemSettingModel)

# TODO: Переконатися, що `SystemSettingCreateSchema` та `SystemSettingUpdateSchema`
#       коректно обробляють серіалізацію значення `value` в рядок,
#       оскільки модель `SystemSettingModel.value` зберігає `Text`.
#       (Схема `SystemSettingCreateSchema` має валідатор для цього).
#       Для `SystemSettingUpdateSchema` це має оброблятися на сервісному рівні.
#
# TODO: Подумати про кешування системних налаштувань, оскільки вони можуть часто читатися.
#       Це краще реалізувати на сервісному рівні.
#
# Все виглядає добре. Репозиторій надає зручні методи для роботи з налаштуваннями.
# `get_setting_value` та `get_all_settings_as_dict` з автоматичною конвертацією типів корисні.
# Унікальність `key` в `SystemSettingModel` забезпечується на рівні моделі.
