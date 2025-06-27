# backend/app/src/api/middleware.py
# -*- coding: utf-8 -*-
"""
Модуль для специфічного middleware FastAPI, що застосовується до API.

Цей файл може містити кастомні класи middleware або функції, які
виконуються для кожного запиту до API або для певних його частин.
Приклади використання middleware:
- Логування деталей запитів та відповідей.
- Додавання специфічних заголовків до відповідей (наприклад, `X-Request-ID`).
- Обробка винятків на рівні API.
- Вимірювання часу обробки запиту.
- Реалізація кастомних механізмів автентифікації (наприклад, API ключі).

Middleware додається до екземпляру FastAPI або до конкретних роутерів.
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp
import time

# from backend.app.src.config.logging import get_logger

# logger = get_logger(__name__)

# TODO: Розкоментувати та адаптувати, коли буде налаштований логер.
# class LoggingMiddleware(BaseHTTPMiddleware):
#     """
#     Middleware для логування інформації про запити та відповіді.
#     """
#     async def dispatch(
#         self, request: Request, call_next: RequestResponseEndpoint
#     ) -> Response:
#         """
#         Обробляє запит, логує інформацію та передає запит далі.
#
#         Args:
#             request (Request): Об'єкт запиту FastAPI.
#             call_next (RequestResponseEndpoint): Наступний обробник у ланцюжку middleware/ендпоінт.
#
#         Returns:
#             Response: Об'єкт відповіді FastAPI.
#         """
#         start_time = time.time()
#         logger.info(f"Вхідний запит: {request.method} {request.url.path}")
#         try:
#             response = await call_next(request)
#             process_time = time.time() - start_time
#             logger.info(
#                 f"Вихідна відповідь: {response.status_code} "
#                 f"для {request.method} {request.url.path} (час обробки: {process_time:.4f}s)"
#             )
#         except Exception as e:
#             process_time = time.time() - start_time
#             logger.error(
#                 f"Помилка під час обробки запиту: {request.method} {request.url.path} "
#                 f"(час обробки: {process_time:.4f}s) - {e}",
#                 exc_info=True
#             )
#             # Важливо повторно викликати виняток, щоб FastAPI міг його обробити
#             raise
#         return response


# TODO: Приклад middleware для додавання кастомного заголовку.
# class CustomHeaderMiddleware(BaseHTTPMiddleware):
#     """
#     Middleware для додавання кастомного заголовку до кожної відповіді.
#     """
#     def __init__(self, app: ASGIApp, header_value: str = "CustomValue"):
#         super().__init__(app)
#         self.header_value = header_value
#
#     async def dispatch(
#         self, request: Request, call_next: RequestResponseEndpoint
#     ) -> Response:
#         response = await call_next(request)
#         response.headers["X-Custom-Header"] = self.header_value
#         return response

# TODO: Додати інші специфічні для API middleware, якщо потрібно.
# Наприклад, middleware для перевірки API ключів, якщо це основний
# спосіб автентифікації для певних частин API.

# Приклад того, як ці middleware можуть бути додані в main.py:
# from backend.app.src.api.middleware import LoggingMiddleware, CustomHeaderMiddleware
# app.add_middleware(LoggingMiddleware)
# app.add_middleware(CustomHeaderMiddleware, header_value="MySpecificAPIValue")
