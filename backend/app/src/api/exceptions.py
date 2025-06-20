# backend/app/src/api/exceptions.py
# -*- coding: utf-8 -*-
from backend.app.src.core.i18n import _
"""
Модуль для визначення та реєстрації обробників винятків, специфічних для API.

FastAPI дозволяє визначати кастомні обробники для різних типів винятків.
Це дозволяє стандартизувати формат відповідей про помилки,
додавати додаткову інформацію для логування або клієнта.

Сумісність: Python 3.13, SQLAlchemy v2, Pydantic v2.
"""

from typing import Any, Dict, Union

from fastapi import FastAPI, Request, HTTPException, status, APIRouter
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from backend.app.src.config import settings  # Стандартизований імпорт settings
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)


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
        location_str = ".".join(str(loc) for loc in error.get("loc", (_("api_exceptions.unknown_location"),)))
        location_str = location_str.replace(".[", "[").replace("body.", "")

        error_details.append({
            "field": location_str,
            "message": error.get("msg"), # Повідомлення від Pydantic зазвичай англійською, їх можна мапити або перекладати окремо, якщо потрібно
            "type": error.get("type"),
        })

    response_message = _("api_exceptions.validation.response_message_generic")
    log_message = _(
        "api_exceptions.validation.log_message_details",
        method=request.method,
        path=request.url.path,
        error_details=str(error_details), # str() для логування
        client_host=request.client.host if request.client else _("api_exceptions.not_applicable_short")
    )
    logger.warning(log_message)

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "type": _("api_exceptions.validation.error_type_name"), # "VALIDATION_ERROR"
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
    log_message = _(
        "api_exceptions.http.log_message_details",
        status_code=exc.status_code,
        detail=exc.detail,
        method=request.method,
        path=request.url.path,
        headers=str(exc.headers), # str() для логування
        client_host=request.client.host if request.client else _("api_exceptions.not_applicable_short")
    )

    error_type = _("api_exceptions.http.default_error_type_name") # "HTTP_EXCEPTION"
    if exc.headers and "X-Error-Type" in exc.headers: # Це залишаємо, якщо використовується
        error_type = exc.headers["X-Error-Type"]
    # Можна додати більш гранульовані типи помилок на основі статус-коду, якщо потрібно
    elif exc.status_code == status.HTTP_401_UNAUTHORIZED:
        error_type = _("api_exceptions.http.error_type_401_name") # "AUTHENTICATION_ERROR"
    elif exc.status_code == status.HTTP_403_FORBIDDEN:
        error_type = _("api_exceptions.http.error_type_403_name") # "AUTHORIZATION_ERROR"
    elif exc.status_code == status.HTTP_404_NOT_FOUND:
        error_type = _("api_exceptions.http.error_type_404_name") # "NOT_FOUND_ERROR"


    if 500 <= exc.status_code < 600:
        logger.error(log_message, exc_info=exc if settings.DEBUG else True)
    else:
        logger.warning(log_message)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": error_type,
                "message": exc.detail, # exc.detail - це вже повідомлення для користувача, яке може бути перекладеним там, де виняток генерується
            }
        },
        headers=exc.headers,
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
        _("api_exceptions.generic.unhandled_exception_log", method=request.method, path=request.url.path, error_message=str(exc)),
        exc_info=True
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "type": _("api_exceptions.generic.error_type_500_name"), # "INTERNAL_SERVER_ERROR"
                "message": _("api_exceptions.generic.user_message_500"),
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
#         _("api_exceptions.custom_app.log_details", error_code=exc.error_code, detail=exc.detail, method=request.method, path=request.url.path, data=str(exc.data)),
#         exc_info=True
#     )
#     return JSONResponse(
#         status_code=exc.status_code,
#         content={
#             "error": {
#                 "type": exc.error_code,
#                 "message": exc.detail, # Припускаємо, що exc.detail вже перекладено
#                 "data": exc.data,
#             }
#         },
#     )

def register_exception_handlers(app_or_router: Union[FastAPI, APIRouter]) -> None:
    """
    Реєструє кастомні обробники винятків для FastAPI додатку або APIRouter.
    """
    app_or_router.add_exception_handler(RequestValidationError, custom_request_validation_exception_handler)
    logger.debug(_("api_exceptions.log.handler_registered_request_validation_error"))

    app_or_router.add_exception_handler(HTTPException, custom_http_exception_handler)
    logger.debug(_("api_exceptions.log.handler_registered_http_exception"))

    app_or_router.add_exception_handler(Exception, generic_exception_handler)
    logger.debug(_("api_exceptions.log.handler_registered_generic_exception"))

    # TODO: Зареєструвати обробник для CustomAppException, коли він буде визначений
    # from backend.app.src.core.exceptions import CustomAppException # Приклад
    # app_or_router.add_exception_handler(CustomAppException, custom_app_exception_handler)
    # logger.debug(_("api_exceptions.log.handler_registered_custom_app_exception"))

    logger.info(_("api_exceptions.log.all_handlers_registered_successfully"))


logger.info(_("api_exceptions.log.module_loaded_info"))
