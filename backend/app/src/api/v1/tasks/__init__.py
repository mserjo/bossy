# backend/app/src/api/v1/tasks/__init__.py
# -*- coding: utf-8 -*-
"""
Ініціалізаційний файл для пакету 'tasks' API v1.

Цей пакет містить ендпоінти для управління завданнями та подіями
в системі через API v1. Операції можуть включати:
- Створення, перегляд, редагування та видалення завдань/подій (`task.py`).
- Призначення завдань користувачам (`assignment.py`).
- Відстеження виконання завдань (`completion.py`).
- Робота з пропозиціями завдань від користувачів (`proposal.py`).
- Залишення відгуків на завдання (`review.py`).

Шляхи до ендпоінтів завдань часто є вкладеними в групи, наприклад:
`/groups/{group_id}/tasks/...`

Цей файл робить каталог 'tasks' пакетом Python та експортує
агрегований роутер `router` для всіх ендпоінтів завдань.
Цей `router` призначений для підключення в контексті конкретної групи,
наприклад, в `groups/__init__.py` або в `v1/router.py` з префіксом `/groups/{group_id}/tasks`.
"""

from fastapi import APIRouter

# TODO: Імпортувати окремі роутери з модулів цього пакету, коли вони будуть створені.
# from backend.app.src.api.v1.tasks.task import router as crud_tasks_router
# from backend.app.src.api.v1.tasks.assignment import router as task_assignment_router
# from backend.app.src.api.v1.tasks.completion import router as task_completion_router
# from backend.app.src.api.v1.tasks.proposal import router as task_proposal_router
# from backend.app.src.api.v1.tasks.review import router as task_review_router

# Агрегуючий роутер для всіх ендпоінтів завдань API v1.
# Цей роутер буде підключений з префіксом, що включає group_id.
router = APIRouter(tags=["v1 :: Tasks & Events"])

# TODO: Розкоментувати та підключити окремі роутери.
# Приклад структури підключення:

# Основні CRUD операції з завданнями (наприклад, /groups/{group_id}/tasks/, /groups/{group_id}/tasks/{task_id})
# router.include_router(crud_tasks_router) # Шляхи визначаються всередині crud_tasks_router

# Дії, пов'язані з конкретним завданням (вкладені під /{task_id}/)
# router.include_router(task_assignment_router, prefix="/{task_id}/assignments")
# router.include_router(task_completion_router, prefix="/{task_id}/completions") # Або /actions
# router.include_router(task_review_router, prefix="/{task_id}/reviews")

# Пропозиції завдань (можуть бути на рівні групи, а не конкретного завдання)
# Наприклад, /groups/{group_id}/tasks/proposals
# router.include_router(task_proposal_router, prefix="/proposals")


# Експорт агрегованого роутера.
__all__ = [
    "router",
]

# TODO: Узгодити назву експортованого роутера ("router") з імпортом
# в `backend.app.src.api.v1.router.py` (очікує `tasks_v1_router`) або
# в `backend.app.src.api.v1.groups.__init__.py` (якщо підключається там).
# TODO: Переконатися, що шляхи та префікси коректно обробляють `group_id` та `task_id`.
# Файли `task.py`, `assignment.py` і т.д. повинні враховувати ці параметри шляху.
