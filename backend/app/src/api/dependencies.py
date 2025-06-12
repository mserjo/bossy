# backend/app/src/api/dependencies.py
# -*- coding: utf-8 -*-
"""
Модуль для визначення загальних залежностей (dependencies) для API ендпоінтів FastAPI.
"""

# import logging # Замінено на централізований логер
from typing import AsyncGenerator, Optional, Any, Dict  # AsyncGenerator для сесії БД

from fastapi import Depends, HTTPException, status, Path, Query  # Додано Path, Query
from fastapi.security import OAuth2PasswordBearer

# Повні шляхи імпорту
from backend.app.src.config.logging import logger  # Централізований логер
from backend.app.src.config.settings import settings
from backend.app.src.core.database import get_db_session  # Припускаємо, що ця функція існує
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.src.services import (  # Імпортуємо реальні сервіси
    UserService,
    TokenService,
    GroupMembershipService  # Для перевірки адміна групи
)
from backend.app.src.models.auth.user import User as UserModel  # Модель SQLAlchemy для користувача
from backend.app.src.schemas.auth.token import TokenPayload  # Схема Pydantic для payload токена
from backend.app.src.models.dictionaries.user_roles import UserRole  # Для перевірки ролі в групі


# --- Залежність для сесії бази даних ---
async def get_api_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Залежність FastAPI для надання асинхронної сесії бази даних.
    Використовує контекстний менеджер `get_db_session` з `core.database`.
    """
    async for session in get_db_session():  # Припускаємо, що get_db_session є async generator
        logger.debug(f"Сесію БД {id(session)} надано для API ендпоінта.")
        yield session


# --- Схема OAuth2 ---
# TODO: Перевірити та оновити tokenUrl на фактичний URL ендпоінта логіну, коли він буде визначений.
# Наприклад: f"{settings.API_V1_PREFIX}/auth/token" або f"{settings.API_V1_PREFIX}/auth/login"
OAUTH2_SCHEME = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login/token")


# --- Залежності для автентифікації та авторизації ---

# Ініціалізація сервісів (може бути краще через систему DI, якщо використовується)
# Для простоти поки що так, але це створюватиме нові екземпляри сервісів на кожен запит, що потребує сесії.
# Краще, якщо сервіси ін'єктуються з сесією вже в них.

async def get_token_service(session: AsyncSession = Depends(get_api_db_session)) -> TokenService:
    """Залежність для отримання екземпляра TokenService."""
    return TokenService(db_session=session)


async def get_user_service(session: AsyncSession = Depends(get_api_db_session)) -> UserService:
    """Залежність для отримання екземпляра UserService."""
    return UserService(db_session=session)


async def get_group_membership_service(session: AsyncSession = Depends(get_api_db_session)) -> GroupMembershipService:
    """Залежність для отримання екземпляра GroupMembershipService."""
    return GroupMembershipService(db_session=session)


async def get_current_user_payload(
        token: str = Depends(OAUTH2_SCHEME),
        token_service: TokenService = Depends(get_token_service)
) -> TokenPayload:
    """
    Отримує та валідує JWT токен з Authorization header, повертає його payload.
    Використовує TokenService.validate_access_token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не вдалося валідувати облікові дані",  # i18n
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload_dict = await token_service.validate_access_token(token=token)
    if not payload_dict or payload_dict.get("sub") is None:
        logger.warning(f"Невалідний токен або відсутній 'sub'. Токен: {token[:15]}...")
        raise credentials_exception

    # TODO: Переконатися, що TokenPayload схема відповідає вмісту payload_dict
    #  і обробляє можливі помилки валідації Pydantic.
    try:
        token_payload = TokenPayload(**payload_dict)
    except Exception as e:  # Наприклад, pydantic.ValidationError
        logger.warning(f"Помилка валідації TokenPayload: {e}. Payload: {payload_dict}")
        raise credentials_exception

    logger.debug(f"Payload токена успішно отримано для sub: {token_payload.sub}")
    return token_payload


async def get_current_user(
        payload: TokenPayload = Depends(get_current_user_payload),
        user_service: UserService = Depends(get_user_service)
) -> UserModel:  # Повертає модель SQLAlchemy User
    """
    Отримує поточного користувача з бази даних на основі user_id ('sub') з payload токена.
    """
    if not payload.sub:  # sub має бути UUID
        logger.warning("Відсутній 'sub' (user_id) в payload токена.")
        # i18n
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Некоректний формат токена.")

    # Повертаємо ORM модель, а не Pydantic схему, для внутрішнього використання в інших залежностях/ендпоінтах
    user = await user_service.get_user_orm_by_id(user_id=payload.sub)
    if user is None:
        logger.warning(f"Користувача з id '{payload.sub}' (з токена) не знайдено в БД.")
        # i18n
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Користувача, пов'язаного з токеном, не знайдено.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    logger.debug(f"Користувача '{user.username}' (id: {user.id}) отримано з БД.")
    return user


