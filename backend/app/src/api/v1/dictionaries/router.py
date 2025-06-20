# backend/app/src/api/v1/dictionaries/router.py
# -*- coding: utf-8 -*-
"""
Маршрутизатор для довідників API v1.
"""
from fastapi import APIRouter

from . import bonus_types, calendars, group_types, messengers, statuses, task_types, user_roles, user_types

dictionaries_router = APIRouter()

# Підключення маршрутизаторів з окремих файлів
dictionaries_router.include_router(statuses.router, prefix="/statuses", tags=["V1 Довідники - Статуси"])
dictionaries_router.include_router(user_roles.router, prefix="/user-roles", tags=["V1 Довідники - Ролі користувачів"])
dictionaries_router.include_router(user_types.router, prefix="/user-types", tags=["V1 Довідники - Типи користувачів"])
dictionaries_router.include_router(group_types.router, prefix="/group-types", tags=["V1 Довідники - Типи груп"])
dictionaries_router.include_router(task_types.router, prefix="/task-types", tags=["V1 Довідники - Типи завдань"])
dictionaries_router.include_router(bonus_types.router, prefix="/bonus-types", tags=["V1 Довідники - Типи бонусів"])
dictionaries_router.include_router(calendars.router, prefix="/calendars", tags=["V1 Довідники - Календарі"])
dictionaries_router.include_router(messengers.router, prefix="/messengers", tags=["V1 Довідники - Месенджери"])

@dictionaries_router.get("/ping_dictionaries_main", tags=["V1 Довідники - Health Check"])
async def ping_dictionaries_main():
    return {"message": "Main Dictionaries router is active and includes sub-routers!"}
