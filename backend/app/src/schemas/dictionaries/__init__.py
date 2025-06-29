# backend/app/src/schemas/dictionaries/__init__.py
# -*- coding: utf-8 -*-
"""
Ініціалізаційний файл для пакету схем довідників (`dictionaries`).

Цей файл робить доступними основні схеми довідників для імпорту з пакету
`backend.app.src.schemas.dictionaries`. Це спрощує імпорти в інших частинах проекту.

Приклад імпорту:
from backend.app.src.schemas.dictionaries import StatusSchema, StatusCreateSchema

Також цей файл може використовуватися для визначення змінної `__all__`,
яка контролює, що саме експортується при використанні `from . import *`.
"""

# Імпорт базових схем для довідників
from backend.app.src.schemas.dictionaries.base_dict import (
    BaseDictSchema,
    BaseDictCreateSchema,
    BaseDictUpdateSchema,
)

# Імпорт конкретних схем довідників
from backend.app.src.schemas.dictionaries.status import (
    StatusSchema,
    StatusCreateSchema,
    StatusUpdateSchema,
)
from backend.app.src.schemas.dictionaries.user_role import (
    UserRoleSchema,
    UserRoleCreateSchema,
    UserRoleUpdateSchema,
)
from backend.app.src.schemas.dictionaries.group_type import (
    GroupTypeSchema,
    GroupTypeCreateSchema,
    GroupTypeUpdateSchema,
)
from backend.app.src.schemas.dictionaries.task_type import (
    TaskTypeSchema,
    TaskTypeCreateSchema,
    TaskTypeUpdateSchema,
)
from backend.app.src.schemas.dictionaries.bonus_type import (
    BonusTypeSchema,
    BonusTypeCreateSchema,
    BonusTypeUpdateSchema,
)
from backend.app.src.schemas.dictionaries.integration_type import (
    IntegrationTypeSchema,
    IntegrationTypeCreateSchema,
    IntegrationTypeUpdateSchema,
)
from backend.app.src.schemas.dictionaries.user_type import ( # Додано імпорт для UserType
    UserTypeSchema,
    UserTypeCreateSchema,
    UserTypeUpdateSchema,
)

# Визначення змінної `__all__` для контролю публічного API пакету.
# Включаємо як схеми для читання, так і для створення/оновлення.
__all__ = [
    # Base dictionary schemas
    "BaseDictSchema",
    "BaseDictCreateSchema",
    "BaseDictUpdateSchema",

    # Status schemas
    "StatusSchema",
    "StatusCreateSchema",
    "StatusUpdateSchema",

    # UserRole schemas
    "UserRoleSchema",
    "UserRoleCreateSchema",
    "UserRoleUpdateSchema",

    # GroupType schemas
    "GroupTypeSchema",
    "GroupTypeCreateSchema",
    "GroupTypeUpdateSchema",

    # TaskType schemas
    "TaskTypeSchema",
    "TaskTypeCreateSchema",
    "TaskTypeUpdateSchema",

    # BonusType schemas
    "BonusTypeSchema",
    "BonusTypeCreateSchema",
    "BonusTypeUpdateSchema",

    # IntegrationType schemas
    "IntegrationTypeSchema",
    "IntegrationTypeCreateSchema",
    "IntegrationTypeUpdateSchema",

    # UserType schemas # Додано експорт для UserType
    "UserTypeSchema",
    "UserTypeCreateSchema",
    "UserTypeUpdateSchema",
]

# TODO: Переконатися, що всі необхідні схеми довідників створені та включені до `__all__`.
# На даний момент включені всі схеми, заплановані для створення в цьому пакеті.
# Це забезпечує консистентний спосіб доступу до схем довідників.
