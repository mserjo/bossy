# backend/app/src/core/utils.py
# -*- coding: utf-8 -*-
"""
Цей модуль містить різноманітні утилітарні функції, які можуть використовуватися
в різних частинах додатку. Наприклад, функції для роботи з датами, рядками,
генерації випадкових значень, хешування (хоча для паролів вже є в security.py) тощо.
"""

import uuid
import random
import string
from datetime import datetime, timezone, timedelta
from typing import Optional, Any, Dict
import hashlib # Для хешування, якщо потрібно (не для паролів)
# import re # Для регулярних виразів, якщо потрібно

# --- Робота з датами та часом ---

def get_current_utc_timestamp() -> datetime:
    """Повертає поточний час в UTC."""
    return datetime.now(timezone.utc)

def datetime_to_iso_string(dt: datetime) -> str:
    """Конвертує datetime об'єкт в ISO 8601 рядок."""
    return dt.isoformat()

def iso_string_to_datetime(iso_str: str) -> Optional[datetime]:
    """Конвертує ISO 8601 рядок в datetime об'єкт."""
    try:
        return datetime.fromisoformat(iso_str)
    except (ValueError, TypeError):
        return None

def calculate_expiration_date(minutes: int) -> datetime:
    """Розраховує дату закінчення терміну дії, додаючи хвилини до поточного часу UTC."""
    return get_current_utc_timestamp() + timedelta(minutes=minutes)

def calculate_expiration_date_days(days: int) -> datetime:
    """Розраховує дату закінчення терміну дії, додаючи дні до поточного часу UTC."""
    return get_current_utc_timestamp() + timedelta(days=days)


# --- Генерація випадкових значень ---

def generate_random_string(length: int = 32, chars: str = string.ascii_letters + string.digits) -> str:
    """Генерує випадковий рядок заданої довжини з вказаних символів."""
    if length <= 0:
        raise ValueError("Довжина рядка має бути позитивним числом.")
    return ''.join(random.choice(chars) for _ in range(length))

def generate_unique_code(length: int = 8, prefix: str = "") -> str:
    """
    Генерує унікальний код (наприклад, для запрошень, кодів підтвердження).
    Використовує UUID4 для унікальності та скорочує його.
    Або можна використовувати `generate_random_string` з більшою довжиною.
    Для коротких кодів, які мають бути унікальними, потрібна перевірка на колізії в БД.
    Ця функція просто генерує випадковий рядок.
    """
    # Варіант 1: На основі UUID (гарантує більшу унікальність, але довший)
    # code = str(uuid.uuid4()).replace('-', '')[:length]
    # Варіант 2: Випадковий рядок (коротший, але можливі колізії для малих довжин)
    # Для кодів запрошень, які мають бути унікальними, краще генерувати
    # достатньо довгий випадковий рядок або використовувати UUID.
    # Якщо потрібен короткий, то перевірка унікальності в БД обов'язкова.
    # Поки що генеруємо випадковий рядок.
    # Для кодів запрошень (наприклад, 8-12 символів) краще використовувати
    # алфавіт без неоднозначних символів (0/O, 1/I/l).
    safe_chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789" # Без 0, O, 1, I, l
    code = generate_random_string(length, chars=safe_chars)
    return f"{prefix}{code}".upper() # Робимо великими літерами для консистентності

def generate_uuid() -> uuid.UUID:
    """Генерує новий UUID v4."""
    return uuid.uuid4()


# --- Хешування (загального призначення, не для паролів) ---
# Для паролів використовуйте функції з `backend.app.src.config.security`.

def simple_sha256_hash(data: str) -> str:
    """Створює SHA256 хеш для рядка."""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


# --- Робота з рядками ---

