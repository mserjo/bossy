# backend/app/src/api/v1/bonuses/router.py
# -*- coding: utf-8 -*-
"""
Маршрутизатор для бонусів, рахунків та винагород API v1.
"""
from fastapi import APIRouter

from . import accounts, bonus_rules, rewards, transactions

bonuses_router = APIRouter()

# Підключення маршрутизаторів з окремих файлів
bonuses_router.include_router(accounts.router, prefix="/accounts", tags=["V1 Бонуси - Рахунки"])
bonuses_router.include_router(bonus_rules.router, prefix="/rules", tags=["V1 Бонуси - Правила"])
bonuses_router.include_router(rewards.router, prefix="/rewards", tags=["V1 Бонуси - Винагороди"])
bonuses_router.include_router(transactions.router, prefix="/transactions", tags=["V1 Бонуси - Транзакції"])

@bonuses_router.get("/ping_bonuses_main", tags=["V1 Бонуси та Винагороди - Health Check"])
async def ping_bonuses_main():
    return {"message": "Main Bonuses router is active and includes sub-routers!"}
