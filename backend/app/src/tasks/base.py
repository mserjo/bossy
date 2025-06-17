# backend/app/src/tasks/base.py
# -*- coding: utf-8 -*-
"""
Базові класи для фонових завдань.

Цей модуль визначає абстрактні базові класи або спільні компоненти для
фонових завдань, що використовуються в системі. Це допомагає стандартизувати
створення та управління завданнями, а також надає спільну функціональність,
таку як логування, обробка помилок, або доступ до контексту додатку.

Сумісність: Python 3.13, SQLAlchemy v2, Pydantic v2.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Coroutine, Optional, Awaitable

from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)


class BaseTask(ABC):
    """
    Абстрактний базовий клас для фонових завдань.

    Цей клас надає загальний інтерфейс для всіх фонових завдань у системі.
    Він може бути розширений для інтеграції з конкретними системами черг завдань,
    такими як Celery, APScheduler, або FastAPI BackgroundTasks.

    Атрибути:
        name (str): Унікальне ім'я завдання, використовується для ідентифікації та логування.
        # Можна додати інші спільні атрибути, наприклад, max_retries, timeout, etc.

    Методи:
        run(*args, **kwargs): Абстрактний метод, який повинен бути реалізований
                              в дочірніх класах для виконання основної логіки завдання.
        on_success(result: Any): Метод, що викликається при успішному виконанні завдання.
        on_failure(exception: Exception): Метод, що викликається при помилці виконання завдання.
        execute(*args, **kwargs): Метод для запуску завдання з обробкою успіху/невдачі.
    """

    def __init__(self, name: Optional[str] = None):
        """
        Ініціалізація базового завдання.

        Args:
            name (Optional[str], optional): Ім'я завдання. Якщо не надано, використовується ім'я класу.
        """
        self.name = name or self.__class__.__name__
        self.logger = logging.getLogger(f"task.{self.name}") # Специфічний логер для завдання

    @abstractmethod
    async def run(self, *args: Any, **kwargs: Any) -> Any:
        """
        Основний метод для виконання логіки завдання.
        Має бути реалізований в дочірніх класах.

        Args:
            *args: Позиційні аргументи для завдання.
            **kwargs: Іменовані аргументи для завдання.

        Returns:
            Any: Результат виконання завдання.

        Raises:
            NotImplementedError: Якщо метод не реалізований у дочірньому класі.
        """
        raise NotImplementedError("Метод 'run' повинен бути реалізований у дочірньому класі.")

    async def on_success(self, result: Any) -> None:
        """
        Обробник успішного виконання завдання.
        За замовчуванням логує успішне завершення. Може бути перевизначений.

        Args:
            result (Any): Результат, повернутий методом `run`.
        """
        self.logger.info(f"Завдання '{self.name}' успішно виконано. Результат: {result}")

    async def on_failure(self, exception: Exception) -> None:
        """
        Обробник помилки під час виконання завдання.
        За замовчуванням логує помилку. Може бути перевизначений.

        Args:
            exception (Exception): Виняток, що стався під час виконання.
        """
        self.logger.error(f"Помилка під час виконання завдання '{self.name}': {exception}", exc_info=True)

    async def execute(self, *args: Any, **kwargs: Any) -> Awaitable[Optional[Any]]:
        """
        Запускає завдання з обробкою успіху та невдачі.

        Цей метод обгортає виклик `run` та викликає відповідні
        методи `on_success` або `on_failure`.

        Args:
            *args: Позиційні аргументи для передачі в метод `run`.
            **kwargs: Іменовані аргументи для передачі в метод `run`.

        Returns:
            Coroutine[Any, Any, Any]: Результат виконання завдання або None у випадку помилки.
        """
        self.logger.info(f"Запуск завдання '{self.name}' з аргументами: args={args}, kwargs={kwargs}")
        try:
            result = await self.run(*args, **kwargs)
            await self.on_success(result)
            return result
        except Exception as e:
            await self.on_failure(e)
            # Тут можна додати логіку повторних спроб або специфічну обробку помилок
            # Залежно від вимог, можна повернути None або прокинути виняток далі
            return None
