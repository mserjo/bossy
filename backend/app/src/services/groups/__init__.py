# backend/app/src/services/groups/__init__.py
# -*- coding: utf-8 -*-
"""
Пакет сервісів для сутностей, пов'язаних з групами.

Включає сервіси для управління групами, їх налаштуваннями, членством,
запрошеннями, шаблонами груп та опитуваннями.
"""

from .group_service import GroupService, group_service
from .group_settings_service import GroupSettingsService, group_settings_service
from .group_membership_service import GroupMembershipService, group_membership_service
from .group_invitation_service import GroupInvitationService, group_invitation_service
from .group_template_service import GroupTemplateService, group_template_service
from .poll_service import PollService, poll_service

__all__ = [
    "GroupService",
    "group_service",
    "GroupSettingsService",
    "group_settings_service",
    "GroupMembershipService",
    "group_membership_service",
    "GroupInvitationService",
    "group_invitation_service",
    "GroupTemplateService",
    "group_template_service",
    "PollService",
    "poll_service",
]

from backend.app.src.config.logging import logger
logger.debug("Пакет 'services.groups' ініціалізовано.")
