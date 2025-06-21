# backend/app/src/schemas/tasks/completion.py
"""
Pydantic схеми для сутності "Виконання Завдання" (TaskCompletion).

Цей модуль визначає схеми для:
- Базового представлення виконання завдання (`TaskCompletionBaseSchema`).
- Створення нового запису про виконання (`TaskCompletionCreateSchema`).
- Оновлення існуючого запису про виконання (наприклад, адміністратором) (`TaskCompletionUpdateSchema`).
- Представлення даних про виконання у відповідях API (`TaskCompletionSchema`).
"""
from datetime import datetime
from typing import Optional

from pydantic import Field  # field_validator видалено, оскільки більше не використовується

# Абсолютний імпорт базових схем та Enum
from backend.app.src.schemas.base import BaseSchema, IDSchemaMixin, TimestampedSchemaMixin
from backend.app.src.schemas.auth.user import UserPublicProfileSchema  # Для представлення користувача та верифікатора
from backend.app.src.core.dicts import TaskStatus  # Enum для статусів виконання
from datetime import timedelta # Переміщено timedelta сюди
from backend.app.src.config.logging import get_logger
from backend.app.src.core.i18n import _
logger = get_logger(__name__)


class TaskCompletionBaseSchema(BaseSchema):
    """
    Базова схема для полів виконання завдання.
    `task_id` та `user_id` зазвичай визначаються з контексту (шлях, поточний користувач).
    """
    # task_id: int = Field(description="Ідентифікатор завдання, що виконується.") # Зазвичай з URL
    # user_id: int = Field(description="Ідентифікатор користувача, який виконав завдання.") # Зазвичай поточний користувач

    completed_at: Optional[datetime] = Field(
        default_factory=datetime.now,
        description=_("task_completion.fields.completed_at.description")
    )
    status: TaskStatus = Field(
        default=TaskStatus.PENDING_REVIEW,
        description=_("task_completion.fields.status.description")
    )
    notes: Optional[str] = Field(None, description=_("task_completion.fields.notes.description"))

    # Валідатор validate_status більше не потрібен, Pydantic обробляє Enum

    # model_config успадковується з BaseSchema (from_attributes=True)


class TaskCompletionCreateSchema(TaskCompletionBaseSchema):
    """
    Схема для створення нового запису про виконання завдання користувачем.
    `task_id` зазвичай з параметра шляху, `user_id` - поточний користувач.
    """
    # Успадковує completed_at, status, notes.
    # task_id та user_id не включаються сюди, бо очікуються з контексту запиту (шлях, автентифікація).
    pass


class TaskCompletionUpdateSchema(
    BaseSchema):  # Не успадковує TaskCompletionBaseSchema, щоб уникнути успадкування полів, які не можна змінювати
    """
    Схема для оновлення запису про виконання завдання (зазвичай адміністратором).
    Дозволяє оновлювати статус, час верифікації та нотатки.
    """
    # completed_at: Optional[datetime] = None
    verified_at: Optional[datetime] = Field(None, description=_("task_completion.update.fields.verified_at.description"))
    # verifier_id: Optional[int] = None

    status: Optional[TaskStatus] = Field(None, description=_("task_completion.update.fields.status.description"))
    notes: Optional[str] = Field(None, description=_("task_completion.update.fields.notes.description"))

    # Валідатор validate_status_on_update більше не потрібен


class TaskCompletionSchema(TaskCompletionBaseSchema, IDSchemaMixin, TimestampedSchemaMixin):
    """
    Схема для представлення даних про виконання завдання у відповідях API.
    `created_at` з TimestampedSchemaMixin може позначати час подання запису про виконання.
    `updated_at` - час останнього оновлення запису (наприклад, зміни статусу).
    """
    # id, created_at, updated_at успадковані.
    # task_id, user_id, completed_at, status, notes успадковані з TaskCompletionBaseSchema.
    # Однак, task_id та user_id потрібно явно додати, бо вони не в TaskCompletionBaseSchema
    task_id: int = Field(description=_("task_completion.response.fields.task_id.description"))
    user_id: int = Field(description=_("task_completion.response.fields.user_id.description"))

    verified_at: Optional[datetime] = Field(None, description=_("task_completion.response.fields.verified_at.description"))

    user: Optional[UserPublicProfileSchema] = Field(None,
                                                    description=_("task_completion.response.fields.user.description"))
    verifier: Optional[UserPublicProfileSchema] = Field(None,
                                                        description=_("task_completion.response.fields.verifier.description"))


if __name__ == "__main__":
    # Демонстраційний блок для схем виконань завдань.
    logger.info("--- Pydantic Схеми для Виконань Завдань (TaskCompletion) ---")

    logger.info("\nTaskCompletionCreateSchema (приклад для створення):")
    create_completion_data = {
        "completed_at": datetime.now(),
        "status": TaskStatus.PENDING_REVIEW, # Використовуємо Enum
        "notes": "Завдання виконано, очікую на перевірку."  # TODO i18n
    }
    create_completion_instance = TaskCompletionCreateSchema(**create_completion_data)
    logger.info(create_completion_instance.model_dump_json(indent=2))

    logger.info("\nTaskCompletionUpdateSchema (приклад для оновлення адміністратором):")
    update_completion_data = {
        "verified_at": datetime.now(),
        "status": TaskStatus.COMPLETED, # Використовуємо Enum
        "notes": "Чудова робота!"  # TODO i18n
    }
    update_completion_instance = TaskCompletionUpdateSchema(**update_completion_data)
    logger.info(update_completion_instance.model_dump_json(indent=2, exclude_none=True))
    try:
        TaskCompletionUpdateSchema(status="невірний_статус")  # Невірний статус
    except Exception as e:
        logger.info(f"Помилка валідації TaskCompletionUpdateSchema (очікувано): {e}")

    logger.info("\nTaskCompletionSchema (приклад відповіді API):")
    completion_response_data = {
        "id": 1,
        "task_id": 10,
        "user_id": 101,
        "completed_at": datetime.now() - timedelta(hours=1),
        "status": TaskStatus.COMPLETED, # Використовуємо Enum
        "notes": "Завдання виконано успішно.",  # TODO i18n
        "created_at": datetime.now() - timedelta(hours=2),  # Час подання
        "updated_at": datetime.now(),  # Час останнього оновлення (напр. верифікації)
        "verified_at": datetime.now(),
        "user": {"id": 101, "name": "Виконавець Завдання"},  # TODO i18n
        "verifier": {"id": 2, "name": "Адмін Перевіряючий"}  # TODO i18n
    }
    completion_response_instance = TaskCompletionSchema(**completion_response_data)
    logger.info(completion_response_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nПримітка: Ці схеми використовуються для валідації та серіалізації даних виконань завдань.")
    logger.info(
        f"Використовується TaskStatus Enum для поля 'status', наприклад: TaskStatus.REJECTED = '{TaskStatus.REJECTED}'") # .value не потрібно для Enum member

# Потрібно для timedelta в __main__ - вже переміщено нагору
# from datetime import timedelta
