# backend/app/src/core/dependencies.py
# -*- coding: utf-8 -*-
"""
Загальні залежності для FastAPI програми Kudos.

Цей модуль визначає залежності, що використовуються в обробниках запитів FastAPI,
зокрема для автентифікації та авторизації користувачів. Вони включають:
- Отримання поточного користувача на основі JWT токена.
- Перевірку активності користувача.
- Перевірку прав суперкористувача.
- Заготовки для більш складних перевірок (наприклад, адміністратор групи).

Залежності використовують `OAuth2PasswordBearer` для отримання токенів,
функції декодування токенів з `config.security` та сесію бази даних з `config.database`.

ВАЖЛИВО: Моделі `UserModel` та `TokenPayload` наразі є заповнювачами (placeholders).
Їх потрібно буде замінити на реальні імпорти з відповідних модулів
(`models.auth.user` та `schemas.auth.token`) після їх створення/рефакторингу.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status, Path # Added Path
from fastapi.security import OAuth2PasswordBearer
# from jose import JWTError
from pydantic import ValidationError # BaseModel removed as TokenPayload is now imported
from datetime import datetime, timezone, timedelta

# SQLAlchemy select
from sqlalchemy import select

# Абсолютні імпорти з проекту
from backend.app.src.config.settings import settings
from backend.app.src.config.security import decode_token
from backend.app.src.config.database import get_db, AsyncSession
from backend.app.src.config.logging import get_logger

# Реальні імпорти для UserModel та TokenPayload
from backend.app.src.models.auth.user import User as UserModel
from backend.app.src.schemas.auth.token import TokenPayload

# Імпорти для get_current_group_admin
from backend.app.src.models.groups.membership import GroupMembership
from backend.app.src.core.dicts import GroupRole

logger = get_logger(__name__)

from backend.app.src.core.i18n import _ # Import the real translation function

# `OAuth2PasswordBearer` - це клас FastAPI, що допомагає отримувати токени Bearer
# з заголовка "Authorization".
# `tokenUrl` має вказувати на ендпоінт для входу в систему (де користувач отримує токен).
reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login/access-token" # Оновлено для відповідності типовому ендпоінту
)

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(reusable_oauth2)
) -> UserModel: # Тип повернення має бути реальним UserModel
    """
    Залежність FastAPI для отримання поточного автентифікованого користувача з JWT токена.

    Виконує декодування токена, перевірку його типу ("access") та отримання
    користувача з бази даних (наразі через логіку-заповнювач).

    Args:
        db (AsyncSession): Асинхронна сесія бази даних.
        token (str): JWT токен, отриманий з заголовка Authorization.

    Returns:
        UserModel: Об'єкт користувача, якщо автентифікація успішна.

    Raises:
        HTTPException (401): Якщо токен недійсний, прострочений, має неправильний тип,
                             або якщо користувача не знайдено.
        HTTPException (400): Якщо корисне навантаження токена пошкоджене або не містить
                             необхідних даних.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=_("dependencies.auth.credentials_check_failed"),
        headers={"WWW-Authenticate": "Bearer"},
    )
    malformed_payload_exception = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=_("dependencies.auth.malformed_token_payload")
    )

    payload = decode_token(token) # decode_token вже логує помилки JWT
    if payload is None:
        # decode_token поверне None, якщо токен недійсний (прострочений, невірний підпис, iss, aud тощо)
        # Логування вже відбулося в decode_token.
        raise credentials_exception

    try:
        # Pydantic v2 uses model_validate, v1 uses parse_obj or direct instantiation
        if hasattr(TokenPayload, 'model_validate'):
            token_data = TokenPayload.model_validate(payload)
        else: # Fallback for Pydantic v1 or if model_validate is not standard
            token_data = TokenPayload(**payload)
    except ValidationError as e:
        logger.warning(f"Помилка валідації TokenPayload: {e}", exc_info=True)
        raise malformed_payload_exception

    if token_data.type != "access":
        logger.warning(f"Отримано невірний тип токена: '{token_data.type}'. Очікувався 'access'.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_("dependencies.auth.invalid_token_type"),
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_identifier = token_data.sub or (str(token_data.user_id) if token_data.user_id is not None else None)
    if user_identifier is None:
        logger.warning("Ідентифікатор користувача (sub або user_id) відсутній у токені.")
        raise malformed_payload_exception

    # --- TODO: Замінити логіку-заповнювач на реальне отримання користувача з БД ---
    # Поточна логіка є лише для демонстрації та тестування.
    # У реальній системі тут має бути виклик до сервісу або репозиторію користувачів:
    # Наприклад:
    # from backend.app.src.services.auth.user_service import UserService # Потрібно створити
    # user_service = UserService(db)
    # current_user = await user_service.get_user_by_identifier(user_identifier)
    # Або напряму через репозиторій:
    # from backend.app.src.repositories.auth.user_repository import user_repository # Потрібно створити
    # current_user = await user_repository.get_by_email_or_id(db, identifier=user_identifier)

    current_user: Optional[UserModel] = None
    logger.debug(f"Спроба знайти користувача за ідентифікатором: {user_identifier}")
    if user_identifier == "testuser@example.com" or user_identifier == "123":
        current_user = UserModel(id=123, email="testuser@example.com", is_active=True, is_superuser=False)
        logger.info(f"Знайдено тестового користувача-заповнювача: {user_identifier}")
    elif user_identifier == settings.FIRST_SUPERUSER_EMAIL:
        current_user = UserModel(id=1, email=settings.FIRST_SUPERUSER_EMAIL, is_active=True, is_superuser=True)
        logger.info(f"Знайдено суперкористувача-заповнювача: {user_identifier}")
    # --- Кінець TODO блоку ---

    if current_user is None:
        logger.warning(f"Користувача з ідентифікатором '{user_identifier}' не знайдено в базі даних (або в логіці-заповнювачі).")
        raise credentials_exception

    logger.info(f"Користувач '{current_user.email}' (ID: {current_user.id}) успішно автентифікований.")
    return current_user

async def get_current_active_user(
    current_user: UserModel = Depends(get_current_user)
) -> UserModel:
    """
    Залежність FastAPI для отримання поточного активного користувача.

    Використовує `get_current_user` для отримання користувача та додатково
    перевіряє, чи є поле `is_active` користувача встановленим в `True`.

    Args:
        current_user (UserModel): Об'єкт користувача, отриманий з `get_current_user`.

    Returns:
        UserModel: Об'єкт автентифікованого та активного користувача.

    Raises:
        HTTPException (403): Якщо користувач неактивний.
    """
    if not current_user.is_active:
        logger.warning(f"Користувач '{current_user.email}' (ID: {current_user.id}) неактивний.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=_("dependencies.auth.inactive_user"))
    logger.debug(f"Користувач '{current_user.email}' (ID: {current_user.id}) активний.")
    return current_user

async def get_current_superuser(
    current_active_user: UserModel = Depends(get_current_active_user)
) -> UserModel:
    """
    Залежність FastAPI для отримання поточного активного суперкористувача.

    Використовує `get_current_active_user` для отримання активного користувача
    та додатково перевіряє, чи є поле `is_superuser` встановленим в `True`.

    Args:
        current_active_user (UserModel): Об'єкт активного користувача, отриманий з `get_current_active_user`.

    Returns:
        UserModel: Об'єкт автентифікованого, активного суперкористувача.

    Raises:
        HTTPException (403): Якщо користувач не є суперкористувачем.
    """
    # Перевіряємо наявність атрибута is_superuser перед доступом до нього,
    # оскільки UserModel є заповнювачем і може не мати цього поля в майбутніх реальних моделях,
    # хоча поточний заповнювач його має.
    if not hasattr(current_active_user, 'is_superuser') or not current_active_user.is_superuser:
        logger.warning(
            f"Користувач '{current_active_user.email}' (ID: {current_active_user.id}) "
            "не має прав суперкористувача."
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=_("dependencies.auth.not_superuser")
        )
    logger.debug(f"Користувач '{current_active_user.email}' (ID: {current_active_user.id}) підтверджений як суперкористувач.")
    return current_active_user


async def get_current_group_admin(
    current_active_user: UserModel = Depends(get_current_active_user),
    group_id: int = Path(..., description="ID групи, до якої перевіряється доступ"),
    db: AsyncSession = Depends(get_db)
) -> UserModel:
    """
    Перевіряє, чи є поточний активний користувач адміністратором (або вищою роллю,
    наприклад, суперкористувачем) для вказаної групи.
    """
    logger.info(f"Перевірка прав адміністратора для користувача ID {current_active_user.id} у групі ID {group_id}")

    # Спочатку перевіримо, чи є користувач суперкористувачем - суперкористувачі мають доступ до всього.
    if hasattr(current_active_user, 'is_superuser') and current_active_user.is_superuser:
        logger.debug(f"Користувач ID {current_active_user.id} є суперкористувачем, надано доступ до групи ID {group_id}.")
        return current_active_user

    # Запит до бази даних для перевірки членства та ролі користувача в групі.
    stmt = select(GroupMembership).where(
        GroupMembership.user_id == current_active_user.id,
        GroupMembership.group_id == group_id
    )
    result = await db.execute(stmt)
    membership: Optional[GroupMembership] = result.scalar_one_or_none()

    if membership is None or membership.role != GroupRole.ADMIN:
        logger.warning(
            f"Користувач ID {current_active_user.id} не є адміністратором групи ID {group_id}. "
            f"Членство: {'знайдено' if membership else 'не знайдено'}, Роль: {membership.role if membership else 'N/A'}."
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=_("dependencies.auth.not_group_admin")
        )

    logger.info(f"Користувач ID {current_active_user.id} підтверджений як адміністратор групи ID {group_id}.")
    return current_active_user


# Блок для демонстрації та базового тестування при прямому запуску модуля.
if __name__ == "__main__":
    # Зазвичай, залежності FastAPI тестуються через інтеграційні тести з TestClient.
    # Цей блок лише для базової демонстрації структури.
    logger.info("--- Демонстрація модуля залежностей FastAPI ---")
    logger.info("Створено екземпляр OAuth2PasswordBearer для URL токена:")
    logger.info(f"  reusable_oauth2.scheme.tokenUrl = {reusable_oauth2.scheme.tokenUrl}")

    logger.info("\nВизначені основні залежності:")
    logger.info("- get_current_user: Отримує користувача з токена (використовує UserModel-заповнювач).")
    logger.info("- get_current_active_user: Перевіряє, чи активний користувач, отриманий з get_current_user.")
    logger.info("- get_current_superuser: Перевіряє, чи є активний користувач суперкористувачем.")
    logger.info("- get_current_group_admin: Залежність-заповнювач для перевірки адміністратора групи (потребує реалізації).")

    logger.info("\nПримітка: Для повноцінного тестування цих залежностей потрібен TestClient FastAPI,")
    logger.info("а також макети (mocks) для взаємодії з базою даних та функцією decode_token.")

    # Приклад створення екземпляра TokenPayload-заповнювача
    try:
        payload_demo_data = {
            "sub": "user@example.com",
            "user_id": 1,
            "type": "access",
            "exp": int((datetime.now(timezone.utc) + timedelta(minutes=15)).timestamp())
        }
        token_payload_instance = TokenPayload(**payload_demo_data)
        logger.info(f"\nПриклад екземпляра TokenPayload (заповнювач): {token_payload_instance.model_dump_json(indent=2)}")
    except ValidationError as e:
        logger.error(f"\nПомилка при створенні тестового TokenPayload: {e}")

    # Демонстрація UserModel-заповнювача
    logger.info(f"\nСтруктура UserModel-заповнювача: id, email, is_active, is_superuser")
    dummy_user = UserModel(id=1, email="dummy@example.com", is_active=True, is_superuser=False)
    logger.info(f"  Створено фіктивного користувача (заповнювач): id={dummy_user.id}, email='{dummy_user.email}', active={dummy_user.is_active}")
    logger.info("ВАЖЛИВО: UserModel та TokenPayload є заповнювачами і мають бути замінені реальними імпортами.")
