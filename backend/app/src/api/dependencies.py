# backend/app/src/api/dependencies.py
# -*- coding: utf-8 -*-
"""
Модуль для визначення загальних залежностей (dependencies) для API ендпоінтів.

Ці залежності використовуються FastAPI для ін'єкції даних або виконання
перевірок перед тим, як буде викликано основний обробник ендпоінта.
Типові приклади включають:
- Отримання сесії бази даних.
- Перевірка автентифікації користувача (наприклад, за JWT токеном).
- Перевірка авторизації (прав доступу) користувача.
"""

import logging
from typing import Generator, Optional, Any, Dict # Додано Dict

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer # Для схеми автентифікації OAuth2

# У реальному проекті, ці залежності будуть імпортуватися з відповідних сервісів та моделей
# from app.src.services.user_service import UserService # Приклад
# from app.src.services.token_service import TokenService # Приклад
# from app.src.models.user import User as UserModel # Приклад моделі користувача SQLAlchemy
# from app.src.schemas.auth.token import TokenPayload # Приклад схеми Pydantic для payload токена
# from app.src.core.database import get_db_session_context # Приклад отримання сесії БД
# from app.src.config.settings import settings # Для доступу до JWT_SECRET_KEY, ALGORITHM тощо

logger = logging.getLogger(__name__)

# --- Залежність для сесії бази даних ---
# Ця залежність, ймовірно, вже визначена в src/core/dependencies.py або src/core/database.py
# Якщо так, її можна імпортувати звідти, або визначити тут, якщо потрібна специфічна логіка для API.
# Наприклад (якщо AsyncSession використовується):
# from sqlalchemy.ext.asyncio import AsyncSession
# async def get_api_db_session() -> Generator[AsyncSession, None, None]:
#     # Припускаючи, що get_db_session_context() є асинхронним контекстним менеджером
#     # async with get_db_session_context() as session:
#     #     yield session
#     # Для прикладу, поки що не реалізовано, оскільки get_db_session_context не визначено.
 Hashing Algorithm #     logger.debug("Сесію БД надано для API ендпоінта.")
    pass


# --- Схема OAuth2 для отримання токена з Authorization header ---
# `tokenUrl` вказує на ендпоінт, де клієнт може отримати токен (наприклад, /api/v1/auth/login).
# Цей URL має відповідати реальному ендпоінту в системі.
# Для прикладу, використовуємо тимчасовий URL.
# У реальному проекті це буде, наприклад, f"{settings.API_V1_PREFIX}/auth/token"
OAUTH2_SCHEME = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token_placeholder")

# --- Залежності для автентифікації та авторизації ---

# Для прикладу, створимо фіктивні сервіси та моделі, щоб залежності мали до чого звертатися.
# У реальному проекті ці класи будуть значно складнішими та знаходитимуться у відповідних модулях.

class FakeUserService: # Заглушка
    """Імітує сервіс для роботи з користувачами."""
    async def get_user_by_id(self, user_id: Any) -> Optional[Dict[str, Any]]:
        self.logger = logging.getLogger(self.__class__.__name__) # Логер для екземпляру
        self.logger.debug(f"FakeUserService: Запит користувача з ID: {user_id}")
        # Імітація пошуку користувача в БД
        # У реальній системі тут буде запит до БД через SQLAlchemy або інший ORM/DAL.
        # Повертатиметься екземпляр моделі користувача (наприклад, UserModel).
        # Для заглушки повертаємо словник.
        if user_id == "user_active_id":
            return {"id": user_id, "username": "active_user", "email": "active@example.com", "is_active": True, "role_code": "user", "is_superuser": False}
        if user_id == "user_inactive_id":
            return {"id": user_id, "username": "inactive_user", "email": "inactive@example.com", "is_active": False, "role_code": "user", "is_superuser": False}
        if user_id == "superuser_id":
            return {"id": user_id, "username": "super_user", "email": "superuser@example.com", "is_active": True, "role_code": "superuser", "is_superuser": True}
        if user_id == "group_admin_id":
            return {"id": user_id, "username": "group_admin", "email": "groupadmin@example.com", "is_active": True, "role_code": "group_admin", "is_superuser": False}
        self.logger.warning(f"FakeUserService: Користувача з ID '{user_id}' не знайдено.")
        return None

