# backend/app/src/schemas/tasks/__init__.py
"""
Pydantic схеми для сутностей, пов'язаних із "Завданнями".

Цей пакет містить схеми Pydantic, що використовуються для валідації
даних запитів та формування відповідей API, які стосуються завдань (або подій),
їх призначень користувачам, записів про виконання та відгуків в програмі Kudos.
"""

# Схеми, пов'язані з Завданням (Task)
from .task import (
    TaskBaseSchema,
    TaskCreateSchema,
    TaskUpdateSchema,
    TaskSchema,
    TaskDetailSchema
)

# Схеми, пов'язані з Призначенням Завдання (TaskAssignment)
from .assignment import (
    TaskAssignmentBaseSchema,
    TaskAssignmentCreateSchema,
    TaskAssignmentUpdateSchema,
    TaskAssignmentSchema
)

# Схеми, пов'язані з Виконанням Завдання (TaskCompletion)
from .completion import (
    TaskCompletionBaseSchema,
    TaskCompletionCreateSchema,
    TaskCompletionUpdateSchema,
    TaskCompletionSchema
)

# Схеми, пов'язані з Відгуком на Завдання (TaskReview)
from .review import (
    TaskReviewBaseSchema,
    TaskReviewCreateSchema,
    TaskReviewUpdateSchema,
    TaskReviewSchema
)

# Модуль event.py для схем був видалений, оскільки Event як сутність була об'єднана з Task.

__all__ = [
    # Task schemas
    "TaskBaseSchema",
    "TaskCreateSchema",
    "TaskUpdateSchema",
    "TaskSchema",
    "TaskDetailSchema",
    # TaskAssignment schemas
    "TaskAssignmentBaseSchema",
    "TaskAssignmentCreateSchema",
    "TaskAssignmentUpdateSchema",
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
