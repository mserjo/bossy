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

# Імпорт централізованого логера
from backend.app.src.config import logger

# Імпорт моделей з відповідних файлів цього пакету, використовуючи нову конвенцію імен.
# Припускаємо, що класи в файлах будуть перейменовані на *Model.
from backend.app.src.models.notifications.template import NotificationTemplateModel
from backend.app.src.models.notifications.notification import NotificationModel
from backend.app.src.models.notifications.delivery import NotificationDeliveryAttemptModel

# Визначаємо, які символи будуть експортовані при використанні `from backend.app.src.models.notifications import *`.
__all__ = [
    "NotificationTemplateModel",
    "NotificationModel",
    "NotificationDeliveryAttemptModel",
]

logger.debug("Ініціалізація пакету моделей `notifications`...")

# Коментар щодо можливого розширення:
# В майбутньому сюди можуть бути додані інші моделі, пов'язані зі сповіщеннями,
# наприклад, для налаштувань сповіщень користувача (UserNotificationPreferenceModel)
# або для підписок на певні типи сповіщень.
