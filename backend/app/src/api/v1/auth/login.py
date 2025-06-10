# backend/app/src/api/v1/auth/login.py
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.config.security import create_access_token, create_refresh_token, verify_password
from app.src.core.dependencies import get_db_session, get_current_user_from_refresh_token, get_current_active_user # Припускаючи, що get_current_active_user призначений для захищених маршрутів, а не для самого входу
from app.src.models.auth import User, RefreshToken as RefreshTokenModel
from app.src.repositories.auth.user import UserRepository
from app.src.repositories.auth.token import RefreshTokenRepository
from app.src.schemas.auth.token import TokenResponse, RefreshTokenRequest
from app.src.schemas.auth.login import LoginRequest
from app.src.services.auth.session import UserSessionService # Для керування сесіями користувачів, якщо застосовно при вході/виході
from app.src.services.auth.token import TokenService

router = APIRouter()

@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Аутентифікація користувача",
    description="Аутентифікує користувача за допомогою email та пароля і повертає пару токенів доступу та оновлення."
)
async def login_for_access_token(
    response: Response,
    form_data: LoginRequest,
    db: AsyncSession = Depends(get_db_session)
):
    '''
    Аутентифікує користувача та видає токени.

    - **email**: Електронна пошта користувача.
    - **password**: Пароль користувача.
    '''
    user_repo = UserRepository(db)
    token_service = TokenService(db)

    user = await user_repo.get_by_email(email=form_data.email)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неправильний email або пароль.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Обліковий запис неактивний."
        )

    access_token = await token_service.create_access_token(user=user)
    refresh_token_value, refresh_token_db = await token_service.create_refresh_token(user=user)

    # Встановлюємо refresh_token в httpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token_value,
        httponly=True,
        secure=True, # Встановлювати в True для HTTPS
        samesite="lax", # або 'strict'
        # domain="example.com", # Вказати домен для production
        # path="/api/v1/auth", # Обмежити шлях дії cookie
        max_age=token_service.settings.REFRESH_TOKEN_EXPIRE_SECONDS
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token_value, # Повертаємо також у тілі відповіді для зручності клієнтів, які не можуть використовувати cookies
        token_type="bearer"
    )

@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Оновлення токена доступу",
    description="Оновлює токен доступу, використовуючи токен оновлення."
)
async def refresh_access_token(
    response: Response, # Додано для можливості оновлення cookie, якщо потрібно
    current_user_with_token: tuple[User, RefreshTokenModel] = Depends(get_current_user_from_refresh_token),
    db: AsyncSession = Depends(get_db_session)
):
    '''
    Оновлює токен доступу.
    Токен оновлення передається через httpOnly cookie або через тіло запиту.
    '''
    user, refresh_token_instance = current_user_with_token # Отримуємо користувача та екземпляр токена
    token_service = TokenService(db)

    if not user or not refresh_token_instance:
         raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недійсний токен оновлення.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Обліковий запис неактивний."
        )

    # Створюємо новий токен доступу
    new_access_token = await token_service.create_access_token(user=user)

    # Опціонально: розглянути можливість ротації токенів оновлення
    # new_refresh_token_value, new_refresh_token_db = await token_service.rotate_refresh_token(refresh_token_instance, user)
    # response.set_cookie(
    #     key="refresh_token",
    #     value=new_refresh_token_value,
    #     httponly=True,
    #     secure=True,
    #     samesite="lax",
    #     max_age=token_service.settings.REFRESH_TOKEN_EXPIRE_SECONDS
    # )
    # return TokenResponse(access_token=new_access_token, refresh_token=new_refresh_token_value, token_type="bearer")

    # Поки що без ротації, повертаємо старий refresh token, якщо він ще валідний, або новий access token
    # Якщо не ротуємо, то просто повертаємо новий access_token. Refresh token з cookie продовжує діяти.
    # У відповіді refresh_token може бути той самий, що і використовувався, якщо не було ротації.
    # Або, якщо клієнт очікує завжди отримувати refresh_token у відповіді:
    refresh_token_value = refresh_token_instance.token

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=refresh_token_value, # Повертаємо існуючий (або новий, якщо була ротація)
        token_type="bearer"
    )

@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Вихід користувача",
    description="Здійснює вихід користувача, інвалідуючи токен оновлення."
)
async def logout(
    response: Response,
    db: AsyncSession = Depends(get_db_session),
    # Захищаємо цей ендпоінт: тільки аутентифікований користувач може вийти
    # Використовуємо токен оновлення для ідентифікації сесії, яку треба завершити
    current_user_with_token: tuple[User, RefreshTokenModel] = Depends(get_current_user_from_refresh_token)
):
    '''
    Виконує вихід користувача.
    Інвалідує токен оновлення, що був переданий в httpOnly cookie.
    '''
    user, refresh_token_instance = current_user_with_token

    if not user or not refresh_token_instance:
        # Це не повинно трапитися, якщо get_current_user_from_refresh_token відпрацював правильно
        # але для безпеки можна додати перевірку
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Необхідна аутентифікація для виходу."
        )

    token_repo = RefreshTokenRepository(db)
    await token_repo.delete(refresh_token_instance.id) # Або позначити як використаний/відкликаний

    # Видаляємо cookie
    response.delete_cookie(
        key="refresh_token",
        # domain="example.com", # Має співпадати з налаштуваннями set_cookie
        # path="/api/v1/auth"   # Має співпадати з налаштуваннями set_cookie
    )

    # Додатково, якщо використовується UserSessionService для відслідковування активних сесій в БД
    # session_service = UserSessionService(db)
    # await session_service.terminate_session_by_refresh_token(refresh_token_instance.token)

    return Response(status_code=status.HTTP_204_NO_CONTENT)

# Додаткові міркування:
# 1. Безпека: Переконатися, що `secure=True` для cookies використовується в production (HTTPS).
# 2. Ротація токенів оновлення: Реалізувати, якщо потрібен вищий рівень безпеки.
#    При ротації старий токен оновлення інвалідується, і видається новий.
# 3. Обробка помилок: Додати більш детальну обробку можливих помилок від сервісів/репозиторіїв.
# 4. Залежності: Перевірити шляхи імпортів для `get_current_user_from_refresh_token` та інших залежностей.
#    Можливо, `get_current_user_from_refresh_token` потрібно буде адаптувати або створити спеціально для обробки refresh token з cookie.
# 5. `TokenService`: Переконатися, що `TokenService` має методи `create_access_token`, `create_refresh_token`,
#    а також доступ до налаштувань (REFRESH_TOKEN_EXPIRE_SECONDS).
# 6. `UserRepository`: Переконатися, що `get_by_email` існує та працює коректно.
# 7. `RefreshTokenRepository`: Переконатися, що методи для роботи з токенами оновлення (збереження, отримання, видалення) реалізовані.
# 8. CORS: Налаштувати CORS, якщо frontend та backend на різних доменах/портах.
