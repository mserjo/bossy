# backend/app/src/api/v1/dictionaries/bonus_types.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для управління довідником "Типи Бонусів".

Дозволяє створювати, отримувати, оновлювати та видаляти типи бонусів.
Доступ до операцій створення, оновлення та видалення обмежений для суперкористувачів.
Перегляд списку та окремих елементів доступний автентифікованим користувачам.

Сумісність: Python 3.13, SQLAlchemy v2, Pydantic v2.
"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.src.api.dependencies import get_api_db_session, get_current_active_superuser, get_current_active_user  # Залежності для авторизації
from backend.app.src.models.auth.user import User as UserModel  # Для типізації current_user
from backend.app.src.schemas.dictionaries.bonus_types import BonusTypeCreate, BonusTypeUpdate, BonusTypeResponse
from backend.app.src.services.dictionaries.bonus_types import BonusTypeService
from backend.app.src.core.pagination import PagedResponse, PageParams  # Для пагінації
from backend.app.src.api.dependencies import paginator  # Залежність для пагінації
from backend.app.src.config.logging import logger  # Централізований логер

router = APIRouter(
    # Префікс буде /bonus-types з __init__.py батьківського роутера
    # Теги також будуть успадковані та/або додані
)


# Залежність для отримання BonusTypeService
async def get_bonus_type_service(session: AsyncSession = Depends(get_api_db_session)) -> BonusTypeService:
    """
    Залежність FastAPI для отримання екземпляра BonusTypeService.
    """
    return BonusTypeService(db_session=session)  # Використовуємо db_session напряму

# ПРИМІТКА: Реалізація поля `created_by_user_id` (якщо воно є в моделі BonusType)
# залежить від можливостей базового сервісу `BaseDictionaryService` або має бути
# реалізована тут явно.
@router.post(
    "/",
    response_model=BonusTypeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Створити новий тип бонусу",  # i18n
    description="Дозволяє суперкористувачу створювати новий тип бонусу.",  # i18n
    dependencies=[Depends(get_current_active_superuser)]  # Тільки суперюзер
)
async def create_bonus_type(
        bonus_type_in: BonusTypeCreate,
        service: BonusTypeService = Depends(get_bonus_type_service),
        current_user: UserModel = Depends(get_current_active_superuser)  # Для created_by_user_id
) -> BonusTypeResponse:
    """
    Створює новий тип бонусу.
    Доступно тільки суперкористувачам.
    """
    logger.info(f"Спроба створення типу бонусу '{bonus_type_in.name}' користувачем ID '{current_user.id}'.")
    try:
        # BaseDictionaryService.create може приймати kwargs для дод. полів
        # TODO: Перевірити, чи модель BonusType має created_by_user_id і чи BaseDictionaryService це обробляє.
        # Припускаємо, що BaseDictionaryService.create може приймати created_by_user_id через kwargs,
        # або це поле встановлюється на рівні моделі/БД.
        # Поки що передаємо як є, якщо сервіс це підтримує.
        # Або, якщо потрібно явно: bonus_type_in_dict = bonus_type_in.model_dump(); bonus_type_in_dict['created_by_user_id'] = current_user.id
        created_bonus_type = await service.create(
            data=bonus_type_in)  # created_by_user_id не передається явно, якщо модель/база це робить
        return created_bonus_type
    except ValueError as e:  # Обробка помилок унікальності або інших помилок валідації з сервісу
        logger.warning(f"Помилка створення типу бонусу '{bonus_type_in.name}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при створенні типу бонусу '{bonus_type_in.name}': {e}", exc_info=True)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Внутрішня помилка сервера при створенні типу бонусу.")


@router.get(
    "/{bonus_type_id}",
    response_model=BonusTypeResponse,
    summary="Отримати тип бонусу за ID",  # i18n
    description="Дозволяє автентифікованим користувачам отримувати інформацію про конкретний тип бонусу.",  # i18n
    dependencies=[Depends(get_current_active_user)]  # Будь-який активний користувач
)
async def get_bonus_type(
        bonus_type_id: UUID,
        service: BonusTypeService = Depends(get_bonus_type_service),
) -> BonusTypeResponse:
    """
    Отримує тип бонусу за його ID.
    Доступно будь-якому автентифікованому користувачеві.
    """
    logger.debug(f"Запит на отримання типу бонусу за ID: {bonus_type_id}")
    db_bonus_type = await service.get_by_id(item_id=bonus_type_id)
    if not db_bonus_type:
        logger.warning(f"Тип бонусу з ID '{bonus_type_id}' не знайдено.")
        # i18n
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тип бонусу не знайдено.")
    return db_bonus_type

