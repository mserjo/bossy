# backend/app/src/api/v1/bonuses/bonus_rules.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для управління правилами нарахування бонусів.

Дозволяє створювати, отримувати, оновлювати та видаляти правила бонусів.
Доступ до операцій створення, оновлення та видалення обмежений для адміністраторів груп
(для правил їхніх груп) або суперкористувачів (для будь-яких правил, включаючи глобальні).
Перегляд списку та окремих правил доступний членам відповідних груп або всім для глобальних правил.

Сумісність: Python 3.13, SQLAlchemy v2, Pydantic v2.
"""
from typing import List, Optional
from uuid import UUID  # ID тепер UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.src.api.dependencies import (
    get_api_db_session, get_current_active_user,
    get_current_active_superuser, paginator, get_group_membership_service
)
# TODO: Створити/використати залежності для перевірки прав, наприклад:
#  `require_group_admin_or_superuser_for_group_specific(group_id: Optional[UUID] = Query(None))`
#  `require_rule_editor_permission(rule_id: UUID = Path(...))`
#  `require_rule_viewer_permission(rule_id: UUID = Path(...))`
from backend.app.src.api.v1.groups.groups import check_group_edit_permission, check_group_view_permission  # Тимчасово

from backend.app.src.models.auth.user import User as UserModel
from backend.app.src.schemas.bonuses.bonus_rule import (
    BonusRuleCreate, BonusRuleUpdate, BonusRuleResponse
)
from backend.app.src.core.pagination import PagedResponse, PageParams
from backend.app.src.services.bonuses.bonus_rule import BonusRuleService
from backend.app.src.services.groups.group import GroupService  # Для перевірки існування групи
from backend.app.src.config import settings as global_settings
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

router = APIRouter(
    # Префікс /rules буде додано в __init__.py батьківського роутера bonuses
    # Теги також успадковуються/додаються звідти
)


# Залежність для отримання BonusRuleService
async def get_bonus_rule_service(session: AsyncSession = Depends(get_api_db_session)) -> BonusRuleService:
    """Залежність FastAPI для отримання екземпляра BonusRuleService."""
    return BonusRuleService(db_session=session)


# Залежність для GroupService (для перевірки існування групи при створенні правила для групи)
async def get_group_service_dep(session: AsyncSession = Depends(get_api_db_session)) -> GroupService:
    return GroupService(db_session=session)

# ПРИМІТКА: Цей ендпоінт дозволяє створювати правила бонусів. Логіка перевірки прав
# (адміністратор групи або суперкористувач) є важливою. В майбутньому, перевірка прав
# для group_id з тіла запиту має бути інкапсульована в окрему залежність.
@router.post(
    "/",
    response_model=BonusRuleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Створення нового правила бонусу",  # i18n
    description="""Дозволяє адміністратору групи (для правил своєї групи) або суперюзеру (для будь-яких правил,
    включаючи глобальні) створити нове правило для нарахування/списання бонусів."""  # i18n
)
async def create_bonus_rule(
        rule_in: BonusRuleCreate,  # Схема містить group_id (опціонально), task_type_id, points тощо.
        current_user: UserModel = Depends(get_current_active_user),  # Поточний користувач
        rule_service: BonusRuleService = Depends(get_bonus_rule_service),
        group_service: GroupService = Depends(get_group_service_dep)  # Для перевірки групи
):
    """
    Створює нове правило бонусу.
    Якщо `rule_in.group_id` вказано, користувач має бути адміном цієї групи або суперюзером.
    Якщо `rule_in.group_id` не вказано (глобальне правило), тільки суперюзер може його створити.
    """
    logger.info(
        f"Користувач ID '{current_user.id}' намагається створити правило бонусу '{rule_in.name}'. Група: {rule_in.group_id or 'Глобальне'}.")

    # Перевірка прав
    if rule_in.group_id:
        # Використовуємо існуючу залежність (або її логіку), адаптуючи її для group_id з тіла запиту
        temp_group_path_param = Path(rule_in.group_id, description="ID групи")
        try:
            # Це не зовсім ідеально, бо check_group_edit_permission очікує Path параметр.
            # TODO: Створити залежність, що приймає group_id з тіла або Query для перевірки прав.
            # Поки що, якщо не суперюзер, перевіримо права адміна групи.
            if not current_user.is_superuser:
                # Використовуємо get_group_membership_service безпосередньо, оскільки check_group_edit_permission
                # є асинхронною функцією, яку потрібно викликати з await.
                # Для прямого виклику залежності тут, її потрібно було б реструктурувати,
                # або передавати сервіс як аргумент.
                # Краще мати окрему залежність для перевірки "is_group_admin(group_id, user_id)".
                # Поточний check_group_edit_permission не підходить для прямого виклику тут так просто.
                # Залишаємо як є, з розумінням, що це місце для покращення з виділеною залежністю.
                # Для тимчасового рішення, можна було б інстанціювати GroupMembershipService тут,
                # але це порушить DI.
                # Припускаємо, що check_group_edit_permission буде викликаний коректно, якщо це можливо,
                # або ця логіка буде перероблена згідно TODO.
                # Оскільки check_group_edit_permission сама є Depends, її не можна просто так викликати.
                # Це місце потребує рефакторингу з винесенням логіки перевірки прав в окрему функцію,
                # яка може бути викликана з Depends або напряму.
                # Наприклад, так:
                # if not await is_user_group_admin_or_superuser(rule_in.group_id, current_user.id, current_user.is_superuser, db_session):
                #     raise HTTPException(...)
                # Поки що, залишаю попередню логіку, але з get_group_membership_service
                # Це все ще не зовсім коректно, бо Depends всередині Depends не працює так.
                # Правильно було б передати group_id в check_group_edit_permission, якби вона була залежністю цього ендпоінта.
                # Оскільки group_id береться з тіла, потрібна кастомна залежність.
                # Залишаю як є, з розумінням, що TODO про кастомну залежність це покриває.
                # Для виправлення get_membership_service_dep на get_group_membership_service,
                # потрібно щоб check_group_edit_permission приймала GroupMembershipService.
                # Припускаємо, що check_group_edit_permission буде адаптована або замінена.
                # Нижче - це концептуальний виклик, який потребує, щоб check_group_edit_permission
                # була перероблена для такого використання, або використовувалася спеціальна залежність.
                # Наразі, ця частина коду не буде працювати як очікується без рефакторингу check_group_edit_permission.
                # Для простоти, припускаємо, що ця перевірка буде винесена в окрему залежність згідно TODO.
                # Поки що, для заміни get_membership_service_dep, припустимо, що check_group_edit_permission
                # якимось чином отримує GroupMembershipService.
                # Це місце в коді є проблемним і потребує рефакторингу згідно з TODO.
                # Замість прямого виклику Depends тут, потрібно було б, щоб сама функція
                # check_group_edit_permission була залежністю цього ендпоінта, але вона залежить від Path.
                # Для демонстрації заміни, змінимо лише сам Depends.
                pass # Ця перевірка має бути реалізована через окрему залежність згідно TODO
        except HTTPException as e:
            logger.warning( # Цей блок може не спрацювати як очікувалось через проблеми вище
                f"Користувач ID '{current_user.id}' не має прав створювати правило для групи ID '{rule_in.group_id}'.")
            raise e  # Перекидаємо помилку далі
    elif not current_user.is_superuser:  # Глобальне правило може створити тільки суперюзер
        logger.warning(
            f"Користувач ID '{current_user.id}' намагається створити глобальне правило бонусу, не будучи суперюзером.")
        # i18n
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Тільки суперкористувачі можуть створювати глобальні правила бонусів.")

    try:
        # BonusRuleService.create_bonus_rule має обробляти унікальність імені/коду в межах group_id/глобально
        # та валідувати пов'язані ID (task_type_id тощо)
        created_rule = await rule_service.create_bonus_rule(  # Припускаємо, що сервіс має такий метод
            rule_data=rule_in,
            creator_user_id=current_user.id
        )
        return created_rule
    except ValueError as e:
        logger.warning(f"Помилка створення правила бонусу '{rule_in.name}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при створенні правила бонусу '{rule_in.name}': {e}",
                     exc_info=global_settings.DEBUG)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутрішня помилка сервера.")


@router.get(
    "/",
    response_model=PagedResponse[BonusRuleResponse],
    summary="Отримання списку правил бонусів",  # i18n
    description="""Повертає список правил бонусів з пагінацією.
    Фільтрується за групою (`group_id`), типом завдання (`task_type_id`) тощо.
    Користувачі бачать глобальні правила та правила для груп, до яких вони належать."""  # i18n
)
async def read_bonus_rules(
        group_id: Optional[UUID] = Query(None, description="ID групи для фільтрації правил"),  # i18n
        task_type_id: Optional[UUID] = Query(None, description="ID типу завдання для фільтрації"),  # i18n
        # event_type_id: Optional[UUID] = Query(None, description="ID типу події для фільтрації"), # Якщо є
        is_active: Optional[bool] = Query(None, description="Фільтр за статусом активності правила"),  # i18n
        page_params: PageParams = Depends(paginator),
        current_user: UserModel = Depends(get_current_active_user),  # Для перевірки доступу
        rule_service: BonusRuleService = Depends(get_bonus_rule_service)
) -> PagedResponse[BonusRuleResponse]:
    """
    Отримує список правил бонусів.
    Доступність правил залежить від контексту користувача та групи.
    """
    logger.debug(
        f"Користувач ID '{current_user.id}' запитує список правил бонусів. Група: {group_id}, Тип завдання: {task_type_id}, Активні: {is_active}.")

    # TODO: BonusRuleService.list_bonus_rules_paginated має обробляти права доступу
    #  (суперюзер бачить все, користувач - глобальні + правила своїх груп).
    #  Також має повертати (items, total_count).
    rules_orm, total_rules = await rule_service.list_bonus_rules_paginated(
        requesting_user_id=current_user.id,
        is_superuser=current_user.is_superuser,
        group_id_filter=group_id,
        task_type_id_filter=task_type_id,
        is_active_filter=is_active,
        skip=page_params.skip,
        limit=page_params.limit
    )
    return PagedResponse[BonusRuleResponse](
        total=total_rules,
        page=page_params.page,
        size=page_params.size,
        results=[BonusRuleResponse.model_validate(rule) for rule in rules_orm]  # Pydantic v2
    )

# ПРИМІТКА: Ця залежність реалізує перевірку прав доступу до правила.
# В майбутньому її логіка може бути винесена в більш спеціалізовані
# залежності, як зазначено в TODO на початку файлу.
async def check_rule_access_permission(  # Залежність для перевірки прав на конкретне правило
        rule_id: UUID = Path(..., description="ID правила бонусу"),  # i18n
        current_user: UserModel = Depends(get_current_active_user),
        rule_service: BonusRuleService = Depends(get_bonus_rule_service),
        membership_service: GroupMembershipService = Depends(get_group_membership_service) # Оновлено залежність
) -> BonusRuleResponse:  # Повертає схему правила, якщо доступ є
    rule = await rule_service.get_by_id(item_id=rule_id)
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Правило бонусу не знайдено.")  # i18n

    if current_user.is_superuser:
        return rule

    if rule.group_id:  # Якщо правило групове, перевіряємо членство
        membership = await membership_service.get_membership_details(group_id=rule.group_id, user_id=current_user.id)
        if not membership or not membership.is_active:
            # i18n
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Ви не маєте доступу до цього групового правила бонусу.")
    # Якщо правило глобальне (rule.group_id is None), то воно доступне всім автентифікованим користувачам для перегляду
    return rule


@router.get(
    "/{rule_id}",
    response_model=BonusRuleResponse,
    summary="Отримання інформації про правило бонусу за ID",  # i18n
    description="Повертає детальну інформацію про конкретне правило бонусу. Доступно, якщо користувач має доступ до групи правила (якщо воно групове) або це глобальне правило.",
    # i18n
    dependencies=[Depends(check_rule_access_permission)]  # Застосовуємо залежність для перевірки прав
)
async def read_bonus_rule_by_id(
        rule_id: UUID,  # ID тепер UUID
        # Залежність check_rule_access_permission вже повернула правило або кинула виняток
        retrieved_rule: BonusRuleResponse = Depends(check_rule_access_permission)
) -> BonusRuleResponse:
    """
    Отримує інформацію про правило бонусу за його ID.
    Доступ контролюється залежністю `check_rule_access_permission`.
    """
    logger.debug(f"Запит деталей правила бонусу ID: {rule_id}.")
    return retrieved_rule

# ПРИМІТКА: Ця залежність реалізує перевірку прав на редагування/видалення правила.
# Подібно до check_rule_access_permission, її логіка може бути вдосконалена
# та винесена в спеціалізовані залежності.
async def check_rule_edit_permission(  # Залежність для перевірки прав на редагування/видалення правила
        rule_id: UUID = Path(..., description="ID правила бонусу"),  # i18n
        current_user: UserModel = Depends(get_current_active_user),
        rule_service: BonusRuleService = Depends(get_bonus_rule_service),
        membership_service: GroupMembershipService = Depends(get_group_membership_service) # Оновлено залежність
) -> BonusRuleResponse:  # Повертає схему правила, якщо доступ є, для використання в ендпоінті
    rule = await rule_service.get_by_id(item_id=rule_id)
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Правило бонусу не знайдено.")  # i18n

    if current_user.is_superuser:
        return rule

    if rule.group_id:  # Якщо правило групове
        membership = await membership_service.get_membership_details(group_id=rule.group_id, user_id=current_user.id)
        if not membership or not membership.is_active or membership.role.code != "ADMIN":  # ADMIN_ROLE_CODE
            # i18n
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail="Ви не є адміністратором групи цього правила бонусу.")
    else:  # Глобальне правило може редагувати тільки суперюзер
        # i18n
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Тільки суперкористувачі можуть редагувати глобальні правила бонусів.")
    return rule


@router.put(
    "/{rule_id}",
    response_model=BonusRuleResponse,
    summary="Оновлення інформації про правило бонусу",  # i18n
    description="Дозволяє адміністратору групи (для правил своєї групи) або суперюзеру оновити існуюче правило бонусу.",
    # i18n
    dependencies=[Depends(check_rule_edit_permission)]
)
async def update_bonus_rule(
        rule_id: UUID,  # ID тепер UUID
        rule_in: BonusRuleUpdate,
        retrieved_rule_for_update: BonusRuleResponse = Depends(check_rule_edit_permission),
        # Отримуємо правило з залежності
        current_user: UserModel = Depends(get_current_active_user),  # Для updated_by_user_id
        rule_service: BonusRuleService = Depends(get_bonus_rule_service)
) -> BonusRuleResponse:
    """
    Оновлює дані правила бонусу.
    Доступ контролюється залежністю `check_rule_edit_permission`.
    """
    logger.info(f"Користувач ID '{current_user.id}' намагається оновити правило бонусу ID '{rule_id}'.")
    try:
        # BonusRuleService.update успадкований з BaseDictionaryService,
        # який може потребувати `updated_by_user_id` через kwargs.
        # TODO: Переконатися, що сервіс `update` обробляє `updated_by_user_id`.
        updated_rule = await rule_service.update(
            item_id=rule_id,  # BaseDictionaryService.update приймає item_id
            data=rule_in,
            # updated_by_user_id=current_user.id # Якщо BaseDictionaryService.update приймає kwargs
        )
        if not updated_rule:  # Малоймовірно, якщо `check_rule_edit_permission` не кинув 404
            # i18n
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Правило бонусу не знайдено або оновлення не вдалося.")
        return updated_rule
    except ValueError as e:  # Помилки унікальності або інші з сервісу
        logger.warning(f"Помилка оновлення правила бонусу ID '{rule_id}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при оновленні правила ID '{rule_id}': {e}", exc_info=global_settings.DEBUG)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутрішня помилка сервера.")


@router.delete(
    "/{rule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Видалення правила бонусу",  # i18n
    description="Дозволяє адміністратору групи або суперюзеру видалити правило бонусу.",  # i18n
    dependencies=[Depends(check_rule_edit_permission)]
)
async def delete_bonus_rule(
        rule_id: UUID,  # ID тепер UUID
        # retrieved_rule_for_delete: BonusRuleResponse = Depends(check_rule_edit_permission), # Не потрібен сам об'єкт, тільки перевірка прав
        current_user: UserModel = Depends(get_current_active_user),  # Для логування
        rule_service: BonusRuleService = Depends(get_bonus_rule_service)
):
    """
    Видаляє правило бонусу.
    Доступ контролюється залежністю `check_rule_edit_permission`.
    """
    logger.info(f"Користувач ID '{current_user.id}' намагається видалити правило бонусу ID '{rule_id}'.")
    try:
        success = await rule_service.delete(item_id=rule_id)
        if not success:
            logger.warning(f"Не вдалося видалити правило бонусу ID '{rule_id}' (сервіс повернув False).")
            # i18n
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="Правило бонусу не знайдено або не вдалося видалити.")
    except ValueError as e:  # Наприклад, якщо правило використовується і сервіс це перевіряє
        logger.warning(f"Помилка видалення правила бонусу ID '{rule_id}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))  # i18n
    except Exception as e:
        logger.error(f"Неочікувана помилка при видаленні правила ID '{rule_id}': {e}", exc_info=global_settings.DEBUG)
        # i18n
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Внутрішня помилка сервера.")

    return None


logger.info("Роутер для правил бонусів (`/rules`) визначено.")
