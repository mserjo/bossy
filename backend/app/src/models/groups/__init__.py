# backend/app/src/models/groups/__init__.py
# -*- coding: utf-8 -*-
"""
Пакет моделей SQLAlchemy для сутностей, пов'язаних з "Групами".

Цей пакет містить моделі для представлення груп користувачів,
членства в групах, налаштувань груп, запрошень до груп та інших
аспектів, що стосуються функціоналу груп в програмі Kudos.

Моделі експортуються для зручного доступу з інших частин програми.
"""

from backend.app.src.models.groups.group import Group
from backend.app.src.models.groups.membership import GroupMembership
from backend.app.src.models.groups.settings import GroupSetting
from backend.app.src.models.groups.invitation import GroupInvitation

__all__ = [
    "Group",
    "GroupMembership",
    "GroupSetting",
    "GroupInvitation",
]

# Майбутні моделі, пов'язані з групами (наприклад, GroupJoinRequest, GroupEventLog),
# також можуть бути додані сюди для експорту.
