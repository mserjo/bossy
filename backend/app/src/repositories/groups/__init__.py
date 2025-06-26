# backend/app/src/repositories/groups/__init__.py
# -*- coding: utf-8 -*-
"""
Пакет репозиторіїв для сутностей, пов'язаних з групами.

Цей пакет містить класи репозиторіїв для роботи з моделями `GroupModel`,
`GroupSettingsModel`, `GroupMembershipModel`, `GroupInvitationModel`,
`GroupTemplateModel`, `PollModel` та пов'язаними з ними.
"""

from .group import GroupRepository, group_repository
from .settings import GroupSettingsRepository, group_settings_repository
from .membership import GroupMembershipRepository, group_membership_repository
from .invitation import GroupInvitationRepository, group_invitation_repository
from .template import GroupTemplateRepository, group_template_repository
from .poll import PollRepository, poll_repository
# from .poll_option import PollOptionRepository, poll_option_repository # Може бути частиною PollRepository
# from .poll_vote import PollVoteRepository, poll_vote_repository     # Може бути частиною PollRepository


__all__ = [
    "GroupRepository",
    "group_repository",
    "GroupSettingsRepository",
    "group_settings_repository",
    "GroupMembershipRepository",
    "group_membership_repository",
    "GroupInvitationRepository",
    "group_invitation_repository",
    "GroupTemplateRepository",
    "group_template_repository",
    "PollRepository",
    "poll_repository",
]

from backend.app.src.config.logging import logger
logger.debug("Пакет 'repositories.groups' ініціалізовано.")
