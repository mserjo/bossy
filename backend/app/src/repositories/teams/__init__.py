# backend/app/src/repositories/teams/__init__.py
# -*- coding: utf-8 -*-
"""
Пакет репозиторіїв для сутностей, пов'язаних з командами.
"""

from .team import TeamRepository, team_repository
from .membership import TeamMembershipRepository, team_membership_repository

__all__ = [
    "TeamRepository",
    "team_repository",
    "TeamMembershipRepository",
    "team_membership_repository",
]

from backend.app.src.config.logging import logger
logger.debug("Пакет 'repositories.teams' ініціалізовано.")
