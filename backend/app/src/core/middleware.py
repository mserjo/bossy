# backend/app/src/core/middleware.py
# -*- coding: utf-8 -*-
"""
Цей модуль призначений для визначення кастомних FastAPI middleware.
Middleware - це функції, які обробляють кожен запит до того, як він досягне
обробника шляху (ендпоінта), та кожну відповідь перед тим, як вона буде
надіслана клієнту.

Приклади можливих middleware:
- Логування деталей кожного запиту та відповіді.
- Додавання кастомних HTTP заголовків до відповідей (наприклад, для безпеки).
- Обробка сесій (якщо використовуються серверні сесії).
- Вимірювання часу обробки запиту.
- Обробка помилок та форматування відповідей про помилки.
- Стиснення відповідей (GZip).
"""

from fastapi import Request, Response # Request та Response для роботи з запитами/відповідями
from fastapi.middleware.cors import CORSMiddleware # Вже є в FastAPI, але тут може бути кастомна логіка
# from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseCall # Для створення кастомних middleware
# from starlette.types import ASGIApp # Для типізації ASGI додатку
import time
from typing import Callable, Awaitable

# Імпорт логгера
from backend.app.src.config.logging import logger
# Імпорт налаштувань (наприклад, для CORS або заголовків безпеки)
from backend.app.src.config.settings import settings

# --- Приклад Middleware для вимірювання часу обробки запиту ---
# async def add_process_time_header_middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
#     """
#     Middleware, що додає заголовок X-Process-Time до кожної відповіді,
#     який вказує час обробки запиту на сервері.
#     """
#     start_time = time.time()
#     response = await call_next(request)
#     process_time = time.time() - start_time
#     response.headers["X-Process-Time"] = str(process_time)
#     logger.info(f"Запит {request.method} {request.url.path} оброблено за {process_time:.4f} сек.")
#     return response

# --- Приклад Middleware для логування запитів/відповідей (більш детальний) ---
# async def request_response_logging_middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
#     """
#     Middleware для детального логування інформації про HTTP запити та відповіді.
#     """
#     # Логування інформації про запит
#     log_details = {
#         "method": request.method,
#         "url": str(request.url),
#         "headers": dict(request.headers),
#         "client_host": request.client.host if request.client else "unknown",
#         "client_port": request.client.port if request.client else "unknown",
#     }
#     # Тіло запиту може бути прочитане лише один раз.
#     # Якщо потрібно логувати тіло, його треба буде "клонувати" або обережно обробляти.
#     # body = await request.body() # Це "споживає" тіло
#     # logger.debug(f"Вхідний запит: {log_details}, тіло (приклад перших 100 байт): {body[:100]}")
#     logger.info(f"Вхідний запит: {log_details}")
#
#     response = await call_next(request)
#
#     # Логування інформації про відповідь
#     log_response_details = {
#         "status_code": response.status_code,
#         "headers": dict(response.headers),
#     }
#     # Тіло відповіді також може бути прочитане лише один раз або потребувати спеціальної обробки.
#     # response_body = b""
#     # async for chunk in response.body_iterator: # type: ignore
#     #     response_body += chunk
#     # logger.debug(f"Відповідь: {log_response_details}, тіло (приклад перших 100 байт): {response_body[:100]}")
#     # # Повертаємо нову відповідь з прочитаним тілом (це може бути небезпечно або неефективно)
#     # response = Response(content=response_body, status_code=response.status_code, headers=dict(response.headers), media_type=response.media_type)
#     logger.info(f"Відповідь для {request.method} {request.url.path}: {log_response_details}")
#
#     return response


# --- Приклад Middleware для додавання стандартних заголовків безпеки ---
# async def add_security_headers_middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
#     """
#     Middleware для додавання стандартних HTTP заголовків безпеки до відповідей.
#     """
#     response = await call_next(request)
#     response.headers["X-Content-Type-Options"] = "nosniff"
#     response.headers["X-Frame-Options"] = "DENY"
#     # response.headers["Content-Security-Policy"] = "default-src 'self'; img-src * data:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline';" # Дуже базовий CSP
#     response.headers["X-XSS-Protection"] = "1; mode=block" # Застарілий, краще CSP
#
#     # HSTS (HTTP Strict Transport Security) - лише якщо сайт завжди на HTTPS
#     # if request.url.scheme == "https": # Або якщо завжди HTTPS
#     #     response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
#
#     # Referrer-Policy
#     response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
#
#     # Permissions-Policy (Feature-Policy)
#     # response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=()" # Приклад: вимкнути все
#
#     return response

# --- Реєстрація Middleware в FastAPI додатку (в `main.py`) ---
# Middleware додаються до екземпляра FastAPI `app`.
# Порядок додавання Middleware важливий, оскільки вони обробляються
# в порядку їх додавання для запитів, і в зворотному порядку для відповідей.
#
# from fastapi import FastAPI
#
# app = FastAPI()
#
# # Додавання CORS Middleware (зазвичай одним з перших)
# if settings.app.BACKEND_CORS_ORIGINS:
#     app.add_middleware(
#         CORSMiddleware,
#         allow_origins=[str(origin) for origin in settings.app.BACKEND_CORS_ORIGINS],
#         allow_credentials=True,
#         allow_methods=["*"],
#         allow_headers=["*"],
#     )
#
# # Додавання кастомних middleware
# # app.middleware("http")(add_process_time_header_middleware) # Старий спосіб для функцій
# # app.add_middleware(BaseHTTPMiddleware, dispatch=add_process_time_header_middleware_class_based) # Якщо це клас
#
# # Для функціональних middleware, як визначено вище (з Request, call_next):
# # Їх можна додати через @app.middleware("http") або app.add_middleware(StarletteMiddleware, handler=...)
# # Або, якщо вони сумісні з BaseHTTPMiddleware, то через нього.
# #
# # Приклад додавання функціонального middleware (потребує адаптації або використання BaseHTTPMiddleware)
# # async def dispatch_process_time(request: Request, call_next): ... (як вище)
# # app.add_middleware(BaseHTTPMiddleware, dispatch=dispatch_process_time)
# #
# # Простіший спосіб для функцій-middleware в FastAPI - це використання @app.middleware("http")
# # @app.middleware("http")
# # async def process_time_mw(request: Request, call_next): ...
# #
# # Цей код має бути в `main.py`.

# TODO: Визначити, які саме кастомні middleware потрібні для проекту.
# - Логування запитів/відповідей (може бути частково покрито Uvicorn логуванням).
# - Додавання заголовків безпеки.
# - Обробка глобальних винятків (хоча FastAPI має @app.exception_handler).
# - Можливо, middleware для автентифікації API ключів (якщо не через Depends).
#
# На даному етапі цей файл є заглушкою з прикладами.
# Фактична реалізація та реєстрація middleware буде залежати від потреб.
#
# Важливо: Middleware, що читають тіло запиту або відповіді, мають бути реалізовані
# обережно, оскільки тіло можна прочитати лише один раз.
# Starlette надає механізми для цього (наприклад, `request.stream()`, `response.body_iterator`).
#
# Все готово для базової структури файлу.
# Конкретні middleware будуть розроблятися за потреби.
#
# Все готово.
