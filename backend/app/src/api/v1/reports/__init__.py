# backend/app/src/api/v1/reports/__init__.py
# -*- coding: utf-8 -*-
"""
Ініціалізаційний файл для пакету 'reports' API v1.

Цей пакет містить ендпоінти для генерації та отримання звітів
в системі через API v1. Звіти можуть стосуватися різних аспектів системи.
Очікується, що основна логіка ендпоінтів звітів буде в файлі `reports.py`.

Цей файл робить каталог 'reports' пакетом Python та експортує
роутер `router` для ендпоінтів звітів.
"""

from fastapi import APIRouter

# TODO: Імпортувати роутер з файлу `reports.py`, коли він буде створений.
# from backend.app.src.api.v1.reports.reports import router as reports_module_router

# Роутер для ендпоінтів звітів API v1.
router = APIRouter(tags=["v1 :: Reports"])

# TODO: Розкоментувати підключення роутера, коли він буде готовий.
# router.include_router(reports_module_router)
# Префікс для звітів (наприклад, `/reports` або `/groups/{group_id}/reports`)
# буде встановлений при підключенні цього `router` в `v1/router.py`
# або в `groups/__init__.py`.

# Експорт роутера.
__all__ = [
    "router",
]

# TODO: Узгодити назву експортованого роутера ("router") з імпортом
# в `backend.app.src.api.v1.router.py` (очікує `reports_v1_router`).
