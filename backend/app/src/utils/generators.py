# backend/app/src/utils/generators.py
# -*- coding: utf-8 -*-
"""Модуль функцій-генераторів.

Цей модуль надає утиліти для генерації різноманітних даних,
таких як випадкові коди (числові, буквено-числові тощо) та
унікальні URL-дружні "слаги" (slugs) для ідентифікації ресурсів.
Такі генератори корисні для створення OTP, кодів підтвердження,
унікальних ідентифікаторів, читабельних URL та іншого.
"""
import logging  # Для локального використання в __main__
import random
import re
import secrets
import string
from typing import List, Optional

# Імпорт централізованого логера проекту
from backend.app.src.config.logging_config import setup_logging # type: ignore
logger = setup_logging()

# Спроба імпортувати бібліотеку python-slugify.
# Якщо вона не встановлена, awesome_slugify буде None, і буде використано
# резервну базову реалізацію для генерації слагів.
try:
    from slugify import slugify as awesome_slugify
except ImportError:
    awesome_slugify = None
    logger.info(
        "Бібліотека 'python-slugify' не встановлена. "
        "Для генерації слагів буде використано базову реалізацію."
    )


def generate_random_code(length: int = 6, code_type: str = "numeric") -> str:
    """Генерує випадковий код заданої довжини та типу.

    Використовує криптографічно стійкий генератор `secrets.choice`, якщо доступний,
    з резервним переходом до `random.SystemRandom` та `random.choice`.

    Args:
        length: Бажана довжина коду. За замовчуванням 6.
        code_type: Тип символів для використання в коді. Можливі значення:
                   "numeric" (тільки цифри),
                   "alphanumeric" (букви та цифри),
                   "alpha_upper" (тільки великі літери),
                   "alpha_lower" (тільки малі літери),
                   "hex" (шістнадцяткові символи в нижньому регістрі).
                   За замовчуванням "numeric".

    Returns:
        Випадково згенерований рядок коду.

    Raises:
        ValueError: Якщо `length` не є додатним цілим числом,
                    або якщо вказано недійсний `code_type`.
    """
    if not isinstance(length, int) or length <= 0:
        logger.error("Недійсна довжина для випадкового коду: %s. Повинно бути додатне ціле число.", length)
        raise ValueError("Довжина коду повинна бути додатним цілим числом.")

    char_set_map = {
        "numeric": string.digits,
        "alphanumeric": string.ascii_letters + string.digits,
        "alpha_upper": string.ascii_uppercase,
        "alpha_lower": string.ascii_lowercase,
        "hex": string.hexdigits.lower(),
    }

    char_set = char_set_map.get(code_type)
    if not char_set:
        logger.error("Недійсний тип '%s' для випадкового коду.", code_type)
        raise ValueError(
            "Вказано недійсний тип коду. Оберіть з: "
            f"{', '.join(char_set_map.keys())}."
        )

    try:
        # Використання secrets для криптографічно надійних випадкових послідовностей
        code = "".join(secrets.choice(char_set) for _ in range(length))
    except AttributeError:  # 'secrets' може бути недоступним на дуже старих версіях Python або специфічних збірках
        logger.warning(
            "Модуль 'secrets' недоступний або не має методу 'choice'. "
            "Використовується random.SystemRandom для генерації коду."
        )
        try:
            sys_random = random.SystemRandom()  # Більш криптографічно стійкий, ніж random.choice
            code = "".join(sys_random.choice(char_set) for _ in range(length))
        except AttributeError:  # random.SystemRandom може бути недоступним на деяких екзотичних ОС
            logger.warning(
                "random.SystemRandom недоступний. "
                "Використовується базовий random.choice для генерації коду (не рекомендовано для безпеки)."
            )
            code = "".join(random.choice(char_set) for _ in range(length))

    logger.debug("Згенеровано випадковий код типу '%s' довжиною %d: '%s...'", code_type, length, code[:3])
    return code


