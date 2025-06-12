# backend/app/src/config/security.py
# -*- coding: utf-8 -*-
# # Модуль конфігурацій та утиліт безпеки для FastAPI програми Kudos (Virtus).
# #
# # Відповідає за створення та валідацію JWT (JSON Web Tokens) для автентифікації
# # та авторизації користувачів, включаючи токени доступу (access tokens) та
# # токени оновлення (refresh tokens). Використовує налаштування безпеки
# # (секретні ключі, алгоритми, час життя токенів, видавець, аудиторія)
# # з модуля `backend.app.src.config.settings`.
# #
# # Примітка: Утиліти для хешування паролів знаходяться в `backend.app.src.utils.hash`.
# # Налаштування CORS політик відбувається в головному файлі програми (`main.py`)
# # з використанням значень з `settings.py`.

from datetime import datetime, timedelta, timezone
from typing import Optional, Any
# `jose.exceptions` імпортується для типізації конкретних помилок JWT, що дозволяє їх точно обробляти.
from jose import jwt, JWTError, exceptions as jose_exceptions
# from passlib.context import CryptContext # Видалено, оскільки хешування паролів перенесено до `utils.hash`

# Абсолютний імпорт налаштувань та логера
from backend.app.src.config.settings import settings
from backend.app.src.config.logging import get_logger

# Отримання логера для цього модуля
logger = get_logger(__name__)

