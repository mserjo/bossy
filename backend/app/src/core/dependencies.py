# backend/app/src/core/dependencies.py
# -*- coding: utf-8 -*-
# # Модуль загальних залежностей (dependencies) для FastAPI програми Kudos (Virtus).
# #
# # Цей модуль визначає функції-залежності, які використовуються в обробниках
# # запитів FastAPI для реалізації таких завдань, як автентифікація користувача
# # (через JWT токени), перевірка активності користувача та його прав доступу
# # (наприклад, чи є користувач суперкористувачем).
# #
# # Важливо: Класи `UserModel` та `TokenPayload` у цьому файлі є тимчасовими
# # заповнювачами (placeholders). Вони ПОВИННІ БУТИ ЗАМІНЕНІ реальними імпортами
# # моделей та схем з відповідних модулів (`backend.app.src.models.auth.user`
# # та `backend.app.src.schemas.auth.token`) після їх створення або рефакторингу.

from typing import Optional, Any # AsyncGenerator було видалено, оскільки не використовується в цьому файлі.
from fastapi import Depends, HTTPException, status # Path тут не використовується.
from fastapi.security import OAuth2PasswordBearer
# from jose import JWTError # Закоментовано, оскільки decode_token вже обробляє JWTError та його підтипи.
from pydantic import BaseModel, ValidationError # BaseModel для TokenPayload-заповнювача.
from datetime import datetime, timezone, timedelta # Використовується в __main__ для прикладу.

# Абсолютні імпорти з проекту
from backend.app.src.config.settings import settings
from backend.app.src.config.security import decode_token
from backend.app.src.config.database import get_db, AsyncSession # AsyncSession для типізації db.
from backend.app.src.config.logging import get_logger # Імпорт логера.

# Отримання логера для цього модуля
logger = get_logger(__name__)

