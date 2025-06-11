# backend/app/src/utils/generators.py
# -*- coding: utf-8 -*-
"""
Модуль функцій-генераторів.

Цей модуль надає утиліти для генерації різноманітних даних,
таких як випадкові коди (числові, буквено-числові тощо) та
унікальні URL-дружні "слаги" (slugs) для ідентифікації ресурсів.
"""
import logging
import random
import string
import secrets
import re
from typing import Optional, List # Added List

# Attempt to import a slugify library, fallback to basic implementation
try:
    from slugify import slugify as awesome_slugify
except ImportError:
    awesome_slugify = None

# Configure logger for this module
logger = logging.getLogger(__name__)

def generate_random_code(length: int = 6, type: str = "numeric") -> str:
    """
    Генерує випадковий код заданої довжини та типу.

    Args:
        length: Бажана довжина коду. За замовчуванням 6.
        type: Тип символів для використання в коді.
              Опції: "numeric", "alphanumeric", "alpha_upper", "alpha_lower", "hex".
              За замовчуванням "numeric".

    Returns:
        Випадково згенерований рядок коду.
    Raises:
        ValueError: якщо довжина не є додатним числом або тип недійсний.
    """
    if not isinstance(length, int) or length <= 0:
        logger.error(f"Недійсна довжина для випадкового коду: {length}. Повинно бути додатне ціле число.")
        raise ValueError("Довжина повинна бути додатним цілим числом.")

    char_set = ""
    if type == "numeric":
        char_set = string.digits
    elif type == "alphanumeric":
        char_set = string.ascii_letters + string.digits
    elif type == "alpha_upper":
        char_set = string.ascii_uppercase
    elif type == "alpha_lower":
        char_set = string.ascii_lowercase
    elif type == "hex":
        char_set = string.hexdigits.lower()
    else:
        logger.error(f"Недійсний тип для випадкового коду: {type}.")
        raise ValueError("Вказано недійсний тип. Оберіть з 'numeric', 'alphanumeric', 'alpha_upper', 'alpha_lower', 'hex'.")

    if not char_set: # Невже це можливо, враховуючи перевірку вище? Але для безпеки...
        raise ValueError("Набір символів для генерації коду порожній.")

    try:
        code = ''.join(secrets.choice(char_set) for _ in range(length))
    except NameError: # 'secrets' може бути недоступним на деяких платформах Python (рідко)
        logger.warning("Модуль 'secrets' недоступний, використовується random.SystemRandom для генерації коду.")
        try:
            sys_random = random.SystemRandom() # Більш криптографічно стійкий, ніж random.choice
            code = ''.join(sys_random.choice(char_set) for _ in range(length))
        except AttributeError: # random.SystemRandom може бути недоступним на деяких екзотичних ОС
            logger.warning("random.SystemRandom недоступний, використовується базовий random.choice для генерації коду.")
            code = ''.join(random.choice(char_set) for _ in range(length))

    logger.debug(f"Згенеровано випадковий код типу '{type}' довжиною {length}: '{code[:3]}...'")
    return code

def generate_unique_slug(text: str, existing_slugs: Optional[List[str]] = None, max_length: int = 255) -> str:
    """
    Генерує URL-дружній "слаг" із заданого текстового рядка, забезпечуючи унікальність
    відносно необов'язкового списку існуючих слагів шляхом додавання лічильника за потреби.

    Args:
        text: Вхідний рядок для слагіфікації (наприклад, заголовок).
        existing_slugs: Необов'язковий список вже існуючих слагів для перевірки на унікальність.
        max_length: Максимально дозволена довжина для слага.

    Returns:
        Унікальний, URL-дружній рядок слага.
    """
    if not text: # Якщо текст порожній, генеруємо випадковий слаг
        return generate_random_code(length=8, type="alphanumeric").lower()

    if awesome_slugify:
        base_slug = awesome_slugify(text, max_length=max_length, word_boundary=True, save_order=True)
    else:
        text = re.sub(r'[^\w\s-]', '', text.lower().strip())
        text = re.sub(r'[-\s]+', '-', text)
        base_slug = text.strip('-')
        if len(base_slug) > max_length:
            trimmed_slug = base_slug[:max_length]
            last_hyphen = trimmed_slug.rfind('-')
            if last_hyphen > 0:
                base_slug = trimmed_slug[:last_hyphen]
            else:
                base_slug = trimmed_slug
        if not base_slug:
            return generate_random_code(length=8, type="alphanumeric").lower()

    if not existing_slugs:
        return base_slug

    slug = base_slug
    counter = 1
    while slug in existing_slugs:
        suffix = f"-{counter}"
        if len(base_slug) + len(suffix) > max_length:
            truncated_base_len = max_length - len(suffix)
            base_slug_for_suffix = base_slug[:truncated_base_len] if truncated_base_len > 0 else ""
            slug = f"{base_slug_for_suffix}{suffix}"
            if not base_slug_for_suffix: # Якщо навіть після обрізки база порожня
                 slug = f"slug-{counter}" # Використовуємо префікс "slug-"
        else:
            slug = f"{base_slug}{suffix}"
        counter += 1
        if counter > 1000: # Запобіжник від нескінченного циклу
            logger.warning(f"Не вдалося згенерувати унікальний слаг для '{text}' після 1000 спроб. Повертається слаг з випадковим суфіксом.")
            return f"{base_slug}-{generate_random_code(5, 'alphanumeric')}"

    logger.debug(f"Згенеровано слаг '{slug}' для тексту '{text}'.")
    return slug

