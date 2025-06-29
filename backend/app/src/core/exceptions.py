# backend/app/src/core/exceptions.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає кастомні класи винятків, що використовуються в додатку.
Це включає як HTTP винятки, які можуть бути автоматично оброблені FastAPI
для повернення відповідних HTTP відповідей, так і специфічні помилки бізнес-логіки.
"""

from fastapi import HTTPException, status as http_status # Використовуємо статуси з fastapi
from typing import Optional, Dict, Any

from backend.app.src.core.i18n import _ # Імпортуємо функцію перекладу

# --- Базовий клас для кастомних винятків додатку ---
class AppException(Exception):
    """
    Базовий клас для всіх кастомних винятків додатку.
    Дозволяє додати додаткові атрибути, якщо потрібно.
    """
    def __init__(self, message_key: str, *args: Any, **kwargs_format: Any) -> None:
        # message_key - це ключ для перекладу
        # kwargs_format - аргументи для форматування перекладеного рядка
        self.message_key = message_key
        self.kwargs_format = kwargs_format
        # Перекладений рядок буде отримано при необхідності (наприклад, в обробнику винятків)
        # або можна одразу тут: self.translated_message = _(message_key, **kwargs_format)
        # Але тоді локаль має бути відома на момент створення винятку.
        # Краще передавати ключ і форматувати в обробнику, де відома локаль запиту.
        super().__init__(f"AppException: {message_key}") # Базовий Exception приймає рядок

    def get_translated_message(self, locale: Optional[str] = None) -> str:
        """Повертає перекладене повідомлення для заданої локалі."""
        return _(self.message_key, locale=locale, **self.kwargs_format)

    def __str__(self) -> str:
        # Повертає ключ, якщо не перекладено, або перекладене повідомлення для дефолтної локалі.
        # Це для випадків, коли виняток логується або виводиться без явного перекладу.
        return _(self.message_key, **self.kwargs_format)


# --- HTTP Винятки (успадковуються від HTTPException FastAPI) ---
# detail тепер може приймати ключ для перекладу, який буде оброблено в main.py exception_handler

class NotFoundException(HTTPException):
    """
    Виняток для ситуацій, коли запитуваний ресурс не знайдено (HTTP 404).
    """
    def __init__(self, detail_key: str = "error_resource_not_found", headers: Optional[Dict[str, Any]] = None, **kwargs_format: Any) -> None:
        # Перекладаємо ключ одразу, якщо локаль не буде передана в обробник.
        # Або передаємо ключ, а обробник перекладає.
        # Поки що передаємо ключ, а обробник в main.py буде відповідати за переклад.
        super().__init__(status_code=http_status.HTTP_404_NOT_FOUND, detail={"key": detail_key, "format_args": kwargs_format}, headers=headers)

class BadRequestException(HTTPException):
    """
    Виняток для некоректних запитів (HTTP 400).
    Використовується, коли дані запиту не валідні або відсутні необхідні параметри.
    """
    def __init__(self, detail_key: str = "error_bad_request", headers: Optional[Dict[str, Any]] = None, **kwargs_format: Any) -> None:
        super().__init__(status_code=http_status.HTTP_400_BAD_REQUEST, detail={"key": detail_key, "format_args": kwargs_format}, headers=headers)

class UnauthorizedException(HTTPException):
    """
    Виняток для неавторизованого доступу (HTTP 401).
    Використовується, коли користувач не автентифікований, але намагається отримати доступ
    до ресурсу, що потребує автентифікації.
    Зазвичай включає заголовок WWW-Authenticate.
    """
    def __init__(self, detail_key: str = "error_unauthorized", headers: Optional[Dict[str, Any]] = None, **kwargs_format: Any) -> None:
        if headers is None:
            headers = {"WWW-Authenticate": "Bearer"}
        super().__init__(status_code=http_status.HTTP_401_UNAUTHORIZED, detail={"key": detail_key, "format_args": kwargs_format}, headers=headers)

class ForbiddenException(HTTPException):
    """
    Виняток для забороненого доступу (HTTP 403).
    Використовується, коли користувач автентифікований, але не має достатньо прав
    для доступу до ресурсу або виконання дії.
    """
    def __init__(self, detail_key: str = "error_forbidden", headers: Optional[Dict[str, Any]] = None, **kwargs_format: Any) -> None:
        super().__init__(status_code=http_status.HTTP_403_FORBIDDEN, detail={"key": detail_key, "format_args": kwargs_format}, headers=headers)

class UnprocessableEntityException(HTTPException):
    """
    Виняток для неможливості обробки сутності (HTTP 422).
    Часто використовується FastAPI для помилок валідації Pydantic схем.
    Може використовуватися і для інших семантичних помилок в даних.
    `detail` тут може бути складним об'єктом (списком помилок валідації).
    Якщо це наш кастомний виклик, то передаємо ключ.
    """
    def __init__(self, detail: Any = None, headers: Optional[Dict[str, Any]] = None, detail_key: str = "error_unprocessable_entity", **kwargs_format: Any) -> None:
        # Якщо detail не передано, використовуємо detail_key.
        # Якщо detail передано (наприклад, помилки валідації FastAPI), використовуємо його.
        processed_detail = detail
        if detail is None:
            processed_detail = {"key": detail_key, "format_args": kwargs_format}
        super().__init__(status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, detail=processed_detail, headers=headers)


class ConflictException(HTTPException):
    """
    Виняток для конфліктних запитів (HTTP 409).
    Наприклад, спроба створити ресурс, який вже існує (з унікальним полем).
    """
    def __init__(self, detail_key: str = "error_conflict_resource", headers: Optional[Dict[str, Any]] = None, **kwargs_format: Any) -> None:
        super().__init__(status_code=http_status.HTTP_409_CONFLICT, detail={"key": detail_key, "format_args": kwargs_format}, headers=headers)

class InternalServerErrorException(HTTPException):
    """
    Виняток для внутрішніх помилок сервера (HTTP 500).
    Використовується для непередбачених помилок на сервері.
    """
    def __init__(self, detail_key: str = "error_internal_server", headers: Optional[Dict[str, Any]] = None, **kwargs_format: Any) -> None:
        super().__init__(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail={"key": detail_key, "format_args": kwargs_format}, headers=headers)


# --- Специфічні винятки бізнес-логіки (успадковуються від AppException) ---

class DatabaseErrorException(AppException):
    """Виняток, пов'язаний з помилками бази даних."""
    def __init__(self, message_key: str = "error_database", original_exception: Optional[Exception] = None, **kwargs_format: Any) -> None:
        super().__init__(message_key, **kwargs_format)
        self.original_exception = original_exception

