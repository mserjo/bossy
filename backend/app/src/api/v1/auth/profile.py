# backend/app/src/api/v1/auth/profile.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для управління профілем поточного користувача.

Сумісність: Python 3.13, SQLAlchemy v2, Pydantic v2.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession  # Не використовується прямо, якщо сесія інкапсульована в сервісах

from backend.app.src.api.dependencies import get_api_db_session, get_current_active_user, get_user_service
from backend.app.src.models.auth.user import User as UserModel  # Модель SQLAlchemy
from backend.app.src.schemas.auth.user import UserResponse, UserUpdate  # Схеми Pydantic
from backend.app.src.services.auth.user import UserService
from backend.app.src.config import settings as global_settings  # Для доступу до DEBUG тощо
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

router = APIRouter()


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Отримання профілю поточного користувача",  # i18n
    description="Повертає дані профілю для поточного автентифікованого та активного користувача."  # i18n
)
async def read_current_user_profile(  # Перейменовано для уникнення конфлікту з FastAPI Users (якщо буде)
        current_user: UserModel = Depends(get_current_active_user)
        # Залежність для отримання поточного активного користувача
):
    """
    Надає інформацію профілю поточного автентифікованого користувача.
    Дані користувача (модель SQLAlchemy) автоматично перетворюються на відповідь
    за допомогою Pydantic схеми `UserResponse`.
    """
    logger.info(f"Запит профілю для користувача: {current_user.username} (ID: {current_user.id})")
    # UserModel вже містить всі необхідні дані, Pydantic модель UserResponse відфільтрує потрібні.
    # Pydantic v2 .model_validate() використовується неявно FastAPI при поверненні ORM моделі з response_model
    return current_user

# ПРИМІТКА: Функціональність оновлення профілю залежить від реалізації методу `update_user`
# в `UserService`, включаючи логіку валідації (наприклад, унікальність username/email,
# якщо вони змінюються) та визначення полів, які користувач може самостійно оновлювати
# (див. TODO нижче).
@router.put(
    "/me",
    response_model=UserResponse,
    summary="Оновлення профілю поточного користувача",  # i18n
    description="Дозволяє поточному аутентифікованому користувачу оновити дані свого профілю."  # i18n
)
async def update_current_user_profile(  # Перейменовано
        user_update_data: UserUpdate,  # Схема для оновлення, містить тільки дозволені поля
        current_user: UserModel = Depends(get_current_active_user),
        user_service: UserService = Depends(get_user_service)  # Ін'єкція UserService
):
    """
    Оновлює профіль поточного автентифікованого користувача.
    Дозволяє змінювати такі поля, як ім'я, прізвище тощо.
    Зміна email та пароля зазвичай відбувається через окремі, більш захищені ендпоінти.

    Приклад полів в `UserUpdate` (визначається в `schemas/auth/user.py`):
    - `first_name: Optional[str]`
    - `last_name: Optional[str]`
    - `username: Optional[constr(min_length=3)]` (якщо дозволено змінювати і має бути унікальним)
    - `phone_number: Optional[str]`
    - `avatar_file_id: Optional[UUID]` (для встановлення нового аватара)
    """
    logger.info(
        f"Користувач ID '{current_user.id}' намагається оновити свій профіль з даними: {user_update_data.model_dump(exclude_unset=True)}")

    # TODO: Уточнити, які саме поля дозволено оновлювати користувачу через UserUpdate.
    #  Наприклад, зміна email або username може вимагати окремих потоків або додаткових перевірок,
    #  які краще інкапсулювати в UserService.update_user.

    try:
        # UserService.update_user має обробляти логіку валідації (наприклад, унікальність username/email, якщо вони змінюються)
        # та повертати оновлену ORM модель користувача або кидати ValueError/HTTPException.
        updated_user_orm = await user_service.update_user(
            user_id=current_user.id,
            user_update_data=user_update_data,
            # current_user_id=current_user.id # Якщо сервіс потребує знати, хто виконує оновлення (для аудиту)
            is_admin_update=False  # Користувач оновлює свій профіль, не адмін
        )
        if not updated_user_orm:  # Малоймовірно, якщо сервіс кидає винятки при помилках
            logger.error(f"Оновлення профілю для ID '{current_user.id}' повернуло None з сервісу.")
            # i18n
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Не вдалося оновити профіль.")

        logger.info(f"Профіль користувача ID '{current_user.id}' успішно оновлено.")
        # Pydantic v2 .model_validate() використовується неявно FastAPI
        return updated_user_orm
    except ValueError as e:  # Обробка помилок валідації з сервісного шару (наприклад, email/username зайнято)
        logger.warning(f"Помилка валідації при оновленні профілю ID '{current_user.id}': {e}")
        # i18n (повідомлення `e` вже має бути інтернаціоналізоване або зрозумілим для користувача)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:  # Якщо сервіс кидає PermissionError
        logger.warning(f"Спроба неавторизованого оновлення профілю ID '{current_user.id}': {e}")
        # i18n
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.error(f"Неочікувана помилка при оновленні профілю ID '{current_user.id}': {e}",
                     exc_info=global_settings.DEBUG)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Виникла помилка сервера при оновленні профілю.")


logger.info("Роутер для профілю користувача (`/profile`) визначено.")
