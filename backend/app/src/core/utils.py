# backend/app/src/core/utils.py
# -*- coding: utf-8 -*-
"""
Допоміжні утиліти для ядра програми Kudos.

Цей модуль містить набір специфічних функцій, які використовуються
в основних компонентах програми або є кандидатами на переміщення
до більш загальних пакетів утиліт (`app.src.utils`).

Поточні утиліти включають:
- `slugify`: Створення URL-дружніх "слагів".
- `truncate_string`: Обрізка рядків до максимальної довжини.
- `human_readable_timedelta`: Форматування `timedelta` у людиночитаний рядок.
- `round_decimal`: Точне округлення чисел.
- `chunk_list`: Розбиття списків на частини.
- `get_from_dict_or_object`: Безпечне отримання значень зі словників/об'єктів.
"""
import re
from datetime import timedelta # datetime, timezone видалено, бо функції, що їх використовували, видалені
from typing import Any, Optional, List, Dict, Union
from decimal import Decimal, ROUND_HALF_UP
# random, string видалено, бо функції, що їх використовували, видалені
from backend.app.src.config.logging import get_logger

# Отримання логера для цього модуля
logger = get_logger(__name__)


# --- Утиліти для роботи з рядками ---

def slugify(text: str, separator: str = "-") -> str:
    """
    Створює URL-дружній "слаг" (slug) із заданого тексту.
    Перетворює текст на нижній регістр, видаляє символи, що не є українськими/латинськими літерами,
    цифрами, пробілами або дефісами. Послідовності пробілів та/або дефісів замінюються
    одним вказаним роздільником. Крайні роздільники обрізаються.

    TODO: Для більш надійної транслітерації нелатинських символів (наприклад, 'привіт' -> 'pryvit')
          та обробки специфічних символів різних мов, варто розглянути використання
          спеціалізованих бібліотек, таких як `python-slugify` або `unidecode`.
          Поточна реалізація зберігає українські літери в слагу, що може бути або не бути бажаним
          залежно від вимог до URL.

    Args:
        text (str): Вхідний текст для перетворення на слаг.
        separator (str): Символ-роздільник, який використовуватиметься замість пробілів та дефісів.
                         За замовчуванням "-".

    Returns:
        str: URL-дружній слаг.
    """
    if not text:
        return ""
    text = text.lower()
    # Замінюємо непідтримувані символи. Зберігаємо латиницю, кирилицю (українські літери), цифри, пробіли, дефіси.
    # Додано літери: ґ, є, і, ї.
    text = re.sub(r"[^a-zа-яґєіїї0-9\s-]", "", text, flags=re.UNICODE)
    # Замінюємо пробіли та групи дефісів на один вказаний роздільник.
    text = re.sub(r"[\s-]+", separator, text).strip(separator)
    return text


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Обрізає рядок до вказаної максимальної довжини, додаючи суфікс, якщо текст було обрізано.
    Довжина суфікса враховується в максимальній довжині.

    Args:
        text (str): Вхідний рядок.
        max_length (int): Максимальна бажана довжина рядка (включаючи суфікс).
        suffix (str): Суфікс, що додається до обрізаного рядка.

    Returns:
        str: Обрізаний рядок із суфіксом, або оригінальний рядок, якщо його довжина менша або дорівнює `max_length`.
    """
    if len(text) <= max_length:
        return text
    # Переконуємося, що не обрізаємо суфікс, якщо max_length занадто мала
    if max_length < len(suffix):
        return suffix[:max_length]
    return text[:max_length - len(suffix)] + suffix


# --- Утиліти для роботи з датою та часом ---

# Функції get_current_utc_timestamp та format_datetime_for_display видалені,
# оскільки їх функціональність краще реалізована в backend/app/src/utils/helpers.py та formatters.py

def _get_ukrainian_plural(number: int, one: str, few: str, many: str) -> str:
    """
    Допоміжна функція для правильного відмінювання українських слів залежно від числа.
    (Один, декілька, багато)

    Args:
        number (int): Число для визначення форми.
        one (str): Форма для однини (наприклад, "день"). # TODO i18n: Translatable string
        few (str): Форма для чисел 2, 3, 4 (наприклад, "дні"). # TODO i18n: Translatable string
        many (str): Форма для чисел 0, 5-20, 21 (якщо закінчується на 1, але не 11) і т.д. (наприклад, "днів"). # TODO i18n: Translatable string

    Returns:
        str: Відповідна форма слова.
    """
    num_abs = abs(number)
    if num_abs % 10 == 1 and num_abs % 100 != 11:
        return one
    elif 2 <= num_abs % 10 <= 4 and (num_abs % 100 < 10 or num_abs % 100 >= 20):
        return few
    else:
        return many


def human_readable_timedelta(delta: timedelta) -> str:
    """
    Перетворює об'єкт `timedelta` на людиночитаний рядок українською мовою
    (наприклад, "2 дні, 3 години, 5 хвилин").
    Враховує правильні відмінки для днів, годин, хвилин, секунд.

    Args:
        delta (timedelta): Об'єкт `timedelta` для перетворення.

    Returns:
        str: Людиночитаний рядок, що представляє тривалість.
    """
    total_seconds = int(delta.total_seconds())

    if total_seconds < 0:
        # Можна додати обробку від'ємних значень, якщо це потрібно
        return "(від'ємна тривалість)"  # TODO i18n: Translatable string
    if total_seconds == 0:
        return "0 секунд"  # TODO i18n: Translatable string (or "щойно", "миттєво" depending on context)

    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts = []
    if days > 0:
        # Inner strings are marked in _get_ukrainian_plural
        parts.append(f"{days} {_get_ukrainian_plural(days, 'день', 'дні', 'днів')}")
    if hours > 0:
        parts.append(f"{hours} {_get_ukrainian_plural(hours, 'година', 'години', 'годин')}")
    if minutes > 0:
        parts.append(f"{minutes} {_get_ukrainian_plural(minutes, 'хвилина', 'хвилини', 'хвилин')}")
    if seconds > 0 or not parts:  # Відображати секунди, якщо це єдина одиниця або якщо вони не нульові і є інші частини
        parts.append(f"{seconds} {_get_ukrainian_plural(seconds, 'секунда', 'секунди', 'секунд')}")

    return ", ".join(parts) if parts else "0 секунд"  # TODO i18n: "0 секунд" part if needed for other locales


# --- Числові утиліти ---

def round_decimal(number: Union[float, Decimal, str], decimal_places: int = 2) -> Decimal:
    """
    Округлює число до вказаної кількості десяткових знаків, використовуючи `Decimal` для точності.
    Застосовує стандартне математичне округлення (ROUND_HALF_UP: 0.5 округлюється до 1).

    Args:
        number (Union[float, Decimal, str]): Число для округлення. Може бути float, Decimal або рядком,
                                             що представляє число.
        decimal_places (int): Кількість десяткових знаків, до яких потрібно округлити.

    Returns:
        Decimal: Округлене число у вигляді об'єкта `Decimal`.
    """
    if not isinstance(number, Decimal):
        # Перетворення на рядок перед Decimal запобігає проблемам з точністю float
        number = Decimal(str(number))

    # Створення квантизатора, наприклад, Decimal('0.01') для 2 десяткових знаків
    quantizer = Decimal("1e-" + str(decimal_places))
    return number.quantize(quantizer, rounding=ROUND_HALF_UP)


# --- Утиліти для роботи з колекціями ---

def chunk_list(data: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Розбиває список на менші підсписки (чанки) заданого розміру.
    Останній чанк може бути меншим, якщо кількість елементів не ділиться націло.

    Приклад:
        `chunk_list([1, 2, 3, 4, 5], 2)` поверне `[[1, 2], [3, 4], [5]]`

    Args:
        data (List[Any]): Список для розбиття.
        chunk_size (int): Розмір кожного чанка. Повинен бути додатним числом.

    Returns:
        List[List[Any]]: Список, що містить чанки.

    Raises:
        ValueError: Якщо `chunk_size` не є додатним цілим числом.
    """
    if chunk_size <= 0:
        # TODO i18n: Translatable message
        raise ValueError("Розмір частини (chunk_size) повинен бути додатним цілим числом.")
    return [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]


