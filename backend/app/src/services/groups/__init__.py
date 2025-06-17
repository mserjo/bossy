# backend/app/src/services/groups/__init__.py
"""
Ініціалізаційний файл для модуля сервісів, пов'язаних з групами.

Цей модуль реекспортує основні класи сервісів для управління групами,
членством, налаштуваннями груп та запрошеннями.
"""

# Явний імпорт сервісів для кращої читабельності та статичного аналізу
from backend.app.src.services.groups.group import GroupService
from backend.app.src.services.groups.settings import GroupSettingService # Уточнити назву класу, якщо потрібно
from backend.app.src.services.groups.membership import GroupMembershipService
from backend.app.src.services.groups.invitation import GroupInvitationService
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

__all__ = [
    "GroupService",
    "GroupSettingService",    # Уточнити фактичну назву класу у файлі settings.py
    "GroupMembershipService",
    "GroupInvitationService",
]

logger.info(f"Сервіси груп експортують: {__all__}")
