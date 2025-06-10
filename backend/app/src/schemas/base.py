# backend/app/src/schemas/base.py
"""
Базові схеми Pydantic для програми Kudos.

Цей модуль визначає набір базових класів та міксинів для Pydantic схем,
які використовуються для валідації даних, серіалізації та документації API.
Включає загальні поля, конфігурації моделей та узагальнені схеми відповідей.

Основні компоненти:
- `BaseSchema`: Базовий клас для всіх Pydantic схем з загальною конфігурацією.
- Міксини: `IDSchemaMixin`, `TimestampedSchemaMixin`, `SoftDeleteSchemaMixin` для додавання спільних полів.
- `BaseMainSchema`: Комбінована схема, що успадковує базові поля та міксини,
                    призначена для основних об'єктів предметної області.
- Узагальнені схеми відповідей: `MsgResponse`, `DataResponse`, `PaginatedResponse`
                               для стандартизації відповідей API.
"""

from datetime import datetime
from typing import List, Optional, TypeVar, Generic, Any

from pydantic import BaseModel, ConfigDict, Field, EmailStr, AnyHttpUrl # EmailStr, AnyHttpUrl для можливого використання в майбутніх базових схемах
from backend.app.src.config.logging import get_logger  # Імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)

# Узагальнений тип для використання в DataResponse та PaginatedResponse
T = TypeVar("T")

class BaseSchema(BaseModel):
    """
    Базовий клас для всіх Pydantic схем у програмі.

    Встановлює загальну конфігурацію для моделей Pydantic:
    - `from_attributes=True`: Дозволяє створювати схеми з атрибутів об'єктів SQLAlchemy (ORM mode).
    - `populate_by_name=True`: Дозволяє використовувати аліаси полів (наприклад, для `totalItems`).
    - `arbitrary_types_allowed=True`: Дозволяє використовувати складні типи, такі як `Decimal`,
                                     хоча для них часто потрібні кастомні серіалізатори/валідатори.
    """
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        arbitrary_types_allowed=True
    )

# --- Міксини для полів ---

class IDSchemaMixin(BaseModel):
    """Міксин для додавання поля `id` (цілочисельний ідентифікатор)."""
    id: int

class TimestampedSchemaMixin(BaseModel):
    """Міксин для додавання полів `created_at` та `updated_at` (дата та час)."""
    created_at: datetime
    updated_at: datetime

class SoftDeleteSchemaMixin(BaseModel):
    """Міксин для додавання поля `deleted_at` (опціональна дата та час м'якого видалення)."""
    deleted_at: Optional[datetime] = None

# --- Основна базова схема для об'єктів предметної області ---

class BaseMainSchema(BaseSchema, IDSchemaMixin, TimestampedSchemaMixin, SoftDeleteSchemaMixin):
    """
    Основна базова схема для більшості об'єктів предметної області.

    Успадковує `BaseSchema` та міксини для `id`, часових міток (`created_at`, `updated_at`),
    та м'якого видалення (`deleted_at`). Також включає типові поля, такі як `name`,
    `description`, `state`, `notes` та `group_id`.

    Атрибути:
        id (int): Унікальний ідентифікатор (з `IDSchemaMixin`).
        name (str): Назва об'єкта.
        description (Optional[str]): Опис об'єкта.
        state (Optional[str]): Поточний стан об'єкта.
        notes (Optional[str]): Додаткові нотатки.
        group_id (Optional[int]): Ідентифікатор групи, до якої може належати об'єкт.
        created_at (datetime): Час створення (з `TimestampedSchemaMixin`).
        updated_at (datetime): Час останнього оновлення (з `TimestampedSchemaMixin`).
        deleted_at (Optional[datetime]): Час м'якого видалення (з `SoftDeleteSchemaMixin`).
    """
    name: str
    description: Optional[str] = None
    state: Optional[str] = None
    notes: Optional[str] = None
    group_id: Optional[int] = None # Може бути None для системних об'єктів або об'єктів верхнього рівня

# --- Узагальнені схеми відповідей API ---

class MsgResponse(BaseSchema):
    """Схема для простих повідомлень у відповіді API (наприклад, статус операції)."""
    msg: str # Повідомлення для клієнта