class FakeTokenService: # Заглушка
    """Імітує сервіс для роботи з JWT токенами."""
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__) # Логер для екземпляру

    async def decode_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        self.logger.debug(f"FakeTokenService: Декодування токена: {token[:15]}...")
        # Імітація декодування JWT токена.
        # Реальний сервіс використовував би jwt.decode() з секретним ключем та алгоритмом.
        # Повертав би Pydantic схему (наприклад, TokenPayload).
        if token == "valid_active_user_token":
            # "sub" - стандартне поле для ідентифікатора користувача в JWT.
            return {"sub": "user_active_id", "username": "active_user", "role": "user", "scopes": ["read_own_profile", "write_comments"], "exp": 9999999999} # 'exp' для імітації валідного
        if token == "valid_inactive_user_token":
            return {"sub": "user_inactive_id", "username": "inactive_user", "role": "user", "scopes": [], "exp": 9999999999}
        if token == "valid_superuser_token":
            return {"sub": "superuser_id", "username": "super_user", "role": "superuser", "scopes": ["system:admin", "users:manage"], "exp": 9999999999}
        if token == "valid_group_admin_token":
            return {"sub": "group_admin_id", "username": "group_admin", "role": "group_admin", "scopes": ["group:manage_members", "group:read_content"], "exp": 9999999999}
        if token == "expired_token":
            self.logger.warning("FakeTokenService: Спроба використати прострочений токен (імітація).")
            # Реальний TokenService перевіряв би поле 'exp' і викликав би помилку.
            # Тут імітуємо помилку, яку міг би викликати JWT-парсер або TokenService.
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Токен прострочено (заглушка)", headers={"WWW-Authenticate": "Bearer"})

        self.logger.warning(f"FakeTokenService: Не вдалося розкодувати або невідомий токен: {token[:15]}...")
        return None

# Створюємо екземпляри сервісів-заглушок для використання в залежностях
# У реальному проекті ці сервіси будуть ін'єктуватися через Depends(), якщо вони самі є залежностями,
# або будуть доступні через інший механізм DI.
_fake_user_service = FakeUserService()
_fake_token_service = FakeTokenService()


