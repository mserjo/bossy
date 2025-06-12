# backend/app/src/core/validators.py
# -*- coding: utf-8 -*-
# # Модуль кастомних функцій-валідаторів для програми Kudos (Virtus).
# #
# # Цей модуль містить набір багаторазових функцій для перевірки коректності даних.
# # Валідатори можуть використовуватися в різних частинах програми, зокрема
# # в Pydantic моделях (через `@field_validator`) для валідації полів,
# # або безпосередньо в сервісах чи обробниках запитів. У разі невдалої
# # перевірки, валідатори зазвичай викликають `ValidationException`
# # з деталізованою інформацією про помилку.

import re
from typing import Any, Optional, List, Union # Додано Union для validate_number_range

# Імпорт phonenumbers є опціональним і обробляється через try-except,
# щоб модуль можна було імпортувати навіть без встановленої бібліотеки.
try:
    import phonenumbers
    from phonenumbers import phonenumberutil
    PHONENUMBERS_LIB_AVAILABLE = True
except ImportError:
    PHONENUMBERS_LIB_AVAILABLE = False
    # Далі в коді буде перевірка PHONENUMBERS_LIB_AVAILABLE

# Абсолютні імпорти з проекту
from backend.app.src.core.exceptions import ValidationException
from backend.app.src.core.constants import PASSWORD_REGEX, USERNAME_REGEX
from backend.app.src.config.logging import get_logger

# Отримання логера для цього модуля
logger = get_logger(__name__)


# --- Валідатори для рядкових значень ---

