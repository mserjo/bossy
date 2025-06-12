# backend/app/src/core/utils.py
# -*- coding: utf-8 -*-
# # Модуль допоміжних утиліт для ядра програми Kudos (Virtus).
# #
# # Цей модуль містить набір різноманітних функцій, які використовуються
# # в основних компонентах програми (`core`) або є кандидатами на переміщення
# # до більш загального пакету утиліт (`backend.app.src.utils`) у майбутньому.
# # Поточні утиліти включають функції для роботи з рядками (слагіфікація, обрізка),
# # форматування часових інтервалів (`timedelta`), точного округлення чисел,
# # маніпуляцій зі списками та безпечного доступу до даних у словниках/об'єктах.
# #
# # Примітка: Деякі функції, що раніше тут знаходились (наприклад, генерація випадкових рядків),
# # були видалені, оскільки їх функціональність краще реалізована іншими засобами
# # або в спеціалізованих модулях.

import re # Для функції slugify
from datetime import timedelta # Для human_readable_timedelta
from typing import Any, Optional, List, Dict, Union # Типізація
from decimal import Decimal, ROUND_HALF_UP # Для точного округлення round_decimal

# Імпорт логера з централізованої конфігурації
from backend.app.src.config.logging import get_logger

# Отримання логера для цього модуля
logger = get_logger(__name__)


# --- Утиліти для роботи з рядками ---

def slugify(text: str, separator: str = "-") -> str:
    """
    Створює URL-дружній "слаг" (slug) із заданого тексту.
    Перетворює текст на нижній регістр, видаляє символи, що не є українськими/латинськими літерами,
    цифрами, пробілами або дефісами. Послідовності пробілів та/або дефісів замінюються
    одним вказаним роздільником. Крайні роздільники (на початку та в кінці) обрізаються.

    TODO: Для більш надійної транслітерації нелатинських символів (наприклад, 'привіт' -> 'pryvit')
          та обробки специфічних символів різних мов (наприклад, німецькі умлаути), варто розглянути
          використання спеціалізованих бібліотек, таких як `python-slugify` або `unidecode`.
          Поточна реалізація зберігає українські літери в слагу, що може бути або не бути бажаним
          залежно від вимог до URL та SEO.

    Args:
        text (str): Вхідний текст для перетворення на слаг.
        separator (str): Символ-роздільник, який використовуватиметься замість пробілів та дефісів.
                         За замовчуванням "-".

    Returns:
        str: URL-дружній слаг. Повертає порожній рядок, якщо вхідний текст порожній.
    """
    if not text:
        return ""
    text = text.lower() # Перетворення на нижній регістр
    # Замінюємо непідтримувані символи. Зберігаємо латиницю (a-z), кирилицю (а-я),
    # українські літери ґ, є, і, ї, цифри (0-9), пробіли (\s) та дефіси (-).
    # Зверніть увагу, що \s також включає табуляцію, нові рядки тощо, які потім обробляються.
    text = re.sub(r"[^a-zа-яґєіїї0-9\s-]", "", text, flags=re.UNICODE)
    # Замінюємо одну або більше послідовностей пробілів та/або дефісів на один вказаний роздільник.
    text = re.sub(r"[\s-]+", separator, text).strip(separator)
    return text


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Обрізає рядок до вказаної максимальної довжини, додаючи суфікс, якщо текст було обрізано.
    Довжина суфікса враховується в загальній максимальній довжині рядка.

    Args:
        text (str): Вхідний рядок для обрізки.
        max_length (int): Максимальна бажана довжина рядка (включаючи суфікс).
        suffix (str): Суфікс, що додається до обрізаного рядка (наприклад, "...").

    Returns:
        str: Обрізаний рядок із суфіксом, або оригінальний рядок, якщо його довжина
             менша або дорівнює `max_length`. Якщо `max_length` менша за довжину
             суфікса, повертається обрізаний суфікс.
    """
    if len(text) <= max_length:
        return text
    # Переконуємося, що не обрізаємо сам суфікс, якщо max_length занадто мала.
    if max_length < len(suffix):
        return suffix[:max_length] # Повертаємо частину суфікса, що вміщується
    return text[:max_length - len(suffix)] + suffix


# --- Утиліти для роботи з датою та часом ---

def _get_ukrainian_plural(number: int, one: str, few: str, many: str) -> str:
    """
    Допоміжна функція для правильного відмінювання українських слів (іменників),
    що йдуть після числівника, залежно від самого числа.
    (Форми: один, декілька, багато)

    Args:
        number (int): Число для визначення правильної форми слова.
        one (str): Форма слова для однини (наприклад, "день" для числа 1, 21, 31, ... крім 11).
        few (str): Форма слова для невеликої кількості (наприклад, "дні" для чисел 2, 3, 4, 22, 23, 24, ... крім 12, 13, 14).
        many (str): Форма слова для множини (наприклад, "днів" для чисел 0, 5-20, 25-30, ... або 21, якщо `one` інше).

    Returns:
        str: Відповідна форма слова українською мовою.
    """
    num_abs = abs(number) # Працюємо з абсолютним значенням для визначення закінчення
    # Правила для української мови:
    # - закінчується на 1, але не на 11: однина (one)
    # - закінчується на 2, 3, 4, але не на 12, 13, 14: "декілька" (few)
    # - решта випадків (0, 5-9, 10-20, та числа, що закінчуються на 11-19): "багато" (many)
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
             Повертає "0 секунд", якщо тривалість нульова.
             Повертає "(від'ємна тривалість)", якщо тривалість від'ємна.
    """
    total_seconds = int(delta.total_seconds())

    if total_seconds < 0:
        # TODO i18n: Translatable string "(від'ємна тривалість)"
        return "(від'ємна тривалість)"
    if total_seconds == 0:
        # TODO i18n: Translatable string "0 секунд"
        return "0 секунд" # Або "щойно", "миттєво" залежно від контексту використання

    days, remainder = divmod(total_seconds, 86400) # 86400 секунд у дні
    hours, remainder = divmod(remainder, 3600)    # 3600 секунд у годині
    minutes, seconds = divmod(remainder, 60)      # 60 секунд у хвилині

    parts = []
    if days > 0:
        # TODO i18n: Base words for _get_ukrainian_plural: 'день', 'дні', 'днів'
        parts.append(f"{days} {_get_ukrainian_plural(days, 'день', 'дні', 'днів')}")
    if hours > 0:
        # TODO i18n: Base words for _get_ukrainian_plural: 'година', 'години', 'годин'
        parts.append(f"{hours} {_get_ukrainian_plural(hours, 'година', 'години', 'годин')}")
    if minutes > 0:
        # TODO i18n: Base words for _get_ukrainian_plural: 'хвилина', 'хвилини', 'хвилин'
        parts.append(f"{minutes} {_get_ukrainian_plural(minutes, 'хвилина', 'хвилини', 'хвилин')}")
    if seconds > 0 or not parts:  # Відображати секунди, якщо це єдина одиниця або якщо вони не нульові і є інші частини
        # TODO i18n: Base words for _get_ukrainian_plural: 'секунда', 'секунди', 'секунд'
        parts.append(f"{seconds} {_get_ukrainian_plural(seconds, 'секунда', 'секунди', 'секунд')}")

    # Якщо parts порожній (що малоймовірно через `seconds > 0 or not parts`), повертаємо "0 секунд"
    # TODO i18n: Translatable string "0 секунд" (if parts is empty)
    return ", ".join(parts) if parts else "0 секунд"


