# backend/app/src/api/v1/auth/token.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для управління JWT токенами (API v1).

Цей модуль містить FastAPI роутер для операцій, пов'язаних з
оновленням (refresh) JWT токенів доступу.
"""

from fastapi import APIRouter, Depends, HTTPException, status
# from backend.app.src.schemas.auth.token import TokenSchema, RefreshTokenRequestSchema # TODO: Розкоментувати
# from backend.app.src.services.auth.token_service import TokenService # TODO: Розкоментувати
# from backend.app.src.core.dependencies import get_current_user_from_refresh_token # TODO: Розкоментувати
# from backend.app.src.models.auth.user import UserModel # TODO: Розкоментувати для типу current_user
# from backend.app.src.config.logging import get_logger # TODO: Розкоментувати

# logger = get_logger(__name__) # TODO: Розкоментувати
router = APIRouter()

# @router.post(
#     "/refresh",
#     response_model=TokenSchema,
#     summary="Оновлення JWT токена доступу за допомогою refresh токена"
# )
# async def refresh_access_token(
#     refresh_token_data: RefreshTokenRequestSchema, # Очікує схему з полем refresh_token
#     # token_service: TokenService = Depends(), # TODO: Впровадити сервіс
#     # user: UserModel = Depends(get_current_user_from_refresh_token) # Залежність для валідації refresh токена
# ):
#     """
#     Приймає дійсний refresh токен та повертає нову пару JWT токенів
#     (access token та, можливо, новий refresh token).
#     """
#     # if not user: # Ця перевірка вже має бути в get_current_user_from_refresh_token
#     #     logger.warning("Invalid refresh token received for token refresh.")
#     #     raise HTTPException(
#     #         status_code=status.HTTP_401_UNAUTHORIZED,
#     #         detail="Недійсний refresh токен",
#     #         headers={"WWW-Authenticate": "Bearer"},
#     #     )
#     #
#     # new_access_token = await token_service.create_access_token(data={"sub": user.email, "user_id": user.id})
#     # # Опціонально: генерувати новий refresh token
#     # new_refresh_token = await token_service.create_refresh_token(data={"sub": user.email, "user_id": user.id})
#     # await token_service.revoke_refresh_token(refresh_token_data.refresh_token) # Інвалідувати старий
#     # await token_service.store_refresh_token(new_refresh_token, user.id) # Зберегти новий
#     #
#     # logger.info(f"Access token refreshed for user {user.email}")
#     # return {"access_token": new_access_token, "refresh_token": new_refresh_token, "token_type": "bearer"}
#     return {"access_token": "new_example_access_token", "refresh_token": "new_example_refresh_token", "token_type": "bearer"} # Заглушка

# TODO: Розглянути ендпоінт для інвалідації конкретного refresh токена (якщо не частина logout).
# TODO: Інтегрувати з реальними сервісами управління токенами та їх сховищем.