def generate_unique_slug(
    text: str,
    existing_slugs: Optional[List[str]] = None,
    max_length: int = 255,
    default_slug_prefix: str = "slug"
) -> str:
    """Генерує URL-дружній "слаг" із заданого тексту.

    Забезпечує унікальність відносно необов'язкового списку існуючих слагів
    шляхом додавання числового суфікса (-1, -2, ...) за потреби.
    Якщо бібліотека `python-slugify` встановлена, використовує її для кращої
    транслітерації та обробки символів. В іншому випадку використовує базову
    реалізацію на основі регулярних виразів.

    Args:
        text: Вхідний рядок для створення слага (наприклад, заголовок статті).
        existing_slugs: Необов'язковий список вже існуючих слагів для перевірки унікальності.
        max_length: Максимально дозволена довжина для згенерованого слага.
        default_slug_prefix: Префікс для слага, якщо вхідний текст порожній або
                             після обробки стає порожнім (наприклад, "slug").

    Returns:
        Унікальний, URL-дружній рядок слага, що не перевищує `max_length`.
    """
    if not text or not text.strip():
        logger.debug("Вхідний текст для генерації слага порожній. Генерується випадковий слаг.")
        # Генеруємо випадковий слаг, якщо вхідний текст порожній
        return generate_random_code(length=12, code_type="alphanumeric").lower()

    # Генерація базового слага
    if awesome_slugify:
        # Використовуємо python-slugify, якщо доступно
        base_slug = awesome_slugify(text, max_length=max_length, word_boundary=True, save_order=True)
    else:
        # Базова реалізація слагіфікації
        slug_text = text.lower().strip()
        slug_text = re.sub(r"[^\w\s-]", "", slug_text)  # Видалення не алфавітно-цифрових символів (крім пробілів та дефісів)
        slug_text = re.sub(r"[-\s]+", "-", slug_text)   # Заміна пробілів та множинних дефісів на один дефіс
        slug_text = slug_text.strip("-")                # Видалення дефісів на початку/кінці
        base_slug = slug_text[:max_length]              # Обрізка до максимальної довжини

        # Додаткова обрізка, щоб не розрізати слово, якщо можливо
        if len(base_slug) == max_length and base_slug.count("-") > 0:
            last_hyphen_pos = base_slug.rfind("-")
            # Якщо останній дефіс не на самому кінці і не є єдиним символом
            if last_hyphen_pos > 0 and last_hyphen_pos < max_length -1 :
                base_slug = base_slug[:last_hyphen_pos]

    # Якщо після обробки базовий слаг порожній (наприклад, вхідний текст складався тільки зі спецсимволів)
    if not base_slug:
        logger.debug(
            "Базовий слаг виявився порожнім після обробки тексту '%s'. Генерується випадковий слаг.", text
        )
        return f"{default_slug_prefix}-{generate_random_code(length=8, code_type='alphanumeric').lower()}"


    # Забезпечення унікальності, якщо надано список існуючих слагів
    if existing_slugs is None:
        existing_slugs = []

    current_slug = base_slug
    counter = 1
    # Максимальна кількість ітерацій для уникнення нескінченного циклу
    max_attempts = 1000

    while current_slug in existing_slugs:
        if counter >= max_attempts:
            logger.warning(
                "Не вдалося згенерувати унікальний слаг для тексту '%s' після %d спроб. "
                "Додається випадковий суфікс.", text, max_attempts
            )
            # Додаємо короткий випадковий суфікс для забезпечення унікальності
            random_suffix = generate_random_code(5, "alphanumeric").lower()
            current_slug = f"{base_slug[:max_length - len(random_suffix) - 1]}-{random_suffix}"
            # Переконуємось, що він все ще не перевищує max_length
            current_slug = current_slug[:max_length]
            break # Виходимо з циклу

        suffix = f"-{counter}"
        potential_slug_len = len(base_slug) + len(suffix)

        if potential_slug_len > max_length:
            # Якщо додавання суфікса перевищує максимальну довжину, обрізаємо базовий слаг
            available_len_for_base = max_length - len(suffix)
            # Переконуємося, що доступна довжина для базового слага не від'ємна
            trimmed_base_slug = base_slug[:available_len_for_base] if available_len_for_base > 0 else ""
            current_slug = f"{trimmed_base_slug}{suffix}"
            # Якщо після обрізки базовий слаг став порожнім, використовуємо префікс
            if not trimmed_base_slug:
                current_slug = f"{default_slug_prefix}{suffix}"[:max_length]
        else:
            current_slug = f"{base_slug}{suffix}"

        counter += 1

    logger.debug("Згенеровано слаг '%s' для тексту '%s'.", current_slug, text)
    return current_slug


