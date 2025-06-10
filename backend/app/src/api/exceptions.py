# backend/app/src/api/exceptions.py
# -*- coding: utf-8 -*-
"""
Модуль для визначення та реєстрації обробників винятків, специфічних для API.

FastAPI дозволяє визначати кастомні обробники для різних типів винятків.
Це дозволяє стандартизувати формат відповідей про помилки,
додавати додаткову інформацію для логування або клієнта.

Обробники винятків зазвичай реєструються в основному екземплярі FastAPI
або в APIRouter.
"""

import logging
from typing import Any, Dict, Union # Union для типізації app_or_router

from fastapi import FastAPI, Request, HTTPException, status, APIRouter # APIRouter для типізації
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
# from starlette.exceptions import HTTPException as StarletteHTTPException # Можна також обробляти винятки Starlette

# Приклад імпорту кастомного винятку з core. Якщо такого файлу/класу немає, це буде помилка.
# Поки що закоментуємо, оскільки core.exceptions ще не створено.
# from app.src.core.exceptions import CustomAppException

logger = logging.getLogger(__name__)

# --- Кастомний обробник для помилок валідації Pydantic (RequestValidationError) ---
async def custom_request_validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """
    Обробляє винятки `RequestValidationError`, які виникають, коли дані запиту
    (тіло, параметри шляху/запиту, заголовки) не проходять валідацію Pydantic.

    Повертає відповідь зі статусом 422 та детальним описом помилок валідації.
    Формат відповіді можна налаштувати для відповідності стандартам API.
    """
    error_details = []
    for error in exc.errors():
        # Формуємо деталі помилки. 'loc' - це кортеж, що вказує шлях до поля.
        # Наприклад, ('body', 'items', 0, 'name') -> "body.items[0].name"
        location_str = ""
        if error.get("loc"):
            location_parts = []
            for part in error.get("loc", []):
                if isinstance(part, int):
                    location_parts.append(f"[{part}]")
                else:
                    location_parts.append(str(part))
            # Об'єднуємо частини, видаляючи зайві точки для індексів масивів
            location_str = ".".join(p for p in location_parts if p).replace(".[", "[")


        error_details.append({
            "field": location_str or "unknown", # Поле, де сталася помилка
            "message": error.get("msg"),      # Повідомлення про помилку
            "type": error.get("type"),    # Тип помилки (наприклад, "value_error.missing")
            # "ctx": error.get("ctx", {})   # Додатковий контекст помилки (може бути великим)
        })

    # Логування помилки валідації
    # Уникаємо логування тіла запиту (exc.body), якщо воно може містити чутливі дані.
    # Замість цього логуємо лише деталі помилок.
    logger.warning(
        f"Помилка валідації запиту: {request.method} {request.url.path}. "
        f"Деталі помилок: {error_details}. "
        f"Клієнт: {request.client.host if request.client else 'N/A'}"
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": { # Стандартизована структура помилки
                "type": "VALIDATION_ERROR",
                "message": "Помилка валідації вхідних даних. Перевірте надані параметри.",
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
    Обробляє стандартні винятки `HTTPException` з FastAPI (та Starlette, якщо зареєстровано).
    Дозволяє уніфікувати формат відповіді для всіх HTTP помилок, що генеруються
    через `raise HTTPException(...)`.
    """
    # Логування HTTP винятку. Уникаємо логування тіла запиту за замовчуванням.
    log_message = (
        f"HTTP виняток оброблено: Статус={exc.status_code}, Деталі='{exc.detail}' "
        f"для {request.method} {request.url.path}. "
        f"Заголовки винятку: {exc.headers}. Клієнт: {request.client.host if request.client else 'N/A'}"
    )
    # Для помилок сервера (5xx) логуємо з рівнем ERROR, для клієнтських (4xx) - WARNING
    if 500 <= exc.status_code < 600:
        logger.error(log_message, exc_info=True) # Додаємо traceback для серверних помилок
    else:
        logger.warning(log_message)

    response_content: Dict[str, Any] = {
        "error": {
            # Спробуємо отримати кастомний код помилки з заголовка X-Error-Code, якщо він є
            "type": exc.headers.get("X-Error-Code", "HTTP_EXCEPTION") if exc.headers else "HTTP_EXCEPTION",
            "message": exc.detail, # Повідомлення з HTTPException
        }
    }
    # Якщо є додаткові деталі в HTTPException (нестандартне поле, але можна додати при створенні винятку)
    # if hasattr(exc, "custom_details") and exc.custom_details:
    #    response_content["error"]["details"] = exc.custom_details

    return JSONResponse(
        status_code=exc.status_code, # Використовуємо статус-код з оригінального винятку
        content=response_content,
        headers=exc.headers, # Передаємо оригінальні заголовки (наприклад, WWW-Authenticate для 401)
    )

# --- Приклад обробника для кастомного винятку з app.src.core.exceptions ---
# # Припустимо, CustomAppException визначено так:
# class CustomAppException(Exception): # Або успадковується від HTTPException
#     def __init__(self, status_code: int, detail: str, error_code: Optional[str] = None, custom_data: Optional[Dict[str, Any]] = None):
#         self.status_code = status_code
#         self.detail = detail
#         self.error_code = error_code or "CUSTOM_APP_ERROR"
#         self.custom_data = custom_data
#         super().__init__(detail)

# async def my_custom_app_exception_handler(request: Request, exc: CustomAppException) -> JSONResponse:
#     logger.error(
#         f"Кастомний виняток додатку '{exc.error_code}': {exc.detail} для {request.method} {request.url.path}. "
#         f"Додаткові дані: {exc.custom_data}",
#         exc_info=True # Логуємо traceback для кастомних помилок серверної логіки
#     )
#     return JSONResponse(
#         status_code=exc.status_code, # Використовуємо статус код з винятку
#         content={
#             "error": {
#                 "type": exc.error_code,
#                 "message": exc.detail,
#                 "data": exc.custom_data if exc.custom_data else None, # Додаткові структуровані дані
#             }
#         },
#     )


def register_exception_handlers(app_or_router: Union[FastAPI, APIRouter]) -> None:
    """
    Реєструє кастомні обробники винятків для FastAPI додатку або APIRouter.
    Цю функцію можна викликати в main.py для глобальних обробників,
    або в api/router.py (чи в v1/router.py) для специфічних для роутера обробників.

    Args:
        app_or_router: Екземпляр FastAPI додатку або APIRouter, до якого додаються обробники.
    """
    app_or_router.add_exception_handler(RequestValidationError, custom_request_validation_exception_handler)
    logger.debug("Зареєстровано обробник для RequestValidationError.")

    app_or_router.add_exception_handler(HTTPException, custom_http_exception_handler)
    logger.debug("Зареєстровано обробник для HTTPException.")

    # Якщо ви використовуєте StarletteHTTPException напряму і хочете його так само обробляти:
    # from starlette.exceptions import HTTPException as StarletteHTTPException
    # app_or_router.add_exception_handler(StarletteHTTPException, custom_http_exception_handler)
    # logger.debug("Зареєстровано обробник для StarletteHTTPException.")

    # Реєстрація кастомного обробника (розкоментуйте, коли CustomAppException буде визначено)
    # app_or_router.add_exception_handler(CustomAppException, my_custom_app_exception_handler)
    # logger.debug("Зареєстровано обробник для CustomAppException.")

    logger.info("Кастомні обробники винятків API успішно зареєстровано.")

# Приклад використання в main.py:
# --- main.py ---
# from fastapi import FastAPI
# from app.src.api.exceptions import register_exception_handlers
#
# app = FastAPI(title="My Kudos App")
# register_exception_handlers(app) # Реєстрація глобально для всього додатку
#
# # ... підключення роутерів ...
#
# Або в api/router.py (якщо api_router - це APIRouter, і ви хочете, щоб ці обробники
# застосовувалися тільки до шляхів, визначених в api_router та його під-роутерах):
# --- api/router.py ---
# from . import api_router # Припускаючи, що api_router визначено в __init__.py або тут
# from .exceptions import register_exception_handlers
# register_exception_handlers(api_router) # Реєстрація для конкретного роутера

logger.info("Модуль 'api.exceptions' завантажено. Визначено: custom_request_validation_exception_handler, custom_http_exception_handler, register_exception_handlers.")