async def get_current_user_payload(
    token: str = Depends(OAUTH2_SCHEME)
    # У реальному проекті: token_service: TokenService = Depends(get_token_service)
) -> Dict[str, Any]: # Повертає Pydantic схему (наприклад, TokenPayload)
    """
    Отримує та валідує JWT токен з Authorization header, повертає його payload.
    Це базова залежність, яка перевіряє лише наявність, формат та валідність підпису/часу життя токена.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не вдалося валідувати облікові дані (токен невалідний або відсутній 'sub')",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # payload = await token_service.decode_access_token(token=token) # Реальний виклик
        payload = await _fake_token_service.decode_access_token(token=token) # Виклик заглушки

        if payload is None or payload.get("sub") is None: # Перевірка, чи токен розкодовано і чи є 'sub'
            logger.warning(f"Не вдалося розкодувати токен або відсутній 'sub' (user_id). Токен: {token[:15]}...")
            raise credentials_exception

        # Тут також можна було б перевіряти 'exp' (expiration time), якщо це не робиться всередині decode_access_token.
        # Наприклад:
        # if datetime.utcnow() > datetime.fromtimestamp(payload.get("exp", 0)):
        #     raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Токен прострочено", headers={"WWW-Authenticate": "Bearer"})

    except HTTPException as http_exc: # Якщо токен прострочено (виняток з decode_access_token)
        logger.warning(f"HTTPException під час отримання payload: {http_exc.detail}")
        raise http_exc # Перепрокидаємо виняток далі
    except Exception as e: # Будь-які інші помилки при декодуванні
        logger.error(f"Неочікувана помилка декодування токена: {e}. Токен: {token[:10]}...", exc_info=True)
        raise credentials_exception # Замінюємо на загальну помилку автентифікації

    logger.debug(f"Payload токена успішно отримано для sub: {payload.get('sub')}")
    return payload


async def get_current_user(
    payload: Dict[str, Any] = Depends(get_current_user_payload)
    # У реальному проекті: user_service: UserService = Depends(get_user_service),
    #                      session: AsyncSession = Depends(get_api_db_session)
) -> Dict[str, Any]: # У реальному проекті повертатиме UserModel або Pydantic схему користувача
    """
    Отримує поточного користувача з бази даних на основі user_id ('sub') з payload токена.
    Не перевіряє, чи користувач активний на цьому етапі.
    """
    user_id = payload.get("sub") # 'sub' - це стандартне поле для ID користувача в JWT
    # user = await user_service.get_user_by_id(db_session=session, user_id=user_id) # Реальний виклик
    user = await _fake_user_service.get_user_by_id(user_id=user_id) # Виклик заглушки

    if user is None:
        logger.warning(f"Користувача з id '{user_id}' (з токена) не знайдено в БД.")
        # Статус 401, оскільки токен валідний, але користувач, якому він належав, більше не існує.
        # Це відрізняється від ситуації, коли токен сам по собі невалідний.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Користувача, пов'язаного з токеном, не знайдено.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    logger.debug(f"Користувача '{user.get('username')}' (id: {user_id}) отримано з БД.")
    return user


async def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]: # Повертає UserModel або Pydantic схему
    """
    Отримує поточного автентифікованого та активного користувача.
    Якщо користувач неактивний, викликає помилку HTTP 403 Forbidden.
    """
    if not current_user.get("is_active"):
        logger.warning(f"Спроба доступу неактивним користувачем '{current_user.get('username')}' (id: {current_user.get('id')}).")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Обліковий запис користувача неактивний.")
    logger.debug(f"Користувач '{current_user.get('username')}' активний.")
    return current_user


async def get_current_active_superuser(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> Dict[str, Any]: # Повертає UserModel або Pydantic схему
    """
    Перевіряє, чи поточний активний користувач є суперюзером.
    Якщо ні, викликає помилку HTTP 403 Forbidden.
    """
    # У реальній системі перевірка ролі може бути складнішою (наприклад, через поле role_code або зв'язок з моделлю ролей)
    # Або перевірка наявності певних прав/скоупів у користувача.
    is_superuser_flag = current_user.get("is_superuser", False)
    is_superuser_role = current_user.get("role_code") == "superuser"

    if not (is_superuser_flag or is_superuser_role):
        logger.warning(
            f"Користувач '{current_user.get('username')}' (id: {current_user.get('id')}) "
            f"не є суперюзером (is_superuser: {is_superuser_flag}, роль: {current_user.get('role_code')}). "
            f"Доступ заборонено."
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостатньо прав: потрібні права суперкористувача."
        )
    logger.debug(f"Користувач '{current_user.get('username')}' успішно авторизований як суперюзер.")
    return current_user


async def get_current_active_group_admin(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
    # У реальній системі може знадобитися group_id, наприклад, з Path:
    # from fastapi import Path
    # group_id: str = Path(...)
    # Або з Query, або з тіла запиту, залежно від ендпоінта.
) -> Dict[str, Any]: # Повертає UserModel або Pydantic схему
    """
    Перевіряє, чи поточний активний користувач є адміністратором групи.
    Ця залежність є заглушкою і перевіряє лише загальну роль 'group_admin'.
    У реальній системі вона повинна перевіряти членство та роль користувача
    в контексті конкретної групи, ID якої передається в ендпоінт.
    """
    # У реальній системі:
    # 1. Отримати group_id (з Path, Query, Body ендпоінта).
    # 2. Використати сервіс груп, щоб перевірити, чи є `current_user.id` адміністратором `group_id`.
    #    is_admin_of_specific_group = await group_service.is_user_group_admin(
    #        user_id=current_user.get("id"),
    #        group_id=group_id_from_path_or_query
    #    )
    #    if not is_admin_of_specific_group:
    #        # Також суперюзер може мати доступ
    #        if not current_user.get("is_superuser"):
    #            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Не є адміном цієї групи.")

    # Поточна заглушка перевіряє тільки загальну роль користувача
    user_role = current_user.get("role_code")
    if user_role not in ["group_admin", "superuser"]: # Суперюзер зазвичай має права адміна групи
        logger.warning(
            f"Користувач '{current_user.get('username')}' (id: {current_user.get('id')}) "
            f"не має ролі адміністратора групи або суперюзера (роль: {user_role}). Доступ заборонено."
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостатньо прав: потрібні права адміністратора групи."
        )
    logger.debug(f"Користувач '{current_user.get('username')}' авторизований з правами, достатніми для адміністрування груп (роль: {user_role}).")
    return current_user


# --- Інші можливі залежності ---
# - Перевірка API ключів для доступу до певних ендпоінтів (APIKeyHeader, APIKeyQuery)
# - Залежності для пагінації (отримання параметрів limit, offset)
# - Залежності для сортування та фільтрації

# Приклад залежності для пагінації:
# async def get_pagination_params(
#     skip: int = Query(0, ge=0, description="Кількість елементів, які потрібно пропустити (для пагінації)"),
#     limit: int = Query(100, ge=1, le=1000, description="Максимальна кількість елементів для повернення (для пагінації)")
# ) -> Dict[str, int]:
#     # Додаткова валідація тут не потрібна, якщо ge/le використовуються в Query,
#     # але можна додати логіку за замовчуванням або більш складні перевірки.
#     return {"skip": skip, "limit": limit}

logger.info("Модуль залежностей 'api.dependencies' завантажено з заглушками.")
