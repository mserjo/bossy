# backend/app/src/api/v1/groups/router.py
# -*- coding: utf-8 -*-
"""
Маршрутизатор для операцій з групами API v1.
"""
from fastapi import APIRouter

from . import groups, invitation, membership, reports, settings as group_settings

groups_router = APIRouter()

# Підключення маршрутизаторів з окремих файлів
# Основний CRUD для груп може не мати додаткового префіксу або мати префікс типу "/"
groups_router.include_router(groups.router, tags=["V1 Групи - Основні операції"])
groups_router.include_router(membership.router, prefix="/memberships", tags=["V1 Групи - Членство"])
groups_router.include_router(invitation.router, prefix="/invitations", tags=["V1 Групи - Запрошення"])
groups_router.include_router(group_settings.router, prefix="/settings", tags=["V1 Групи - Налаштування"])
groups_router.include_router(reports.router, prefix="/reports", tags=["V1 Групи - Звіти"])


@groups_router.get("/ping_groups_main", tags=["V1 Групи - Health Check"])
async def ping_groups_main():
    return {"message": "Main Groups router is active and includes sub-routers!"}
