# backend/app/src/api/v1/users/users.py
from typing import List, Optional, TypeVar
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel # Потрібно для PaginatedResponse Generic
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.dependencies import get_db_session, get_current_active_superuser
from app.src.models.auth import User as UserModel
from app.src.schemas.auth.user import (
    UserResponse,
    UserCreateSuperuser, # Спеціальна схема для створення користувача суперюзером
    UserUpdateSuperuser  # Спеціальна схема для оновлення користувача суперюзером
)
# Припускаємо, що PageParams та PaginatedResponse визначені тут або імпортовані
# Наприклад, з app.src.schemas.pagination import PaginatedResponse, PageParams

# --- Початок визначення схем пагінації (якщо вони не в окремому файлі) ---
class PageParams:
    def __init__(
        self,
        page: int = Query(1, ge=1, description="Номер сторінки"),
        size: int = Query(10, ge=1, le=100, description="Розмір сторінки (кількість елементів)")
    ):
        self.page = page
        self.size = size
        self.limit = size
        self.skip = (page - 1) * size

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    total: int
    page: int
    size: int
    results: List[T]
# --- Кінець визначення схем пагінації ---


from app.src.services.auth.user import UserService
# from app.src.core.utils import I18nMessages # Якщо є для інтернаціоналізації повідомлень

router = APIRouter()

@router.post(
    "/",
    response_model=UserResponse, # Або UserSuperAdminView, якщо є специфічний вид для адміна
    status_code=status.HTTP_201_CREATED,
    summary="Створення нового користувача (Суперюзер)",
    description="Дозволяє суперюзеру створити нового користувача в системі, потенційно з розширеними правами або налаштуваннями."
)
async def create_user_by_superuser(
    user_in: UserCreateSuperuser, # Використовуємо UserCreateSuperuser
    db: AsyncSession = Depends(get_db_session),
    current_superuser: UserModel = Depends(get_current_active_superuser),
    user_service: UserService = Depends()
):
    '''
    Створює нового користувача. Доступно тільки суперюзерам.
    Може включати поля для ролі, статусу активації тощо.

    - **email**: Email нового користувача (унікальний).
    - **password**: Пароль нового користувача.
    - **first_name**: Ім'я.
    - **last_name**: Прізвище.
    - **username**: Нікнейм (якщо використовується, має бути унікальним).
    - **user_role_id**: ID ролі користувача.
    - **user_type_id**: ID типу користувача.
    - **is_active**: Статус активності.
    - **is_superuser**: Чи є користувач суперюзером (зазвичай встановлюється обережно).
    '''
    if not hasattr(user_service, 'db_session') or user_service.db_session is None:
        user_service.db_session = db

    existing_user_email = await user_service.user_repo.get_by_email(email=user_in.email)
    if existing_user_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Користувач з email '{user_in.email}' вже існує."
            # detail=I18nMessages.USER_EMAIL_EXISTS.format(email=user_in.email) # Приклад з i18n
        )

    if user_in.username:
        existing_user_username = await user_service.user_repo.get_by_username(username=user_in.username)
        if existing_user_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Користувач з нікнеймом '{user_in.username}' вже існує."
            )

    # UserCreateSuperuser передається в сервіс, який знає як з нею працювати
    created_user = await user_service.create_user_by_superuser(user_create_schema=user_in)
    if not created_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не вдалося створити користувача."
        )
    return UserResponse.model_validate(created_user)

@router.get(
    "/",
    response_model=PaginatedResponse[UserResponse], # Або UserSuperAdminView
    summary="Отримання списку користувачів (Суперюзер)",
    description="Повертає список всіх користувачів системи з пагінацією. Доступно тільки суперюзерам."
)
async def read_users(
    page_params: PageParams = Depends(), # Залежність для параметрів пагінації (skip, limit)
    db: AsyncSession = Depends(get_db_session),
    current_superuser: UserModel = Depends(get_current_active_superuser),
    user_service: UserService = Depends()
):
    '''
    Отримує список користувачів з пагінацією.
    Дозволяє фільтрацію за певними критеріями (буде додано за потреби).
    '''
    if not hasattr(user_service, 'db_session') or user_service.db_session is None:
        user_service.db_session = db

    total_users, users = await user_service.get_multi_with_count(
        skip=page_params.skip,
        limit=page_params.limit
    )

    return PaginatedResponse[UserResponse]( # Явно вказуємо тип для PaginatedResponse
        total=total_users,
        page=page_params.page,
        size=page_params.size,
        results=[UserResponse.model_validate(user) for user in users]
    )

@router.get(
    "/{user_id}",
    response_model=UserResponse, # Або UserSuperAdminView
    summary="Отримання інформації про користувача за ID (Суперюзер)",
    description="Повертає детальну інформацію про конкретного користувача за його ID. Доступно тільки суперюзерам."
)
async def read_user_by_id(
    user_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_superuser: UserModel = Depends(get_current_active_superuser),
    user_service: UserService = Depends()
):
    '''
    Отримує інформацію про користувача за його ID.
    '''
    if not hasattr(user_service, 'db_session') or user_service.db_session is None:
        user_service.db_session = db

    user = await user_service.user_repo.get_by_id(id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Користувача з ID {user_id} не знайдено."
            # detail=I18nMessages.USER_NOT_FOUND.format(id=user_id)
        )
    return UserResponse.model_validate(user)