# ПРИМІТКА: Коректна пагінація залежить від реалізації методу `count_all()`
# в `BonusTypeService` (успадкованого від `BaseDictionaryService`), як зазначено в TODO.
# Також, можливість сортування залежить від реалізації в методі `get_all`.
@router.get(
    "/",
    response_model=PagedResponse[BonusTypeResponse],
    summary="Отримати список всіх типів бонусів",  # i18n
    description="Дозволяє автентифікованим користувачам отримувати сторінковий список всіх типів бонусів.",  # i18n
    dependencies=[Depends(get_current_active_user)]  # Будь-який активний користувач
)
async def get_all_bonus_types(
        page_params: PageParams = Depends(paginator),  # Залежність для пагінації
        service: BonusTypeService = Depends(get_bonus_type_service),
) -> PagedResponse[BonusTypeResponse]:
    """
    Отримує всі типи бонусів з пагінацією.
    Доступно будь-якому автентифікованому користувачеві.
    """
    logger.debug(f"Запит на отримання списку типів бонусів: сторінка {page_params.page}, розмір {page_params.size}")
    # TODO: Додати сортування до сервісного методу get_all, якщо потрібно, або передати з page_params
    bonus_types_page = await service.get_all(skip=page_params.skip, limit=page_params.limit)

    # Для PagedResponse потрібна загальна кількість елементів для розрахунку сторінок
    # BaseDictionaryService має надати метод count()
    # TODO: Реалізувати метод count() в BaseDictionaryService або тут викликати окремий запит count.
    # Припускаємо, що сервіс може мати метод count() або get_all повертає кортеж (items, total_count)
    # Для прикладу, поки що використовуємо len(), що не є коректним для реальної пагінації з БД.
    # total_count = len(bonus_types_page) # ЗАГЛУШКА - ПОТРІБЕН РЕАЛЬНИЙ COUNT

    # Якщо get_all повертає тільки список, а count треба окремо:
    total_count = await service.count_all()  # Припускаємо, що такий метод є або буде доданий до BaseDictionaryService

    return PagedResponse(
        results=bonus_types_page,
        total=total_count,
        page=page_params.page,
        size=page_params.size
    )


@router.put(
    "/{bonus_type_id}",
    response_model=BonusTypeResponse,
    summary="Оновити тип бонусу",  # i18n
    description="Дозволяє суперкористувачу оновлювати існуючий тип бонусу.",  # i18n
    dependencies=[Depends(get_current_active_superuser)]  # Тільки суперюзер
)
async def update_bonus_type(
        bonus_type_id: UUID,
        bonus_type_in: BonusTypeUpdate,
        service: BonusTypeService = Depends(get_bonus_type_service),
        current_user: UserModel = Depends(get_current_active_superuser)  # Для updated_by_user_id
) -> BonusTypeResponse:
    """
    Оновлює існуючий тип бонусу.
    Доступно тільки суперкористувачам.
    """
    logger.info(f"Спроба оновлення типу бонусу ID '{bonus_type_id}' користувачем ID '{current_user.id}'.")
    try:
        # BaseDictionaryService.update може приймати kwargs для дод. полів
        updated_bonus_type = await service.update(item_id=bonus_type_id,
                                                  data=bonus_type_in)  # updated_by_user_id не передається явно
        if not updated_bonus_type:  # Сервіс повертає None, якщо об'єкт не знайдено
            logger.warning(f"Тип бонусу з ID '{bonus_type_id}' не знайдено для оновлення.")
            # i18n
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тип бонусу не знайдено.")
        return updated_bonus_type
    except ValueError as e:  # Обробка помилок унікальності або інших помилок валідації з сервісу
        logger.warning(f"Помилка оновлення типу бонусу ID '{bonus_type_id}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при оновленні типу бонусу ID '{bonus_type_id}': {e}", exc_info=True)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Внутрішня помилка сервера при оновленні типу бонусу.")


@router.delete(
    "/{bonus_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалити тип бонусу",  # i18n
    description="Дозволяє суперкористувачу видалити тип бонусу. Виконується жорстке видалення.",  # i18n
    dependencies=[Depends(get_current_active_superuser)]  # Тільки суперюзер
)
async def delete_bonus_type(
        bonus_type_id: UUID,
        service: BonusTypeService = Depends(get_bonus_type_service),
        current_user: UserModel = Depends(get_current_active_superuser)  # Для логування аудиту
):
    """
    Видаляє тип бонусу за його ID.
    Доступно тільки суперкористувачам.
    """
    logger.info(f"Спроба видалення типу бонусу ID '{bonus_type_id}' користувачем ID '{current_user.id}'.")
    # BaseDictionaryService.delete повертає bool або кидає виняток
    try:
        deleted = await service.delete(item_id=bonus_type_id)
        if not deleted:  # Якщо сервіс повернув False (наприклад, не знайдено)
            logger.warning(f"Тип бонусу з ID '{bonus_type_id}' не знайдено для видалення.")
            # i18n
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тип бонусу не знайдено.")
    except ValueError as e:  # Якщо сервіс кинув ValueError (наприклад, об'єкт використовується)
        logger.warning(f"Помилка видалення типу бонусу ID '{bonus_type_id}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при видаленні типу бонусу ID '{bonus_type_id}': {e}", exc_info=True)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Внутрішня помилка сервера при видаленні типу бонусу.")

    return None  # Повертаємо порожню відповідь зі статусом 204


logger.info(f"Роутер для довідника '{router.prefix}' (Типи Бонусів) визначено.")