class DataResponse(BaseSchema, Generic[T]):
    """
    Узагальнена схема для відповідей API, що містять один об'єкт даних.

    Атрибути:
        data (T): Об'єкт даних, тип якого визначається параметром `T`.
    """
    data: T

class PaginatedResponse(BaseSchema, Generic[T]):
    """
    Узагальнена схема для відповідей API, що містять список об'єктів з пагінацією.

    Атрибути:
        items (List[T]): Список об'єктів на поточній сторінці.
        total_items (int): Загальна кількість об'єктів у наборі даних.
        current_page (int): Номер поточної сторінки.
        page_size (int): Кількість об'єктів на сторінці.
        total_pages (int): Загальна кількість сторінок.
    """
    items: List[T]
    total_items: int = Field(alias="totalItems") # Використовуємо аліас для відповідності camelCase конвенції в JSON
    current_page: int = Field(alias="currentPage")
    page_size: int = Field(alias="pageSize")
    total_pages: int = Field(alias="totalPages")
    # Можливе розширення для cursor-based pagination:
    # next_page_token: Optional[str] = None
    # prev_page_token: Optional[str] = None


# Блок для демонстрації та базового тестування схем при прямому запуску модуля.
if __name__ == "__main__":
    logger.info("--- Демонстрація Базових Схем Pydantic ---")

    # Демонстрація BaseMainSchema
    class ConcreteMain(BaseMainSchema):
        """Конкретна реалізація BaseMainSchema для тестування."""
        specific_field: str = "специфічне поле" # TODO i18n

    main_instance_data = {
        "id": 1,
        "name": "Тестовий Об'єкт", # TODO i18n
        "description": "Це опис тестового об'єкта.", # TODO i18n
        "state": "активний", # TODO i18n
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "specific_field": "значення поля" # TODO i18n
        # group_id, notes, deleted_at - опціональні
    }
    main_instance = ConcreteMain(**main_instance_data)
    logger.info(f"\nЕкземпляр ConcreteMain:\n{main_instance.model_dump_json(indent=2, exclude_none=True)}")

    # Демонстрація MsgResponse
    msg_response = MsgResponse(msg="Операція успішно завершена.") # TODO i18n
    logger.info(f"\nЕкземпляр MsgResponse:\n{msg_response.model_dump_json(indent=2)}")

    # Демонстрація DataResponse
    class DummyData(BaseSchema):
        """Фіктивна схема даних для демонстрації."""
        field_a: str
        field_b: int

    dummy_data_instance = DummyData(field_a="текст", field_b=123) # TODO i18n
    data_response = DataResponse[DummyData](data=dummy_data_instance)
    logger.info(f"\nЕкземпляр DataResponse[DummyData]:\n{data_response.model_dump_json(indent=2)}")

    # Демонстрація PaginatedResponse
    items_list = [
        DummyData(field_a="елемент1", field_b=1), # TODO i18n
        DummyData(field_a="елемент2", field_b=2)  # TODO i18n
    ]
    paginated_response = PaginatedResponse[DummyData](
        items=items_list,
        totalItems=100, # Використовуємо аліас totalItems
        currentPage=1,
        pageSize=2,
        totalPages=50
    )
    logger.info(f"\nЕкземпляр PaginatedResponse[DummyData]:\n{paginated_response.model_dump_json(indent=2)}")
    logger.info(f"\nДоступ через Python атрибут (не аліас): paginated_response.total_items = {paginated_response.total_items}")

    logger.info("\nПеревірка конфігурації моделі в BaseSchema:")
    logger.info(f"  BaseSchema.model_config['from_attributes'] = {BaseSchema.model_config.get('from_attributes')}")
    logger.info(f"  BaseSchema.model_config['populate_by_name'] = {BaseSchema.model_config.get('populate_by_name')}")
    logger.info(f"  BaseSchema.model_config['arbitrary_types_allowed'] = {BaseSchema.model_config.get('arbitrary_types_allowed')}")

    logger.info("\nПримітка: Ці базові схеми призначені для успадкування конкретними схемами даних у модулях `schemas`.")
