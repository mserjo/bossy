# backend/app/src/core/exceptions.py
# -*- coding: utf-8 -*-
"""
Модуль власних винятків для програми Kudos.

Цей модуль визначає ієрархію кастомних класів винятків, що використовуються
в різних частинах програми (сервіси, API, ядро). Використання спеціалізованих
винятків дозволяє більш точно обробляти помилки та повертати змістовні
HTTP-відповіді клієнтам через обробники винятків FastAPI.

Кожен виняток містить:
- `message`: Загальне повідомлення про помилку (для логування або внутрішнього використання).
- `status_code`: HTTP-статус код, який асоціюється з цим типом помилки.
- `detail`: Більш детальне повідомлення або структурована інформація,
            призначена для відображення клієнту (може бути такою ж, як `message`).
"""
from decimal import Decimal # Додано для InsufficientFundsError
from typing import Optional, Dict, Any, List
from backend.app.src.config.logging import get_logger

# Отримання логера для цього модуля
logger = get_logger(__name__)


class AppException(Exception):
    """
    Базовий клас для всіх кастомних винятків програми Kudos.

    Цей клас успадковується від стандартного `Exception` і додає
    атрибути для HTTP-статус коду та деталей помилки, що полегшує
    інтеграцію з обробниками винятків FastAPI.

    Атрибути:
        message (str): Повідомлення про помилку, призначене для логування або внутрішньої діагностики.
        status_code (int): HTTP-статус код, який повинен повертатися клієнту при виникненні цього винятку.
                           За замовчуванням 500 (Внутрішня помилка сервера).
        detail (Optional[Any]): Детальна інформація про помилку, яка може бути безпечно передана клієнту.
                                Якщо не вказано, використовується значення `message`.
    """

    def __init__(self, message: str, status_code: int = 500, detail: Optional[Any] = None):
        super().__init__(message)
        self.message = message  # Внутрішнє повідомлення про помилку
        self.status_code = status_code  # HTTP статус код для відповіді
        # Детальне повідомлення для клієнта; якщо не надано, використовуємо загальне повідомлення
        self.detail = detail if detail is not None else message

    def __str__(self) -> str:
        """Повертає рядкове представлення винятку."""
        return (f"{self.__class__.__name__}(status_code={self.status_code}, "
                f"message='{self.message}', detail='{self.detail}')")


# --- Специфічні винятки програми ---

class RecordNotFoundException(AppException):
    """Викликається, коли запитуваний запис (сутність) не знайдено в базі даних."""

    def __init__(self, entity_name: str, identifier: Any, message: Optional[str] = None, detail: Optional[Any] = None):
        # Формуємо повідомлення за замовчуванням, якщо воно не надане
        # TODO i18n: Translatable message format
        resolved_message = message or f"Сутність '{entity_name}' з ідентифікатором '{identifier}' не знайдено."
        super().__init__(message=resolved_message, status_code=404, detail=detail)
        self.entity_name = entity_name  # Назва сутності (наприклад, "Користувач", "Завдання")
        self.identifier = identifier  # Ідентифікатор, за яким шукали сутність (наприклад, ID, email)


class DuplicateRecordException(AppException):
    """Викликається при спробі створити запис, який порушує обмеження унікальності (наприклад, дублікат email)."""

    def __init__(self, entity_name: str, identifier: Any, message: Optional[str] = None, detail: Optional[Any] = None):
        # TODO i18n: Translatable message format
        resolved_message = message or f"Сутність '{entity_name}' з унікальним полем '{identifier}' вже існує."
        super().__init__(message=resolved_message, status_code=409, detail=detail)  # 409 Conflict
        self.entity_name = entity_name
        self.identifier = identifier  # Значення поля, що спричинило конфлікт


class AuthenticationException(AppException):
    """Викликається при помилках автентифікації (наприклад, недійсні облікові дані, невалідний або прострочений токен)."""

    def __init__(self, message: str = "Помилка автентифікації.", detail: Optional[Any] = None, status_code: int = 401):
        # TODO i18n: Translatable default message
        super().__init__(message=message, status_code=status_code, detail=detail)


class AuthorizationException(AppException):
    """Викликається, коли автентифікований користувач не має достатньо прав для виконання певної дії."""

    def __init__(self, message: str = "Недостатньо прав для виконання цієї дії.", detail: Optional[Any] = None,
                 status_code: int = 403):
        # TODO i18n: Translatable default message
        super().__init__(message=message, status_code=status_code, detail=detail)


