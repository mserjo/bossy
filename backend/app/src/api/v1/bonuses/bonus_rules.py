# backend/app/src/api/v1/bonuses/bonus_rules.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для управління правилами нарахування бонусів/штрафів API v1.

Цей модуль може надавати API для CRUD операцій з правилами бонусів,
які можуть бути пов'язані з типами завдань, конкретними завданнями або подіями.
Наприклад, скільки бонусів нараховується за виконання певного типу завдання,
або який штраф за невиконання.

Доступ до управління цими правилами, ймовірно, матимуть адміністратори груп.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Path, Response
from typing import List, Optional

from backend.app.src.config.logging import get_logger
# Припускаємо, що схеми та сервіс існують. Якщо ні, їх потрібно буде створити.
# Назви схем та сервісу можуть відрізнятися.
from backend.app.src.schemas.bonuses.bonus_rule import BonusRuleSchema, BonusRuleCreateSchema, BonusRuleUpdateSchema # Прикладні назви
from backend.app.src.services.bonuses.bonus_rule_service import BonusRuleService # Прикладна назва
from backend.app.src.api.dependencies import DBSession, CurrentActiveUser
from backend.app.src.api.v1.groups.groups import group_admin_permission # Для дій адміна групи
from backend.app.src.models.auth.user import UserModel

logger = get_logger(__name__)
router = APIRouter()

# Ендпоінти можуть бути прив'язані до групи: /groups/{group_id}/bonus-rules
# Або до конкретного завдання: /groups/{group_id}/tasks/{task_id}/bonus-rules
# Або бути більш загальними, якщо правила не завжди жорстко прив'язані до групи.
# Для початку, зробимо їх в контексті групи.

@router.post(
    "", # Шлях буде /groups/{group_id}/bonus-rules
    response_model=BonusRuleSchema,
    status_code=status.HTTP_201_CREATED,
    tags=["Bonuses", "Bonus Rules"],
    summary="Створити нове правило для бонусів/штрафів у групі (адміністратор групи)"
)
async def create_bonus_rule_for_group(
    group_id: int = Path(..., description="ID групи, для якої створюється правило"),
    rule_in: BonusRuleCreateSchema,
    group_with_admin_rights: dict = Depends(group_admin_permission),
    db_session: DBSession = Depends()
):
    current_admin: UserModel = group_with_admin_rights["current_user"]

    # Перевірка, чи group_id в rule_in співпадає (якщо він там є)
    # Або сервіс сам встановлює group_id на основі шляху
    # if hasattr(rule_in, 'group_id') and rule_in.group_id is not None and rule_in.group_id != group_id:
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Невідповідність ID групи.")

    logger.info(
        f"Адміністратор {current_admin.email} створює нове правило бонусів "
        f"'{rule_in.name if hasattr(rule_in, 'name') else 'без назви'}' в групі ID {group_id}."
    )
    service = BonusRuleService(db_session)
    try:
        # Сервіс може вимагати group_id для створення правила в контексті групи
        new_rule = await service.create_bonus_rule_for_group(
            rule_create_data=rule_in,
            group_id=group_id,
            creator_id=current_admin.id
        )
        return new_rule
    except HTTPException as e:
        raise e
    except Exception as e_gen:
        logger.error(f"Помилка створення правила бонусів в групі {group_id}: {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера.")


@router.get(
    "",
    response_model=List[BonusRuleSchema],
    tags=["Bonuses", "Bonus Rules"],
    summary="Отримати список правил бонусів/штрафів для групи"
)
async def list_bonus_rules_for_group(
    group_id: int = Path(..., description="ID групи"),
    # Доступ може бути для всіх учасників групи або тільки для адмінів
    access_check: dict = Depends(group_member_permission), # Або group_admin_permission
    db_session: DBSession = Depends(),
    # TODO: Додати фільтри (наприклад, за task_type_id, event_type)
):
    current_user: UserModel = access_check["current_user"]
    logger.info(f"Користувач {current_user.email} запитує список правил бонусів для групи ID {group_id}.")
    service = BonusRuleService(db_session)
    rules = await service.get_bonus_rules_for_group(group_id=group_id)
    return rules

@router.get(
    "/{rule_id}",
    response_model=BonusRuleSchema,
    tags=["Bonuses", "Bonus Rules"],
    summary="Отримати деталі конкретного правила бонусів/штрафів"
)
async def get_bonus_rule_details(
    group_id: int = Path(..., description="ID групи"),
    rule_id: int = Path(..., description="ID правила бонусів"),
    access_check: dict = Depends(group_member_permission),
    db_session: DBSession = Depends()
):
    current_user: UserModel = access_check["current_user"]
    logger.info(f"Користувач {current_user.email} запитує деталі правила бонусів ID {rule_id} з групи {group_id}.")
    service = BonusRuleService(db_session)
    rule = await service.get_bonus_rule_by_id_and_group_id(rule_id=rule_id, group_id=group_id)
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Правило бонусів не знайдено.")
    return rule

@router.put(
    "/{rule_id}",
    response_model=BonusRuleSchema,
    tags=["Bonuses", "Bonus Rules"],
    summary="Оновити правило бонусів/штрафів (адміністратор групи)"
)
async def update_existing_bonus_rule(
    group_id: int = Path(..., description="ID групи"),
    rule_id: int = Path(..., description="ID правила для оновлення"),
    rule_in: BonusRuleUpdateSchema,
    group_with_admin_rights: dict = Depends(group_admin_permission),
    db_session: DBSession = Depends()
):
    current_admin: UserModel = group_with_admin_rights["current_user"]
    logger.info(f"Адміністратор {current_admin.email} оновлює правило бонусів ID {rule_id} в групі {group_id}.")
    service = BonusRuleService(db_session)
    try:
        updated_rule = await service.update_bonus_rule(
            rule_id=rule_id,
            rule_update_data=rule_in,
            group_id_context=group_id,
            actor_id=current_admin.id
        )
        if not updated_rule:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Правило бонусів не знайдено для оновлення.")
        return updated_rule
    except HTTPException as e:
        raise e
    except Exception as e_gen:
        logger.error(f"Помилка оновлення правила бонусів ID {rule_id}: {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера.")

@router.delete(
    "/{rule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Bonuses", "Bonus Rules"],
    summary="Видалити правило бонусів/штрафів (адміністратор групи)"
)
async def delete_existing_bonus_rule(
    group_id: int = Path(..., description="ID групи"),
    rule_id: int = Path(..., description="ID правила для видалення"),
    group_with_admin_rights: dict = Depends(group_admin_permission),
    db_session: DBSession = Depends()
):
    current_admin: UserModel = group_with_admin_rights["current_user"]
    logger.info(f"Адміністратор {current_admin.email} видаляє правило бонусів ID {rule_id} з групи {group_id}.")
    service = BonusRuleService(db_session)
    try:
        success = await service.delete_bonus_rule(
            rule_id=rule_id,
            group_id_context=group_id,
            actor_id=current_admin.id
        )
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Правило бонусів не знайдено або не вдалося видалити.")
    except HTTPException as e:
        raise e
    except Exception as e_gen:
        logger.error(f"Помилка видалення правила бонусів ID {rule_id}: {e_gen}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Помилка сервера.")

    return Response(status_code=status.HTTP_204_NO_CONTENT)

# Роутер буде підключений в backend/app/src/api/v1/bonuses/__init__.py
# з префіксом, наприклад, /groups/{group_id}/bonus-rules
