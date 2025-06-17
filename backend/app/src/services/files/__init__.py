# backend/app/src/services/files/__init__.py
"""
Ініціалізаційний файл для модуля сервісів, пов'язаних з файлами.

Цей модуль реекспортує основні класи сервісів для управління записами файлів,
завантаженням файлів та управлінням аватарами користувачів.
"""

# Явний імпорт сервісів для кращої читабельності та статичного аналізу
from backend.app.src.services.files.file_record_service import FileRecordService
from backend.app.src.services.files.file_upload_service import FileUploadService
from backend.app.src.services.files.user_avatar_service import UserAvatarService
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

__all__ = [
    "FileRecordService",
    "FileUploadService",
    "UserAvatarService",
]

logger.info(f"Сервіси файлів експортують: {__all__}")
