# backend/app/src/core/exceptions.py
# -*- coding: utf-8 -*-
# # Модуль кастомних винятків для програми Kudos (Virtus).
# #
# # Цей модуль визначає ієрархію спеціалізованих класів винятків, що
# # використовуються в різних частинах програми для обробки помилок.
# # Базовим класом є `AppException`, який розширює стандартний `Exception`
# # атрибутами для HTTP-статус коду та деталей помилки, що полегшує
# # інтеграцію з обробниками винятків FastAPI та повернення змістовних
# # HTTP-відповідей клієнтам.

from typing import Optional, Dict, Any, List

# Імпорт логера з централізованої конфігурації логування
from backend.app.src.config.logging import get_logger

# Отримання логера для цього модуля
logger = get_logger(__name__)


class AppException(Exception):
    """
    Базовий клас для всіх кастомних винятків програми Kudos (Virtus).

    Цей клас успадковується від стандартного `Exception` і додає
    атрибути для HTTP-статус коду та деталей помилки, що полегшує
    інтеграцію з обробниками винятків FastAPI.

    Атрибути:
        message (str): Внутрішнє повідомлення про помилку, призначене для логування
                       або внутрішньої діагностики. Не обов'язково для показу клієнту.
        status_code (int): HTTP-статус код, який повинен повертатися клієнту
                           при виникненні цього винятку. За замовчуванням 500
                           (Внутрішня помилка сервера).
        detail (Optional[Any]): Детальна інформація про помилку, яка може бути безпечно
                                передана клієнту (наприклад, у відповіді API).
                                Якщо не вказано, використовується значення `message`.
    """

    def __init__(self, message: str, status_code: int = 500, detail: Optional[Any] = None):
        super().__init__(message) # Виклик конструктора батьківського класу Exception
        self.message = message
        self.status_code = status_code
        # Якщо `detail` не надано, воно приймає значення `message`.
        # Це спрощує випадки, коли повідомлення для логу та для клієнта однакове.
        self.detail = detail if detail is not None else message

    def __str__(self) -> str:
        """Повертає рядкове представлення винятку для логування або налагодження."""
        return (f"{self.__class__.__name__}(status_code={self.status_code}, "
                f"message='{self.message}', detail='{self.detail}')")


# --- Специфічні винятки програми, що успадковуються від AppException ---

class RecordNotFoundException(AppException):
    """Викликається, коли запитуваний запис (сутність) не знайдено в базі даних."""

    def __init__(self, entity_name: str, identifier: Any, message: Optional[str] = None, detail: Optional[Any] = None):
        # Формуємо повідомлення за замовчуванням, якщо воно не надане явно.
        # TODO i18n: Translatable message format. "Сутність '{entity_name}' ... не знайдено."
        resolved_message = message or f"Сутність '{entity_name}' з ідентифікатором '{identifier}' не знайдено."
        super().__init__(message=resolved_message, status_code=404, detail=detail) # HTTP 404 Not Found
        self.entity_name = entity_name  # Назва сутності (наприклад, "Користувач", "Завдання")
        self.identifier = identifier  # Ідентифікатор, за яким шукали сутність (наприклад, ID, email)


class DuplicateRecordException(AppException):
    """Викликається при спробі створити запис, який порушує обмеження унікальності (наприклад, дублікат email)."""

    def __init__(self, entity_name: str, identifier_field: str, identifier_value: Any, message: Optional[str] = None, detail: Optional[Any] = None):
        # TODO i18n: Translatable message format. "Сутність '{entity_name}' з '{identifier_field}' = '{identifier_value}' вже існує."
        resolved_message = message or f"Сутність '{entity_name}' з унікальним полем '{identifier_field}' зі значенням '{identifier_value}' вже існує."
        super().__init__(message=resolved_message, status_code=409, detail=detail)  # HTTP 409 Conflict
        self.entity_name = entity_name
        self.identifier_field = identifier_field # Назва унікального поля
        self.identifier_value = identifier_value # Значення поля, що спричинило конфлікт


class AuthenticationException(AppException):
    """Викликається при помилках автентифікації (наприклад, недійсні облікові дані, невалідний або прострочений токен)."""

    def __init__(self, message: str = "Помилка автентифікації.", detail: Optional[Any] = None, status_code: int = 401):
        # TODO i18n: Translatable default message. "Помилка автентифікації."
        super().__init__(message=message, status_code=status_code, detail=detail) # HTTP 401 Unauthorized


class AuthorizationException(AppException):
    """Викликається, коли автентифікований користувач не має достатньо прав для виконання певної дії."""

    def __init__(self, message: str = "Недостатньо прав для виконання цієї дії.", detail: Optional[Any] = None,
                 status_code: int = 403):
        # TODO i18n: Translatable default message. "Недостатньо прав для виконання цієї дії."
        super().__init__(message=message, status_code=status_code, detail=detail) # HTTP 403 Forbidden


