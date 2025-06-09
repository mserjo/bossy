# backend/app/src/core/dependencies.py

"""
Цей модуль визначає загальні залежності FastAPI, зокрема для автентифікації
та авторизації, наприклад, отримання поточного користувача з токена.
"""

from typing import Optional, AsyncGenerator
from fastapi import Depends, HTTPException, status, Path
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from pydantic import BaseModel, ValidationError # Додано BaseModel для TokenPayload
from datetime import datetime, timezone, timedelta # Додано для прикладу в __main__

from backend.app.src.config.settings import settings
from backend.app.src.config.security import decode_token
from backend.app.src.config.database import get_db, AsyncSession
# Зазвичай імпортують моделі користувачів та сервіс/репозиторій для отримання даних користувача
# Наразі ми будемо використовувати заповнювач. Їх слід замінити на фактичні імпорти
# from backend.app.src.models.auth import User as UserModel # Заповнювач
# from backend.app.src.services.auth.user import UserService # Заповнювач
# from backend.app.src.schemas.auth.token import TokenPayload # Заповнювач для схеми корисного навантаження токена

# Це заповнювач для фактичної моделі User. Замініть на імпорт вашої моделі User.
class UserModel:
    id: int
    email: str
    is_active: bool
    is_superuser: bool
    # Додайте інші відповідні поля, такі як ролі, членство в групах тощо.
    def __init__(self, id: int, email: str, is_active: bool = True, is_superuser: bool = False):
        self.id = id
        self.email = email
        self.is_active = is_active
        self.is_superuser = is_superuser

# Це заповнювач для фактичної схеми TokenPayload. Замініть на вашу схему Pydantic.
class TokenPayload(BaseModel): # Успадкування від BaseModel
    sub: Optional[str] = None # 'sub' зазвичай зберігає ідентифікатор користувача (наприклад, email або user_id)
    user_id: Optional[int] = None # Або використовуйте user_id безпосередньо, якщо це ваш 'sub'
    type: Optional[str] = None # Для розрізнення токенів доступу та оновлення

# OAuth2PasswordBearer - це утилітарний клас FastAPI, який обробляє вилучення токена
# з заголовка Authorization (токен Bearer).
# `tokenUrl` повинен вказувати на ваш ендпоінт входу, де видаються токени.
reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login" # Приклад ендпоінту входу
)

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(reusable_oauth2)
) -> UserModel: # Повинен повертати ваш фактичний тип моделі User
    """
    Залежність FastAPI для отримання поточного користувача з JWT токена.

    Args:
        db (AsyncSession): Залежність сесії бази даних.
        token (str): JWT токен, вилучений з заголовка Authorization.

    Returns:
        UserModel: Об'єкт автентифікованого користувача з бази даних.

    Raises:
        HTTPException (401): Якщо токен недійсний, прострочений або користувача не знайдено.
        HTTPException (400): Якщо корисне навантаження токена пошкоджено.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не вдалося перевірити облікові дані",
        headers={"WWW-Authenticate": "Bearer"},
    )
    malformed_payload_exception = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Пошкоджене корисне навантаження токена"
    )

    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    try:
        token_data = TokenPayload(**payload)
    except ValidationError:
        raise malformed_payload_exception

    if token_data.type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недійсний тип токена, очікується токен 'access'.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_identifier = token_data.sub or (str(token_data.user_id) if token_data.user_id else None)
    if user_identifier is None:
        raise malformed_payload_exception

    # --- Отримання користувача з бази даних ---
    # Цю частину потрібно адаптувати до вашої фактичної логіки сервісу/репозиторію користувачів.
    # user_service = UserService(db) # Приклад створення екземпляра
    # current_user = await user_service.get_user_by_email(email=user_identifier) # Якщо 'sub' - це email
    # Або: current_user = await user_service.get_user_by_id(id=int(user_identifier)) # Якщо 'sub' - це user_id

    # Логіка-заповнювач для отримання користувача:
    # У реальній програмі ви б запитували базу даних, використовуючи user_identifier з токена.
    # Для демонстрації ми створимо фіктивного користувача, якщо ідентифікатор відповідає шаблону.
    # Замініть це на фактичний пошук у базі даних.
    if user_identifier == "testuser@example.com" or user_identifier == "123":
        # Це фіктивний користувач. Замініть на фактичний пошук у БД.
        # Переконайтеся, що структура UserModel відповідає вашій фактичній моделі User.
        current_user = UserModel(id=123, email="testuser@example.com", is_active=True)
    elif user_identifier == settings.FIRST_SUPERUSER_EMAIL:
        current_user = UserModel(id=1, email=settings.FIRST_SUPERUSER_EMAIL, is_active=True, is_superuser=True)
    else:
        current_user = None # Користувача не знайдено
    # --- Кінець логіки-заповнювача для отримання користувача ---

    if current_user is None:
        raise credentials_exception # Користувача не знайдено в БД

    return current_user

async def get_current_active_user(
    current_user: UserModel = Depends(get_current_user)
) -> UserModel:
    """
    Залежність FastAPI для отримання поточного активного користувача.
    Базується на `get_current_user` і перевіряє, чи активний користувач.

    Args:
        current_user (UserModel): Об'єкт користувача, отриманий з `get_current_user`.

    Returns:
        UserModel: Об'єкт автентифікованого та активного користувача.

    Raises:
        HTTPException (403): Якщо користувач неактивний.
    """
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Неактивний користувач")
    return current_user

async def get_current_superuser(
    current_active_user: UserModel = Depends(get_current_active_user)
) -> UserModel:
    """
    Залежність FastAPI для отримання поточного активного суперкористувача.
    Базується на `get_current_active_user` і перевіряє, чи є користувач суперкористувачем.

    Args:
        current_active_user (UserModel): Об'єкт користувача з `get_current_active_user`.

    Returns:
        UserModel: Об'єкт автентифікованого, активного та суперкористувача.

    Raises:
        HTTPException (403): Якщо користувач не є суперкористувачем.
    """
    if not hasattr(current_active_user, 'is_superuser') or not current_active_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Користувач не має прав суперкористувача."
        )
    return current_active_user

# Заповнювач для залежності адміністратора групи - це потребуватиме більше контексту
# from backend.app.src.models.groups import GroupMembershipModel # Заповнювач
# from backend.app.src.core.dicts import GroupRole # Заповнювач

# async def get_current_group_admin(
#     current_active_user: UserModel = Depends(get_current_active_user),
#     group_id: int = Path(..., title="ID групи"), # Припускаючи, що group_id є параметром шляху
#     db: AsyncSession = Depends(get_db)
# ) -> UserModel:
#     """
#     Залежність FastAPI для перевірки, чи є поточний користувач адміністратором конкретної групи.
#     Це складніша залежність, яка потребує вашої фактичної моделі GroupMembership та логіки.
#     """
#     # Приклад логіки (потребує ваших фактичних моделей та репозиторію/сервісу):
#     # membership = await GroupMembershipRepository(db).get_by_user_and_group(
#     # user_id=current_active_user.id, group_id=group_id
#     # )
#     # if not membership or membership.role != GroupRole.ADMIN:
#     #     raise HTTPException(
#     # status_code=status.HTTP_403_FORBIDDEN,
#     # detail="Користувач не є адміністратором цієї групи."
#     #     )
#     # return current_active_user
#     # Наразі, для тестування, дозволимо, якщо користувач є суперкористувачем
#     if hasattr(current_active_user, 'is_superuser') and current_active_user.is_superuser:
#         return current_active_user
#     raise HTTPException(status_code=403, detail="Не є адміністратором групи (логіка-заповнювач)")


