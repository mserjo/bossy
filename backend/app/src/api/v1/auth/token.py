# backend/app/src/api/v1/auth/token.py
from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError, jwt # Assuming jose for JWT operations, consistent with FastAPI examples
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.config.settings import settings_app # To get JWT_SECRET_KEY and ALGORITHM
from app.src.core.dependencies import get_db_session, get_current_active_superuser # Protected endpoint
from app.src.schemas.auth.token import TokenData, TokenVerifyRequest, TokenVerifyResponse
# TokenService might be needed if we interact with stored tokens or perform complex validation
# from app.src.services.auth.token import TokenService

router = APIRouter()

@router.post(
    "/token/verify",
    response_model=TokenVerifyResponse,
    status_code=status.HTTP_200_OK,
    summary="Перевірка валідності токена доступу",
    description="Перевіряє наданий токен доступу та повертає його розкодовані дані, якщо токен валідний. Доступно тільки суперкористувачам.",
    dependencies=[Depends(get_current_active_superuser)] # Захист ендпоінту
)
async def verify_access_token(
    token_data: TokenVerifyRequest,
    db: AsyncSession = Depends(get_db_session) # Якщо потрібен доступ до БД
    # token_service: TokenService = Depends() # Якщо потрібен сервіс
):
    '''
    Перевіряє валідність токена доступу.

    - **token**: Токен доступу (access token) для перевірки.
    '''
    try:
        payload = jwt.decode(
            token_data.token,
            settings_app.JWT_SECRET_KEY,
            algorithms=[settings_app.JWT_ALGORITHM]
        )
        username: str | None = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Некоректний формат токена: відсутній 'sub' (ідентифікатор користувача)."
            )

        # Тут можна додати додаткові перевірки, наприклад, чи існує користувач в БД,
        # чи не був токен відкликаний (якщо реалізовано такий механізм).
        # user_repo = UserRepository(db)
        # user = await user_repo.get_by_username(username=username) # Або get_by_id, якщо 'sub' це ID
        # if not user:
        #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Користувача з токена не знайдено")
        # if not user.is_active:
        #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Користувач з токена неактивний")

        return TokenVerifyResponse(
            valid=True,
            message="Токен валідний.",
            data=TokenData(**payload) # Перетворюємо payload в Pydantic модель
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Невалідний токен: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e: # Для інших непередбачених помилок
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Помилка перевірки токена: {str(e)}"
        )

# Міркування:
# 1. Призначення: Цей файл може бути розширений іншими ендпоінтами, пов'язаними з токенами,
#    якщо такі з'являться (наприклад, список активних токенів для користувача).
# 2. Захист: Ендпоінт `/token/verify` захищений і доступний тільки суперкористувачам (`get_current_active_superuser`).
#    Це важливо, оскільки він може розкривати вміст токенів.
# 3. Залежності: Використовує `jose` для декодування JWT, що є стандартним для FastAPI.
#    Потребує налаштувань `JWT_SECRET_KEY` та `JWT_ALGORITHM` з `settings_app`.
# 4. Pydantic схеми: `TokenVerifyRequest` для отримання токена, `TokenVerifyResponse` для відповіді,
#    та `TokenData` для представлення розкодованого вмісту токена. Ці схеми потрібно буде визначити в
#    `backend/app/src/schemas/auth/token.py`.
# 5. Розширення: Можна додати більш глибоку валідацію, наприклад, перевірку токена проти списку відкликаних токенів,
#    якщо така система реалізована (це вимагатиме взаємодії з `TokenService` або `RefreshTokenRepository`).
# 6. Коментарі: Весь код та коментарі надані українською мовою.

# Якщо інших операцій з токенами не передбачається, цей файл може залишитися таким,
# або його функціональність (якщо вона визнана непотрібною) може бути видалена,
# а сам файл - виключений з роутера.
# На даному етапі створюємо його згідно з планом.
