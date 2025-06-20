# backend/app/src/core/validators.py
"""
Модуль кастомних функцій-валідаторів для програми Kudos.

Цей модуль містить набір багаторазових функцій для перевірки коректності даних.
Валідатори можуть використовуватися в різних частинах програми, зокрема
в Pydantic моделях для валідації полів, або безпосередньо в сервісах чи обробниках запитів.

Кожна функція-валідатор викликає `ValidationException` у разі невдалої перевірки,
надаючи деталізовану інформацію про помилку, включаючи поле, повідомлення та тип помилки.
"""

import re
from typing import Any, Optional, List
# TODO: Додати 'phonenumbers' до файлу requirements.txt або pyproject.toml
import phonenumbers # Розкоментуйте, коли бібліотека буде додана до залежностей
from phonenumbers import phonenumberutil # Розкоментуйте для використання винятків phonenumbers

# Абсолютні імпорти з проекту
from backend.app.src.core.exceptions import ValidationException
from backend.app.src.core.constants import PASSWORD_REGEX, USERNAME_REGEX
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)


# from backend.app.src.config.logging import get_logger # Якщо потрібне логування

# logger = get_logger(__name__), якщо потрібен

# --- Валідатори для рядкових значень ---

def validate_not_empty(value: Optional[str], field_name: str) -> str:
    """
    Перевіряє, що рядкове значення не є `None` і не є порожнім або складається лише з пробілів.

    Args:
        value (Optional[str]): Рядкове значення для перевірки.
        field_name (str): Назва поля, що валідується (для повідомлення про помилку).

    Returns:
        str: Оригінальне значення, якщо воно пройшло валідацію.

    Raises:
        ValidationException: Якщо значення є `None`, порожнім або містить лише пробіли.
    """
    if value is None or not value.strip():
        raise ValidationException(
            message=_("validators.field_cannot_be_empty_log", field_name=field_name),
            errors=[{
                "loc": (field_name,),
                "msg": _("validators.field_required_no_spaces"),
                "type": "value_error.missing_or_empty"
            }]
        )
    return value


def validate_max_length(value: str, max_len: int, field_name: str) -> str:
    """
    Перевіряє, що довжина рядкового значення не перевищує вказану максимальну довжину.

    Args:
        value (str): Рядкове значення для перевірки.
        max_len (int): Максимально дозволена довжина рядка.
        field_name (str): Назва поля, що валідується.

    Returns:
        str: Оригінальне значення, якщо його довжина не перевищує `max_len`.

    Raises:
        ValidationException: Якщо довжина значення перевищує `max_len`.
    """
    if len(value) > max_len:
        raise ValidationException(
            message=_("validators.field_length_exceeds_max_log", field_name=field_name, max_len=max_len),
            errors=[{
                "loc": (field_name,),
                "msg": _("validators.max_length_is_provided_len", max_len=max_len, current_len=len(value)),
                "type": "value_error.string.max_length"
            }]
        )
    return value


def validate_min_length(value: str, min_len: int, field_name: str) -> str:
    """
    Перевіряє, що рядкове значення має щонайменше вказану мінімальну довжину.

    Args:
        value (str): Рядкове значення для перевірки.
        min_len (int): Мінімально дозволена довжина рядка.
        field_name (str): Назва поля, що валідується.

    Returns:
        str: Оригінальне значення, якщо його довжина не менша за `min_len`.

    Raises:
        ValidationException: Якщо довжина значення менша за `min_len`.
    """
    if len(value) < min_len:
        raise ValidationException(
            message=_("validators.field_length_less_than_min_log", field_name=field_name, min_len=min_len),
            errors=[{
                "loc": (field_name,),
                "msg": _("validators.min_length_is_provided_len", min_len=min_len, current_len=len(value)),
                "type": "value_error.string.min_length"
            }]
        )
    return value


def validate_allowed_characters(value: str, pattern: str, field_name: str, error_message: Optional[str] = None) -> str:
    """
    Перевіряє, що рядок містить лише символи, дозволені вказаним регулярним виразом.

    Args:
        value (str): Рядкове значення для перевірки.
        pattern (str): Регулярний вираз для перевірки відповідності.
        field_name (str): Назва поля, що валідується.
        error_message (Optional[str]): Кастомне повідомлення про помилку. Якщо `None`,
                                       використовується повідомлення за замовчуванням.
                                       Очікується, що error_message вже перекладено, якщо надано.

    Returns:
        str: Оригінальне значення, якщо воно відповідає шаблону.

    Raises:
        ValidationException: Якщо значення не відповідає регулярному виразу.
    """
    if not re.fullmatch(pattern, value):
        default_log_msg = _("validators.field_contains_invalid_chars_log", field_name=field_name)
        final_user_msg = error_message or _("validators.value_does_not_match_format")
        raise ValidationException(
            message=error_message or default_log_msg,
            errors=[{
                "loc": (field_name,),
                "msg": final_user_msg,
                "type": "value_error.string.pattern_mismatch",
                "ctx": {"pattern": pattern}
            }]
        )
    return value


