# backend/app/src/models/groups/__init__.py
"""
Пакет моделей SQLAlchemy для сутностей, пов'язаних з "Групами".

Цей пакет містить моделі для представлення груп користувачів,
членства в групах, налаштувань груп, запрошень до груп та інших
аспектів, що стосуються функціоналу груп в програмі Kudos.

Моделі експортуються для зручного доступу з інших частин програми.
"""

from .group import Group
from .membership import GroupMembership
from .settings import GroupSetting
from .invitation import GroupInvitation

__all__ = [
    "Group",
    "GroupMembership",
    "GroupSetting",
    "GroupInvitation",
]

# Майбутні моделі, пов'язані з групами (наприклад, GroupJoinRequest, GroupEventLog),
# також можуть бути додані сюди для експорту.
