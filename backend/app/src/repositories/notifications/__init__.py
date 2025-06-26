# backend/app/src/repositories/notifications/__init__.py
# -*- coding: utf-8 -*-
"""
Пакет репозиторіїв для сутностей, пов'язаних зі сповіщеннями.
Включає репозиторії для сповіщень, шаблонів сповіщень та статусів їх доставки.
"""

from .notification import NotificationRepository, notification_repository
from .template import NotificationTemplateRepository, notification_template_repository
from .delivery import NotificationDeliveryRepository, notification_delivery_repository

__all__ = [
    "NotificationRepository",
    "notification_repository",
    "NotificationTemplateRepository",
    "notification_template_repository",
    "NotificationDeliveryRepository",
    "notification_delivery_repository",
]

from backend.app.src.config.logging import logger
logger.debug("Пакет 'repositories.notifications' ініціалізовано.")
