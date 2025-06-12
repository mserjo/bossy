# backend/app/src/config/security.py
# -*- coding: utf-8 -*-
"""Модуль конфігурацій та утиліт безпеки для додатку.

Цей модуль відповідає за:
- Створення та декодування JWT (JSON Web Tokens) для автентифікації та авторизації.
  Включає функції для генерації токенів доступу (access tokens) та токенів
  оновлення (refresh tokens).
- Додавання стандартних "клеймів" (claims) до JWT, таких як `exp` (час закінчення),
  `iat` (час видачі), `iss` (видавець), `aud` (аудиторія) та кастомний
  клейм `type` (тип токена: "access" або "refresh").
- Обробку помилок, пов'язаних з JWT (наприклад, прострочений токен, недійсна
  аудиторія/видавець, помилка підпису), та їх логування.

Налаштування, такі як секретний ключ JWT, алгоритм шифрування, час життя токенів,
ідентифікатори видавця та аудиторії, беруться з об'єкта `settings`
(з `backend.app.src.config.settings`).

Утиліти для хешування паролів винесені до окремого модуля `backend.app.src.utils.hash`.
"""
import logging # Для локального використання в __main__
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

# `jose.exceptions` імпортується для типізації та обробки конкретних помилок JWT
from jose import JWTError, jwt
from jose import exceptions as jose_exceptions

# Абсолютний імпорт налаштувань та централізованого логера
from backend.app.src.config import logger, settings


# --- Утиліти для роботи з JWT (JSON Web Token) ---

def create_jwt_token(
    data: Dict[str, Any],
    token_type: str,
    expires_delta: timedelta,
    secret_key: str,
    algorithm: str,
    issuer: Optional[str] = None,
    audience: Optional[str] = None,
) -> str:
    """Створює JWT токен (загальна функція).

    Args:
        data: Дані для кодування в токен (наприклад, ідентифікатор користувача `sub`).
        token_type: Тип токена (наприклад, "access", "refresh", "email_verification").
        expires_delta: Тривалість життя токена.
        secret_key: Секретний ключ для підпису токена.
        algorithm: Алгоритм підпису токена.
        issuer: Опціональний видавець токена (claim "iss").
        audience: Опціональна аудиторія токена (claim "aud").

    Returns:
        Закодований JWT токен у вигляді рядка.
    """
    to_encode = data.copy()
    issued_at = datetime.now(timezone.utc)
    expire = issued_at + expires_delta

    to_encode.update({
        "iat": issued_at,
        "exp": expire,
        "type": token_type,
    })
    if issuer:
        to_encode["iss"] = issuer
    if audience:
        to_encode["aud"] = audience

    encoded_jwt = jwt.encode(claims=to_encode, key=secret_key, algorithm=algorithm)
    logger.debug("Створено JWT токен типу '%s', термін дії до: %s", token_type, expire.isoformat())
    return encoded_jwt


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Створює новий JWT токен доступу.

    Токен містить надані дані, стандартні клейми (iat, exp, type, iss, aud)
    та використовує налаштування з `settings` для секретного ключа, алгоритму,
    часу життя, видавця та аудиторії.

    Args:
        data: Дані для кодування в токен (наприклад, `{"sub": "user_id"}`).
        expires_delta: Опціональна тривалість життя токена. Якщо не надано,
                       використовується `settings.ACCESS_TOKEN_EXPIRE_MINUTES`.

    Returns:
        Закодований JWT токен доступу у вигляді рядка.
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    return create_jwt_token(
        data=data,
        token_type="access",
        expires_delta=expires_delta,
        secret_key=settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
        issuer=settings.JWT_ISSUER,
        audience=settings.JWT_AUDIENCE,
    )


