# backend/app/src/repositories/files/__init__.py
"""
Репозиторії для моделей, пов'язаних з "Файлами", в програмі Kudos.

Цей пакет містить класи репозиторіїв для кожної моделі, що стосується
управління файлами, їх метаданими та специфічним використанням,
наприклад, як аватари користувачів.

Кожен репозиторій успадковує `BaseRepository` та надає спеціалізований
інтерфейс для роботи з конкретною моделлю даних.
"""

from .file_record_repository import FileRecordRepository
from .user_avatar_repository import UserAvatarRepository

# Можливо, в майбутньому тут будуть репозиторії для інших типів файлів,
# якщо вони матимуть власну логіку (наприклад, GroupIconRepository).

__all__ = [
    "FileRecordRepository",
    "UserAvatarRepository",
]
