from datetime import datetime, timedelta, timezone
from typing import Optional, Any, Union
from jose import jwt, JWTError
from passlib.context import CryptContext

from backend.app.src.config.settings import settings

# --- Налаштування хешування паролів ---
# CryptContext використовується для хешування та перевірки паролів.
# "bcrypt" - це надійний і широко рекомендований алгоритм хешування.
# `deprecated="auto"` означає, що будь-які застарілі схеми все ще будуть використовуватися для перевірки,
# але нові хеші використовуватимуть схему за замовчуванням.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Перевіряє звичайний пароль на відповідність хешованому паролю.

    Args:
        plain_password (str): Пароль у відкритому вигляді.
        hashed_password (str): Хешований пароль, що зберігається в базі даних.

    Returns:
        bool: True, якщо пароль збігається, False в іншому випадку.
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        # Залогувати помилку або обробити її належним чином
        # З міркувань безпеки уникайте розголошення зайвої інформації про причину невдалої перевірки.
        # get_logger().error(f"Помилка перевірки пароля: {e}")
        return False

def get_password_hash(password: str) -> str:
    """
    Хешує звичайний пароль.

    Args:
        password (str): Пароль у відкритому вигляді.

    Returns:
        str: Хешований пароль.
    """
    return pwd_context.hash(password)


# --- Утиліти JWT (JSON Web Token) ---

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Створює новий JWT токен доступу.

    Args:
        data (dict): Дані для кодування в токен (зазвичай ідентифікатор користувача).
        expires_delta (Optional[timedelta]): Тривалість життя токена.
                                             За замовчуванням `ACCESS_TOKEN_EXPIRE_MINUTES` з налаштувань.

    Returns:
        str: Закодований JWT токен доступу.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"}) # Додати час закінчення терміну дії та тип токена
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Створює новий JWT токен оновлення.

    Args:
        data (dict): Дані для кодування в токен (зазвичай ідентифікатор користувача).
        expires_delta (Optional[timedelta]): Тривалість життя токена.
                                             За замовчуванням `REFRESH_TOKEN_EXPIRE_DAYS` з налаштувань.

    Returns:
        str: Закодований JWT токен оновлення.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"}) # Додати час закінчення терміну дії та тип токена
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> Optional[dict[str, Any]]:
    """
    Декодує JWT токен і повертає його корисне навантаження, якщо він дійсний.

    Args:
        token (str): JWT токен для декодування.

    Returns:
        Optional[dict[str, Any]]: Корисне навантаження токена, якщо він дійсний і не прострочений,
                                  в іншому випадку None.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError: # Ловить різні помилки JWT, такі як закінчення терміну дії, недійний підпис тощо.
        # Розгляньте можливість логування конкретної JWTError для налагодження, якщо потрібно
        # get_logger().warning(f"Помилка декодування JWT: {e}", exc_info=True)
        return None


# --- Конфігурація проміжного програмного забезпечення CORS (Cross-Origin Resource Sharing) (Приклад) ---
# Хоча налаштування для джерел CORS знаходяться в `settings.py`, фактичне проміжне ПЗ
# зазвичай додається в `main.py`.
# Цей розділ є скоріше приміткою/заповнювачем, якщо тут потрібні були б конкретні функції безпеки, пов'язані з CORS.
# Наприклад, функція для динамічної генерації параметрів CORS, якби вони були складнішими.

# def get_cors_settings() -> dict:
#     return {
# "allow_origins": [str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
# "allow_credentials": True,
# "allow_methods": ["*"],
# "allow_headers": ["*"],
#     }

if __name__ == "__main__":
    # Приклад використання (потребує налаштованого логера для перегляду логів помилок з verify_password)
    # from backend.app.src.config.logging import setup_logging, get_logger
    # setup_logging()
    # logger = get_logger(__name__)

    # --- Тестування хешування паролів ---
    print("--- Тестування хешування паролів ---")
    raw_password = "s3cureP@sswOrd!"
    hashed = get_password_hash(raw_password)
    print(f"Сирий пароль: {raw_password}")
    print(f"Хешований пароль: {hashed}")
    print(f"Перевірка (правильно): {verify_password(raw_password, hashed)}")
    print(f"Перевірка (неправильно): {verify_password('wrongpassword', hashed)}")

    # --- Тестування створення та декодування JWT ---
    print("\n--- Тестування створення та декодування JWT ---")
    user_data = {"sub": "testuser@example.com", "user_id": 123, "role": "user"}

    # Токен доступу
    access_token = create_access_token(user_data)
    print(f"Згенерований токен доступу: {access_token}")
    decoded_access_payload = decode_token(access_token)
    if decoded_access_payload:
        print(f"Декодоване корисне навантаження токена доступу: {decoded_access_payload}")
        exp_timestamp = decoded_access_payload.get('exp')
        if exp_timestamp:
            print(f"Токен доступу закінчується (UTC): {datetime.fromtimestamp(exp_timestamp, timezone.utc)}")
    else:
        print("Не вдалося декодувати токен доступу (або він недійсний/прострочений).")

    # Токен оновлення
    refresh_token = create_refresh_token(user_data)
    print(f"\nЗгенерований токен оновлення: {refresh_token}")
    decoded_refresh_payload = decode_token(refresh_token)
    if decoded_refresh_payload:
        print(f"Декодоване корисне навантаження токена оновлення: {decoded_refresh_payload}")
        exp_timestamp = decoded_refresh_payload.get('exp')
        if exp_timestamp:
            print(f"Токен оновлення закінчується (UTC): {datetime.fromtimestamp(exp_timestamp, timezone.utc)}")
    else:
        print("Не вдалося декодувати токен оновлення (або він недійсний/прострочений).")

    # Тестування простроченого токена (приклад)
    print("\n--- Тестування простроченого токена (Приклад) ---")
    expired_access_token = create_access_token(user_data, expires_delta=timedelta(seconds=-1))
    print(f"Згенерований прострочений токен доступу: {expired_access_token}")
    decoded_expired_payload = decode_token(expired_access_token)
    if decoded_expired_payload:
        print(f"Декодоване корисне навантаження простроченого токена: {decoded_expired_payload}") # Не повинно статися
    else:
        print("Правильно не вдалося декодувати прострочений токен доступу.")

    # Тестування недійсного токена
    print("\n--- Тестування недійсного токена (Приклад) ---")
    invalid_token = "this.is.not.a.valid.token"
    decoded_invalid_payload = decode_token(invalid_token)
    if decoded_invalid_payload:
        print(f"Декодоване корисне навантаження недійсного токена: {decoded_invalid_payload}") # Не повинно статися
    else:
        print("Правильно не вдалося декодувати недійсний токен.")
