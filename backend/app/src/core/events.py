# backend/app/src/core/events.py
# -*- coding: utf-8 -*-
"""
Цей модуль призначений для визначення та обробки системних подій,
якщо в проекті буде використовуватися event-driven підхід.

Події можуть представляти собою значущі зміни стану в системі
(наприклад, "користувач зареєструвався", "завдання виконано", "створено нову групу").
Обробники подій (event handlers/listeners) можуть підписуватися на ці події
та виконувати відповідні дії (наприклад, надіслати сповіщення, оновити статистику,
запустити фонову задачу).

Для реалізації системи подій можуть використовуватися бібліотеки типу `PyDispatcher`,
`blinker`, або кастомна реалізація на основі черг повідомлень (RabbitMQ, Redis Streams)
для асинхронної обробки подій між різними компонентами системи.

На даному етапі створюється заглушка для цього модуля.
"""

from typing import Any, Callable, Dict, List, Type
from abc import ABC, abstractmethod
import asyncio

# Імпорт логгера
from backend.app.src.config.logging import logger

# --- Базовий клас для подій ---
class BaseEvent(ABC):
    """
    Абстрактний базовий клас для всіх системних подій.
    Кожна подія може мати свої специфічні дані (атрибути).
    """
    event_name: str # Унікальна назва типу події

    def __init__(self, **kwargs: Any):
        # Можна ініціалізувати атрибути події через kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __repr__(self) -> str:
        attrs = ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items() if k != "event_name")
        return f"<{self.event_name}({attrs})>"

# --- Приклади конкретних подій ---
# class UserRegisteredEvent(BaseEvent):
#     event_name = "user.registered"
#     user_id: uuid.UUID
#     email: str
#
#     def __init__(self, user_id: uuid.UUID, email: str):
#         super().__init__(user_id=user_id, email=email)

# class TaskCompletedEvent(BaseEvent):
#     event_name = "task.completed"
#     task_id: uuid.UUID
#     user_id: uuid.UUID
#     group_id: uuid.UUID
#     bonus_awarded: Optional[Decimal]
#
#     def __init__(self, task_id: uuid.UUID, user_id: uuid.UUID, group_id: uuid.UUID, bonus_awarded: Optional[Decimal]):
#         super().__init__(task_id=task_id, user_id=user_id, group_id=group_id, bonus_awarded=bonus_awarded)


# --- Базовий клас для обробників подій ---
class BaseEventHandler(ABC):
    """
    Абстрактний базовий клас для обробників подій.
    """
    @abstractmethod
    async def handle(self, event: BaseEvent) -> None:
        """
        Асинхронний метод для обробки події.
        :param event: Екземпляр події, що обробляється.
        """
        pass

# --- Приклади конкретних обробників ---
# class SendWelcomeEmailHandler(BaseEventHandler):
#     async def handle(self, event: BaseEvent) -> None:
#         if isinstance(event, UserRegisteredEvent):
#             logger.info(f"Обробка події {event.event_name}: надсилання вітального листа на {event.email}")
#             # ... логіка надсилання email ...
#             await asyncio.sleep(1) # Імітація асинхронної операції
#             logger.info(f"Вітальний лист для {event.email} надіслано (імітація).")

# class UpdateUserStatsOnTaskCompletionHandler(BaseEventHandler):
#     async def handle(self, event: BaseEvent) -> None:
#         if isinstance(event, TaskCompletedEvent):
#             logger.info(f"Обробка події {event.event_name} для завдання {event.task_id}, користувач {event.user_id}")
#             # ... логіка оновлення статистики користувача ...
#             await asyncio.sleep(0.5)
#             logger.info(f"Статистика для користувача {event.user_id} оновлена (імітація).")