# --- Валідатори для специфічних форматів даних ---

def validate_username_format(username: str) -> str:
    """
    Перевіряє формат імені користувача на основі регулярного виразу `USERNAME_REGEX`
    з модуля `core.constants`.
    """
    try:
        return validate_allowed_characters(
            username, USERNAME_REGEX, _("validators.fieldnames.username"), # "ім'я користувача"
            error_message=_("validators.username_format_requirements")
        )
    except ValidationException as e:
        if e.errors and isinstance(e.errors, list) and e.errors[0]:
            e.errors[0]["type"] = "value_error.username.format"
        raise


def validate_password_strength(password: str) -> str:
    """
    Перевіряє надійність пароля на основі регулярного виразу `PASSWORD_REGEX`
    з модуля `core.constants`.
    """
    try:
        return validate_allowed_characters(
            password, PASSWORD_REGEX, _("validators.fieldnames.password"), # "пароль"
            error_message=_("validators.password_strength_requirements")
        )
    except ValidationException as e:
        if e.errors and isinstance(e.errors, list) and e.errors[0]:
            e.errors[0]["type"] = "value_error.password.strength"
        raise


def validate_phone_number(phone_number: str, default_region: Optional[str] = "UA") -> str:
    """
    Перевіряє та форматує міжнародний номер телефону за допомогою бібліотеки `phonenumbers`.
    Повертає номер у форматі E.164, якщо він валідний.

    TODO: Додати `phonenumbers` до файлу `requirements.txt` або `pyproject.toml` проєкту.
          Приклад: `pip install phonenumbers`

    Args:
        phone_number (str): Номер телефону для перевірки.
        default_region (Optional[str]): Код регіону (наприклад, "UA", "PL"), який використовується
                                       для парсингу номерів без міжнародного префікса.
                                       За замовчуванням "UA".

    Returns:
        str: Відформатований номер телефону у стандарті E.164 (наприклад, "+380501234567").

    Raises:
        ValidationException: Якщо номер телефону недійсний або бібліотека `phonenumbers` не встановлена.
    """
    try:
        import phonenumbers
        from phonenumbers import phonenumberutil

        if not phone_number:
            raise ValidationException(
                _("validators.phone.cannot_be_empty_log"),
                errors=[{"loc": ("phone_number",), "msg": _("validators.phone.please_enter_number"),
                         "type": "value_error.phone_number.empty"}]
            )

        parsed_number = phonenumbers.parse(phone_number, region=default_region)
        if not phonenumbers.is_valid_number(parsed_number):
            raise ValidationException(
                _("validators.phone.invalid_number_log"),
                errors=[{"loc": ("phone_number",), "msg": _("validators.phone.invalid_format_or_nonexistent"),
                         "type": "value_error.phone_number.invalid"}]
            )

        formatted_number = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
        logger.info(_("validators.phone.validation_success_log", phone_number=phone_number, region=default_region, formatted_number=formatted_number))
        return formatted_number
    except ImportError:
        logger.error(_("validators.phone.library_not_installed_log"))
        raise ValidationException(
            _("validators.phone.service_unavailable_no_library_log"),
            errors=[{"loc": ("phone_number",),
                     "msg": _("validators.phone.check_failed_no_library_user"),
                     "type": "value_error.phone_number.config_error"}]
        )
    except phonenumberutil.NumberParseException as e:
        logger.warning(_("validators.phone.parse_error_log", phone_number=phone_number, error=str(e)))
        error_key_map = {
            phonenumberutil.NumberParseException.INVALID_COUNTRY_CODE: "validators.phone.parse_errors.invalid_country_code",
            phonenumberutil.NumberParseException.NOT_A_NUMBER: "validators.phone.parse_errors.not_a_number",
            phonenumberutil.NumberParseException.TOO_SHORT_AFTER_IDD: "validators.phone.parse_errors.too_short_after_idd",
            phonenumberutil.NumberParseException.TOO_SHORT_NSN: "validators.phone.parse_errors.too_short_nsn",
            phonenumberutil.NumberParseException.TOO_LONG: "validators.phone.parse_errors.too_long"
        }
        specific_error_msg_key = error_key_map.get(e.error_type, "validators.phone.parse_errors.default_format_error")
        specific_error_msg = _(specific_error_msg_key)

        raise ValidationException(
            _("validators.phone.could_not_parse_user_message", error_details=specific_error_msg),
            errors=[
                {"loc": ("phone_number",), "msg": specific_error_msg, "type": "value_error.phone_number.parse_error"}]
        )


