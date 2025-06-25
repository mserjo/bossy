# backend/app/src/schemas/notifications/__init__.py
# -*- coding: utf-8 -*-
"""
Ініціалізаційний файл для пакету схем, пов'язаних зі сповіщеннями (`notifications`).

Цей файл робить доступними основні схеми сповіщень для імпорту з пакету
`backend.app.src.schemas.notifications`.

Приклад імпорту:
from backend.app.src.schemas.notifications import NotificationSchema, NotificationCreateSchema

Також цей файл може використовуватися для визначення змінної `__all__`,
яка контролює, що саме експортується при використанні `from . import *`.
"""

# Імпорт конкретних схем, пов'язаних зі сповіщеннями
from backend.app.src.schemas.notifications.notification import (
    NotificationSchema,
    NotificationCreateSchema,
    NotificationUpdateSchema,
    NotificationBulkReadSchema,
)
from backend.app.src.schemas.notifications.template import (
    NotificationTemplateSchema,
    NotificationTemplateCreateSchema,
    NotificationTemplateUpdateSchema,
)
from backend.app.src.schemas.notifications.delivery import (
    NotificationDeliverySchema,
    NotificationDeliveryCreateSchema,
    NotificationDeliveryUpdateSchema,
)

# Визначення змінної `__all__` для контролю публічного API пакету.
__all__ = [
    # Notification Schemas
    "NotificationSchema",
    "NotificationCreateSchema",
    "NotificationUpdateSchema",
    "NotificationBulkReadSchema",

    # Notification Template Schemas
    "NotificationTemplateSchema",
    "NotificationTemplateCreateSchema",
    "NotificationTemplateUpdateSchema",

    # Notification Delivery Schemas
    "NotificationDeliverySchema",
    "NotificationDeliveryCreateSchema",
    "NotificationDeliveryUpdateSchema",
]

# Виклик model_rebuild для схем, що використовують ForwardRef.
# from typing import ForwardRef, List, Optional, Union, Any, Dict # Потрібні імпорти для контексту
# import uuid
# from datetime import datetime, timedelta
# from pydantic import BaseModel as PydanticBaseModel

# schemas_to_rebuild = [
#     NotificationSchema,
#     NotificationTemplateSchema, # Може мати ForwardRef на Group або Status
#     NotificationDeliverySchema, # Може мати ForwardRef на NotificationSchema
# ]

# for schema in schemas_to_rebuild:
#     try:
#         # schema.model_rebuild(force=True) # Pydantic v2
#         pass # Pydantic v2 зазвичай справляється
#     except Exception as e:
#         print(f"Warning: Could not rebuild schema {schema.__name__}: {e}")

# Поки що залишаю без явних викликів `model_rebuild`.
# Головне, що всі схеми експортуються через `__all__`.

# Виклик model_rebuild для схем, що містять ForwardRef
NotificationSchema.model_rebuild()
NotificationTemplateSchema.model_rebuild()
NotificationDeliverySchema.model_rebuild()

# Все виглядає добре.
