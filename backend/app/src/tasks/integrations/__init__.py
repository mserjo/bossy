# backend/app/src/tasks/integrations/__init__.py
# -*- coding: utf-8 -*-
"""
Підпакет для фонових завдань, пов'язаних з інтеграціями із зовнішніми системами.

Цей пакет містить завдання для синхронізації даних (наприклад, з календарями)
та обробки подій або повідомлень від зовнішніх сервісів (наприклад, месенджер-боти).

Модулі:
    calendar.py: Завдання для синхронізації з календарями (Google Calendar, Outlook Calendar).
    messenger_processing.py: Завдання для обробки вхідних повідомлень/команд від месенджерів.

Імпорт основних класів завдань:
    З .calendar імпортується SyncCalendarTask.
    З .messenger_processing імпортується ProcessIncomingMessageTask.
"""

from backend.app.src.tasks.integrations.calendar import SyncCalendarTask
from backend.app.src.tasks.integrations.messenger_processing import ProcessIncomingMessageTask
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

__all__ = [
    'SyncCalendarTask',
    'ProcessIncomingMessageTask',
]

logger.info("Підпакет 'tasks.integrations' ініціалізовано.")
