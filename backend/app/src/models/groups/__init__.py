# backend/app/src/models/groups/__init__.py
# -*- coding: utf-8 -*-
"""Пакет моделей SQLAlchemy для сутностей, пов'язаних з "Групами".

Цей пакет містить моделі даних для представлення груп користувачів,
членства в цих групах, специфічних налаштувань для кожної групи,
системи запрошень до груп та інших аспектів, що стосуються
функціоналу груп в додатку.

Моделі з цього пакету експортуються для використання в сервісному шарі,
API ендпоінтах та інших частинах додатку, що реалізують логіку роботи з групами.
"""

# Імпорт моделей з відповідних файлів цього пакету.
from backend.app.src.models.groups.group import Group
from backend.app.src.models.groups.membership import GroupMembership
from backend.app.src.models.groups.settings import GroupSetting
from backend.app.src.models.groups.invitation import GroupInvitation
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

# Визначаємо, які символи будуть експортовані при використанні `from backend.app.src.models.groups import *`.
__all__ = [
    "Group",
    "GroupMembership",
    "GroupSetting",
    "GroupInvitation",
]

logger.debug("Ініціалізація пакету моделей `groups`...")

# Коментар щодо можливого розширення:
# В майбутньому сюди можуть бути додані інші моделі, пов'язані з групами,
# наприклад, для запитів на приєднання до групи (GroupJoinRequestModel)
# або для логування подій, специфічних для групи (GroupEventLogModel).
