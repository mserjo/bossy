# backend/app/src/api/v1/tasks/reviews.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для управління відгуками на завдання.

Дозволяє користувачам створювати/оновлювати відгуки на завдання,
переглядати відгуки для завдання, а також видаляти власні відгуки
(або адміністраторам/суперюзерам видаляти будь-які відгуки).
"""
from typing import List, Optional  # Generic, TypeVar, BaseModel не потрібні, якщо імпортуються з core
from uuid import UUID  # ID тепер UUID
from fastapi import APIRouter, Depends, HTTPException, status, Path  # Query не використовується прямо тут
from sqlalchemy.ext.asyncio import AsyncSession

# Повні шляхи імпорту
from backend.app.src.api.dependencies import (
    get_api_db_session, get_current_active_user,
    # TODO: Створити/використати залежності для перевірки прав, наприклад:
    #  `require_task_interaction_for_review(task_id: UUID = Path(...))` (чи користувач може залишити відгук)
    #  `require_review_owner_or_admin(review_id: UUID = Path(...))` (для редагування/видалення)
    get_current_active_superuser,  # Тимчасово для деяких адмінських дій
    paginator
)
from backend.app.src.api.v1.groups.groups import check_group_view_permission  # Для перегляду відгуків в контексті групи
from backend.app.src.services.tasks.task import TaskService  # Для отримання завдання, до якого належить відгук
from backend.app.src.models.auth.user import User as UserModel
from backend.app.src.schemas.tasks.review import (
    TaskReviewCreate,
    TaskReviewUpdate,
    TaskReviewResponse
)
from backend.app.src.core.pagination import PagedResponse, PageParams
from backend.app.src.services.tasks.review import TaskReviewService
from backend.app.src.config.logging import logger  # Централізований логер
from backend.app.src.config import settings as global_settings

router = APIRouter(
    # Префікс /reviews буде додано в __init__.py батьківського роутера tasks
    # Теги також успадковуються/додаються звідти
)


# Залежність для отримання TaskReviewService
async def get_task_review_service(session: AsyncSession = Depends(get_api_db_session)) -> TaskReviewService:
    """Залежність FastAPI для отримання екземпляра TaskReviewService."""
    return TaskReviewService(db_session=session)


# Залежність для TaskService (для перевірки прав через групу завдання)
async def get_task_service_dep(session: AsyncSession = Depends(get_api_db_session)) -> TaskService:
    return TaskService(db_session=session)


# Допоміжна залежність для перевірки прав на перегляд/редагування відгуків завдання
async def review_access_dependency(
        task_id: UUID = Path(..., description="ID Завдання, до якого належать відгуки"),  # i18n
        # Використовуємо check_group_view_permission, передаючи group_id завдання
        # Це потребує отримання завдання та його group_id всередині залежності.
        # TODO: Створити більш спеціалізовану залежність, яка приймає task_id і перевіряє членство в групі завдання.
        # Поки що, ця залежність не використовується напряму в шляхах, а логіка вбудована.
        current_user: UserModel = Depends(get_current_active_user),
        task_service: TaskService = Depends(get_task_service_dep)
) -> UserModel:
    task = await task_service.get_task_orm_by_id(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Завдання не знайдено")  # i18n
    # Тепер використовуємо group_id з завдання для перевірки прав через check_group_view_permission
    # Це не зовсім правильно, бо check_group_view_permission приймає group_id з Path.
    # Потрібна адаптація або нова залежність.
    # Для прикладу, тут просто повернемо користувача, якщо завдання знайдено.
    # Фактична перевірка прав буде вбудована в ендпоінти або сервіси.
    if not current_user.is_superuser:
        # Тут має бути перевірка членства користувача в групі task.group_id
        pass  # Заглушка
    return current_user


@router.post(
    "/task/{task_id}",  # Шлях: /reviews/task/{task_id}
    response_model=TaskReviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Створення або оновлення відгуку на завдання",  # i18n
    description="""Дозволяє користувачу залишити або оновити свій відгук (оцінка, коментар) на завдання.
    Зазвичай один користувач може залишити один відгук на завдання (або на виконання)."""  # i18n
)
async def create_or_update_task_review(
        task_id: UUID = Path(..., description="ID завдання, для якого залишається відгук"),  # i18n
        review_in: TaskReviewCreate,  # Схема для створення/оновлення
        current_user: UserModel = Depends(get_current_active_user),
        # Будь-який активний користувач, що має доступ до завдання
        review_service: TaskReviewService = Depends(get_task_review_service),
        # TODO: Додати залежність для перевірки, чи користувач може залишати відгук на це завдання
        # (наприклад, чи він є членом групи завдання або виконавцем)
):
    """
    Створює новий відгук або оновлює існуючий відгук користувача на завдання.
    Сервіс `create_task_review` має обробляти логіку "один відгук на користувача" (upsert).
    """
    logger.info(f"Користувач ID '{current_user.id}' створює/оновлює відгук для завдання ID '{task_id}'.")
    try:
        # TaskReviewService.create_task_review може приймати completion_id з review_in, якщо він там є.
        # Припускаємо, що review_in може містити completion_id.
        completion_id = getattr(review_in, 'completion_id', None)

        # TODO: Уточнити, чи сервіс create_task_review реалізує логіку upsert.
        # Якщо ні, потрібно спочатку перевірити існування відгуку.
        # Поки що припускаємо, що сервіс обробляє це.
        review = await review_service.create_task_review(
            task_id=task_id,
            reviewer_user_id=current_user.id,
            review_data=review_in,
            completion_id=completion_id
        )
        return review
    except ValueError as e:
        logger.warning(f"Помилка створення/оновлення відгуку для завдання ID '{task_id}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except PermissionError as e:
        logger.warning(f"Заборона створення/оновлення відгуку для завдання ID '{task_id}': {e}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка: {e}", exc_info=global_settings.DEBUG)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутрішня помилка сервера.")


@router.get(
    "/task/{task_id}",  # Шлях: /reviews/task/{task_id}
    response_model=PagedResponse[TaskReviewResponse],
    summary="Список відгуків для завдання",  # i18n
    description="Повертає список відгуків для вказаного завдання з пагінацією. Доступно користувачам, що мають доступ до завдання.",
    # i18n
    # dependencies=[Depends(task_view_permission_dependency)] # TODO: Адаптувати або створити залежність
)
async def list_reviews_for_task_endpoint(  # Перейменовано
        task_id: UUID = Path(..., description="ID завдання"),  # i18n
        page_params: PageParams = Depends(paginator),
        current_user: UserModel = Depends(get_current_active_user),  # Для перевірки доступу до завдання
        review_service: TaskReviewService = Depends(get_task_review_service),
        task_service: TaskService = Depends(get_task_service_dep)  # Для отримання групи завдання
):
    """Отримує список відгуків для конкретного завдання."""
    # Перевірка доступу до завдання (чи є користувач членом групи завдання)
    task_orm = await task_service.get_task_orm_by_id(task_id)
    if not task_orm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Завдання не знайдено")  # i18n

    # Використовуємо залежність check_group_view_permission з groups.py, передаючи group_id завдання
    # Це приклад, як можна було б зробити. Краще мати спеціалізовану залежність.
    try:
        await check_group_view_permission(group_id=task_orm.group_id, current_user=current_user,
                                          membership_service=Depends(
                                              get_membership_service_dep).dependency)  # type: ignore
    except HTTPException as e:
        if e.status_code == status.HTTP_403_FORBIDDEN:
            # i18n
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Ви не маєте доступу для перегляду відгуків цього завдання.")
        raise e

    logger.debug(f"Запит списку відгуків для завдання ID '{task_id}'.")
    # TODO: TaskReviewService.list_reviews_for_task має повертати (items, total_count)
    reviews_orm, total_reviews = await review_service.list_reviews_for_task_paginated(
        task_id=task_id,
        skip=page_params.skip,
        limit=page_params.limit
    )
    return PagedResponse[TaskReviewResponse](
        total=total_reviews,
        page=page_params.page,
        size=page_params.size,
        results=[TaskReviewResponse.model_validate(rev) for rev in reviews_orm]  # Pydantic v2
    )


@router.get(
    "/{review_id}",  # Шлях: /reviews/{review_id}
    response_model=TaskReviewResponse,
    summary="Отримання конкретного відгуку за ID",  # i18n
    description="Повертає деталі конкретного відгуку. Доступно автору, адміну групи завдання або суперюзеру.",  # i18n
    # TODO: Додати залежність для перевірки прав доступу до конкретного відгуку
)
async def get_task_review_by_id_endpoint(  # Перейменовано
        review_id: UUID = Path(..., description="ID відгуку"),  # i18n
        # current_user: UserModel = Depends(get_current_active_user), # Для перевірки прав
        review_service: TaskReviewService = Depends(get_task_review_service)
):
    """Отримує відгук за його ID."""
    # TODO: В TaskReviewService.get_review_by_id додати логіку перевірки прав доступу на основі current_user.
    #  Або ця перевірка має бути в залежності FastAPI.
    logger.debug(f"Запит на отримання відгуку за ID: {review_id}")
    review = await review_service.get_review_by_id(review_id=review_id)
    if not review:
        logger.warning(f"Відгук з ID '{review_id}' не знайдено.")
        # i18n
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Відгук не знайдено.")
    return review


@router.put(
    "/{review_id}",  # Шлях: /reviews/{review_id}
    response_model=TaskReviewResponse,
    summary="Оновлення відгуку на завдання",  # i18n
    description="Дозволяє автору відгуку оновити свій відгук.",  # i18n
    # TODO: Додати залежність, що перевіряє, чи є current_user автором відгуку.
)
async def update_task_review(
        review_id: UUID = Path(..., description="ID відгуку для оновлення"),  # i18n
        review_in: TaskReviewUpdate,  # Схема для оновлення (зазвичай rating, comment)
        current_user: UserModel = Depends(get_current_active_user),  # Автор відгуку
        review_service: TaskReviewService = Depends(get_task_review_service)
) -> TaskReviewResponse:
    """Оновлює існуючий відгук. Доступно тільки автору відгуку."""
    logger.info(f"Користувач ID '{current_user.id}' намагається оновити відгук ID '{review_id}'.")
    try:
        # TaskReviewService.update_task_review має перевіряти, чи current_user є автором.
        updated_review = await review_service.update_task_review(
            review_id=review_id,
            review_update_data=review_in,
            current_user_id=current_user.id
        )
        if not updated_review:  # Малоймовірно, якщо сервіс кидає винятки
            # i18n
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Відгук не знайдено або оновлення не вдалося.")
        return updated_review
    except ValueError as e:
        logger.warning(f"Помилка валідації при оновленні відгуку ID '{review_id}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except PermissionError as e:
        logger.warning(f"Заборона оновлення відгуку ID '{review_id}': {e}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при оновленні відгуку ID '{review_id}': {e}", exc_info=global_settings.DEBUG)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутрішня помилка сервера.")


@router.delete(
    "/{review_id}",  # Шлях: /reviews/{review_id}
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалення відгуку",  # i18n
    description="Дозволяє автору відгуку, адміністратору групи або суперюзеру видалити відгук.",  # i18n
    # TODO: Додати залежність, що перевіряє права (автор, адмін групи завдання, суперюзер).
)
async def delete_task_review_endpoint(  # Перейменовано
        review_id: UUID = Path(..., description="ID відгуку, який видаляється"),  # i18n
        current_user: UserModel = Depends(get_current_active_user),  # Для перевірки прав
        review_service: TaskReviewService = Depends(get_task_review_service)
):
    """
    Видаляє відгук.
    Доступно автору, адміністратору групи завдання або суперюзеру.
    """
    logger.info(f"Користувач ID '{current_user.id}' намагається видалити відгук ID '{review_id}'.")
    try:
        # TaskReviewService.delete_task_review має перевіряти права.
        success = await review_service.delete_task_review(
            review_id=review_id,
            current_user_id=current_user.id  # Передаємо для перевірки прав в сервісі
        )
        if not success:
            logger.warning(f"Не вдалося видалити відгук ID '{review_id}' (сервіс повернув False).")
            # i18n
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Відгук не знайдено або не вдалося видалити.")
    except ValueError as e:  # Наприклад, якщо об'єкт не знайдено (вже оброблено вище)
        logger.warning(f"Помилка видалення відгуку ID '{review_id}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except PermissionError as e:  # Якщо сервіс кидає помилку прав
        logger.warning(f"Заборона видалення відгуку ID '{review_id}': {e}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при видаленні відгуку ID '{review_id}': {e}", exc_info=global_settings.DEBUG)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутрішня помилка сервера.")

    return None  # HTTP 204 No Content


logger.info("Роутер для відгуків на завдання (`/reviews`) визначено.")
