# backend/app/src/api/v1/auth/password.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для управління паролями користувачів (API v1).

Цей модуль містить FastAPI роутер для операцій, пов'язаних з
відновленням забутого пароля та зміною поточного пароля користувача.
"""

from fastapi import APIRouter, Depends, HTTPException, status
# from backend.app.src.schemas.auth.password import PasswordResetRequestSchema, PasswordResetConfirmSchema, PasswordChangeSchema # TODO: Розкоментувати
# from backend.app.src.services.auth.user_service import UserService # TODO: Розкоментувати (або PasswordService)
# from backend.app.src.services.auth.token_service import TokenService # TODO: Для генерації/валідації токенів скидання
# from backend.app.src.core.dependencies import get_current_active_user # TODO: Розкоментувати
# from backend.app.src.models.auth.user import UserModel # TODO: Розкоментувати для типу current_user
# from backend.app.src.config.logging import get_logger # TODO: Розкоментувати

# logger = get_logger(__name__) # TODO: Розкоментувати
router = APIRouter()

# @router.post(
#     "/forgot-password",
#     status_code=status.HTTP_200_OK,
#     summary="Запит на відновлення забутого пароля"
# )
# async def forgot_password(
#     request_data: PasswordResetRequestSchema, # Очікує email користувача
#     # user_service: UserService = Depends(),
#     # token_service: TokenService = Depends()
# ):
#     """
#     Ініціює процес відновлення пароля для користувача з вказаним email.
#     - Перевіряє, чи існує користувач з таким email.
#     - Генерує унікальний токен для скидання пароля.
#     - Відправляє користувачу email з посиланням/токеном для скидання пароля.
#     """
#     # user = await user_service.get_user_by_email(email=request_data.email)
#     # if user:
#     #     password_reset_token = await token_service.create_password_reset_token(email=user.email)
#     #     await user_service.send_password_reset_email(email=user.email, token=password_reset_token)
#     #     logger.info(f"Password reset email sent to {user.email}")
#     # else:
#     #     logger.warning(f"Password reset requested for non-existing email: {request_data.email}")
#     # # Важливо: не повідомляти, чи існує email, для безпеки.
#     return {"message": "Якщо користувач з таким email існує, йому буде надіслано інструкції для відновлення пароля."}

# @router.post(
#     "/reset-password",
#     status_code=status.HTTP_200_OK,
#     summary="Встановлення нового пароля за допомогою токена скидання"
# )
# async def reset_password(
#     reset_data: PasswordResetConfirmSchema, # Очікує токен та новий пароль
#     # user_service: UserService = Depends(),
#     # token_service: TokenService = Depends()
# ):
#     """
#     Встановлює новий пароль для користувача, використовуючи дійсний токен скидання.
#     """
#     # email = await token_service.verify_password_reset_token(token=reset_data.token)
#     # if not email:
#     #     raise HTTPException(
#     #         status_code=status.HTTP_400_BAD_REQUEST,
#     #         detail="Недійсний або прострочений токен скидання пароля",
#     #     )
#     #
#     # user = await user_service.get_user_by_email(email=email)
#     # if not user: # Малоймовірно, якщо токен валідний, але перевірка не завадить
#     #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Користувача не знайдено")
#     #
#     # await user_service.reset_password(user=user, new_password=reset_data.new_password)
#     # logger.info(f"Password reset successfully for user {email}")
#     return {"message": "Пароль успішно скинуто. Тепер ви можете увійти з новим паролем."}

# @router.put(
#     "/change-password",
#     status_code=status.HTTP_200_OK,
#     summary="Зміна поточного пароля аутентифікованого користувача"
# )
# async def change_password(
#     password_data: PasswordChangeSchema, # Очікує старий та новий паролі
#     # current_user: UserModel = Depends(get_current_active_user),
#     # user_service: UserService = Depends()
# ):
#     """
#     Дозволяє аутентифікованому користувачу змінити свій поточний пароль.
#     """
#     # if not await user_service.verify_password(plain_password=password_data.old_password, hashed_password=current_user.hashed_password):
#     #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Неправильний старий пароль")
#     #
#     # await user_service.change_password(user=current_user, new_password=password_data.new_password)
#     # logger.info(f"Password changed successfully for user {current_user.email}")
#     return {"message": "Пароль успішно змінено."}

# TODO: Інтегрувати з реальними сервісами та моделями.
# TODO: Забезпечити безпеку токенів скидання (обмежений час дії, одноразовість).
