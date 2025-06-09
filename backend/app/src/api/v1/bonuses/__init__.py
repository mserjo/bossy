# backend/app/src/api/v1/bonuses/__init__.py
from fastapi import APIRouter

# Імпортуємо роутери з файлів цього модуля
from .bonus_rules import router as bonus_rules_router
from .accounts import router as accounts_router
from .transactions import router as transactions_router
from .rewards import router as rewards_router

# Створюємо агрегований роутер для всіх ендпоінтів, пов'язаних з бонусною системою
bonuses_router = APIRouter()

# Підключення роутера для правил бонусів
bonuses_router.include_router(bonus_rules_router, prefix="/rules", tags=["Bonus Rules"])

# Підключення роутера для рахунків користувачів
bonuses_router.include_router(accounts_router, prefix="/accounts", tags=["User Accounts & History"])

# Підключення роутера для транзакцій
bonuses_router.include_router(transactions_router, prefix="/transactions", tags=["Account Transactions"])

# Підключення роутера для нагород
bonuses_router.include_router(rewards_router, prefix="/rewards", tags=["Rewards & Redemption"])


# Експортуємо bonuses_router для використання в головному v1_router (app/src/api/v1/router.py)
__all__ = ["bonuses_router"]
