# backend/app/src/api/v1/auth/password.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для управління паролями користувачів: зміна, запит на скидання, встановлення нового.

Сумісність: Python 3.13, SQLAlchemy v2, Pydantic v2.
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.src.api.dependencies import get_api_db_session, get_current_active_user, get_user_service, get_password_service
# TODO: Додати get_notification_service, коли він буде готовий для надсилання email
# from backend.app.src.api.dependencies import get_notification_service
from backend.app.src.models.auth.user import User as UserModel
from backend.app.src.schemas.auth.password import (
    PasswordChange,
    PasswordResetRequest,
    PasswordResetConfirm
)
from backend.app.src.schemas.message import MessageResponse  # Загальна схема відповіді з повідомленням
from backend.app.src.services.auth.user import UserService
from backend.app.src.services.auth.password import PasswordService  # Оновлений PasswordService
# from backend.app.src.services.notifications.notification import NotificationService # Для надсилання email
from backend.app.src.config import settings as global_settings  # Для FRONTEND_URL
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

router = APIRouter()

# ПРИМІТКА: Цей ендпоінт залежить від реалізації методу `change_password`
# в `PasswordService`, який має перевіряти поточний пароль користувача
# та оновлювати його на новий.
@router.post(
    "/change",  # Префікс /password буде додано в auth/__init__.py
    response_model=MessageResponse,
    summary="Зміна паролю користувача",  # i18n
    description="Дозволяє автентифікованому користувачеві змінити свій поточний пароль."  # i18n
)
async def change_password_endpoint(  # Перейменовано, щоб уникнути конфлікту з імпортом PasswordService
        password_data: PasswordChange,
        current_user: UserModel = Depends(get_current_active_user),
        password_service: PasswordService = Depends(get_password_service)
):
    """
    Змінює пароль поточного автентифікованого користувача.

    - **current_password**: Поточний пароль користувача.
    - **new_password**: Новий пароль користувача.
    """
    logger.info(f"Користувач ID '{current_user.id}' намагається змінити пароль.")
    try:
        success = await password_service.change_password(
            user_id=current_user.id,
            old_password=password_data.current_password,
            new_password=password_data.new_password
        )
        if not success:  # change_password може повертати False або кидати ValueError
            # i18n
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Не вдалося змінити пароль. Перевірте поточний пароль.")
    except ValueError as e:  # Якщо сервіс кидає ValueError (напр., старий пароль невірний, або новий такий самий)
        logger.warning(f"Помилка зміни пароля для користувача ID '{current_user.id}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n

    # i18n
    return MessageResponse(message="Пароль успішно змінено.")

# ПРИМІТКА: Цей ендпоінт залежить від реалізації `create_password_reset_token` в `PasswordService`
# та майбутньої інтеграції з `NotificationService` для надсилання email (див. TODO).
# Також важливою є коректна конфігурація `FRONTEND_URL` в налаштуваннях.
@router.post(
    "/forgot",  # Префікс /password
    response_model=MessageResponse,
    summary="Запит на відновлення паролю",  # i18n
    description="Ініціює процес відновлення паролю для користувача за його email."  # i18n
)
async def forgot_password_endpoint(  # Перейменовано
        request_data: PasswordResetRequest,
        background_tasks: BackgroundTasks,
        user_service: UserService = Depends(get_user_service),
        password_service: PasswordService = Depends(get_password_service)
        # TODO: Додати notification_service: NotificationService = Depends(get_notification_service)
):
    """
    Надсилає інструкції для відновлення паролю, якщо користувач з таким email існує та активний.
    Завжди повертає однакову відповідь для запобігання розкриттю існування email.

    - **email**: Електронна пошта користувача.
    """
    logger.info(f"Запит на відновлення паролю для email: {request_data.email}")

    # Використовуємо метод сервісу, що повертає ORM модель для внутрішньої логіки
    user = await user_service.get_user_by_email_orm(email=request_data.email)

    if user and user.is_active:
        logger.info(f"Користувача знайдено та він активний (ID: {user.id}). Генерація токена скидання паролю.")
        reset_token = await password_service.create_password_reset_token(user_id=user.id)

        # TODO: Переконатися, що FRONTEND_PASSWORD_RESET_URL налаштовано в settings.py
        frontend_reset_url = f"{global_settings.FRONTEND_URL}/reset-password?token={reset_token}" # Шлях `/reset-password` визначається логікою фронтенд-додатку.

        logger.info(
            f"Токен скидання паролю для {user.email}: {reset_token}. Посилання: {frontend_reset_url}")  # Тільки для розробки!

        # Надсилання email у фоновому режимі
        # TODO: Реалізувати надсилання email через NotificationService.
        # background_tasks.add_task(
        #     notification_service.create_notification_from_template,
        #     template_name="PASSWORD_RESET_REQUEST", # Потрібен такий шаблон
        #     user_id=user.id,
        #     context_data={"user_name": user.full_name or user.username, "reset_link": frontend_reset_url},
        #     # notification_type_override="EMAIL" # Якщо шаблон універсальний
        # )
        logger.warning(
            f"[ЗАГЛУШКА] Надсилання email для скидання пароля користувачу {user.email} з посиланням: {frontend_reset_url}")
    else:
        logger.info(
            f"Користувача з email '{request_data.email}' не знайдено або він неактивний. Надсилання email не відбувається.")

    # i18n
    return MessageResponse(
        message="Якщо ваша пошта зареєстрована та активна, ви отримаєте лист з інструкціями для відновлення паролю."
    )

# ПРИМІТКА: Цей ендпоінт залежить від реалізації методу `reset_password_with_token_flow`
# в `PasswordService`, який має валідувати токен, оновлювати пароль користувача
# та інвалідувати використаний токен.
@router.post(
    "/reset",  # Префікс /password
    response_model=MessageResponse,
    summary="Встановлення нового паролю",  # i18n
    description="Встановлює новий пароль, використовуючи токен відновлення."  # i18n
)
async def reset_password_endpoint(  # Перейменовано
        reset_data: PasswordResetConfirm,
        password_service: PasswordService = Depends(get_password_service)
        # user_service: UserService = Depends(get_user_service) # Не потрібен, якщо password_service все обробляє
):
    """
    Встановлює новий пароль для користувача.

    - **token**: Токен відновлення паролю.
    - **new_password**: Новий пароль.
    """
    logger.info(f"Спроба скидання паролю з токеном (перші 8 символів): {reset_data.token[:8]}...")
    try:
        # PasswordService.reset_password_with_token має валідувати токен, знайти користувача,
        # оновити пароль та інвалідувати токен.
        # Припускаємо, що метод повертає user_id або кидає ValueError/HTTPException.
        # Або, якщо він повертає bool:
        success = await password_service.reset_password_with_token_flow(
            plain_token=reset_data.token,
            new_password=reset_data.new_password
        )  # Потрібно додати такий метод до PasswordService

        if not success:
            # i18n
            # Причина може бути різною (токен невалідний, користувач не знайдений),
            # але для безпеки можна повернути загальне повідомлення.
            # PasswordService має логувати конкретну причину.
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Не вдалося скинути пароль. Можливо, токен недійсний, прострочений або користувач не знайдений.")

    except ValueError as e:  # Якщо PasswordService кидає ValueError для конкретних помилок
        logger.warning(f"Помилка скидання пароля (токен: {reset_data.token[:8]}...): {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except HTTPException as http_exc:  # Якщо сервіс кидає HTTPException
        raise http_exc
    except Exception as e:
        logger.error(f"Неочікувана помилка скидання пароля (токен: {reset_data.token[:8]}...): {e}",
                     exc_info=global_settings.DEBUG)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Виникла помилка сервера при спробі скинути пароль.")

    # i18n
    return MessageResponse(message="Пароль успішно скинуто та встановлено новий.")


logger.info("Роутер для управління паролями (`/password/*`) визначено.")