# --- Числові валідатори ---

def validate_positive_number(value: Any, field_name: str) -> Any:
    """
    Перевіряє, що надане значення є числом (int або float) і є строго додатним (> 0).
    """
    if not isinstance(value, (int, float)):
        raise ValidationException(
            message=_("validators.field_must_be_number_log", field_name=field_name),
            errors=[{"loc": (field_name,), "msg": _("validators.value_must_be_numeric"), "type": "type_error.number"}]
        )
    if value <= 0:
        raise ValidationException(
            message=_("validators.field_must_be_positive_log", field_name=field_name),
            errors=[{"loc": (field_name,), "msg": _("validators.value_must_be_greater_than_zero"),
                     "type": "value_error.number.positive"}]
        )
    return value


def validate_number_range(
        value: Any,
        min_val: Optional[Union[int, float]] = None,
        max_val: Optional[Union[int, float]] = None,
        field_name: str = _("validators.fieldnames.default_numeric_field") # "Числове поле"
) -> Any:
    """
    Перевіряє, що числове значення знаходиться у вказаному діапазоні (включно з межами).
    """
    if not isinstance(value, (int, float)):
        raise ValidationException(
            message=_("validators.field_must_be_number_log", field_name=field_name),
            errors=[{"loc": (field_name,), "msg": _("validators.value_must_be_numeric"), "type": "type_error.number"}]
        )
    if min_val is not None and value < min_val:
        raise ValidationException(
            message=_("validators.value_less_than_min_log", field_name=field_name, value=value, min_val=min_val),
            errors=[{"loc": (field_name,), "msg": _("validators.value_must_be_not_less_than", min_val=min_val),
                     "type": "value_error.number.min_value", "ctx": {"limit_value": min_val}}]
        )
    if max_val is not None and value > max_val:
        raise ValidationException(
            message=_("validators.value_exceeds_max_log", field_name=field_name, value=value, max_val=max_val),
            errors=[{"loc": (field_name,), "msg": _("validators.value_must_be_not_greater_than", max_val=max_val),
                     "type": "value_error.number.max_value", "ctx": {"limit_value": max_val}}]
        )
    return value


# --- Валідатори для списків/колекцій ---

def validate_list_not_empty(value: Optional[List[Any]], field_name: str) -> List[Any]:
    """
    Перевіряє, що наданий список не є `None` і містить принаймні один елемент.
    """
    if value is None or not value:
        raise ValidationException(
            message=_("validators.list_cannot_be_empty_log", field_name=field_name),
            errors=[{"loc": (field_name,), "msg": _("validators.list_must_contain_elements"),
                     "type": "value_error.list.not_empty"}]
        )
    return value