async def get_current_active_user(
        current_user: UserModel = Depends(get_current_user)
) -> UserModel:
    """
    Отримує поточного автентифікованого та активного користувача.
    Якщо користувач неактивний, викликає помилку HTTP 403 Forbidden.
    """
    if not current_user.is_active:
        logger.warning(f"Спроба доступу неактивним користувачем '{current_user.username}' (id: {current_user.id}).")
        # i18n
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Обліковий запис користувача неактивний.")
    logger.debug(f"Користувач '{current_user.username}' активний.")
    return current_user


async def get_current_active_superuser(
        current_user: UserModel = Depends(get_current_active_user)
) -> UserModel:
    """
    Перевіряє, чи поточний активний користувач є суперюзером.
    Якщо ні, викликає помилку HTTP 403 Forbidden.
    """
    if not current_user.is_superuser:
        logger.warning(
            f"Користувач '{current_user.username}' (id: {current_user.id}) не є суперюзером. Доступ заборонено."
        )
        # i18n
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостатньо прав: потрібні права суперкористувача."
        )
    logger.debug(f"Користувач '{current_user.username}' успішно авторизований як суперюзер.")
    return current_user


async def get_current_active_group_admin(
        group_id: UUID = Path(..., description="ID групи для перевірки прав адміністратора"),  # i18n
        current_user: UserModel = Depends(get_current_active_user),
        membership_service: GroupMembershipService = Depends(get_group_membership_service)
) -> UserModel:
    """
    Перевіряє, чи поточний активний користувач є адміністратором вказаної групи.
    Суперкористувачі також проходять цю перевірку.

    :param group_id: ID групи, отриманий з шляху URL.
    :param current_user: Поточний активний користувач (залежність).
    :param membership_service: Сервіс членства в групах (залежність).
    :return: Об'єкт поточного користувача, якщо він є адміном групи або суперюзером.
    :raises HTTPException: 403, якщо користувач не має відповідних прав.
                           404, якщо групу або членство не знайдено (обробляється в membership_service).
    """
    logger.debug(
        f"Перевірка прав адміна групи для користувача '{current_user.username}' (ID: {current_user.id}) в групі ID: {group_id}")
    if current_user.is_superuser:
        logger.debug(f"Користувач '{current_user.username}' є суперюзером, доступ дозволено.")
        return current_user

    # TODO: Додати в GroupMembershipService метод `check_user_role_in_group(user_id, group_id, role_code)`
    #  або `is_user_group_admin(user_id, group_id)` для більш чистої перевірки.
    #  Поточний `get_membership_details` може повернути None, якщо членства немає.
    membership = await membership_service.get_membership_details(group_id=group_id, user_id=current_user.id)

    if not membership or not membership.is_active or not membership.role:
        logger.warning(
            f"Користувач '{current_user.username}' не є активним членом або не має ролі в групі ID '{group_id}'.")
        # i18n
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Ви не є активним членом цієї групи або не маєте призначеної ролі.")

    if membership.role.code != ADMIN_ROLE_CODE:  # Припускаємо, що ADMIN_ROLE_CODE це "ADMIN"
        logger.warning(
            f"Користувач '{current_user.username}' (ID: {current_user.id}) не є адміністратором групи ID '{group_id}' (роль: {membership.role.code}). Доступ заборонено."
        )
        # i18n
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостатньо прав: потрібні права адміністратора цієї групи."
        )

    logger.debug(f"Користувач '{current_user.username}' авторизований як адміністратор групи ID '{group_id}'.")
    return current_user


# --- Залежність для пагінації ---
async def get_pagination_params(
        skip: int = Query(0, ge=0, description="Кількість елементів для пропуску (для пагінації)"),  # i18n
        limit: int = Query(global_settings.DEFAULT_PAGE_SIZE, ge=1, le=global_settings.MAX_PAGE_SIZE,
                           description="Максимальна кількість елементів для повернення (для пагінації)")  # i18n
) -> Dict[str, int]:
    """
    Отримує параметри пагінації `skip` та `limit` з параметрів запиту.
    Використовує значення за замовчуванням та максимальні ліміти з конфігурації.
    """
    return {"skip": skip, "limit": limit}


logger.info("Модуль залежностей 'api.dependencies' завантажено та налаштовано з реальними сервісами.")
