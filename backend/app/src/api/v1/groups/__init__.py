# backend/app/src/api/v1/groups/__init__.py
# -*- coding: utf-8 -*-
"""
Ініціалізаційний файл для пакету 'groups' API v1.

Цей пакет містить ендпоінти для управління групами в системі через API v1.
Сюди входять операції, пов'язані з:
- Створенням, переглядом, редагуванням та видаленням груп (`groups.py`).
- Управлінням налаштуваннями групи (`settings.py`).
- Управлінням членством в групі (`membership.py`).
- Управлінням запрошеннями до групи (`invitation.py`).
- Роботою з шаблонами груп (`templates.py`).
- Проведенням опитувань/голосувань в групі (`polls.py`).
- Отриманням звітів по групі (`reports.py`).

Також цей пакет може агрегувати роутери для вкладених ресурсів,
таких як завдання (`tasks`) та команди (`teams`), якщо вони розглядаються
в контексті групи.

Цей файл робить каталог 'groups' пакетом Python та експортує
агрегований роутер для всіх ендпоінтів, пов'язаних з групами, в API v1.
"""

from fastapi import APIRouter

# TODO: Імпортувати окремі роутери з модулів цього пакету, коли вони будуть створені.
# from backend.app.src.api.v1.groups.groups import router as crud_groups_router
# from backend.app.src.api.v1.groups.settings import router as group_settings_router
# from backend.app.src.api.v1.groups.membership import router as group_membership_router
# from backend.app.src.api.v1.groups.invitation import router as group_invitation_router
# from backend.app.src.api.v1.groups.templates import router as group_templates_router
# from backend.app.src.api.v1.groups.polls import router as group_polls_router
# from backend.app.src.api.v1.groups.reports import router as group_reports_router

# Імпорт роутерів для вкладених ресурсів (завдання, команди), якщо вони обробляються тут.
# from backend.app.src.api.v1.tasks import router as tasks_within_groups_router # Приклад
# from backend.app.src.api.v1.teams import router as teams_within_groups_router # Приклад

# Агрегуючий роутер для всіх ендпоінтів, пов'язаних з групами, API v1.
router = APIRouter(tags=["v1 :: Groups"])

# TODO: Розкоментувати та підключити окремі роутери.
# Префікси для вкладених сутностей (settings, members, invitations, polls, reports, tasks, teams)
# зазвичай включають `{group_id}`.

# Основні операції CRUD з групами (наприклад, /groups, /groups/{group_id})
# router.include_router(crud_groups_router)

# Налаштування конкретної групи (наприклад, /groups/{group_id}/settings)
# router.include_router(group_settings_router) # Цей роутер вже має шляхи відносно /{group_id}/settings

# Членство в групі (наприклад, /groups/{group_id}/members)
# router.include_router(group_membership_router)

# Запрошення до групи (наприклад, /groups/{group_id}/invitations)
# router.include_router(group_invitation_router)

# Шаблони груп (наприклад, /groups/templates - не залежить від group_id)
# router.include_router(group_templates_router, prefix="/templates")

# Опитування/голосування в групі (наприклад, /groups/{group_id}/polls)
# router.include_router(group_polls_router)

# Звіти по групі (наприклад, /groups/{group_id}/reports)
# router.include_router(group_reports_router)

# Вкладені ресурси: Завдання в групі (наприклад, /groups/{group_id}/tasks)
# router.include_router(tasks_within_groups_router, prefix="/{group_id}/tasks", tags=["v1 :: Tasks & Events (in Group)"])

# Вкладені ресурси: Команди в групі (наприклад, /groups/{group_id}/teams)
# router.include_router(teams_within_groups_router, prefix="/{group_id}/teams", tags=["v1 :: Teams (in Group)"])


# Експорт агрегованого роутера.
__all__ = [
    "router",
]

# TODO: Узгодити назву експортованого роутера ("router") з імпортом
# в `backend.app.src.api.v1.router.py` (там очікується `groups_v1_router`).
# TODO: Переглянути структуру підключення роутерів для завдань та команд.
# `structure-claude-v3.md` передбачає окремі каталоги `tasks` та `teams` на рівні `v1`.
# Якщо їх роутери підключаються там, то тут їх підключати не потрібно,
# але їхні шляхи все одно будуть містити `/groups/{group_id}/...`.
# Це питання архітектури роутингу: чи групувати за ресурсом (група), чи за функцією (завдання).
# Поки що залишаю тут згадку про можливе вкладене підключення.
