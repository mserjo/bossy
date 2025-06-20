# backend/app/src/tasks/notifications/__init__.py
# -*- coding: utf-8 -*-
"""
Підпакет для фонових завдань, пов'язаних з відправкою сповіщень.

Цей пакет містить завдання для асинхронної відправки сповіщень
через різні канали, такі як електронна пошта, SMS, месенджери тощо.

Модулі:
    email.py: Завдання для відправки email сповіщень.
    sms.py: Завдання для відправки SMS сповіщень.
    messenger.py: Завдання для відправки сповіщень через месенджери.

Імпорт основних класів завдань:
    З .email імпортується SendEmailTask.
    З .sms імпортується SendSmsTask.
    З .messenger імпортується SendMessengerNotificationTask.
"""

from backend.app.src.tasks.notifications.email import SendEmailTask
from backend.app.src.tasks.notifications.sms import SendSmsTask
from backend.app.src.tasks.notifications.messenger import SendMessengerNotificationTask
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

__all__ = [
    'SendEmailTask',
    'SendSmsTask',
    'SendMessengerNotificationTask',
]

logger.info("Підпакет 'tasks.notifications' ініціалізовано.")
