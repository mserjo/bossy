# backend/app/src/schemas/tasks/__init__.py
# -*- coding: utf-8 -*-
"""
Ініціалізаційний файл для пакету схем, пов'язаних із завданнями та подіями (`tasks`).

Цей файл робить доступними основні схеми завдань для імпорту з пакету
`backend.app.src.schemas.tasks`.

Приклад імпорту:
from backend.app.src.schemas.tasks import TaskSchema, TaskCreateSchema

Також цей файл може використовуватися для визначення змінної `__all__`,
яка контролює, що саме експортується при використанні `from . import *`.
"""

# Імпорт конкретних схем, пов'язаних із завданнями та подіями
from backend.app.src.schemas.tasks.task import (
    TaskSchema,
    TaskCreateSchema,
    TaskUpdateSchema,
    # TaskSimpleSchema, # Якщо буде створена
)
from backend.app.src.schemas.tasks.assignment import (
    TaskAssignmentSchema,
    TaskAssignmentCreateSchema,
    TaskAssignmentUpdateSchema,
)
from backend.app.src.schemas.tasks.completion import (
    TaskCompletionSchema,
    TaskCompletionStartSchema,
    TaskCompletionSubmitSchema,
    TaskCompletionReviewSchema,
)
from backend.app.src.schemas.tasks.dependency import (
    TaskDependencySchema,
    TaskDependencyCreateSchema,
    TaskDependencyUpdateSchema,
)
from backend.app.src.schemas.tasks.proposal import (
    TaskProposalSchema,
    TaskProposalCreateSchema,
    TaskProposalUpdateSchema,
)
from backend.app.src.schemas.tasks.review import (
    TaskReviewSchema,
    TaskReviewCreateSchema,
    TaskReviewUpdateSchema,
)

# Визначення змінної `__all__` для контролю публічного API пакету.
__all__ = [
    # Task Schemas
    "TaskSchema",
    "TaskCreateSchema",
    "TaskUpdateSchema",
    # "TaskSimpleSchema",

    # Task Assignment Schemas
    "TaskAssignmentSchema",
    "TaskAssignmentCreateSchema",
    "TaskAssignmentUpdateSchema",

    # Task Completion Schemas
    "TaskCompletionSchema",
    "TaskCompletionStartSchema", # Для початку виконання
    "TaskCompletionSubmitSchema", # Для подання на перевірку
    "TaskCompletionReviewSchema", # Для перевірки адміном

    # Task Dependency Schemas
    "TaskDependencySchema",
    "TaskDependencyCreateSchema",
    "TaskDependencyUpdateSchema",

    # Task Proposal Schemas
    "TaskProposalSchema",
    "TaskProposalCreateSchema",
    "TaskProposalUpdateSchema",

    # Task Review Schemas
    "TaskReviewSchema",
    "TaskReviewCreateSchema",
    "TaskReviewUpdateSchema",
]

# Виклик model_rebuild для схем, що використовують ForwardRef.
# Це потрібно робити після того, як всі залежні схеми визначені та імпортовані.
# Pydantic v2 може обробляти це автоматично.
# Якщо виникають помилки, розкоментуйте та налаштуйте.

# from typing import ForwardRef, List, Optional, Union, Any, Dict # Потрібні імпорти для контексту
# import uuid
# from datetime import datetime, timedelta
# from pydantic import BaseModel as PydanticBaseModel

# # Імітація імпортів для model_rebuild, якщо вони потрібні тут
# # (краще, щоб ці схеми вже були імпортовані вище)
# StatusSchema = ForwardRef('backend.app.src.schemas.dictionaries.status.StatusSchema')
# GroupSimpleSchema = ForwardRef('backend.app.src.schemas.groups.group.GroupSimpleSchema')
# UserPublicSchema = ForwardRef('backend.app.src.schemas.auth.user.UserPublicSchema')
# TeamSimpleSchema = ForwardRef('backend.app.src.schemas.teams.team.TeamSimpleSchema')
# TaskTypeSchema = ForwardRef('backend.app.src.schemas.dictionaries.task_type.TaskTypeSchema')

# # Класи, які використовують ForwardRef і можуть потребувати model_rebuild
# schemas_to_rebuild = [
#     TaskSchema,
#     TaskAssignmentSchema,
#     TaskCompletionSchema,
#     TaskDependencySchema,
#     TaskProposalSchema,
#     TaskReviewSchema,
# ]

# for schema in schemas_to_rebuild:
#     try:
#         # Для Pydantic v2, model_rebuild() може не бути потрібним так часто,
#         # але якщо є помилки NameError через ForwardRef, це може допомогти.
#         # Також, Pydantic v2 використовує `model_rebuild(force=True)` для примусового оновлення.
#         # schema.model_rebuild(force=True) # Або просто schema.model_rebuild()
#         pass # Pydantic v2 зазвичай справляється
#     except Exception as e:
#         print(f"Warning: Could not rebuild schema {schema.__name__}: {e}")
#         # Це може статися, якщо залежні схеми ще не повністю завантажені.
#         # Порядок імпорту та виклику model_rebuild важливий.

# Поки що залишаю без явних викликів `model_rebuild`, покладаючись на Pydantic v2.
# Якщо виникнуть проблеми з ForwardRef, їх потрібно буде додати.
# Головне, що всі схеми експортуються через `__all__`.