class BusinessLogicException(AppException):
    """Загальний виняток для помилок бізнес-логіки."""
    def __init__(self, message_key: str = "error_business_logic", **kwargs_format: Any) -> None:
        super().__init__(message_key, **kwargs_format)

class AuthenticationFailedException(BusinessLogicException):
    """Виняток при невдалій автентифікації (неправильний логін/пароль)."""
    def __init__(self, message_key: str = "error_auth_failed", **kwargs_format: Any) -> None:
        super().__init__(message_key, **kwargs_format)

class InsufficientPermissionsException(BusinessLogicException):
    """Виняток при недостатніх правах для виконання дії."""
    def __init__(self, message_key: str = "error_insufficient_permissions", **kwargs_format: Any) -> None:
        super().__init__(message_key, **kwargs_format)

class ResourceAlreadyExistsException(BusinessLogicException):
    """Виняток при спробі створити ресурс, що вже існує."""
    def __init__(self, resource_name: str = "Ресурс", identifier: Optional[Any] = None) -> None:
        # resource_name може бути ключем для перекладу або вже перекладеним рядком.
        # Для простоти, поки що залишимо resource_name як є, а identifier використовуємо в форматуванні.
        super().__init__("error_resource_already_exists", resource_name=_(resource_name), identifier=identifier)

class ResourceNotFoundException(BusinessLogicException):
    """Виняток, якщо ресурс не знайдено в бізнес-логіці (не HTTP 404)."""
    def __init__(self, resource_name: str = "Ресурс", identifier: Optional[Any] = None) -> None:
        super().__init__("error_resource_not_found_details", resource_name=_(resource_name), identifier=identifier)

# TODO: Додати інші специфічні винятки, якщо потрібно.
# Наприклад:
# - InvalidTokenException (для невалідних JWT токенів) -> перетворюється в UnauthorizedException
# - ExpiredTokenException (для прострочених JWT токенів) -> перетворюється в UnauthorizedException
# - EmailAlreadyExistsException -> ConflictException
# - UserNotFoundException -> NotFoundException
# - InsufficientFundsException (для бонусів) -> BadRequestException або кастомний
# - TaskAssignmentException (помилки при призначенні завдань) -> BusinessLogicException / BadRequestException

# Обробники винятків (Exception Handlers) для FastAPI:
# В `main.py` можна буде додати обробники для перетворення кастомних винятків бізнес-логіки
# у відповідні HTTP відповіді.
#
# from fastapi import Request
# from fastapi.responses import JSONResponse
#
# @app.exception_handler(DatabaseErrorException)
# async def database_error_exception_handler(request: Request, exc: DatabaseErrorException):
#     # Логування помилки exc.original_exception
#     return JSONResponse(
#         status_code=http_status.HTTP_503_SERVICE_UNAVAILABLE, # Або 500
#         content={"detail": exc.message or "Помилка доступу до бази даних"},
#     )
#
# @app.exception_handler(AuthenticationFailedException)
# async def auth_failed_exception_handler(request: Request, exc: AuthenticationFailedException):
#     raise UnauthorizedException(detail=exc.message) # Перетворюємо на стандартний HTTP виняток
#
# Цей код тут лише для ілюстрації.

# Все виглядає як хороший набір базових та HTTP винятків.
# Використання стандартних HTTP статусів з `fastapi.status` є хорошою практикою.
# `AppException` як базовий клас для кастомних не-HTTP винятків також корисно.
# `detail` в HTTPException може бути рядком або списком/словником (для помилок валідації від Pydantic).
# Тут для простоти `detail` - це рядок.
#
# Все готово.

class InvalidTokenException(UnauthorizedException):
    """Виняток для невалідних або прострочених токенів (не лише JWT, а й refresh, one-time)."""
    def __init__(self, detail_key: str = "error_invalid_or_expired_token", headers: Optional[Dict[str, Any]] = None, **kwargs_format: Any) -> None:
        # WWW-Authenticate може бути недоречним для всіх типів невалідних токенів,
        # але оскільки успадковується від UnauthorizedException, він буде.
        # Можна перекрити, якщо потрібно.
        super().__init__(detail_key=detail_key, headers=headers, **kwargs_format)
