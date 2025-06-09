# backend/app/src/api/v1/groups/__init__.py
from fastapi import APIRouter

# Імпортуємо роутери з файлів цього модуля
from .groups import router as crud_groups_router
from .settings import router as group_settings_router
from .membership import router as group_membership_router
from .invitation import router as group_invitation_router # Цей роутер вже агрегує свої під-шляхи
from .reports import router as group_reports_router

# Створюємо агрегований роутер для всіх ендпоінтів, пов'язаних з групами
groups_router = APIRouter()

# Підключення роутера для CRUD операцій з групами
# Його шляхи (напр. / та /{group_id}) будуть відносні до префіксу groups_router (/groups)
groups_router.include_router(crud_groups_router, tags=["Groups Core"])

# Підключення роутера для налаштувань групи
# Його шляхи (напр. /{group_id}/settings) також будуть відносні до /groups
# Оскільки group_id є частиною шляху в самому group_settings_router, тут префікс не потрібен.
groups_router.include_router(group_settings_router, tags=["Groups Settings"])

# Підключення роутера для членства в групі
# Його шляхи (напр. /{group_id}/members, /{group_id}/leave) аналогічно.
groups_router.include_router(group_membership_router, tags=["Groups Membership"])

# Підключення роутера для запрошень до групи
# group_invitation_router вже має внутрішню структуру шляхів:
# - /{group_id}/invitations (для дій адміна групи)
# - /invitations (для дій користувача)
# При підключенні до groups_router (префікс /groups), шляхи стануть:
# - /groups/{group_id}/invitations
# - /groups/invitations
groups_router.include_router(group_invitation_router) # Теги вже визначені в самому group_invitation_router

# Підключення роутера для звітів по групі
# group_reports_router має шлях /activity і очікує group_id з Path.
# Тому підключаємо його з префіксом /{group_id}/reports.
groups_router.include_router(
    group_reports_router,
    prefix="/{group_id}/reports", # Це гарантує, що group_id буде доступний для Path параметра в reports.py
    tags=["Groups Reports"]
)


# Експортуємо groups_router для використання в головному v1_router (app/src/api/v1/router.py)
__all__ = ["groups_router"]
