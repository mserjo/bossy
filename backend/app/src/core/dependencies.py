# backend/app/src/core/dependencies.py
"""
Загальні залежності для FastAPI програми Kudos.

Цей модуль визначає залежності, що використовуються в обробниках запитів FastAPI,
зокрема для автентифікації та авторизації користувачів. Вони включають:
- Отримання поточного користувача на основі JWT токена.
- Перевірку активності користувача.
- Перевірку прав суперкористувача.
- Заготовки для більш складних перевірок (наприклад, адміністратор групи).

Залежності використовують `OAuth2PasswordBearer` для отримання токенів,
функції декодування токенів з `config.security` та сесію бази даних з `config.database`.

ВАЖЛИВО: Моделі `UserModel` та `TokenPayload` наразі є заповнювачами (placeholders).
Їх потрібно буде замінити на реальні імпорти з відповідних модулів
(`models.auth.user` та `schemas.auth.token`) після їх створення/рефакторингу.
"""

from typing import Optional # AsyncGenerator було видалено, оскільки не використовується в цьому файлі.
from fastapi import Depends, HTTPException, status # Path тут не використовується, але може знадобитися для get_current_group_admin
from fastapi.security import OAuth2PasswordBearer
# JWTError імпортується для можливої обробки, хоча decode_token вже це робить
# from jose import JWTError # Закоментовано, бо decode_token вже обробляє JWTError
from pydantic import BaseModel, ValidationError # BaseModel для TokenPayload-заповнювача
from datetime import datetime, timezone, timedelta # Використовується в __main__ для прикладу

from backend.app.src.config.settings import settings
from backend.app.src.config.security import decode_token
from backend.app.src.config.database import get_db, AsyncSession
from backend.app.src.config.logging import get_logger

# Отримання логера для цього модуля
logger = get_logger(__name__)

# TODO: Замінити UserModel на імпорт реальної моделі користувача, наприклад:
# from backend.app.src.models.auth.user import User as UserModel
# Наразі UserModel є класом-заповнювачем для демонстрації структури.
class UserModel:
    """
    Клас-заповнювач для моделі користувача (User).

    ВАЖЛИВО: Цей клас ПОВИНЕН БУТИ ЗАМІНЕНИЙ на імпорт реальної моделі User
    з `backend.app.src.models.auth.user` після її визначення.

    Поля, що очікуються залежностями:
    - id (int): Унікальний ідентифікатор користувача.
    - email (str): Електронна пошта користувача.
    - is_active (bool): Прапорець активності користувача.
    - is_superuser (bool): Прапорець, чи є користувач суперкористувачем.
    """
    id: int
    email: str
    is_active: bool
    is_superuser: bool

    def __init__(self, id: int, email: str, is_active: bool = True, is_superuser: bool = False):
        self.id = id
        self.email = email
        self.is_active = is_active
        self.is_superuser = is_superuser

# TODO: Замінити TokenPayload на імпорт реальної Pydantic схеми, наприклад:
# from backend.app.src.schemas.auth.token import TokenPayload
# Наразі TokenPayload є схемою-заповнювачем.
class TokenPayload(BaseModel):
    """
    Схема-заповнювач для корисного навантаження JWT токена (TokenPayload).

    ВАЖЛИВО: Ця схема ПОВИННА БУТИ ЗАМІНЕНА на імпорт реальної схеми TokenPayload
    з `backend.app.src.schemas.auth.token` після її визначення.

    Поля, що очікуються залежностями:
    - sub (Optional[str]): Ідентифікатор суб'єкта (зазвичай email або ID користувача).
    - user_id (Optional[int]): Явний ID користувача, якщо 'sub' використовується для іншого.
    - type (Optional[str]): Тип токена ("access" або "refresh").
    - exp (Optional[int]): Час закінчення терміну дії токена (timestamp).
    - iss (Optional[str]): Видавець токена (перевіряється в decode_token).
    - aud (Optional[str]): Аудиторія токена (перевіряється в decode_token).
    """
    sub: Optional[str] = None
    user_id: Optional[int] = None
    type: Optional[str] = None
    # exp, iss, aud тут не потрібні, оскільки вони використовуються та перевіряються decode_token


