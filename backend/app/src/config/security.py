# /backend/app/src/config/security.py
"""
Модуль безпеки для FastAPI програми Kudos.

Цей модуль відповідає за:
- Хешування та перевірку паролів за допомогою Passlib (bcrypt).
- Створення та декодування JWT (JSON Web Tokens) для автентифікації та авторизації.
  Включає токени доступу (access tokens) та токени оновлення (refresh tokens).
- Додавання стандартних клеймів до JWT, таких як `exp` (час закінчення), `iss` (видавець),
  `aud` (аудиторія) та кастомний клейм `type` (тип токена: access/refresh).
- Обробку помилок, пов'язаних з JWT, та їх логування.

Налаштування, такі як секретний ключ JWT, алгоритм, час життя токенів, видавець та аудиторія,
беруться з `settings.py`.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Any
from jose import jwt, JWTError, exceptions as jose_exceptions
from passlib.context import CryptContext

from backend.app.src.config.settings import settings
from backend.app.src.config.logging import get_logger

# Отримання логера для цього модуля
logger = get_logger(__name__)

# --- Налаштування хешування паролів ---
# `CryptContext` використовується для хешування та перевірки паролів.
# "bcrypt" є надійним та широко рекомендованим алгоритмом хешування.
# `deprecated="auto"` означає, що будь-які застарілі схеми (якщо вони були б вказані)
# все ще будуть використовуватися для перевірки, але нові хеші генеруватимуться
# схемою за замовчуванням (першою у списку `schemes`).
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Перевіряє наданий пароль у відкритому вигляді на відповідність збереженому хешованому паролю.

    Args:
        plain_password (str): Пароль у відкритому вигляді для перевірки.
        hashed_password (str): Хешований пароль, що зберігається в базі даних.

    Returns:
        bool: `True`, якщо паролі збігаються, `False` в іншому випадку.
    """
    try:
        is_valid = pwd_context.verify(plain_password, hashed_password)
        if not is_valid:
            logger.debug("Невдала спроба перевірки пароля: пароль не збігається.")
        return is_valid
    except Exception as e:
        # З міркувань безпеки, не розголошуємо деталі помилки хешування або валідації.
        # Логуємо помилку для внутрішнього аналізу, але повертаємо False.
        logger.error(f"Помилка під час перевірки пароля: {e}", exc_info=True)
        return False

def get_password_hash(password: str) -> str:
    """
    Хешує пароль у відкритому вигляді за допомогою bcrypt.

    Args:
        password (str): Пароль у відкритому вигляді.

    Returns:
        str: Хешований пароль.
    """
    return pwd_context.hash(password)


