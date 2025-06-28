# backend/app/src/api/dependencies.py
# -*- coding: utf-8 -*-
"""
Модуль для специфічних залежностей (dependencies) FastAPI, що використовуються в API.

Цей файл містить функції-залежності, які можуть бути використані в ендпоінтах API
для різних цілей, таких як:
- Перевірка автентифікації та авторизації користувача.
- Отримання поточного користувача.
- Забезпечення доступу до сесії бази даних.
- Валідація параметрів запиту або заголовків.
- Реалізація специфічних для API перевірок або логіки.

Використання залежностей допомагає дотримуватися принципу DRY (Don't Repeat Yourself)
та покращує читабельність і структуру коду ендпоінтів.
"""

from typing import AsyncGenerator, Annotated, Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

# Імпортуємо функцію для отримання сесії БД з core.dependencies або config.database
# Припускаємо, що get_db_session визначено в backend.app.src.config.database, як у health.py
from jose import jwt # Додано для обробки JWTError
from backend.app.src.config.database import get_db_session as core_get_db_session
from backend.app.src.config.logging import get_logger
from backend.app.src.models.auth.user import UserModel
from backend.app.src.services.auth.user_service import UserService
from backend.app.src.schemas.auth.token import TokenPayloadSchema # Потрібно для get_current_user
from backend.app.src.config.security import oauth2_scheme # Потрібно для get_current_user
from backend.app.src.core.security import decode_access_token # Потрібно для get_current_user

logger = get_logger(__name__)

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Асинхронна залежність для отримання сесії бази даних.
    Використовує основну функцію отримання сесії.
    """
    async with core_get_db_session() as session:
        yield session

DBSession = Annotated[AsyncSession, Depends(get_async_session)]


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db_session: DBSession = Depends(get_async_session) # Використовуємо вже визначену DBSession
) -> UserModel:
    """
    Залежність для отримання поточного автентифікованого користувача з токена.

    Args:
        token (str): JWT токен доступу, отриманий зі схеми OAuth2.
        db_session (AsyncSession): Сесія бази даних.

    Raises:
        HTTPException: Якщо токен недійсний, термін дії закінчився, або користувач не знайдений.

    Returns:
        UserModel: Об'єкт моделі поточного користувача.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не вдалося валідувати облікові дані",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload_dict = decode_access_token(token) # Використовуємо функцію з core.security
        if payload_dict is None:
            logger.warning("Не вдалося декодувати токен або токен порожній.")
            raise credentials_exception
        token_data = TokenPayloadSchema(**payload_dict)
    except jwt.ExpiredSignatureError:
        logger.warning("Термін дії токена закінчився.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Термін дії токена закінчився",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTError as e: # Більш загальний виняток JWT з python-jose
        logger.warning(f"Помилка валідації JWT токена: {e}")
        raise credentials_exception
    except Exception as e: # Інші можливі винятки (наприклад, при розборі payload_dict в TokenPayloadSchema)
        logger.error(f"Неочікувана помилка під час обробки токена: {e}", exc_info=True)
        raise credentials_exception

    user_service = UserService(db_session)
    # Пошук за user_id (sub) з токена
    user_id = token_data.sub
    if user_id is None: # Додаткова перевірка, хоча sub зазвичай є в JWT
        logger.warning("В токені відсутній ідентифікатор користувача (sub).")
        raise credentials_exception

    user = await user_service.get_user_by_id(user_id=int(user_id)) # Припускаємо, що user_id це int

    if user is None:
        logger.warning(f"Користувача з ID {user_id} з токена не знайдено в БД.")
        raise credentials_exception
    logger.info(f"Користувача {user.email} (ID: {user.id}) успішно отримано з токена.")
    return user

CurrentUser = Annotated[UserModel, Depends(get_current_user)]


async def get_current_active_user(
    current_user: CurrentUser = Depends(get_current_user) # Використовуємо вже визначену CurrentUser
) -> UserModel:
    """
    Залежність для отримання поточного активного автентифікованого користувача.

    Args:
        current_user (UserModel): Поточний користувач, отриманий з `get_current_user`.

    Raises:
        HTTPException: Якщо користувач неактивний.

    Returns:
        UserModel: Об'єкт моделі активного користувача.
    """
    if not current_user.is_active:
        logger.warning(f"Користувач {current_user.email} (ID: {current_user.id}) неактивний.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Неактивний користувач")
    logger.info(f"Активний користувач {current_user.email} (ID: {current_user.id}) підтверджений.")
    return current_user

CurrentActiveUser = Annotated[UserModel, Depends(get_current_active_user)]


async def get_current_superuser(
    current_active_user: CurrentActiveUser = Depends(get_current_active_user) # Використовуємо CurrentActiveUser
) -> UserModel:
    """
    Залежність для отримання поточного користувача з правами суперкористувача.

    Args:
        current_active_user (UserModel): Поточний активний користувач.

    Raises:
        HTTPException: Якщо користувач не є суперкористувачем.

    Returns:
        UserModel: Об'єкт моделі користувача з правами суперкористувача.
    """
    # Припускаємо, що UserModel має поле is_superuser або логіка перевірки ролі є в UserService
    # Наприклад, якщо є поле is_superuser:
    if not current_active_user.is_superuser:
         logger.warning(
            f"Користувач {current_active_user.email} (ID: {current_active_user.id}) "
            "не має прав суперкористувача."
        )
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Користувач не має достатньо прав (потрібен суперкористувач)"
        )
    logger.info(f"Суперкористувач {current_active_user.email} (ID: {current_active_user.id}) підтверджений.")
    return current_active_user

CurrentSuperuser = Annotated[UserModel, Depends(get_current_superuser)]

# TODO: Додати інші специфічні для API залежності, якщо потрібно.
# Наприклад, залежності для перевірки прав доступу до певних ресурсів на основі ролей,
# отримання API ключів, тощо.
#
# Приклад залежності для перевірки ролі адміністратора групи (потребує GroupService та GroupMembershipModel):
# async def get_current_group_admin(
#     group_id: int, # Або інший ідентифікатор групи, що передається в шляху/запиті
#     current_user: CurrentActiveUser = Depends(get_current_active_user),
#     db_session: DBSession = Depends(get_async_session)
# ) -> UserModel:
#     group_service = GroupService(db_session) # Припустимо, є GroupService
#     is_admin = await group_service.is_user_group_admin(user_id=current_user.id, group_id=group_id)
#     if not is_admin:
#         logger.warning(f"Користувач {current_user.email} не є адміном групи {group_id}.")
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Ви не є адміністратором цієї групи."
#         )
#     return current_user
