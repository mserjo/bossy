# backend/app/src/repositories/files/__init__.py
# -*- coding: utf-8 -*-
"""
Пакет репозиторіїв для сутностей, пов'язаних з файлами.
"""

from .file import FileRepository, file_repository
from .avatar import AvatarRepository, avatar_repository

__all__ = [
    "FileRepository",
    "file_repository",
    "AvatarRepository",
    "avatar_repository",
]

from backend.app.src.config.logging import logger
logger.debug("Пакет 'repositories.files' ініціалізовано.")
