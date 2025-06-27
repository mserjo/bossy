# backend/app/src/api/v1/bonuses/__init__.py
# -*- coding: utf-8 -*-
"""
Ініціалізаційний файл для пакету ендпоінтів бонусів, рахунків, транзакцій та нагород API v1.

Цей пакет містить роутери для:
- Управління правилами нарахування бонусів (`bonus_rules.py`).
- Перегляду та управління рахунками користувачів (`accounts.py`).
- Перегляду транзакцій по рахунках та ручного коригування (`transactions.py`).
- Управління нагородами та їх отримання (`rewards.py`).

Ендпоінти зазвичай прив'язані до конкретної групи: `/groups/{group_id}/...`
"""

from fastapi import APIRouter

from backend.app.src.api.v1.bonuses.bonus_rules import router as bonus_rules_router
from backend.app.src.api.v1.bonuses.accounts import router as accounts_router
from backend.app.src.api.v1.bonuses.transactions import router as account_transactions_router # Для шляхів під /accounts
from backend.app.src.api.v1.bonuses.transactions import manual_transactions_router # Окремий для ручних операцій
from backend.app.src.api.v1.bonuses.rewards import router as rewards_router

# Агрегуючий роутер для всіх ендпоінтів, пов'язаних з бонусною системою.
# Цей роутер буде підключатися до головного роутера API v1
# з префіксом, що включає group_id.
bonuses_router = APIRouter()

# Роутери, що прив'язані до /groups/{group_id}/
bonuses_router.include_router(bonus_rules_router, prefix="/bonus-rules", tags=["Bonuses"])
bonuses_router.include_router(rewards_router, prefix="/rewards", tags=["Bonuses"])

# Роутер для рахунків та транзакцій по них
# /groups/{group_id}/accounts
# /groups/{group_id}/accounts/me/transactions
# /groups/{group_id}/accounts/{user_id}/transactions
accounts_main_router = APIRouter()
accounts_main_router.include_router(accounts_router) # Ендпоінти для /accounts та /accounts/{user_id}
accounts_main_router.include_router(account_transactions_router, prefix="") # Ендпоінти /me/transactions та /{user_id}/transactions будуть відносно /accounts

bonuses_router.include_router(accounts_main_router, prefix="/accounts", tags=["Bonuses"])


# Роутер для ручних транзакцій/коригувань
# Наприклад, /groups/{group_id}/adjustments
bonuses_router.include_router(manual_transactions_router, prefix="/adjustments", tags=["Bonuses"])


__all__ = (
    "bonuses_router",
)
