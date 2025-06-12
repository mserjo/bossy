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
from backend.app.src.config import logger

# Схеми, пов'язані з Групою (очікувані назви згідно з завданням)
from backend.app.src.schemas.groups.group import (
    GroupBaseSchema,
    GroupCreateSchema,
    GroupUpdateSchema,
    GroupResponseSchema
    # GroupDetailResponseSchema # Якщо буде окрема деталізована схема
)

# Схеми, пов'язані з Членством в Групі
from backend.app.src.schemas.groups.membership import (
    GroupMembershipBaseSchema,
    GroupMembershipCreateSchema,
    GroupMembershipUpdateSchema,
    GroupMembershipResponseSchema
)

# Схеми, пов'язані з Налаштуваннями Групи
from backend.app.src.schemas.groups.settings import (
    GroupSettingBaseSchema,
    GroupSettingCreateSchema, # Додано згідно завдання
    GroupSettingUpdateSchema,
    GroupSettingResponseSchema
)

# Схеми, пов'язані із Запрошеннями до Групи
from backend.app.src.schemas.groups.invitation import (
    GroupInvitationBaseSchema,
    GroupInvitationCreateSchema,
    GroupInvitationUpdateSchema,
    GroupInvitationResponseSchema
    # GroupInvitationAcceptSchema # Якщо це окрема схема, а не частина Update/сервісу
)

__all__ = [
    # Group schemas
    "GroupBaseSchema",
    "GroupCreateSchema",
    "GroupUpdateSchema",
    "GroupResponseSchema",
    # "GroupDetailResponseSchema",
    # GroupMembership schemas
    "GroupMembershipBaseSchema",
    "GroupMembershipCreateSchema",
    "GroupMembershipUpdateSchema",
    "GroupMembershipResponseSchema",
    # GroupSetting schemas
    "GroupSettingBaseSchema",
    "GroupSettingCreateSchema",
    "GroupSettingUpdateSchema",
    "GroupSettingResponseSchema",
    # GroupInvitation schemas
    "GroupInvitationBaseSchema",
    "GroupInvitationCreateSchema",
    "GroupInvitationUpdateSchema",
    "GroupInvitationResponseSchema",
    # "GroupInvitationAcceptSchema",
]

logger.debug("Ініціалізація пакету схем Pydantic `groups`...")