# `OAuth2PasswordBearer` - це клас FastAPI, що допомагає отримувати токени Bearer
# з заголовка "Authorization".
# `tokenUrl` має вказувати на ендпоінт для входу в систему (де користувач отримує токен).
reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login/access-token" # Оновлено для відповідності типовому ендпоінту
)

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(reusable_oauth2)
) -> UserModel: # Тип повернення має бути реальним UserModel
    """
    Залежність FastAPI для отримання поточного автентифікованого користувача з JWT токена.

    Виконує декодування токена, перевірку його типу ("access") та отримання
    користувача з бази даних (наразі через логіку-заповнювач).

    Args:
        db (AsyncSession): Асинхронна сесія бази даних.
        token (str): JWT токен, отриманий з заголовка Authorization.

    Returns:
        UserModel: Об'єкт користувача, якщо автентифікація успішна.

    Raises:
        HTTPException (401): Якщо токен недійсний, прострочений, має неправильний тип,
                             або якщо користувача не знайдено.
        HTTPException (400): Якщо корисне навантаження токена пошкоджене або не містить
                             необхідних даних.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не вдалося перевірити облікові дані", # TODO i18n: Translatable message. Повідомлення для кінцевого користувача
        headers={"WWW-Authenticate": "Bearer"},
    )
    malformed_payload_exception = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Пошкоджене або неповне корисне навантаження токена" # TODO i18n: Translatable message. Повідомлення для кінцевого користувача
    )

    payload = decode_token(token) # decode_token вже логує помилки JWT
    if payload is None:
        # decode_token поверне None, якщо токен недійсний (прострочений, невірний підпис, iss, aud тощо)
        # Логування вже відбулося в decode_token.
        raise credentials_exception

    try:
        token_data = TokenPayload(**payload)
    except ValidationError as e:
        logger.warning(f"Помилка валідації TokenPayload: {e}", exc_info=True)
        raise malformed_payload_exception

    if token_data.type != "access":
        logger.warning(f"Отримано невірний тип токена: '{token_data.type}'. Очікувався 'access'.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недійсний тип токена, очікується токен доступу.", # TODO i18n: Translatable message
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_identifier = token_data.sub or (str(token_data.user_id) if token_data.user_id is not None else None)
    if user_identifier is None:
        logger.warning("Ідентифікатор користувача (sub або user_id) відсутній у токені.")
        raise malformed_payload_exception

    # --- TODO: Замінити логіку-заповнювач на реальне отримання користувача з БД ---
    # Поточна логіка є лише для демонстрації та тестування.
    # У реальній системі тут має бути виклик до сервісу або репозиторію користувачів:
    # Наприклад:
    # from backend.app.src.services.auth.user_service import UserService # Потрібно створити
    # user_service = UserService(db)
    # current_user = await user_service.get_user_by_identifier(user_identifier)
    # Або напряму через репозиторій:
    # from backend.app.src.repositories.auth.user_repository import user_repository # Потрібно створити
    # current_user = await user_repository.get_by_email_or_id(db, identifier=user_identifier)

    current_user: Optional[UserModel] = None
    logger.debug(f"Спроба знайти користувача за ідентифікатором: {user_identifier}")
    if user_identifier == "testuser@example.com" or user_identifier == "123":
        current_user = UserModel(id=123, email="testuser@example.com", is_active=True, is_superuser=False)
        logger.info(f"Знайдено тестового користувача-заповнювача: {user_identifier}")
    elif user_identifier == settings.FIRST_SUPERUSER_EMAIL:
        current_user = UserModel(id=1, email=settings.FIRST_SUPERUSER_EMAIL, is_active=True, is_superuser=True)
        logger.info(f"Знайдено суперкористувача-заповнювача: {user_identifier}")
    # --- Кінець TODO блоку ---

    if current_user is None:
        logger.warning(f"Користувача з ідентифікатором '{user_identifier}' не знайдено в базі даних (або в логіці-заповнювачі).")
        raise credentials_exception

    logger.info(f"Користувач '{current_user.email}' (ID: {current_user.id}) успішно автентифікований.")
    return current_user

async def get_current_active_user(
    current_user: UserModel = Depends(get_current_user)
) -> UserModel:
    """
    Залежність FastAPI для отримання поточного активного користувача.

    Використовує `get_current_user` для отримання користувача та додатково
    перевіряє, чи є поле `is_active` користувача встановленим в `True`.

    Args:
        current_user (UserModel): Об'єкт користувача, отриманий з `get_current_user`.

    Returns:
        UserModel: Об'єкт автентифікованого та активного користувача.

    Raises:
        HTTPException (403): Якщо користувач неактивний.
    """
    if not current_user.is_active:
        logger.warning(f"Користувач '{current_user.email}' (ID: {current_user.id}) неактивний.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Неактивний користувач") # TODO i18n: Translatable message
    logger.debug(f"Користувач '{current_user.email}' (ID: {current_user.id}) активний.")
    return current_user

async def get_current_superuser(
    current_active_user: UserModel = Depends(get_current_active_user)
) -> UserModel:
    """
    Залежність FastAPI для отримання поточного активного суперкористувача.

    Використовує `get_current_active_user` для отримання активного користувача
    та додатково перевіряє, чи є поле `is_superuser` встановленим в `True`.

    Args:
        current_active_user (UserModel): Об'єкт активного користувача, отриманий з `get_current_active_user`.

    Returns:
        UserModel: Об'єкт автентифікованого, активного суперкористувача.

    Raises:
        HTTPException (403): Якщо користувач не є суперкористувачем.
    """
    # Перевіряємо наявність атрибута is_superuser перед доступом до нього,
    # оскільки UserModel є заповнювачем і може не мати цього поля в майбутніх реальних моделях,
    # хоча поточний заповнювач його має.
    if not hasattr(current_active_user, 'is_superuser') or not current_active_user.is_superuser:
        logger.warning(
            f"Користувач '{current_active_user.email}' (ID: {current_active_user.id}) "
            "не має прав суперкористувача."
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Недостатньо прав (потрібен статус суперкористувача)." # TODO i18n: Translatable message
        )
    logger.debug(f"Користувач '{current_active_user.email}' (ID: {current_active_user.id}) підтверджений як суперкористувач.")
    return current_active_user

# --- TODO: Реалізувати залежність get_current_group_admin ---
# Залежність для перевірки, чи є поточний користувач адміністратором вказаної групи.
# Ця залежність потребуватиме доступу до моделей Group, GroupMembership та, можливо,
# параметра шляху `group_id` (який можна отримати через `request.path_params` або FastAPI Path).
#
# Приклад сигнатури:
# from fastapi import Path
# async def get_current_group_admin(
#     current_active_user: UserModel = Depends(get_current_active_user),
#     group_id: int = Path(..., description="ID групи, до якої перевіряється доступ"), # Отримання group_id з шляху
#     db: AsyncSession = Depends(get_db)
# ) -> UserModel:
#     """
#     Перевіряє, чи є поточний активний користувач адміністратором (або вищою роллю,
#     наприклад, суперкористувачем) для вказаної групи.
#     """
#     logger.info(f"Перевірка прав адміністратора для користувача ID {current_active_user.id} у групі ID {group_id}")
#     # Спочатку перевіримо, чи є користувач суперкористувачем - суперкористувачі мають доступ до всього.
#     if hasattr(current_active_user, 'is_superuser') and current_active_user.is_superuser:
#         logger.debug(f"Користувач ID {current_active_user.id} є суперкористувачем, надано доступ до групи ID {group_id}.")
#         return current_active_user
#
#     # TODO: Тут має бути логіка запиту до бази даних для перевірки членства та ролі користувача в групі.
#     # Наприклад, з використанням сервісу або репозиторію:
#     # from backend.app.src.services.groups import GroupMembershipService # Потрібно створити
#     # membership_service = GroupMembershipService(db)
#     # role = await membership_service.get_user_role_in_group(user_id=current_active_user.id, group_id=group_id)
#     # if role not in [UserGroupRole.ADMIN, UserGroupRole.OWNER]: # Припустимо, є Enum UserGroupRole
#     #     logger.warning(f"Користувач ID {current_active_user.id} не є адміністратором групи ID {group_id}. Роль: {role}")
#     #     raise HTTPException(
#     # status_code=status.HTTP_403_FORBIDDEN,
#     # detail="Ви не є адміністратором цієї групи." # TODO i18n: Translatable message
#     #     )
#     # logger.info(f"Користувач ID {current_active_user.id} підтверджений як адміністратор групи ID {group_id}.")
#     # return current_active_user
#
#     # Тимчасова логіка-заповнювач (видалити після реалізації реальної логіки)
#     logger.warning(f"Логіка get_current_group_admin для групи ID {group_id} ще не реалізована. Тимчасово відхилено.")
#     raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Перевірка адміністратора групи ще не реалізована.") # TODO i18n: Translatable message


