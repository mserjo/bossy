# backend/app/src/core/exceptions.py

"""
Цей модуль визначає власні класи винятків для програми.
Ці винятки можуть бути викликані сервісами або іншими частинами програми
і потім оброблені обробниками винятків FastAPI для повернення відповідних HTTP-відповідей.
"""

from typing import Optional, Dict, Any, List

class AppException(Exception):
    """
    Базовий клас для власних винятків програми.

    Attributes:
        message (str): Повідомлення про помилку, пов'язане з винятком.
        status_code (int): HTTP-код стану, який повертається клієнту.
        detail (Optional[Any]): Додаткові деталі або структурована інформація про помилку.
    """
    def __init__(self, message: str, status_code: int = 500, detail: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.detail = detail if detail is not None else message

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(status_code={self.status_code}, message='{self.message}', detail='{self.detail}')"

# --- Специфічні винятки програми ---

class RecordNotFoundException(AppException):
    """Викликається, коли запитуваний запис не знайдено в базі даних."""
    def __init__(self, entity_name: str, identifier: Any, message: Optional[str] = None, detail: Optional[Any] = None):
        resolved_message = message or f"Сутність '{entity_name}' з ідентифікатором '{identifier}' не знайдено."
        super().__init__(message=resolved_message, status_code=404, detail=detail)
        self.entity_name = entity_name
        self.identifier = identifier

class DuplicateRecordException(AppException):
    """Викликається при спробі створити запис, який вже існує (порушує унікальність)."""
    def __init__(self, entity_name: str, identifier: Any, message: Optional[str] = None, detail: Optional[Any] = None):
        resolved_message = message or f"Сутність '{entity_name}' з ідентифікатором '{identifier}' вже існує."
        super().__init__(message=resolved_message, status_code=409, detail=detail) # 409 Конфлікт
        self.entity_name = entity_name
        self.identifier = identifier

class AuthenticationException(AppException):
    """Викликається при помилках автентифікації (наприклад, недійсні облікові дані, поганий токен)."""
    def __init__(self, message: str = "Автентифікація не вдалася.", detail: Optional[Any] = None, status_code: int = 401):
        super().__init__(message=message, status_code=status_code, detail=detail)

class AuthorizationException(AppException):
    """Викликається, коли автентифікований користувач не авторизований для виконання дії."""
    def __init__(self, message: str = "Ви не авторизовані для виконання цієї дії.", detail: Optional[Any] = None, status_code: int = 403):
        super().__init__(message=message, status_code=status_code, detail=detail)

class ValidationException(AppException):
    """
    Викликається, коли вхідні дані не проходять перевірку валідації (наприклад, помилки валідації Pydantic).
    Атрибут `errors` може містити детальну інформацію про помилки валідації.
    """
    def __init__(self, message: str = "Перевірка вхідних даних не вдалася.", errors: Optional[List[Dict[str, Any]]] = None, detail: Optional[Any] = None):
        super().__init__(message=message, status_code=422, detail=detail) # 422 Необроблювана сутність
        self.errors = errors # Список словників помилок, подібних до Pydantic

class BusinessLogicException(AppException):
    """
    Викликається для загальних помилок бізнес-логіки, які не підпадають під інші категорії.
    Наприклад, спроба виконати дію над сутністю в недійсному стані.
    """
    def __init__(self, message: str, detail: Optional[Any] = None, status_code: int = 400):
        super().__init__(message=message, status_code=status_code, detail=detail)

class ExternalServiceException(AppException):
    """Викликається, коли виникає помилка під час взаємодії із зовнішнім сервісом."""
    def __init__(self, service_name: str, message: str = "Помилка взаємодії із зовнішнім сервісом.", detail: Optional[Any] = None, status_code: int = 503):
        full_message = f"{message} (Сервіс: {service_name})"
        super().__init__(message=full_message, status_code=status_code, detail=detail) # 503 Сервіс недоступний
        self.service_name = service_name

class RateLimitExceededException(AppException):
    """Викликається, коли користувач перевищує ліміт запитів."""
    def __init__(self, message: str = "Ліміт запитів перевищено. Будь ласка, спробуйте пізніше.", detail: Optional[Any] = None, status_code: int = 429):
        super().__init__(message=message, status_code=status_code, detail=detail) # 429 Забагато запитів

class FileProcessingException(AppException):
    """Викликається при помилках під час завантаження або обробки файлів."""
    def __init__(self, message: str = "Помилка обробки файлу.", detail: Optional[Any] = None, status_code: int = 400):
        super().__init__(message=message, status_code=status_code, detail=detail)

# Гарною практикою є мати загальний ServiceException, якщо у вас є чітка концепція сервісного шару
# class ServiceException(AppException):
#     """Базовий виняток для специфічних помилок сервісного шару."""
#     def __init__(self, message: str, detail: Optional[Any] = None, status_code: int = 500):
#         super().__init__(message, status_code=status_code, detail=detail)


if __name__ == "__main__":
    print("--- Власні винятки ядра ---")

    def demonstrate_exception(exc_class, *args, **kwargs):
        try:
            raise exc_class(*args, **kwargs)
        except AppException as e:
            print(f"Перехоплено: {e}")
            if hasattr(e, 'entity_name'):
                print(f"  Сутність: {e.entity_name}, Ідентифікатор: {e.identifier}")
            if hasattr(e, 'errors') and e.errors:
                print(f"  Помилки: {e.errors}")
            if hasattr(e, 'service_name'):
                print(f"  Назва сервісу: {e.service_name}")

    demonstrate_exception(AppException, "Сталася загальна помилка програми.")
    demonstrate_exception(RecordNotFoundException, "Користувач", "123")
    demonstrate_exception(RecordNotFoundException, "Продукт", "xyz", message="Спеціальне повідомлення: Продукт xyz недоступний.")
    demonstrate_exception(DuplicateRecordException, "Електронна пошта", "test@example.com")
    demonstrate_exception(AuthenticationException, "Надано недійсний API ключ.")
    demonstrate_exception(AuthorizationException, "Користувач не має дозволу на видалення цього ресурсу.")

    validation_errors_example = [
        {"loc": ("body", "email"), "msg": "значення не є дійсною адресою електронної пошти", "type": "value_error.email"},
        {"loc": ("body", "password"), "msg": "переконайтеся, що це значення має принаймні 8 символів", "type": "value_error.too_short"}
    ]
    demonstrate_exception(ValidationException, "Дані реєстрації користувача недійсні.", errors=validation_errors_example)
    demonstrate_exception(ValidationException, detail={"field": "custom_error_detail"})

    demonstrate_exception(BusinessLogicException, "Неможливо деактивувати обліковий запис з непогашеним балансом.")
    demonstrate_exception(ExternalServiceException, "ПлатіжнийШлюз", "Час очікування транзакції минув.")
    demonstrate_exception(RateLimitExceededException)
    demonstrate_exception(FileProcessingException, "Тип завантаженого файлу не підтримується.")

    # Приклад того, як status_code може використовуватися в контексті веб-фреймворку
    try:
        raise AuthorizationException()
    except AppException as e:
        http_response_status = e.status_code
        http_response_body = {"error": e.message, "detail": e.detail}
        print(f"\nІмітація HTTP-відповіді:")
        print(f"  Статус: {http_response_status}")
        print(f"  Тіло: {http_response_body}")
