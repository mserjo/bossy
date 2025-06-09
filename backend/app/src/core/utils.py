# backend/app/src/core/utils.py

"""
Цей модуль надає різноманітні допоміжні функції, які можна повторно
використовувати в різних частинах програми і які не вписуються
в більш специфічні модулі утиліт (наприклад, validators.py або security.py з config).
"""

import random
import string
import re
from datetime import datetime, timezone, timedelta
from typing import Any, Optional, List, Dict, Union
from decimal import Decimal, ROUND_HALF_UP

# --- Утиліти для рядків ---

def generate_random_string(length: int, chars: str = string.ascii_letters + string.digits) -> str:
    """
    Генерує випадковий рядок заданої довжини із заданого набору символів.

    Args:
        length (int): Бажана довжина випадкового рядка.
        chars (str): Рядок, що містить символи для вибору.
                     За замовчуванням використовуються буквено-цифрові символи (літери + цифри).

    Returns:
        str: Згенерований випадковий рядок.
    """
    if length <= 0:
        return ""
    return "".join(random.choice(chars) for _ in range(length))

def generate_random_numeric_string(length: int) -> str:
    """
    Генерує випадковий рядок, що складається лише з цифр.
    """
    return generate_random_string(length, string.digits)

def slugify(text: str, separator: str = "-") -> str:
    """
    Генерує URL-дружній "слаг" із заданого тексту.
    Перетворює на нижній регістр, видаляє небуквено-цифрові символи (крім пробілів та дефісів),
    замінює пробіли та повторювані дефіси одним вказаним роздільником.
    """
    if not text:
        return ""
    text = text.lower()
    # Видалити спеціальні символи, поки що зберігаючи пробіли та дефіси
    text = re.sub(r"[^a-z0-9\s-]", "", text, flags=re.UNICODE)
    # Замінити пробіли та кілька дефісів одним роздільником
    text = re.sub(r"[\s-]+|-", separator, text).strip(separator)
    return text

def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Обрізає рядок до максимальної довжини, додаючи суфікс, якщо обрізано.
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

# --- Утиліти для дати та часу ---

def get_current_utc_timestamp() -> datetime:
    """Повертає поточну дату та час у UTC з інформацією про часовий пояс."""
    return datetime.now(timezone.utc)

