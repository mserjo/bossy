# backend/app/src/api/dependencies.py
# -*- coding: utf-8 -*-
"""
Модуль для визначення загальних залежностей (dependencies) для API ендпоінтів FastAPI.

Сумісність: Python 3.13, SQLAlchemy v2, Pydantic v2.
"""

# import logging # Замінено на централізований логер
from typing import AsyncGenerator, Optional, Any, Dict  # AsyncGenerator для сесії БД

from fastapi import Depends, HTTPException, status, Path, Query  # Додано Path, Query
from fastapi.security import OAuth2PasswordBearer

# Повні шляхи імпорту
from backend.app.src.config import logger  # Стандартизований імпорт логера
from backend.app.src.config.settings import settings
from backend.app.src.core.database import get_db_session  # Припускаємо, що ця функція існує
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.src.services import (  # Імпортуємо реальні сервіси
    UserService,
    TokenService,
    GroupMembershipService  # Для перевірки адміна групи
)
from backend.app.src.models.auth.user import User  # Модель SQLAlchemy для користувача
from backend.app.src.schemas.auth.token import TokenPayload  # Схема Pydantic для payload токена
from backend.app.src.models.dictionaries.user_roles import UserRole  # Для перевірки ролі в групі
from backend.app.src.core.constants import ADMIN_ROLE_CODE # Код ролі адміністратора

# Імпорти для кешу та сервісів довідників
from backend.app.src.services.cache.base_cache import BaseCacheService
from backend.app.src.services.cache.redis_service import RedisCacheService
from backend.app.src.services.cache.memory_service import InMemoryCacheService
from backend.app.src.services.dictionaries import (
    StatusService, UserRoleService, UserTypeService, GroupTypeService,
    TaskTypeService, BonusTypeService, CalendarProviderService, MessengerPlatformService
)

# ADMIN_ROLE_CODE = "ADMIN" # TODO: Перенесено до core.constants

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
        detail="Не вдалося валідувати облікові дані",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload_dict = await token_service.validate_access_token(token=token)
    if not payload_dict or payload_dict.get("sub") is None:
        logger.warning(f"Невалідний токен або відсутній 'sub'. Токен: {token[:15]}...")
        # i18n
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Невалідний токен або відсутній 'sub'.")

    # TODO: Переконатися, що TokenPayload схема відповідає вмісту payload_dict
    #  і обробляє можливі помилки валідації Pydantic.
    try:
        token_payload = TokenPayload(**payload_dict)
    except Exception as e:  # Наприклад, pydantic.ValidationError
        logger.warning(f"Помилка валідації TokenPayload: {e}. Payload: {payload_dict}")
        # i18n
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Некоректний формат токена.")

    logger.debug(f"Payload токена успішно отримано для sub: {token_payload.sub}")
    return token_payload


