# backend/app/src/core/__init__.py
# -*- coding: utf-8 -*-
"""
Ініціалізаційний файл для пакету ядра (`core`).

Цей файл робить доступними основні компоненти ядра для імпорту з пакету
`backend.app.src.core`. Це можуть бути базові класи, утиліти, константи,
кастомні винятки, залежності FastAPI тощо.

Приклад імпорту:
from backend.app.src.core import BaseRepository, AppException, get_current_user

Також цей файл може використовуватися для визначення змінної `__all__`,
яка контролює, що саме експортується при використанні `from . import *`.
"""

# Імпорт основних компонентів з модулів ядра
from backend.app.src.core.base import (
    BaseRepository,
    BaseService,
    # Типізація (ModelType, CreateSchemaType, UpdateSchemaType, SchemaType) -
    # зазвичай не експортується напряму, а використовується всередині.
)
from backend.app.src.core.constants import * # Експортуємо всі константи
from backend.app.src.core.exceptions import (
    AppException,
    NotFoundException,
    BadRequestException,
    UnauthorizedException,
    ForbiddenException,
    UnprocessableEntityException,
    ConflictException,
    InternalServerErrorException,
    DatabaseErrorException,
    BusinessLogicException,
    AuthenticationFailedException,
    InsufficientPermissionsException,
    ResourceAlreadyExistsException,
    ResourceNotFoundException,
)
from backend.app.src.core.dependencies import (
    get_current_user,
    # get_current_active_user, # Видалено, функціонал в get_current_user
    get_current_superuser,
    get_optional_current_user,
    oauth2_scheme, # OAuth2PasswordBearer схема для FastAPI
    # get_api_key, # Якщо використовується
    # Інші залежності, наприклад, для перевірки ролей в групах
)
from backend.app.src.core.utils import (
    get_current_utc_timestamp,
    datetime_to_iso_string,
    iso_string_to_datetime,
    calculate_expiration_date,
    calculate_expiration_date_days,
    generate_random_string,
    generate_unique_code,
    generate_uuid,
    simple_sha256_hash,
    slugify_string,
    deep_update_dict,
)
from backend.app.src.core.dicts import ( # Enum-довідники
    NotificationChannelEnum,
    TransactionTypeEnum,
    BadgeConditionTypeEnum,
    RatingTypeEnum,
    ReportCodeEnum,
    # UserTypeEnum, # Якщо буде використовуватися
)
from backend.app.src.core.decorators import ( # Приклади декораторів
    log_function_call,
    timing_decorator,
    # manage_transaction, # Концептуальний, потребує доопрацювання
)
# from backend.app.src.core.events import ( # Система подій (якщо використовується)
#     BaseEvent,
#     BaseEventHandler,
#     EventDispatcher,
#     # event_dispatcher, # Глобальний екземпляр (якщо створюється тут)
# )
# from backend.app.src.core.middleware import ( # Приклади middleware (реєструються в main.py)
#     # add_process_time_header_middleware,
#     # request_response_logging_middleware,
#     # add_security_headers_middleware,
# )
# from backend.app.src.core.permissions import ( # Логіка дозволів (функції або класи)
#     # require_group_admin,
#     # require_group_member,
#     # require_roles,
# )
from backend.app.src.core.validators import ( # Кастомні валідатори
    is_valid_username_format,
    is_strong_password,
    # validate_phone_number,
)
from backend.app.src.core.i18n import ( # Інтернаціоналізація
    SUPPORTED_LOCALES,
    DEFAULT_LOCALE,
    get_locale,
    # _ as gettext, # Функція перекладу (якщо готова)
    # load_translations,
)


# Визначення змінної `__all__` для контролю публічного API пакету `core`.
_constants_all = [name for name in dir() if name.isupper() and not name.startswith('_')] # Експорт всіх констант з constants.py

__all__ = [
    # base.py
    "BaseRepository",
    "BaseService",

    # constants.py - всі константи експортуються через * вище,
    # але можна перерахувати явно, якщо потрібно.
    # Або додати _constants_all до цього списку.

    # exceptions.py
    "AppException", "NotFoundException", "BadRequestException", "UnauthorizedException",
    "ForbiddenException", "UnprocessableEntityException", "ConflictException",
    "InternalServerErrorException", "DatabaseErrorException", "BusinessLogicException",
    "AuthenticationFailedException", "InsufficientPermissionsException",
    "ResourceAlreadyExistsException", "ResourceNotFoundException",

    # dependencies.py
    "get_current_user", # "get_current_active_user", # Видалено
    "get_current_superuser",
    "get_optional_current_user", "oauth2_scheme",
    # "get_api_key",

    # utils.py
    "get_current_utc_timestamp", "datetime_to_iso_string", "iso_string_to_datetime",
    "calculate_expiration_date", "calculate_expiration_date_days",
    "generate_random_string", "generate_unique_code", "generate_uuid",
    "simple_sha256_hash", "slugify_string", "deep_update_dict",

    # dicts.py
    "NotificationChannelEnum", "TransactionTypeEnum", "BadgeConditionTypeEnum",
    "RatingTypeEnum", "ReportCodeEnum",
    # "UserTypeEnum",

    # decorators.py
    "log_function_call", "timing_decorator",
    # "manage_transaction",

    # events.py (якщо використовується)
    # "BaseEvent", "BaseEventHandler", "EventDispatcher", "event_dispatcher",

    # permissions.py (якщо є експортовані функції/класи)
    # "require_group_admin", "require_group_member", "require_roles",

    # validators.py
    "is_valid_username_format", "is_strong_password",
    # "validate_phone_number",

    # i18n.py
    "SUPPORTED_LOCALES", "DEFAULT_LOCALE", "get_locale",
    # "gettext", "load_translations",

] + _constants_all # Додаємо всі константи до __all__

# TODO: Переконатися, що всі необхідні компоненти ядра експортуються.
# На даний момент експортуються основні класи, функції та константи.
# Модулі `middleware.py` та `permissions.py` поки що містять переважно заглушки
# або приклади, тому їх активний експорт може бути обмеженим.
# `events.py` також залежить від рішення про використання event-driven підходу.
#
# Цей файл слугує єдиною точкою входу для доступу до компонентів ядра,
# що спрощує імпорти та структуру проекту.
#
# Все виглядає добре.
# Динамічне додавання констант до `__all__` через `_constants_all` є зручним.
#
# Все готово.
