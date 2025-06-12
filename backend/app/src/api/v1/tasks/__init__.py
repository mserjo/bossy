# backend/app/src/api/v1/tasks/__init__.py
# -*- coding: utf-8 -*-
"""
Агрегований роутер для всіх ендпоінтів, пов'язаних з управлінням завданнями та подіями.

Цей модуль імпортує та об'єднує окремі роутери для:
- CRUD операцій над завданнями (`tasks.py`)
- CRUD операцій над подіями (`events.py`)
- Управління призначеннями завдань/подій (`assignments.py`)
- Обробки виконань завдань/подій (`completions.py`)
- Управління відгуками на завдання (`reviews.py`)

Загальний префікс для всіх цих шляхів (наприклад, `/tasks`) буде встановлено
при підключенні `tasks_router` до роутера версії API (`v1_router`).
"""
from fastapi import APIRouter

# Повні шляхи імпорту (відносно поточного пакету)
from .tasks import router as crud_tasks_router
from .events import router as events_router
from .assignments import router as task_assignments_router
from .completions import router as task_completions_router
from .reviews import router as task_reviews_router

from backend.app.src.config.logging import logger # Централізований логер

# Створюємо агрегований роутер для всіх ендпоінтів, пов'язаних із задачами та подіями
tasks_router = APIRouter()

# Підключення роутера для CRUD операцій з задачами
# Шляхи будуть відносні до префіксу tasks_router (наприклад, /tasks/ або /tasks/{task_id})
tasks_router.include_router(crud_tasks_router, tags=["Завдання - Основні операції"]) # i18n tag

# Підключення роутера для CRUD операцій з подіями
tasks_router.include_router(events_router, prefix="/events", tags=["Події - Основні операції"]) # i18n tag

# Підключення роутера для призначень завдань/подій
# Шляхи, наприклад: /tasks/assignments/{task_id}/users або /tasks/events/assignments/{event_id}/users
# TODO: Переглянути префікси для assignments, completions, reviews, щоб вони були вкладені або в /tasks/{task_id}/ або в /events/{event_id}/
# Поточна структура assignments.py може очікувати {task_id} або {event_id} в шляху.
# Якщо ці роутери вже містять повні шляхи або {item_id}, то префікс тут може бути простим.
tasks_router.include_router(task_assignments_router, prefix="/assignments", tags=["Завдання/Події - Призначення"]) # i18n tag

# Підключення роутера для виконань завдань/подій
tasks_router.include_router(task_completions_router, prefix="/completions", tags=["Завдання/Події - Виконання"]) # i18n tag

# Підключення роутера для відгуків на задачі
tasks_router.include_router(task_reviews_router, prefix="/reviews", tags=["Завдання - Відгуки"]) # i18n tag


# Експортуємо tasks_router для використання в головному v1_router
__all__ = [
    "tasks_router",
]

logger.info("Роутер для завдань та подій (`tasks_router`) зібрано та готовий до підключення до API v1.")
