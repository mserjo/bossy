# backend/app/src/api/v1/users/__init__.py
# -*- coding: utf-8 -*-
"""
Агрегований роутер для ендпоінтів управління користувачами на рівні системи.

Цей модуль імпортує роутер `crud_users_router` з файлу `users.py`
та експортує його як `users_router`. Цей `users_router` призначений для
адміністративних дій над користувачами, таких як перегляд списку всіх користувачів,
створення, оновлення та видалення користувачів суперкористувачем.
"""
from fastapi import APIRouter

# Повні шляхи імпорту (відносно поточного пакету)
from .users import router as crud_users_router # Роутер з CRUD операціями для користувачів

from backend.app.src.config.logging import logger # Централізований логер

# Створюємо агрегований роутер для всіх ендпоінтів керування користувачами
users_router = APIRouter()

# Підключаємо роутер CRUD операцій з користувачами
# Префікс для цих ендпоінтів (наприклад, /users) буде встановлений при підключенні
# users_router до v1_router в backend/app/src/api/v1/router.py.
# Теги також краще визначати на рівні v1_router або в самому crud_users_router.
users_router.include_router(crud_users_router)

# Експортуємо users_router для використання в головному v1_router
__all__ = [
    "users_router",
]

logger.info("Роутер для управління користувачами (`users_router`) зібрано та готовий до підключення до API v1.")
