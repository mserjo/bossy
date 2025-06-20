# backend/app/src/api/v1/tasks/router.py
# -*- coding: utf-8 -*-
"""
Маршрутизатор для завдань та подій API v1.
"""
from fastapi import APIRouter

from . import assignments, completions, events, reviews, tasks

tasks_router = APIRouter()

# Підключення маршрутизаторів з окремих файлів
tasks_router.include_router(tasks.router, prefix="/tasks", tags=["V1 Завдання - Основні"]) # /tasks/tasks/...
tasks_router.include_router(events.router, prefix="/events", tags=["V1 Завдання - Події"]) # /tasks/events/...
tasks_router.include_router(assignments.router, prefix="/assignments", tags=["V1 Завдання - Призначення"]) # /tasks/assignments/...
tasks_router.include_router(completions.router, prefix="/completions", tags=["V1 Завдання - Виконання"]) # /tasks/completions/...
tasks_router.include_router(reviews.router, prefix="/reviews", tags=["V1 Завдання - Відгуки"]) # /tasks/reviews/...


@tasks_router.get("/ping_tasks_main", tags=["V1 Завдання та Події - Health Check"])
async def ping_tasks_main():
    return {"message": "Main Tasks router is active and includes sub-routers!"}