@router.put(
    "/{user_id}",
    response_model=UserResponse, # Або UserSuperAdminView
    summary="Оновлення інформації про користувача (Суперюзер)",
    description="Дозволяє суперюзеру оновити дані існуючого користувача. Може включати зміну ролі, статусу тощо."
)
async def update_user_by_superuser(
    user_id: int,
    user_in: UserUpdateSuperuser, # Схема для оновлення суперюзером
    db: AsyncSession = Depends(get_db_session),
    current_superuser: UserModel = Depends(get_current_active_superuser),
    user_service: UserService = Depends()
):
    '''
    Оновлює дані користувача. Доступно тільки суперюзерам.
    Дозволяє змінювати такі поля, як email, ім'я, роль, статус активації.
    Зміна паролю зазвичай відбувається через окремий механізм.
    '''
    if not hasattr(user_service, 'db_session') or user_service.db_session is None:
        user_service.db_session = db

    user_to_update = await user_service.user_repo.get_by_id(id=user_id)
    if not user_to_update:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Користувача з ID {user_id} не знайдено для оновлення."
        )

    # Перевірка унікальності email, якщо він змінюється
    if user_in.email and user_in.email != user_to_update.email:
        existing_email_user = await user_service.user_repo.get_by_email(email=user_in.email)
        if existing_email_user and existing_email_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Email '{user_in.email}' вже використовується іншим користувачем."
            )

    # Перевірка унікальності username, якщо він змінюється
    if hasattr(user_in, 'username') and user_in.username and user_in.username != user_to_update.username: # Додано hasattr
        existing_username_user = await user_service.user_repo.get_by_username(username=user_in.username)
        if existing_username_user and existing_username_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Нікнейм '{user_in.username}' вже використовується іншим користувачем."
            )

    updated_user = await user_service.update_user_by_superuser(
        user_to_update=user_to_update,
        user_update_schema=user_in
    )
    if not updated_user:
         raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, # Або 404, якщо user_to_update раптом зник
            detail="Не вдалося оновити користувача."
        )
    return UserResponse.model_validate(updated_user)

@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалення користувача (Суперюзер)",
    description="Дозволяє суперюзеру видалити користувача (зазвичай м'яке видалення). Доступно тільки суперюзерам."
)
async def delete_user_by_superuser(
    user_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_superuser: UserModel = Depends(get_current_active_superuser),
    user_service: UserService = Depends()
):
    '''
    Видаляє користувача (зазвичай встановлює прапорець is_deleted або deleted_at).
    Фактичне видалення з БД може бути небезпечним через пов'язані дані.
    '''
    if not hasattr(user_service, 'db_session') or user_service.db_session is None:
        user_service.db_session = db

    user_to_delete = await user_service.user_repo.get_by_id(id=user_id)
    if not user_to_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Користувача з ID {user_id} не знайдено для видалення."
        )

    if user_to_delete.id == current_superuser.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Суперюзер не може видалити сам себе через цей ендпоінт."
        )

    success = await user_service.delete_user_by_superuser(user_to_delete=user_to_delete)
    if not success:
        # Це може статися, якщо, наприклад, сервіс має додаткові перевірки перед видаленням
        # або якщо soft delete не вдалося з якоїсь причини.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Не вдалося видалити користувача з ID {user_id}."
        )

    # Відповідь HTTP 204 No Content не повинна мати тіла

# Міркування:
# 1. Схеми:
#    - `UserCreateSuperuser`: Для створення користувача суперюзером. Може включати поля `user_role_id`, `user_type_id`, `is_active`, `is_superuser`.
#    - `UserUpdateSuperuser`: Для оновлення користувача суперюзером. Може дозволяти зміну всіх цих полів.
#    - `UserResponse` (або `UserSuperAdminView`): Для повернення даних користувача, можливо з більшою кількістю полів, ніж стандартний `UserResponse`.
#    - `PaginatedResponse`, `PageParams`: Для пагінації списку користувачів. (Визначено вище в цьому файлі для прикладу)
# 2. Сервіс `UserService`:
#    - Потребує методів: `create_user_by_superuser`, `get_multi_with_count` (для пагінації), `update_user_by_superuser`, `delete_user_by_superuser`.
#    - Репозиторій користувачів (`user_repo`) повинен мати методи `get_by_email`, `get_by_username`, `get_by_id`.
# 3. Захист: Всі ендпоінти захищені `Depends(get_current_active_superuser)`.
# 4. Безпека:
#    - Суперюзер не повинен мати можливості легко видалити себе через цей API, щоб уникнути блокування системи (додано перевірку).
#    - Призначення ролі суперюзера іншим користувачам має бути контрольованим.
# 5. Пагінація: Використовується `PageParams` для `skip` та `limit` і `PaginatedResponse` для відповіді.
# 6. Коментарі: Українською мовою.
# 7. I18n: Закоментовані приклади використання `I18nMessages` для інтернаціоналізації повідомлень про помилки.
# 8. Ініціалізація сервісів: Як і раніше, `UserService = Depends()` припускає, що сервіс налаштований як залежність FastAPI.
#    Якщо ні, то `user_service = UserService(db)` буде використовуватися в кожній функції.
#    Додано перевірки `hasattr` для гнучкості.
# 9. Поля `user_role_id` та `user_type_id` в `UserCreateSuperuser` та `UserUpdateSuperuser` припускають,
#    що існують відповідні довідники та моделі для ролей та типів користувачів.
#    Сервіс повинен валідувати існування таких ID.
from typing import Generic # Потрібно для PaginatedResponse Generic, якщо не імпортовано раніше