def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Створює новий JWT токен оновлення.

    Токен містить надані дані, стандартні клейми (iat, exp, type, iss, aud)
    та використовує налаштування з `settings` для секретного ключа, алгоритму,
    часу життя, видавця та аудиторії.

    Args:
        data: Дані для кодування в токен (наприклад, `{"sub": "user_id"}`).
        expires_delta: Опціональна тривалість життя токена. Якщо не надано,
                       використовується `settings.REFRESH_TOKEN_EXPIRE_DAYS`.

    Returns:
        Закодований JWT токен оновлення у вигляді рядка.
    """
    if expires_delta is None:
        expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    return create_jwt_token(
        data=data,
        token_type="refresh",
        expires_delta=expires_delta,
        secret_key=settings.JWT_SECRET_KEY, # Можна використовувати інший ключ для refresh токенів
        algorithm=settings.JWT_ALGORITHM,
        issuer=settings.JWT_ISSUER,
        audience=settings.JWT_AUDIENCE, # Можна використовувати іншу аудиторію
    )


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Декодує JWT токен та перевіряє його валідність.

    Перевіряється підпис, термін дії, видавець (`issuer`) та аудиторія (`audience`)
    на основі значень, вказаних у `settings`.

    Args:
        token: JWT токен для декодування у вигляді рядка.

    Returns:
        Словник з корисним навантаженням (payload) токена, якщо він дійсний
        та відповідає всім критеріям перевірки.
        Повертає `None` у разі будь-якої помилки декодування або валідації
        (наприклад, прострочений токен, невірний підпис, невідповідність видавця/аудиторії).
    """
    if not token:
        logger.warning("Спроба декодувати порожній токен.")
        return None
    try:
        payload = jwt.decode(
            token=token,
            key=settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            audience=settings.JWT_AUDIENCE, # Перевірка очікуваної аудиторії
            issuer=settings.JWT_ISSUER      # Перевірка очікуваного видавця
        )
        # Додаткова перевірка типу токена, якщо потрібно розрізняти їх після декодування
        # token_type = payload.get("type")
        # if token_type not in ["access", "refresh", ...]: # Додайте очікувані типи
        #     logger.warning("Невідомий або непідтримуваний тип токена: '%s'", token_type)
        #     return None
        logger.debug("JWT токен успішно декодовано та валідовано.")
        return payload
    except jose_exceptions.ExpiredSignatureError:
        logger.warning("Помилка декодування JWT: термін дії токена закінчився.")
        return None
    except jose_exceptions.InvalidAudienceError:
        logger.warning("Помилка декодування JWT: недійсна аудиторія (aud) токена.")
        return None
    except jose_exceptions.InvalidIssuerError:
        logger.warning("Помилка декодування JWT: недійсний видавець (iss) токена.")
        return None
    except jose_exceptions.InvalidAlgorithmError as e:
        logger.error(
            "Помилка декодування JWT: недійсний алгоритм. Очікувався '%s', але токен використовує інший. Деталі: %s",
            settings.JWT_ALGORITHM, e, exc_info=True
        )
        return None
    except JWTError as e:  # Загальна помилка JWT (наприклад, недійсний підпис, неправильний формат)
        logger.warning("Загальна помилка декодування JWT: %s", e, exc_info=True)
        return None
    except Exception as e: # pylint: disable=broad-except # Інші непередбачені помилки
        logger.error("Неочікувана помилка (%s) при декодуванні JWT: %s", type(e).__name__, e, exc_info=True)
        return None