# --- Числові утиліти ---

def round_decimal(number: Union[float, Decimal, str], decimal_places: int = 2) -> Decimal:
    """
    Округлює число до вказаної кількості десяткових знаків, використовуючи `Decimal` для точності.
    Застосовує стандартне математичне округлення (ROUND_HALF_UP: 0.5 округлюється "вгору" від нуля).

    Args:
        number (Union[float, Decimal, str]): Число для округлення. Може бути float, Decimal або рядком,
                                             що представляє число (наприклад, "123.456").
        decimal_places (int): Кількість десяткових знаків, до яких потрібно округлити.
                              Має бути невід'ємним цілим числом.

    Returns:
        Decimal: Округлене число у вигляді об'єкта `Decimal`.
    """
    if not isinstance(decimal_places, int) or decimal_places < 0:
        # TODO i18n: Translatable message for developers
        raise ValueError("Кількість десяткових знаків (decimal_places) має бути невід'ємним цілим числом.")

    try:
        if not isinstance(number, Decimal):
            # Перетворення на рядок перед Decimal запобігає проблемам з точністю представлення float.
            # Наприклад, float(0.1) не є точно 0.1.
            number_decimal = Decimal(str(number))
        else:
            number_decimal = number
    except Exception as e: # Обробка можливих помилок перетворення на Decimal (наприклад, нечисловий рядок)
        # TODO i18n: Translatable message for developers
        raise ValueError(f"Не вдалося перетворити '{number}' на Decimal для округлення: {e}")


    # Створення квантизатора, наприклад, Decimal('0.01') для 2 десяткових знаків, Decimal('1') для 0 знаків.
    if decimal_places == 0:
        quantizer = Decimal("1")
    else:
        quantizer = Decimal("1e-" + str(decimal_places)) # Наприклад, "1e-2" для Decimal("0.01")

    return number_decimal.quantize(quantizer, rounding=ROUND_HALF_UP)


