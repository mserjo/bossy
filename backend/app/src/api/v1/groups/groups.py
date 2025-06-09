# backend/app/src/api/v1/groups/groups.py
from typing import List, Optional, Generic, TypeVar # Додано Generic, TypeVar для PaginatedResponse
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel # Додано BaseModel для PaginatedResponse, якщо визначається локально
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.dependencies import get_db_session, get_current_active_user, get_current_active_superuser
from app.src.models.auth import User as UserModel
from app.src.models.groups import Group as GroupModel # Потрібна модель групи
from app.src.schemas.groups.group import ( # Схеми для груп
    GroupCreate,
    GroupUpdate,
    GroupResponse,
    # GroupDetailedResponse # Якщо є більш детальна схема
)

# Припускаємо, що ці схеми імпортуються, якщо ні - можна визначити як у users.py
from app.src.schemas.pagination import PaginatedResponse, PageParams # Схема для пагінації

from app.src.services.groups.group import GroupService # Сервіс для груп
from app.src.core.permissions import GroupPermissionsChecker # Для перевірки прав доступу до групи
# from app.src.core.utils import I18nMessages # Для інтернаціоналізації

router = APIRouter()

@router.post(
    "/",
    response_model=GroupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Створення нової групи",
    description="Дозволяє аутентифікованому користувачу створити нову групу. Користувач, що створив групу, автоматично стає її адміністратором."
)
async def create_group(
    group_in: GroupCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user),
    group_service: GroupService = Depends()
):
    '''
    Створює нову групу.

    - **name**: Назва групи (обов'язково).
    - **description**: Опис групи (опціонально).
    - **group_type_id**: ID типу групи (обов'язково, має існувати в довіднику).
    - ... інші поля з GroupCreate ...
    '''
    if not hasattr(group_service, 'db_session') or group_service.db_session is None:
        group_service.db_session = db
    if not hasattr(group_service, 'current_user') or group_service.current_user is None:
        group_service.current_user = current_user # Сервіс може потребувати поточного користувача

    # Перевірка, чи існує тип групи, якщо group_type_id передається
    if hasattr(group_in, 'group_type_id') and group_in.group_type_id: # Додано hasattr для безпеки
        # Цю перевірку краще робити в сервісі або на рівні БД з foreign key
        pass

    created_group = await group_service.create_group(group_create_schema=group_in, creator=current_user)
    if not created_group:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Не вдалося створити групу."
        )
    return GroupResponse.model_validate(created_group)

@router.get(
    "/",
    response_model=PaginatedResponse[GroupResponse],
    summary="Отримання списку груп",
    description="Повертає список груп. Суперюзер бачить усі групи. Звичайний користувач бачить групи, до яких він належить або які є публічними (якщо реалізовано)."
)
async def read_groups(
    page_params: PageParams = Depends(),
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user), # Потрібен для визначення контексту
    group_service: GroupService = Depends()
    # TODO: Додати фільтри (наприклад, за назвою, типом, мої групи)
):
    '''
    Отримує список груп з пагінацією.
    Поведінка залежить від ролі користувача.
    '''
    if not hasattr(group_service, 'db_session') or group_service.db_session is None:
        group_service.db_session = db
    if not hasattr(group_service, 'current_user') or group_service.current_user is None:
        group_service.current_user = current_user

    # Логіка визначення, які групи показувати, має бути в сервісі
    total_groups, groups = await group_service.get_groups_for_user(
        user=current_user,
        skip=page_params.skip,
        limit=page_params.limit
        # Додати параметри фільтрації сюди
    )

    return PaginatedResponse[GroupResponse]( # Явно вказуємо тип Generic
        total=total_groups,
        page=page_params.page,
        size=page_params.size,
        results=[GroupResponse.model_validate(group) for group in groups]
    )

@router.get(
    "/{group_id}",
    response_model=GroupResponse, # Або GroupDetailedResponse
    summary="Отримання інформації про групу за ID",
    description="Повертає детальну інформацію про конкретну групу. Доступно суперюзеру або члену групи."
)
async def read_group_by_id(
    group_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user),
    group_service: GroupService = Depends()
):
    '''
    Отримує інформацію про групу за її ID.
    '''
    if not hasattr(group_service, 'db_session') or group_service.db_session is None:
        group_service.db_session = db
    if not hasattr(group_service, 'current_user') or group_service.current_user is None:
        group_service.current_user = current_user

    group = await group_service.get_group_by_id_for_user(group_id=group_id, user=current_user)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Групу з ID {group_id} не знайдено або доступ заборонено."
        )

    # Перевірка прав доступу (чи є користувач членом групи або суперюзером)
    # Це може бути частиною group_service.get_group_by_id_for_user або окремою перевіркою
    # await GroupPermissionsChecker(db).check_user_can_view_group(user=current_user, group_id=group_id)

    return GroupResponse.model_validate(group)


