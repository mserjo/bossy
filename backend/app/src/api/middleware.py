# backend/app/src/api/middleware.py
# -*- coding: utf-8 -*-
from backend.app.src.core.i18n import _
"""
Модуль для визначення проміжних обробників (middleware), специфічних для API.

Middleware в FastAPI дозволяє обробляти кожен запит до того, як він досягне
конкретного ендпоінта, та кожну відповідь перед тим, як її буде повернуто клієнту.
Це місце для логіки, яка має застосовуватися глобально до API або його частини.

Сумісність: Python 3.13, SQLAlchemy v2, Pydantic v2.
"""

import time
from typing import Callable, Awaitable
from fastapi import Request, Response
from backend.app.src.config import settings  # Для доступу до налаштувань, наприклад, DEBUG або VALID_API_KEYS
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

# --- Middleware для додавання часу обробки запиту ---

async def add_process_time_header_middleware(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """
    Простий middleware для вимірювання часу обробки запиту та додавання
    його до заголовків відповіді як 'X-Process-Time'.

    :param request: Вхідний запит.
    :param call_next: Наступний обробник у ланцюжку middleware/ендпоінт.
    :return: Відповідь, збагачена заголовком X-Process-Time.
    """
    start_time = time.perf_counter()

    try:
        response: Response = await call_next(request)
    except Exception as e:
        process_time_on_error = time.perf_counter() - start_time
        logger.error(
            _("api_middleware.log.error_processing_request",
              method=request.method,
              path=request.url.path,
              time_to_error=f"{process_time_on_error:.4f}",
              error=str(e)),
            exc_info=True
        )
        raise

    process_time = time.perf_counter() - start_time
    # Додаємо одиниці виміру до ключа, щоб уникнути плутанини при автоматичному парсингу заголовків
    response.headers["X-Process-Time-Seconds"] = f"{process_time:.4f}"

    log_message = _(
        "api_middleware.log.request_processed_summary",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        process_time=f"{process_time:.4f}"
    )
    if settings.DEBUG:
        logger.debug(log_message)
    else:
        logger.info(log_message)

    return response


# --- Заглушка для API Key Middleware ---
# Цей middleware міг би використовуватися для захисту певних ендпоінтів,
# призначених для взаємодії з зовнішніми системами, які автентифікуються за API ключем.

# TODO: Завантажувати VALID_API_KEYS та API_KEY_HEADER_NAME з backend.app.src.config.settings
# VALID_API_KEYS_EXAMPLE = {
#     "supersecretapikey12345forServiceA": "Service A",
#     "anothersecurekey67890forPartnerB": "External Partner B",
# }
# API_KEY_HEADER_NAME_EXAMPLE = "X-Api-Key" # Стандартний заголовок для API ключів

# async def verify_api_key_middleware(
#     request: Request,
#     call_next: Callable[[Request], Awaitable[Response]]
# ) -> Response:
#     """
#     Перевіряє API ключ для шляхів, що цього потребують.
#     Примітка: Фільтрація шляхів (наприклад, застосування тільки до /api/v1/external/*)
#     має бути реалізована або тут, або при підключенні middleware до конкретного роутера.
#     """
#     # Приклад фільтрації шляху:
#     # if not request.url.path.startswith(f"{global_settings.API_V1_STR}/external"):
#     #     return await call_next(request) # Пропускаємо для інших шляхів

#     valid_api_keys = getattr(global_settings, "VALID_API_KEYS", {})
#     api_key_header_name = getattr(global_settings, "API_KEY_HEADER_NAME", "X-Api-Key")

#     received_api_key = request.headers.get(api_key_header_name)

#     if not received_api_key:
#         logger.warning(_("api_middleware.log.api_key_header_missing", header_name=api_key_header_name, path=request.url.path, client_host=request.client.host if request.client else _("api_exceptions.not_applicable_short")))
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail=_("api_middleware.errors.api_key_header_required", header_name=api_key_header_name)
#         )

#     if received_api_key not in valid_api_keys:
#         logger.warning(_("api_middleware.log.api_key_invalid", path=request.url.path, key_preview=received_api_key[:10]))
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail=_("api_middleware.errors.api_key_invalid_provided")
#         )

#     client_name = valid_api_keys[received_api_key]
#     # request.state.api_client_name = client_name
#     logger.info(_("api_middleware.log.api_key_access_granted", client_name=client_name, path=request.url.path))

#     response = await call_next(request)
#     return response

# --- Реєстрація middleware ---
# Middleware реєструються в основному файлі додатку (наприклад, main.py)
# або для конкретних APIRouter.
#
# Приклад для main.py:
# from backend.app.src.api.middleware import add_process_time_header_middleware
# app.middleware("http")(add_process_time_header_middleware)
#
# Або для APIRouter:
# from fastapi import APIRouter
# from backend.app.src.api.middleware import verify_api_key_middleware
# external_router = APIRouter()
# external_router.middleware("http")(verify_api_key_middleware) # Застосувати тільки до цього роутера

logger.info(_("api_middleware.log.module_loaded_defined_middlewares", middlewares="add_process_time_header_middleware"))
