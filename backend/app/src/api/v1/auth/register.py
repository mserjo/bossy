# backend/app/src/api/v1/auth/register.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.dependencies import get_db_session
from app.src.models.auth import User as UserModel
from app.src.schemas.auth.user import UserCreate, UserResponse
from app.src.services.auth.user import UserService
# from app.src.services.auth.token import TokenService # Потенційно для автоматичного входу після реєстрації

router = APIRouter()

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Реєстрація нового користувача",
    description="Створює новий обліковий запис користувача в системі."
)
async def register_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db_session)
    # token_service: TokenService = Depends() # Якщо потрібна автоматична аутентифікація після реєстрації
):
    '''
    Реєструє нового користувача в системі.

    - **email**: Електронна пошта користувача (має бути унікальною).
    - **password**: Пароль користувача (буде хешовано перед збереженням).
    - **first_name**: Ім'я користувача (опціонально).
    - **last_name**: Прізвище користувача (опціонально).
    '''
    user_service = UserService(db)

    # Перевірка, чи користувач з таким email вже існує
    existing_user = await user_service.user_repo.get_by_email(email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Користувач з email '{user_in.email}' вже існує."
        )

    # Перевірка, чи користувач з таким нікнеймом вже існує, якщо нікнейм використовується і є унікальним
    if user_in.username: # Припускаючи, що username є в UserCreate і може бути унікальним
        existing_username = await user_service.user_repo.get_by_username(username=user_in.username)
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Користувач з нікнеймом '{user_in.username}' вже існує."
            )

    try:
        created_user = await user_service.create_user(user_create=user_in)
    except Exception as e: # Більш конкретна обробка помилок сервісу, якщо є
        # Наприклад, якщо сервіс кидає кастомні винятки
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Помилка під час створення користувача: {str(e)}"
        )

    if not created_user:
        # Цей випадок малоймовірний, якщо create_user або кидає виняток, або повертає користувача
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не вдалося створити користувача."
        )

    # Опціонально: автоматична аутентифікація після реєстрації
    # Треба буде повернути TokenResponse замість UserResponse, якщо це реалізовано.
    # access_token = await token_service.create_access_token(user=created_user)
    # refresh_token_value, _ = await token_service.create_refresh_token(user=created_user)
    # response.set_cookie(key="refresh_token", value=refresh_token_value, httponly=True, ...)
    # return TokenResponse(access_token=access_token, refresh_token=refresh_token_value, token_type="bearer")

    return UserResponse.model_validate(created_user)

# Міркування:
# 1. Унікальність полів: `UserService` або репозиторій повинні коректно обробляти обмеження унікальності на рівні БД.
#    Попередня перевірка в API (як показано для email та username) є хорошою практикою для надання користувачу зрозумілих помилок.
# 2. Валідація: Pydantic схеми (`UserCreate`) повинні містити всю необхідну валідацію для полів (довжина пароля, формат email тощо).
# 3. Пароль: `UserService.create_user` відповідає за хешування пароля перед збереженням. Пароль у відкритому вигляді не повинен логуватися або зберігатися.
# 4. Відповідь: Повернення `UserResponse` є стандартним. Якщо потрібна автоматична аутентифікація, відповідь та логіка мають бути змінені для повернення токенів.
# 5. Ролі та дозволи: За замовчуванням, новий користувач може отримувати стандартну роль (наприклад, "користувач"). Це має оброблятися в `UserService`.
# 6. Повідомлення: Розглянути можливість відправки вітального email або email для підтвердження пошти після реєстрації (це буде логіка сервісу).
# 7. `get_by_username`: Якщо поле `username` використовується, відповідний метод має бути в `UserRepository`.
