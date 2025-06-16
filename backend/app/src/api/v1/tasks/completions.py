# backend/app/src/api/v1/tasks/completions.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для управління виконанням завдань та подій.

Включає позначення завдань/подій як виконаних користувачами,
а також їх ухвалення або відхилення адміністраторами.

Сумісність: Python 3.13, SQLAlchemy v2, Pydantic v2.
"""
from typing import List, Optional  # Generic, TypeVar, BaseModel не потрібні, якщо імпортуються з core
from uuid import UUID  # ID тепер UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

# Повні шляхи імпорту
from backend.app.src.api.dependencies import (
    get_api_db_session, get_current_active_user,
    # TODO: Створити/використати залежності для перевірки прав адміна групи або суперюзера,
    #  які приймають group_id або completion_id для контексту.
    #  Наприклад, require_group_admin_or_superuser(group_id: UUID = Query(None))
    #  require_completion_reviewer(completion_id: UUID = Path(...))
    get_current_active_superuser,  # Тимчасово для адмінських дій
    paginator
)
from backend.app.src.models.auth.user import User as UserModel
from backend.app.src.schemas.tasks.completion import (
    TaskCompletionCreateRequest,
    TaskCompletionResponse,
    TaskCompletionAdminUpdateRequest  # Перейменовано з CompletionAdminUpdateRequest для ясності
)
from backend.app.src.core.pagination import PagedResponse, PageParams
from backend.app.src.services.tasks.completion import TaskCompletionService
from backend.app.src.core.constants import TASK_COMPLETION_STATUS_APPROVED, TASK_COMPLETION_STATUS_REJECTED # Імпорт статусів
from backend.app.src.config.logging import logger  # Централізований логер
from backend.app.src.config import settings as global_settings

router = APIRouter()


# Залежність для отримання TaskCompletionService
async def get_task_completion_service(session: AsyncSession = Depends(get_api_db_session)) -> TaskCompletionService:
    """Залежність FastAPI для отримання екземпляра TaskCompletionService."""
    return TaskCompletionService(db_session=session)


# TODO: Визначити більш гранульовані залежності для перевірки прав, наприклад:
# async def require_task_assignee_or_group_member(task_id: UUID = Path(...), ...): ...
# async def require_completion_reviewer(completion_id: UUID = Path(...), ...): ... (перевіряє, чи є юзер адміном групи завдання)


@router.post(
    "/task/{task_id}/complete",
    response_model=TaskCompletionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Позначення завдання як виконаного користувачем",  # i18n
    description="""Дозволяє користувачу позначити призначене йому завдання як виконане.
    Залежно від налаштувань типу завдання, може потребувати підтвердження адміністратором."""  # i18n
)
# ПРИМІТКА: Цей ендпоінт залежить від реалізації `mark_task_as_completed_by_user`
# в `TaskCompletionService`, включаючи перевірку, чи призначено завдання
# користувачеві та чи дозволено йому самостійно позначати виконання.
async def mark_task_as_completed(
        task_id: UUID = Path(..., description="ID завдання, яке позначено як виконане"),  # i18n
        completion_data: TaskCompletionCreateRequest = Depends(TaskCompletionCreateRequest.as_form),
        # Дозволяє пусте тіло, якщо всі поля опціональні, або використовуйте Body(...)
        current_user: UserModel = Depends(get_current_active_user),  # Будь-який активний користувач
        completion_service: TaskCompletionService = Depends(get_task_completion_service)
) -> TaskCompletionResponse:
    """
    Користувач позначає завдання як виконане.
    Сервіс перевіряє, чи завдання призначене користувачеві (якщо потрібно) і чи може бути позначене як виконане.
    """
    logger.info(
        f"Користувач ID '{current_user.id}' позначає завдання ID '{task_id}' як виконане. Дані: {completion_data.model_dump(exclude_unset=True)}")
    try:
        # TaskCompletionService.mark_task_as_completed_by_user тепер приймає user_id
        new_completion = await completion_service.mark_task_as_completed_by_user(
            task_id=task_id,
            user_id=current_user.id,  # Передаємо ID поточного користувача
            completion_data=completion_data
        )
        return new_completion
    except ValueError as e:
        logger.warning(
            f"Помилка позначення завдання ID '{task_id}' як виконаного користувачем ID '{current_user.id}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except PermissionError as e:  # Якщо сервіс перевіряє права і кидає PermissionError
        logger.warning(
            f"Заборона доступу для користувача ID '{current_user.id}' при позначенні завдання ID '{task_id}': {e}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка: {e}", exc_info=global_settings.DEBUG)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутрішня помилка сервера.")


# TODO: Додати ендпоінт для позначення подій як виконаних/відвіданих, аналогічно до завдань,
#  якщо логіка відрізняється або якщо TaskCompletionCreateRequest не підходить для подій.
#  @router.post("/event/{event_id}/complete", ...)


@router.get(
    "/pending-approval",
    response_model=PagedResponse[TaskCompletionResponse],
    summary="Список виконань, що очікують підтвердження (Адмін/Суперюзер)",  # i18n
    description="""Повертає список виконань завдань/подій, які потребують підтвердження.
    Доступно адміністраторам групи (якщо вказано `group_id`) або суперюзерам (для всіх груп).""",  # i18n
    dependencies=[Depends(get_current_active_user)]  # Базова перевірка, детальніша логіка в сервісі
)
# ПРИМІТКА: Важливою є реалізація коректної логіки фільтрації та прав доступу
# в `list_completions_pending_approval_paginated` сервісу, щоб адміністратори
# бачили тільки виконання в своїх групах, а суперюзери - всі.
# Також, сервіс має коректно повертати загальну кількість для пагінації.
async def list_completions_pending_approval(
        group_id: Optional[UUID] = Query(None,
                                         description="ID групи для фільтрації (адміни групи бачать тільки свою групу)"),
        # i18n
        page_params: PageParams = Depends(paginator),
        current_user: UserModel = Depends(get_current_active_user),
        completion_service: TaskCompletionService = Depends(get_task_completion_service)
) -> PagedResponse[TaskCompletionResponse]:
    """
    Отримує список виконань, що очікують на підтвердження.
    """
    logger.info(
        f"Користувач ID '{current_user.id}' запитує список виконань, що очікують на ухвалення. Група: {group_id}, сторінка: {page_params.page}.")
    # TODO: TaskCompletionService.list_completions_pending_approval_paginated має повертати (items, total_count)
    #  та враховувати права current_user (суперюзер бачить все, адмін групи - тільки своєї).
    completions_orm, total_completions = await completion_service.list_completions_pending_approval_paginated(
        requesting_user_id=current_user.id,
        is_superuser=current_user.is_superuser,
        group_id_filter=group_id,
        skip=page_params.skip,
        limit=page_params.limit
    )
    return PagedResponse[TaskCompletionResponse](
        total=total_completions,
        page=page_params.page,
        size=page_params.size,
        results=[TaskCompletionResponse.model_validate(comp) for comp in completions_orm]  # Pydantic v2
    )


# TODO: Створити залежність `require_completion_reviewer(completion_id: UUID = Path(...))`
#  яка перевіряє, чи є `current_user` адміном групи, до якої належить завдання цього виконання, або суперюзером.

@router.post(
    "/{completion_id}/approve",
    response_model=TaskCompletionResponse,
    summary="Підтвердження виконання (Адмін/Суперюзер)",  # i18n
    description="Дозволяє адміністратору групи або суперюзеру підтвердити виконання завдання/події.",  # i18n
    # dependencies=[Depends(require_completion_reviewer)] # Використовувати залежність для прав
)
# ПРИМІТКА: Важливою є реалізація гранульованої перевірки прав доступу
# (адміністратор групи завдання або суперюзер) замість тимчасової залежності
# від `get_current_active_superuser`, як зазначено в TODO.
async def approve_completion(
        completion_id: UUID = Path(..., description="ID виконання, яке підтверджується"),  # i18n
        admin_update_data: TaskCompletionAdminUpdateRequest,  # Опціонально, може містити коментар
        current_user: UserModel = Depends(get_current_active_superuser),  # Тимчасово, потрібна гранульована перевірка
        completion_service: TaskCompletionService = Depends(get_task_completion_service)
) -> TaskCompletionResponse:
    """
    Адміністратор підтверджує виконання. `admin_update_data` може містити коментар.
    """
    logger.info(f"Адмін/Суперюзер ID '{current_user.id}' підтверджує виконання ID '{completion_id}'.")
    try:
        # Передаємо admin_update_data, навіть якщо воно може бути порожнім (тільки зі статусом)
        approved_completion = await completion_service.update_task_completion_status(
            completion_id=completion_id,
            admin_update_data=admin_update_data.model_copy(update={"status": TASK_COMPLETION_STATUS_APPROVED}), # Використання константи
            # Pydantic v2 model_copy
            admin_user_id=current_user.id
        )
        return approved_completion
    except ValueError as e:  # Наприклад, виконання не знайдено, або не в тому статусі
        logger.warning(f"Помилка підтвердження виконання ID '{completion_id}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except PermissionError as e:
        logger.warning(f"Заборона підтвердження виконання ID '{completion_id}': {e}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при підтвердженні виконання ID '{completion_id}': {e}",
                     exc_info=global_settings.DEBUG)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутрішня помилка сервера.")


@router.post(
    "/{completion_id}/reject",
    response_model=TaskCompletionResponse,
    summary="Відхилення виконання (Адмін/Суперюзер)",  # i18n
    description="Дозволяє адміністратору групи або суперюзеру відхилити виконання завдання/події. Коментар є бажаним."
    # i18n
    # dependencies=[Depends(require_completion_reviewer)]
)
# ПРИМІТКА: Аналогічно до `approve_completion`, цей ендпоінт потребує ретельної
# реалізації перевірки прав доступу. Коментар `admin_notes` при відхиленні є важливим.
async def reject_completion(
        completion_id: UUID = Path(..., description="ID виконання, яке відхиляється"),  # i18n
        admin_update_data: TaskCompletionAdminUpdateRequest,  # Має містити admin_notes
        current_user: UserModel = Depends(get_current_active_superuser),  # Тимчасово
        completion_service: TaskCompletionService = Depends(get_task_completion_service)
) -> TaskCompletionResponse:
    """
    Адміністратор відхиляє виконання. `admin_update_data` має містити причину відхилення.
    """
    logger.info(
        f"Адмін/Суперюзер ID '{current_user.id}' відхиляє виконання ID '{completion_id}'. Причина: {admin_update_data.admin_notes}")
    if not admin_update_data.admin_notes:  # Коментар при відхиленні важливий
        # i18n
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Причина відхилення (admin_notes) є обов'язковою.")

    try:
        rejected_completion = await completion_service.update_task_completion_status(
            completion_id=completion_id,
            admin_update_data=admin_update_data.model_copy(update={"status": TASK_COMPLETION_STATUS_REJECTED}), # Використання константи
            # Pydantic v2
            admin_user_id=current_user.id
        )
        return rejected_completion
    except ValueError as e:
        logger.warning(f"Помилка відхилення виконання ID '{completion_id}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except PermissionError as e:
        logger.warning(f"Заборона відхилення виконання ID '{completion_id}': {e}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при відхиленні виконання ID '{completion_id}': {e}",
                     exc_info=global_settings.DEBUG)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутрішня помилка сервера.")


# TODO: Додати ендпоінти для перегляду деталей конкретного виконання (GET /{completion_id})
# TODO: Додати ендпоінти для перегляду виконань для конкретного завдання або користувача (GET /task/{task_id}/completions, GET /user/{user_id}/completions)
#  (частково реалізовано в TaskCompletionService, потрібно винести в API)

logger.info("Роутер для управління виконанням завдань (`/completions`) визначено.")
