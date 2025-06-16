# backend/app/src/repositories/auth/__init__.py
"""
Репозиторії для моделей автентифікації та авторизації програми Kudos.

Цей пакет містить класи репозиторіїв для кожної моделі, пов'язаної з
автентифікацією користувачів, керуванням їхніми сесіями та токенами оновлення.

Кожен репозиторій успадковує `BaseRepository` (або його похідні) та надає
спеціалізований інтерфейс для роботи з конкретною моделлю даних.
"""

from backend.app.src.repositories.auth.user_repository import UserRepository
from backend.app.src.repositories.auth.refresh_token_repository import RefreshTokenRepository
from backend.app.src.repositories.auth.session_repository import SessionRepository

__all__ = [
    "UserRepository",
    "RefreshTokenRepository",
    "SessionRepository",
]