if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- Демонстрація Утиліт Генерації Даних ---")

    logger.info("\n--- Генерація Випадкових Кодів ---")
    logger.info(f"Числовий (6): {generate_random_code(6, 'numeric')}")
    logger.info(f"Буквено-числовий (8): {generate_random_code(8, 'alphanumeric')}")
    logger.info(f"Великі літери (10): {generate_random_code(10, 'alpha_upper')}")
    logger.info(f"Малі літери (5): {generate_random_code(5, 'alpha_lower')}")
    logger.info(f"Шістнадцятковий (12): {generate_random_code(12, 'hex')}")
    try:
        generate_random_code(0)
    except ValueError as e:
        logger.info(f"Перехоплено очікувану помилку для довжини 0: {e}")
    try:
        generate_random_code(6, "invalid_type")
    except ValueError as e:
        logger.info(f"Перехоплено очікувану помилку для недійсного типу: {e}")

    logger.info("\n--- Генерація Унікальних Слагів ---")
    existing = ["myj-pershyj-post", "myj-pershyj-post-1", "insha-nazva"] # Приклад існуючих слагів

    title1 = "Мій перший пост!"
    slug1 = generate_unique_slug(title1, existing)
    logger.info(f"Заголовок: '{title1}' -> Слаг: '{slug1}'")
    assert slug1 not in existing
    existing.append(slug1)

    title2 = "Інша назва" # Має конфліктувати з "insha-nazva" після слагіфікації
    slug2 = generate_unique_slug(title2, existing)
    logger.info(f"Заголовок: '{title2}' -> Слаг: '{slug2}'")
    assert slug2 not in existing
    existing.append(slug2)

    title3 = "Абсолютно новий заголовок"
    slug3 = generate_unique_slug(title3, existing)
    logger.info(f"Заголовок: '{title3}' -> Слаг: '{slug3}'")
    assert slug3 not in existing
    existing.append(slug3)

    title4 = "Зі спеціальними --- символами & штуками"
    slug4 = generate_unique_slug(title4, existing)
    logger.info(f"Заголовок: '{title4}' -> Слаг: '{slug4}'")
    assert slug4 not in existing
    existing.append(slug4)

    title5_long = "Це дуже довгий заголовок, який точно перевищить максимальну довжину для слагів і має бути коректно обрізаний"
    slug5 = generate_unique_slug(title5_long, existing, max_length=50)
    logger.info(f"Заголовок: '{title5_long[:60]}...' -> Слаг (макс 50): '{slug5}' (Довжина: {len(slug5)})")
    assert len(slug5) <= 50
    assert slug5 not in existing
    existing.append(slug5)

    existing_for_trunc = ["korotka-nazva"]
    title6 = "Коротка Назва" # Конфлікт з "korotka-nazva"
    slug6 = generate_unique_slug(title6, existing_for_trunc, max_length=10) # Дуже мала довжина
    logger.info(f"Заголовок: '{title6}' -> Слаг (макс 10, з існуючим 'korotka-nazva'): '{slug6}' (Довжина: {len(slug6)})")
    assert len(slug6) <= 10 # Має бути щось типу "slug-1" або "k-1", "ko-1"
    assert slug6 not in existing_for_trunc
    existing_for_trunc.append(slug6)

    slug7 = generate_unique_slug("", existing)
    logger.info(f"Заголовок: '' -> Слаг: '{slug7}'")
    assert len(slug7) == 8 # Повертає випадковий код
    assert slug7 not in existing

    if awesome_slugify:
        logger.info("Використовується бібліотека 'python-slugify' для генерації слагів.")
    else:
        logger.warning("Необов'язкова бібліотека 'python-slugify' не знайдена. Використовується базова внутрішня функція слагіфікації.")
