# backend/app/src/schemas/groups/__init__.py
"""
Pydantic схеми для сутностей, пов'язаних з "Групами".

Цей пакет містить схеми Pydantic, що використовуються для валідації
даних запитів та формування відповідей API, які стосуються груп,
членства в них, їх налаштувань та запрошень до груп в програмі Kudos.
"""

# Схеми, пов'язані з Групою
from .group import (
    GroupBaseSchema,
    GroupCreateSchema,
    GroupUpdateSchema,
    GroupSchema,
    GroupDetailSchema
)

# Схеми, пов'язані з Членством в Групі
from .membership import (
    GroupMembershipBaseSchema,
    GroupMembershipCreateSchema,
    GroupMembershipUpdateSchema,
    GroupMembershipSchema
)

# Схеми, пов'язані з Налаштуваннями Групи
from .settings import (
    GroupSettingBaseSchema,
    GroupSettingUpdateSchema,
    GroupSettingSchema
)

# Схеми, пов'язані із Запрошеннями до Групи
from .invitation import (
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
    "GroupSettingUpdateSchema",
    "GroupSettingSchema",
    # GroupInvitation schemas
    "GroupInvitationBaseSchema",
    "GroupInvitationCreateSchema",
    "GroupInvitationUpdateSchema",
    "GroupInvitationSchema",
    "GroupInvitationAcceptSchema",
]