if __name__ == "__main__":
    # Логер вже налаштований через імпорт `from backend.app.src.config import logger`
    # та виклик setup_logging() в __init__.py пакета config.
    main_logger = logging.getLogger(__name__) # Використовуємо окремий логер для __main__

    main_logger.info("--- Тестування створення та декодування JWT ---")
    user_data_payload: Dict[str, Any] = {"sub": "testuser@example.com", "user_id": 123, "role": "user"}

    # Токен доступу
    access_token = create_access_token(user_data_payload)
    main_logger.info("Згенерований токен доступу: %s", access_token)
    decoded_access_payload = decode_token(access_token)
    if decoded_access_payload:
        main_logger.info("Декодоване корисне навантаження токена доступу: %s", decoded_access_payload)
        exp_timestamp = decoded_access_payload.get('exp')
        if exp_timestamp:
            main_logger.info("Токен доступу закінчується (UTC): %s", datetime.fromtimestamp(exp_timestamp, timezone.utc))
        assert decoded_access_payload.get("sub") == user_data_payload["sub"]
        assert decoded_access_payload.get("type") == "access"
        assert decoded_access_payload.get("iss") == settings.JWT_ISSUER
        assert decoded_access_payload.get("aud") == settings.JWT_AUDIENCE
    else:
        main_logger.warning("Не вдалося декодувати токен доступу (або він недійсний/прострочений).")

    # Токен оновлення
    refresh_token = create_refresh_token(user_data_payload)
    main_logger.info("\nЗгенерований токен оновлення: %s", refresh_token)
    decoded_refresh_payload = decode_token(refresh_token)
    if decoded_refresh_payload:
        main_logger.info("Декодоване корисне навантаження токена оновлення: %s", decoded_refresh_payload)
        exp_timestamp = decoded_refresh_payload.get('exp')
        if exp_timestamp:
            main_logger.info("Токен оновлення закінчується (UTC): %s", datetime.fromtimestamp(exp_timestamp, timezone.utc))
        assert decoded_refresh_payload.get("type") == "refresh"
    else:
        main_logger.warning("Не вдалося декодувати токен оновлення (або він недійсний/прострочений).")

    # Тестування простроченого токена
    main_logger.info("\n--- Тестування простроченого токена ---")
    expired_access_token = create_access_token(user_data_payload, expires_delta=timedelta(seconds=-3600))
    main_logger.info("Згенерований прострочений токен доступу: %s", expired_access_token)
    decoded_expired_payload = decode_token(expired_access_token)
    if decoded_expired_payload:
        main_logger.error("ПОМИЛКА ТЕСТУ: Декодовано прострочений токен: %s", decoded_expired_payload)
        assert False, "Прострочений токен не повинен декодуватися."
    else:
        main_logger.info("КОРЕКТНО: Не вдалося декодувати прострочений токен доступу.")

    # Тестування недійсного токена (неправильний підпис)
    main_logger.info("\n--- Тестування недійсного токена (неправильний підпис) ---")
    invalid_signature_token = access_token[:-5] + "XXXXX" # Змінюємо частину підпису
    main_logger.info("Недійсний токен (змінений підпис): %s", invalid_signature_token)
    decoded_invalid_payload = decode_token(invalid_signature_token)
    if decoded_invalid_payload:
        main_logger.error("ПОМИЛКА ТЕСТУ: Декодовано токен з недійсним підписом: %s", decoded_invalid_payload)
        assert False, "Токен з недійсним підписом не повинен декодуватися."
    else:
        main_logger.info("КОРЕКТНО: Не вдалося декодувати токен з недійсним підписом.")

    # Тестування токена з неправильним видавцем (issuer)
    main_logger.info("\n--- Тестування токена з неправильним видавцем ---")
    original_issuer = settings.JWT_ISSUER
    # Створюємо токен з правильним видавцем
    temp_payload_issuer = {"sub": "test_user_issuer", "type": "access", "iss": original_issuer, "aud": settings.JWT_AUDIENCE}
    token_correct_issuer = jwt.encode(temp_payload_issuer, settings.JWT_SECRET_KEY, settings.JWT_ALGORITHM)
    # Тепер намагаємося декодувати його, очікуючи іншого видавця
    settings.JWT_ISSUER = "some.other.issuer.com" # Тимчасово змінюємо очікуваного видавця
    decoded_wrong_issuer = decode_token(token_correct_issuer)
    if decoded_wrong_issuer:
        main_logger.error("ПОМИЛКА ТЕСТУ: Декодовано токен, хоча видавець мав бути неправильним: %s", decoded_wrong_issuer)
        assert False, "Токен з неправильним видавцем не повинен декодуватися."
    else:
        main_logger.info("КОРЕКТНО: Не вдалося декодувати токен через невідповідність видавця.")
    settings.JWT_ISSUER = original_issuer # Повертаємо оригінальне значення

    # Тестування токена з неправильною аудиторією (audience)
    main_logger.info("\n--- Тестування токена з неправильною аудиторією ---")
    original_audience = settings.JWT_AUDIENCE
    # Створюємо токен з правильною аудиторією
    temp_payload_audience = {"sub": "test_user_audience", "type": "access", "iss": settings.JWT_ISSUER, "aud": original_audience}
    token_correct_audience = jwt.encode(temp_payload_audience, settings.JWT_SECRET_KEY, settings.JWT_ALGORITHM)
    # Тепер намагаємося декодувати його, очікуючи іншу аудиторію
    settings.JWT_AUDIENCE = "some.other.audience.com" # Тимчасово змінюємо очікувану аудиторію
    decoded_wrong_audience = decode_token(token_correct_audience)
    if decoded_wrong_audience:
        main_logger.error("ПОМИЛКА ТЕСТУ: Декодовано токен, хоча аудиторія мала бути неправильною: %s", decoded_wrong_audience)
        assert False, "Токен з неправильною аудиторією не повинен декодуватися."
    else:
        main_logger.info("КОРЕКТНО: Не вдалося декодувати токен через невідповідність аудиторії.")
    settings.JWT_AUDIENCE = original_audience # Повертаємо оригінальне значення

    main_logger.info("\nТестування функцій безпеки завершено.")