# TODO: (ВАЖЛИВО) Замінити UserModel на імпорт реальної моделі користувача, наприклад:
# from backend.app.src.models.auth.user import User as UserModel # Шлях може відрізнятися
# Наразі UserModel є класом-заповнювачем для демонстрації структури та функціональності.
class UserModel:
    """
    Клас-заповнювач (placeholder) для моделі користувача (User).

    ВАЖЛИВО: Цей клас ПОВИНЕН БУТИ ЗАМІНЕНИЙ на імпорт реальної моделі User
    з `backend.app.src.models.auth.user` (або відповідного шляху) після її визначення.

    Поля, що очікуються залежностями `get_current_user` та похідними:
    - `id` (int): Унікальний ідентифікатор користувача.
    - `email` (str): Електронна пошта користувача.
    - `is_active` (bool): Прапорець активності облікового запису користувача.
    - `is_superuser` (bool): Прапорець, чи є користувач суперкористувачем системи.
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

# TODO: (ВАЖЛИВО) Замінити TokenPayload на імпорт реальної Pydantic схеми, наприклад:
# from backend.app.src.schemas.auth.token import TokenPayload # Шлях може відрізнятися
# Наразі TokenPayload є схемою-заповнювачем для валідації корисного навантаження токена.
class TokenPayload(BaseModel):
    """
    Схема-заповнювач (placeholder) для корисного навантаження JWT токена (TokenPayload).

    ВАЖЛИВО: Ця схема ПОВИННА БУТИ ЗАМІНЕНА на імпорт реальної схеми TokenPayload
    з `backend.app.src.schemas.auth.token` (або відповідного шляху) після її визначення.

    Поля, що очікуються залежностями при розкодуванні токена:
    - `sub` (Optional[str]): Ідентифікатор суб'єкта (зазвичай email або ID користувача).
                             Використовується як основний ідентифікатор для пошуку користувача.
    - `user_id` (Optional[int]): Явний ID користувача, якщо `sub` використовується для іншого
                                 (наприклад, якщо `sub` - це email, а `user_id` - числовий ID).
    - `type` (Optional[str]): Тип токена ("access" або "refresh"). Перевіряється для запобігання
                              використання токена оновлення замість токена доступу.
    - `exp` (Optional[int]): Час закінчення терміну дії токена (timestamp). Валідується функцією `decode_token`.
    - `iss` (Optional[str]): Видавець токена. Валідується функцією `decode_token`.
    - `aud` (Optional[str]): Аудиторія токена. Валідується функцією `decode_token`.
    """
    sub: Optional[str] = None # Subject (ідентифікатор користувача, часто email)
    user_id: Optional[int] = None # Додатковий ID користувача, якщо sub - не числовий ID
    type: Optional[str] = None # Тип токена: "access" або "refresh"
    # Поля `exp`, `iss`, `aud` перевіряються функцією `decode_token` і тут не обов'язкові для валідації Pydantic,
    # оскільки їх наявність та валідність вже перевірено на етапі декодування JWT.


# `OAuth2PasswordBearer` - це клас FastAPI, що реалізує стандартний спосіб отримання токенів Bearer
# з HTTP-заголовка "Authorization".
# `tokenUrl` має вказувати на відносний шлях до ендпоінту FastAPI, який відповідає за видачу токенів
# (зазвичай це ендпоінт логіну, де користувач обмінює свої облікові дані на токен).
reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login/access-token" # Шлях до ендпоінту для отримання токена
)

async def get_current_user(
    db: AsyncSession = Depends(get_db), # Залежність для отримання сесії бази даних
    token: str = Depends(reusable_oauth2) # Залежність для отримання токена з запиту
) -> UserModel: # Тип повернення має бути реальним UserModel після заміни заповнювача
    """
    Залежність FastAPI для отримання поточного автентифікованого користувача з JWT токена.

    Виконує декодування JWT токена, перевірку його типу ("access") та отримання
    відповідного користувача з бази даних (наразі через логіку-заповнювач, яка потребує заміни).

    Args:
        db (AsyncSession): Асинхронна сесія бази даних, надана залежністю `get_db`.
        token (str): JWT токен, автоматично отриманий FastAPI з заголовка "Authorization: Bearer <token>".

    Returns:
        UserModel: Об'єкт користувача (зараз UserModel-заповнювач), якщо автентифікація успішна.

    Raises:
        HTTPException (401 Unauthorized): Якщо токен недійсний, прострочений, має неправильний тип,
                                          або якщо користувача з даними токена не знайдено.
        HTTPException (400 Bad Request): Якщо корисне навантаження токена пошкоджене або не містить
                                         необхідних ідентифікаційних даних (`sub` або `user_id`).
    """
    # TODO i18n: Translatable user-facing error message. "Не вдалося перевірити облікові дані"
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не вдалося перевірити облікові дані",
        headers={"WWW-Authenticate": "Bearer"}, # Стандартний заголовок для Bearer автентифікації
    )
    # TODO i18n: Translatable user-facing error message. "Пошкоджене або неповне корисне навантаження токена"
    malformed_payload_exception = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Пошкоджене або неповне корисне навантаження токена"
    )

    payload = decode_token(token) # `decode_token` з `config.security` вже обробляє помилки JWT та логує їх.
    if payload is None:
        # Якщо `decode_token` повернув `None`, це означає, що токен недійсний
        # (прострочений, невірний підпис, невірний `iss` або `aud` тощо).
        # Логування деталей помилки вже відбулося всередині `decode_token`.
        raise credentials_exception

    try:
        # Валідація структури корисного навантаження токена за допомогою схеми Pydantic.
        token_data = TokenPayload(**payload)
    except ValidationError as e:
        # i18n: Log message for developers. "Помилка валідації TokenPayload: {e}"
        logger.warning(f"Помилка валідації TokenPayload при отриманні поточного користувача: {e}", exc_info=True)
        raise malformed_payload_exception

    if token_data.type != "access":
        # i18n: Log message for developers. "Отримано невірний тип токена: '{token_data.type}'. Очікувався 'access'."
        logger.warning(f"Отримано невірний тип токена: '{token_data.type}'. Очікувався 'access'.")
        # TODO i18n: Translatable user-facing error message. "Недійсний тип токена, очікується токен доступу."
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недійсний тип токена, очікується токен доступу.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Визначаємо ідентифікатор користувача з токена (або `sub`, або `user_id`).
    user_identifier = token_data.sub or (str(token_data.user_id) if token_data.user_id is not None else None)
    if user_identifier is None:
        # i18n: Log message for developers. "Ідентифікатор користувача (sub або user_id) відсутній у токені."
        logger.warning("Ідентифікатор користувача (sub або user_id) відсутній у токені.")
        raise malformed_payload_exception

    # --- TODO: (ВАЖЛИВО) Замінити логіку-заповнювач на реальне отримання користувача з БД ---
    # Поточна логіка є лише для демонстрації та тестування.
    # У реальній системі тут має бути виклик до сервісу або репозиторію користувачів:
    # Наприклад (потрібно створити відповідні сервіси/репозиторії):
    # from backend.app.src.services.auth.user_service import UserService
    # user_service = UserService(db)
    # current_user = await user_service.get_user_by_identifier(identifier=user_identifier)
    # Або напряму через репозиторій:
    # from backend.app.src.repositories.auth.user_repository import user_repository
    # current_user = await user_repository.get_by_email_or_id(db, identifier=user_identifier)

    current_user: Optional[UserModel] = None # Явно ініціалізуємо, щоб уникнути UnboundLocalError
    # i18n: Log message for developers. "Спроба знайти користувача за ідентифікатором: {user_identifier}"
    logger.debug(f"Спроба знайти користувача за ідентифікатором: {user_identifier}")
    # Логіка-заповнювач для тестування:
    if user_identifier == "testuser@example.com" or user_identifier == "123":
        current_user = UserModel(id=123, email="testuser@example.com", is_active=True, is_superuser=False)
        # i18n: Log message for developers. "Знайдено тестового користувача-заповнювача: {user_identifier}"
        logger.info(f"Знайдено тестового користувача-заповнювача: {user_identifier}")
    elif user_identifier == settings.FIRST_SUPERUSER_EMAIL: # Використовуємо email з налаштувань
        current_user = UserModel(id=1, email=settings.FIRST_SUPERUSER_EMAIL, is_active=True, is_superuser=True)
        # i18n: Log message for developers. "Знайдено суперкористувача-заповнювача: {user_identifier}"
        logger.info(f"Знайдено суперкористувача-заповнювача: {user_identifier}")
    # --- Кінець TODO блоку ---

    if current_user is None:
        # i18n: Log message for developers. "Користувача з ідентифікатором '{user_identifier}' не знайдено..."
        logger.warning(f"Користувача з ідентифікатором '{user_identifier}' не знайдено в базі даних (або в логіці-заповнювачі).")
        raise credentials_exception # Викидаємо 401, оскільки токен валідний, але користувач не існує.

    # i18n: Log message for developers. "Користувач '{current_user.email}' (ID: {current_user.id}) успішно автентифікований."
    logger.info(f"Користувач '{current_user.email}' (ID: {current_user.id}) успішно автентифікований.")
    return current_user

async def get_current_active_user(
    current_user: UserModel = Depends(get_current_user) # Залежить від get_current_user
) -> UserModel: # Тип повернення має бути реальним UserModel
    """
    Залежність FastAPI для отримання поточного активного користувача.

    Використовує `get_current_user` для отримання користувача та додатково
    перевіряє, чи є поле `is_active` цього користувача встановленим в `True`.

    Args:
        current_user (UserModel): Об'єкт користувача, отриманий з залежності `get_current_user`.

    Returns:
        UserModel: Об'єкт автентифікованого та активного користувача.

    Raises:
        HTTPException (403 Forbidden): Якщо користувач неактивний.
    """
    if not current_user.is_active:
        # i18n: Log message for developers. "Користувач '{current_user.email}' (ID: {current_user.id}) неактивний."
        logger.warning(f"Користувач '{current_user.email}' (ID: {current_user.id}) неактивний.")
        # TODO i18n: Translatable user-facing error message. "Неактивний користувач"
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Неактивний користувач")
    # i18n: Log message for developers. "Користувач '{current_user.email}' (ID: {current_user.id}) активний."
    logger.debug(f"Користувач '{current_user.email}' (ID: {current_user.id}) активний.")
    return current_user

async def get_current_superuser(
    current_active_user: UserModel = Depends(get_current_active_user) # Залежить від get_current_active_user
) -> UserModel: # Тип повернення має бути реальним UserModel
    """
    Залежність FastAPI для отримання поточного активного суперкористувача.

    Використовує `get_current_active_user` для отримання активного користувача
    та додатково перевіряє, чи є поле `is_superuser` цього користувача встановленим в `True`.

    Args:
        current_active_user (UserModel): Об'єкт активного користувача, отриманий з `get_current_active_user`.

    Returns:
        UserModel: Об'єкт автентифікованого, активного суперкористувача.

    Raises:
        HTTPException (403 Forbidden): Якщо користувач не є суперкористувачем.
    """
    # Перевіряємо наявність атрибута is_superuser перед доступом до нього для більшої надійності,
    # особливо враховуючи, що UserModel є заповнювачем.
    if not hasattr(current_active_user, 'is_superuser') or not current_active_user.is_superuser:
        # i18n: Log message for developers. "Користувач '{current_active_user.email}' ... не має прав суперкористувача."
        logger.warning(
            f"Користувач '{current_active_user.email}' (ID: {current_active_user.id}) "
            "не має прав суперкористувача."
        )
        # TODO i18n: Translatable user-facing error message. "Недостатньо прав (потрібен статус суперкористувача)."
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Недостатньо прав (потрібен статус суперкористувача)."
        )
    # i18n: Log message for developers. "Користувач '{current_active_user.email}' ... підтверджений як суперкористувач."
    logger.debug(f"Користувач '{current_active_user.email}' (ID: {current_active_user.id}) підтверджений як суперкористувач.")
    return current_active_user

# --- TODO: (ВАЖЛИВО) Реалізувати залежність get_current_group_admin ---
# Залежність для перевірки, чи є поточний користувач адміністратором вказаної групи.
# Ця залежність потребуватиме доступу до моделей Group, GroupMembership та, можливо,
# параметра шляху `group_id` (який можна отримати через `fastapi.Path`).
#
# Приклад сигнатури та базової логіки:
# from fastapi import Path # Потрібно буде імпортувати Path
# async def get_current_group_admin(
#     current_active_user: UserModel = Depends(get_current_active_user),
#     group_id: int = Path(..., description="ID групи, до якої перевіряється доступ адміністратора"),
#     db: AsyncSession = Depends(get_db)
# ) -> UserModel:
#     """
#     Перевіряє, чи є поточний активний користувач адміністратором (або власником)
#     вказаної групи, або чи є він суперкористувачем системи.
#     """
#     logger.info(f"Перевірка прав адміністратора/власника для користувача ID {current_active_user.id} у групі ID {group_id}")
#
#     # Суперкористувачі мають доступ до адміністрування будь-якої групи.
#     if hasattr(current_active_user, 'is_superuser') and current_active_user.is_superuser:
#         logger.debug(f"Користувач ID {current_active_user.id} є суперкористувачем, надано доступ до адміністрування групи ID {group_id}.")
#         return current_active_user
#
#     # TODO: Тут має бути реальна логіка запиту до бази даних для перевірки членства та ролі користувача в групі.
#     # Наприклад, з використанням сервісу або репозиторію:
#     # from backend.app.src.services.groups.group_membership_service import GroupMembershipService # Потрібно створити
#     # from backend.app.src.core.dicts import GroupRole # Потрібно імпортувати
#     # membership_service = GroupMembershipService(db)
#     # user_role_in_group = await membership_service.get_user_role_in_group(user_id=current_active_user.id, group_id=group_id)
#     #
#     # if user_role_in_group not in [GroupRole.ADMIN, GroupRole.OWNER]:
#     #     logger.warning(f"Користувач ID {current_active_user.id} не є адміністратором або власником групи ID {group_id}. Поточна роль: {user_role_in_group}")
#     #     # TODO i18n: Translatable user-facing error message. "Ви не є адміністратором або власником цієї групи."
#     #     raise HTTPException(
#     #         status_code=status.HTTP_403_FORBIDDEN,
#     #         detail="Ви не є адміністратором або власником цієї групи."
#     #     )
#     # logger.info(f"Користувач ID {current_active_user.id} підтверджений як адміністратор/власник групи ID {group_id}.")
#     # return current_active_user
#
#     # Тимчасова логіка-заповнювач (видалити після реалізації реальної логіки):
#     # i18n: Log message for developers. "Логіка get_current_group_admin для групи ID {group_id} ще не реалізована."
#     logger.warning(f"Логіка get_current_group_admin для групи ID {group_id} ще не реалізована. Тимчасово відхилено.")
#     # TODO i18n: Translatable user-facing error message. "Перевірка адміністратора групи ще не реалізована."
#     raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Перевірка адміністратора групи ще не реалізована.")


