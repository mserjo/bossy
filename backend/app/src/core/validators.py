# backend/app/src/core/validators.py
# -*- coding: utf-8 -*-
"""
Цей модуль призначений для визначення кастомних функцій-валідаторів даних,
які можуть використовуватися в Pydantic схемах або в інших частинах системи,
де потрібна специфічна логіка валідації, що виходить за межі стандартних
можливостей Pydantic або типів даних.

Pydantic вже надає потужні інструменти для валідації (Field, @field_validator,
@model_validator, типи даних як EmailStr, HttpUrl тощо).
Цей файл може бути корисним для:
- Дуже специфічних валідаторів, які використовуються в кількох місцях.
- Валідаторів, що взаємодіють з зовнішніми сервісами або базою даних
  (хоча така логіка частіше знаходиться в сервісному шарі).
- Складних валідаторів форматів (наприклад, номерів телефонів для різних країн,
  поштових індексів, якщо стандартних бібліотек недостатньо).
"""

import re
from typing import Any, Optional, List


# from phonenumbers import parse as parse_phone_number, is_valid_number, NumberParseException # type: ignore # Приклад з бібліотекою

# Імпорт логгера (якщо потрібне логування під час валідації)
# from backend.app.src.config.logging import logger

# --- Приклади кастомних валідаторів ---

def is_valid_username_format(username: str) -> bool:
    """
    Перевіряє, чи відповідає ім'я користувача (логін) заданому формату.
    Наприклад: літери, цифри, підкреслення, дефіс, довжина від 3 до 30 символів.
    """
    if not (3 <= len(username) <= 30):
        return False
    # Дозволені символи: літери (будь-якої мови), цифри, _, -
    # \w еквівалентно [a-zA-Z0-9_] для ASCII, але може включати інші символи Unicode.
    # Для строгості можна вказати конкретні діапазони.
    # Поки що проста перевірка на основі \w та дефісу.
    if not re.match(r"^[a-zA-Z0-9_-]+$", username): # Додано a-zA-Z для явного вказання латиниці
        return False
    return True

# Приклад використання в Pydantic схемі:
# from pydantic import field_validator
# class UserCreateSchema(BaseModel):
#     username: str
#     @field_validator('username')
#     def username_must_be_valid(cls, value):
#         if not is_valid_username_format(value):
#             raise ValueError("Некоректний формат імені користувача.")
#         return value


def is_strong_password(password: str, min_length: int = 8) -> List[str]:
    """
    Перевіряє надійність пароля за кількома критеріями.
    Повертає список повідомлень про помилки, якщо пароль не відповідає вимогам,
    або порожній список, якщо пароль надійний.
    """
    errors: List[str] = []
    if len(password) < min_length:
        errors.append(f"Пароль повинен містити щонайменше {min_length} символів.")
    if not re.search(r"[a-z]", password): # Маленькі літери
        errors.append("Пароль повинен містити хоча б одну маленьку літеру.")
    if not re.search(r"[A-Z]", password): # Великі літери
        errors.append("Пароль повинен містити хоча б одну велику літеру.")
    if not re.search(r"[0-9]", password): # Цифри
        errors.append("Пароль повинен містити хоча б одну цифру.")
    # Можна додати перевірку на спецсимволи:
    # if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
    #     errors.append("Пароль повинен містити хоча б один спеціальний символ.")
    return errors

# Приклад використання в Pydantic схемі:
# class PasswordSchema(BaseModel):
#     password: str
#     @field_validator('password')
#     def password_strength_check(cls, value):
#         strength_errors = is_strong_password(value)
#         if strength_errors:
#             # Можна об'єднати помилки в один рядок або кинути кастомний виняток
#             raise ValueError(". ".join(strength_errors))
#         return value


# def validate_phone_number(phone_number: str, region: Optional[str] = None) -> bool:
#     """
#     Перевіряє валідність номера телефону за допомогою бібліотеки phonenumbers.
#     :param phone_number: Номер телефону для перевірки.
#     :param region: Код країни (наприклад, "UA", "US"), якщо формат номера не міжнародний.
#     :return: True, якщо номер валідний, інакше False.
#     """
#     try:
#         parsed_number = parse_phone_number(phone_number, region)
#         return is_valid_number(parsed_number)
#     except NumberParseException:
#         return False
#     except Exception as e:
#         # logger.error(f"Помилка валідації номера телефону '{phone_number}': {e}")
#         return False

# Приклад використання в Pydantic:
# class UserProfileUpdate(BaseModel):
#     phone: Optional[str] = None
#     @field_validator('phone')
#     def phone_must_be_valid_or_none(cls, value):
#         if value is not None and not validate_phone_number(value, "UA"): # Приклад для України
#             raise ValueError("Некоректний формат номера телефону.")
#         return value

# TODO: Додати інші специфічні валідатори, якщо вони будуть потрібні
# для бізнес-логіки додатку.
# Наприклад:
# - Валідатор для cron-виразів (можна використовувати бібліотеку `croniter`).
# - Валідатор для перевірки, чи є рядок валідним JSON.
# - Валідатори для специфічних форматів ID або кодів, що використовуються в системі.
#
# На даному етапі цей файл містить приклади валідаторів для формату імені користувача
# та надійності пароля. Валідатор для номера телефону (з використанням `phonenumbers`)
# закоментований, оскільки потребує встановлення додаткової бібліотеки.
#
# Якщо валідатори стають дуже специфічними для певних схем Pydantic,
# їх краще визначати безпосередньо в цих схемах за допомогою `@field_validator`
# або `@model_validator`. Цей файл призначений для більш загальних валідаторів,
# які можуть повторно використовуватися.
#
# Все готово для базової структури.
# Конкретні валідатори будуть додаватися за потреби.
#
# Все готово.
