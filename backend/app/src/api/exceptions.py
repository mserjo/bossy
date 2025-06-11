# backend/app/src/api/exceptions.py
# -*- coding: utf-8 -*-
"""
Модуль для визначення та реєстрації обробників винятків, специфічних для API.

FastAPI дозволяє визначати кастомні обробники для різних типів винятків.
Це дозволяє стандартизувати формат відповідей про помилки,
додавати додаткову інформацію для логування або клієнта.
"""

# import logging # Замінено на централізований логер
from typing import Any, Dict, Union

from fastapi import FastAPI, Request, HTTPException, status, APIRouter
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
# from starlette.exceptions import HTTPException as StarletteHTTPException # Можна також обробляти винятки Starlette

# Повні шляхи імпорту
from backend.app.src.config.logging import logger # Централізований логер
from backend.app.src.config import settings as global_settings # Для доступу до DEBUG тощо
# from backend.app.src.core.exceptions import CustomAppException # Приклад, якщо визначено


# --- Кастомний обробник для помилок валідації Pydantic (RequestValidationError) ---
async def custom_request_validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """
    Обробляє винятки `RequestValidationError` від FastAPI, які виникають, коли дані запиту
    не проходять валідацію Pydantic.

    Повертає відповідь зі статусом 422 та детальним описом помилок валідації.
    """
    error_details = []
    for error in exc.errors():
        location_str = ".".join(str(loc) for loc in error.get("loc", ("unknown",))) # unknown - i18n
        location_str = location_str.replace(".[", "[").replace("body.", "") # Спрощення шляху

        error_details.append({
            "field": location_str,
            "message": error.get("msg"),
            "type": error.get("type"),
        })

    # i18n
    response_message = "Помилка валідації вхідних даних. Перевірте надані параметри."
    log_message = (
        f"Помилка валідації запиту: {request.method} {request.url.path}. "
        f"Деталі: {error_details}. Клієнт: {request.client.host if request.client else 'N/A'}"
    )
    logger.warning(log_message)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "type": "VALIDATION_ERROR", # i18n
                "message": response_message,
                "details": error_details,
            }
        },
    )

# --- Кастомний обробник для HTTPException ---
async def custom_http_exception_handler(
    request: Request,
    exc: HTTPException
) -> JSONResponse:
    """
    Обробляє стандартні винятки `HTTPException` з FastAPI.
    Уніфікує формат відповіді для всіх HTTP помилок.
    """
    log_message = (
        f"HTTP виняток: Статус={exc.status_code}, Деталі='{exc.detail}' "
        f"для {request.method} {request.url.path}. "
        f"Заголовки: {exc.headers}. Клієнт: {request.client.host if request.client else 'N/A'}"
    )

    error_type = "HTTP_EXCEPTION" # i18n
    # Спробуємо отримати більш конкретний тип помилки, якщо він переданий через X-Error-Type
    # (нестандартний, але може бути корисним для внутрішніх потреб)
    if exc.headers and "X-Error-Type" in exc.headers:
        error_type = exc.headers["X-Error-Type"]

    if 500 <= exc.status_code < 600:
        logger.error(log_message, exc_info=exc if global_settings.DEBUG else True) # traceback для серверних помилок
    else:
        logger.warning(log_message)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": error_type,
                "message": exc.detail, # Повідомлення з HTTPException
            }
        },
        headers=exc.headers, # Передаємо оригінальні заголовки (наприклад, WWW-Authenticate)
    )

# --- Загальний обробник для всіх інших винятків (500 Internal Server Error) ---
async def generic_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    Обробляє будь-які неперехоплені винятки, повертаючи стандартизовану відповідь 500.
    Логує повний traceback для діагностики.
    """
    logger.error(
        f"Необроблений виняток: {request.method} {request.url.path}. Помилка: {exc}",
        exc_info=True # Завжди логуємо повний traceback для невідомих помилок
    )
    # i18n
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "type": "INTERNAL_SERVER_ERROR", # i18n
                "message": "Виникла непередбачена помилка на сервері. Будь ласка, спробуйте пізніше.", # i18n
                # Не передаємо деталі винятку клієнту з міркувань безпеки
            }
        },
    )

# --- Приклад обробника для кастомного винятку з backend.app.src.core.exceptions ---
# TODO: Визначити CustomAppException в backend/app/src/core/exceptions.py
# class CustomAppException(Exception):
#     def __init__(self, status_code: int, detail: str, error_code: Optional[str] = None, data: Optional[Dict[str, Any]] = None):
#         self.status_code = status_code
#         self.detail = detail # Це повідомлення для клієнта
#         self.error_code = error_code or self.__class__.__name__.upper() # Використовуємо ім'я класу як код помилки
#         self.data = data # Додаткові структуровані дані
#         super().__init__(self.detail)

# async def custom_app_exception_handler(request: Request, exc: CustomAppException) -> JSONResponse:
#     logger.error(
#         f"Кастомний виняток '{exc.error_code}': {exc.detail} для {request.method} {request.url.path}. Дані: {exc.data}",
#         exc_info=True
#     )
#     return JSONResponse(
#         status_code=exc.status_code,
#         content={
#             "error": {
#                 "type": exc.error_code,
#                 "message": exc.detail,
#                 "data": exc.data,
#             }
#         },
#     )

def register_exception_handlers(app_or_router: Union[FastAPI, APIRouter]) -> None:
    """
    Реєструє кастомні обробники винятків для FastAPI додатку або APIRouter.
    """
    app_or_router.add_exception_handler(RequestValidationError, custom_request_validation_exception_handler)
    logger.debug("Зареєстровано обробник для RequestValidationError.")

    app_or_router.add_exception_handler(HTTPException, custom_http_exception_handler)
    logger.debug("Зареєстровано обробник для HTTPException.")

    # Реєструємо загальний обробник останнім, щоб він не перехоплював специфічніші HTTPExceptions
    app_or_router.add_exception_handler(Exception, generic_exception_handler)
    logger.debug("Зареєстровано загальний обробник для Exception (500 Internal Server Error).")


    # TODO: Зареєструвати обробник для CustomAppException, коли він буде визначений
    # from backend.app.src.core.exceptions import CustomAppException # Приклад
    # app_or_router.add_exception_handler(CustomAppException, custom_app_exception_handler)
    # logger.debug("Зареєстровано обробник для CustomAppException.")

    logger.info("Кастомні обробники винятків API успішно зареєстровано.")


logger.info("Модуль 'api.exceptions' завантажено. Визначено обробники для RequestValidationError, HTTPException та загальний Exception.")
