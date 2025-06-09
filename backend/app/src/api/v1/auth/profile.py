# backend/app/src/api/v1/auth/profile.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.dependencies import get_db_session, get_current_active_user
from app.src.models.auth import User as UserModel
from app.src.schemas.auth.user import UserResponse, UserUpdate # UserUpdate може потребувати специфічних полів для профілю
from app.src.services.auth.user import UserService

router = APIRouter()

@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Отримання профілю поточного користувача",
    description="Повертає дані профілю для поточного аутентифікованого та активного користувача."
)
async def read_users_me(
    current_user: UserModel = Depends(get_current_active_user)
):
    '''
    Надає інформацію профілю поточного аутентифікованого користувача.
    '''
    # UserModel вже містить всі необхідні дані, Pydantic модель UserResponse відфільтрує потрібні.
    return current_user

@router.put(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Оновлення профілю поточного користувача",
    description="Дозволяє поточному аутентифікованому користувачу оновити дані свого профілю."
)
async def update_users_me(
    user_update_data: UserUpdate, # Схема для оновлення, може містити тільки дозволені поля
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user),
    user_service: UserService = Depends() # Або user_service = UserService(db)
):
    '''
    Оновлює профіль поточного аутентифікованого користувача.
    Дозволяє змінювати такі поля, як ім'я, прізвище, тощо.
    Email та пароль зазвичай змінюються через окремі ендпоінти.

    - **first_name**: Нове ім'я користувача (опціонально).
    - **last_name**: Нове прізвище користувача (опціонально).
    - **username**: Новий нікнейм (опціонально, якщо дозволено змінювати і він унікальний).
    - ... інші дозволені поля ...
    '''
    if not hasattr(user_service, 'db_session') or user_service.db_session is None:
         user_service.db_session = db

    # Перевірка, чи новий email (якщо дозволено змінювати) не зайнятий
    # Зазвичай email змінюється окремо або потребує підтвердження.
    # Якщо UserUpdate дозволяє зміну email:
    if user_update_data.email and user_update_data.email != current_user.email:
        existing_user = await user_service.user_repo.get_by_email(email=user_update_data.email)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Email '{user_update_data.email}' вже використовується іншим користувачем."
            )

    # Перевірка, чи новий username (якщо дозволено змінювати) не зайнятий
    if hasattr(user_update_data, 'username') and user_update_data.username and user_update_data.username != current_user.username:
         # Припускаючи, що UserUpdate може містити username і він має бути унікальним
        existing_username = await user_service.user_repo.get_by_username(username=user_update_data.username)
        if existing_username and existing_username.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Нікнейм '{user_update_data.username}' вже використовується іншим користувачем."
            )

    try:
        updated_user = await user_service.update_user(
            user=current_user,
            user_update_schema=user_update_data
        )
    except Exception as e: # Обробка можливих помилок від сервісу
        # Логування помилки e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Помилка оновлення профілю: {str(e)}"
        )

    if not updated_user:
        # Малоймовірно, якщо сервіс кидає виняток або повертає оновленого користувача
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не вдалося оновити профіль користувача."
        )

    return UserResponse.model_validate(updated_user)

# Міркування:
# 1. Схеми:
#    - `UserResponse`: Для повернення даних профілю (має виключати пароль та інші чутливі дані).
#    - `UserUpdate`: Схема для оновлення профілю. Важливо, щоб ця схема містила тільки ті поля,
#      які користувач може безпечно змінювати (наприклад, не is_active, is_superuser).
#      Зміна email та пароля зазвичай виноситься в окремі, більш захищені процеси.
#      Якщо `UserUpdate` дозволяє змінювати email, потрібна додаткова логіка (наприклад, підтвердження нового email).
# 2. Сервіс `UserService`:
#    - Метод `update_user(user: UserModel, user_update_schema: UserUpdate) -> UserModel`.
#      Цей метод повинен безпечно оновлювати поля користувача.
# 3. Безпека:
#    - Користувач може редагувати тільки свій профіль (забезпечується `get_current_active_user`).
#    - Поля, які не можна змінювати користувачем напряму (ролі, статус активації), не повинні бути в `UserUpdate`.
# 4. Унікальність полів: Якщо `UserUpdate` дозволяє змінювати поля, які мають бути унікальними (email, username),
#    потрібна перевірка на унікальність перед оновленням (як показано в прикладі).
# 5. Коментарі: Українською мовою.
# 6. Залежності: `get_current_active_user` для отримання поточного користувача.
# 7. `UserUpdate` схема:
#    Потрібно ретельно визначити, які поля можуть бути в `UserUpdate`. Наприклад:
'''
# В app/src/schemas/auth/user.py
# ...
class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[constr(min_length=3)] = None # Якщо username можна змінювати
    email: Optional[EmailStr] = None # Якщо email можна змінювати (потребує обережності та, можливо, підтвердження)
    # НЕ додавати сюди: is_active, is_superuser, hashed_password, user_role_id тощо.
    # Ці поля мають керуватися адміністраторами або через спеціальні процеси.

    class Config:
        extra = "forbid" # Забороняє передачу полів, не визначених у схемі
'''
# Ця частина з визначенням схеми UserUpdate є контекстом.
