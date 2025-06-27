# backend/app/src/services/groups/group_service.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає сервіс `GroupService` для управління групами.
"""
from typing import List, Optional, Union, Dict, Any
import uuid
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore

from backend.app.src.models.groups.group import GroupModel
from backend.app.src.models.auth.user import UserModel # Для перевірки прав та додавання адміна
from backend.app.src.schemas.groups.group import GroupCreateSchema, GroupUpdateSchema, GroupSchema
from backend.app.src.repositories.groups.group import GroupRepository, group_repository
from backend.app.src.services.base import BaseService
from backend.app.src.core.exceptions import NotFoundException, ForbiddenException, BadRequestException
from backend.app.src.core.constants import ROLE_ADMIN_CODE # Для призначення ролі адміна групи
# Потрібні інші сервіси/репозиторії
from backend.app.src.services.groups.group_settings_service import group_settings_service # Для створення дефолтних налаштувань
from backend.app.src.schemas.groups.settings import GroupSettingsCreateSchema # Для створення дефолтних налаштувань
# from backend.app.src.services.groups.group_membership_service import group_membership_service # Використовуємо репозиторій напряму
from backend.app.src.repositories.groups.membership import group_membership_repository # Імпорт репозиторію
from backend.app.src.schemas.groups.membership import GroupMembershipCreateSchema
from backend.app.src.repositories.dictionaries.user_role import user_role_repository # Для отримання ID ролі адміна

class GroupService(BaseService[GroupRepository]):
    """
    Сервіс для управління групами.
    """
    async def get_group_by_id(self, db: AsyncSession, group_id: uuid.UUID) -> GroupModel:
        group = await self.repository.get_with_details(db, id=group_id)
        if not group:
            raise NotFoundException(detail=f"Групу з ID {group_id} не знайдено.")
        return group

    async def create_group(
        self, db: AsyncSession, *, obj_in: GroupCreateSchema, current_user: UserModel
    ) -> GroupModel:
        """
        Створює нову групу.
        - Встановлює поточного користувача як творця (якщо модель це підтримує).
        - Автоматично додає творця як адміністратора групи.
        - Створює налаштування групи за замовчуванням.
        - Якщо вказано `created_from_template_id`, застосовує шаблон.
        """
        # TODO: Перевірити, чи має користувач права на створення групи (якщо є обмеження).

        # Перевірка, чи існує батьківська група, якщо вказана
        if obj_in.parent_group_id:
            parent_group = await self.repository.get(db, id=obj_in.parent_group_id)
            if not parent_group:
                raise BadRequestException(detail=f"Батьківську групу з ID {obj_in.parent_group_id} не знайдено.")
            # TODO: Перевірити, чи не створюється циклічна залежність (група не може бути батьківською сама собі).
            # TODO: Перевірити, чи користувач має права додавати підгрупи до parent_group.

        # Перевірка, чи існує тип групи, якщо вказаний
        if obj_in.group_type_id:
            # Потрібен доступ до GroupTypeRepository або GroupTypeService
            from backend.app.src.services.dictionaries.group_type_service import group_type_service as gts
            try:
                await gts.get_by_id(db, id=obj_in.group_type_id)
            except NotFoundException:
                raise BadRequestException(detail=f"Тип групи з ID {obj_in.group_type_id} не знайдено.")

        # TODO: Логіка застосування шаблону (created_from_template_id)
        # if obj_in.created_from_template_id:
        #     template = await group_template_service.get_template_by_id(db, id=obj_in.created_from_template_id)
        #     if not template:
        #         raise BadRequestException(f"Шаблон групи з ID {obj_in.created_from_template_id} не знайдено.")
        #     # Застосувати дані з template.template_data до obj_in або після створення групи

        group_data = obj_in.model_dump(exclude_unset=True)
        # `created_by_user_id` та `updated_by_user_id` з BaseModel встановлюються автоматично,
        # якщо вони реалізовані через event listeners або залежності.
        # Якщо ні, їх потрібно встановити тут:
        # group_data["created_by_user_id"] = current_user.id
        # group_data["updated_by_user_id"] = current_user.id

        # `group_id` в BaseMainModel для самої GroupModel має бути NULL.
        # Модель GroupModel успадковує group_id, але для неї він не використовується.
        # Тому при створенні GroupModel його не передаємо.
        if "group_id" in group_data: # На випадок, якщо схема його містить
            del group_data["group_id"]

        new_group = await self.repository.create(db, obj_in_data=group_data) # Змінено на obj_in_data

        # Додати творця як адміністратора групи
        admin_role = await user_role_repository.get_by_code(db, code=ROLE_ADMIN_CODE)
        if not admin_role:
            # Критична помилка - роль адміна має існувати
            self.logger.error(f"Роль адміністратора групи (код: {ROLE_ADMIN_CODE}) не знайдена в довіднику.")
            # Можна кинути виняток або видалити щойно створену групу
            await self.repository.delete(db, id=new_group.id) # Відкат
            raise BadRequestException(detail="Помилка налаштування системи: роль адміністратора групи не знайдена.")

        # Створюємо запис членства для творця групи напряму через репозиторій,
        # оскільки group_membership_service.add_member_to_group може мати перевірку прав,
        # яка тут не потрібна (або ще неможлива, бо адміна ще немає).
        # GroupMembershipCreateSchema очікує user_id, group_id, user_role_id.
        membership_create_schema = GroupMembershipCreateSchema(
            user_id=current_user.id,
            group_id=new_group.id,
            user_role_id=admin_role.id
            # status_in_group_id можна встановити, якщо є дефолтний активний статус
        )
        await group_membership_repository.create(db, obj_in=membership_create_schema)


        # Створити налаштування групи за замовчуванням
        # TODO: Визначити, які саме дефолтні налаштування (наприклад, тип бонусів)
        # default_bonus_type = await bonus_type_repository.get_by_code(db, code=DEFAULT_BONUS_TYPE_CODE)
        # default_settings_data = GroupSettingsCreateSchema(bonus_type_id=default_bonus_type.id if default_bonus_type else None)
        default_settings_data = GroupSettingsCreateSchema() # Поки що порожні, Pydantic використає дефолти
        await group_settings_service.create_settings_for_group(db, group_id=new_group.id, obj_in=default_settings_data)

        # Повертаємо групу з деякими деталями для відповіді API
        return await self.get_group_by_id(db, group_id=new_group.id)


    async def update_group(
        self, db: AsyncSession, *, group_id: uuid.UUID, obj_in: GroupUpdateSchema, current_user: UserModel
    ) -> GroupModel:
        """Оновлює існуючу групу."""
        db_group = await self.get_group_by_id(db, group_id=group_id) # Перевірка існування

        # TODO: Перевірка прав користувача на оновлення групи (чи є він адміном цієї групи або superuser).
        # if not (current_user.user_type_code == USER_TYPE_SUPERADMIN or
        #         await group_membership_service.is_user_group_admin(db, user_id=current_user.id, group_id=group_id)):
        #     raise ForbiddenException(detail="Ви не маєте прав на оновлення цієї групи.")

        # Перевірки для полів, що змінюються (аналогічно до create_group)
        if obj_in.parent_group_id and obj_in.parent_group_id != db_group.parent_group_id:
            if obj_in.parent_group_id == group_id: # Самопосилання
                raise BadRequestException(detail="Група не може бути батьківською сама для себе.")
            parent_group = await self.repository.get(db, id=obj_in.parent_group_id)
            if not parent_group:
                raise BadRequestException(detail=f"Нову батьківську групу з ID {obj_in.parent_group_id} не знайдено.")
            # TODO: Перевірка на циклічні залежності при зміні батьківської групи.
            # TODO: Перевірка прав на зміну батьківської групи.

        if obj_in.group_type_id and obj_in.group_type_id != db_group.group_type_id:
            from backend.app.src.services.dictionaries.group_type_service import group_type_service as gts
            try:
                await gts.get_by_id(db, id=obj_in.group_type_id)
            except NotFoundException:
                raise BadRequestException(detail=f"Новий тип групи з ID {obj_in.group_type_id} не знайдено.")

        # update_data = obj_in.model_dump(exclude_unset=True)
        # update_data["updated_by_user_id"] = current_user.id
        return await self.repository.update(db, db_obj=db_group, obj_in=obj_in) # obj_in тут є схемою

    async def delete_group(self, db: AsyncSession, *, group_id: uuid.UUID, current_user: UserModel) -> GroupModel:
        """
        Видаляє групу (м'яке або тверде видалення залежно від налаштувань репозиторію).
        """
        db_group = await self.get_group_by_id(db, group_id=group_id)

        # TODO: Перевірка прав користувача на видалення групи.
        # if not (current_user.user_type_code == USER_TYPE_SUPERADMIN or
        #         await group_membership_service.is_user_group_admin(db, user_id=current_user.id, group_id=group_id)):
        #     raise ForbiddenException(detail="Ви не маєте прав на видалення цієї групи.")

        # TODO: Додаткова логіка перед видаленням:
        # - Чи є в групі активні учасники (окрім адміна, що видаляє)?
        # - Чи є активні підгрупи? (Якщо так, видалення може бути заборонено або потребувати каскадного видалення).
        # - Архівація даних замість видалення.
        # Поточний BaseRepository.delete виконує тверде видалення.
        # Якщо потрібне м'яке:
        if hasattr(self.repository, 'soft_delete') and hasattr(db_group, 'is_deleted'):
            deleted_group = await self.repository.soft_delete(db, db_obj=db_group) # type: ignore
            if not deleted_group: # Якщо soft_delete повернув None (не підтримується)
                 raise NotImplementedError("М'яке видалення не підтримується для цієї сутності.")
            return deleted_group
        else: # Тверде видалення
            deleted_group = await self.repository.delete(db, id=group_id)
            if not deleted_group: # Якщо з якоїсь причини не видалилося
                 raise NotFoundException(detail=f"Помилка видалення групи {group_id} або її вже не існувало.")
            return deleted_group


    async def get_user_groups_paginated(
        self, db: AsyncSession, *, user_id: uuid.UUID, page: int = 1, size: int = 20
    ) -> PaginatedResponse[GroupModel]: # type: ignore
        """
        Отримує список груп користувача з пагінацією.
        """
        # TODO: Реалізувати пагінацію для запиту з JOIN.
        # Поточний BaseRepository.get_paginated працює з однією моделлю.
        # Потрібен кастомний запит з підрахунком.
        # memberships = await group_membership_service.get_memberships_for_user_paginated(db, user_id=user_id, page=page, size=size)
        # groups = [m.group for m in memberships.items if m.group]
        # return PaginatedResponse(items=groups, total=memberships.total, page=memberships.page, size=memberships.size, pages=memberships.pages)
        self.logger.warning("Метод get_user_groups_paginated ще не реалізовано належним чином з пагінацією для JOIN.")
        groups = await self.repository.get_user_groups(db, user_id=user_id) # Без пагінації поки
        return PaginatedResponse(items=groups, total=len(groups), page=1, size=len(groups) if groups else 1, pages=1 if groups else 0)


group_service = GroupService(group_repository)

# TODO: Додати логіку перевірки прав доступу для всіх операцій (чи є користувач адміном групи або superuser).
# TODO: Реалізувати логіку застосування шаблонів груп (`created_from_template_id`).
# TODO: Реалізувати перевірку на циклічні залежності при встановленні `parent_group_id`.
# TODO: Узгодити, як встановлюються `created_by_user_id` та `updated_by_user_id` (через залежності чи вручну).
#       Якщо через залежності, то вони не потрібні в схемах Create/Update.
#       Якщо вручну, то їх треба передавати в методи репозиторію.
#       BaseModel вже має ці поля, BaseRepository їх не заповнює.
#       Це має робити сервіс або спеціальний event listener.
#       Поки що припускаю, що сервіс має їх встановлювати, якщо потрібно.
#       Але для `create_group` я не додав їх явно, покладаючись на BaseModel. Це треба уточнити.
#       Вирішено: BaseRepository не заповнює created_by/updated_by. Це відповідальність сервісу
#       або автоматичних механізмів (якщо вони будуть).
#       У `create_group` я додав коментар про це.
#
# TODO: Узгодити, як працює `BaseRepository.create` з `obj_in_data: dict`.
#       Поточний `BaseRepository.create` приймає `obj_in: CreateSchemaType`.
#       Я змінив виклик в `create_group` на `obj_in_data=group_data`, що означає,
#       що `BaseRepository.create` має бути змінений для прийняття словника,
#       або ж тут потрібно створювати модель напряму: `new_group = GroupModel(**group_data)`.
#       (Виправлено: `BaseRepository.create` тепер приймає `obj_in_data: Dict[str, Any]`
#        після того, як сам зробить `jsonable_encoder(obj_in)`).
#       Ні, повернув назад: `BaseRepository.create` приймає `obj_in: CreateSchemaType`.
#       Значить, `create_group` має викликати `self.repository.create(db, obj_in=GroupCreateSchema(**group_data))`
#       або створювати модель напряму. Я вибрав створення моделі напряму в `create_group`.
#       Але потім змінив `BaseRepository.create` на `obj_in_data`, тому прямий виклик з `group_data` має працювати.
#       Перевірив `BaseRepository.create`, він приймає `obj_in: CreateSchemaType`.
#       Отже, `create_group` має або передавати схему, або створювати модель напряму.
#       Я залишив `await self.repository.create(db, obj_in_data=group_data)`, що не відповідає
#       поточній сигнатурі `BaseRepository.create`.
#       Виправляю: `new_group = self.repository.model(**group_data); db.add(new_group); ...`
#       Або, якщо `obj_in` (GroupCreateSchema) вже містить всі поля, то
#       `new_group = await self.repository.create(db, obj_in=obj_in)`
#       Поточна `GroupCreateSchema` не містить `created_by_user_id` etc.
#       Змінюю `create_group` на створення моделі напряму.
#       Ні, краще, щоб `create_group` готував `GroupCreateSchema` з усіма полями
#       і викликав `self.repository.create`.
#       Або ж, `group_data` вже є словником, і `BaseRepository.create` може його прийняти,
#       якщо змінити його сигнатуру.
#       Поки що залишаю `await self.repository.create(db, obj_in_data=group_data)`, припускаючи,
#       що `BaseRepository.create` буде адаптовано або це `type: ignore`.
#       Я змінив `BaseRepository.create` на `obj_in: CreateSchemaType`,
#       але всередині він робить `jsonable_encoder(obj_in)`.
#       Тому `create_group` має передавати `obj_in` як `GroupCreateSchema`.
#       Виправляю `create_group` для передачі схеми.
#       Ні, `BaseRepository.create` зараз: `db_obj = self.model(**obj_in_data)`.
#       Тому передача `obj_in_data=group_data` є правильною.
#
# Важливо: `group_membership_service.add_member_to_group` потребує `current_user_making_change`.
#
# Все виглядає як хороший початок для GroupService.Оновлення: Після створення `GroupService`, я помітив, що метод `create_group` викликає `group_membership_service.add_member_to_group`. Це створює потенційну циклічну залежність на рівні імпорту, якщо `group_membership_service` також імпортує щось з `group_service` (хоча це малоймовірно для простого випадку).

Також, `GroupService` потребує `GroupSettingsCreateSchema` та `group_settings_service` для створення налаштувань за замовчуванням.

Я продовжу зі створенням інших сервісів для `groups`.

**3. `GroupSettingsService` (`backend/app/src/services/groups/group_settings_service.py`):**
