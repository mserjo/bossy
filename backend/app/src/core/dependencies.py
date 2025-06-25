# backend/app/src/core/dependencies.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає залежності (dependencies) FastAPI, які використовуються
в ендпоінтах для отримання спільних ресурсів (наприклад, сесії БД)
або для виконання перевірок (наприклад, автентифікація, авторизація).
"""

from fastapi import Depends, HTTPException, Security
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from jose import JWTError, jwt # type: ignore
from pydantic import ValidationError, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore
from typing import Optional, List, Any

# Імпорт налаштувань та утиліт
from backend.app.src.config.database import get_db_session # Фабрика сесій БД
from backend.app.src.config.settings import settings
from backend.app.src.config.security import ALGORITHM, SECRET_KEY # Параметри JWT
from backend.app.src.core.exceptions import UnauthorizedException, ForbiddenException, NotFoundException
# Імпорт констант для ролей (якщо перевірка ролей тут)
from backend.app.src.core.constants import ROLE_SUPERADMIN_CODE, ROLE_ADMIN_CODE, ROLE_USER_CODE
# Імпорт схем для токенів та користувачів
from backend.app.src.schemas.auth.token import TokenPayloadSchema
from backend.app.src.schemas.auth.user import UserSchema
# Імпорт сервісів (якщо залежності викликають сервіси, наприклад, для отримання користувача)
# from backend.app.src.services.auth.user_service import UserService # Приклад

# --- Залежність для OAuth2 (отримання токена з заголовка Authorization: Bearer <token>) ---
# `tokenUrl` вказує на ендпоінт, де клієнт може отримати токен (для документації Swagger).
# Це має бути відносний шлях до ендпоінта логіну.
# Наприклад, якщо ендпоінт логіну `/api/v1/auth/login`, то tokenUrl="auth/login" (відносно API_V1_STR).
# Або повний шлях. Поки що залишу відносний.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.app.API_V1_STR}/auth/login/token")


# --- Залежність для отримання поточного активного користувача ---
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db_session)
) -> UserSchema: # Повертає Pydantic схему користувача, а не ORM модель
    """
    Отримує та валідує JWT токен, повертає дані користувача.
    Викликає UnauthorizedException, якщо токен невалідний або користувач не знайдений/неактивний.
    """
    credentials_exception = UnauthorizedException(detail="Не вдалося валідувати облікові дані")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Перевірка типу токена (якщо є поле 'type' в payload)
        # token_type: Optional[str] = payload.get("type")
        # if token_type != "access": # Або константа TOKEN_TYPE_ACCESS
        #     raise credentials_exception

        # Отримання ID користувача з токена
        user_id_str: Optional[str] = payload.get("sub") # "sub" - стандартне поле для ідентифікатора суб'єкта
        if user_id_str is None:
            raise credentials_exception

        try:
            user_id = uuid.UUID(user_id_str) # Перетворюємо рядок в UUID
        except ValueError:
            raise credentials_exception # Якщо user_id не валідний UUID

        # Валідація payload за допомогою Pydantic схеми
        try:
            token_data = TokenPayloadSchema.model_validate(payload)
        except ValidationError:
            raise credentials_exception

        user_id = token_data.sub # user_id тепер є uuid.UUID завдяки валідатору в TokenPayloadSchema

        # Перевірка типу токена (якщо потрібно)
        if token_data.token_type and token_data.token_type != "access":
             raise UnauthorizedException(detail="Некоректний тип токена, очікується 'access'")

    except JWTError: # Включає ExpiredSignatureError, InvalidTokenError тощо.
        raise credentials_exception
    # ValidationError вже оброблено вище

    # Отримання користувача з БД за user_id
    # TODO: ЗАМІНИТИ ЦЕ НА РЕАЛЬНИЙ ВИКЛИК СЕРВІСУ КОРИСТУВАЧІВ, КОЛИ ВІН БУДЕ ГОТОВИЙ!
    # user_service = UserService(db)
    # user_orm = await user_service.get_active_user_by_id_for_auth(user_id) # Метод сервісу має робити всі перевірки

    # --- Поточна імітація отримання та перевірки користувача ---
    from backend.app.src.models.auth import UserModel # Тимчасовий імпорт
    from backend.app.src.models.dictionaries.status import StatusModel # Для перевірки статусу
    from sqlalchemy import select # type: ignore

    query = select(UserModel).where(UserModel.id == user_id).options(
        # Додаємо завантаження зв'язку зі статусом, якщо він потрібен для перевірки
        # from sqlalchemy.orm import selectinload # type: ignore
        # selectinload(UserModel.state) # Припускаючи, що UserModel має зв'язок `state`
    )
    result = await db.execute(query)
    user_orm: Optional[UserModel] = result.scalar_one_or_none()
    # --- Кінець імітації ---

    if user_orm is None:
        raise credentials_exception # Користувача не знайдено (або був видалений і GC спрацював)

    # Перевірка, чи користувач "активний" в широкому сенсі
    if user_orm.is_deleted:
         raise UnauthorizedException(detail="Обліковий запис користувача видалено.")

    # Перевірка статусу користувача (state_id)
    # Припускаємо, що UserModel має state_id, і ми можемо отримати код статусу.
    # Це потребуватиме ще одного запиту до БД для отримання StatusModel.code,
    # якщо статус не завантажено разом з користувачем.
    # Краще, щоб сервіс користувачів повертав цю інформацію або робив перевірку.
    # Поки що, якщо state_id є, і він не відповідає активному статусу, кидаємо помилку.
    # (Це дуже спрощена перевірка, потребує реального довідника статусів)
    if user_orm.state_id: # Якщо статус встановлено
        # Імітація перевірки коду статусу
        # Потрібно отримати StatusModel.code для user_orm.state_id
        # status_query = select(StatusModel.code).where(StatusModel.id == user_orm.state_id)
        # status_result = await db.execute(status_query)
        # status_code = status_result.scalar_one_or_none()
        # if status_code and status_code not in [STATUS_ACTIVE_CODE, "інший_активний_статус_користувача"]:
        #     raise UnauthorizedException(detail=f"Обліковий запис користувача неактивний (статус: {status_code}).")
        #
        # Простіша перевірка (якщо є константа для ID активного статусу, що погано):
        # if user_orm.state_id != ID_АКТИВНОГО_СТАТУСУ:
        #     raise UnauthorizedException(detail="Обліковий запис користувача неактивний.")
        #
        # Поки що цю перевірку залишаю як TODO для реалізації через сервіс,
        # оскільки вона потребує знання кодів активних статусів.
        pass # TODO: Реалізувати перевірку state_id користувача на активність

    return UserSchema.model_validate(user_orm) # Повертаємо Pydantic схему

async def get_current_active_user(
    current_user: UserSchema = Depends(get_current_user)
) -> UserSchema:
    """
    Залежність, що перевіряє, чи поточний користувач активний.
    (Додаткова перевірка, якщо get_current_user її не робить повністю).
    Наразі, `get_current_user` вже має робити базові перевірки.
    Це може бути корисно для більш специфічних перевірок активності.
    """
    # Приклад: якщо UserSchema має поле is_active або state.code
    # if not current_user.is_active: # Або current_user.state.code != STATUS_ACTIVE_CODE
    #     raise ForbiddenException(detail="Неактивний користувач") # Або Unauthorized
    # Поки що просто повертаємо користувача, якщо get_current_user пройшов.
    return current_user


# --- Залежності для перевірки ролей ---
# Ці залежності використовують `get_current_active_user` для отримання користувача.

async def get_current_superuser(
    current_user: UserSchema = Depends(get_current_active_user)
) -> UserSchema:
    """
    Перевіряє, чи є поточний користувач супер-адміністратором.
    Викликає ForbiddenException, якщо ні.
    """
    # `user_type_code` зберігається в `UserModel` та `UserSchema`.
    if current_user.user_type_code != USER_TYPE_SUPERADMIN:
        # Або, якщо ролі зберігаються в окремому полі/зв'язку:
        # if ROLE_SUPERADMIN_CODE not in [role.code for role in current_user.roles]:
        raise ForbiddenException(detail="Недостатньо прав: потрібен рівень супер-адміністратора.")
    return current_user

# TODO: Додати залежності для інших ролей, якщо потрібно.
# Наприклад, `get_current_group_admin` (потребуватиме `group_id` з шляху для перевірки).
# async def get_current_group_admin(
#     group_id: uuid.UUID, # З параметра шляху
#     current_user: UserSchema = Depends(get_current_active_user),
#     db: AsyncSession = Depends(get_db_session)
# ) -> UserSchema:
#     # Потрібно перевірити членство користувача в групі group_id та його роль.
#     # Це вимагає доступу до GroupMembershipModel та UserService/GroupService.
#     # ... логіка перевірки ...
#     is_admin = await check_user_is_group_admin(db, current_user.id, group_id) # Приклад функції
#     if not is_admin:
#         raise ForbiddenException(detail=f"Ви не є адміністратором групи {group_id}.")
#     return current_user


# --- Залежність для опціонального поточного користувача ---
async def get_optional_current_user(
    token: Optional[str] = Depends(oauth2_scheme) if settings.app.ENVIRONMENT != "testing" else None, # У тестах токен може бути відсутнім
    db: AsyncSession = Depends(get_db_session)
) -> Optional[UserSchema]:
    """
    Намагається отримати поточного користувача, якщо токен надано.
    Повертає None, якщо токен відсутній або невалідний (не кидає виняток).
    Корисно для ендпоінтів, які мають різну поведінку для автентифікованих
    та анонімних користувачів.
    """
    if token is None: # Якщо токен не передано (наприклад, для публічного доступу або в тестах)
        return None
    try:
        # Використовуємо логіку з get_current_user, але перехоплюємо винятки.
        # Це дублювання коду, краще винести спільну частину.
        # Поки що для простоти:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: Optional[str] = payload.get("sub")
        if user_id_str is None: return None
        try: user_id = uuid.UUID(user_id_str)
        except ValueError: return None

        from backend.app.src.models.auth import UserModel # Тимчасовий імпорт
        from sqlalchemy import select # type: ignore
        query = select(UserModel).where(UserModel.id == user_id)
        result = await db.execute(query)
        user_orm: Optional[UserModel] = result.scalar_one_or_none()

        if user_orm is None or user_orm.is_deleted: # Додамо перевірку is_deleted
            return None

        return UserSchema.model_validate(user_orm)
    except (JWTError, ValidationError, UnauthorizedException, ForbiddenException):
        # Будь-яка помилка валідації токена або отримання користувача означає,
        # що користувач не автентифікований (або токен невалідний).
        return None

# --- Залежність для API ключа (якщо використовується) ---
# api_key_header_auth = APIKeyHeader(name="X-API-Key", auto_error=True)
# async def get_api_key(api_key: str = Security(api_key_header_auth)) -> str:
#     # Тут має бути логіка перевірки API ключа (наприклад, з БД або конфігурації)
#     # У `settings` можна додати список валідних API ключів.
#     # VALID_API_KEYS = settings.app.VALID_API_KEYS (List[str])
#     if api_key in settings.app.VALID_API_KEYS: # Приклад
#         return api_key
#     else:
#         raise UnauthorizedException(detail="Невалідний або відсутній API ключ")

# TODO: Реалізувати `TokenPayloadSchema` в `schemas.auth.token`, якщо ще не створено.
# Вона має містити поля, які очікуються в JWT payload (sub, exp, iat, type тощо).
# Наразі `get_current_user` перевіряє лише `sub`.
#
# TODO: Замінити імітацію отримання користувача в `get_current_user` та `get_optional_current_user`
# на реальні виклики відповідного сервісу (наприклад, `UserService.get_active_user_by_id`).
# Це потребуватиме створення `UserService`.
#
# TODO: Розширити перевірку активності користувача в `get_current_user`
# (наприклад, перевірка `state_id` на відповідність активному статусу).
#
# TODO: Реалізувати залежності для перевірки ролей в контексті групи
# (наприклад, `get_current_group_admin`, `get_current_group_member`).
# Це потребуватиме `group_id` як параметра шляху та логіки перевірки
# членства та ролі в `GroupMembershipModel`.
#
# `oauth2_scheme` налаштований.
# `get_db_session` імпортується з `config.database`.
# Базові залежності `get_current_user`, `get_current_active_user`, `get_current_superuser`,
# `get_optional_current_user` визначені.
#
# Все виглядає як хороший початок для системи залежностей.
# Важливо, що `get_current_user` повертає Pydantic схему `UserSchema`,
# а не ORM модель, що є хорошою практикою для FastAPI.
#
# Для `get_optional_current_user`: в тестах токен може бути відсутнім,
# тому `Depends(oauth2_scheme)` робиться умовним.
# Якщо `settings.app.ENVIRONMENT == "testing"`, то `token` може бути `None`.
# Це дозволяє тестувати ендпоінти без обов'язкової автентифікації, якщо логіка це підтримує.
# Або ж, у тестах можна використовувати `app.dependency_overrides` для мокання автентифікації.
# Поточний підхід з умовним `Depends` є одним з варіантів.
#
# Все готово.