# Блок для демонстрації та базового тестування при прямому запуску модуля.
if __name__ == "__main__":
    # Зазвичай, залежності FastAPI тестуються через інтеграційні тести з TestClient.
    # Цей блок лише для базової демонстрації структури.
    logger.info("--- Демонстрація модуля залежностей FastAPI ---")
    logger.info("Створено екземпляр OAuth2PasswordBearer для URL токена:")
    logger.info(f"  reusable_oauth2.scheme.tokenUrl = {reusable_oauth2.scheme.tokenUrl}")

    logger.info("\nВизначені основні залежності:")
    logger.info("- get_current_user: Отримує користувача з токена (використовує UserModel-заповнювач).")
    logger.info("- get_current_active_user: Перевіряє, чи активний користувач, отриманий з get_current_user.")
    logger.info("- get_current_superuser: Перевіряє, чи є активний користувач суперкористувачем.")
    logger.info("- get_current_group_admin: Залежність-заповнювач для перевірки адміністратора групи (потребує реалізації).")

    logger.info("\nПримітка: Для повноцінного тестування цих залежностей потрібен TestClient FastAPI,")
    logger.info("а також макети (mocks) для взаємодії з базою даних та функцією decode_token.")

    # Приклад створення екземпляра TokenPayload-заповнювача
    try:
        payload_demo_data = {
            "sub": "user@example.com",
            "user_id": 1,
            "type": "access",
            "exp": int((datetime.now(timezone.utc) + timedelta(minutes=15)).timestamp())
        }
        token_payload_instance = TokenPayload(**payload_demo_data)
        logger.info(f"\nПриклад екземпляра TokenPayload (заповнювач): {token_payload_instance.model_dump_json(indent=2)}")
    except ValidationError as e:
        logger.error(f"\nПомилка при створенні тестового TokenPayload: {e}")

    # Демонстрація UserModel-заповнювача
    logger.info(f"\nСтруктура UserModel-заповнювача: id, email, is_active, is_superuser")
    dummy_user = UserModel(id=1, email="dummy@example.com", is_active=True, is_superuser=False)
    logger.info(f"  Створено фіктивного користувача (заповнювач): id={dummy_user.id}, email='{dummy_user.email}', active={dummy_user.is_active}")
    logger.info("ВАЖЛИВО: UserModel та TokenPayload є заповнювачами і мають бути замінені реальними імпортами.")