if __name__ == "__main__":
    # Цей модуль визначає залежності для FastAPI і зазвичай не запускається безпосередньо.
    # Тестування цих залежностей зазвичай включає інтеграційні тести з тестовим клієнтом FastAPI.
    print("--- Основні залежності (для FastAPI) ---")
    print("Створено екземпляр OAuth2PasswordBearer для URL токена:")
    print(f"  reusable_oauth2.scheme.tokenUrl = {reusable_oauth2.scheme.tokenUrl}")

    print("\nВизначені залежності:")
    print("- get_current_user: Декодує токен, отримує користувача з БД (заповнювач).")
    print("- get_current_active_user: Гарантує, що користувач з get_current_user активний.")
    print("- get_current_superuser: Гарантує, що користувач з get_current_active_user є суперкористувачем.")
    # print("- get_current_group_admin: Заповнювач для перевірки адміністратора групи.")

    print("\nПримітка: Для тестування цих залежностей зазвичай використовується TestClient FastAPI та макети взаємодії з базою даних/токенами.")

    # Приклад використання TokenPayload (хоча зазвичай він внутрішній для get_current_user)
    try:
        payload_data = {"sub": "user@example.com", "user_id": 1, "type": "access", "exp": datetime.now(timezone.utc) + timedelta(minutes=15)}
        token_payload_instance = TokenPayload(**payload_data)
        print(f"\nПриклад екземпляра TokenPayload: {token_payload_instance.model_dump_json(indent=2)}")
    except ValidationError as e:
        print(f"\nПомилка створення екземпляра TokenPayload: {e}")

    # Фактична UserModel надходила б з вашого модуля models.auth.user
    # Це лише для демонстрації структури класу-заповнювача
    print(f"\nСтруктура UserModel-заповнювача: id, email, is_active, is_superuser")
    dummy_user = UserModel(id=1, email="dummy@example.com", is_active=True, is_superuser=False)
    print(f"  Фіктивний користувач: id={dummy_user.id}, email='{dummy_user.email}', active={dummy_user.is_active}")
