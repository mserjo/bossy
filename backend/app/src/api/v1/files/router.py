# backend/app/src/api/v1/files/router.py
# -*- coding: utf-8 -*-
"""
Маршрутизатор для операцій з файлами API v1.
"""
from fastapi import APIRouter

files_router = APIRouter()

# Тут будуть ендпоінти для завантаження файлів (аватари, іконки, додатки),
# отримання інформації про файли, видалення файлів тощо.

@files_router.get("/ping", tags=["V1 Файли"])
async def ping_files():
    return {"message": "Files router is active!"}
