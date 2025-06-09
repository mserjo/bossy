# backend/app/src/api/v1/bonuses/bonus_rules.py
from typing import List, Optional, Generic, TypeVar # Додано Generic, TypeVar для PaginatedResponse
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel # Додано BaseModel для PaginatedResponse, якщо визначається локально
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.dependencies import get_db_session, get_current_active_user # Potentially get_current_active_superuser for some actions
from app.src.models.auth import User as UserModel
# from app.src.models.bonuses import BonusRule as BonusRuleModel # Потрібна модель правила бонусу
from app.src.schemas.bonuses.bonus_rule import ( # Схеми для правил бонусів
    BonusRuleCreate,
    BonusRuleUpdate,
    BonusRuleResponse
)
# Припускаємо, що ці схеми імпортуються, якщо ні - можна визначити як у users.py або groups.py
from app.src.schemas.pagination import PaginatedResponse, PageParams
from app.src.services.bonuses.bonus_rule import BonusRuleService # Сервіс для правил бонусів

router = APIRouter()

@router.post(
    "/", # Шлях відносно префіксу /bonuses/rules
    response_model=BonusRuleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Створення нового правила бонусу",
    description="Дозволяє адміністратору групи або суперюзеру створити нове правило для нарахування/списання бонусів."
)
async def create_bonus_rule(
    rule_in: BonusRuleCreate, # Очікує group_id (якщо правило специфічне для групи), task_type_id, event_type_id, points, тощо.
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user), # Адмін групи або суперюзер
    rule_service: BonusRuleService = Depends()
):
    '''
    Створює нове правило бонусу.
    - `group_id`: ID групи, для якої діє правило (None для глобальних правил, якщо підтримується).
    - `name`: Назва правила.
    - `description`: Опис правила.
    - `points`: Кількість балів (може бути від'ємною для штрафів).
    - `task_type_id`: ID типу задачі, до якої прив'язане правило (опціонально).
    - `event_type_id`: ID типу події, до якої прив'язане правило (опціонально).
    - `condition`: Додаткові умови правила (наприклад, JSON або спеціальний формат).
    '''
    if not hasattr(rule_service, 'db_session') or rule_service.db_session is None:
        rule_service.db_session = db

    # Перевірка прав (чи є користувач адміном групи або суперюзером) - логіка в сервісі
    created_rule = await rule_service.create_bonus_rule(
        rule_create_schema=rule_in,
        requesting_user=current_user
    )
    # Сервіс має кидати HTTPException у разі помилок
    return BonusRuleResponse.model_validate(created_rule)

@router.get(
    "/",
    response_model=PaginatedResponse[BonusRuleResponse],
    summary="Отримання списку правил бонусів",
    description="""Повертає список правил бонусів з пагінацією.
    Може фільтруватися за групою (`group_id`), типом задачі/події тощо."""
)
async def read_bonus_rules(
    group_id: Optional[int] = Query(None, description="ID групи для фільтрації правил"),
    task_type_id: Optional[int] = Query(None, description="ID типу задачі для фільтрації"),
    event_type_id: Optional[int] = Query(None, description="ID типу події для фільтрації"),
    page_params: PageParams = Depends(),
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user), # Для перевірки доступу до правил групи
    rule_service: BonusRuleService = Depends()
):
    '''
    Отримує список правил бонусів.
    Доступність правил залежить від контексту користувача та групи.
    '''
    if not hasattr(rule_service, 'db_session') or rule_service.db_session is None:
        rule_service.db_session = db

    total_rules, rules = await rule_service.get_bonus_rules(
        requesting_user=current_user,
        group_id=group_id,
        task_type_id=task_type_id,
        event_type_id=event_type_id,
        skip=page_params.skip,
        limit=page_params.limit
    )

    return PaginatedResponse[BonusRuleResponse]( # Явно вказуємо тип Generic
        total=total_rules,
        page=page_params.page,
        size=page_params.size,
        results=[BonusRuleResponse.model_validate(rule) for rule in rules]
    )

@router.get(
    "/{rule_id}",
    response_model=BonusRuleResponse,
    summary="Отримання інформації про правило бонусу за ID",
    description="Повертає детальну інформацію про конкретне правило бонусу."
)
async def read_bonus_rule_by_id(
    rule_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user), # Для перевірки доступу
    rule_service: BonusRuleService = Depends()
):
    '''
    Отримує інформацію про правило бонусу за його ID.
    Перевірка доступу до правила (через групу або глобальний статус) виконується в сервісі.
    '''
    if not hasattr(rule_service, 'db_session') or rule_service.db_session is None:
        rule_service.db_session = db

    rule = await rule_service.get_bonus_rule_by_id(rule_id=rule_id, requesting_user=current_user)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Правило бонусу з ID {rule_id} не знайдено або доступ заборонено."
        )
    return BonusRuleResponse.model_validate(rule)

@router.put(
    "/{rule_id}",
    response_model=BonusRuleResponse,
    summary="Оновлення інформації про правило бонусу",
    description="Дозволяє адміністратору групи або суперюзеру оновити існуюче правило бонусу."
)
async def update_bonus_rule(
    rule_id: int,
    rule_in: BonusRuleUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user), # Адмін групи або суперюзер
    rule_service: BonusRuleService = Depends()
):
    '''
    Оновлює дані правила бонусу.
    Перевірка прав - у сервісі.
    '''
    if not hasattr(rule_service, 'db_session') or rule_service.db_session is None:
        rule_service.db_session = db

    updated_rule = await rule_service.update_bonus_rule(
        rule_id=rule_id,
        rule_update_schema=rule_in,
        requesting_user=current_user
    )
    # Сервіс має кидати HTTPException у разі помилок
    return BonusRuleResponse.model_validate(updated_rule)

@router.delete(
    "/{rule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалення правила бонусу",
    description="Дозволяє адміністратору групи або суперюзеру видалити правило бонусу."
)
async def delete_bonus_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserModel = Depends(get_current_active_user), # Адмін групи або суперюзер
    rule_service: BonusRuleService = Depends()
):
    '''
    Видаляє правило бонусу.
    Перевірка прав - у сервісі.
    '''
    if not hasattr(rule_service, 'db_session') or rule_service.db_session is None:
        rule_service.db_session = db

    success = await rule_service.delete_bonus_rule(rule_id=rule_id, requesting_user=current_user)
    if not success: # Сервіс має кидати HTTPException
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, # Або 403
            detail=f"Не вдалося видалити правило бонусу з ID {rule_id}. Можливо, його не існує або у вас немає прав."
        )
    # HTTP 204 No Content

# Міркування:
# 1.  Схеми: `BonusRuleCreate`, `BonusRuleUpdate`, `BonusRuleResponse` з `app.src.schemas.bonuses.bonus_rule`.
# 2.  Сервіс `BonusRuleService`: Інкапсулює бізнес-логіку та перевірку прав.
#     - Правила можуть бути прив'язані до груп, типів задач, типів подій або бути глобальними.
# 3.  Права доступу: Адміністратори груп можуть керувати правилами для своїх груп. Суперюзери - глобальними або всіма.
# 4.  Пагінація: Для списку правил. Фільтрація за `group_id`, `task_type_id`, `event_type_id`.
# 5.  Коментарі: Українською мовою.
# 6.  URL-и: Цей роутер буде підключений до `bonuses_router` (в `bonuses/__init__.py`)
#     з префіксом `/rules`. Шляхи будуть `/api/v1/bonuses/rules/`, `/api/v1/bonuses/rules/{rule_id}`.
