# backend/app/src/config/security.py
# -*- coding: utf-8 -*-
"""
Цей модуль відповідає за налаштування безпеки додатку.
Включає параметри для JWT токенів, хешування паролів, політики CORS тощо.
"""

from passlib.context import CryptContext # type: ignore # Для хешування паролів
from typing import List, Union, Optional
from pydantic import HttpUrl

# Імпорт налаштувань додатку
from backend.app.src.config.settings import settings

# --- Налаштування хешування паролів ---
# Використовуємо CryptContext для визначення алгоритмів хешування.
# bcrypt є рекомендованим алгоритмом.
# `schemes` - список алгоритмів, які підтримуються (перший - дефолтний для нових хешів).
# `deprecated="auto"` - автоматично позначає старі алгоритми як застарілі
# (корисно при міграції з інших алгоритмів).
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Функції для роботи з паролями
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Перевіряє, чи співпадає звичайний пароль з захешованим."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Генерує хеш для пароля."""
    return pwd_context.hash(password)


# --- Параметри JWT токенів (взяті з settings.auth, оскільки вони стосуються автентифікації) ---
# SECRET_KEY для JWT береться з AuthSettings
SECRET_KEY = settings.auth.SECRET_KEY
ALGORITHM = settings.auth.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.auth.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.auth.REFRESH_TOKEN_EXPIRE_DAYS
# JWT_AUDIENCE = settings.app.JWT_AUDIENCE # Якщо використовується
# JWT_ISSUER = settings.app.JWT_ISSUER # Якщо використовується

# --- Налаштування CORS (Cross-Origin Resource Sharing) ---
# Беруться з settings.app.BACKEND_CORS_ORIGINS
# Ці налаштування будуть використовуватися в FastAPI CORS Middleware.
#
# from fastapi.middleware.cors import CORSMiddleware
#
# origins = settings.app.BACKEND_CORS_ORIGINS
# if not origins:
#     # Якщо список порожній, можна встановити значення за замовчуванням,
#     # наприклад, дозволити лише з того ж домену або нічого не дозволяти.
#     # Або ж, якщо FastAPI CORS Middleware не додається, то політика браузера
#     # за замовчуванням буде обмежувати cross-origin запити.
#     # Для розробки часто використовують ["*"] або конкретні локальні хости.
#     if settings.app.ENVIRONMENT == "development":
#         origins = ["http://localhost", "http://localhost:8080", "http://127.0.0.1", "http://127.0.0.1:8080"] # Приклад для Flutter Web dev
#     else:
#         origins = [] # Для production мають бути чітко вказані домени фронтенду

# `origins` будуть використовуватися в `main.py` при налаштуванні CORS Middleware.
# Тут ми їх просто можемо визначити або залишити для використання напряму з `settings`.
#
# Приклад, як це може використовуватися в main.py:
#
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from backend.app.src.config.settings import settings
#
# app = FastAPI()
#
# if settings.app.BACKEND_CORS_ORIGINS:
#     app.add_middleware(
#         CORSMiddleware,
#         allow_origins=[str(origin) for origin in settings.app.BACKEND_CORS_ORIGINS], # Дозволені джерела
#         allow_credentials=True, # Дозволяє cookies
#         allow_methods=["*"],    # Дозволені HTTP методи (GET, POST, PUT, DELETE, etc.)
#         allow_headers=["*"],    # Дозволені HTTP заголовки
#         # expose_headers=["Content-Disposition"], # Заголовки, які клієнт може читати
#     )
#
# Цей код тут лише для ілюстрації, він має бути в `main.py` або там, де створюється FastAPI app.

# --- Інші налаштування безпеки ---

# Налаштування для Security Headers (можуть додаватися через Middleware)
# Наприклад:
# X_FRAME_OPTIONS = "DENY"
# X_CONTENT_TYPE_OPTIONS = "nosniff"
# CONTENT_SECURITY_POLICY = "default-src 'self'; img-src *; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline';"
# STRICT_TRANSPORT_SECURITY = "max-age=31536000; includeSubDomains"
# REFERRER_POLICY = "strict-origin-when-cross-origin"
# PERMISSIONS_POLICY = "camera=(), microphone=(), geolocation=()"
#
# Ці політики також налаштовуються в Middleware в `main.py`.

# TODO: Розглянути необхідність констант для типів токенів (наприклад, "access", "refresh", "password_reset", "email_verify").
# TOKEN_TYPE_ACCESS = "access"
# TOKEN_TYPE_REFRESH = "refresh"
# ...

# TODO: Якщо використовуються API ключі для доступу до певних ендпоінтів,
# тут можна визначити механізми їх перевірки або зберігання (хоча зберігання - це більше до БД/сервісів).

# Все виглядає як хороший набір базових налаштувань та утиліт для безпеки.
# `pwd_context` для роботи з паролями.
# Константи для JWT, взяті з `settings`.
# Політики CORS та Security Headers налаштовуються на рівні FastAPI додатку,
# але тут можна визначити значення за замовчуванням або посилання на `settings`.
#
# Важливо, що `SECRET_KEY` має бути надійним і зберігатися в безпеці.
# Алгоритм JWT (HS256) є поширеним, але для асиметричного шифрування (RS256)
# потрібні були б публічний та приватний ключі.
#
# Все готово.
