# backend/app/src/schemas/tasks/assignment.py
"""
Pydantic схеми для сутності "Призначення Завдання" (TaskAssignment).

Цей модуль визначає схеми для:
- Базового представлення призначення завдання (`TaskAssignmentBaseSchema`).
- Створення нового запису про призначення (`TaskAssignmentCreateSchema`).
- Представлення даних про призначення у відповідях API (`TaskAssignmentSchema`).
"""
from datetime import datetime
from typing import Optional

from pydantic import Field # field_validator видалено, оскільки більше не використовується

# Абсолютний імпорт базових схем та Enum
from backend.app.src.schemas.base import BaseSchema, TimestampedSchemaMixin
from backend.app.src.schemas.auth.user import UserPublicProfileSchema  # Для представлення користувача
from backend.app.src.core.dicts import TaskAssignmentStatus
from backend.app.src.config.logging import get_logger
from backend.app.src.core.i18n import _
logger = get_logger(__name__)

# TaskAssignmentStatus Enum імпортовано вище.


class TaskAssignmentBaseSchema(BaseSchema):
    """
    Базова схема для полів призначення завдання.
    """
    task_id: int = Field(description=_("task_assignment.fields.task_id.description"))
    user_id: int = Field(description=_("task_assignment.fields.user_id.description"))
    status: Optional[TaskAssignmentStatus] = Field(
        None,
        description=_("task_assignment.fields.status.description")
    )

    # model_config успадковується з BaseSchema (from_attributes=True)


class TaskAssignmentCreateSchema(BaseSchema):
    """
    Схема для створення нового запису про призначення завдання.
    `task_id` зазвичай передається як параметр шляху.
    """
    user_id: int = Field(description=_("task_assignment.create.fields.user_id.description"))
    status: Optional[TaskAssignmentStatus] = Field(
        default=TaskAssignmentStatus.ASSIGNED,  # Статус за замовчуванням при створенні
        description=_("task_assignment.create.fields.status.description")
    )


class TaskAssignmentUpdateSchema(BaseSchema):
    """
    Схема для оновлення статусу призначення завдання.
    Дозволяє оновлювати лише поле `status`.
    """
    status: TaskAssignmentStatus = Field(description=_("task_assignment.update.fields.status.description"))


class TaskAssignmentSchema(TaskAssignmentBaseSchema, TimestampedSchemaMixin):
    """
    Схема для представлення даних про призначення завдання у відповідях API.
    Включає інформацію про користувача та часові мітки (коли було створено/оновлено призначення).
    `created_at` тут може трактуватися як `assigned_at`.
    """
    # task_id, user_id, status успадковані з TaskAssignmentBaseSchema
    # created_at, updated_at успадковані з TimestampedSchemaMixin

    user: Optional[UserPublicProfileSchema] = Field(None,
                                                    description=_("task_assignment.response.fields.user.description"))
    # Можна додати поле `task: Optional[TaskBriefSchema] = None`, якщо потрібно коротко показувати деталі завдання.


if __name__ == "__main__":
    # Демонстраційний блок для схем призначень завдань.
    logger.info("--- Pydantic Схеми для Призначень Завдань (TaskAssignment) ---")

    logger.info("\nTaskAssignmentBaseSchema (приклад):")
    base_assign_data = {"task_id": 1, "user_id": 101, "status": TaskAssignmentStatus.ACCEPTED} # Використовуємо Enum
    base_assign_instance = TaskAssignmentBaseSchema(**base_assign_data)
    logger.info(base_assign_instance.model_dump_json(indent=2))

    logger.info("\nTaskAssignmentCreateSchema (приклад для створення):")
    create_assign_data = {"user_id": 102, "status": TaskAssignmentStatus.ASSIGNED} # Використовуємо Enum
    create_assign_instance = TaskAssignmentCreateSchema(**create_assign_data)
    logger.info(create_assign_instance.model_dump_json(indent=2))
    try:
        TaskAssignmentCreateSchema(user_id=103, status="невірний_статус") # Pydantic валідує Enum
    except Exception as e:
        logger.info(f"Помилка валідації TaskAssignmentCreateSchema (очікувано): {e}")

    logger.info("\nTaskAssignmentUpdateSchema (приклад для оновлення):")
    update_assign_data = {"status": TaskAssignmentStatus.DECLINED} # Використовуємо Enum
    update_assign_instance = TaskAssignmentUpdateSchema(**update_assign_data)
    logger.info(update_assign_instance.model_dump_json(indent=2))

    logger.info("\nTaskAssignmentSchema (приклад відповіді API):")
    assignment_response_data = {
        "task_id": 1,
        "user_id": 101,
        "status": TaskAssignmentStatus.ACCEPTED, # Використовуємо Enum
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "user": {"id": 101, "name": "Призначений Користувач"}  # TODO i18n (UserPublicProfileSchema)
    }
    assignment_response_instance = TaskAssignmentSchema(**assignment_response_data)
    logger.info(assignment_response_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nПримітка: Ці схеми використовуються для валідації та серіалізації даних призначень завдань.")
    # logger.info("TODO: Інтегрувати Enum 'TaskAssignmentStatus' з core.dicts для поля 'status'.") # Вирішено
