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
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

# Схеми, пов'язані з Завданням (Task)
from backend.app.src.schemas.tasks.task import (
    TaskBaseSchema,
    TaskCreateSchema,
    TaskUpdateSchema,
    TaskSchema,  # Використовуємо фактичну назву
    TaskDetailSchema # Додано деталізовану схему
)

# Схеми, пов'язані з Подією (Event)
# EventResponseSchema є фактичною назвою в event.py
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
    TaskAssignmentUpdateSchema, # Додано, оскільки схема існує
    TaskAssignmentSchema # Використовуємо фактичну назву
)

# Схеми, пов'язані з Виконанням Завдання (TaskCompletion)
from backend.app.src.schemas.tasks.completion import (
    TaskCompletionBaseSchema,
    TaskCompletionCreateSchema,
    TaskCompletionUpdateSchema,
    TaskCompletionSchema # Використовуємо фактичну назву
)

# Схеми, пов'язані з Відгуком на Завдання (TaskReview)
from backend.app.src.schemas.tasks.review import (
    TaskReviewBaseSchema,
    TaskReviewCreateSchema,
    TaskReviewUpdateSchema,
    TaskReviewSchema # Використовуємо фактичну назву
)

__all__ = [
    # Task schemas
    "TaskBaseSchema",
    "TaskCreateSchema",
    "TaskUpdateSchema",
    "TaskSchema",
    "TaskDetailSchema",
    # Event schemas
    "EventBaseSchema",
    "EventCreateSchema",
    "EventUpdateSchema",
    "EventResponseSchema", # EventResponseSchema є фактичною назвою
    # TaskAssignment schemas
    "TaskAssignmentBaseSchema",
    "TaskAssignmentCreateSchema",
    "TaskAssignmentUpdateSchema", # Додано
    "TaskAssignmentSchema",
    # TaskCompletion schemas
    "TaskCompletionBaseSchema",
    "TaskCompletionCreateSchema",
    "TaskCompletionUpdateSchema",
    "TaskCompletionSchema",
    # TaskReview schemas
    "TaskReviewBaseSchema",
    "TaskReviewCreateSchema",
    "TaskReviewUpdateSchema",
    "TaskReviewSchema",
]

logger.debug("Ініціалізація пакету схем Pydantic `tasks`...")