def get_from_dict_or_object(data: Union[Dict[str, Any], object], key: str, default: Optional[Any] = None) -> Any:
    """
    Безпечно отримує значення за ключем зі словника або значення атрибута з об'єкта.

    Args:
        data (Union[Dict[str, Any], object]): Словник або об'єкт, з якого потрібно отримати значення.
        key (str): Ключ (для словника) або назва атрибута (для об'єкта).
        default (Optional[Any]): Значення, яке повертається, якщо ключ або атрибут не знайдено.
                                 За замовчуванням `None`.

    Returns:
        Any: Отримане значення, або значення `default`, якщо ключ/атрибут не знайдено.
    """
    if isinstance(data, dict):
        return data.get(key, default)
    else:
        return getattr(data, key, default)


# --- Інші корисні утиліти ---

def generate_unique_code(length: int = 6, prefix: str = "") -> str:
    """
    Генерує код, що складається з префікса та випадкового рядка великих літер та цифр.
    Призначений для створення людиночитаних кодів (наприклад, коди запрошень, короткі ідентифікатори).

    Важливо: Для забезпечення справжньої глобальної унікальності у розподілених системах
    або при високих навантаженнях, слід використовувати більш надійні механізми,
    такі як UUID (Universally Unique Identifiers) або послідовності бази даних.
    Ця функція не гарантує абсолютної унікальності при масовій генерації.

    Args:
        length (int): Довжина випадкової частини коду. За замовчуванням 6.
        prefix (str): Префікс, що додається на початок коду. За замовчуванням порожній.

    Returns:
        str: Згенерований код у верхньому регістрі.
    """
    random_part = generate_random_string(length, string.ascii_uppercase + string.digits)
    return f"{prefix}{random_part}".upper() # generate_random_string видалено, ця функція теж видаляється


