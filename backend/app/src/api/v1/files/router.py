# backend/app/src/api/v1/files/router.py
# -*- coding: utf-8 -*-
"""
Маршрутизатор для операцій з файлами API v1.
"""
from fastapi import APIRouter

from . import avatars, files, uploads

files_router = APIRouter()

# Підключення маршрутизаторів з окремих файлів
files_router.include_router(uploads.router, prefix="/uploads", tags=["V1 Файли - Завантаження"])
files_router.include_router(avatars.router, prefix="/avatars", tags=["V1 Файли - Аватари"])
files_router.include_router(files.router, prefix="/general", tags=["V1 Файли - Загальні"]) # 'files.router' might be too generic, added 'general'

@files_router.get("/ping_files_main", tags=["V1 Файли - Health Check"])
async def ping_files_main():
    return {"message": "Main Files router is active and includes sub-routers!"}
