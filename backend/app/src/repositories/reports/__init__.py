# backend/app/src/repositories/reports/__init__.py
# -*- coding: utf-8 -*-
"""
Пакет репозиторіїв для сутностей, пов'язаних зі звітами.
"""

from .report import ReportRepository, report_repository

__all__ = [
    "ReportRepository",
    "report_repository",
]

from backend.app.src.config.logging import logger
logger.debug("Пакет 'repositories.reports' ініціалізовано.")
