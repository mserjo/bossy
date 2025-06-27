# backend/app/src/services/notifications/__init__.py
# -*- coding: utf-8 -*-
"""
Пакет сервісів для сутностей, пов'язаних зі сповіщеннями.
Включає сервіси для управління сповіщеннями, їх шаблонами та статусами доставки.
"""

from .notification_service import NotificationService, notification_service
from .notification_template_service import NotificationTemplateService, notification_template_service
from .notification_delivery_service import NotificationDeliveryService, notification_delivery_service
# from .notification_composer_service import NotificationComposerService, notification_composer_service # Можливий сервіс для композиції сповіщень
# from .notification_sender_service import NotificationSenderService, notification_sender_service # Можливий сервіс для відправки

__all__ = [
    "NotificationService",
    "notification_service",
    "NotificationTemplateService",
    "notification_template_service",
    "NotificationDeliveryService",
    "notification_delivery_service",
    # "NotificationComposerService",
    # "notification_composer_service",
    # "NotificationSenderService",
    # "notification_sender_service",
]

from backend.app.src.config.logging import logger
logger.debug("Пакет 'services.notifications' ініціалізовано.")
