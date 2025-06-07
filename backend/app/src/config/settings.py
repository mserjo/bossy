import os
from typing import List, Optional, Union, Any
from pydantic import PostgresDsn, RedisDsn, field_validator, AnyHttpUrl, ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Load .env file from the project root (backend/.env or kudos/.env)
dotenv_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env") # Points to backend/.env
if not os.path.exists(dotenv_path):
    dotenv_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".env") # Points to kudos/.env

load_dotenv(dotenv_path=dotenv_path, override=True)

class Settings(BaseSettings):
    """
    Application settings are loaded from environment variables and/or a .env file.
    Pydantic's BaseSettings provides validation and type casting.
    """

    # --- Core Application Settings ---
    PROJECT_NAME: str = "Kudos"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "a_very_secret_key_that_should_be_changed"

    # --- Database Settings (PostgreSQL) ---
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "kudos_db"
    DATABASE_URL: Optional[PostgresDsn] = None

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info: ValidationInfo) -> Any:
        if isinstance(v, str):
            return v
        data = info.data if info and hasattr(info, 'data') else {}
        return str(PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=data.get("POSTGRES_USER"),
            password=data.get("POSTGRES_PASSWORD"),
            host=data.get("POSTGRES_SERVER"),
            port=int(data.get("POSTGRES_PORT", 5432)),
            path=f"/{data.get('POSTGRES_DB') or ''}",
        ))

    # --- Redis Settings ---
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_URL: Optional[RedisDsn] = None

    @field_validator("REDIS_URL", mode="before")
    @classmethod
    def assemble_redis_connection(cls, v: Optional[str], info: ValidationInfo) -> Any:
        if isinstance(v, str):
            return v
        data = info.data if info and hasattr(info, 'data') else {}
        scheme = "redis"
        host = data.get("REDIS_HOST")
        port = data.get("REDIS_PORT")
        db = data.get("REDIS_DB")
        password = data.get("REDIS_PASSWORD")
        if password:
            return str(RedisDsn(f"{scheme}://:{password}@{host}:{port}/{db}"))
        return str(RedisDsn(f"{scheme}://{host}:{port}/{db}"))

    # --- JWT Authentication Settings ---
    JWT_SECRET_KEY: str = "another_very_secret_jwt_key_to_be_changed"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --- CORS (Cross-Origin Resource Sharing) Settings ---
    BACKEND_CORS_ORIGINS: List[Union[AnyHttpUrl, str]] = ["*"]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                try:
                    import json
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass # Fall through to comma-separated logic
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        raise ValueError("BACKEND_CORS_ORIGINS must be a list of URLs or a comma-separated string")

    # --- Initial Superuser Settings ---
    FIRST_SUPERUSER_EMAIL: str = "admin@example.com"
    FIRST_SUPERUSER_PASSWORD: str = "supersecret"

    # --- System User Settings ---
    SYSTEM_USER_ODIN_EMAIL: str = "odin@system.kudos"
    SYSTEM_USER_SHADOW_EMAIL: str = "shadow@system.kudos"

    # --- File Storage Settings ---
    STATIC_FILES_DIR: str = "static"
    UPLOADED_FILES_DIR: str = os.path.join(STATIC_FILES_DIR, "uploads") # Ensure this is a valid path segment
    MAX_FILE_SIZE_MB: int = 10

    # --- Email Settings ---
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = 587
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = "Kudos System"

    # --- Logging Settings ---
    LOGGING_LEVEL: str = "INFO"
    LOG_TO_FILE: bool = False # Default to console logging for simple setups
    LOG_DIR: str = "logs" # Directory for log files
    LOG_APP_FILE: str = "app.log"
    LOG_ERROR_FILE: str = "error.log"
    LOG_MAX_BYTES: int = 1024 * 1024 * 10
    LOG_BACKUP_COUNT: int = 5

    model_config = SettingsConfigDict(
        env_file=dotenv_path,
        env_file_encoding='utf-8',
        extra='ignore',
        case_sensitive=False
    )

settings = Settings()

if __name__ == "__main__":
    print(f"Dotenv path: {dotenv_path}, Exists: {os.path.exists(dotenv_path)}")
    print("--- Application Settings Loaded ---")
    for key, value in settings.model_dump().items():
        if "password" in key.lower() or "secret" in key.lower():
            print(f"{key}: ******")
        else:
            print(f"{key}: {value}")
