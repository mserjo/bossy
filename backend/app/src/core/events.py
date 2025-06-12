# backend/app/src/core/events.py
# -*- coding: utf-8 -*-
# # Модуль системи подій для програми Kudos (Virtus).
# #
# # Цей модуль визначає базову структуру для створення та обробки
# # системних подій. Використання подій дозволяє реалізувати шаблон
# # "спостерігач" (Observer) або "видавець-підписник" (Publisher-Subscriber),
# # що сприяє слабкій зв'язності між різними компонентами системи.
# # Наприклад, після реєстрації користувача може бути викликана подія,
# # на яку підписані сервіси для відправки вітального листа, створення
# # профілю за замовчуванням тощо, без прямої залежності реєстраційного
# # сервісу від цих додаткових дій.
# #
# # Основні компоненти:
# # - Базовий клас `BaseEvent` для всіх подій.
# # - Специфічні класи подій, що успадковують `BaseEvent`.
# # - Простий механізм для реєстрації обробників подій та їх диспетчеризації.
# #
# # TODO: Розглянути інтеграцію з більш потужними бібліотеками для обробки подій,
# #       такими як `arq` (для фонових завдань на основі подій), `broadcaster`,
# #       або використання Celery для асинхронної обробки подій, якщо
# #       потреби системи вимагатимуть складнішої логіки або гарантованої доставки.

from abc import ABC, abstractmethod # abstractmethod тут не використовується, але ABC - так
from typing import Dict, List, Callable, Any, Coroutine, Type
import asyncio # Для асинхронних обробників та asyncio.gather

# Імпорт логера з централізованої конфігурації
from backend.app.src.config.logging import get_logger
# TODO: Імпортувати UserModel, TaskModel та інші моделі, коли вони будуть визначені,
#       для типізації в конкретних подіях та уникнення передачі лише ID.
# from backend.app.src.models.auth.user import User as UserModel
# from backend.app.src.models.tasks.task import Task as TaskModel

# Ініціалізація логера для цього модуля
logger = get_logger(__name__)

# --- Базовий клас для подій ---
class BaseEvent(ABC):
    """
    Абстрактний базовий клас для всіх системних подій.
    Кожна конкретна подія в програмі повинна успадковувати цей клас.
    Назва класу події може використовуватися як унікальний тип події для підписки.
    """
    # Можна додати спільні атрибути для всіх подій, наприклад, timestamp їх створення.
    # from datetime import datetime, timezone
    # occurred_at: datetime = datetime.now(timezone.utc) # Потребуватиме `default_factory` в dataclass або __init__

    @property
    def event_name(self) -> str:
        """Повертає назву класу події, яка використовується як її ідентифікатор типу."""
        return self.__class__.__name__

    def __str__(self) -> str:
        """Базове рядкове представлення події для логування."""
        return f"Подія: {self.event_name}"

# --- Специфічні класи подій ---
# Кожен клас події представляє конкретну подію в системі та може нести дані,
# пов'язані з цією подією.

class UserRegisteredEvent(BaseEvent):
    """Подія, що виникає після успішної реєстрації нового користувача."""
    def __init__(self, user_id: int, email: str): # TODO: Замінити на UserModel, коли він буде доступний
        self.user_id = user_id
        self.email = email
        # Логуємо факт створення екземпляра події
        # i18n: Log message for developers - Event initialized
        logger.info(f"Ініційовано подію {self.event_name}: user_id={user_id}, email='{email}'")

    def __str__(self) -> str:
        return f"{super().__str__()} (user_id: {self.user_id}, email: '{self.email}')"

class TaskCompletedEvent(BaseEvent):
    """Подія, що виникає, коли користувач позначає завдання як виконане (до перевірки адміном)."""
    def __init__(self, task_id: int, user_id: int, group_id: int): # TODO: Замінити на TaskModel, UserModel
        self.task_id = task_id
        self.user_id = user_id
        self.group_id = group_id
        # i18n: Log message for developers - Event initialized
        logger.info(f"Ініційовано подію {self.event_name}: task_id={task_id}, user_id={user_id}, group_id={group_id}")

    def __str__(self) -> str:
        return f"{super().__str__()} (task_id: {self.task_id}, user_id: {self.user_id}, group_id: {self.group_id})"

