# backend/app/src/models/notifications/__init__.py
# -*- coding: utf-8 -*-
"""Пакет моделей SQLAlchemy для сутностей, пов'язаних зі сповіщеннями.

Цей пакет містить моделі даних для управління шаблонами сповіщень
(`NotificationTemplateModel`), самими сповіщеннями, що надсилаються
користувачам (`NotificationModel`), та записами про спроби доставки
цих сповіщень через різні канали (`NotificationDeliveryAttemptModel`).

Моделі з цього пакету експортуються для використання в сервісному шарі,
API ендпоінтах та інших частинах додатку, що реалізують логіку
створення, надсилання та відстеження сповіщень.
"""

# Імпорт моделей з відповідних файлів цього пакету.
from backend.app.src.models.notifications.template import NotificationTemplate
from backend.app.src.models.notifications.notification import Notification
from backend.app.src.models.notifications.delivery import NotificationDeliveryAttempt
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

# Визначаємо, які символи будуть експортовані при використанні `from backend.app.src.models.notifications import *`.
__all__ = [
    "NotificationTemplate",
    "Notification",
    "NotificationDeliveryAttempt",
]

logger.debug("Ініціалізація пакету моделей `notifications`...")

# Коментар щодо можливого розширення:
# В майбутньому сюди можуть бути додані інші моделі, пов'язані зі сповіщеннями,
# наприклад, для налаштувань сповіщень користувача (UserNotificationPreferenceModel)
# або для підписок на певні типи сповіщень.