# --- Утиліти для роботи з JWT (JSON Web Token) ---

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Створює новий JWT токен доступу.

    Токен містить надані дані, час закінчення терміну дії, тип токена ("access"),
    видавця (`iss`) та аудиторію (`aud`), взяті з налаштувань.

    Args:
        data (dict): Дані для кодування в токен (наприклад, ідентифікатор користувача `sub`).
        expires_delta (Optional[timedelta]): Тривалість життя токена.
                                             Якщо не надано, використовується значення
                                             `ACCESS_TOKEN_EXPIRE_MINUTES` з налаштувань.

    Returns:
        str: Закодований JWT токен доступу у вигляді рядка.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "type": "access", # Тип токена
        "iss": settings.JWT_ISSUER, # Видавець токена
        "aud": settings.JWT_AUDIENCE, # Аудиторія токена
    })
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Створює новий JWT токен оновлення.

    Токен містить надані дані, час закінчення терміну дії, тип токена ("refresh"),
    видавця (`iss`) та аудиторію (`aud`), взяті з налаштувань.

    Args:
        data (dict): Дані для кодування в токен (наприклад, ідентифікатор користувача `sub`).
        expires_delta (Optional[timedelta]): Тривалість життя токена.
                                             Якщо не надано, використовується значення
                                             `REFRESH_TOKEN_EXPIRE_DAYS` з налаштувань.

    Returns:
        str: Закодований JWT токен оновлення у вигляді рядка.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({
        "exp": expire,
        "type": "refresh", # Тип токена
        "iss": settings.JWT_ISSUER, # Видавець токена
        "aud": settings.JWT_AUDIENCE, # Аудиторія токена
    })
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> Optional[dict[str, Any]]:
    """
    Декодує JWT токен, перевіряє його валідність (включаючи термін дії, видавця та аудиторію)
    та повертає його корисне навантаження (payload).

    Args:
        token (str): JWT токен для декодування.

    Returns:
        Optional[dict[str, Any]]: Словник з корисним навантаженням токена, якщо він дійсний
                                  та відповідає всім критеріям перевірки.
                                  Повертає `None` у разі будь-якої помилки декодування або валідації.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            audience=settings.JWT_AUDIENCE, # Перевірка аудиторії
            issuer=settings.JWT_ISSUER      # Перевірка видавця
        )
        return payload
    except jose_exceptions.ExpiredSignatureError:
        logger.warning("Помилка декодування JWT: термін дії токена закінчився.")
        return None
    except jose_exceptions.InvalidAudienceError:
        logger.warning("Помилка декодування JWT: недійсна аудиторія (aud).")
        return None
    except jose_exceptions.InvalidIssuerError:
        logger.warning("Помилка декодування JWT: недійсний видавець (iss).")
        return None
    except jose_exceptions.InvalidAlgorithmError as e:
        logger.error(f"Помилка декодування JWT: недійсний алгоритм. Очікувався {settings.JWT_ALGORITHM}, отримано інший. Деталі: {e}", exc_info=True)
        return None
    except JWTError as e: # Загальна помилка JWT (недійсний підпис, неправильний формат тощо)
        logger.warning(f"Загальна помилка декодування JWT: {e}", exc_info=True)
        return None
    except Exception as e: # Інші непередбачені помилки
        logger.error(f"Неочікувана помилка при декодуванні JWT: {e}", exc_info=True)
        return None


# Приклад можливих додаткових функцій безпеки (не частина поточного завдання):
# def check_permissions(user_role: str, required_role: str) -> bool:
# """Перевіряє, чи має користувач необхідну роль."""
#     # Логіка перевірки ролей...
# return user_role == required_role


# Блок для демонстрації або тестування функціональності цього модуля
if __name__ == "__main__":
    # Для перегляду логів помилок з verify_password та decode_token,
    # потрібно налаштувати логування, якщо воно ще не налаштоване.
    # Зазвичай це робиться в main.py або при старті програми.
    # Тут ми можемо спробувати налаштувати його для тестування:
    try:
        from backend.app.src.config.logging import setup_logging
        setup_logging() # Застосувати конфігурацію логування
        logger.info("Логування налаштовано для тестування security.py.")
    except ImportError:
        # Якщо setup_logging не доступний, використовуємо базове налаштування
        import logging as base_logging
        base_logging.basicConfig(level=base_logging.INFO)
        logger.warning("Не вдалося імпортувати setup_logging. Використовується базова конфігурація логування для тестів security.py.")


    # --- Тестування хешування паролів ---
    logger.info("--- Тестування хешування паролів ---")
    raw_password = "s3cureP@sswOrd!"
    hashed = get_password_hash(raw_password)
    logger.info(f"Сирий пароль: {raw_password}")
    logger.info(f"Хешований пароль: {hashed}")
    logger.info(f"Перевірка (правильно): {verify_password(raw_password, hashed)}")
    logger.info(f"Перевірка (неправильно): {verify_password('wrongpassword', hashed)}")

    # --- Тестування створення та декодування JWT ---
    logger.info("\n--- Тестування створення та декодування JWT ---")
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
        logger.info("КОРЕКТНО: Не вдалося декодувати прострочений токен доступу.")

    # Тестування недійсного токена (неправильний підпис)
    logger.info("\n--- Тестування недійсного токена (неправильний підпис) ---")
    invalid_signature_token = access_token[:-5] + "XXXXX" # Змінити частину підпису
    logger.info(f"Недійсний токен (змінений підпис): {invalid_signature_token}")
    decoded_invalid_payload = decode_token(invalid_signature_token)
    if decoded_invalid_payload:
        logger.error(f"ПОМИЛКА ТЕСТУ: Декодовано токен з недійсним підписом: {decoded_invalid_payload}")
    else:
        logger.info("КОРЕКТНО: Не вдалося декодувати токен з недійсним підписом.")

    # Тестування токена з неправильним видавцем (issuer)
    logger.info("\n--- Тестування токена з неправильним видавцем ---")
    original_issuer = settings.JWT_ISSUER
    settings.JWT_ISSUER = "some.other.issuer.com" # Тимчасово змінюємо для тесту
    token_with_wrong_issuer_payload = user_data_payload.copy()
    token_with_wrong_issuer_payload["iss"] = original_issuer # Створюємо токен зі старим (правильним) видавцем
    token_with_wrong_issuer = jwt.encode(
        token_with_wrong_issuer_payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    # А тепер намагаємось декодувати, очікуючи settings.JWT_ISSUER = "some.other.issuer.com"
    decoded_wrong_issuer = decode_token(token_with_wrong_issuer)
    if decoded_wrong_issuer:
        logger.error(f"ПОМИЛКА ТЕСТУ: Декодовано токен з неправильним видавцем: {decoded_wrong_issuer}")
    else:
        logger.info("КОРЕКТНО: Не вдалося декодувати токен з неправильним видавцем.")
    settings.JWT_ISSUER = original_issuer # Повертаємо оригінальне значення

    # Тестування токена з неправильною аудиторією (audience)
    logger.info("\n--- Тестування токена з неправильною аудиторією ---")
    original_audience = settings.JWT_AUDIENCE
    settings.JWT_AUDIENCE = "some.other.audience.com" # Тимчасово змінюємо для тесту
    token_with_wrong_audience_payload = user_data_payload.copy()
    token_with_wrong_audience_payload["aud"] = original_audience # Створюємо токен зі старою (правильною) аудиторією
    # Додамо також правильного видавця, щоб ізолювати тест аудиторії
    token_with_wrong_audience_payload["iss"] = settings.JWT_ISSUER
    token_with_wrong_audience = jwt.encode(
        token_with_wrong_audience_payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    # А тепер намагаємось декодувати, очікуючи settings.JWT_AUDIENCE = "some.other.audience.com"
    decoded_wrong_audience = decode_token(token_with_wrong_audience)
    if decoded_wrong_audience:
        logger.error(f"ПОМИЛКА ТЕСТУ: Декодовано токен з неправильною аудиторією: {decoded_wrong_audience}")
    else:
        logger.info("КОРЕКТНО: Не вдалося декодувати токен з неправильною аудиторією.")
    settings.JWT_AUDIENCE = original_audience # Повертаємо оригінальне значення

    logger.info("\nТестування функцій безпеки завершено.")
