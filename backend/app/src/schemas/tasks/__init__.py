# backend/app/src/schemas/tasks/__init__.py
# -*- coding: utf-8 -*-
"""Pydantic схеми для сутностей, пов'язаних із завданнями та подіями.

Цей пакет містить схеми Pydantic, що використовуються для валідації
даних запитів та формування відповідей API, які стосуються:
- Завдань (`TaskBaseSchema`, `TaskCreateSchema`, `TaskUpdateSchema`, `TaskResponseSchema` з `task.py`).
- Подій (`EventBaseSchema`, `EventCreateSchema`, `EventUpdateSchema`, `EventResponseSchema` з `event.py`).
- Призначень завдань користувачам (`TaskAssignmentBaseSchema`, `TaskAssignmentCreateSchema`, `TaskAssignmentResponseSchema` з `assignment.py`).
- Записів про виконання завдань (`TaskCompletionBaseSchema`, `TaskCompletionCreateSchema`, `TaskCompletionUpdateSchema`, `TaskCompletionResponseSchema` з `completion.py`).
- Відгуків на завдання (`TaskReviewBaseSchema`, `TaskReviewCreateSchema`, `TaskReviewUpdateSchema`, `TaskReviewResponseSchema` з `review.py`).

Моделі з цього пакету експортуються для використання в сервісному шарі та API.
"""

# Імпорт централізованого логера
from backend.app.src.config import logger

# Схеми, пов'язані з Завданням (Task)
from backend.app.src.schemas.tasks.task import (
    TaskBaseSchema,
    TaskCreateSchema,
    TaskUpdateSchema,
    TaskResponseSchema
    # TaskDetailResponseSchema # Якщо буде окрема деталізована схема, наразі TaskResponseSchema використовується
)

# Схеми, пов'язані з Подією (Event)
from backend.app.src.schemas.tasks.event import (
    EventBaseSchema,
    EventCreateSchema,
    EventUpdateSchema,
    EventResponseSchema
)

# Схеми, пов'язані з Призначенням Завдання (TaskAssignment)
from backend.app.src.schemas.tasks.assignment import (
    TaskAssignmentBaseSchema,
    TaskAssignmentCreateSchema,
    # TaskAssignmentUpdateSchema, # Зазвичай призначення не оновлюються, а видаляються/створюються нові
    TaskAssignmentResponseSchema
)

# Схеми, пов'язані з Виконанням Завдання (TaskCompletion)
from backend.app.src.schemas.tasks.completion import (
    TaskCompletionBaseSchema,
    TaskCompletionCreateSchema,
    TaskCompletionUpdateSchema,
    TaskCompletionResponseSchema
)

# Схеми, пов'язані з Відгуком на Завдання (TaskReview)
from backend.app.src.schemas.tasks.review import (
    TaskReviewBaseSchema,
    TaskReviewCreateSchema,
    TaskReviewUpdateSchema,
    TaskReviewResponseSchema
)

__all__ = [
    # Task schemas
    "TaskBaseSchema",
    "TaskCreateSchema",
    "TaskUpdateSchema",
    "TaskResponseSchema",
    # "TaskDetailResponseSchema",
    # Event schemas
    "EventBaseSchema",
    "EventCreateSchema",
    "EventUpdateSchema",
    "EventResponseSchema",
    # TaskAssignment schemas
    "TaskAssignmentBaseSchema",
    "TaskAssignmentCreateSchema",
    # "TaskAssignmentUpdateSchema", # Зазвичай не оновлюється
    "TaskAssignmentResponseSchema",
    # TaskCompletion schemas
    "TaskCompletionBaseSchema",
    "TaskCompletionCreateSchema",
    "TaskCompletionUpdateSchema",
    "TaskCompletionResponseSchema",
    # TaskReview schemas
    "TaskReviewBaseSchema",
    "TaskReviewCreateSchema",
    "TaskReviewUpdateSchema",
    "TaskReviewResponseSchema",
]

logger.debug("Ініціалізація пакету схем Pydantic `tasks`...")