class ValidationException(AppException):
    """
    Викликається, коли вхідні дані не проходять валідацію (наприклад, помилки валідації схем Pydantic).

    Атрибут `errors` може містити структурований список помилок валідації,
    подібний до формату помилок Pydantic, для надання детального фідбеку клієнту.
    Самі повідомлення в `errors` (ключ 'msg') також потребуватимуть перекладу, якщо вони є фіксованими рядками.
    """

    def __init__(self, message: str = "Помилка валідації вхідних даних.", errors: Optional[List[Dict[str, Any]]] = None,
                 detail: Optional[Any] = None):
        # TODO i18n: Translatable default message
        # Якщо `detail` не надано, а `errors` є, можна сформувати `detail` з `errors` або використати `message`.
        effective_detail = detail if detail is not None else (errors if errors else message)
        super().__init__(message=message, status_code=422, detail=effective_detail)  # 422 Unprocessable Entity
        self.errors = errors  # Список словників з деталями помилок валідації


class BusinessLogicException(AppException):
    """
    Викликається для загальних помилок бізнес-логіки, які не підпадають під інші специфічні категорії винятків.
    Наприклад, спроба виконати операцію над сутністю, яка перебуває в невідповідному стані
    (наприклад, спроба активувати вже активованого користувача).
    Повідомлення для цього винятку зазвичай є специфічним для ситуації і передається при виклику.
    """

    def __init__(self, message: str, detail: Optional[Any] = None, status_code: int = 400):  # 400 Bad Request
        # `message` тут є обов'язковим і кастомним, тому TODO i18n застосовується в місці виклику.
        super().__init__(message=message, status_code=status_code, detail=detail)


class ExternalServiceException(AppException):
    """Викликається, коли виникає помилка під час взаємодії з зовнішнім сервісом (наприклад, платіжна система, поштовий сервіс)."""

    def __init__(self, service_name: str, message: str = "Помилка при взаємодії із зовнішнім сервісом.",
                 detail: Optional[Any] = None, status_code: int = 503):
        # TODO i18n: Translatable default message format
        full_message = f"{message} (Сервіс: {service_name})"
        super().__init__(message=full_message, status_code=status_code, detail=detail)  # 503 Service Unavailable
        self.service_name = service_name


class RateLimitExceededException(AppException):
    """Викликається, коли користувач перевищує встановлений ліміт запитів до API."""

    def __init__(self, message: str = "Ліміт запитів перевищено. Будь ласка, спробуйте пізніше.",
                 detail: Optional[Any] = None, status_code: int = 429):  # 429 Too Many Requests
        # TODO i18n: Translatable default message
        super().__init__(message=message, status_code=status_code, detail=detail)


class FileProcessingException(AppException):
    """Викликається при помилках, пов'язаних із завантаженням, обробкою або збереженням файлів."""

    def __init__(self, message: str = "Помилка обробки файлу.", detail: Optional[Any] = None,
                 status_code: int = 400):  # Може бути 400 або 422
        # TODO i18n: Translatable default message
        super().__init__(message=message, status_code=status_code, detail=detail)


class InvalidTokenTypeError(ValueError):
    """Кастомна помилка для невірного типу токена."""
    # Цей виняток успадковується від ValueError, оскільки він сигналізує про невідповідне значення
    # для типу токена, що очікується. Можна також успадкувати від AuthenticationException,
    # якщо це завжди пов'язано з помилкою автентифікації.
    # Поки що залишимо ValueError, якщо він використовується для перевірки типів токенів
    # в більш загальному контексті, не тільки автентифікації.
    # Якщо він використовується виключно в TokenService для перевірки access/refresh,
    # то краще було б AuthenticationException. Згідно завдання, це ValueError.
    pass


class InsufficientFundsError(ValueError):
    """Помилка недостатньо коштів на рахунку."""
    def __init__(self, message: str = "Недостатньо коштів на рахунку", current_balance: Optional[Decimal] = None): # i18n
        self.current_balance = current_balance
        super().__init__(message)


class RewardUnavailableError(ValueError):
    """Помилка, що нагорода недоступна (наприклад, закінчилася кількість)."""
    pass


class RedemptionConditionError(ValueError):
    """Помилка, що умови для отримання нагороди не виконані."""
    pass


