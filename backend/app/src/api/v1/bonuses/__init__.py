# backend/app/src/api/v1/bonuses/__init__.py
# -*- coding: utf-8 -*-
"""
Ініціалізаційний файл для пакету 'bonuses' API v1.

Цей пакет містить ендпоінти для управління бонусами, рахунками користувачів
та нагородами в системі через API v1. Операції можуть включати:
- Управління правилами нарахування бонусів/штрафів (`bonus_rules.py`).
- Перегляд рахунків користувачів та їх виписок (`accounts.py`).
- Перегляд історії транзакцій по рахунках (`transactions.py`).
- Управління нагородами (`rewards.py`).

Більшість ендпоінтів тут, ймовірно, будуть діяти в контексті певної групи,
отже, очікується, що `group_id` буде частиною шляху.

Цей файл робить каталог 'bonuses' пакетом Python та експортує
агрегований роутер `router` для всіх ендпоінтів бонусної системи.
"""

from fastapi import APIRouter

# TODO: Імпортувати окремі роутери з модулів цього пакету, коли вони будуть створені.
# from backend.app.src.api.v1.bonuses.bonus_rules import router as bonus_rules_router
# from backend.app.src.api.v1.bonuses.accounts import router as accounts_router
# from backend.app.src.api.v1.bonuses.transactions import router as transactions_router # Можливо, окремо для перегляду та для ручних операцій
# from backend.app.src.api.v1.bonuses.rewards import router as rewards_router

# Агрегуючий роутер для всіх ендпоінтів бонусної системи API v1.
# Цей роутер, ймовірно, буде підключений з префіксом, що включає group_id,
# наприклад, в `groups/__init__.py` або в `v1/router.py` як `/groups/{group_id}/bonuses`.
router = APIRouter(tags=["v1 :: Bonuses & Rewards"])

# TODO: Розкоментувати та підключити окремі роутери.
# Приклад структури підключення:

# Правила бонусів (наприклад, /groups/{group_id}/bonuses/rules)
# router.include_router(bonus_rules_router, prefix="/rules")

# Рахунки користувачів та транзакції по них
# (наприклад, /groups/{group_id}/bonuses/accounts, /groups/{group_id}/bonuses/accounts/{user_id}/transactions)
# accounts_sub_router = APIRouter()
# accounts_sub_router.include_router(accounts_router) # для /
# accounts_sub_router.include_router(transactions_router, prefix="/{user_id}/transactions") # або просто /transactions, якщо user_id вже в context
# router.include_router(accounts_sub_router, prefix="/accounts")

# Нагороди (наприклад, /groups/{group_id}/bonuses/rewards)
# router.include_router(rewards_router, prefix="/rewards")

# Ручні транзакції або коригування (якщо є такий функціонал)
# from backend.app.src.api.v1.bonuses.manual_transactions import router as manual_transactions_router
# router.include_router(manual_transactions_router, prefix="/adjustments")


# Експорт агрегованого роутера.
__all__ = [
    "router",
]

# TODO: Узгодити назву експортованого роутера ("router") з імпортом
# в `backend.app.src.api.v1.router.py` (очікує `bonuses_v1_router`).
# TODO: Детально продумати шляхи та префікси для кожного під-ресурсу
# (rules, accounts, transactions, rewards) в контексті `group_id`.
