# backend/app/src/api/middleware.py
# -*- coding: utf-8 -*-
"""
Модуль для визначення проміжних обробників (middleware), специфічних для API.

Middleware в FastAPI дозволяє обробляти кожен запит до того, як він досягне
конкретного ендпоінта, та кожну відповідь перед тим, як її буде повернуто клієнту.
Це місце для логіки, яка має застосовуватися глобально до API або його частини.
"""

import time
# import logging # Замінено на централізований логер
from typing import Callable, Awaitable

from fastapi import Request, Response, HTTPException, status
from starlette.types import ASGIApp  # Для типізації app при реєстрації middleware

# Повні шляхи імпорту
from backend.app.src.config.logging import logger  # Централізований логер
from backend.app.src.config import settings  # Для доступу до налаштувань, наприклад, DEBUG або VALID_API_KEYS


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
        response: Response = await call_next(request)  # Передача запиту наступному обробнику
    except Exception as e:
        # Важливо обробляти винятки, щоб middleware не "зламав" відповідь про помилку
        process_time_on_error = time.perf_counter() - start_time
        logger.error(
            f"Помилка під час обробки запиту {request.method} {request.url.path} "
            f"(час до помилки: {process_time_on_error:.4f} сек): {e}",
            exc_info=True  # Додаємо traceback для діагностики
        )
        # Перепрокидаємо виняток, щоб FastAPI міг його обробити стандартним чином
        # (наприклад, через зареєстровані обробники винятків)
        raise

    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f} сек"

    # Логування може бути більш детальним, включаючи статус відповіді
    # Використовуємо global_settings.DEBUG для визначення рівня деталізації логування
    log_level = logging.DEBUG if hasattr(global_settings, "DEBUG") and global_settings.DEBUG else logging.INFO
    logger.log(
        log_level,
        f"Запит {request.method} {request.url.path} - Статус {response.status_code} - "
        f"Оброблено за {process_time:.4f} сек."
    )

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
#         logger.warning(f"API Key Middleware: Відсутній заголовок '{api_key_header_name}' для {request.url.path} від {request.client.host if request.client else 'N/A'}")
#         # i18n
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail=f"Обов'язковий заголовок '{api_key_header_name}' не надано."
#         )

#     if received_api_key not in valid_api_keys:
#         logger.warning(f"API Key Middleware: Невалідний API ключ надано для {request.url.path}. Ключ: '{received_api_key[:10]}...'")
#         # i18n
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Надано невалідний API ключ."
#         )

#     client_name = valid_api_keys[received_api_key]
#     # request.state.api_client_name = client_name # Зберігаємо ім'я клієнта в стані запиту
#     logger.info(f"API Key Middleware: Доступ надано для клієнта '{client_name}' до {request.url.path}")

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

logger.info("Модуль 'api.middleware' завантажено. Визначено: add_process_time_header_middleware.")