def slugify_string(text: str, separator: str = "-") -> str:
    """
    Створює "slug" з рядка: переводить в нижній регістр, замінює пробіли
    та спецсимволи на розділювач.
    Потребує більш надійної реалізації для різних мов та символів.
    Можна використовувати бібліотеку `python-slugify`.
    """
    # Дуже проста реалізація, потребує покращення.
    # Для більш надійної реалізації, особливо з Unicode, розгляньте python-slugify.
    import re
    text = str(text).strip().lower() # Переконуємося, що це рядок, прибираємо зайві пробіли
    text = re.sub(r'[^\w\s-]', '', text) # Видаляємо не-алфавітно-цифрові (крім пробілів та дефісів)
    text = re.sub(r'[\s._-]+', separator, text) # Замінюємо пробіли, крапки, підкреслення, дефіси на один розділювач
    text = re.sub(r'%s+' % separator, separator, text) # Видаляємо дублікати розділювача
    return text.strip(separator)

# --- Валідація cron-виразів ---
def is_valid_cron_expression(cron_expression: str) -> bool:
    """
    Перевіряє, чи є рядок валідним cron-виразом (базова перевірка).
    Для повної валідації краще використовувати бібліотеку типу `croniter`.
    """
    if not isinstance(cron_expression, str):
        return False
    parts = cron_expression.split()
    if len(parts) not in [5, 6]: # 5 частин (хв, год, день місяця, місяць, день тижня) або 6 (з секундами на початку)
        return False
    # TODO: Додати більш детальну перевірку діапазонів та символів для кожної частини,
    #       або інтегрувати `croniter.is_valid()`.
    # from croniter import croniter
    # try:
    #     return croniter.is_valid(cron_expression)
    # except: # ImportError або інші помилки від croniter
    #     # Проста перевірка, якщо croniter недоступний
    #     # (цей блок лише для прикладу, croniter має бути в залежностях, якщо використовується)
    #     pass
    return True # Поки що дуже базова перевірка

# --- Робота зі словниками/JSON ---

def deep_update_dict(source: Dict[Any, Any], overrides: Dict[Any, Any]) -> Dict[Any, Any]:
    """
    Рекурсивно оновлює словник `source` значеннями зі словника `overrides`.
    Якщо значення є вкладеним словником, воно також оновлюється рекурсивно.
    """
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(source.get(key), dict):
            source[key] = deep_update_dict(source[key], value)
        else:
            source[key] = value
    return source

# --- Інші утиліти ---

# def get_object_or_404(db_session: Any, model: Any, object_id: Any, error_message: Optional[str] = None) -> Any:
#     """
#     Допоміжна функція для отримання об'єкта з БД або викидання NotFoundException.
#     Потребує адаптації для асинхронних сесій та SQLAlchemy 2.0.
#     Краще реалізовувати таку логіку в базовому репозиторії або сервісах.
#     """
#     # obj = db_session.query(model).get(object_id) # Для синхронного SQLAlchemy
#     # if obj is None:
#     #     from backend.app.src.core.exceptions import NotFoundException # Уникаємо циклічного імпорту
#     #     detail = error_message or f"{model.__name__} з ID {object_id} не знайдено."
#     #     raise NotFoundException(detail=detail)
#     # return obj
#     pass

# TODO: Додати інші корисні утиліти за потреби:
# - Робота з файловою системою (створення шляхів, перевірка існування тощо).
# - Форматування чисел, валют.
# - Утиліти для пагінації (розрахунок зміщення, ліміту).
# - Функції для роботи з Enum.
# - Якщо потрібна більш складна логіка slugify, краще використовувати готову бібліотеку.
#
# `generate_unique_code` - важливо пам'ятати про перевірку на колізії в БД,
# якщо генеруються короткі коди, які мають бути строго унікальними.
# Для довгих випадкових рядків (наприклад, 32+ символи) ймовірність колізії низька.
#
# `deep_update_dict` може бути корисною для оновлення JSONB полів або конфігурацій.
#
# `get_object_or_404` - типова утиліта, але її реалізація залежить від ORM та
# асинхронності, і часто краще мати її в базовому репозиторії.
#
# Все виглядає як хороший набір базових утиліт.
# `get_current_utc_timestamp` - важливо для консистентності часових міток.
# Функції для конвертації дат в/з ISO рядків корисні для API.
# Генератори випадкових рядків та UUID також часто потрібні.
#
# Все готово.