if __name__ == "__main__":
    # Налаштування базового логування для демонстрації, якщо ще не налаштовано.
    if not logging.getLogger().hasHandlers(): # Перевіряємо, чи є вже обробники у кореневого логера
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    # Використовуємо логер модуля для повідомлень в __main__
    main_logger = logging.getLogger(__name__) # Отримуємо логер для __main__ контексту
    main_logger.info("--- Демонстрація Утиліт Генерації Даних ---")

    main_logger.info("\n--- Генерація Випадкових Кодів ---")
    main_logger.info("Числовий (6): %s", generate_random_code(6, 'numeric'))
    main_logger.info("Буквено-числовий (8): %s", generate_random_code(8, 'alphanumeric'))
    main_logger.info("Великі літери (10): %s", generate_random_code(10, 'alpha_upper'))
    main_logger.info("Малі літери (5): %s", generate_random_code(5, 'alpha_lower'))
    main_logger.info("Шістнадцятковий (12): %s", generate_random_code(12, 'hex'))
    try:
        generate_random_code(0)
    except ValueError as e:
        main_logger.info("Перехоплено очікувану помилку для довжини 0: %s", e)
    try:
        generate_random_code(6, "invalid_type")
    except ValueError as e:
        main_logger.info("Перехоплено очікувану помилку для недійсного типу: %s", e)

    main_logger.info("\n--- Генерація Унікальних Слагів ---")
    existing = ["myj-pershyj-post", "myj-pershyj-post-1", "insha-nazva"] # Приклад існуючих слагів

    title1 = "Мій перший пост!"
    slug1 = generate_unique_slug(title1, existing)
    main_logger.info("Заголовок: '%s' -> Слаг: '%s'", title1, slug1)
    assert slug1 not in existing, f"Згенерований слаг '{slug1}' вже існує."
    existing.append(slug1)

    title2 = "Інша назва" # Має конфліктувати з "insha-nazva" після слагіфікації
    slug2 = generate_unique_slug(title2, existing)
    main_logger.info("Заголовок: '%s' -> Слаг: '%s'", title2, slug2)
    assert slug2 not in existing, f"Згенерований слаг '{slug2}' вже існує."
    existing.append(slug2)

    title3 = "Абсолютно новий заголовок"
    slug3 = generate_unique_slug(title3, existing)
    main_logger.info("Заголовок: '%s' -> Слаг: '%s'", title3, slug3)
    assert slug3 not in existing, f"Згенерований слаг '{slug3}' вже існує."
    existing.append(slug3)

    title4 = "Зі спеціальними --- символами & штуками"
    slug4 = generate_unique_slug(title4, existing)
    main_logger.info("Заголовок: '%s' -> Слаг: '%s'", title4, slug4)
    assert slug4 not in existing, f"Згенерований слаг '{slug4}' вже існує."
    existing.append(slug4)

    title5_long = "Це дуже довгий заголовок, який точно перевищить максимальну довжину для слагів і має бути коректно обрізаний"
    slug5 = generate_unique_slug(title5_long, existing, max_length=50)
    main_logger.info("Заголовок: '%s...' -> Слаг (макс 50): '%s' (Довжина: %d)", title5_long[:60], slug5, len(slug5))
    assert len(slug5) <= 50, f"Довжина слага '{slug5}' ({len(slug5)}) перевищує максимальну (50)."
    assert slug5 not in existing, f"Згенерований слаг '{slug5}' вже існує."
    existing.append(slug5)

    existing_for_trunc = ["korotka-n"] # Змінено, щоб не конфліктувати з логікою обрізки
    title6 = "Коротка Назва"
    # Тест, де базовий слаг "korotka-nazva" обрізається до "korotka-n" (max_length=10)
    # Потім додається суфікс, наприклад "-1", що робить "korotka-n-1" (12 символів)
    # Це перевищить max_length=10. Логіка має обрізати "korotka-n" до "korotk-1" або щось подібне.
    slug6 = generate_unique_slug(title6, existing_for_trunc, max_length=10, default_slug_prefix="slug")
    main_logger.info("Заголовок: '%s' -> Слаг (макс 10, існуючий '%s'): '%s' (Довжина: %d)",
                     title6, existing_for_trunc[0], slug6, len(slug6))
    assert len(slug6) <= 10, f"Довжина слага '{slug6}' ({len(slug6)}) перевищує максимальну (10)."
    assert slug6 not in existing_for_trunc, f"Згенерований слаг '{slug6}' вже існує."
    existing_for_trunc.append(slug6)

    slug7 = generate_unique_slug("", existing) # Тест для порожнього рядка
    main_logger.info("Заголовок: '' -> Слаг: '%s'", slug7)
    assert len(slug7) == 12, f"Довжина випадкового слага для порожнього рядка має бути 12, а не {len(slug7)}."
    assert slug7 not in existing, f"Згенерований випадковий слаг '{slug7}' вже існує."

    if awesome_slugify:
        main_logger.info("Використовується бібліотека 'python-slugify' для генерації слагів.")
    else:
        main_logger.warning(
            "Необов'язкова бібліотека 'python-slugify' не знайдена. "
            "Використовується базова внутрішня функція слагіфікації."
        )
