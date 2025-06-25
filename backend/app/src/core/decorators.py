# backend/app/src/core/decorators.py
# -*- coding: utf-8 -*-
"""
Цей модуль призначений для визначення кастомних декораторів,
які можуть використовуватися в різних частинах додатку для додавання
повторюваної функціональності до функцій або методів.

Приклади можливих декораторів:
- Декоратор для логування викликів функцій та їх результатів.
- Декоратор для обробки транзакцій БД (автоматичний commit/rollback).
- Декоратор для перевірки дозволів (хоча це часто робиться через FastAPI Depends).
- Декоратор для кешування результатів функцій.
- Декоратор для вимірювання часу виконання функцій.
"""

import functools
from typing import Callable, Any, Coroutine # Coroutine для асинхронних функцій
import time

# Імпорт логгера
from backend.app.src.config.logging import logger
# Імпорт сесії БД для декоратора транзакцій (якщо буде)
# from backend.app.src.config.database import AsyncSessionLocal # Приклад

# --- Приклад декоратора для логування ---
def log_function_call(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Декоратор для логування інформації про виклик функції (назва, аргументи)
    та її результат або виняток.
    Працює як для синхронних, так і для асинхронних функцій.
    """
    @functools.wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        func_name = func.__name__
        logger.debug(f"Виклик асинхронної функції {func_name} з args: {args}, kwargs: {kwargs}")
        try:
            result = await func(*args, **kwargs)
            logger.debug(f"Асинхронна функція {func_name} успішно виконана, результат: {result}")
            return result
        except Exception as e:
            logger.error(f"Помилка в асинхронній функції {func_name}: {e}", exc_info=True)
            raise

    @functools.wraps(func)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        func_name = func.__name__
        logger.debug(f"Виклик синхронної функції {func_name} з args: {args}, kwargs: {kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"Синхронна функція {func_name} успішно виконана, результат: {result}")
            return result
        except Exception as e:
            logger.error(f"Помилка в синхронній функції {func_name}: {e}", exc_info=True)
            raise

    if asyncio.iscoroutinefunction(func): # Перевіряємо, чи функція асинхронна
        return async_wrapper
    else:
        return sync_wrapper

# --- Приклад декоратора для вимірювання часу виконання ---
def timing_decorator(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Декоратор для вимірювання та логування часу виконання функції.
    Працює як для синхронних, так і для асинхронних функцій.
    """
    @functools.wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        func_name = func.__name__
        start_time = time.perf_counter()
        logger.trace(f"Початок виконання асинхронної функції {func_name}")
        try:
            return await func(*args, **kwargs)
        finally:
            end_time = time.perf_counter()
            total_time = end_time - start_time
            logger.info(f"Асинхронна функція {func_name} виконана за {total_time:.4f} секунд.")

    @functools.wraps(func)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        func_name = func.__name__
        start_time = time.perf_counter()
        logger.trace(f"Початок виконання синхронної функції {func_name}")
        try:
            return func(*args, **kwargs)
        finally:
            end_time = time.perf_counter()
            total_time = end_time - start_time
            logger.info(f"Синхронна функція {func_name} виконана за {total_time:.4f} секунд.")

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper

# --- Приклад декоратора для управління транзакціями БД (концептуально) ---
# Потребує доступу до сесії БД. Це може бути складно реалізувати як універсальний
# декоратор без передачі сесії або використання контекстних змінних.
# Часто ця логіка інкапсулюється в базовому сервісі або використовується
# `async with AsyncSessionLocal() as session:` в кожному методі сервісу.
#
# def manage_transaction(func: Callable[..., Coroutine[Any, Any, Any]]):
#     """
#     Декоратор для автоматичного commit/rollback транзакції БД.
#     Призначений для асинхронних функцій, які приймають `db: AsyncSession` як один з аргументів.
#     """
#     @functools.wraps(func)
#     async def wrapper(*args: Any, **kwargs: Any) -> Any:
#         db_session: Optional[AsyncSession] = None
#         # Спроба знайти сесію в аргументах або kwargs
#         for arg in args:
#             if isinstance(arg, AsyncSession):
#                 db_session = arg
#                 break
#         if not db_session and 'db' in kwargs and isinstance(kwargs['db'], AsyncSession):
#             db_session = kwargs['db']
#         elif not db_session and 'db_session' in kwargs and isinstance(kwargs['db_session'], AsyncSession):
#             db_session = kwargs['db_session']
#
#         if not db_session:
#             # Якщо сесія не передана, можливо, вона створюється всередині?
#             # Або декоратор використовується неправильно.
#             # Можна створити нову сесію тут, але це не ідеально.
#             logger.warning(f"Декоратор manage_transaction для функції {func.__name__} не знайшов сесію БД в аргументах.")
#             # Просто викликаємо функцію без управління транзакцією тут.
#             return await func(*args, **kwargs)
#
#         try:
#             result = await func(*args, **kwargs)
#             await db_session.commit()
#             logger.debug(f"Транзакцію для {func.__name__} успішно закоммічено.")
#             return result
#         except Exception as e:
#             logger.error(f"Помилка в функції {func.__name__} під час транзакції, відкочую: {e}", exc_info=True)
#             await db_session.rollback()
#             raise
#         # finally:
#             # Закриття сесії тут може бути зайвим, якщо сесія керується залежністю FastAPI.
#             # await db_session.close()
#     return wrapper


# TODO: Додати інші кастомні декоратори за потреби.
# Наприклад, для кешування результатів, перевірки певних умов тощо.
#
# Важливо: при написанні декораторів для асинхронних функцій (`async def`)
# потрібно використовувати `async def wrapper` та `await func(...)`.
# `functools.wraps` допомагає зберегти метадані оригінальної функції (назву, docstring).
#
# Декоратор `manage_transaction` є складним, оскільки він має отримати доступ
# до сесії БД. Якщо сесія передається як аргумент, це можливо, але потребує
# консистентності в сигнатурах функцій.
# Альтернатива - використання `asynccontextmanager` для створення контекстного менеджера
# транзакцій, або покладатися на `try/except/finally` з `commit/rollback`
# всередині самих сервісних методів.
# Поки що `manage_transaction` залишено як концептуальний приклад.
#
# Для розрізнення синхронних та асинхронних функцій використовується `asyncio.iscoroutinefunction`.
# Це дозволяє створювати універсальні декоратори, якщо їх логіка може бути застосована до обох типів.
# Потрібен `import asyncio` для цього.
import asyncio

# Все виглядає як хороша основа для модуля з декораторами.
# Надано приклади для логування та вимірювання часу.
# Декоратор для транзакцій - як ідея для подальшого розгляду.
#
# Все готово.
