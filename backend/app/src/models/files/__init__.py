# backend/app/src/models/files/__init__.py
# -*- coding: utf-8 -*-
"""
Пакет моделей SQLAlchemy для сутностей, пов'язаних з "Файлами".

Цей пакет містить моделі для представлення записів про файли,
завантажені в систему, та їх специфічне використання, наприклад,
як аватари користувачів.

Моделі експортуються для зручного доступу з інших частин програми.
"""

from backend.app.src.models.files.file import FileRecord
from backend.app.src.models.files.avatar import UserAvatar
# В майбутньому тут можуть бути інші моделі, пов'язані з файлами,
# наприклад, GroupIconRecord, RewardIconRecord, якщо вони матимуть
# власні таблиці та логіку, відмінну від загального FileRecord.

__all__ = [
    "FileRecord",
    "UserAvatar",
]
