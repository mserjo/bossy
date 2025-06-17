# backend/app/src/models/files/__init__.py
# -*- coding: utf-8 -*-
"""Пакет моделей SQLAlchemy для сутностей, пов'язаних з файлами.

Цей пакет містить моделі для представлення записів про файли,
завантажені в систему (`FileRecordModel`), та їх специфічне використання,
наприклад, як аватари користувачів (`UserAvatarModel`).

Моделі з цього пакету експортуються для зручного доступу з інших частин програми,
наприклад, для визначення зв'язків у моделі користувача або при обробці
завантаження та доступу до файлів.
"""

# Імпорт моделей з відповідних файлів цього пакету.
from backend.app.src.models.files.file import FileRecord
from backend.app.src.models.files.avatar import UserAvatar
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

# TODO: В майбутньому тут можуть бути інші моделі, пов'язані з файлами,
#       наприклад, GroupIconModel, RewardIconModel, якщо вони матимуть
#       власні таблиці та логіку, відмінну від загального FileRecordModel.
#       Необхідно буде їх також імпортувати та додати до __all__.

# Визначаємо, які символи будуть експортовані при використанні `from backend.app.src.models.files import *`.
__all__ = [
    "FileRecord",
    "UserAvatar",
]

logger.debug("Ініціалізація пакету моделей `files`...")
