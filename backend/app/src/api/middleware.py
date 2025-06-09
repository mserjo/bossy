# backend/app/src/api/middleware.py
# -*- coding: utf-8 -*-
"""
Модуль для визначення проміжних обробників (middleware), специфічних для API.

Middleware в FastAPI дозволяє обробляти кожен запит до того, як він досягне
конкретного ендпоінта, та кожну відповідь перед тим, як її буде повернуто клієнту.
Це місце для логіки, яка має застосовуватися глобально до API або його частини.

Приклади:
- Логування запитів/відповідей.
- Додавання кастомних заголовків (наприклад, `X-Process-Time`).
- Обробка CORS (хоча FastAPI має вбудовану підтримку).
- Спеціалізована автентифікація (наприклад, за API ключем для певних шляхів).
"""

import time
import logging
from typing import Callable, Awaitable # Awaitable для типу повернення call_next

from fastapi import Request, Response, HTTPException, status
# from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseCall # Для старішого стилю middleware, якщо знадобиться
from starlette.types import ASGIApp # , Receive, Scope, Send # Для ASGI middleware, якщо писати його вручну

logger = logging.getLogger(__name__)

# --- Middleware для додавання часу обробки запиту ---

async def add_process_time_header_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """
    Простий middleware для вимірювання часу обробки запиту та додавання
    його до заголовків відповіді як 'X-Process-Time'.

    Args:
        request (Request): Вхідний запит.
        call_next (Callable): Наступний обробник у ланцюжку middleware/ендпоінт.

    Returns:
        Response: Відповідь, збагачена заголовком X-Process-Time.
    """
    start_time = time.perf_counter() # Використовуємо perf_counter для точнішого вимірювання

    try:
        response: Response = await call_next(request) # Передача запиту наступному обробнику
    except Exception as e:
        # Важливо обробляти винятки, щоб middleware не "зламав" відповідь про помилку
        process_time_on_error = time.perf_counter() - start_time
        logger.error(
            f"Помилка під час обробки запиту {request.method} {request.url.path} "
            f"(час до помилки: {process_time_on_error:.4f} сек): {e}",
            exc_info=True
        )
        # Перепрокидаємо виняток, щоб FastAPI міг його обробити стандартним чином
        raise

    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f} сек"
    # Логування може бути більш детальним, включаючи статус відповіді
    logger.info(
        f"Запит {request.method} {request.url.path} - Статус {response.status_code} - "
        f"Оброблено за {process_time:.4f} сек."
    )

    return response

# --- Заглушка для API Key Middleware ---
# Цей middleware міг би використовуватися для захисту певних ендпоінтів,
# призначених для взаємодії з зовнішніми системами, які автентифікуються за API ключем.

# Очікувані API ключі (мають бути в settings або захищеному сховищі, наприклад, HashiCorp Vault)
# VALID_API_KEYS_EXAMPLE = {
#     "supersecretapikey12345forServiceA": "Service A",
#     "anothersecurekey67890forPartnerB": "External Partner B",
# }
# API_KEY_HEADER_NAME_EXAMPLE = "X-Api-Key" # Стандартний заголовок для API ключів

# # Приклад реалізації API Key Middleware як асинхронної функції (сучасний стиль FastAPI)
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
#     # if not request.url.path.startswith("/api/v1/integrations/"): # Шляхи, що потребують API ключа
#     #     return await call_next(request) # Пропускаємо для інших шляхів
#
#     # Завантаження конфігурації (в реальному додатку - з settings)
#     # valid_api_keys = settings.VALID_API_KEYS
#     # api_key_header_name = settings.API_KEY_HEADER_NAME
#     valid_api_keys = VALID_API_KEYS_EXAMPLE
#     api_key_header_name = API_KEY_HEADER_NAME_EXAMPLE
#
#     received_api_key = request.headers.get(api_key_header_name)
#
#     if not received_api_key:
#         logger.warning(f"API Key Middleware: Відсутній заголовок '{api_key_header_name}' для {request.url.path} від {request.client.host}")
#         # Використовуємо HTTPException для автоматичної генерації відповіді FastAPI
#         # return Response(content=f"Заголовок '{api_key_header_name}' не надано", status_code=status.HTTP_401_UNAUTHORIZED, media_type="text/plain")
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail=f"Обов'язковий заголовок '{api_key_header_name}' не надано."
#         )
#
#     if received_api_key not in valid_api_keys:
#         logger.warning(f"API Key Middleware: Невалідний API ключ надано для {request.url.path}. Ключ: '{received_api_key[:10]}...'")
#         # return Response(content="Невалідний API ключ", status_code=status.HTTP_403_FORBIDDEN, media_type="text/plain")
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Надано невалідний API ключ."
#         )
#
#     # Якщо ключ валідний, можна додати інформацію про клієнта до стану запиту
#     # request.state.api_client_name = valid_api_keys[received_api_key]
#     logger.info(f"API Key Middleware: Доступ надано для клієнта '{valid_api_keys[received_api_key]}' до {request.url.path}")
#
#     response = await call_next(request)
#     return response


# --- Інші можливі middleware ---
# - Middleware для логування тіла запиту/відповіді (обережно з чутливими даними та GDPR).
# - Middleware для обробки кастомних заголовків сесії або трасування.
# - Middleware для інтеграції з системами моніторингу та алертингу (наприклад, Prometheus, Sentry).
#   (Sentry має власну інтеграцію з ASGI/FastAPI, яка зазвичай краща).
# - Middleware для обмеження частоти запитів (rate limiting).

# Підключення middleware до FastAPI додатку або роутера відбувається в main.py або api/router.py:
#
# Спосіб 1: Додавання до конкретного екземпляру FastAPI (глобально для всього додатку)
# --- main.py ---
# from fastapi import FastAPI
# from app.src.api.middleware import add_process_time_header_middleware # , verify_api_key_middleware
#
# app = FastAPI()
#
# # Додавання як ASGI middleware (рекомендований спосіб для FastAPI >= 0.70.0)
# # Middleware виконуються у порядку їх додавання (зверху вниз для запитів, знизу вверх для відповідей)
# app.middleware("http")(add_process_time_header_middleware)
# # app.middleware("http")(verify_api_key_middleware) # Якщо цей middleware має бути глобальним
#
# # Або для старішого стилю (BaseHTTPMiddleware):
# # from starlette.middleware.base import BaseHTTPMiddleware
# # class MyOldStyleMiddleware(BaseHTTPMiddleware): ...
# # app.add_middleware(MyOldStyleMiddleware)
#
# Спосіб 2: Додавання до APIRouter (тільки для ендпоінтів цього роутера)
# --- api/router.py ---
# from fastapi import APIRouter
# from app.src.api.middleware import add_process_time_header_middleware # , verify_api_key_middleware
#
# # Припустимо, є роутер для зовнішніх інтеграцій
# external_integrations_router = APIRouter()
# # external_integrations_router.middleware("http")(verify_api_key_middleware) # Застосувати тільки до цього роутера
#
# # Головний api_router може не мати цього middleware, якщо він не потрібен глобально
# # api_router = APIRouter()
# # api_router.include_router(external_integrations_router, prefix="/external", tags=["External"])
# # api_router.middleware("http")(add_process_time_header_middleware) # Застосувати до всіх шляхів під api_router

logger.info("Модуль 'api.middleware' завантажено. Визначено: add_process_time_header_middleware.")
