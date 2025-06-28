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
from fastapi import APIRouter, Depends, HTTPException, status # Додано APIRouter, HTTPException, status

from backend.app.src.schemas.auth.password import PasswordResetRequestSchema, PasswordResetConfirmSchema
from backend.app.src.services.auth.user_service import UserService
from backend.app.src.services.auth.token_service import TokenService # Для генерації/валідації токенів скидання
from backend.app.src.services.notifications.notification_service import NotificationService # Для відправки email
from backend.app.src.api.dependencies import DBSession
from backend.app.src.config.logging import logger
from backend.app.src.core.exceptions import NotFoundException


router = APIRouter()

@router.post(
    "/forgot-password",
    status_code=status.HTTP_200_OK,
    summary="Запит на відновлення забутого пароля",
    response_model=dict # Повертаємо словник з повідомленням
)
async def forgot_password(
    request_data: PasswordResetRequestSchema,
    db_session: DBSession = Depends(),
):
    """
    Ініціює процес відновлення пароля для користувача з вказаним email.
    - Перевіряє, чи існує користувач з таким email.
    - Генерує унікальний токен для скидання пароля.
    - Відправляє користувачу email з посиланням/токеном для скидання пароля.
    """
    logger.info(f"Запит на скидання пароля для email: {request_data.email}")
    user_service = UserService(db_session)
    token_service = TokenService(db_session)
    # notification_service = NotificationService(db_session) # TODO: Розкоментувати коли NotificationService буде готовий

    user = await user_service.get_user_by_email(email=request_data.email)
    if user:
        # TODO: Перевірити, чи користувач не заблокований, чи дозволено йому скидання пароля
        if user.is_deleted or not user.state or user.state.code != "active": # Приклад простої перевірки
             logger.warning(f"Спроба скидання пароля для неактивного/видаленого користувача: {request_data.email}")
             # Все одно повертаємо успішне повідомлення, щоб не розкривати статус користувача
             return {"message": "Якщо користувач з таким email існує та активний, йому буде надіслано інструкції для відновлення пароля."}

        password_reset_token = await token_service.create_password_reset_token(user_id=user.id)
        logger.info(f"Згенеровано токен скидання пароля для користувача {user.email} (ID: {user.id}). Токен: {password_reset_token}") # Логуємо токен тільки в DEBUG

        # TODO: Реалізувати відправку email через NotificationService
        # await notification_service.send_password_reset_email(
        #     to_email=user.email,
        #     username=user.name or user.email,
        #     token=password_reset_token
        # )
        logger.info(f"Email для скидання пароля (імітація відправки) мав би бути надісланий на {user.email} з токеном.")
    else:
        logger.warning(f"Запит на скидання пароля для неіснуючого email: {request_data.email}")

    # Важливо: завжди повертати однакове повідомлення, щоб не розкривати, чи існує email в системі.
    return {"message": "Якщо користувач з таким email існує та активний, йому буде надіслано інструкції для відновлення пароля."}


@router.post(
    "/reset-password",
    status_code=status.HTTP_200_OK,
    summary="Встановлення нового пароля за допомогою токена скидання",
    response_model=dict
)
async def reset_password(
    reset_data: PasswordResetConfirmSchema,
    db_session: DBSession = Depends(),
):
    """
    Встановлює новий пароль для користувача, використовуючи дійсний токен скидання.
    """
    logger.info(f"Спроба встановлення нового пароля за допомогою токена: {reset_data.token[:10]}...") # Логуємо тільки частину токена
    user_service = UserService(db_session)
    token_service = TokenService(db_session)

    try:
        user_id = await token_service.verify_password_reset_token(token=reset_data.token)
        if not user_id: # Малоймовірно, якщо verify_password_reset_token не кинув виняток
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Недійсний або прострочений токен скидання пароля.",
            )

        user = await user_service.get_user_by_id(user_id=user_id)
        if not user:
            # Це не повинно статися, якщо токен був валідним і пов'язаний з існуючим user_id
            logger.error(f"Користувача з ID {user_id} (з токена скидання) не знайдено.")
            raise NotFoundException("Користувача, пов'язаного з цим токеном, не знайдено.")

        # Перевірка, чи користувач все ще активний
        if user.is_deleted or not user.state or user.state.code != "active":
            logger.warning(f"Спроба скидання пароля для неактивного/видаленого користувача ID: {user_id} ({user.email})")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Обліковий запис неактивний або видалений.")

        await user_service.reset_user_password(user=user, new_password=reset_data.new_password)

        # Після успішного скидання пароля, токен скидання має бути інвалідований (видалений)
        await token_service.delete_password_reset_token(token=reset_data.token)
        logger.info(f"Пароль для користувача {user.email} (ID: {user.id}) успішно скинуто та токен інвалідовано.")

        return {"message": "Пароль успішно скинуто. Тепер ви можете увійти з новим паролем."}

    except HTTPException as http_exc:
        logger.warning(f"Помилка при скиданні пароля: {http_exc.detail}")
        raise http_exc
    except NotFoundException as nf_exc: # Обробка NotFoundException з user_service
        logger.warning(f"Помилка при скиданні пароля: {str(nf_exc)}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(nf_exc))
    except ValueError as val_err: # Від is_strong_password або якщо паролі не співпадають (з схеми)
        logger.warning(f"Помилка валідації при скиданні пароля: {str(val_err)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
    except Exception as e:
        logger.error(f"Неочікувана помилка під час скидання пароля: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутрішня помилка сервера.")


# Ендпоінт для зміни пароля аутентифікованим користувачем знаходиться в profile.py
# (/me/change-password)

# TODO: Забезпечити безпеку токенів скидання (обмежений час дії - реалізовано в TokenService, одноразовість - реалізовано).
# TODO: Інтегрувати з реальним NotificationService для відправки email.