# Блок для демонстрації та базового тестування при прямому запуску модуля.
if __name__ == "__main__":
    # Зазвичай, залежності FastAPI тестуються через інтеграційні тести з використанням TestClient.
    # Цей блок лише для базової демонстрації структури та обговорення.
    logger.info("--- Демонстрація Модуля Залежностей FastAPI (`core.dependencies`) ---")
    logger.info("Створено екземпляр OAuth2PasswordBearer для URL токена:")
    logger.info(f"  reusable_oauth2.scheme.tokenUrl = {reusable_oauth2.scheme.tokenUrl}")

    logger.info("\nВизначені основні залежності для автентифікації та авторизації:")
    logger.info("  - `get_current_user`: Отримує користувача з JWT токена (наразі використовує UserModel-заповнювач).")
    logger.info("  - `get_current_active_user`: Перевіряє, чи активний користувач, отриманий з `get_current_user`.")
    logger.info("  - `get_current_superuser`: Перевіряє, чи є активний користувач також суперкористувачем.")
    logger.info("  - `get_current_group_admin` (TODO): Залежність-заповнювач для перевірки прав адміністратора групи (потребує повної реалізації).")

    logger.info("\nВажливі примітки щодо цього модуля:")
    logger.info("  1. Класи `UserModel` та `TokenPayload` є тимчасовими заповнювачами (placeholders).")
    logger.info("     Вони ОБОВ'ЯЗКОВО мають бути замінені на імпорти реальних моделей та схем Pydantic")
    logger.info("     з відповідних модулів (наприклад, `backend.app.src.models.auth.user` та `backend.app.src.schemas.auth.token`).")
    logger.info("  2. Логіка отримання користувача з бази даних в `get_current_user` наразі є фіктивною (placeholder).")
    logger.info("     Її потрібно замінити на реальні запити до БД через сервісний шар або репозиторії.")
    logger.info("  3. Для повноцінного тестування цих залежностей потрібен TestClient FastAPI,")
    logger.info("     а також макети (mocks) для взаємодії з базою даних та функцією `decode_token`,")
    logger.info("     або реальна інфраструктура для інтеграційних тестів.")

    # Приклад створення екземпляра TokenPayload-заповнювача для демонстрації
    try:
        payload_demo_data = {
            "sub": "user@example.com",
            "user_id": 1,
            "type": "access",
            "exp": int((datetime.now(timezone.utc) + timedelta(minutes=15)).timestamp()) # Приклад часу життя
        }
        token_payload_instance = TokenPayload(**payload_demo_data)
        logger.info(f"\nПриклад успішного створення екземпляра TokenPayload (заповнювач): {token_payload_instance.model_dump_json(indent=2)}")
    except ValidationError as e:
        logger.error(f"\nПомилка при створенні тестового екземпляра TokenPayload: {e}")

    # Демонстрація UserModel-заповнювача
    logger.info(f"\nСтруктура UserModel-заповнювача: id (int), email (str), is_active (bool), is_superuser (bool)")
    dummy_user = UserModel(id=999, email="dummy.user@example.com", is_active=True, is_superuser=False)
    logger.info(f"  Створено фіктивного користувача (заповнювач): id={dummy_user.id}, email='{dummy_user.email}', is_active={dummy_user.is_active}, is_superuser={dummy_user.is_superuser}")
    logger.info("\nВАЖЛИВО: Нагадування - UserModel та TokenPayload є заповнювачами і мають бути замінені реальними імпортами.")
