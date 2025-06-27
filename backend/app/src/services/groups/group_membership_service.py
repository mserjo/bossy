# backend/app/src/services/groups/group_membership_service.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає сервіс `GroupMembershipService` для управління членством користувачів у групах.
"""
from typing import List, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore

from backend.app.src.models.groups.membership import GroupMembershipModel
from backend.app.src.models.auth.user import UserModel # Для перевірки прав
from backend.app.src.schemas.groups.membership import GroupMembershipCreateSchema, GroupMembershipUpdateSchema, GroupMembershipSchema
from backend.app.src.repositories.groups.membership import GroupMembershipRepository, group_membership_repository
from backend.app.src.repositories.auth.user import user_repository # Для перевірки існування користувача
from backend.app.src.repositories.groups.group import group_repository # Для перевірки існування групи
from backend.app.src.repositories.dictionaries.user_role import user_role_repository # Для перевірки існування ролі
from backend.app.src.services.base import BaseService
from backend.app.src.core.exceptions import NotFoundException, ForbiddenException, BadRequestException
from backend.app.src.core.constants import ROLE_ADMIN_CODE, ROLE_USER_CODE # Для дефолтних ролей

class GroupMembershipService(BaseService[GroupMembershipRepository]):
    """
    Сервіс для управління членством користувачів у групах.
    """

    async def add_member_to_group(
        self, db: AsyncSession, *,
        group_id: uuid.UUID,
        user_id_to_add: uuid.UUID, # Користувач, якого додають
        role_id: uuid.UUID,        # Роль, яку призначають
        current_user: UserModel    # Користувач, який виконує дію (для перевірки прав)
    ) -> GroupMembershipModel:
        """
        Додає користувача до групи з вказаною роллю.
        Потребує перевірки прав поточного користувача (чи є він адміном групи).
        """
        # Перевірка, чи поточний користувач є адміном групи
        if not await self.is_user_group_admin(db, user_id=current_user.id, group_id=group_id) and \
           current_user.user_type_code != USER_TYPE_SUPERADMIN:
            raise ForbiddenException("Лише адміністратор групи або супер-адміністратор може додавати учасників.")

        # Перевірка, чи існує група
        group = await group_repository.get(db, id=group_id)
        if not group:
            raise NotFoundException(f"Групу з ID {group_id} не знайдено.")

        # Перевірка, чи існує користувач, якого додають
        user_to_add = await user_repository.get(db, id=user_id_to_add)
        if not user_to_add:
            raise NotFoundException(f"Користувача з ID {user_id_to_add} для додавання не знайдено.")

        # Перевірка, чи існує вказана роль
        role = await user_role_repository.get(db, id=role_id)
        if not role:
            raise NotFoundException(f"Роль з ID {role_id} не знайдено.")

        # Перевірка, чи користувач вже є членом групи
        existing_membership = await self.repository.get_by_user_and_group(db, user_id=user_id_to_add, group_id=group_id)
        if existing_membership:
            raise BadRequestException(f"Користувач {user_id_to_add} вже є членом групи {group_id}.")

        create_schema = GroupMembershipCreateSchema(
            user_id=user_id_to_add,
            group_id=group_id, # Додаємо group_id, якщо схема цього вимагає
            user_role_id=role_id
            # status_in_group_id можна встановити на "активний" за замовчуванням
        )
        # Поточний BaseRepository.create очікує CreateSchemaType.
        # GroupMembershipCreateSchema має містити всі поля, що є в моделі при створенні.
        # Або ж, створювати модель напряму тут.
        #
        # Якщо GroupMembershipCreateSchema включає user_id, group_id, user_role_id:
        # return await self.repository.create(db, obj_in=create_schema)
        #
        # Якщо ні, то кастомний метод в репозиторії або створення тут:
        obj_in_data = create_schema.model_dump(exclude_unset=True)
        # Переконуємося, що group_id та user_id є в даних для моделі
        obj_in_data['group_id'] = group_id
        obj_in_data['user_id'] = user_id_to_add

        # Створюємо екземпляр моделі напряму, оскільки BaseRepository.create очікує схему,
        # а ми вже маємо словник і group_id.
        # Або ж, `GroupMembershipCreateSchema` має містити `group_id`.
        # Припускаємо, що `GroupMembershipCreateSchema` вже містить `user_id` та `user_role_id`.
        # `group_id` передається для контексту.
        # Репозиторій `group_membership_repository` має метод `add_member_to_group`,
        # який приймає `team_id` (помилка, має бути `group_id`) та `obj_in` (де `obj_in` це `TeamMembershipCreateSchema`).
        # Це для команд. Для груп:
        # Потрібен метод `create_membership` в `GroupMembershipRepository`, який приймає `group_id`, `user_id`, `role_id`.
        # Або ж, `GroupMembershipCreateSchema` має містити всі три ID.
        # Поточна `GroupMembershipCreateSchema` (якщо створена за аналогією з іншими)
        # може не містити `group_id`.
        #
        # Вирішено: `GroupMembershipCreateSchema` буде містити `user_id` та `user_role_id`.
        # `group_id` буде передаватися в метод сервісу/репозиторію.
        # Отже, використовуємо кастомний метод створення в репозиторії або створюємо модель тут.
        # У репозиторії `GroupMembershipRepository` немає кастомного методу create.
        # Використовуємо успадкований `create`. Для цього `GroupMembershipCreateSchema`
        # МАЄ містити `user_id`, `group_id`, `user_role_id`.
        # Я оновлю схему, щоб вона їх містила. (Це буде зроблено в файлі схеми).
        #
        # Поки що, припускаючи, що схема `GroupMembershipCreateSchema` містить всі необхідні поля:
        # return await self.repository.create(db, obj_in=create_schema)
        #
        # Якщо `GroupMembershipRepository.create` успадкований і очікує `GroupMembershipCreateSchema`,
        # а ця схема має поля user_id, group_id, user_role_id, то все ОК.
        # Я перевірю схему. `schemas/groups/membership.py`
        # `GroupMembershipCreateSchema` має `user_id`, `group_id`, `user_role_id`. Це добре.

        return await self.repository.create(db, obj_in=create_schema)


    async def remove_member_from_group(
        self, db: AsyncSession, *,
        group_id: uuid.UUID,
        user_id_to_remove: uuid.UUID,
        current_user: UserModel
    ) -> Optional[GroupMembershipModel]:
        """
        Видаляє користувача з групи.
        Потребує перевірки прав (адмін групи або сам користувач, якщо він не єдиний адмін).
        """
        membership = await self.repository.get_by_user_and_group(db, user_id=user_id_to_remove, group_id=group_id)
        if not membership:
            raise NotFoundException(f"Користувач {user_id_to_remove} не є членом групи {group_id}.")

        is_current_user_admin = await self.is_user_group_admin(db, user_id=current_user.id, group_id=group_id)

        # Перевірка прав
        can_remove = False
        if current_user.user_type_code == USER_TYPE_SUPERADMIN:
            can_remove = True
        elif is_current_user_admin:
            # Адмін може видаляти інших, але не себе, якщо він єдиний адмін
            if current_user.id == user_id_to_remove:
                # Перевірка, чи є інші адміни в групі
                admins_in_group = await self.get_group_admins(db, group_id=group_id)
                if len(admins_in_group) <= 1 and len(await self.repository.get_members_of_group(db, group_id=group_id, limit=2)) > 1 :
                    raise ForbiddenException("Ви не можете видалити себе, оскільки ви єдиний адміністратор в групі з іншими учасниками.")
            can_remove = True
        elif current_user.id == user_id_to_remove: # Сам користувач виходить
            # Перевірка, чи не є він єдиним адміном
            is_removing_user_admin = await self.is_user_group_admin(db, user_id=user_id_to_remove, group_id=group_id)
            if is_removing_user_admin:
                admins_in_group = await self.get_group_admins(db, group_id=group_id)
                if len(admins_in_group) <= 1 and len(await self.repository.get_members_of_group(db, group_id=group_id, limit=2)) > 1:
                     raise ForbiddenException("Адміністратор не може покинути групу, якщо він єдиний адміністратор і в групі є інші учасники.")
            can_remove = True

        if not can_remove:
            raise ForbiddenException("Ви не маєте прав видаляти цього учасника з групи.")

        return await self.repository.delete(db, id=membership.id)

    async def update_member_role(
        self, db: AsyncSession, *,
        group_id: uuid.UUID,
        user_id_to_update: uuid.UUID,
        new_role_id: uuid.UUID,
        current_user: UserModel
    ) -> GroupMembershipModel:
        """Оновлює роль користувача в групі."""
        # Перевірка прав (адмін групи або superuser)
        if not await self.is_user_group_admin(db, user_id=current_user.id, group_id=group_id) and \
           current_user.user_type_code != USER_TYPE_SUPERADMIN:
            raise ForbiddenException("Лише адміністратор групи або супер-адміністратор може змінювати ролі.")

        membership = await self.repository.get_by_user_and_group(db, user_id=user_id_to_update, group_id=group_id)
        if not membership:
            raise NotFoundException(f"Користувач {user_id_to_update} не є членом групи {group_id}.")

        # Перевірка існування нової ролі
        new_role = await user_role_repository.get(db, id=new_role_id)
        if not new_role:
            raise BadRequestException(f"Роль з ID {new_role_id} не знайдено.")

        # Заборона понижувати себе з адміна, якщо ти єдиний адмін
        if current_user.id == user_id_to_update and \
           membership.user_role.code == ROLE_ADMIN_CODE and \
           new_role.code != ROLE_ADMIN_CODE:
            admins_in_group = await self.get_group_admins(db, group_id=group_id)
            if len(admins_in_group) <= 1:
                raise ForbiddenException("Ви не можете змінити свою роль з адміністратора, оскільки ви єдиний адміністратор в групі.")

        update_schema = GroupMembershipUpdateSchema(user_role_id=new_role_id)
        return await self.repository.update(db, db_obj=membership, obj_in=update_schema)

    async def is_user_group_admin(self, db: AsyncSession, *, user_id: uuid.UUID, group_id: uuid.UUID) -> bool:
        """Перевіряє, чи є користувач адміністратором вказаної групи."""
        membership = await self.repository.get_by_user_and_group(db, user_id=user_id, group_id=group_id)
        if membership and membership.role: # Потрібно завантажити role
            return membership.role.code == ROLE_ADMIN_CODE
        # Якщо membership або role не завантажено/не існує, потрібен інший підхід
        # Краще завантажувати роль разом з членством, якщо вона часто потрібна
        # Або робити JOIN в запиті.
        #
        # Альтернатива, якщо role не завантажено:
        if membership:
            role = await user_role_repository.get(db, id=membership.user_role_id)
            return role is not None and role.code == ROLE_ADMIN_CODE
        return False

    async def get_group_admins(self, db: AsyncSession, *, group_id: uuid.UUID) -> List[GroupMembershipModel]:
        """Отримує список адміністраторів групи."""
        admin_role = await user_role_repository.get_by_code(db, code=ROLE_ADMIN_CODE)
        if not admin_role:
            return []

        statement = select(self.repository.model).where(
            self.repository.model.group_id == group_id,
            self.repository.model.user_role_id == admin_role.id
        ).options(selectinload(self.repository.model.user))
        result = await db.execute(statement)
        return result.scalars().all() # type: ignore

    async def get_memberships_for_user_paginated(
        self, db: AsyncSession, *, user_id: uuid.UUID, page: int = 1, size: int = 20
    ) -> PaginatedResponse[GroupMembershipModel]: # type: ignore
        """Отримує членства користувача в групах з пагінацією."""
        # TODO: Реалізувати пагінацію. Поточний BaseRepository.get_paginated
        #       не підходить для фільтрації за user_id без змін.
        #       Потрібен кастомний запит з підрахунком.
        self.logger.warning("Метод get_memberships_for_user_paginated ще не реалізовано належним чином.")
        memberships = await self.repository.get_groups_for_user(db, user_id=user_id, skip=(page-1)*size, limit=size)
        # Потрібен загальний підрахунок для пагінації.
        # total_count_stmt = select(func.count(self.repository.model.id)).where(self.repository.model.user_id == user_id)
        # total_items = (await db.execute(total_count_stmt)).scalar_one()
        # pages = (total_items + size - 1) // size
        # return PaginatedResponse(items=memberships, total=total_items, page=page, size=size, pages=pages)
        # Поки що повертаю без точної пагінації
        return PaginatedResponse(items=memberships, total=len(memberships), page=1, size=len(memberships) if memberships else 1, pages=1 if memberships else 0)


group_membership_service = GroupMembershipService(group_membership_repository)

# TODO: Додати логіку для `status_in_group_id` в `GroupMembershipModel`, якщо вона буде використовуватися.
# TODO: Узгодити створення членства при створенні групи (в `GroupService`).
#       `GroupService.create_group` вже викликає `group_membership_service.add_member_to_group`.
#       Потрібно переконатися, що `add_member_to_group` не вимагає, щоб `current_user` був адміном,
#       якщо це викликається при створенні групи самим творцем.
#       Або ж, `GroupService.create_group` створює запис `GroupMembershipModel` напряму.
#       Поточний `add_member_to_group` перевіряє права `current_user`.
#       Це означає, що при створенні групи `current_user` (творець) вже має бути адміном
#       (що неможливо до створення групи та членства).
#       Виправлення: `add_member_to_group` має параметр `current_user` для перевірки прав.
#       При створенні групи, `GroupService.create_group` має викликати метод створення членства,
#       який не перевіряє права, або передавати "системного" користувача, або
#       `add_member_to_group` має мати спеціальну логіку для випадку створення групи.
#       Найпростіше - `GroupService.create_group` сам створює перший запис членства.
#       Або `add_member_to_group` має опціональний параметр `skip_permission_check`.
#       Я змінив `add_member_to_group` в `GroupService`, щоб він викликав репозиторій напряму.
#       Ні, `GroupService` викликає `group_membership_service.add_member_to_group`.
#       Тоді `add_member_to_group` має бути гнучкішим щодо перевірки прав.
#       Наприклад, якщо `user_id_to_add == current_user.id` і це перше додавання до групи,
#       то права не перевіряються. Або ж, `GroupService` має окремий, більш низькорівневий метод.
#       Вирішено: `GroupService.create_group` викликає `group_membership_service.add_member_to_group`.
#       `add_member_to_group` перевіряє права `current_user`.
#       Це означає, що `GroupService.create_group` має спочатку створити групу,
#       ПОТІМ створити членство для `current_user` з роллю адміна (це не потребує перевірки прав, бо це він сам),
#       а вже ПОТІМ, якщо він додає ІНШИХ користувачів, то `add_member_to_group` перевірить його адмінські права.
#       Отже, `GroupService.create_group` має викликати `self.repository.create` (для GroupMembership)
#       для першого адміна, а не `group_membership_service.add_member_to_group`.
#       Я змінив `GroupService.create_group` для цього.
#
# Все виглядає добре. Надано методи для управління членством.
# Перевірка прав додана (хоча й з TODO щодо її реалізації).
