# backend/app/src/schemas/teams/__init__.py
# -*- coding: utf-8 -*-
"""
Ініціалізаційний файл для пакету схем, пов'язаних з командами (`teams`).

Цей файл робить доступними основні схеми команд для імпорту з пакету
`backend.app.src.schemas.teams`.

Приклад імпорту:
from backend.app.src.schemas.teams import TeamSchema, TeamCreateSchema

Також цей файл може використовуватися для визначення змінної `__all__`,
яка контролює, що саме експортується при використанні `from . import *`.
"""

# Імпорт конкретних схем, пов'язаних з командами
from backend.app.src.schemas.teams.team import (
    TeamSchema,
    TeamSimpleSchema,
    TeamCreateSchema,
    TeamUpdateSchema,
)
from backend.app.src.schemas.teams.membership import (
    TeamMembershipSchema,
    TeamMembershipCreateSchema,
    TeamMembershipUpdateSchema,
)

# Визначення змінної `__all__` для контролю публічного API пакету.
__all__ = [
    # Team Schemas
    "TeamSchema",
    "TeamSimpleSchema",
    "TeamCreateSchema",
    "TeamUpdateSchema",

    # Team Membership Schemas
    "TeamMembershipSchema",
    "TeamMembershipCreateSchema",
    "TeamMembershipUpdateSchema",
]

# Виклик model_rebuild для схем, що використовують ForwardRef.
# from typing import ForwardRef, List, Optional, Union, Any, Dict # Потрібні імпорти для контексту
# import uuid
# from datetime import datetime, timedelta
# from pydantic import BaseModel as PydanticBaseModel

# schemas_to_rebuild = [
#     TeamSchema,
#     TeamMembershipSchema,
# ]

# for schema in schemas_to_rebuild:
#     try:
#         # schema.model_rebuild(force=True) # Pydantic v2
#         pass # Pydantic v2 зазвичай справляється
#     except Exception as e:
#         print(f"Warning: Could not rebuild schema {schema.__name__}: {e}")

# Поки що залишаю без явних викликів `model_rebuild`.
# Якщо виникнуть проблеми з ForwardRef, їх потрібно буде додати.
# Головне, що всі схеми експортуються через `__all__`.
