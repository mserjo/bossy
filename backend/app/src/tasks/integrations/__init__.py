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

# На даний момент, відповідні класи завдань ще не створені в модулях,
# тому імпорти будуть додані або розкоментовані, коли класи будуть реалізовані.

from .calendar import SyncCalendarTask
from .messenger_processing import ProcessIncomingMessageTask

__all__ = [
    'SyncCalendarTask',
    'ProcessIncomingMessageTask',
]

import logging

logger = logging.getLogger(__name__)
logger.info("Підпакет 'tasks.integrations' ініціалізовано.")
