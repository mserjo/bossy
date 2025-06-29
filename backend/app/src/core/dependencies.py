# backend/app/src/core/dependencies.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає залежності (dependencies) FastAPI, які використовуються
в ендпоінтах для отримання спільних ресурсів (наприклад, сесії БД)
або для виконання перевірок (наприклад, автентифікація, авторизація).
"""
import uuid

from fastapi import Depends, HTTPException, Security
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from jose import JWTError, jwt # type: ignore
from pydantic import ValidationError, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore
from typing import Optional, List, Any

# Імпорт налаштувань та утиліт
from backend.app.src.config.database import get_async_session # Фабрика сесій БД
from backend.app.src.config.settings import settings
from backend.app.src.config.security import ALGORITHM, SECRET_KEY # Параметри JWT
from backend.app.src.core.exceptions import UnauthorizedException, ForbiddenException, NotFoundException
# Імпорт констант для ролей (якщо перевірка ролей тут)
from backend.app.src.core.constants import ROLE_SUPERADMIN_CODE, ROLE_ADMIN_CODE, ROLE_USER_CODE, USER_TYPE_SUPERADMIN
# Імпорт схем для токенів та користувачів
from backend.app.src.schemas.auth.token import TokenPayloadSchema
from backend.app.src.schemas.auth.user import UserSchema
# Імпорт сервісів
# from backend.app.src.services.auth.user_service import UserService # Реальний імпорт - ПЕРЕМІЩЕНО

# --- Залежність для OAuth2 (отримання токена з заголовка Authorization: Bearer <token>) ---
# `tokenUrl` вказує на ендпоінт, де клієнт може отримати токен (для документації Swagger).
# Це має бути відносний шлях до ендпоінта логіну.
# Наприклад, якщо ендпоінт логіну `/api/v1/auth/login`, то tokenUrl="auth/login" (відносно API_V1_STR).
# Або повний шлях. Поки що залишу відносний.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.app.API_V1_STR}/auth/login/token")


# --- Залежність для отримання поточного активного користувача ---
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_async_session)
) -> UserSchema: # Повертає Pydantic схему користувача, а не ORM модель
    """
    Отримує та валідує JWT токен, повертає дані користувача.
    Викликає UnauthorizedException, якщо токен невалідний або користувач не знайдений/неактивний.
    """
    from backend.app.src.services.auth.user_service import UserService # Локальний імпорт для розриву циклу
    credentials_exception = UnauthorizedException(detail="Не вдалося валідувати облікові дані")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Перевірка типу токена (якщо є поле 'type' в payload)
        # token_type: Optional[str] = payload.get("type")
        # if token_type != "access": # Або константа TOKEN_TYPE_ACCESS
        #     raise credentials_exception

        # Отримання ID користувача з токена
        user_id_str: Optional[str] = payload.get("sub") # "sub" - стандартне поле для ідентифікатора суб'єкта
        if user_id_str is None:
            raise credentials_exception

        try:
            user_id = uuid.UUID(user_id_str) # Перетворюємо рядок в UUID
        except ValueError:
            raise credentials_exception # Якщо user_id не валідний UUID

        # Валідація payload за допомогою Pydantic схеми
        try:
            token_data = TokenPayloadSchema.model_validate(payload)
        except ValidationError:
            raise credentials_exception

        user_id = token_data.sub # user_id тепер є uuid.UUID завдяки валідатору в TokenPayloadSchema

        # Перевірка типу токена (якщо потрібно)
        if token_data.token_type and token_data.token_type != "access":
             raise UnauthorizedException(detail="Некоректний тип токена, очікується 'access'")

    except JWTError: # Включає ExpiredSignatureError, InvalidTokenError тощо.
        raise credentials_exception
    # ValidationError вже оброблено вище

    # Отримання користувача з БД за user_id
    # Створюємо екземпляр UserService з поточною сесією БД
    user_service = UserService(db)
    user_model: Optional[Any] = None # Використовуємо Any, щоб уникнути імпорту UserModel тут

    try:
        # Викликаємо метод сервісу, який повертає UserModel та кидає винятки
        user_model = await user_service.get_active_user_by_id_for_auth(user_id=user_id)
        # Цей метод вже має робити всі перевірки (is_deleted, state_id на активність).
        # Якщо користувач не знайдений або не активний, сервіс кидає NotFoundException або ForbiddenException.
    except NotFoundException:
        raise credentials_exception
    except ForbiddenException as e: # Якщо get_active_user_by_id_for_auth кидає ForbiddenException
        raise UnauthorizedException(detail=e.detail) # Перетворюємо на Unauthorized для контексту токена

    if user_model is None: # Додаткова перевірка, хоча сервіс мав би кинути виняток
        raise credentials_exception

    # Повертаємо UserModel напряму, а не UserSchema
    return user_model

# Функція get_current_active_user видалена, оскільки get_current_user тепер виконує її роль.

# --- Залежності для перевірки ролей ---
# Ці залежності використовують `get_current_user` (яка вже гарантує активного користувача).

async def get_current_superuser(
    current_user: UserSchema = Depends(get_current_user) # Змінено на get_current_user
) -> UserSchema:
    """
    Перевіряє, чи є поточний користувач супер-адміністратором.
    Викликає ForbiddenException, якщо ні.
    """
    # `user_type_code` зберігається в `UserModel` та `UserSchema`.
    if current_user.user_type_code != USER_TYPE_SUPERADMIN:
        # Або, якщо ролі зберігаються в окремому полі/зв'язку:
        # if ROLE_SUPERADMIN_CODE not in [role.code for role in current_user.roles]:
        raise ForbiddenException(detail="Недостатньо прав: потрібен рівень супер-адміністратора.")
    return current_user

# TODO: Додати залежності для інших ролей, якщо потрібно.
# Наприклад, `get_current_group_admin` (потребуватиме `group_id` з шляху для перевірки).
# async def get_current_group_admin(
#     group_id: uuid.UUID, # З параметра шляху
#     current_user: UserSchema = Depends(get_current_active_user),
#     db: AsyncSession = Depends(get_async_session)
# ) -> UserSchema:
#     # Потрібно перевірити членство користувача в групі group_id та його роль.
#     # Це вимагає доступу до GroupMembershipModel та UserService/GroupService.
#     # ... логіка перевірки ...
#     is_admin = await check_user_is_group_admin(db, current_user.id, group_id) # Приклад функції
#     if not is_admin:
#         raise ForbiddenException(detail=f"Ви не є адміністратором групи {group_id}.")
#     return current_user


# --- Залежність для опціонального поточного користувача ---
async def get_optional_current_user(
    token: Optional[str] = Depends(oauth2_scheme) if settings.app.ENVIRONMENT != "testing" else None, # У тестах токен може бути відсутнім
    db: AsyncSession = Depends(get_async_session)
) -> Optional[UserSchema]:
    """
    Намагається отримати поточного користувача, якщо токен надано.
    Повертає None, якщо токен відсутній або невалідний (не кидає виняток).
    Корисно для ендпоінтів, які мають різну поведінку для автентифікованих
    та анонімних користувачів.
    """
    if token is None: # Якщо токен не передано (наприклад, для публічного доступу або в тестах)
        return None
    try:
        # Намагаємося отримати користувача через get_current_user
        # Передаємо db явно, оскільки Depends не викликається тут напряму для get_db_session
        # get_current_user повертає UserSchema
        user_schema = await get_current_user(token=token, db=db)
        return user_schema # Повертаємо UserSchema або None, якщо get_current_user кинув виняток
    except HTTPException: # Ловимо UnauthorizedException та ForbiddenException, які кидає get_current_user
        return None

# --- Залежність для API ключа (якщо використовується) ---
# api_key_header_auth = APIKeyHeader(name="X-API-Key", auto_error=True)
# async def get_api_key(api_key: str = Security(api_key_header_auth)) -> str:
#     # Тут має бути логіка перевірки API ключа (наприклад, з БД або конфігурації)
#     # У `settings` можна додати список валідних API ключів.
#     # VALID_API_KEYS = settings.app.VALID_API_KEYS (List[str])
#     if api_key in settings.app.VALID_API_KEYS: # Приклад
#         return api_key
#     else:
#         raise UnauthorizedException(detail="Невалідний або відсутній API ключ")

# TODO: Замінити імітацію отримання користувача в `get_current_user`
# на реальні виклики відповідного сервісу (наприклад, `UserService.get_active_user_by_id_for_auth`).
# Це потребуватиме створення `UserService`.
#
# TODO: Розширити перевірку активності користувача в `get_current_user` (має робити сервіс)
# (наприклад, перевірка `state_id` на відповідність активному статусу).
#
# TODO: Реалізувати залежності для перевірки ролей в контексті групи
# (наприклад, `get_current_group_admin`, `get_current_group_member`).
# Це потребуватиме `group_id` як параметра шляху та логіки перевірки
# членства та ролі в `GroupMembershipModel`.
#
# `oauth2_scheme` налаштований.
# `get_db_session` імпортується з `config.database`.
# Базові залежності `get_current_user`, `get_current_active_user`, `get_current_superuser`,
# `get_optional_current_user` визначені.
#
# Все виглядає як хороший початок для системи залежностей.
# Важливо, що `get_current_user` повертає Pydantic схему `UserSchema`,
# а не ORM модель, що є хорошою практикою для FastAPI.
#
# Для `get_optional_current_user`: в тестах токен може бути відсутнім,
# тому `Depends(oauth2_scheme)` робиться умовним.
# Якщо `settings.app.ENVIRONMENT == "testing"`, то `token` може бути `None`.
# Це дозволяє тестувати ендпоінти без обов'язкової автентифікації, якщо логіка це підтримує.
# Або ж, у тестах можна використовувати `app.dependency_overrides` для мокання автентифікації.
# Поточний підхід з умовним `Depends` є одним з варіантів.
#
# Все готово.
