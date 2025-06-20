# backend/app/src/api/v1/bonuses/__init__.py
# -*- coding: utf-8 -*-
"""
Агрегований роутер для всіх ендпоінтів, пов'язаних з бонусною системою.

Цей модуль імпортує та об'єднує окремі роутери для:
- Управління правилами нарахування бонусів (`bonus_rules.py`)
- Перегляду бонусних рахунків користувачів (`accounts.py`)
- Перегляду транзакцій по бонусних рахунках (`transactions.py`)
- Управління нагородами та їх отримання (`rewards.py`)

Загальний префікс для всіх цих шляхів (наприклад, `/bonuses`) буде встановлено
при підключенні `bonuses_router` до роутера версії API (`v1_router`).

Сумісність: Python 3.13, SQLAlchemy v2, Pydantic v2.
"""
from fastapi import APIRouter

from backend.app.src.api.v1.bonuses.bonus_rules import router as bonus_rules_router
from backend.app.src.api.v1.bonuses.accounts import router as accounts_router
from backend.app.src.api.v1.bonuses.transactions import router as transactions_router
from backend.app.src.api.v1.bonuses.rewards import router as rewards_router
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

# Створюємо агрегований роутер для всіх ендпоінтів, пов'язаних з бонусною системою
bonuses_router = APIRouter()

# Підключення роутера для правил бонусів
bonuses_router.include_router(bonus_rules_router, prefix="/rules", tags=["Бонуси - Правила нарахування"]) # i18n tag

# Підключення роутера для рахунків користувачів
# Цей роутер може містити ендпоінти для перегляду балансу поточного користувача
# або для адміністративних дій над рахунками (якщо такі передбачені).
bonuses_router.include_router(accounts_router, prefix="/accounts", tags=["Бонуси - Рахунки користувачів"]) # i18n tag

# Підключення роутера для транзакцій
# Дозволяє переглядати історію транзакцій по рахунках.
bonuses_router.include_router(transactions_router, prefix="/transactions", tags=["Бонуси - Транзакції"]) # i18n tag

# Підключення роутера для нагород
# Включає CRUD операції для визначень нагород та ендпоінти для їх отримання користувачами.
bonuses_router.include_router(rewards_router, prefix="/rewards", tags=["Бонуси - Нагороди"]) # i18n tag


# Експортуємо bonuses_router для використання в головному v1_router
__all__ = [
    "bonuses_router",
]

logger.info("Роутер для бонусної системи (`bonuses_router`) зібрано та готовий до підключення до API v1.")