# --- Простий диспетчер подій (Event Dispatcher/Bus) ---
# Це дуже спрощена реалізація для демонстрації.
# У реальному проекті краще використовувати готові бібліотеки або більш надійні рішення.
class EventDispatcher:
    """
    Простий диспетчер подій, що дозволяє реєструвати обробники
    та публікувати події.
    """
    def __init__(self):
        self._handlers: Dict[Type[BaseEvent], List[BaseEventHandler]] = {}

    def register_handler(self, event_type: Type[BaseEvent], handler_instance: BaseEventHandler) -> None:
        """Реєструє обробник для певного типу події."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        if handler_instance not in self._handlers[event_type]:
            self._handlers[event_type].append(handler_instance)
            logger.debug(f"Обробник {handler_instance.__class__.__name__} зареєстровано для події {event_type.event_name}")

    def unregister_handler(self, event_type: Type[BaseEvent], handler_instance: BaseEventHandler) -> None:
        """Видаляє реєстрацію обробника для певного типу події."""
        if event_type in self._handlers and handler_instance in self._handlers[event_type]:
            self._handlers[event_type].remove(handler_instance)
            logger.debug(f"Реєстрацію обробника {handler_instance.__class__.__name__} для події {event_type.event_name} скасовано.")

    async def publish_event(self, event: BaseEvent) -> None:
        """
        Публікує подію, викликаючи всі зареєстровані обробники для цього типу події.
        Обробники викликаються асинхронно та паралельно.
        """
        event_type = type(event)
        if event_type in self._handlers:
            logger.info(f"Публікація події: {event!r}")
            # Збираємо всі задачі обробки події
            tasks = [handler.handle(event) for handler in self._handlers[event_type]]
            # Виконуємо їх паралельно
            # `return_exceptions=True` дозволяє продовжити виконання інших обробників,
            # якщо один з них викликає виняток.
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for i, result in enumerate(results):
                handler_name = self._handlers[event_type][i].__class__.__name__
                if isinstance(result, Exception):
                    logger.error(f"Помилка в обробнику {handler_name} для події {event.event_name}: {result}", exc_info=result)
                else:
                    logger.debug(f"Обробник {handler_name} успішно обробив подію {event.event_name}.")
        else:
            logger.debug(f"Немає зареєстрованих обробників для події: {event!r}")

# Створюємо глобальний екземпляр диспетчера подій,
# який може використовуватися в усьому додатку.
# event_dispatcher = EventDispatcher()

# Приклад використання:
# async def main_example():
#     # Реєстрація обробників
#     user_event_handler = SendWelcomeEmailHandler()
#     task_event_handler = UpdateUserStatsOnTaskCompletionHandler()
#
#     event_dispatcher.register_handler(UserRegisteredEvent, user_event_handler)
#     event_dispatcher.register_handler(TaskCompletedEvent, task_event_handler)
#
#     # Публікація подій
#     user_event = UserRegisteredEvent(user_id=uuid.uuid4(), email="test@example.com")
#     await event_dispatcher.publish_event(user_event)
#
#     task_event = TaskCompletedEvent(task_id=uuid.uuid4(), user_id=uuid.uuid4(), group_id=uuid.uuid4(), bonus_awarded=Decimal("10.0"))
#     await event_dispatcher.publish_event(task_event)

# if __name__ == "__main__":
#     # Для тестування цього модуля
#     # Потрібно налаштувати логгер, якщо запускати окремо
#     logger.add(sys.stderr, level="DEBUG", format=LOG_FORMAT_DETAILED, colorize=True)
#     asyncio.run(main_example())


# TODO: Вирішити, чи буде використовуватися event-driven підхід та яка бібліотека/реалізація.
# Поточна реалізація `EventDispatcher` є дуже простою і може не підійти для складних сценаріїв
# (наприклад, гарантована доставка, повторні спроби, транзакційність подій).
#
# Якщо події будуть оброблятися через Celery (фонові задачі), то замість прямого виклику
# обробників, `publish_event` може створювати та відправляти задачу Celery.
#
# TODO: Визначити конкретні системні події, які будуть використовуватися в проекті,
# та їх обробники.
#
# На даному етапі цей файл є заглушкою, що демонструє можливу структуру
# системи подій. Фактична реалізація залежатиме від архітектурних рішень.
#
# Все готово для базової структури файлу.
# Поки що не створюю глобальний `event_dispatcher`, оскільки це залежить від того,
# як і де він буде ініціалізуватися та використовуватися (наприклад, при старті FastAPI).
# Класи `BaseEvent`, `BaseEventHandler`, `EventDispatcher` визначені як основа.
# Приклади подій та обробників закоментовані.
#
# Все готово.