# TODO: Додати інші типи подій, що випливають з `technical_task.txt` та логіки програми, наприклад:
# - TaskVerifiedEvent(task_id: int, verifier_id: int, new_status: TaskStatus, points_awarded: Optional[int])
# - BonusAwardedEvent(user_id: int, amount: int, reason_task_id: Optional[int], description: str)
# - PenaltyAppliedEvent(user_id: int, amount: int, reason_task_id: Optional[int], description: str)
# - GroupInvitationSentEvent(inviter_id: int, invitee_email: str, group_id: int)
# - NewMemberJoinedGroupEvent(user_id: int, group_id: int)
# - UserProfileUpdatedEvent(user_id: int, changed_fields: List[str])


# --- Механізм диспетчеризації подій ---

# Тип для обробника події: асинхронна функція, що приймає екземпляр події BaseEvent (або її нащадка).
EventHandlerType = Callable[[BaseEvent], Coroutine[Any, Any, None]]

# Словник для зберігання підписників на події:
# Ключ - клас події (Type[BaseEvent]), значення - список асинхронних функцій-обробників.
_event_handlers: Dict[Type[BaseEvent], List[EventHandlerType]] = {}

def subscribe(event_type: Type[BaseEvent], handler: EventHandlerType) -> None:
    """
    Підписує функцію-обробник на вказаний тип події.
    Один обробник може бути підписаний на подію лише один раз.

    Args:
        event_type (Type[BaseEvent]): Клас події (наприклад, `UserRegisteredEvent`),
                                      на яку підписується обробник.
        handler (EventHandlerType): Асинхронна функція-обробник, яка буде викликана
                                    при публікації події цього типу.
    """
    if not asyncio.iscoroutinefunction(handler):
        # i18n: Error message for developers
        logger.error(f"Спроба підписати неасинхронний обробник '{handler.__name__}' на подію '{event_type.__name__}'. Обробники повинні бути асинхронними (`async def`).")
        # Можна викликати виняток, якщо це критично:
        # raise TypeError("Обробник подій повинен бути асинхронною функцією (визначеною з `async def`).")
        return

    if event_type not in _event_handlers:
        _event_handlers[event_type] = [] # Ініціалізуємо список обробників для нового типу події

    if handler not in _event_handlers[event_type]:
        _event_handlers[event_type].append(handler)
        # i18n: Log message for developers
        logger.info(f"Обробник '{handler.__name__}' успішно підписано на подію '{event_type.__name__}'.")
    else:
        # i18n: Log message for developers
        logger.warning(f"Обробник '{handler.__name__}' вже підписаний на подію '{event_type.__name__}'. Повторна підписка проігнорована.")

async def publish(event: BaseEvent) -> None:
    """
    Публікує подію, асинхронно викликаючи всіх підписаних на неї обробників.
    Обробники для одного типу події виконуються паралельно за допомогою `asyncio.gather`.

    Args:
        event (BaseEvent): Екземпляр події для публікації.
    """
    event_type = type(event) # Отримуємо фактичний тип переданого об'єкта події
    if event_type in _event_handlers:
        # i18n: Log message for developers
        logger.info(f"Публікація події: {event} (тип: {event.event_name}). Кількість обробників: {len(_event_handlers[event_type])}.")

        # Створюємо список корутин (завдань) для одночасного асинхронного виконання
        tasks_to_run = [handler(event) for handler in _event_handlers[event_type]]

        # Виконуємо всі обробники асинхронно і чекаємо їх завершення.
        # `return_exceptions=True` дозволяє продовжити виконання інших обробників,
        # якщо один з них викликає виняток, та отримати інформацію про виняток.
        results = await asyncio.gather(*tasks_to_run, return_exceptions=True)

        # Обробка результатів виконання (включаючи можливі винятки в обробниках)
        for i, result in enumerate(results):
            handler_name = _event_handlers[event_type][i].__name__
            if isinstance(result, Exception):
                # i18n: Error message for developers
                logger.error(
                    f"Помилка під час виконання обробника '{handler_name}' для події '{event.event_name}': {result}",
                    exc_info=result # Передаємо сам об'єкт винятку для повного трасування стеку
                )
            else:
                # i18n: Log message for developers
                logger.debug(f"Обробник '{handler_name}' для події '{event.event_name}' успішно виконано.")
    else:
        # i18n: Log message for developers
        logger.debug(f"Подія '{event.event_name}' опублікована, але на неї немає підписаних обробників.")


