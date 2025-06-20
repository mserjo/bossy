# backend/app/src/api/v1/tasks/router.py
# -*- coding: utf-8 -*-
"""
Маршрутизатор для завдань та подій API v1.
"""
from fastapi import APIRouter

tasks_router = APIRouter()

# Тут будуть ендпоінти для CRUD операцій над завданнями та подіями,
# їх призначення, відстеження виконання, коментарі тощо.

@tasks_router.get("/ping", tags=["V1 Завдання та Події"])
async def ping_tasks():
    return {"message": "Tasks router is active!"}