# Блок для демонстрації та базового тестування валідаторів при прямому запуску модуля.
if __name__ == "__main__":
    logger.info("--- Демонстрація Основних Функцій-Валідаторів ---")


    # Допоміжна функція для тестування валідаторів
    def test_validator(validator_func: callable, test_value: Any, *args: Any, expected_to_pass: bool = True):
        """Тестує валідатор та виводить результат."""
        # Останній аргумент в args часто є field_name, але не завжди (напр. для username/password)
        field_name_for_log = args[-1] if args and isinstance(args[-1], str) else "значення"
        if validator_func in [validate_username_format, validate_password_strength]:
            field_name_for_log = validator_func.__name__.split("_")[1]  # username або password

        logger.info(f"\nТестування {validator_func.__name__} з '{test_value}' для поля '{field_name_for_log}':")
        try:
            result = validator_func(test_value, *args)
            if expected_to_pass:
                logger.info(f"  \033[92mУСПІХ:\033[0m Валідація пройдена. Результат: '{result}'")
            else:
                logger.info(f"  \033[91mПОМИЛКА ТЕСТУ:\033[0m Валідація неочікувано пройдена. Результат: '{result}'")
        except ValidationException as e:
            if expected_to_pass:
                logger.info(
                    f"  \033[91mПОМИЛКА ТЕСТУ:\033[0m Валідація не пройдена, хоча очікувався успіх. Помилка: {e.message}")
                logger.info(f"    Деталі: {e.errors}")
            else:
                logger.info(f"  \033[92mУСПІХ (очікувана помилка):\033[0m {e.message}")
                logger.info(f"    Деталі: {e.errors}")
        except Exception as e:
            logger.info(f"  \033[91mНЕОЧІКУВАНА ПОМИЛКА:\033[0m {e}")


    # Тестування валідаторів рядків
    test_validator(validate_not_empty, "Привіт Світ", "повідомлення")
    test_validator(validate_not_empty, "  ", "повідомлення", expected_to_pass=False)
    test_validator(validate_not_empty, None, "повідомлення", expected_to_pass=False)

    test_validator(validate_max_length, "коротко", 10, "назва_тегу")
    test_validator(validate_max_length, "дужедовгийтекст", 10, "назва_тегу", expected_to_pass=False)

    test_validator(validate_min_length, "достатньо", 5, "ключ_API")
    test_validator(validate_min_length, "мало", 5, "ключ_API", expected_to_pass=False)

    # Тестування валідаторів специфічних форматів
    test_validator(validate_username_format, "korystuvach_123")
    test_validator(validate_username_format, "sh", expected_to_pass=False)  # Занадто короткий
    test_validator(validate_username_format, "ім'я з пробілом", expected_to_pass=False)  # Пробіл
    test_validator(validate_username_format, "korystuvach!", expected_to_pass=False)  # Недійсний символ

    test_validator(validate_password_strength, "MicNyiP@r0l!")
    test_validator(validate_password_strength, "slabyi", expected_to_pass=False)
    test_validator(validate_password_strength, "BezSpecSymv0liv", expected_to_pass=False)
    test_validator(validate_password_strength, "bezvelykoiliteri1@", expected_to_pass=False)

    logger.info("\nТестування validate_phone_number (з бібліотекою phonenumbers):")
    # TODO: Розкоментуйте та розширте ці тести, коли бібліотека phonenumbers буде встановлена та налаштована.
    # Для запуску цих тестів без встановленої бібліотеки, вони викличуть помилку конфігурації.
    # Якщо ви хочете, щоб вони проходили з базовою логікою (якщо така буде реалізована),
    # то змініть expected_to_pass=False на True для валідних за простою логікою номерів.
    # Наразі, оскільки функція викликає ValidationException при ImportError, всі тести очікують помилку.

    # Приклади для тестування з phonenumbers (розкоментувати, коли бібліотека активна)
    # test_validator(validate_phone_number, "+380501234567", "UA", expected_to_pass=True) # Валідний UA
    # test_validator(validate_phone_number, "0501234567", "UA", expected_to_pass=True)    # Валідний UA без префіксу
    # test_validator(validate_phone_number, "+14155552671", "US", expected_to_pass=True) # Валідний US
    # test_validator(validate_phone_number, "12345", "UA", expected_to_pass=False)        # Невалідний (короткий)
    # test_validator(validate_phone_number, "+38050123456", "UA", expected_to_pass=False) # Невалідний (короткий для UA)
    # test_validator(validate_phone_number, "не номер", "UA", expected_to_pass=False)     # Не номер
    # test_validator(validate_phone_number, "+123", "UA", expected_to_pass=False)           # Недійсний код країни

    # Поточні тести, які очікують помилку через відсутність бібліотеки або невалідний формат базовим regex
    test_validator(validate_phone_number, "+380501234567", "UA", expected_to_pass=False)
    test_validator(validate_phone_number, "не_номер_телефонy", "UA", expected_to_pass=False)

    # Тестування числових валідаторів
    test_validator(validate_positive_number, 15.5, "ціна")
    test_validator(validate_positive_number, 0, "кількість", expected_to_pass=False)
    test_validator(validate_positive_number, -10, "рейтинг", expected_to_pass=False)
    test_validator(validate_positive_number, "нечисло", "сума", expected_to_pass=False)

    test_validator(validate_number_range, 7, 1, 10, "оцінка")
    test_validator(validate_number_range, 0, 1, 10, "оцінка", expected_to_pass=False)  # Менше min_val
    test_validator(validate_number_range, 11, 1, 10, "оцінка", expected_to_pass=False)  # Більше max_val
    test_validator(validate_number_range, 10, None, 10, "верхня_межа")  # max_val включно
    test_validator(validate_number_range, 1, 1, None, "нижня_межа")  # min_val включно

    # Тестування валідаторів списків
    test_validator(validate_list_not_empty, ["яблуко", "банан"], "фрукти")
    test_validator(validate_list_not_empty, [], "теги", expected_to_pass=False)
    test_validator(validate_list_not_empty, None, "категорії", expected_to_pass=False)

    logger.info("\nПримітка: Для використання цих валідаторів у моделях Pydantic, їх зазвичай")
    logger.info("інтегрують за допомогою декоратора `@validator` або `@field_validator`.")
