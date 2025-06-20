# backend/app/src/api/v1/groups/router.py
# -*- coding: utf-8 -*-
"""
Маршрутизатор для операцій з групами API v1.
"""
from fastapi import APIRouter

groups_router = APIRouter()

# Тут будуть ендпоінти для CRUD операцій над групами,
# управління членством, запрошеннями, налаштуваннями груп тощо.

@groups_router.get("/ping", tags=["V1 Групи"])
async def ping_groups():
    return {"message": "Groups router is active!"}