# --- Утиліти для роботи з JWT (JSON Web Token) ---

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Створює новий JWT токен доступу (access token).

    Токен містить надані дані (`data`), час закінчення терміну дії (`exp`),
    тип токена (`type: "access"`), видавця (`iss` з `settings.JWT_ISSUER`)
    та аудиторію (`aud` з `settings.JWT_AUDIENCE`).

    Args:
        data (dict): Дані для кодування в токен (наприклад, ідентифікатор користувача як `sub`).
        expires_delta (Optional[timedelta]): Тривалість життя токена.
                                             Якщо не надано, використовується значення
                                             `settings.ACCESS_TOKEN_EXPIRE_MINUTES`.

    Returns:
        str: Закодований JWT токен доступу у вигляді рядка.
    """
    to_encode = data.copy() # Копіюємо дані, щоб не модифікувати оригінальний словник
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    # Додавання стандартних та кастомних клеймів
    to_encode.update({
        "exp": expire, # Час закінчення терміну дії токена (обов'язковий для JOSE)
        "type": "access", # Кастомний клейм для розрізнення типів токенів
        "iss": settings.JWT_ISSUER, # Видавець токена (RFC 7519)
        "aud": settings.JWT_AUDIENCE, # Аудиторія токена (RFC 7519)
    })
    # Кодування токена з використанням секретного ключа та алгоритму з налаштувань
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Створює новий JWT токен оновлення (refresh token).

    Токен містить надані дані (`data`), час закінчення терміну дії (`exp`),
    тип токена (`type: "refresh"`), видавця (`iss`) та аудиторію (`aud`).

    Args:
        data (dict): Дані для кодування в токен (наприклад, ідентифікатор користувача як `sub`).
        expires_delta (Optional[timedelta]): Тривалість життя токена.
                                             Якщо не надано, використовується значення
                                             `settings.REFRESH_TOKEN_EXPIRE_DAYS`.

    Returns:
        str: Закодований JWT токен оновлення у вигляді рядка.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    # Додавання стандартних та кастомних клеймів
    to_encode.update({
        "exp": expire,
        "type": "refresh", # Кастомний клейм для розрізнення типів токенів
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
    })
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> Optional[dict[str, Any]]:
    """
    Декодує JWT токен, перевіряє його валідність (включаючи термін дії, видавця, аудиторію)
    та повертає його корисне навантаження (payload).

    Args:
        token (str): JWT токен для декодування.

    Returns:
        Optional[dict[str, Any]]: Словник з корисним навантаженням токена, якщо він дійсний
                                  та відповідає всім критеріям перевірки (секретний ключ,
                                  алгоритм, термін дії, видавець, аудиторія).
                                  Повертає `None` у разі будь-якої помилки декодування або валідації.
    """
    try:
        # Декодування токена з валідацією аудиторії та видавця
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY, # Секретний ключ для перевірки підпису
            algorithms=[settings.JWT_ALGORITHM], # Список дозволених алгоритмів
            audience=settings.JWT_AUDIENCE, # Очікувана аудиторія
            issuer=settings.JWT_ISSUER      # Очікуваний видавець
        )
        return payload
    except jose_exceptions.ExpiredSignatureError:
        # i18n: Log message for developers/security audit
        logger.warning("Помилка декодування JWT: термін дії токена закінчився (ExpiredSignatureError).")
        return None
    except jose_exceptions.InvalidAudienceError:
        # i18n: Log message for developers/security audit
        logger.warning("Помилка декодування JWT: недійсна аудиторія (InvalidAudienceError).")
        return None
    except jose_exceptions.InvalidIssuerError:
        # i18n: Log message for developers/security audit
        logger.warning("Помилка декодування JWT: недійсний видавець (InvalidIssuerError).")
        return None
    except jose_exceptions.InvalidAlgorithmError as e:
        # i18n: Log message for developers/security audit
        logger.error(f"Помилка декодування JWT: недійсний алгоритм. Очікувався '{settings.JWT_ALGORITHM}', але токен використовує інший. Деталі: {e}", exc_info=settings.DEBUG)
        return None
    except JWTError as e: # Загальна помилка JWT (наприклад, недійсний підпис, неправильний формат токена)
        # i18n: Log message for developers/security audit
        logger.warning(f"Загальна помилка декодування JWT: {e}", exc_info=settings.DEBUG)
        return None
    except Exception as e: # Інші непередбачені помилки під час декодування
        # i18n: Log message for developers/security audit
        logger.error(f"Неочікувана помилка при декодуванні JWT: {e}", exc_info=True) # True для повного трасування
        return None


# Блок для демонстрації або тестування функціональності цього модуля
if __name__ == "__main__":
    # Для перегляду логів помилок з decode_token,
    # потрібно налаштувати логування, якщо воно ще не налаштоване глобально.
    try:
        from backend.app.src.config.logging import setup_logging
        if settings.LOG_TO_FILE: # Налаштовуємо логування у файл, якщо вказано
            log_file_path = settings.LOG_DIR / f"{Path(__file__).stem}_test.log"
            setup_logging(log_file_path=log_file_path)
        else:
            setup_logging() # Стандартне логування в консоль
        logger.info("Логування налаштовано для тестування security.py.")
    except ImportError:
        # Якщо setup_logging не доступний, використовуємо базове налаштування
        import logging as base_logging
        base_logging.basicConfig(level=base_logging.INFO)
        logger.warning("Не вдалося імпортувати setup_logging. Використовується базова конфігурація логування для тестів security.py.")

    # --- Тестування створення та декодування JWT ---
    logger.info("--- Тестування створення та декодування JWT ---")
    user_data_payload = {"sub": "testuser@example.com", "user_id": 123, "role": "user"}

    # Токен доступу
    access_token = create_access_token(user_data_payload)
    logger.info(f"Згенерований токен доступу: {access_token}")
    decoded_access_payload = decode_token(access_token)
    if decoded_access_payload:
        logger.info(f"Декодоване корисне навантаження токена доступу: {decoded_access_payload}")
        exp_timestamp = decoded_access_payload.get('exp')
        if exp_timestamp:
            logger.info(f"Токен доступу закінчується (UTC): {datetime.fromtimestamp(exp_timestamp, timezone.utc)}")
    else:
        logger.warning("Не вдалося декодувати токен доступу (або він недійсний/прострочений).")

    # Токен оновлення
    refresh_token = create_refresh_token(user_data_payload)
    logger.info(f"\nЗгенерований токен оновлення: {refresh_token}")
    decoded_refresh_payload = decode_token(refresh_token)
    if decoded_refresh_payload:
        logger.info(f"Декодоване корисне навантаження токена оновлення: {decoded_refresh_payload}")
        exp_timestamp = decoded_refresh_payload.get('exp')
        if exp_timestamp:
            logger.info(f"Токен оновлення закінчується (UTC): {datetime.fromtimestamp(exp_timestamp, timezone.utc)}")
    else:
        logger.warning("Не вдалося декодувати токен оновлення (або він недійсний/прострочений).")

    # Тестування простроченого токена
    logger.info("\n--- Тестування простроченого токена ---")
    expired_access_token = create_access_token(user_data_payload, expires_delta=timedelta(seconds=-3600)) # Прострочений на 1 годину
    logger.info(f"Згенерований прострочений токен доступу: {expired_access_token}")
    decoded_expired_payload = decode_token(expired_access_token)
    if decoded_expired_payload:
        logger.error(f"ПОМИЛКА ТЕСТУ: Декодовано прострочений токен: {decoded_expired_payload}")
    else:
        logger.info("КОРЕКТНО: Не вдалося декодувати прострочений токен доступу (ExpiredSignatureError).")

    # Тестування недійсного токена (неправильний підпис)
    logger.info("\n--- Тестування недійсного токена (неправильний підпис) ---")
    invalid_signature_token = access_token[:-5] + "XXXXX" # Змінити частину підпису
    logger.info(f"Недійсний токен (змінений підпис): {invalid_signature_token}")
    decoded_invalid_payload = decode_token(invalid_signature_token)
    if decoded_invalid_payload:
        logger.error(f"ПОМИЛКА ТЕСТУ: Декодовано токен з недійсним підписом: {decoded_invalid_payload}")
    else:
        logger.info("КОРЕКТНО: Не вдалося декодувати токен з недійсним підписом (JWTError).")

    # Тестування токена з неправильним видавцем (issuer)
    logger.info("\n--- Тестування токена з неправильним видавцем ---")
    original_issuer = settings.JWT_ISSUER
    settings.JWT_ISSUER = "some.other.issuer.com" # Тимчасово змінюємо для тесту
    # Створюємо токен, який буде мати 'iss' = original_issuer
    payload_for_wrong_issuer_test = user_data_payload.copy()
    payload_for_wrong_issuer_test["iss"] = original_issuer # Цей 'iss' буде в токені
    # expires_delta тут не потрібна, бо ми не перевіряємо час життя
    token_with_original_issuer = jwt.encode(
        payload_for_wrong_issuer_test,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
        # Не передаємо 'exp' сюди, jwt.encode не додасть його автоматично,
        # але decode_token його перевірить, якщо він є. Для цього тесту 'exp' не критичний.
    )
    # А тепер намагаємось декодувати, очікуючи settings.JWT_ISSUER = "some.other.issuer.com"
    decoded_wrong_issuer = decode_token(token_with_original_issuer) # Тут decode_token очікує "some.other.issuer.com"
    if decoded_wrong_issuer:
        logger.error(f"ПОМИЛКА ТЕСТУ: Декодовано токен, хоча видавець мав бути неправильним: {decoded_wrong_issuer}")
    else:
        logger.info("КОРЕКТНО: Не вдалося декодувати токен з неправильним видавцем (InvalidIssuerError).")
    settings.JWT_ISSUER = original_issuer # Повертаємо оригінальне значення

    # Тестування токена з неправильною аудиторією (audience)
    logger.info("\n--- Тестування токена з неправильною аудиторією ---")
    original_audience = settings.JWT_AUDIENCE
    settings.JWT_AUDIENCE = "some.other.audience.com" # Тимчасово змінюємо для тесту
    payload_for_wrong_audience_test = user_data_payload.copy()
    payload_for_wrong_audience_test["aud"] = original_audience # Цей 'aud' буде в токені
    payload_for_wrong_audience_test["iss"] = settings.JWT_ISSUER # Додамо правильного видавця
    token_with_original_audience = jwt.encode(
        payload_for_wrong_audience_test,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    decoded_wrong_audience = decode_token(token_with_original_audience) # Тут decode_token очікує "some.other.audience.com"
    if decoded_wrong_audience:
        logger.error(f"ПОМИЛКА ТЕСТУ: Декодовано токен, хоча аудиторія мала бути неправильною: {decoded_wrong_audience}")
    else:
        logger.info("КОРЕКТНО: Не вдалося декодувати токен з неправильною аудиторією (InvalidAudienceError).")
    settings.JWT_AUDIENCE = original_audience # Повертаємо оригінальне значення

    logger.info("\nТестування функцій безпеки завершено.")