class ValidationException(AppException):
    """
    Викликається, коли вхідні дані не проходять валідацію (наприклад, помилки валідації схем Pydantic).

    Атрибут `errors` може містити структурований список помилок валідації,
    подібний до формату помилок Pydantic, для надання детального фідбеку клієнту.
    Самі повідомлення в `errors` (ключ 'msg') також потребуватимуть перекладу, якщо вони є фіксованими рядками
    або генеруються бібліотеками без підтримки i18n.
    """

    def __init__(self, message: str = "Помилка валідації вхідних даних.", errors: Optional[List[Dict[str, Any]]] = None,
                 detail: Optional[Any] = None):
        # TODO i18n: Translatable default message. "Помилка валідації вхідних даних."
        # Якщо `detail` не надано, а `errors` є, можна сформувати `detail` з `errors` або використати загальне `message`.
        effective_detail = detail if detail is not None else (errors if errors else message)
        super().__init__(message=message, status_code=422, detail=effective_detail)  # HTTP 422 Unprocessable Entity
        self.errors = errors  # Список словників з деталями помилок валідації (наприклад, від Pydantic)


class BusinessLogicException(AppException):
    """
    Викликається для загальних помилок бізнес-логіки, які не підпадають під інші специфічні категорії винятків.
    Наприклад, спроба виконати операцію над сутністю, яка перебуває в невідповідному стані
    (наприклад, спроба активувати вже активованого користувача).
    Повідомлення для цього винятку зазвичай є специфічним для конкретної ситуації і передається при створенні винятку.
    """

    def __init__(self, message: str, detail: Optional[Any] = None, status_code: int = 400):  # HTTP 400 Bad Request
        # `message` тут є обов'язковим і кастомним, тому TODO i18n для нього застосовується в місці виклику цього винятку.
        super().__init__(message=message, status_code=status_code, detail=detail)


class ExternalServiceException(AppException):
    """Викликається, коли виникає помилка під час взаємодії з зовнішнім сервісом (наприклад, платіжна система, поштовий сервіс, стороннє API)."""

    def __init__(self, service_name: str, message: str = "Помилка при взаємодії із зовнішнім сервісом.",
                 detail: Optional[Any] = None, status_code: int = 503): # HTTP 503 Service Unavailable
        # TODO i18n: Translatable default message format. "Помилка при взаємодії із зовнішнім сервісом. (Сервіс: {service_name})"
        full_message = f"{message} (Сервіс: {service_name})"
        super().__init__(message=full_message, status_code=status_code, detail=detail)
        self.service_name = service_name


class RateLimitExceededException(AppException):
    """Викликається, коли користувач перевищує встановлений ліміт запитів до API (rate limiting)."""

    def __init__(self, message: str = "Ліміт запитів перевищено. Будь ласка, спробуйте пізніше.",
                 detail: Optional[Any] = None, status_code: int = 429):  # HTTP 429 Too Many Requests
        # TODO i18n: Translatable default message. "Ліміт запитів перевищено. Будь ласка, спробуйте пізніше."
        super().__init__(message=message, status_code=status_code, detail=detail)


class FileProcessingException(AppException):
    """Викликається при помилках, пов'язаних із завантаженням, обробкою або збереженням файлів."""

    def __init__(self, message: str = "Помилка обробки файлу.", detail: Optional[Any] = None,
                 status_code: int = 400):  # Може бути 400 Bad Request або 422 Unprocessable Entity залежно від контексту
        # TODO i18n: Translatable default message. "Помилка обробки файлу."
        super().__init__(message=message, status_code=status_code, detail=detail)


