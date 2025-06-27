# backend/app/src/api/v1/reports/__init__.py
# -*- coding: utf-8 -*-
"""
Ініціалізаційний файл для пакету ендпоінтів звітів API v1.

Цей пакет містить роутери для генерації та отримання різноманітних звітів.
"""

from fastapi import APIRouter

from backend.app.src.api.v1.reports.reports import router as main_reports_router

# Агрегуючий роутер для всіх ендпоінтів звітів.
reports_router = APIRouter()

# Підключаємо основний роутер звітів.
# Префікси для конкретних звітів (наприклад, /groups/{group_id}/reports)
# будуть визначені або тут при підключенні main_reports_router,
# або в самому main_reports_router для кожного ендпоінта,
# або при підключенні reports_router до головного v1_router.
# Наразі, шляхи в reports.py вже містять /groups/{group_id}/... або /generate/...
# Тому тут просто включаємо.
reports_router.include_router(main_reports_router)


__all__ = (
    "reports_router",
)
