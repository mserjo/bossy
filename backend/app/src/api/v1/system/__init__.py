# backend/app/src/api/v1/system/__init__.py
# -*- coding: utf-8 -*-
"""
Ініціалізаційний файл для пакету 'system' API v1.

Цей пакет об'єднує ендпоінти, пов'язані з системними функціями для API v1.
Сюди входять:
- Перевірка стану системи (`health.py`).
- Ініціалізація початкових даних (`init_data.py`).
- Управління налаштуваннями системи (`settings.py`) для супер-адміністратора.
- Управління системними завданнями cron (`cron_task.py`).
- Доступ до даних моніторингу системи (`monitoring.py`).

Цей файл робить каталог 'system' пакетом Python. Він також агрегує
окремі роутери з модулів цього пакету в єдиний `system_router`,
який потім експортується для використання в головному роутері API v1
(`backend.app.src.api.v1.router.py`).
"""

from fastapi import APIRouter

# Імпорт окремих роутерів з модулів цього пакету.
# TODO: Розкоментувати, коли відповідні файли та роутери в них будуть створені.
# from backend.app.src.api.v1.system.health import router as health_router
# from backend.app.src.api.v1.system.init_data import router as init_data_router
# from backend.app.src.api.v1.system.settings import router as system_settings_router
# from backend.app.src.api.v1.system.cron_task import router as cron_task_router
# from backend.app.src.api.v1.system.monitoring import router as monitoring_router

# Агрегуючий роутер для всіх системних ендпоінтів API v1.
# Теги, визначені тут, будуть застосовані до всіх підключених роутерів,
# якщо вони не мають власних тегів, або можуть доповнювати їх.
router = APIRouter(tags=["v1 :: System"])

# Підключення окремих роутерів до агрегуючого роутера.
# Префікси тут відносні до префіксу, з яким `system_router` буде підключений
# в `backend.app.src.api.v1.router.py` (наприклад, `/system`).

# TODO: Розкоментувати підключення, коли роутери будуть готові.
# router.include_router(health_router) # Зазвичай /health, без додаткового префіксу в межах /system
# router.include_router(init_data_router, prefix="/init-data")
# router.include_router(system_settings_router, prefix="/settings")
# router.include_router(cron_task_router, prefix="/cron-tasks")
# router.include_router(monitoring_router, prefix="/monitoring")

# Експорт агрегованого роутера.
__all__ = [
    "router",
]

# TODO: Переконатися, що назва експортованого роутера (тут "router")
# узгоджується з тим, як він імпортується в `backend.app.src.api.v1.router.py`
# (там очікується `system_v1_router`). Можливо, варто перейменувати "router" на "system_v1_router" тут
# або змінити імпорт там. Для консистентності, якщо цей файл експортує "router",
# то імпорт має бути `from .system import router as system_v1_router`.
# Поки що залишаю "router", як це часто робиться в __init__.py для головного роутера пакета.