async def get_current_user(
        payload: TokenPayload = Depends(get_current_user_payload),
        user_service: UserService = Depends(get_user_service)
) -> User:  # Повертає модель SQLAlchemy User
    """
    Отримує поточного користувача з бази даних на основі user_id ('sub') з payload токена.
    """
    if not payload.sub:
        logger.warning("Відсутній 'sub' (user_id) в payload токена.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Некоректний формат токена.")

    try:
        user_id_from_token = int(payload.sub)
    except (ValueError, TypeError):
        logger.warning(f"Не вдалося конвертувати 'sub' з токена ('{payload.sub}') в int.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Некоректний формат ідентифікатора користувача в токені.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Використання захищеного методу, який повертає ORM модель, або get_user_by_id, якщо він повертає модель
    user = await user_service._get_user_model_by_id(user_id=user_id_from_token)
    if user is None:
        logger.warning(f"Користувача з id '{user_id_from_token}' (з токена) не знайдено в БД.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Користувача, пов'язаного з токеном, не знайдено.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    logger.debug(f"Користувача '{user.username}' (id: {user.id}) отримано з БД.")
    return user


async def get_current_active_user(
        current_user: User = Depends(get_current_user)
) -> User:
    """
    Отримує поточного автентифікованого та активного користувача.
    Якщо користувач неактивний, викликає помилку HTTP 403 Forbidden.
    """
    if not current_user.is_active:
        logger.warning(f"Спроба доступу неактивним користувачем '{current_user.username}' (id: {current_user.id}).")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Обліковий запис користувача неактивний.")
    logger.debug(f"Користувач '{current_user.username}' активний.")
    return current_user


async def get_current_active_superuser(
        current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Перевіряє, чи поточний активний користувач є суперюзером.
    Якщо ні, викликає помилку HTTP 403 Forbidden.
    """
    if not current_user.is_superuser:
        logger.warning(
            f"Користувач '{current_user.username}' (id: {current_user.id}) не є суперюзером. Доступ заборонено."
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостатньо прав: потрібні права суперкористувача."
        )
    logger.debug(f"Користувач '{current_user.username}' успішно авторизований як суперюзер.")
    return current_user


async def get_current_active_group_admin(
        group_id: int = Path(..., description="ID групи для перевірки прав адміністратора"),  # i18n, group_id змінено на int
        current_user: User = Depends(get_current_active_user),
        membership_service: GroupMembershipService = Depends(get_group_membership_service)
) -> User:
    """
    Перевіряє, чи поточний активний користувач є адміністратором вказаної групи.
    Суперкористувачі також проходять цю перевірку.

    :param group_id: ID групи (int), отриманий з шляху URL.
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
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Ви не є активним членом цієї групи або не маєте призначеної ролі.")

    if membership.role.code != ADMIN_ROLE_CODE:  # Використовуємо імпортовану константу
        logger.warning(
            f"Користувач '{current_user.username}' (ID: {current_user.id}) не є адміністратором групи ID '{group_id}' (роль: {membership.role.code}). Доступ заборонено."
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостатньо прав: потрібні права адміністратора цієї групи."
        )

    logger.debug(f"Користувач '{current_user.username}' авторизований як адміністратор групи ID '{group_id}'.")
    return current_user


# --- Залежність для пагінації ---
async def get_pagination_params(
        skip: int = Query(0, ge=0, description="Кількість елементів для пропуску (для пагінації)"),  # i18n
        limit: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, # Використання settings замість global_settings
                           description="Максимальна кількість елементів для повернення (для пагінації)")  # i18n
) -> Dict[str, int]:
    """
    Отримує параметри пагінації `skip` та `limit` з параметрів запиту.
    Використовує значення за замовчуванням та максимальні ліміти з конфігурації.
    """
    return {"skip": skip, "limit": limit}

# --- Залежність для сервісу кешування ---
# TODO: [DI/Singleton] Поточна реалізація singleton для _cache_service_instance є спрощеною
# і не буде працювати як справжній singleton з кількома worker'ами (наприклад, Gunicorn/Uvicorn).
# Розглянути використання механізмів FastAPI для управління життєвим циклом залежностей
# (наприклад, ініціалізація кешу під час події 'startup' додатку та збереження його в app.state,
# а потім залежність отримує його з app.state).
_cache_service_instance: Optional[BaseCacheService] = None

async def get_cache_service() -> BaseCacheService:
    """
    Залежність FastAPI для надання екземпляра сервісу кешування.
    Використовує Redis, якщо налаштовано, інакше InMemory.
    Поточна реалізація використовує спрощений singleton, який може не працювати
    коректно з кількома worker'ами. Для production слід використовувати
    механізми FastAPI для управління життєвим циклом (наприклад, app.state).

    Примітка: Поточна реалізація RedisCacheService ініціалізує клієнта "ліниво".
    """
    global _cache_service_instance

    if _cache_service_instance is None:
        # TODO: Розглянути можливість вибору реалізації кешу (Redis/InMemory) через налаштування settings.CACHE_TYPE
        # Поки що використовуємо RedisCacheService, якщо доступний, інакше InMemoryCacheService.
        logger.info("Створення нового екземпляра CacheService.")
        if settings.REDIS_HOST and settings.REDIS_PORT: # Припускаємо, що ці налаштування є
            try:
                # Спроба ініціалізувати RedisCacheService
                # RedisCacheService сам обробляє підключення до пулу
                _cache_service_instance = RedisCacheService()
                # Можна додати перевірку з'єднання тут, якщо потрібно
                # await _cache_service_instance._get_client() # Тест з'єднання
                logger.info("Використовується RedisCacheService.")
            except Exception as e:
                logger.error(f"Помилка ініціалізації RedisCacheService: {e}. Перехід на InMemoryCacheService.")
                _cache_service_instance = InMemoryCacheService()
                logger.info("Використовується InMemoryCacheService як запасний варіант.")
        else:
            _cache_service_instance = InMemoryCacheService()
            logger.info("Конфігурація Redis не знайдена. Використовується InMemoryCacheService.")

    if _cache_service_instance is None: # Якщо ініціалізація все ще не вдалася
        logger.error("Не вдалося створити жоден екземпляр CacheService!")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Сервіс кешування недоступний.")

    return _cache_service_instance

# --- Залежності для сервісів довідників ---
async def get_status_service(
    db_session: AsyncSession = Depends(get_api_db_session),
    cache_service: BaseCacheService = Depends(get_cache_service)
) -> StatusService:
    return StatusService(db_session=db_session, cache_service=cache_service)

async def get_user_role_service(
    db_session: AsyncSession = Depends(get_api_db_session),
    cache_service: BaseCacheService = Depends(get_cache_service)
) -> UserRoleService:
    return UserRoleService(db_session=db_session, cache_service=cache_service)

async def get_user_type_service(
    db_session: AsyncSession = Depends(get_api_db_session),
    cache_service: BaseCacheService = Depends(get_cache_service)
) -> UserTypeService:
    return UserTypeService(db_session=db_session, cache_service=cache_service)

async def get_group_type_service(
    db_session: AsyncSession = Depends(get_api_db_session),
    cache_service: BaseCacheService = Depends(get_cache_service)
) -> GroupTypeService:
    return GroupTypeService(db_session=db_session, cache_service=cache_service)

async def get_task_type_service(
    db_session: AsyncSession = Depends(get_api_db_session),
    cache_service: BaseCacheService = Depends(get_cache_service)
) -> TaskTypeService:
    return TaskTypeService(db_session=db_session, cache_service=cache_service)

async def get_bonus_type_service(
    db_session: AsyncSession = Depends(get_api_db_session),
    cache_service: BaseCacheService = Depends(get_cache_service)
) -> BonusTypeService:
    return BonusTypeService(db_session=db_session, cache_service=cache_service)

async def get_calendar_provider_service(
    db_session: AsyncSession = Depends(get_api_db_session),
    cache_service: BaseCacheService = Depends(get_cache_service)
) -> CalendarProviderService:
    return CalendarProviderService(db_session=db_session, cache_service=cache_service)

async def get_messenger_platform_service(
    db_session: AsyncSession = Depends(get_api_db_session),
    cache_service: BaseCacheService = Depends(get_cache_service)
) -> MessengerPlatformService:
    return MessengerPlatformService(db_session=db_session, cache_service=cache_service)


logger.info("Модуль залежностей 'api.dependencies' завантажено та налаштовано з реальними сервісами.")
