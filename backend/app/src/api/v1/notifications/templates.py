# backend/app/src/api/v1/notifications/templates.py
from typing import List, Optional, Generic, TypeVar # Додано Generic, TypeVar для PaginatedResponse
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from pydantic import BaseModel # Додано BaseModel для PaginatedResponse, якщо визначається локально
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.dependencies import get_db_session, get_current_active_superuser # Адміністративні дії
from app.src.models.auth import User as UserModel
# from app.src.models.notifications import NotificationTemplate as NotificationTemplateModel # Потрібна модель шаблону
from app.src.schemas.notifications.template import ( # Схеми для шаблонів
    NotificationTemplateCreate,
    NotificationTemplateUpdate,
    NotificationTemplateResponse
)
# Припускаємо, що ці схеми імпортуються, якщо ні - можна визначити як у users.py або groups.py
from app.src.schemas.pagination import PaginatedResponse, PageParams
from app.src.services.notifications.template import NotificationTemplateService # Сервіс для шаблонів

router = APIRouter()

@router.post(
    "/", # Шлях відносно /notifications/templates/
    response_model=NotificationTemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Створення нового шаблону сповіщення (Адмін/Суперюзер)",
    description="Дозволяє адміністратору або суперюзеру створити новий шаблон для генерації сповіщень."
)
async def create_notification_template(
    template_in: NotificationTemplateCreate,
    db: AsyncSession = Depends(get_db_session),
    current_admin_user: UserModel = Depends(get_current_active_superuser),
    template_service: NotificationTemplateService = Depends()
):
    '''
    Створює новий шаблон сповіщення.
    - `name`: Унікальна назва/ідентифікатор шаблону.
    - `description`: Опис шаблону.
    - `subject_template`: Шаблон для теми сповіщення.
    - `body_template`: Шаблон для тіла сповіщення (може містити HTML, Markdown, або плейсхолдери).
    - `template_type`: Тип шаблону (наприклад, 'email', 'in_app', 'sms').
    - `available_variables`: Список доступних змінних для цього шаблону.
    '''
    if not hasattr(template_service, 'db_session') or template_service.db_session is None:
        template_service.db_session = db

    created_template = await template_service.create_template(
        template_create_schema=template_in,
        requesting_user=current_admin_user # Для перевірки прав або логування
    )
    # Сервіс має кидати HTTPException у разі помилок (наприклад, неунікальна назва)
    return NotificationTemplateResponse.model_validate(created_template)

@router.get(
    "/",
    response_model=PaginatedResponse[NotificationTemplateResponse],
    summary="Отримання списку шаблонів сповіщень (Адмін/Суперюзер)",
    description="Повертає список усіх шаблонів сповіщень з пагінацією."
)
async def read_notification_templates(
    page_params: PageParams = Depends(),
    template_type: Optional[str] = Query(None, description="Фільтр за типом шаблону (наприклад, 'email', 'in_app')"),
    db: AsyncSession = Depends(get_db_session),
    current_admin_user: UserModel = Depends(get_current_active_superuser),
    template_service: NotificationTemplateService = Depends()
):
    '''
    Отримує список шаблонів сповіщень.
    '''
    if not hasattr(template_service, 'db_session') or template_service.db_session is None:
        template_service.db_session = db

    total_templates, templates = await template_service.get_templates(
        template_type=template_type,
        skip=page_params.skip,
        limit=page_params.limit
        # requesting_user=current_admin_user # Якщо потрібна додаткова логіка доступу
    )
    return PaginatedResponse[NotificationTemplateResponse]( # Явно вказуємо тип Generic
        total=total_templates,
        page=page_params.page,
        size=page_params.size,
        results=[NotificationTemplateResponse.model_validate(t) for t in templates]
    )

@router.get(
    "/{template_id}",
    response_model=NotificationTemplateResponse,
    summary="Отримання інформації про шаблон за ID (Адмін/Суперюзер)",
    description="Повертає детальну інформацію про конкретний шаблон сповіщення."
)
async def read_notification_template_by_id(
    template_id: int, # В структурі проекту було template_id, але часто використовують name або code як унікальний ідентифікатор
    db: AsyncSession = Depends(get_db_session),
    current_admin_user: UserModel = Depends(get_current_active_superuser),
    template_service: NotificationTemplateService = Depends()
):
    '''
    Отримує інформацію про шаблон за його ID.
    '''
    if not hasattr(template_service, 'db_session') or template_service.db_session is None:
        template_service.db_session = db

    template = await template_service.get_template_by_id(
        template_id=template_id
        # requesting_user=current_admin_user # Якщо потрібна перевірка доступу
        )
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Шаблон сповіщення з ID {template_id} не знайдено."
        )
    return NotificationTemplateResponse.model_validate(template)

@router.put(
    "/{template_id}",
    response_model=NotificationTemplateResponse,
    summary="Оновлення шаблону сповіщення (Адмін/Суперюзер)",
    description="Дозволяє адміністратору або суперюзеру оновити існуючий шаблон сповіщення."
)
async def update_notification_template(
    template_id: int,
    template_in: NotificationTemplateUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_admin_user: UserModel = Depends(get_current_active_superuser),
    template_service: NotificationTemplateService = Depends()
):
    '''
    Оновлює дані шаблону сповіщення.
    '''
    if not hasattr(template_service, 'db_session') or template_service.db_session is None:
        template_service.db_session = db

    updated_template = await template_service.update_template(
        template_id=template_id,
        template_update_schema=template_in,
        requesting_user=current_admin_user
    )
    # Сервіс має кидати HTTPException у разі помилок
    return NotificationTemplateResponse.model_validate(updated_template)

@router.delete(
    "/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалення шаблону сповіщення (Адмін/Суперюзер)",
    description="Дозволяє адміністратору або суперюзеру видалити шаблон сповіщення."
)
async def delete_notification_template(
    template_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_admin_user: UserModel = Depends(get_current_active_superuser),
    template_service: NotificationTemplateService = Depends()
):
    '''
    Видаляє шаблон сповіщення.
    '''
    if not hasattr(template_service, 'db_session') or template_service.db_session is None:
        template_service.db_session = db

    success = await template_service.delete_template(
        template_id=template_id,
        requesting_user=current_admin_user
    )
    if not success: # Сервіс має кидати HTTPException
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Не вдалося видалити шаблон сповіщення з ID {template_id}. Можливо, його не існує."
        )
    # HTTP 204 No Content

# Міркування:
# 1.  Схеми: `NotificationTemplateCreate`, `NotificationTemplateUpdate`, `NotificationTemplateResponse` з `app.src.schemas.notifications.template`.
# 2.  Сервіс `NotificationTemplateService`: CRUD операції для шаблонів.
# 3.  Права доступу: Тільки адміністратори/суперюзери можуть керувати шаблонами.
# 4.  Пагінація: Для списку шаблонів. Фільтр за `template_type`.
# 5.  Унікальність: Назва (`name`) або код шаблону мають бути унікальними, це має забезпечуватися на рівні сервісу/БД.
# 6.  URL-и: Цей роутер буде підключений до `notifications_router` з префіксом `/templates`.
#     Шляхи будуть `/api/v1/notifications/templates/`, `/api/v1/notifications/templates/{template_id}`.
# 7.  Коментарі: Українською мовою.
