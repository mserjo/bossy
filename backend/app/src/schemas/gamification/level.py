# backend/app/src/schemas/gamification/level.py
"""
Pydantic схеми для сутності "Рівень" (Level) в системі гейміфікації.

Цей модуль визначає схеми для:
- Створення нового рівня (`LevelCreateSchema`).
- Оновлення існуючого рівня (`LevelUpdateSchema`).
- Представлення даних про рівень у відповідях API (`LevelSchema`).
"""
from datetime import datetime  # Потрібен для TimestampedSchemaMixin через BaseMainSchema
from typing import Optional, Any  # Any для тимчасових полів

from pydantic import Field, AnyHttpUrl

# Абсолютний імпорт базових схем
from backend.app.src.schemas.base import BaseSchema, \
    BaseMainSchema  # IDSchemaMixin, TimestampedSchemaMixin вже в BaseMainSchema

# TODO: Замінити Any на конкретну схему GroupSchema (коротка версія), коли вона буде готова.
# from backend.app.src.schemas.groups.group import GroupBriefSchema
GroupBriefSchema = Any  # Тимчасовий заповнювач

LEVEL_NAME_MAX_LENGTH = 255
LEVEL_ICON_URL_MAX_LENGTH = 512


class LevelBaseSchema(BaseSchema):
    """
    Базова схема для полів рівня, спільних для створення та оновлення.
    """
    name: str = Field(
        ...,
        max_length=LEVEL_NAME_MAX_LENGTH,
        description="Назва рівня гейміфікації.",
        examples=["Новачок", "Досвідчений Гравець"]
    )
    description: Optional[str] = Field(
        None,
        description="Опис умов або переваг цього рівня."
    )
    required_points: int = Field(
        ...,
        ge=0,
        description="Кількість балів, необхідна для досягнення цього рівня."
    )
    level_number: Optional[int] = Field(
        None,
        ge=0,
        description="Порядковий номер рівня (наприклад, 1, 2, 3). Використовується для сортування та визначення прогресу."
    )
    icon_url: Optional[AnyHttpUrl] = Field(  # Використовуємо AnyHttpUrl для валідації URL
        None,
        # max_length не потрібен для AnyHttpUrl, валідація формату важливіша
        description="URL або шлях до іконки, що представляє рівень."
    )
    group_id: Optional[int] = Field(
        None,
        description="ID групи, до якої належить цей рівень. NULL, якщо рівень глобальний/системний."
    )
    # state успадковується в LevelSchema через BaseMainSchema, але може бути вказаний при створенні/оновленні
    state: Optional[str] = Field(
        None,  # Або default="active"
        max_length=50,
        description="Стан рівня (наприклад, 'active', 'inactive').",
        examples=["active"]
    )
    notes: Optional[str] = Field(  # Додаємо notes, оскільки Level модель успадковує NotesMixin через BaseMainModel
        None,
        description="Додаткові нотатки щодо рівня."
    )


class LevelCreateSchema(LevelBaseSchema):
    """
    Схема для створення нового рівня гейміфікації.
    Успадковує всі поля від `LevelBaseSchema`.
    """
    pass


class LevelUpdateSchema(LevelBaseSchema):
    """
    Схема для оновлення існуючого рівня гейміфікації.
    Всі поля, успадковані з `LevelBaseSchema`, стають опціональними.
    """
    name: Optional[str] = Field(None, max_length=LEVEL_NAME_MAX_LENGTH)
    description: Optional[str] = None
    required_points: Optional[int] = Field(None, ge=0)
    level_number: Optional[int] = Field(None, ge=0)
    icon_url: Optional[AnyHttpUrl] = None
    group_id: Optional[int] = Field(None,
                                    description="Зміна групи для рівня (зазвичай не дозволяється або обробляється окремо).")  # Зазвичай group_id не змінюється
    state: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None


class LevelSchema(BaseMainSchema):  # Успадковує id, name, description, state, notes, group_id, timestamps
    """
    Схема для представлення даних про рівень гейміфікації у відповідях API.
    Успадковує стандартні поля з `BaseMainSchema`.
    """
    # id, name, description, state, notes, group_id, created_at, updated_at, deleted_at - успадковані

    # Специфічні поля моделі Level
    required_points: int = Field(description="Кількість балів, необхідна для досягнення рівня.")
    level_number: Optional[int] = Field(description="Порядковий номер рівня.")
    icon_url: Optional[AnyHttpUrl] = Field(None, description="URL іконки рівня.")

    # Пов'язані об'єкти
    # TODO: Замінити Any на GroupBriefSchema, коли вона буде імпортована.
    group: Optional[GroupBriefSchema] = Field(None,
                                              description="Коротка інформація про групу, до якої належить рівень (якщо є).")

    # model_config успадковується з BaseMainSchema -> BaseSchema (from_attributes=True)


if __name__ == "__main__":
    # Демонстраційний блок для схем рівнів.
    print("--- Pydantic Схеми для Рівнів Гейміфікації (Level) ---")

    print("\nLevelCreateSchema (приклад для створення):")
    create_level_data = {
        "name": "Золотий Рівень",  # TODO i18n
        "description": "Визначний рівень для найактивніших учасників.",  # TODO i18n
        "required_points": 10000,
        "level_number": 5,
        "icon_url": "https://example.com/icons/gold_level.png",
        "group_id": 1,  # Припустимо, специфічний для групи 1
        "state": "active"
    }
    create_level_instance = LevelCreateSchema(**create_level_data)
    print(create_level_instance.model_dump_json(indent=2, exclude_none=True))

    print("\nLevelUpdateSchema (приклад для оновлення):")
    update_level_data = {
        "description": "Оновлений опис для Золотого Рівня, тепер вимагає більше балів.",  # TODO i18n
        "required_points": 12000
    }
    update_level_instance = LevelUpdateSchema(**update_level_data)
    print(update_level_instance.model_dump_json(indent=2, exclude_none=True))

    print("\nLevelSchema (приклад відповіді API):")
    level_response_data = {
        "id": 1,
        "name": "Срібний Рівень",  # TODO i18n
        "description": "Рівень для активних учасників.",  # TODO i18n
        "state": "active",
        "group_id": 1,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "required_points": 5000,
        "level_number": 3,
        "icon_url": "https://example.com/icons/silver_level.png",
        # "group": {"id": 1, "name": "Команда Альфа"} # Приклад GroupBriefSchema
    }
    level_response_instance = LevelSchema(**level_response_data)
    print(level_response_instance.model_dump_json(indent=2, exclude_none=True))

    print("\nПримітка: Схема для `group` наразі є заповнювачем (Any).")
    print("Її потрібно буде замінити на `GroupBriefSchema` після її визначення.")
