# backend/app/src/api/v1/notifications/templates.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для управління шаблонами сповіщень.

Дозволяє суперкористувачам створювати, отримувати, оновлювати та видаляти
шаблони, які використовуються для генерації сповіщень різних типів.
"""
from typing import List, Optional  # Generic, TypeVar, BaseModel не потрібні, якщо імпортуються з core
from uuid import UUID  # ID тепер UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

# Повні шляхи імпорту
from backend.app.src.api.dependencies import get_api_db_session, get_current_active_superuser, paginator
from backend.app.src.models.auth.user import User as UserModel  # Для current_admin_user
from backend.app.src.schemas.notifications.template import (
    NotificationTemplateCreate,
    NotificationTemplateUpdate,
    NotificationTemplateResponse
)
from backend.app.src.core.pagination import PagedResponse, PageParams
from backend.app.src.services.notifications.template import NotificationTemplateService
from backend.app.src.config.logging import logger  # Централізований логер
from backend.app.src.config import settings as global_settings

router = APIRouter(
    # Префікс /templates буде додано в __init__.py батьківського роутера notifications
    # Теги також успадковуються/додаються звідти
    dependencies=[Depends(get_current_active_superuser)]  # Всі операції з шаблонами - тільки для суперюзерів
)


# Залежність для отримання NotificationTemplateService
async def get_notification_template_service(
        session: AsyncSession = Depends(get_api_db_session)) -> NotificationTemplateService:
    """Залежність FastAPI для отримання екземпляра NotificationTemplateService."""
    return NotificationTemplateService(db_session=session)


@router.post(
    "/",
    response_model=NotificationTemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Створення нового шаблону сповіщення",  # i18n
    description="Дозволяє суперкористувачу створити новий шаблон для генерації сповіщень."  # i18n
)
async def create_notification_template(
        template_in: NotificationTemplateCreate,
        service: NotificationTemplateService = Depends(get_notification_template_service),
        current_user: UserModel = Depends(get_current_active_superuser)  # Для аудиту (created_by_user_id)
) -> NotificationTemplateResponse:
    """
    Створює новий шаблон сповіщення.
    Доступно тільки суперкористувачам.
    `NotificationTemplateService` успадковує від `BaseDictionaryService`, тому використовуємо його метод `create`.
    Унікальність поля `name` (яке діє як код для шаблонів) перевіряється в `BaseDictionaryService.create`.
    """
    logger.info(f"Суперкористувач ID '{current_user.id}' створює шаблон сповіщення '{template_in.name}'.")
    try:
        # BaseDictionaryService.create може приймати kwargs для дод. полів (напр. created_by_user_id)
        # TODO: Переконатися, що модель NotificationTemplate та BaseDictionaryService обробляють created_by_user_id.
        created_template = await service.create(data=template_in, created_by_user_id=current_user.id)
        return created_template
    except ValueError as e:  # Помилки унікальності або валідації з сервісу
        logger.warning(f"Помилка створення шаблону '{template_in.name}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при створенні шаблону '{template_in.name}': {e}",
                     exc_info=global_settings.DEBUG)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутрішня помилка сервера.")


@router.get(
    "/",
    response_model=PagedResponse[NotificationTemplateResponse],
    summary="Отримання списку шаблонів сповіщень",  # i18n
    description="Повертає список усіх шаблонів сповіщень з пагінацією. Доступно суперкористувачам."  # i18n
)
async def read_notification_templates(
        template_type: Optional[str] = Query(None,
                                             description="Фільтр за типом шаблону (наприклад, 'EMAIL', 'IN_APP')"),
        # i18n
        page_params: PageParams = Depends(paginator),
        service: NotificationTemplateService = Depends(get_notification_template_service)
        # current_user: UserModel = Depends(get_current_active_superuser) # Вже захищено на рівні роутера
) -> PagedResponse[NotificationTemplateResponse]:
    """
    Отримує список шаблонів сповіщень. Доступно суперкористувачам.
    Можлива фільтрація за типом шаблону.
    """
    logger.debug(
        f"Запит списку шаблонів. Тип: {template_type}, сторінка: {page_params.page}, розмір: {page_params.size}")

    # TODO: Додати фільтрацію за template_type в NotificationTemplateService.get_all або створити окремий метод.
    # Поки що, якщо template_type надано, викликаємо list_templates_by_type, інакше get_all.
    # Це також означає, що пагінація для list_templates_by_type має бути реалізована в сервісі.
    if template_type:
        templates_list = await service.list_templates_by_type(
            template_type=template_type, skip=page_params.skip, limit=page_params.limit
        )
        # TODO: Для коректної пагінації з фільтром потрібен окремий count_by_type.
        # total_count = await service.count_by_type(template_type=template_type)
        total_count = len(templates_list)  # ЗАГЛУШКА для total_count при фільтрації
        logger.warning("Використовується заглушка для total_count при фільтрації шаблонів за типом.")
    else:
        templates_list = await service.get_all(skip=page_params.skip, limit=page_params.limit)
        total_count = await service.count_all()  # Потрібен метод count_all в BaseDictionaryService

    return PagedResponse[NotificationTemplateResponse](
        total=total_count,
        page=page_params.page,
        size=page_params.size,
        results=templates_list  # Сервіс вже повертає список Pydantic моделей
    )


@router.get(
    "/{template_id}",
    response_model=NotificationTemplateResponse,
    summary="Отримання інформації про шаблон за ID",  # i18n
    description="Повертає детальну інформацію про конкретний шаблон сповіщення. Доступно суперкористувачам."  # i18n
)
async def read_notification_template_by_id(
        template_id: UUID,  # ID тепер UUID
        service: NotificationTemplateService = Depends(get_notification_template_service)
        # current_user: UserModel = Depends(get_current_active_superuser) # Вже захищено
) -> NotificationTemplateResponse:
    """
    Отримує інформацію про шаблон за його ID.
    Доступно суперкористувачам.
    """
    logger.debug(f"Запит шаблону за ID: {template_id}")
    db_template = await service.get_by_id(item_id=template_id)
    if not db_template:
        logger.warning(f"Шаблон сповіщення з ID '{template_id}' не знайдено.")
        # i18n
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Шаблон сповіщення не знайдено.")
    return db_template


@router.put(
    "/{template_id}",
    response_model=NotificationTemplateResponse,
    summary="Оновлення шаблону сповіщення",  # i18n
    description="Дозволяє суперкористувачу оновити існуючий шаблон сповіщення.",  # i18n
)
async def update_notification_template(
        template_id: UUID,  # ID тепер UUID
        template_in: NotificationTemplateUpdate,
        service: NotificationTemplateService = Depends(get_notification_template_service),
        current_user: UserModel = Depends(get_current_active_superuser)  # Для updated_by_user_id
) -> NotificationTemplateResponse:
    """
    Оновлює дані шаблону сповіщення.
    Доступно суперкористувачам.
    """
    logger.info(f"Суперкористувач ID '{current_user.id}' намагається оновити шаблон ID '{template_id}'.")
    try:
        # TODO: Переконатися, що BaseDictionaryService.update обробляє updated_by_user_id через kwargs.
        updated_template = await service.update(item_id=template_id, data=template_in,
                                                updated_by_user_id=current_user.id)
        if not updated_template:  # Якщо сервіс повертає None при не знайденому об'єкті
            logger.warning(f"Шаблон з ID '{template_id}' не знайдено для оновлення.")
            # i18n
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Шаблон сповіщення не знайдено.")
        return updated_template
    except ValueError as e:  # Помилки унікальності або валідації з сервісу
        logger.warning(f"Помилка оновлення шаблону ID '{template_id}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при оновленні шаблону ID '{template_id}': {e}",
                     exc_info=global_settings.DEBUG)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутрішня помилка сервера.")


@router.delete(
    "/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалення шаблону сповіщення",  # i18n
    description="Дозволяє суперкористувачу видалити шаблон сповіщення.",  # i18n
)
async def delete_notification_template(
        template_id: UUID,  # ID тепер UUID
        service: NotificationTemplateService = Depends(get_notification_template_service),
        current_user: UserModel = Depends(get_current_active_superuser)  # Для логування аудиту
):
    """
    Видаляє шаблон сповіщення.
    Доступно суперкористувачам.
    """
    logger.info(f"Суперкористувач ID '{current_user.id}' намагається видалити шаблон ID '{template_id}'.")
    try:
        # BaseDictionaryService.delete повертає bool
        deleted = await service.delete(item_id=template_id)
        if not deleted:
            logger.warning(f"Шаблон з ID '{template_id}' не знайдено для видалення.")
            # i18n
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Шаблон сповіщення не знайдено.")
    except ValueError as e:  # Якщо сервіс кидає ValueError (наприклад, шаблон використовується)
        logger.warning(f"Помилка видалення шаблону ID '{template_id}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при видаленні шаблону ID '{template_id}': {e}",
                     exc_info=global_settings.DEBUG)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутрішня помилка сервера.")

    return None  # HTTP 204 No Content


# TODO: Розглянути ендпоінт для рендерингу шаблону з тестовими даними (POST /render-test) для адмінки.

logger.info(f"Роутер для шаблонів сповіщень (`{router.prefix}`) визначено.")
