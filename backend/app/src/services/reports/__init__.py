# backend/app/src/services/reports/__init__.py
# -*- coding: utf-8 -*-
"""
Пакет сервісів для сутностей, пов'язаних зі звітами.
"""

from .report_service import ReportService, report_service
# Можливо, будуть інші сервіси, наприклад, для генерації конкретних типів звітів.
# from .user_activity_report_generator import UserActivityReportGenerator (приклад)

__all__ = [
    "ReportService",
    "report_service",
]

from backend.app.src.config.logging import logger
logger.debug("Пакет 'services.reports' ініціалізовано.")