# --- Приклад використання та тестування системи подій ---
if __name__ == "__main__":
    # Налаштування логування для тестування
    # (у реальному додатку це робиться централізовано при старті програми)
    try:
        from backend.app.src.config.logging import setup_logging
        from backend.app.src.config.settings import settings # Потрібно для шляхів логів
        from pathlib import Path
        if settings.LOG_TO_FILE:
            log_file_path = settings.LOG_DIR / f"{Path(__file__).stem}_test.log"
            setup_logging(log_file_path=log_file_path)
        else:
            setup_logging()
    except ImportError:
        import logging as base_logging
        base_logging.basicConfig(level=logging.INFO) # INFO для кращого виводу тестів
        logger.warning("Не вдалося імпортувати setup_logging. Використовується базова конфігурація логування для тестів events.py.")

    logger.info("--- Демонстрація Системи Подій (`core.events`) ---")

    # Приклади асинхронних обробників подій
    async def handle_user_registered_email(event: UserRegisteredEvent):
        # i18n: Log message for developers
        logger.info(f"Обробник EMAIL: Надсилання вітального листа користувачу {event.email} (ID: {event.user_id}).")
        # Імітація асинхронної операції (наприклад, запит до SMTP сервера)
        await asyncio.sleep(0.1)
        # i18n: Log message for developers
        logger.info(f"Обробник EMAIL: Вітальний лист для {event.email} успішно надіслано.")

    async def handle_user_registered_profile(event: UserRegisteredEvent):
        # i18n: Log message for developers
        logger.info(f"Обробник PROFILE: Створення профілю за замовчуванням для користувача {event.user_id}.")
        await asyncio.sleep(0.05) # Імітація створення профілю
        # i18n: Log message for developers
        logger.info(f"Обробник PROFILE: Профіль для користувача {event.user_id} успішно створено.")
        # Приклад виникнення помилки в обробнику для демонстрації `return_exceptions=True`
        if event.user_id == 12345: # Спеціальна умова для тестування помилки
            raise ValueError(f"Тестова помилка в обробнику 'handle_user_registered_profile' для user_id={event.user_id}")


    async def handle_task_completed_notification(event: TaskCompletedEvent):
        # i18n: Log message for developers
        logger.info(
            f"Обробник NOTIFICATION (TaskCompleted): Надсилання сповіщення адміністратору групи {event.group_id} "
            f"про виконання завдання {event.task_id} користувачем {event.user_id}."
        )
        await asyncio.sleep(0.1) # Імітація відправки сповіщення
        # i18n: Log message for developers
        logger.info(f"Обробник NOTIFICATION (TaskCompleted): Сповіщення для групи {event.group_id} успішно надіслано.")

    # Підписка обробників на відповідні події
    subscribe(UserRegisteredEvent, handle_user_registered_email)
    subscribe(UserRegisteredEvent, handle_user_registered_profile)
    subscribe(TaskCompletedEvent, handle_task_completed_notification)

    # Спроба повторної підписки того ж обробника (для демонстрації попередження)
    subscribe(UserRegisteredEvent, handle_user_registered_email)


    async def run_demo_events():
        logger.info("\n--- Публікація Тестових Подій ---")

        # Створення та публікація події реєстрації користувача (очікується успіх)
        user_event_success = UserRegisteredEvent(user_id=123, email="new_user@example.com")
        await publish(user_event_success)

        # Створення та публікація події реєстрації користувача (очікується помилка в одному з обробників)
        logger.info("\n--- Публікація Події з Очікуваною Помилкою в Обробнику ---")
        user_event_with_error = UserRegisteredEvent(user_id=12345, email="error_user@example.com")
        await publish(user_event_with_error) # Один обробник викличе помилку, інший має виконатися

        # Створення та публікація події завершення завдання
        logger.info("\n--- Публікація Іншої Події ---")
        task_event = TaskCompletedEvent(task_id=789, user_id=123, group_id=10)
        await publish(task_event)

        # Публікація події, на яку немає підписників (для демонстрації відповідного логу)
        class UnhandledTestEvent(BaseEvent):
            def __init__(self, data: str): self.data = data
            def __str__(self): return f"{super().__str__()} (data: '{self.data}')"

        unhandled_event = UnhandledTestEvent(data="тестові дані для не обробленої події")
        await publish(unhandled_event)


    # Запуск асинхронної демонстраційної функції
    asyncio.run(run_demo_events())
    logger.info("\nДемонстрація системи подій завершена.")