# Закоментований приклад ServiceException. Наразі AppException достатньо гнучкий.
# class ServiceException(AppException):
#     """Базовий виняток для специфічних помилок сервісного шару, якщо буде потрібна така гранулярність."""
#     def __init__(self, message: str, detail: Optional[Any] = None, status_code: int = 500):
#         super().__init__(message, status_code=status_code, detail=detail)


# Блок для демонстрації та базового тестування винятків при прямому запуску модуля.
if __name__ == "__main__":
    logger.info("--- Демонстрація Кастомних Винятків Ядра ---")


    def demonstrate_exception(exc_class, *args, **kwargs):
        """Допоміжна функція для демонстрації перехоплення та виводу винятків."""
        try:
            raise exc_class(*args, **kwargs)
        except AppException as e:
            logger.info(f"\nПерехоплено виняток: {e}")
            # Демонстрація доступу до специфічних атрибутів, якщо вони є
            if hasattr(e, 'entity_name') and hasattr(e, 'identifier'):
                logger.info(f"  Деталі сутності: Ім'я='{e.entity_name}', Ідентифікатор='{e.identifier}'")
            if hasattr(e, 'errors') and e.errors:
                logger.info(f"  Помилки валідації: {e.errors}")
            if hasattr(e, 'service_name'):
                logger.info(f"  Назва зовнішнього сервісу: {e.service_name}")


    # Демонстрація кожного типу винятку
    demonstrate_exception(AppException, "Сталася загальна непередбачена помилка програми.", status_code=500)
    demonstrate_exception(RecordNotFoundException, "Користувач", 12345)
    demonstrate_exception(RecordNotFoundException, "Замовлення", "XYZ-789",
                          message="Спеціальне повідомлення: Замовлення XYZ-789 не може бути знайдене.")
    demonstrate_exception(DuplicateRecordException, "Адреса електронної пошти", "duplicate@example.com")
    demonstrate_exception(AuthenticationException, "Надано недійсний або прострочений API ключ.")
    demonstrate_exception(AuthorizationException, "Користувач не має прав на видалення цього коментаря.")

    # Приклад для ValidationException
    validation_errors_payload = [
        {"loc": ("body", "email"), "msg": "Значення не є дійсною адресою електронної пошти.",
         "type": "value_error.email"},
        {"loc": ("body", "age"), "msg": "Значення має бути більше або дорівнювати 18.",
         "type": "value_error.greater_than_equal", "ctx": {"limit_value": 18}}
    ]
    demonstrate_exception(ValidationException, "Надані дані для створення профілю не пройшли валідацію.",
                          errors=validation_errors_payload)
    demonstrate_exception(ValidationException, "Помилка валідації.",
                          detail={"field_x": "Некоректне значення для поля X."})

    demonstrate_exception(BusinessLogicException, "Неможливо виконати операцію: баланс користувача недостатній.")
    demonstrate_exception(ExternalServiceException, "СервісПогоди",
                          "Не вдалося отримати дані про погоду: перевищено час очікування.")
    demonstrate_exception(RateLimitExceededException, "Ви перевищили ліміт запитів для цього ендпоінту.")
    demonstrate_exception(FileProcessingException,
                          "Завантажений файл має непідтримуваний формат. Дозволені формати: JPG, PNG.")
    demonstrate_exception(InvalidTokenTypeError, "Надано невірний тип токена. Очікувався 'access_token'.")
    demonstrate_exception(InsufficientFundsError, "На рахунку недостатньо коштів для виконання операції.", current_balance=Decimal("10.50"))
    demonstrate_exception(RewardUnavailableError, "Вибрана нагорода наразі недоступна.")
    demonstrate_exception(RedemptionConditionError, "Умови для отримання цієї нагороди не виконані.")

    # Приклад імітації HTTP-відповіді на основі винятку
    logger.info("\n--- Імітація HTTP-Відповіді на Основі Винятку ---")
    try:
        # Припустимо, ця дія вимагає прав адміністратора, але користувач їх не має
        raise AuthorizationException(detail="Для доступу до цього ресурсу потрібні права адміністратора.")
    except AppException as e:
        # У реальному FastAPI додатку це оброблялося б декоратором @app.exception_handler(AppException)
        http_response_status_code = e.status_code
        http_response_body = {"message": e.detail}  # Використовуємо e.detail для клієнта

        logger.info(f"Імітована HTTP-відповідь:")
        logger.info(f"  Статус-код: {http_response_status_code}")
        logger.info(f"  Тіло відповіді (JSON): {http_response_body}")
