# backend/app/src/api/v1/auth/password.py
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.dependencies import get_db_session, get_current_active_user
from app.src.models.auth import User as UserModel
from app.src.schemas.auth.password import ( # Assuming schemas are in password.py or similar
    PasswordChange,
    PasswordResetRequest,
    PasswordResetConfirm
)
from app.src.schemas.message import MessageResponse # A generic message response schema
from app.src.services.auth.user import UserService
from app.src.services.auth.token import TokenService # For password reset tokens
# from app.src.services.notifications.email import EmailNotificationService # If sending emails directly

router = APIRouter()

@router.post(
    "/password/change",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Зміна паролю користувача",
    description="Дозволяє аутентифікованому користувачу змінити свій пароль."
)
async def change_password(
    password_data: PasswordChange,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user),
    user_service: UserService = Depends() # UserService can be injected
):
    '''
    Змінює пароль поточного аутентифікованого користувача.

    - **current_password**: Поточний пароль користувача.
    - **new_password**: Новий пароль користувача.
    '''
    # `user_service` can be initialized inside or passed as a dependency
    if not hasattr(user_service, 'db_session') or user_service.db_session is None:
         user_service.db_session = db # Ensure service has db session

    if not await user_service.verify_user_password(user=current_user, password=password_data.current_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Поточний пароль невірний."
        )

    await user_service.update_password(user=current_user, new_password=password_data.new_password)

    # Додатково: можна інвалідувати всі активні сесії/токени користувача, крім поточного,
    # якщо це вимагається політикою безпеки. Це потребуватиме TokenService/UserSessionService.

    return MessageResponse(message="Пароль успішно змінено.")

@router.post(
    "/password/forgot",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Запит на відновлення паролю",
    description="Ініціює процес відновлення паролю для користувача за його email."
)
async def forgot_password(
    request_data: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session),
    user_service: UserService = Depends(),
    token_service: TokenService = Depends()
    # email_service: EmailNotificationService = Depends() # Для відправки email
):
    '''
    Надсилає інструкції для відновлення паролю, якщо користувач з таким email існує та активний.

    - **email**: Електронна пошта користувача.
    '''
    if not hasattr(user_service, 'db_session') or user_service.db_session is None:
         user_service.db_session = db
    if not hasattr(token_service, 'db_session') or token_service.db_session is None:
         token_service.db_session = db
    # if not hasattr(email_service, 'db_session') or email_service.db_session is None:
    #      email_service.db_session = db


    user = await user_service.user_repo.get_by_email(email=request_data.email)
    if user and user.is_active:
        # Генерація токена відновлення паролю
        reset_token = await token_service.create_password_reset_token(user_id=user.id)

        # Формування посилання для відновлення
        # frontend_reset_url = f"https://your-frontend.com/reset-password?token={reset_token}"

        # Надсилання email у фоновому режимі
        # background_tasks.add_task(
        #     email_service.send_password_reset_email,
        #     recipient_email=user.email,
        #     username=user.first_name or user.email, # Або інше ім'я для персоналізації
        #     reset_link=frontend_reset_url
        # )
        # Поки що, без реальної відправки email, просто логуємо або повертаємо токен (не для продакшену!)
        print(f"Password reset token for {user.email}: {reset_token}") # Тільки для розробки!

    # Важливо: Завжди повертати однакову відповідь, незалежно від того,
    # чи знайдено користувача, щоб не розкривати інформацію про існування email.
    return MessageResponse(
        message="Якщо ваша пошта зареєстрована, ви отримаєте лист з інструкціями для відновлення паролю."
    )

@router.post(
    "/password/reset",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Встановлення нового паролю",
    description="Встановлює новий пароль, використовуючи токен відновлення."
)
async def reset_password(
    reset_data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db_session),
    user_service: UserService = Depends(),
    token_service: TokenService = Depends()
):
    '''
    Встановлює новий пароль для користувача.

    - **token**: Токен відновлення паролю.
    - **new_password**: Новий пароль.
    '''
    if not hasattr(user_service, 'db_session') or user_service.db_session is None:
         user_service.db_session = db
    if not hasattr(token_service, 'db_session') or token_service.db_session is None:
         token_service.db_session = db

    try:
        user_id = await token_service.verify_password_reset_token(token=reset_data.token)
        if not user_id: # Або якщо verify_password_reset_token кидає виняток при невалідному токені
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Невалідний або прострочений токен відновлення паролю."
            )

        user = await user_service.user_repo.get_by_id(id=user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Користувача не знайдено, він неактивний, або токен недійсний."
            )

        await user_service.update_password(user=user, new_password=reset_data.new_password)

        # Додатково: Інвалідувати токен відновлення після успішного використання.
        # Це може бути частиною логіки `verify_password_reset_token` або окремим кроком.
        # await token_service.invalidate_password_reset_token(token=reset_data.token)

        return MessageResponse(message="Пароль успішно скинуто та встановлено новий.")

    except HTTPException as http_exc: # Перехоплюємо HTTP винятки, щоб не потрапити в загальний Exception
        raise http_exc
    except Exception as e: # Для інших помилок (наприклад, токен невалідний з іншої причини)
        # Логування помилки e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Помилка скидання паролю. Можливо, токен недійсний або прострочений. {str(e)}"
        )

# Міркування:
# 1. Схеми: Потрібні Pydantic схеми `PasswordChange`, `PasswordResetRequest`, `PasswordResetConfirm`.
#    Вони можуть бути в `backend/app/src/schemas/auth/password.py` або `login.py`.
#    `MessageResponse` - загальна схема для повідомлень.
# 2. Сервіси:
#    - `UserService`: методи `verify_user_password`, `update_password`.
#    - `TokenService`: методи `create_password_reset_token`, `verify_password_reset_token`.
#      Токени відновлення паролю повинні бути короткоживучими та одноразовими.
#    - `EmailNotificationService` (або аналог): для надсилання email з посиланням/кодом відновлення.
#      Ця частина закоментована, оскільки вимагає налаштування відправки email.
# 3. Безпека:
#    - Захист від enumeration атак: ендпоінт `/password/forgot` завжди повертає однакову відповідь.
#    - Токени відновлення: мають бути безпечно згенеровані, збережені (якщо потрібно) та валідовані.
# 4. Залежності: `get_current_active_user` для `/password/change`. `BackgroundTasks` для асинхронної відправки email.
# 5. Коментарі: Українською мовою.
# 6. Ініціалізація сервісів: Показано приклад передачі `db` сесії в сервіси, якщо вони ініціалізуються як залежності FastAPI без прямого доступу до сесії. Краще, якщо сервіси отримують сесію при ініціалізації через свої конструктори, а FastAPI залежності просто створюють екземпляри сервісів.
#    Приклад `user_service: UserService = Depends()` припускає, що `UserService` може бути залежністю FastAPI.
#    Якщо `UserService` ініціалізується як `UserService(db)`, то `Depends()` не потрібен для самого сервісу, а лише для `db`.
#    Я залишив `Depends()` для сервісів, припускаючи, що вони можуть бути налаштовані як залежності, що отримують `db` всередині.
#    Наприклад, `class UserService: def __init__(self, session: AsyncSession = Depends(get_db_session)): self.db_session = session ...`
#    Якщо ні, то `user_service = UserService(db)` є правильним підходом в кожній функції.
#    Я додав перевірку `hasattr(user_service, 'db_session')` для гнучкості.