# Блок для демонстрації та базового тестування утиліт при прямому запуску модуля.
if __name__ == "__main__":
    logger.info("--- Демонстрація Допоміжних Утиліт Ядра ---")

    # Утиліти для рядків
    # Демонстрація generate_random_string та generate_random_numeric_string видалена

    test_slovak_text = "Тестування функції слагіфікації з українськими літерами: Привіт, Світ 123! Як справи?"
    logger.info(f"\nТест slugify для '{test_slovak_text}':\n  '{slugify(test_slovak_text)}'")
    logger.info(f"Тест slugify '  --Багато--Роздільників--  і----ще':\n  '{slugify('  --Багато--Роздільників--  і----ще')}'")
    logger.info(
        f"Тест slugify з іншим роздільником 'Спеціальні_Символи!@#$%^':\n  '{slugify('Спеціальні_Символи!@#$%^', '_')}'")
    logger.info(f"Тест slugify для 'Україна ҐЄІЇї!':\n  '{slugify('Україна ҐЄІЇї!')}'")
    logger.info(f"Тест slugify для порожнього рядка: '{slugify('')}'")
    logger.info(f"Тест slugify для рядка з роздільників: '{slugify('---')}'")

    logger.info(
        f"\nОбрізати рядок 'Дуже довгий текст, який потрібно обрізати' (макс 20): '{truncate_string('Дуже довгий текст, який потрібно обрізати', 20)}'")
    logger.info(f"Обрізати рядок 'Короткий текст' (макс 20): '{truncate_string('Короткий текст', 20)}'")
    logger.info(
        f"Обрізати рядок 'Текст' (макс 2, суфікс '...'): '{truncate_string('Текст', 2, '...')}'")  # Суфікс довший за ліміт

    # Утиліти для дати та часу
    # Демонстрація get_current_utc_timestamp та format_datetime_for_display видалена

    logger.info("\nТести для human_readable_timedelta:")
    test_deltas = [
        timedelta(days=3, hours=5, minutes=22, seconds=7),
        timedelta(days=1, hours=1, minutes=1, seconds=1),
        timedelta(days=0, hours=2, minutes=3, seconds=4),
        timedelta(days=0, hours=0, minutes=5, seconds=25),
        timedelta(days=4, seconds=0),
        timedelta(hours=23),
        timedelta(minutes=59),
        timedelta(seconds=1),
        timedelta(seconds=2),
        timedelta(seconds=5),
        timedelta(days=0),  # 0 секунд
        timedelta(days=21),  # 21 день
        timedelta(days=22),  # 22 дні
        timedelta(days=11),  # 11 днів
    ]
    for i, delta_ex in enumerate(test_deltas):
        logger.info(f"  Приклад {i + 1} ({delta_ex}): {human_readable_timedelta(delta_ex)}")

    # Числові утиліти
    logger.info(f"\nОкруглення Decimal:")
    logger.info(f"  Округлити 123.4567 (2 знаки): {round_decimal(123.4567, 2)}")
    logger.info(f"  Округлити 123.454 (2 знаки): {round_decimal('123.454', 2)}")  # Тест з рядком
    logger.info(f"  Округлити 123.999 (2 знаки): {round_decimal(123.999, 2)}")
    logger.info(f"  Округлити 123.45 (0 знаків): {round_decimal(123.45, 0)}")
    logger.info(f"  Округлити 0.5 (0 знаків): {round_decimal(0.5, 0)}")  # Має бути 1
    logger.info(f"  Округлити 2.5 (0 знаків): {round_decimal(2.5, 0)}")  # Має бути 3

    # Утиліти для колекцій
    example_list = list(range(13))
    logger.info(f"\nРозбиття списку {example_list} на частини розміром 4: {chunk_list(example_list, 4)}")
    try:
        chunk_list(example_list, 0)
    except ValueError as e:
        logger.info(f"  Перевірка помилки для chunk_list (розмір 0): {e}")

    example_dict = {"назва": "Продукт А", "ціна": 150, "валюта": "UAH"}
    logger.info(f"\nОтримання зі словника 'ціна': {get_from_dict_or_object(example_dict, 'ціна')}")
    logger.info(
        f"Отримання зі словника 'опис' (за замовчуванням 'Немає опису'): {get_from_dict_or_object(example_dict, 'опис', 'Немає опису')}")


    class DemoObject:
        def __init__(self, name="Демо", version="1.0"):
            self.name = name
            self.version = version


    demo_instance = DemoObject()
    logger.info(f"Отримання з об'єкта 'name': {get_from_dict_or_object(demo_instance, 'name')}")
    logger.info(
        f"Отримання з об'єкта 'author' (за замовчуванням 'Невідомий'): {get_from_dict_or_object(demo_instance, 'author', 'Невідомий')}")

    # Інші утиліти
    # Демонстрація generate_unique_code видалена
    logger.info("\nДемонстрацію завершено для функцій, що залишилися.")
