from datetime import datetime, timedelta, timezone
from typing import Optional, Any, Union
from jose import jwt, JWTError
from passlib.context import CryptContext

from backend.app.src.config.settings import settings

# --- Password Hashing Setup ---
# CryptContext is used for hashing and verifying passwords.
# "bcrypt" is a strong and widely recommended hashing algorithm.
# `deprecated="auto"` means that any deprecated schemes will still be usable for verification
# but new hashes will use the default scheme.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain password against a hashed password.

    Args:
        plain_password (str): The password in plain text.
        hashed_password (str): The hashed password stored in the database.

    Returns:
        bool: True if the password matches, False otherwise.
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        # Log the error or handle it appropriately
        # For security, avoid leaking too much information about why verification failed.
        # get_logger().error(f"Error verifying password: {e}")
        return False

def get_password_hash(password: str) -> str:
    """
    Hashes a plain password.

    Args:
        password (str): The password in plain text.

    Returns:
        str: The hashed password.
    """
    return pwd_context.hash(password)


# --- JWT (JSON Web Token) Utilities ---

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates a new JWT access token.

    Args:
        data (dict): The data to encode into the token (typically user identifier).
        expires_delta (Optional[timedelta]): The lifespan of the token.
                                             Defaults to `ACCESS_TOKEN_EXPIRE_MINUTES` from settings.

    Returns:
        str: The encoded JWT access token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"}) # Add expiration and token type
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates a new JWT refresh token.

    Args:
        data (dict): The data to encode into the token (typically user identifier).
        expires_delta (Optional[timedelta]): The lifespan of the token.
                                             Defaults to `REFRESH_TOKEN_EXPIRE_DAYS` from settings.

    Returns:
        str: The encoded JWT refresh token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"}) # Add expiration and token type
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> Optional[dict[str, Any]]:
    """
    Decodes a JWT token and returns its payload if valid.

    Args:
        token (str): The JWT token to decode.

    Returns:
        Optional[dict[str, Any]]: The payload of the token if it's valid and not expired,
                                  otherwise None.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError: # Catches various JWT errors like expiration, invalid signature, etc.
        # Consider logging the specific JWTError for debugging purposes if needed
        # get_logger().warning(f"JWT decoding error: {e}", exc_info=True)
        return None


# --- CORS (Cross-Origin Resource Sharing) Middleware Configuration (Example) ---
# While settings for CORS origins are in `settings.py`, the actual middleware
# is typically added in `main.py`.
# This section is more of a note/placeholder if specific security functions related to CORS were needed here.
# For example, a function to dynamically generate CORS parameters if they were more complex.

# def get_cors_settings() -> dict:
#     return {
# "allow_origins": [str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
# "allow_credentials": True,
# "allow_methods": ["*"],
# "allow_headers": ["*"],
#     }

if __name__ == "__main__":
    # Example Usage (requires a logger to be configured to see error logs from verify_password)
    # from backend.app.src.config.logging import setup_logging, get_logger
    # setup_logging()
    # logger = get_logger(__name__)

    # --- Test Password Hashing ---
    print("--- Testing Password Hashing ---")
    raw_password = "s3cureP@sswOrd!"
    hashed = get_password_hash(raw_password)
    print(f"Raw password: {raw_password}")
    print(f"Hashed password: {hashed}")
    print(f"Verification (correct): {verify_password(raw_password, hashed)}")
    print(f"Verification (incorrect): {verify_password('wrongpassword', hashed)}")

    # --- Test JWT Creation and Decoding ---
    print("\n--- Testing JWT Creation & Decoding ---")
    user_data = {"sub": "testuser@example.com", "user_id": 123, "role": "user"}

    # Access Token
    access_token = create_access_token(user_data)
    print(f"Generated Access Token: {access_token}")
    decoded_access_payload = decode_token(access_token)
    if decoded_access_payload:
        print(f"Decoded Access Token Payload: {decoded_access_payload}")
        exp_timestamp = decoded_access_payload.get('exp')
        if exp_timestamp:
            print(f"Access Token Expires At (UTC): {datetime.fromtimestamp(exp_timestamp, timezone.utc)}")
    else:
        print("Failed to decode access token (or it's invalid/expired).")

    # Refresh Token
    refresh_token = create_refresh_token(user_data)
    print(f"\nGenerated Refresh Token: {refresh_token}")
    decoded_refresh_payload = decode_token(refresh_token)
    if decoded_refresh_payload:
        print(f"Decoded Refresh Token Payload: {decoded_refresh_payload}")
        exp_timestamp = decoded_refresh_payload.get('exp')
        if exp_timestamp:
            print(f"Refresh Token Expires At (UTC): {datetime.fromtimestamp(exp_timestamp, timezone.utc)}")
    else:
        print("Failed to decode refresh token (or it's invalid/expired).")

    # Test expired token (example)
    print("\n--- Testing Expired Token (Example) ---")
    expired_access_token = create_access_token(user_data, expires_delta=timedelta(seconds=-1))
    print(f"Generated Expired Access Token: {expired_access_token}")
    decoded_expired_payload = decode_token(expired_access_token)
    if decoded_expired_payload:
        print(f"Decoded Expired Token Payload: {decoded_expired_payload}") # Should not happen
    else:
        print("Correctly failed to decode expired access token.")

    # Test invalid token
    print("\n--- Testing Invalid Token (Example) ---")
    invalid_token = "this.is.not.a.valid.token"
    decoded_invalid_payload = decode_token(invalid_token)
    if decoded_invalid_payload:
        print(f"Decoded Invalid Token Payload: {decoded_invalid_payload}") # Should not happen
    else:
        print("Correctly failed to decode invalid token.")