@router.put(
    "/{group_id}",
    response_model=GroupResponse,
    summary="Оновлення інформації про групу",
    description="Дозволяє суперюзеру або адміністратору групи оновити дані групи."
)
async def update_group(
    group_id: int,
    group_in: GroupUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user),
    group_service: GroupService = Depends()
):
    '''
    Оновлює дані групи. Доступно суперюзеру або адміністратору групи.
    '''
    if not hasattr(group_service, 'db_session') or group_service.db_session is None:
        group_service.db_session = db
    if not hasattr(group_service, 'current_user') or group_service.current_user is None:
        group_service.current_user = current_user

    # Перевірка прав: чи є користувач адміном групи або суперюзером
    # Це може бути зроблено в сервісі або тут за допомогою GroupPermissionsChecker
    # await GroupPermissionsChecker(db).check_user_can_edit_group(user=current_user, group_id=group_id)

    updated_group = await group_service.update_group(
        group_id=group_id,
        group_update_schema=group_in,
        requesting_user=current_user
    )
    if not updated_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, # Або 403, якщо права не дозволяють
            detail=f"Групу з ID {group_id} не знайдено або оновлення не вдалося/заборонено."
        )
    return GroupResponse.model_validate(updated_group)

@router.delete(
    "/{group_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалення групи",
    description="Дозволяє суперюзеру або адміністратору групи видалити групу. Існують обмеження (наприклад, адмін не може видалити групу, якщо він єдиний адмін)."
)
async def delete_group(
    group_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user),
    group_service: GroupService = Depends()
):
    '''
    Видаляє групу.
    '''
    if not hasattr(group_service, 'db_session') or group_service.db_session is None:
        group_service.db_session = db
    if not hasattr(group_service, 'current_user') or group_service.current_user is None:
        group_service.current_user = current_user

    # Перевірка прав та логіка видалення в сервісі
    # await GroupPermissionsChecker(db).check_user_can_delete_group(user=current_user, group_id=group_id)

    success = await group_service.delete_group(group_id=group_id, requesting_user=current_user)
    if not success:
        # Сервіс повинен кидати відповідні HTTPException (403, 404, 400)
        # Якщо сервіс повертає False, це може бути загальна помилка
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, # Або більш конкретний код помилки з сервісу
            detail=f"Не вдалося видалити групу з ID {group_id}. Можливо, існують обмеження (наприклад, ви єдиний адміністратор) або група не знайдена."
        )
    # Відповідь HTTP 204 No Content не повинна мати тіла

# Міркування:
# 1.  Схеми: `GroupCreate`, `GroupUpdate`, `GroupResponse` (і, можливо, `GroupDetailedResponse`) мають бути визначені в `app.src.schemas.groups.group`.
# 2.  Сервіс `GroupService`: Повинен інкапсулювати всю бізнес-логіку, включаючи перевірку прав (або використовувати `GroupPermissionsChecker`), взаємодію з БД.
#     Методи: `create_group`, `get_groups_for_user`, `get_group_by_id_for_user`, `update_group`, `delete_group`.
# 3.  Права доступу:
#     - Створення групи: будь-який аутентифікований користувач.
#     - Перегляд списку: суперюзер бачить все, звичайний - свої групи.
#     - Перегляд деталей: суперюзер або член групи.
#     - Оновлення: суперюзер або адмін групи.
#     - Видалення: суперюзер або адмін групи (з обмеженнями, наприклад, не можна видалити, якщо ти єдиний адмін).
#     `GroupPermissionsChecker` - це гіпотетичний клас/залежність для централізованої перевірки прав.
# 4.  Пагінація: Для списку груп.
# 5.  Коментарі: Українською мовою.
# 6.  Ініціалізація сервісів: `GroupService = Depends()` припускає відповідне налаштування сервісу як залежності FastAPI.
# 7.  Модель `GroupModel`: Потрібна SQLAlchemy модель для групи.
# 8.  `group_type_id`: Поле в `GroupCreate` передбачає існування довідника типів груп. Валідація ID типу групи має відбуватися.
# 9.  Фільтрація: Ендпоінт `read_groups` може бути розширений параметрами для фільтрації.
