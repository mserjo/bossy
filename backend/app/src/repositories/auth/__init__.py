# backend/app/src/repositories/auth/__init__.py
# -*- coding: utf-8 -*-
"""
Пакет репозиторіїв для сутностей, пов'язаних з автентифікацією та користувачами.

Цей пакет містить класи репозиторіїв для роботи з моделями `UserModel`,
`RefreshTokenModel`, `SessionModel` тощо.
"""

from .user import UserRepository, user_repository
from .token import RefreshTokenRepository, refresh_token_repository
from .session import SessionRepository, session_repository

__all__ = [
    "UserRepository",
    "user_repository",
    "RefreshTokenRepository",
    "refresh_token_repository",
    "SessionRepository",
    "session_repository",
]

from backend.app.src.config.logging import logger
logger.debug("Пакет 'repositories.auth' ініціалізовано.")