# Блок для демонстрації та базового тестування винятків при прямому запуску модуля.
if __name__ == "__main__":
    # Налаштування логування для тестування, якщо воно ще не налаштоване глобально
    try:
        from backend.app.src.config.logging import setup_logging
        from backend.app.src.config.settings import settings # Потрібно для шляхів логів
        from pathlib import Path
        if settings.LOG_TO_FILE:
            log_file_path = settings.LOG_DIR / f"{Path(__file__).stem}_test.log"
            setup_logging(log_file_path=log_file_path)
        else:
            setup_logging()
        logger.info("Логування налаштовано для тестування exceptions.py.")
    except ImportError:
        import logging as base_logging
        base_logging.basicConfig(level=logging.INFO)
        logger.warning("Не вдалося імпортувати setup_logging. Використовується базова конфігурація логування для тестів exceptions.py.")

    logger.info("--- Демонстрація Кастомних Винятків Ядра (`core.exceptions`) ---")

    def demonstrate_exception(exc_class, *args, **kwargs):
        """Допоміжна функція для демонстрації перехоплення та виводу інформації про винятки."""
        exception_name = exc_class.__name__
        logger.info(f"\n--- Тестування: {exception_name} ---")
        try:
            raise exc_class(*args, **kwargs)
        except AppException as e:
            logger.info(f"Перехоплено виняток: {e}") # Використовує e.__str__()
            logger.info(f"  Тип винятку: {type(e).__name__}")
            logger.info(f"  Повідомлення (message): {e.message}")
            logger.info(f"  Деталі для клієнта (detail): {e.detail}")
            logger.info(f"  HTTP статус-код: {e.status_code}")

            # Демонстрація доступу до специфічних атрибутів, якщо вони є
            if hasattr(e, 'entity_name'): # Для RecordNotFoundException, DuplicateRecordException
                logger.info(f"  Назва сутності: {e.entity_name}")
            if hasattr(e, 'identifier'): # Для RecordNotFoundException
                logger.info(f"  Ідентифікатор сутності: {e.identifier}")
            if hasattr(e, 'identifier_field') and hasattr(e, 'identifier_value'): # Для DuplicateRecordException
                logger.info(f"  Поле конфлікту: {e.identifier_field} = {e.identifier_value}")
            if hasattr(e, 'errors') and e.errors: # Для ValidationException
                logger.info(f"  Список помилок валідації: {e.errors}")
            if hasattr(e, 'service_name'): # Для ExternalServiceException
                logger.info(f"  Назва зовнішнього сервісу: {e.service_name}")
        except Exception as e_general: # Якщо раптом виняток не є AppException
            logger.error(f"Перехоплено не AppException: {type(e_general).__name__} - {e_general}", exc_info=True)


    # Демонстрація кожного типу винятку
    demonstrate_exception(AppException, "Сталася загальна непередбачена помилка програми.", status_code=500, detail="Зверніться до системного адміністратора.")
    demonstrate_exception(RecordNotFoundException, entity_name="Користувач", identifier=12345)
    demonstrate_exception(RecordNotFoundException, entity_name="Замовлення", identifier="XYZ-789",
                          message="Спеціальне повідомлення: Замовлення XYZ-789 не може бути знайдене в архіві.",
                          detail="Замовлення XYZ-789 не знайдено. Перевірте номер або зверніться до підтримки.")
    demonstrate_exception(DuplicateRecordException, entity_name="Адреса електронної пошти",
                          identifier_field="email", identifier_value="duplicate@example.com")
    demonstrate_exception(AuthenticationException, "Надано недійсний або прострочений API ключ.",
                          detail="API ключ невалідний. Будь ласка, перевірте ваш ключ та спробуйте знову.")
    demonstrate_exception(AuthorizationException, "Користувач не має прав на видалення цього коментаря.",
                          detail="Дія заборонена: недостатньо прав.")

    # Приклад для ValidationException
    validation_errors_payload = [
        {"loc": ("body", "email"), "msg": "Значення не є дійсною адресою електронної пошти.",
         "type": "value_error.email"},
        {"loc": ("body", "age"), "msg": "Значення має бути більше або дорівнювати 18.",
         "type": "value_error.greater_than_equal", "ctx": {"limit_value": 18}}
    ]
    demonstrate_exception(ValidationException, "Надані дані для створення профілю не пройшли валідацію.",
                          errors=validation_errors_payload) # detail буде автоматично errors
    demonstrate_exception(ValidationException, "Помилка валідації.",
                          detail={"field_x": "Некоректне значення для поля X."}) # Явно переданий detail

    demonstrate_exception(BusinessLogicException, "Неможливо виконати операцію: баланс користувача недостатній.",
                          detail="Операція відхилена через недостатній баланс.")
    demonstrate_exception(ExternalServiceException, service_name="ПлатіжнийШлюз 'SecurePay'",
                          message="Помилка обробки платежу.",
                          detail="Не вдалося обробити платіж через технічну помилку на стороні платіжного шлюзу SecurePay.")
    demonstrate_exception(RateLimitExceededException, "Ви перевищили ліміт запитів для цього ендпоінту (3 запити на хвилину).",
                          detail={"retry_after": 60}) # Приклад з додатковою інформацією
    demonstrate_exception(FileProcessingException,
                          "Завантажений файл має непідтримуваний формат. Дозволені формати: JPG, PNG.",
                          detail="Дозволені типи файлів: image/jpeg, image/png.")

    # Приклад імітації HTTP-відповіді на основі винятку (як це міг би робити FastAPI exception_handler)
    logger.info("\n--- Імітація HTTP-Відповіді на Основі Винятку ---")
    try:
        # Припустимо, ця дія вимагає прав адміністратора, але користувач їх не має
        raise AuthorizationException(detail="Для доступу до цього ресурсу потрібні права адміністратора.")
    except AppException as e:
        # У реальному FastAPI додатку це оброблялося б декоратором @app.exception_handler(AppException)
        # або глобальним обробником винятків.
        http_response_status_code = e.status_code
        # Для клієнта зазвичай використовується `e.detail`.
        # `e.message` може містити більш технічну інформацію для логів.
        http_response_body = {"detail": e.detail}

        logger.info("Імітована HTTP-відповідь:")
        logger.info(f"  Статус-код: {http_response_status_code}")
        logger.info(f"  Тіло відповіді (JSON): {http_response_body}")

    logger.info("\nДемонстрація кастомних винятків завершена.")
