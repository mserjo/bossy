# backend/app/src/api/dependencies.py
# -*- coding: utf-8 -*-
from backend.app.src.core.i18n import _
"""
Модуль для визначення загальних залежностей (dependencies) для API ендпоінтів FastAPI.

Сумісність: Python 3.13, SQLAlchemy v2, Pydantic v2.
"""

from typing import AsyncGenerator, Optional, Any, Dict  # AsyncGenerator для сесії БД

from fastapi import Depends, HTTPException, status, Path, Query
from fastapi.security import OAuth2PasswordBearer
from backend.app.src.config.settings import settings
from backend.app.src.config.database import get_db_session  # Припускаємо, що ця функція існує
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
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)


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
        detail=_("dependencies.auth.credentials_check_failed"), # "Не вдалося валідувати облікові дані"
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload_dict = await token_service.validate_access_token(token=token)
    if not payload_dict or payload_dict.get("sub") is None:
        logger.warning(_("dependencies.log.invalid_token_or_sub_missing", token_start=token[:15]))
        raise credentials_exception # Використовуємо вже створений виняток

    try:
        token_payload = TokenPayload(**payload_dict)
    except Exception as e:  # Наприклад, pydantic.ValidationError
        logger.warning(_("dependencies.log.token_payload_validation_error", error=str(e), payload_dict=str(payload_dict)))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_("dependencies.auth.malformed_token_payload"), # "Некоректний формат токена."
            headers={"WWW-Authenticate": "Bearer"} # Додаємо заголовок і сюди
        )

    logger.debug(_("dependencies.log.token_payload_success", sub=token_payload.sub))
    return token_payload


async def get_current_user(
        payload: TokenPayload = Depends(get_current_user_payload),
        user_service: UserService = Depends(get_user_service)
) -> User:  # Повертає модель SQLAlchemy User
    """
    Отримує поточного користувача з бази даних на основі user_id ('sub') з payload токена.
    """
    if not payload.sub:
        logger.warning(_("dependencies.log.sub_missing_in_token_payload"))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_("dependencies.auth.malformed_token_payload"), # "Некоректний формат токена."
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        user_id_from_token = int(payload.sub)
    except (ValueError, TypeError):
        logger.warning(_("dependencies.log.sub_conversion_to_int_failed", sub_value=payload.sub))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_("dependencies.auth.invalid_user_id_in_token"),
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await user_service._get_user_model_by_id(user_id=user_id_from_token)
    if user is None:
        logger.warning(_("dependencies.log.user_from_token_not_found_in_db", user_id=user_id_from_token))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_("dependencies.auth.user_associated_with_token_not_found"),
            headers={"WWW-Authenticate": "Bearer"},
        )
    logger.debug(_("dependencies.log.user_retrieved_from_db", username=user.username, user_id=user.id))
    return user


async def get_current_active_user(
        current_user: User = Depends(get_current_user)
) -> User:
    """
    Отримує поточного автентифікованого та активного користувача.
    Якщо користувач неактивний, викликає помилку HTTP 403 Forbidden.
    """
    if not current_user.is_active:
        logger.warning(_("dependencies.log.inactive_user_access_attempt", username=current_user.username, user_id=current_user.id))
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=_("dependencies.auth.inactive_user_account"))
    logger.debug(_("dependencies.log.user_is_active", username=current_user.username))
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
            _("dependencies.log.superuser_action_attempt_by_non_superuser_detail", username=current_user.username, user_id=current_user.id)
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=_("dependencies.auth.not_superuser_detail")
        )
    logger.debug(_("dependencies.log.superuser_auth_success", username=current_user.username))
    return current_user


async def get_current_active_group_admin(
        group_id: int = Path(..., description=_("dependencies.descriptions.group_id_for_admin_check_path")),
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
        _("dependencies.log.group_admin_check_start", username=current_user.username, user_id=current_user.id, group_id=group_id)
    )
    if current_user.is_superuser:
        logger.debug(_("dependencies.log.group_admin_superuser_override_log", username=current_user.username))
        return current_user

    membership = await membership_service.get_membership_details(group_id=group_id, user_id=current_user.id)

    if not membership or not membership.is_active or not membership.role:
        logger.warning(
             _("dependencies.log.group_admin_not_active_member_or_no_role", username=current_user.username, group_id=group_id)
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=_("dependencies.auth.not_active_member_or_no_role_in_group"))

    if membership.role.code != ADMIN_ROLE_CODE:
        logger.warning(
            _("dependencies.log.group_admin_not_admin_role", username=current_user.username, user_id=current_user.id, group_id=group_id, role_code=membership.role.code)
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=_("dependencies.auth.not_group_admin_insufficient_rights")
        )

    logger.debug(_("dependencies.log.group_admin_auth_success", username=current_user.username, group_id=group_id))
    return current_user


# --- Залежність для пагінації ---
async def get_pagination_params(
        skip: int = Query(0, ge=0, description=_("dependencies.descriptions.pagination_skip_desc")),
        limit: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE,
                           description=_("dependencies.descriptions.pagination_limit_desc"))
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
        logger.info(_("dependencies.log.cache_service_new_instance"))
        if settings.USE_REDIS and settings.REDIS_HOST and settings.REDIS_PORT:
            try:
                _cache_service_instance = RedisCacheService()
                logger.info(_("dependencies.log.cache_service_redis_used"))
            except Exception as e:
                logger.error(_("dependencies.log.cache_service_redis_init_error", error=str(e)))
                _cache_service_instance = InMemoryCacheService()
                logger.info(_("dependencies.log.cache_service_inmemory_fallback_after_redis_error"))
        else:
            if not settings.USE_REDIS:
                logger.info(_("dependencies.log.cache_service_redis_disabled"))
            else:
                logger.info(_("dependencies.log.cache_service_redis_misconfigured"))
            _cache_service_instance = InMemoryCacheService()

    if _cache_service_instance is None:
        logger.error(_("dependencies.log.cache_service_instance_creation_failed"))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=_("dependencies.errors.cache_service_unavailable"))

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


logger.info(_("dependencies.log.module_loaded_and_configured"))
