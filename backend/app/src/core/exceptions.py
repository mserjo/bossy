# backend/app/src/core/exceptions.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає кастомні класи винятків, що використовуються в додатку.
Це включає як HTTP винятки, які можуть бути автоматично оброблені FastAPI
для повернення відповідних HTTP відповідей, так і специфічні помилки бізнес-логіки.
"""

from fastapi import HTTPException, status as http_status # Використовуємо статуси з fastapi
from typing import Optional, Dict, Any

# --- Базовий клас для кастомних винятків додатку ---
class AppException(Exception):
    """
    Базовий клас для всіх кастомних винятків додатку.
    Дозволяє додати додаткові атрибути, якщо потрібно.
    """
    def __init__(self, message: str, *args: Any) -> None:
        super().__init__(message, *args)
        self.message = message

    def __str__(self) -> str:
        return self.message

# --- HTTP Винятки (успадковуються від HTTPException FastAPI) ---
# Ці винятки автоматично перетворюються FastAPI у відповідні HTTP відповіді.

class NotFoundException(HTTPException):
    """
    Виняток для ситуацій, коли запитуваний ресурс не знайдено (HTTP 404).
    """
    def __init__(self, detail: str = "Ресурс не знайдено", headers: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(status_code=http_status.HTTP_404_NOT_FOUND, detail=detail, headers=headers)

class BadRequestException(HTTPException):
    """
    Виняток для некоректних запитів (HTTP 400).
    Використовується, коли дані запиту не валідні або відсутні необхідні параметри.
    """
    def __init__(self, detail: str = "Некоректний запит", headers: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(status_code=http_status.HTTP_400_BAD_REQUEST, detail=detail, headers=headers)

class UnauthorizedException(HTTPException):
    """
    Виняток для неавторизованого доступу (HTTP 401).
    Використовується, коли користувач не автентифікований, але намагається отримати доступ
    до ресурсу, що потребує автентифікації.
    Зазвичай включає заголовок WWW-Authenticate.
    """
    def __init__(self, detail: str = "Не авторизовано", headers: Optional[Dict[str, Any]] = None) -> None:
        # Стандартний заголовок для 401 помилки
        if headers is None:
            headers = {"WWW-Authenticate": "Bearer"}
        super().__init__(status_code=http_status.HTTP_401_UNAUTHORIZED, detail=detail, headers=headers)

class ForbiddenException(HTTPException):
    """
    Виняток для забороненого доступу (HTTP 403).
    Використовується, коли користувач автентифікований, але не має достатньо прав
    для доступу до ресурсу або виконання дії.
    """
    def __init__(self, detail: str = "Доступ заборонено", headers: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(status_code=http_status.HTTP_403_FORBIDDEN, detail=detail, headers=headers)

class UnprocessableEntityException(HTTPException):
    """
    Виняток для неможливості обробки сутності (HTTP 422).
    Часто використовується FastAPI для помилок валідації Pydantic схем.
    Може використовуватися і для інших семантичних помилок в даних.
    """
    def __init__(self, detail: Any = "Неможливо обробити сутність", headers: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail, headers=headers)

class ConflictException(HTTPException):
    """
    Виняток для конфліктних запитів (HTTP 409).
    Наприклад, спроба створити ресурс, який вже існує (з унікальним полем).
    """
    def __init__(self, detail: str = "Конфлікт ресурсу", headers: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(status_code=http_status.HTTP_409_CONFLICT, detail=detail, headers=headers)

class InternalServerErrorException(HTTPException):
    """
    Виняток для внутрішніх помилок сервера (HTTP 500).
    Використовується для непередбачених помилок на сервері.
    """
    def __init__(self, detail: str = "Внутрішня помилка сервера", headers: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail, headers=headers)


# --- Специфічні винятки бізнес-логіки (можуть успадковуватися від AppException або стандартних) ---
# Ці винятки можуть перехоплюватися та оброблятися в сервісному шарі або
# перетворюватися на HTTP винятки за допомогою кастомних обробників винятків FastAPI.

class DatabaseErrorException(AppException):
    """Виняток, пов'язаний з помилками бази даних."""
    def __init__(self, detail: str = "Помилка бази даних", original_exception: Optional[Exception] = None) -> None:
        super().__init__(detail)
        self.original_exception = original_exception

class BusinessLogicException(AppException):
    """Загальний виняток для помилок бізнес-логіки."""
    def __init__(self, detail: str = "Помилка бізнес-логіки") -> None:
        super().__init__(detail)

class AuthenticationFailedException(BusinessLogicException):
    """Виняток при невдалій автентифікації (неправильний логін/пароль)."""
    def __init__(self, detail: str = "Неправильний логін або пароль") -> None:
        super().__init__(detail)
        # Цей виняток може бути перетворений на UnauthorizedException(detail) обробником.

class InsufficientPermissionsException(BusinessLogicException):
    """Виняток при недостатніх правах для виконання дії (не плутати з HTTP 403)."""
    def __init__(self, detail: str = "Недостатньо прав для виконання дії") -> None:
        super().__init__(detail)
        # Може бути перетворений на ForbiddenException(detail).

class ResourceAlreadyExistsException(BusinessLogicException):
    """Виняток при спробі створити ресурс, що вже існує."""
    def __init__(self, resource_name: str = "Ресурс", identifier: Optional[Any] = None) -> None:
        detail = f"{resource_name} "
        if identifier:
            detail += f"з ідентифікатором '{identifier}' "
        detail += "вже існує."
        super().__init__(detail)
        # Може бути перетворений на ConflictException(detail).

class ResourceNotFoundException(BusinessLogicException):
    """Виняток, якщо ресурс не знайдено в бізнес-логіці (не HTTP 404)."""
    def __init__(self, resource_name: str = "Ресурс", identifier: Optional[Any] = None) -> None:
        detail = f"{resource_name} "
        if identifier:
            detail += f"з ідентифікатором '{identifier}' "
        detail += "не знайдено."
        super().__init__(detail)
        # Може бути перетворений на NotFoundException(detail).

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