def format_datetime_for_display(dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S %Z%z") -> str:
    """
    Форматує об'єкт datetime у рядок для відображення.
    За замовчуванням використовується поширений ISO-подібний формат з часовим поясом.
    """
    if not dt:
        return ""
    return dt.strftime(fmt)

def human_readable_timedelta(delta: timedelta) -> str:
    """
    Перетворює об'єкт timedelta на людиночитаний рядок (наприклад, "2 дні, 3 години").
    """
    seconds = int(delta.total_seconds())
    if seconds < 0:
        return "(від'ємна тривалість)"
    if seconds == 0:
        return "0 секунд"

    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts = []
    if days > 0:
        parts.append(f"{days} день{'i' if days != 1 else ''}") # Адаптація для української мови
    if hours > 0:
        parts.append(f"{hours} годин{'а' if hours == 1 else ('и' if 1 < hours < 5 else '')}") # Адаптація для української мови
    if minutes > 0:
        parts.append(f"{minutes} хвилин{'а' if minutes == 1 else ('и' if 1 < minutes < 5 else '')}") # Адаптація для української мови
    if seconds > 0 or not parts: # Показати секунди, якщо це єдина одиниця або якщо не нуль
        parts.append(f"{seconds} секунд{'а' if seconds == 1 else ('и' if 1 < seconds < 5 else '')}") # Адаптація для української мови

    return ", ".join(parts)

# --- Числові утиліти ---

def round_decimal(number: Union[float, Decimal, str], decimal_places: int = 2) -> Decimal:
    """
    Округлює число до вказаної кількості десяткових знаків, використовуючи Decimal для точності.
    Використовує метод округлення ROUND_HALF_UP.
    """
    if not isinstance(number, Decimal):
        number = Decimal(str(number))
    quantizer = Decimal("1e-" + str(decimal_places)) # наприклад, Decimal('0.01') для 2 знаків
    return number.quantize(quantizer, rounding=ROUND_HALF_UP)

# --- Утиліти для колекцій ---

def chunk_list(data: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Розбиває список на менші частини заданого розміру.
    Приклад: chunk_list([1,2,3,4,5], 2) -> [[1,2], [3,4], [5]]
    """
    if chunk_size <= 0:
        raise ValueError("Розмір частини повинен бути додатним цілим числом.")
    return [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]

def get_from_dict_or_object(data: Union[Dict[str, Any], object], key: str, default: Optional[Any] = None) -> Any:
    """
    Безпечно отримує значення зі словника або атрибут з об'єкта.

    Args:
        data: Словник або об'єкт, з якого потрібно отримати значення.
        key: Ключ або назва атрибута.
        default: Значення за замовчуванням, яке повертається, якщо ключ/атрибут не знайдено.

    Returns:
        Значення, якщо знайдено, інакше значення за замовчуванням.
    """
    if isinstance(data, dict):
        return data.get(key, default)
    else:
        return getattr(data, key, default)

# --- Інші утиліти ---

def generate_unique_code(length: int = 6, prefix: str = "") -> str:
    """
    Генерує унікальний код, зазвичай для таких речей, як коди запрошень або короткі ID.
    Поєднує префікс із випадковим рядком. Для справжньої унікальності в розподіленій системі
    потрібні більш надійні механізми (наприклад, UUID, послідовності бази даних).
    Це більше для людиночитаних, відносно коротких кодів.
    """
    random_part = generate_random_string(length, string.ascii_uppercase + string.digits)
    return f"{prefix}{random_part}".upper()


if __name__ == "__main__":
    print("--- Демонстрація основних утиліт ---")

    # Рядкові утиліти
    print(f"\nВипадковий рядок (10 символів): {generate_random_string(10)}")
    print(f"Випадковий числовий рядок (8 символів): {generate_random_numeric_string(8)}")
    print(f"Slugify 'Привіт Світ! 123': {slugify('Привіт Світ! 123')}")
    print(f"Slugify '  --Зайві--Дефіси--  ': {slugify('  --Зайві--Дефіси--  ')}")
    print(f"Обрізати 'Це довгий рядок' (макс 10): {truncate_string('Це довгий рядок', 10)}")
    print(f"Обрізати 'Короткий' (макс 10): {truncate_string('Короткий', 10)}")

    # Утиліти для дати та часу
    utc_now = get_current_utc_timestamp()
    print(f"\nПоточна мітка часу UTC: {utc_now}")
    print(f"Відформатована мітка часу UTC: {format_datetime_for_display(utc_now)}")
    delta_example = timedelta(days=2, hours=3, minutes=30, seconds=5)
    print(f"Людиночитаний timedelta ({delta_example}): {human_readable_timedelta(delta_example)}")
    print(f"Людиночитаний timedelta (0 секунд): {human_readable_timedelta(timedelta(seconds=0))}")

    # Числові утиліти
    print(f"\nОкруглити 123.456 (2 знаки): {round_decimal(123.456, 2)}")
    print(f"Округлити 123.454 (2 знаки): {round_decimal(123.454, 2)}")
    print(f"Округлити 123.45 (0 знаків): {round_decimal(123.45, 0)}")

    # Утиліти для колекцій
    my_list = list(range(10))
    print(f"\nРозбити список {my_list} (розмір 3): {chunk_list(my_list, 3)}")
    my_dict = {"name": "Аліса", "age": 30}
    print(f"Отримати 'name' зі словника: {get_from_dict_or_object(my_dict, 'name')}")
    print(f"Отримати 'city' зі словника (за замовчуванням 'N/A'): {get_from_dict_or_object(my_dict, 'city', 'N/A')}")

    class MyObj:
        def __init__(self):
            self.title = "Тестовий об'єкт"
    my_obj_instance = MyObj()
    print(f"Отримати 'title' з об'єкта: {get_from_dict_or_object(my_obj_instance, 'title')}")

    # Інші утиліти
    print(f"\nУнікальний код (префікс 'INV-'): {generate_unique_code(6, 'INV-')}")
    print(f"Унікальний код (за замовчуванням): {generate_unique_code()}")