# --- Утиліти для роботи з колекціями ---

def chunk_list(data: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Розбиває список на менші підсписки (чанки) заданого розміру.
    Останній чанк може бути меншим, якщо загальна кількість елементів
    не ділиться націло на `chunk_size`.

    Приклад:
        `chunk_list([1, 2, 3, 4, 5], 2)` поверне `[[1, 2], [3, 4], [5]]`

    Args:
        data (List[Any]): Список для розбиття.
        chunk_size (int): Розмір кожного чанка. Повинен бути додатним цілим числом.

    Returns:
        List[List[Any]]: Список, що містить чанки (підсписки).

    Raises:
        ValueError: Якщо `chunk_size` не є додатним цілим числом.
    """
    if not isinstance(chunk_size, int) or chunk_size <= 0:
        # TODO i18n: Translatable message for developers
        raise ValueError("Розмір частини (chunk_size) повинен бути додатним цілим числом.")
    if not data: # Якщо вхідний список порожній, повертаємо порожній список чанків
        return []
    return [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]


def get_from_dict_or_object(data: Union[Dict[str, Any], object], key: str, default: Optional[Any] = None) -> Any:
    """
    Безпечно отримує значення за ключем зі словника або значення атрибута з об'єкта.
    Якщо ключ або атрибут не знайдено, повертає значення `default`.

    Ця функція корисна для уніфікованого доступу до даних, незалежно від того,
    чи вони представлені як словник (наприклад, дані з JSON) або як об'єкт.

    Args:
        data (Union[Dict[str, Any], object]): Словник або об'єкт, з якого потрібно отримати значення.
        key (str): Ключ (для словника) або назва атрибута (для об'єкта).
        default (Optional[Any]): Значення, яке повертається, якщо ключ або атрибут не знайдено.
                                 За замовчуванням `None`.

    Returns:
        Any: Отримане значення, або значення `default`, якщо ключ/атрибут не знайдено.
    """
    if isinstance(data, dict):
        return data.get(key, default) # Використовує метод .get() для словників
    else:
        return getattr(data, key, default) # Використовує getattr() для об'єктів


# Блок для демонстрації та базового тестування утиліт при прямому запуску модуля.
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
        logger.warning("Не вдалося імпортувати setup_logging. Використовується базова конфігурація логування для тестів utils.py.")

    logger.info("--- Демонстрація Допоміжних Утиліт Ядра (`core.utils`) ---")

    # Утиліти для рядків
    logger.info("\n--- Тестування `slugify` ---")
    test_slovak_text = "Тестування функції слагіфікації з українськими літерами: Привіт, Світ 123! Як справи, ҐЄІЇї?"
    logger.info(f"Оригінал: '{test_slovak_text}'\n  Слаг: '{slugify(test_slovak_text)}'")
    logger.info(f"Оригінал: '  --Багато--Роздільників--  і----ще'\n  Слаг: '{slugify('  --Багато--Роздільників--  і----ще')}'")
    logger.info(
        f"Оригінал: 'Спеціальні_Символи!@#$%^' (роздільник '_')\n  Слаг: '{slugify('Спеціальні_Символи!@#$%^', '_')}'")
    logger.info(f"Оригінал: 'Україна ҐЄІЇї! Супер.'\n  Слаг: '{slugify('Україна ҐЄІЇї! Супер.')}'")
    logger.info(f"Оригінал (порожній рядок): ''\n  Слаг: '{slugify('')}'")
    logger.info(f"Оригінал (лише роздільники): '---'\n  Слаг: '{slugify('---')}'")

    logger.info("\n--- Тестування `truncate_string` ---")
    logger.info(
        f"Обрізати 'Дуже довгий текст, який потрібно обрізати' (макс 20): '{truncate_string('Дуже довгий текст, який потрібно обрізати', 20)}'")
    logger.info(f"Обрізати 'Короткий текст' (макс 20): '{truncate_string('Короткий текст', 20)}'")
    logger.info(
        f"Обрізати 'Текст' (макс 2, суфікс '...'): '{truncate_string('Текст', 2, '...')}'")
    logger.info(
        f"Обрізати 'Текст' (макс 3, суфікс '...'): '{truncate_string('Текст', 3, '...')}'") # Точно дорівнює суфіксу
    logger.info(
        f"Обрізати 'Текст' (макс 5, суфікс '--'): '{truncate_string('Текст', 5, '--')}'")

    # Утиліти для дати та часу
    logger.info("\n--- Тестування `human_readable_timedelta` ---")
    test_deltas = [
        timedelta(days=3, hours=5, minutes=22, seconds=7), # 3 дні, 5 годин, 22 хвилини, 7 секунд
        timedelta(days=1, hours=1, minutes=1, seconds=1),   # 1 день, 1 година, 1 хвилина, 1 секунда
        timedelta(days=0, hours=2, minutes=3, seconds=4),   # 2 години, 3 хвилини, 4 секунди
        timedelta(days=0, hours=0, minutes=5, seconds=25),  # 5 хвилин, 25 секунд
        timedelta(days=4, seconds=0),                       # 4 дні
        timedelta(hours=23),                                # 23 години
        timedelta(minutes=59),                              # 59 хвилин
        timedelta(seconds=1),                               # 1 секунда
        timedelta(seconds=2),                               # 2 секунди
        timedelta(seconds=5),                               # 5 секунд
        timedelta(days=0),                                  # 0 секунд
        timedelta(days=21),                                 # 21 день
        timedelta(days=22),                                 # 22 дні
        timedelta(days=11),                                 # 11 днів
        timedelta(seconds=-10)                              # Від'ємна тривалість
    ]
    for i, delta_ex in enumerate(test_deltas):
        logger.info(f"  Приклад {i + 1} (timedelta: {delta_ex}): {human_readable_timedelta(delta_ex)}")

    # Числові утиліти
    logger.info("\n--- Тестування `round_decimal` ---")
    test_numbers_for_rounding = [
        (123.4567, 2, Decimal("123.46")),
        ("123.454", 2, Decimal("123.45")), # Тест з рядком
        (Decimal("123.999"), 2, Decimal("124.00")),
        (123.45, 0, Decimal("123")),
        (0.5, 0, Decimal("1")),
        (2.5, 0, Decimal("3")),
        (1.2345, 3, Decimal("1.235")),
        ("-1.2345", 3, Decimal("-1.234")), # Від'ємне число
        ("-1.2345", 2, Decimal("-1.23")),
        ("-2.5", 0, Decimal("-3")), # Округлення від'ємного -0.5 "вгору" від нуля
    ]
    for num, places, expected in test_numbers_for_rounding:
        result = round_decimal(num, places)
        status = "\033[92mУСПІХ\033[0m" if result == expected else "\033[91mПОМИЛКА\033[0m"
        logger.info(f"  Округлити {num} (тип: {type(num).__name__}) до {places} знаків: {result} (Очікувано: {expected}) - {status}")
    try:
        round_decimal("не число", 2)
    except ValueError as e:
        logger.info(f"  Перевірка помилки для round_decimal ('не число'): {e}")
    try:
        round_decimal(100, -1)
    except ValueError as e:
        logger.info(f"  Перевірка помилки для round_decimal (від'ємні decimal_places): {e}")


    # Утиліти для колекцій
    logger.info("\n--- Тестування `chunk_list` ---")
    example_list = list(range(13))
    logger.info(f"Розбиття списку {example_list} на частини розміром 4: {chunk_list(example_list, 4)}")
    logger.info(f"Розбиття списку {example_list} на частини розміром 3: {chunk_list(example_list, 3)}")
    logger.info(f"Розбиття порожнього списку [] на частини розміром 5: {chunk_list([], 5)}")
    try:
        chunk_list(example_list, 0)
    except ValueError as e:
        logger.info(f"  Перевірка помилки для chunk_list (розмір чанка 0): {e}")

    logger.info("\n--- Тестування `get_from_dict_or_object` ---")
    example_dict = {"назва": "Продукт А", "ціна": 150, "валюта": "UAH", "деталі": {"колір": "синій"}}
    logger.info(f"Зі словника 'ціна': {get_from_dict_or_object(example_dict, 'ціна')}")
    logger.info(
        f"Зі словника 'опис' (за замовчуванням 'Немає опису'): {get_from_dict_or_object(example_dict, 'опис', 'Немає опису')}")
    logger.info(
        f"Зі словника 'деталі.колір' (не підтримує вкладеність напряму): {get_from_dict_or_object(example_dict, 'деталі.колір', 'Не знайдено')}") # Показує обмеження

    class DemoObject:
        def __init__(self, name="Демонстраційний Об'єкт", version="1.0.0"):
            self.name = name
            self.version = version
            self.nested_obj = type("Nested", (), {"attr": "вкладений атрибут"})()

    demo_instance = DemoObject()
    logger.info(f"З об'єкта 'name': {get_from_dict_or_object(demo_instance, 'name')}")
    logger.info(
        f"З об'єкта 'author' (за замовчуванням 'Невідомий Автор'): {get_from_dict_or_object(demo_instance, 'author', 'Невідомий Автор')}")
    logger.info(
        f"З об'єкта 'nested_obj.attr' (не підтримує вкладеність напряму): {get_from_dict_or_object(demo_instance, 'nested_obj.attr', 'Не знайдено')}")

    logger.info("\nДемонстрацію допоміжних утиліт завершено.")
