# backend/app/src/api/graphql/types/auth.py
# -*- coding: utf-8 -*-
"""
GraphQL типи, пов'язані з автентифікацією та токенами.
"""

import strawberry
from typing import Optional

@strawberry.type
class TokenType:
    """
    GraphQL тип, що представляє JWT токени доступу та оновлення.
    """
    access_token: str = strawberry.field(description="JWT токен доступу.")
    refresh_token: Optional[str] = strawberry.field(description="JWT токен оновлення (може бути відсутнім).")
    token_type: str = strawberry.field(description="Тип токена (зазвичай 'bearer').")
    expires_in: Optional[int] = strawberry.field(description="Час життя access_token в секундах (опціонально).")

# Можливо, інші типи, пов'язані з автентифікацією, якщо вони потрібні.
# Наприклад, для відповіді на запит скидання пароля, якщо вона не просто повідомлення.

__all__ = [
    "TokenType",
]
