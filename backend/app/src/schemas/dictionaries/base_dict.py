# backend/app/src/schemas/dictionaries/base_dict.py
"""
Базові Pydantic схеми для моделей-довідників.

Цей модуль визначає:
- `BaseDictionarySchema`: Базова схема для представлення даних довідника у відповідях API.
                         Успадковує поля від `BaseMainSchema`.
- `DictionaryCreateSchema`: Схема для валідації даних при створенні нового запису довідника.
- `DictionaryUpdateSchema`: Схема для валідації даних при оновленні існуючого запису довідника.

Ці базові схеми призначені для успадкування конкретними схемами довідників
(наприклад, `StatusSchema`, `UserRoleSchema`).
"""

from typing import Optional

from pydantic import Field

# Абсолютний імпорт базових схем з головного модуля схем
from backend.app.src.schemas.base import BaseSchema, BaseMainSchema
from backend.app.src.config.logging import get_logger  # Імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)

# Максимальна довжина для поля 'name' та 'code' може бути винесена в константи,
# якщо це потрібно для узгодженості з моделями або іншими частинами системи.
# Наприклад, from backend.app.src.core.constants import DICT_NAME_MAX_LENGTH, DICT_CODE_MAX_LENGTH
DICT_NAME_MAX_LENGTH = 255
DICT_CODE_MAX_LENGTH = 100


class DictionaryBaseResponseSchema(BaseMainSchema): # Renamed from BaseDictionarySchema
    """
    Базова Pydantic схема для представлення запису довідника у відповідях API.

    Успадковує всі поля від `BaseMainSchema` (id, name, description, state, notes,
    group_id, created_at, updated_at, deleted_at) та додає поле `code`.
    Поле `group_id` успадковане, але для більшості системних довідників воно буде `None`.
    """
    code: str = Field(
        ..., # Означає, що поле є обов'язковим
        max_length=DICT_CODE_MAX_LENGTH,
        description="Унікальний текстовий код запису довідника.",
        examples=["active", "admin_role"]
    )
    # model_config успадковується з BaseMainSchema -> BaseSchema (from_attributes=True)

class DictionaryCreateSchema(BaseSchema):
    """
    Базова Pydantic схема для створення нового запису довідника.
    Не включає `id`, часові мітки або `deleted_at`, оскільки вони генеруються сервером або неактуальні при створенні.
    """
    name: str = Field(
        ...,
        max_length=DICT_NAME_MAX_LENGTH,
        description="Назва запису довідника.",
        examples=["Активний", "Роль адміністратора"]
    )
    code: str = Field(
        ...,
        max_length=DICT_CODE_MAX_LENGTH,
        description="Унікальний текстовий код запису довідника.",
        examples=["ACTIVE", "ADMIN_ROLE"]
    )
    description: Optional[str] = Field(
        None,
        description="Детальний опис запису довідника (необов'язково)."
    )
    state: Optional[str] = Field(
        None,
        description="Стан запису довідника (наприклад, 'active', 'deprecated', необов'язково)."
    )
    notes: Optional[str] = Field(
        None,
        description="Додаткові нотатки щодо запису довідника (необов'язково)."
    )
    # group_id тут не додається за замовчуванням, оскільки більшість довідників є глобальними.
    # Якщо конкретний довідник може бути специфічним для групи, group_id додається в його Create/Update схемах.


class DictionaryUpdateSchema(BaseSchema):
    """
    Базова Pydantic схема для оновлення існуючого запису довідника.
    Всі поля є опціональними, оскільки оновлення може бути частковим (PATCH).
    """
    name: Optional[str] = Field(
        None,
        max_length=DICT_NAME_MAX_LENGTH,
        description="Нова назва запису довідника.",
        examples=["Активний статус"]
    )
    code: Optional[str] = Field(
        None,
        max_length=DICT_CODE_MAX_LENGTH,
        description="Новий унікальний текстовий код запису довідника.",
        examples=["ACTIVE_STATUS"]
    )
    description: Optional[str] = Field(
        None,
        description="Новий детальний опис запису довідника."
    )
    state: Optional[str] = Field(
        None,
        description="Новий стан запису довідника."
    )
    notes: Optional[str] = Field(
        None,
        description="Нові додаткові нотатки щодо запису довідника."
    )
    # group_id тут також не додається за замовчуванням.

if __name__ == "__main__":
    # Демонстраційний блок для базових схем довідників.
    logger.info("--- Базові Схеми Pydantic для Довідників ---")

    logger.info("\nBaseDictionarySchema (приклад):")
    # Для демонстрації DictionaryBaseResponseSchema потрібні всі поля з BaseMainSchema
    from datetime import datetime
    try:
        base_dict_example = DictionaryBaseResponseSchema( # Renamed
            id=1,
            name="Приклад Назви",
            code="EXAMPLE_CODE",
            description="Опис прикладу.",
            state="active",
            created_at=datetime.now(),
            updated_at=datetime.now()
            # group_id, notes, deleted_at - опціональні
        )
        logger.info(base_dict_example.model_dump_json(indent=2, exclude_none=True))
    except Exception as e:
        logger.info(f"Помилка створення BaseDictionarySchema: {e}")


    logger.info("\nDictionaryCreateSchema (приклад):")
    create_data = {
        "name": "Новий Статус",
        "code": "NEW_STATUS",
        "description": "Опис нового статусу."
    }
    create_schema_instance = DictionaryCreateSchema(**create_data)
    logger.info(create_schema_instance.model_dump_json(indent=2))

    logger.info("\nDictionaryUpdateSchema (приклад):")
    update_data = {
        "name": "Оновлена Назва Статусу",
        "state": "deprecated"
    }
    update_schema_instance = DictionaryUpdateSchema(**update_data)
    logger.info(update_schema_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nПримітка: Ці базові схеми призначені для успадкування конкретними схемами довідників.")
    logger.info("Конфігурація моделі (наприклад, from_attributes=True) успадковується від BaseSchema.")
