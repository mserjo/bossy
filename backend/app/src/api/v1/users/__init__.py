# backend/app/src/api/v1/users/__init__.py
from fastapi import APIRouter

# Імпортуємо роутер з файлу users.py цього ж модуля
from .users import router as crud_users_router

# Створюємо агрегований роутер для всіх ендпоінтів керування користувачами
users_router = APIRouter()

# Підключаємо роутер CRUD операцій з користувачами
# Префікс тут не потрібен, оскільки він буде встановлений при підключенні users_router до v1_router
# Теги також краще визначати на рівні v1_router або в самому crud_users_router
users_router.include_router(crud_users_router)

# Експортуємо users_router для використання в головному v1_router (app/src/api/v1/router.py)
__all__ = ["users_router"]
