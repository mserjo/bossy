# backend/app/src/services/teams/__init__.py
# -*- coding: utf-8 -*-
"""
Пакет сервісів для сутностей, пов'язаних з командами.
Включає сервіси для управління командами та членством в них.
"""

from .team_service import TeamService, team_service
from .team_membership_service import TeamMembershipService, team_membership_service

__all__ = [
    "TeamService",
    "team_service",
    "TeamMembershipService",
    "team_membership_service",
]

from backend.app.src.config.logging import logger
logger.debug("Пакет 'services.teams' ініціалізовано.")
