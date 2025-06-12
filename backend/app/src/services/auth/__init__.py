# backend/app/src/services/auth/__init__.py
"""
Ініціалізаційний файл для модуля сервісів автентифікації.

Цей модуль реекспортує основні класи сервісів, пов'язаних з автентифікацією
та управлінням користувачами, токенами, сесіями та паролями.
"""

from backend.app.src.config import logger

# Явний імпорт сервісів для кращої читабельності та статичного аналізу
from backend.app.src.services.auth.user import UserService
from backend.app.src.services.auth.token import TokenService
from backend.app.src.services.auth.password import PasswordService
from backend.app.src.services.auth.session import UserSessionService

__all__ = [
    "UserService",
    "TokenService",
    "PasswordService",
    "UserSessionService",
]

logger.info(f"Сервіси автентифікації експортують: {__all__}")
