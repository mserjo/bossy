# backend/app/src/schemas/groups/__init__.py
# -*- coding: utf-8 -*-
"""Pydantic схеми для сутностей, пов'язаних з "Групами".

Цей пакет містить схеми Pydantic, що використовуються для валідації
даних запитів та формування відповідей API, які стосуються груп (`Group...Schema`),
членства в них (`GroupMembership...Schema`), їх налаштувань (`GroupSetting...Schema`)
та запрошень до груп (`GroupInvitation...Schema`).

Кожен підмодуль зазвичай визначає набір схем: Base, Create, Update, Response.
"""

# Імпорт централізованого логера
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

# Схеми, пов'язані з Групою (очікувані назви згідно з завданням)
from backend.app.src.schemas.groups.group import (
    GroupBaseSchema,
    GroupCreateSchema,
    GroupUpdateSchema,
    GroupSchema,
    GroupDetailSchema
)

# Схеми, пов'язані з Членством в Групі
from backend.app.src.schemas.groups.membership import (
    GroupMembershipBaseSchema,
    GroupMembershipCreateSchema,
    GroupMembershipUpdateSchema,
    GroupMembershipSchema # Використовуємо фактичну назву
)

# Схеми, пов'язані з Налаштуваннями Групи
from backend.app.src.schemas.groups.settings import (
    GroupSettingBaseSchema,
    GroupSettingCreateSchema,
    GroupSettingUpdateSchema,
    GroupSettingSchema # Використовуємо фактичну назву
)

# Схеми, пов'язані із Запрошеннями до Групи
from backend.app.src.schemas.groups.invitation import (
    GroupInvitationBaseSchema,
    GroupInvitationCreateSchema,
    GroupInvitationUpdateSchema,
    GroupInvitationSchema,
    GroupInvitationAcceptSchema
)

__all__ = [
    # Group schemas
    "GroupBaseSchema",
    "GroupCreateSchema",
    "GroupUpdateSchema",
    "GroupSchema",
    "GroupDetailSchema",
    # GroupMembership schemas
    "GroupMembershipBaseSchema",
    "GroupMembershipCreateSchema",
    "GroupMembershipUpdateSchema",
    "GroupMembershipSchema",
    # GroupSetting schemas
    "GroupSettingBaseSchema",
    "GroupSettingCreateSchema",
    "GroupSettingUpdateSchema",
    "GroupSettingSchema",
    # GroupInvitation schemas
    "GroupInvitationBaseSchema",
    "GroupInvitationCreateSchema",
    "GroupInvitationUpdateSchema",
    "GroupInvitationSchema",
    "GroupInvitationAcceptSchema",
]

logger.debug("Ініціалізація пакету схем Pydantic `groups`...")
