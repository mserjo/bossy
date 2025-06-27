# backend/app/src/api/v1/tasks/__init__.py
# -*- coding: utf-8 -*-
"""
Ініціалізаційний файл для пакету ендпоінтів завдань та подій API v1.

Цей пакет містить роутери для управління завданнями та пов'язаними сутностями:
- Основні CRUD операції з завданнями/подіями (`tasks.py`).
- Призначення завдань (`assignments.py`).
- Обробка виконання завдань (`completions.py`).
- Пропозиції завдань від користувачів (`proposals.py`).
- Відгуки на завдання (`reviews.py`).

Ендпоінти зазвичай прив'язані до конкретної групи: `/groups/{group_id}/tasks/...`
"""

from fastapi import APIRouter

from backend.app.src.api.v1.tasks.tasks import router as main_tasks_router
from backend.app.src.api.v1.tasks.assignments import router as task_assignments_router
from backend.app.src.api.v1.tasks.completions import router as task_completions_router
from backend.app.src.api.v1.tasks.proposals import router as task_proposals_router
from backend.app.src.api.v1.tasks.reviews import router as task_reviews_router

# Агрегуючий роутер для всіх ендпоінтів, пов'язаних із завданнями.
# Цей роутер буде підключатися до головного роутера API v1 з префіксом,
# що включає group_id, наприклад, в `router.py` модуля `groups` або в головному `v1.router`.
# Для кращої організації, ендпоінти, що стосуються конкретного завдання (наприклад, призначення, відгуки),
# можуть бути вкладеними під шляхом конкретного завдання.

# Наприклад, /groups/{group_id}/tasks - для main_tasks_router
#           /groups/{group_id}/tasks/{task_id}/assignments - для task_assignments_router
#           /groups/{group_id}/task-proposals - для task_proposals_router (може бути окремо від конкретного завдання)

tasks_router = APIRouter()

# Основні операції з завданнями
tasks_router.include_router(main_tasks_router) # Без додаткового префіксу тут, він буде заданий при підключенні tasks_router

# Вкладені роутери для конкретного завдання (під /groups/{group_id}/tasks/{task_id}/)
task_specific_router = APIRouter()
task_specific_router.include_router(task_assignments_router, prefix="/{task_id}/assignments", tags=["Tasks"])
task_specific_router.include_router(task_completions_router, prefix="/{task_id}/actions", tags=["Tasks"]) # "actions" замість "completions" для URL
task_specific_router.include_router(task_reviews_router, prefix="/{task_id}/reviews", tags=["Tasks"])

tasks_router.include_router(task_specific_router) # Підключаємо вкладені роутери

# Роутер для пропозицій завдань (може бути на рівні групи, а не конкретного завдання)
# Наприклад, /groups/{group_id}/task-proposals
tasks_router.include_router(task_proposals_router, prefix="/task-proposals", tags=["Tasks"])


__all__ = (
    "tasks_router",
)
