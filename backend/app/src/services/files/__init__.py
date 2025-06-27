# backend/app/src/services/files/__init__.py
# -*- coding: utf-8 -*-
"""
Пакет сервісів для сутностей, пов'язаних з файлами.
Включає сервіси для управління файлами та аватарами.
"""

from .file_service import FileService, file_service
from .avatar_service import AvatarService, avatar_service

__all__ = [
    "FileService",
    "file_service",
    "AvatarService",
    "avatar_service",
]

from backend.app.src.config.logging import logger
logger.debug("Пакет 'services.files' ініціалізовано.")