def validate_not_empty(value: Optional[str], field_name: str) -> str:
    """
    Перевіряє, що рядкове значення не є `None` і не є порожнім або складається лише з пробілів.

    Args:
        value (Optional[str]): Рядкове значення для перевірки.
        field_name (str): Назва поля, що валідується (використовується в повідомленні про помилку).

    Returns:
        str: Оригінальне значення, якщо воно пройшло валідацію.

    Raises:
        ValidationException: Якщо значення є `None`, порожнім або містить лише пробіли.
    """
    if value is None or not value.strip():
        # TODO i18n: Translatable message for `message` (internal log/debug)
        # TODO i18n: Translatable message for `errors[0].msg` (user-facing)
        raise ValidationException(
            message=f"Поле '{field_name}' не може бути порожнім або складатися лише з пробілів.",
            errors=[{
                "loc": (field_name,),
                "msg": "Це поле є обов'язковим і не може бути порожнім.",
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
        # TODO i18n: Translatable message for `message` (internal log/debug)
        # TODO i18n: Translatable message for `errors[0].msg` (user-facing)
        message = f"Довжина поля '{field_name}' ({len(value)}) перевищує максимально допустиму ({max_len} символів)."
        errors = [{
            "loc": (field_name,),
            "msg": f"Максимальна довжина становить {max_len} символів. Надано {len(value)}.",
            "type": "value_error.string.max_length",
            "ctx": {"limit_value": max_len, "actual_length": len(value)}
        }]
        raise ValidationException(message=message, errors=errors)
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
        # TODO i18n: Translatable message for `message` (internal log/debug)
        # TODO i18n: Translatable message for `errors[0].msg` (user-facing)
        message = f"Довжина поля '{field_name}' ({len(value)}) менша за мінімально допустиму ({min_len} символів)."
        errors = [{
            "loc": (field_name,),
            "msg": f"Мінімальна довжина становить {min_len} символів. Надано {len(value)}.",
            "type": "value_error.string.min_length",
            "ctx": {"limit_value": min_len, "actual_length": len(value)}
        }]
        raise ValidationException(message=message, errors=errors)
    return value


def validate_allowed_characters(value: str, pattern: str, field_name: str, error_message_user: Optional[str] = None) -> str:
    """
    Перевіряє, що рядок містить лише символи, дозволені вказаним регулярним виразом.

    Args:
        value (str): Рядкове значення для перевірки.
        pattern (str): Регулярний вираз для перевірки відповідності (має відповідати повному рядку).
        field_name (str): Назва поля, що валідується (для внутрішніх повідомлень та `loc`).
        error_message_user (Optional[str]): Кастомне повідомлення про помилку для користувача.
                                           Якщо `None`, використовується повідомлення за замовчуванням.

    Returns:
        str: Оригінальне значення, якщо воно відповідає шаблону.

    Raises:
        ValidationException: Якщо значення не відповідає регулярному виразу.
    """
    if not re.fullmatch(pattern, value):
        # TODO i18n: Translatable default for `error_message_user`
        final_user_msg = error_message_user or "Значення містить недійсні символи або не відповідає дозволеному формату."
        # Внутрішнє повідомлення може бути більш детальним
        internal_message = f"Поле '{field_name}' містить недійсні символи або не відповідає шаблону '{pattern}'."
        raise ValidationException(
            message=internal_message,
            errors=[{
                "loc": (field_name,),
                "msg": final_user_msg,
                "type": "value_error.string.pattern_mismatch",
                "ctx": {"pattern": pattern} # pattern для контексту, не обов'язково для прямого показу користувачу
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
        # TODO i18n: Translatable `error_message_user`
        return validate_allowed_characters(
            username, USERNAME_REGEX, "username", # `field_name` тут "username" для `loc`
            error_message_user="Ім'я користувача повинно містити від 3 до 20 символів і може складатися лише з латинських літер, цифр, знаків підкреслення (_) та дефісів (-)."
        )
    except ValidationException as e:
        # Перевизначаємо тип помилки для більшої специфічності, якщо потрібно
        if e.errors and isinstance(e.errors, list) and e.errors[0]:
            e.errors[0]["type"] = "value_error.username.format"
        raise


def validate_password_strength(password: str) -> str:
    """
    Перевіряє надійність пароля на основі регулярного виразу `PASSWORD_REGEX`
    з модуля `core.constants`.
    """
    try:
        # TODO i18n: Translatable `error_message_user`
        return validate_allowed_characters(
            password, PASSWORD_REGEX, "password", # `field_name` тут "password" для `loc`
            error_message_user=(
                "Пароль повинен мати довжину від 8 до 128 символів і містити принаймні одну "
                "велику літеру, одну малу літеру, одну цифру та один спеціальний символ (@$!%*?&_)."
            )
        )
    except ValidationException as e:
        # Перевизначаємо тип помилки для більшої специфічності
        if e.errors and isinstance(e.errors, list) and e.errors[0]:
            e.errors[0]["type"] = "value_error.password.strength"
        raise


def validate_phone_number(phone_number: str, default_region: Optional[str] = "UA") -> str:
    """
    Перевіряє та форматує міжнародний номер телефону за допомогою бібліотеки `phonenumbers`.
    Повертає номер у форматі E.164, якщо він валідний.

    TODO: Додати `phonenumbers` до файлу `requirements.txt` або `pyproject.toml` проєкту.
          (наприклад, `pip install phonenumbers`)

    Args:
        phone_number (str): Номер телефону для перевірки.
        default_region (Optional[str]): Код регіону (наприклад, "UA", "PL", "US"), який використовується
                                       для парсингу номерів без міжнародного префікса.
                                       За замовчуванням "UA".

    Returns:
        str: Відформатований номер телефону у стандарті E.164 (наприклад, "+380501234567").

    Raises:
        ValidationException: Якщо номер телефону недійсний або бібліотека `phonenumbers` не встановлена.
    """
    if not PHONENUMBERS_LIB_AVAILABLE:
        logger.error("Бібліотека 'phonenumbers' не встановлена. Валідація номера телефону неможлива.")
        # TODO i18n: Translatable message
        raise ValidationException(
            message="Сервіс валідації номерів телефонів тимчасово недоступний (відсутня бібліотека 'phonenumbers').",
            errors=[{"loc": ("phone_number",),
                     "msg": "Не вдалося перевірити номер телефону через відсутність необхідної системної бібліотеки.",
                     "type": "value_error.phone_number.config_error"}]
        )

    if not phone_number or not phone_number.strip():
        # TODO i18n: Translatable message
        raise ValidationException(
            message="Номер телефону не може бути порожнім.",
            errors=[{"loc": ("phone_number",), "msg": "Введіть, будь ласка, номер телефону.",
                     "type": "value_error.phone_number.empty"}]
        )

    try:
        parsed_number = phonenumbers.parse(phone_number, region=default_region)
        if not phonenumbers.is_valid_number(parsed_number):
            # TODO i18n: Translatable message
            raise ValidationException(
                message="Вказаний номер телефону не є дійсним.",
                errors=[{"loc": ("phone_number",), "msg": "Номер телефону не відповідає дійсному формату або не існує.",
                         "type": "value_error.phone_number.invalid"}]
            )

        formatted_number = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
        logger.debug(f"Номер телефону '{phone_number}' (регіон: {default_region}) успішно валідовано та відформатовано як {formatted_number}.")
        return formatted_number
    except phonenumberutil.NumberParseException as e:
        logger.warning(f"Помилка парсингу номера телефону '{phone_number}' з регіоном '{default_region}': {e.error_type} - {e._msg}")
        # TODO i18n: Translatable messages in error_type_map and default specific_error_msg
        error_type_map = {
            phonenumbers.PhoneNumberUtil.ValidationResult.INVALID_COUNTRY_CODE: "Недійсний код країни.", # Замінено e.error_type на константи
            phonenumbers.PhoneNumberUtil.ValidationResult.NOT_A_NUMBER: "Рядок містить нецифрові символи там, де очікувались цифри.",
            phonenumbers.PhoneNumberUtil.ValidationResult.TOO_SHORT_AFTER_IDD: "Номер занадто короткий після міжнародного префіксу.",
            phonenumbers.PhoneNumberUtil.ValidationResult.TOO_SHORT_NSN: "Номер занадто короткий.",
            phonenumbers.PhoneNumberUtil.ValidationResult.TOO_LONG: "Номер занадто довгий."
        }
        # Оскільки e.error_type в NumberParseException є числовим індексом, а не самою константою,
        # може знадобитися інший підхід до мапінгу, або просто загальне повідомлення.
        # Для простоти, використаємо загальне повідомлення, якщо конкретне не знайдено.
        specific_error_msg = error_type_map.get(e.error_type, "Некоректний формат номера телефону.")

        # TODO i18n: Translatable message format for internal message
        raise ValidationException(
            message=f"Не вдалося розпізнати номер телефону '{phone_number}': {specific_error_msg}",
            errors=[{"loc": ("phone_number",), "msg": specific_error_msg, "type": "value_error.phone_number.parse_error"}]
        )


# --- Числові валідатори ---

def validate_positive_number(value: Any, field_name: str) -> Any:
    """
    Перевіряє, що надане значення є числом (int або float) і є строго додатним (> 0).
    """
    if not isinstance(value, (int, float)):
        # TODO i18n: Translatable message for `msg` (user-facing)
        raise ValidationException(
            message=f"Поле '{field_name}' повинно бути числом.",
            errors=[{"loc": (field_name,), "msg": "Значення має бути числовим.", "type": "type_error.number"}]
        )
    if value <= 0:
        # TODO i18n: Translatable message for `msg` (user-facing)
        raise ValidationException(
            message=f"Поле '{field_name}' має бути додатним числом (більше нуля).",
            errors=[{"loc": (field_name,), "msg": "Значення повинно бути більше нуля.",
                     "type": "value_error.number.positive"}]
        )
    return value


def validate_number_range(
        value: Any,
        field_name: str, # Змінено порядок для узгодженості з іншими валідаторами
        min_val: Optional[Union[int, float]] = None,
        max_val: Optional[Union[int, float]] = None
) -> Any:
    """
    Перевіряє, що числове значення знаходиться у вказаному діапазоні (включно з межами).
    """
    if not isinstance(value, (int, float)):
        # TODO i18n: Translatable message for `msg` (user-facing)
        raise ValidationException(
            message=f"Поле '{field_name}' повинно бути числом.",
            errors=[{"loc": (field_name,), "msg": "Значення має бути числовим.", "type": "type_error.number"}]
        )
    if min_val is not None and value < min_val:
        # TODO i18n: Translatable message for `msg` (user-facing)
        raise ValidationException(
            message=f"Значення поля '{field_name}' ({value}) менше за мінімально допустиме ({min_val}).",
            errors=[{"loc": (field_name,), "msg": f"Значення повинно бути не менше {min_val}.",
                     "type": "value_error.number.min_value", "ctx": {"limit_value": min_val}}]
        )
    if max_val is not None and value > max_val:
        # TODO i18n: Translatable message for `msg` (user-facing)
        raise ValidationException(
            message=f"Значення поля '{field_name}' ({value}) перевищує максимально допустиме ({max_val}).",
            errors=[{"loc": (field_name,), "msg": f"Значення повинно бути не більше {max_val}.",
                     "type": "value_error.number.max_value", "ctx": {"limit_value": max_val}}]
        )
    return value


# --- Валідатори для списків/колекцій ---

def validate_list_not_empty(value: Optional[List[Any]], field_name: str) -> List[Any]:
    """
    Перевіряє, що наданий список не є `None` і містить принаймні один елемент.
    """
    if value is None or not value:  # Порожній список також вважається невалідним
        # TODO i18n: Translatable message for `msg` (user-facing)
        raise ValidationException(
            message=f"Список '{field_name}' не може бути порожнім.",
            errors=[{"loc": (field_name,), "msg": "Список повинен містити принаймні один елемент.",
                     "type": "value_error.list.not_empty"}]
        )
    return value


# Блок для демонстрації та базового тестування валідаторів при прямому запуску модуля.
if __name__ == "__main__":
    # Налаштування логування для тестування
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
        base_logging.basicConfig(level=logging.INFO)
        logger.warning("Не вдалося імпортувати setup_logging. Використовується базова конфігурація логування для тестів validators.py.")

    logger.info("--- Демонстрація Основних Функцій-Валідаторів ---")

    # Допоміжна функція для тестування валідаторів
    def test_validator(validator_func: callable, test_value: Any, *args: Any, expected_to_pass: bool = True):
        """Тестує валідатор та виводить результат у консоль."""
        # Визначення імені поля для логування
        field_name_for_log = "значення" # За замовчуванням
        if validator_func in [validate_username_format, validate_password_strength]:
            field_name_for_log = validator_func.__name__.split("_")[1]
        elif args and isinstance(args[-1], str) and len(args) >= 1: # Якщо останній арг - рядок, припускаємо, що це field_name
             if validator_func == validate_number_range and len(args) >= 2 and isinstance(args[0], str): # для validate_number_range field_name - перший арг
                 field_name_for_log = args[0]
             elif validator_func != validate_number_range and isinstance(args[-1], str) : # для інших - останній
                 field_name_for_log = args[-1]


        logger.info(f"\nТестування {validator_func.__name__} з '{test_value}' для поля '{field_name_for_log}':")
        try:
            result = validator_func(test_value, *args)
            if expected_to_pass:
                logger.info(f"  \033[92mУСПІХ:\033[0m Валідація пройдена. Результат: '{result}'")
            else:
                logger.error(f"  \033[91mПОМИЛКА ТЕСТУ:\033[0m Валідація неочікувано пройдена. Результат: '{result}'")
        except ValidationException as e:
            if expected_to_pass:
                logger.error(
                    f"  \033[91mПОМИЛКА ТЕСТУ:\033[0m Валідація не пройдена, хоча очікувався успіх. Помилка: {e.message}")
                logger.info(f"    Деталі помилки (errors): {e.errors}")
            else:
                logger.info(f"  \033[92mУСПІХ (очікувана помилка валідації):\033[0m {e.message}")
                logger.info(f"    Деталі помилки (errors): {e.errors}")
        except Exception as e_general:
            logger.critical(f"  \033[91mНЕОЧІКУВАНА КРИТИЧНА ПОМИЛКА:\033[0m {e_general}", exc_info=True)


    # Тестування валідаторів рядків
    test_validator(validate_not_empty, "Привіт Світ", "повідомлення")
    test_validator(validate_not_empty, "  ", "повідомлення_пробіли", expected_to_pass=False)
    test_validator(validate_not_empty, None, "повідомлення_none", expected_to_pass=False)

    test_validator(validate_max_length, "коротко", 10, "назва_тегу")
    test_validator(validate_max_length, "дужедужедовгийтекст", 10, "назва_тегу_довгий", expected_to_pass=False)

    test_validator(validate_min_length, "достатньо", 5, "ключ_API")
    test_validator(validate_min_length, "мало", 5, "ключ_API_короткий", expected_to_pass=False)

    # Тестування валідаторів специфічних форматів
    test_validator(validate_username_format, "korystuvach_123")
    test_validator(validate_username_format, "sh", expected_to_pass=False)
    test_validator(validate_username_format, "ім'я з пробілом", expected_to_pass=False)
    test_validator(validate_username_format, "korystuvach!", expected_to_pass=False)

    test_validator(validate_password_strength, "MicNyiP@r0l!")
    test_validator(validate_password_strength, "slabyi", expected_to_pass=False)
    test_validator(validate_password_strength, "BezSpecSymv0liv", expected_to_pass=False)
    test_validator(validate_password_strength, "bezvelykoiliteri1@", expected_to_pass=False)

    logger.info("\nТестування validate_phone_number (з бібліотекою phonenumbers):")
    # Тести для validate_phone_number (очікують помилку, якщо phonenumbers не встановлено)
    # Або успіх, якщо встановлено та номер валідний.
    # Для CI/CD, де phonenumbers може бути не встановлено, ці тести мають враховувати цей випадок.
    # Встановлюємо expected_to_pass=False, якщо очікуємо помилку через відсутність бібліотеки.
    # Якщо бібліотека буде встановлена, ці тести потрібно буде скоригувати.
    is_phonenumbers_expected_to_pass = PHONENUMBERS_LIB_AVAILABLE # true, якщо бібліотека є

    test_validator(validate_phone_number, "+380501234567", "UA", expected_to_pass=is_phonenumbers_expected_to_pass)
    test_validator(validate_phone_number, "0501234567", "UA", expected_to_pass=is_phonenumbers_expected_to_pass)
    test_validator(validate_phone_number, "+14155552671", "US", expected_to_pass=is_phonenumbers_expected_to_pass)
    test_validator(validate_phone_number, "12345", "UA", expected_to_pass=False) # Завжди невалідний
    test_validator(validate_phone_number, "не номер", "UA", expected_to_pass=False) # Завжди невалідний
    test_validator(validate_phone_number, "", "UA", expected_to_pass=False) # Порожній рядок

    # Тестування числових валідаторів
    test_validator(validate_positive_number, 15.5, "ціна")
    test_validator(validate_positive_number, 0, "кількість", expected_to_pass=False)
    test_validator(validate_positive_number, -10, "рейтинг", expected_to_pass=False)
    test_validator(validate_positive_number, "нечисло", "сума", expected_to_pass=False)

    test_validator(validate_number_range, 7, "оцінка", 1, 10) # field_name, min_val, max_val
    test_validator(validate_number_range, 0, "оцінка_min", 1, 10, expected_to_pass=False)
    test_validator(validate_number_range, 11, "оцінка_max", 1, 10, expected_to_pass=False)
    test_validator(validate_number_range, 10, "верхня_межа", None, 10)
    test_validator(validate_number_range, 1, "нижня_межа", 1, None)
    test_validator(validate_number_range, "текст", "нечисло", 1, 10, expected_to_pass=False)


    # Тестування валідаторів списків
    test_validator(validate_list_not_empty, ["яблуко", "банан"], "фрукти")
    test_validator(validate_list_not_empty, [], "теги_порожні", expected_to_pass=False)
    test_validator(validate_list_not_empty, None, "категорії_none", expected_to_pass=False)

    logger.info("\nПримітка: Для використання цих валідаторів у Pydantic моделях, їх зазвичай")
    logger.info("інтегрують за допомогою декоратора `@field_validator` (Pydantic V2) або `@validator` (Pydantic V1).")
    logger.info("Демонстрацію валідаторів завершено.")
