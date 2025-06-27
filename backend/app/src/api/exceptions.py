# backend/app/src/api/exceptions.py
# -*- coding: utf-8 -*-
"""
Модуль для визначення та реєстрації кастомних обробників винятків для API.

FastAPI дозволяє визначати глобальні обробники винятків, які перехоплюють
певні типи винятків (стандартні HTTP винятки або кастомні) та повертають
структуровані HTTP відповіді.

Цей файл може містити:
- Кастомні класи винятків, специфічні для API (якщо вони не визначені в `core.exceptions`).
- Функції-обробники для цих винятків.
- Функції для реєстрації цих обробників в екземплярі FastAPI або APIRouter.

Використання централізованих обробників винятків допомагає стандартизувати
формат помилок, які повертає API, та спрощує їх обробку на стороні клієнта.
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

# from backend.app.src.core.exceptions import (
#     AppException,
#     NotFoundException,
#     PermissionDeniedException,
#     ValidationException
# )
# from backend.app.src.config.logging import get_logger

# logger = get_logger(__name__)

# TODO: Розкоментувати та адаптувати, коли будуть реалізовані кастомні винятки та логер.

# async def http_exception_handler(request: Request, exc: HTTPException):
#     """
#     Обробник для стандартних HTTPException FastAPI.
#     Може бути використаний для кастомізації логування або формату відповіді.
#     """
#     logger.error(
#         f"HTTP Exception: {exc.status_code} {exc.detail} for {request.method} {request.url.path}",
#         exc_info=exc if exc.status_code >= 500 else None # Логуємо стек трейс для 5xx помилок
#     )
#     return JSONResponse(
#         status_code=exc.status_code,
#         content={"detail": exc.detail, "error_code": getattr(exc, "error_code", None)},
#         headers=getattr(exc, "headers", None),
#     )

# async def app_exception_handler(request: Request, exc: AppException):
#     """
#     Обробник для базового кастомного винятку AppException.
#     """
#     logger.warning(
#         f"Application Exception: {exc.status_code} {exc.detail} (Code: {exc.error_code}) "
#         f"for {request.method} {request.url.path}"
#     )
#     return JSONResponse(
#         status_code=exc.status_code,
#         content={"detail": exc.detail, "error_code": exc.error_code},
#     )

# async def not_found_exception_handler(request: Request, exc: NotFoundException):
#     """
#     Обробник для винятку NotFoundException.
#     """
#     logger.info(
#         f"Resource Not Found: {exc.detail} (Code: {exc.error_code}) "
#         f"for {request.method} {request.url.path}"
#     )
#     return JSONResponse(
#         status_code=exc.status_code, # Зазвичай 404
#         content={"detail": exc.detail, "error_code": exc.error_code},
#     )

# async def permission_denied_exception_handler(request: Request, exc: PermissionDeniedException):
#     """
#     Обробник для винятку PermissionDeniedException.
#     """
#     logger.warning(
#         f"Permission Denied: {exc.detail} (Code: {exc.error_code}) "
#         f"for {request.method} {request.url.path}"
#     )
#     return JSONResponse(
#         status_code=exc.status_code, # Зазвичай 403
#         content={"detail": exc.detail, "error_code": exc.error_code},
#     )

# async def validation_exception_handler(request: Request, exc: ValidationException):
#     """
#     Обробник для винятку ValidationException.
#     """
#     logger.info(
#         f"Validation Error: {exc.detail} (Code: {exc.error_code}, Errors: {exc.errors}) "
#         f"for {request.method} {request.url.path}"
#     )
#     return JSONResponse(
#         status_code=exc.status_code, # Зазвичай 400 або 422
#         content={"detail": exc.detail, "error_code": exc.error_code, "errors": exc.errors},
#     )


# def register_exception_handlers(app_or_router):
#     """
#     Реєструє кастомні обробники винятків для екземпляру FastAPI або APIRouter.
#
#     Args:
#         app_or_router: Екземпляр FastAPI додатка або APIRouter.
#     """
#     # Обробник для стандартних HTTPException (включаючи ті, що згенеровані FastAPI)
#     app_or_router.add_exception_handler(HTTPException, http_exception_handler)
#     # Обробник для Starlette HTTPException (щоб покрити ті, що не від FastAPI)
#     app_or_router.add_exception_handler(StarletteHTTPException, http_exception_handler)
#
#     # Реєстрація обробників для кастомних винятків
#     app_or_router.add_exception_handler(AppException, app_exception_handler)
#     app_or_router.add_exception_handler(NotFoundException, not_found_exception_handler)
#     app_or_router.add_exception_handler(PermissionDeniedException, permission_denied_exception_handler)
#     app_or_router.add_exception_handler(ValidationException, validation_exception_handler)
#
#     # TODO: Додати обробники для інших кастомних винятків, якщо вони є.
#
#     # Приклад реєстрації в main.py:
#     # from backend.app.src.api.exceptions import register_exception_handlers
#     # register_exception_handlers(app)
#
#     # Або для конкретного роутера (наприклад, api_router в backend/app/src/api/router.py):
#     # register_exception_handlers(api_router)


# Приклад простого кастомного винятку, якщо він потрібен саме на рівні API
class APISpecificException(HTTPException):
    """
    Приклад специфічного для API винятку.
    """
    def __init__(self, status_code: int, detail: str, error_code: str = "API_ERROR"):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code

# async def api_specific_exception_handler(request: Request, exc: APISpecificException):
#     """
#     Обробник для APISpecificException.
#     """
#     logger.error(
#         f"API Specific Exception: Status {exc.status_code}, Detail '{exc.detail}', "
#         f"Code '{exc.error_code}' for {request.method} {request.url.path}"
#     )
#     return JSONResponse(
#         status_code=exc.status_code,
#         content={"detail": exc.detail, "error_code": exc.error_code},
#     )

# Якщо цей обробник потрібен, його також треба зареєструвати:
# app_or_router.add_exception_handler(APISpecificException, api_specific_exception_handler)
