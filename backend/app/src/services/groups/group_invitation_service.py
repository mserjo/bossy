# backend/app/src/services/groups/group_invitation_service.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає сервіс `GroupInvitationService` для управління запрошеннями до груп.
"""
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore

from backend.app.src.models.groups.invitation import GroupInvitationModel
from backend.app.src.models.auth.user import UserModel
from backend.app.src.schemas.groups.invitation import GroupInvitationCreateSchema, GroupInvitationUpdateSchema, GroupInvitationSchema
from backend.app.src.repositories.groups.invitation import GroupInvitationRepository, group_invitation_repository
from backend.app.src.repositories.groups.group import group_repository # Для перевірки групи
from backend.app.src.repositories.auth.user import user_repository # Для перевірки запрошеного користувача
from backend.app.src.repositories.dictionaries.user_role import user_role_repository # Для ролі
from backend.app.src.repositories.dictionaries.status import status_repository # Для статусу запрошення
from backend.app.src.services.base import BaseService
from backend.app.src.core.exceptions import NotFoundException, ForbiddenException, BadRequestException
from backend.app.src.core.constants import INVITATION_STATUS_PENDING_CODE, ROLE_USER_CODE # Дефолтні значення
# from backend.app.src.services.groups.group_membership_service import group_membership_service # Для перевірки прав та додавання члена

class GroupInvitationService(BaseService[GroupInvitationRepository]):
    """
    Сервіс для управління запрошеннями до груп.
    """

    def _generate_invitation_code(self) -> str:
        """Генерує унікальний код запрошення."""
        # TODO: Реалізувати більш надійний генератор коду, якщо потрібно (наприклад, короткий, читабельний).
        return str(uuid.uuid4()) # Поки що простий UUID

    async def create_invitation(
        self, db: AsyncSession, *,
        group_id: uuid.UUID,
        obj_in: GroupInvitationCreateSchema,
        current_user: UserModel
    ) -> GroupInvitationModel:
        """
        Створює нове запрошення до групи.
        """
        # Перевірка прав: лише адмін групи або superuser може створювати запрошення
        from backend.app.src.services.groups.group_membership_service import group_membership_service # Відкладений імпорт
        if not await group_membership_service.is_user_group_admin(db, user_id=current_user.id, group_id=group_id) and \
           current_user.user_type_code != USER_TYPE_SUPERADMIN:
            raise ForbiddenException("Лише адміністратор групи може створювати запрошення.")

        # Перевірка існування групи
        group = await group_repository.get(db, id=group_id)
        if not group:
            raise NotFoundException(f"Групу з ID {group_id} не знайдено.")

        # Перевірка існування ролі, що призначається
        role_to_assign = await user_role_repository.get(db, id=obj_in.role_to_assign_id)
        if not role_to_assign:
            raise BadRequestException(f"Роль з ID {obj_in.role_to_assign_id} не знайдено.")
        # TODO: Перевірка, чи можна призначати цю роль (наприклад, адмін не може призначити superadmin).

        # Перевірка запрошеного користувача (якщо вказано email або user_id)
        if obj_in.email_invited:
            invited_user_by_email = await user_repository.get_by_email(db, email=obj_in.email_invited)
            if invited_user_by_email and obj_in.user_id_invited and obj_in.user_id_invited != invited_user_by_email.id:
                raise BadRequestException("Вказаний email та user_id_invited належать різним користувачам.")
            if invited_user_by_email:
                obj_in.user_id_invited = invited_user_by_email.id # Встановлюємо ID, якщо знайдено по email
            # Якщо користувача з таким email немає, запрошення може бути створено (для нового користувача).

        if obj_in.user_id_invited:
            invited_user_by_id = await user_repository.get(db, id=obj_in.user_id_invited)
            if not invited_user_by_id:
                raise BadRequestException(f"Запрошений користувач з ID {obj_in.user_id_invited} не знайдений.")
            # Перевірка, чи запрошений користувач вже не є членом групи
            existing_membership = await group_membership_service.get_membership_by_user_and_group(db, user_id=obj_in.user_id_invited, group_id=group_id)
            if existing_membership:
                raise BadRequestException(f"Користувач {obj_in.user_id_invited} вже є членом групи {group_id}.")


        invitation_code = self._generate_invitation_code()

        # Встановлення статусу "pending"
        pending_status = await status_repository.get_by_code(db, code=INVITATION_STATUS_PENDING_CODE)
        if not pending_status:
            raise BadRequestException(f"Статус '{INVITATION_STATUS_PENDING_CODE}' не знайдено в довіднику.")

        create_data = obj_in.model_dump(exclude_unset=True)
        db_obj = self.repository.model(
            group_id=group_id,
            user_id_creator=current_user.id,
            invitation_code=invitation_code,
            status_id=pending_status.id,
            **create_data
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)

        # TODO: Відправити сповіщення/email запрошеному користувачеві (якщо email_invited).
        return db_obj

    async def get_invitation_by_code(self, db: AsyncSession, invitation_code: str) -> GroupInvitationModel:
        """Отримує запрошення за кодом."""
        invitation = await self.repository.get_by_invitation_code(db, invitation_code=invitation_code)
        if not invitation:
            raise NotFoundException("Запрошення не знайдено або недійсне.")

        # Перевірка, чи запрошення ще активне
        if not invitation.is_active:
            raise BadRequestException("Запрошення більше не активне.")
        if invitation.expires_at and invitation.expires_at < datetime.utcnow():
            raise BadRequestException("Термін дії запрошення закінчився.")
        if invitation.max_uses is not None and invitation.current_uses >= invitation.max_uses:
            raise BadRequestException("Ліміт використання цього запрошення вичерпано.")

        return invitation

    async def accept_invitation(
        self, db: AsyncSession, *, invitation_code: str, accepting_user: UserModel
    ) -> GroupMembershipModel:
        """
        Обробляє прийняття запрошення користувачем.
        Додає користувача до групи та оновлює статус запрошення.
        """
        from backend.app.src.services.groups.group_membership_service import group_membership_service # Відкладений імпорт

        invitation = await self.get_invitation_by_code(db, invitation_code=invitation_code) # Включає перевірки активності

        # Перевірка, чи запрошення було для конкретного користувача (і чи це той самий користувач)
        if invitation.user_id_invited and invitation.user_id_invited != accepting_user.id:
            raise ForbiddenException("Це запрошення призначене для іншого користувача.")
        if invitation.email_invited and invitation.email_invited.lower() != accepting_user.email.lower():
             raise ForbiddenException("Це запрошення призначене для іншого email.")

        # Перевірка, чи користувач вже не є членом групи
        existing_membership = await group_membership_service.get_membership_by_user_and_group(
            db, user_id=accepting_user.id, group_id=invitation.group_id
        )
        if existing_membership:
            raise BadRequestException(f"Ви вже є членом групи '{invitation.group.name}'.") # Потребує завантаження group

        # Додаємо користувача до групи
        new_membership = await group_membership_service.add_member_to_group(
            db,
            group_id=invitation.group_id,
            user_id_to_add=accepting_user.id,
            role_id=invitation.role_to_assign_id,
            current_user=accepting_user # Тут current_user - це той, хто приймає, права не потрібні для додавання себе
                                        # Але add_member_to_group має це врахувати.
                                        # Краще, щоб GroupMembershipService мав метод типу join_group_via_invitation
        )

        # Оновлюємо запрошення
        invitation.current_uses += 1
        accepted_status = await status_repository.get_by_code(db, code="invite_accepted") # Потрібна константа
        if accepted_status:
            invitation.status_id = accepted_status.id
        if invitation.max_uses is not None and invitation.current_uses >= invitation.max_uses:
            invitation.is_active = False

        db.add(invitation)
        await db.commit()
        await db.refresh(invitation)

        return new_membership


    async def revoke_invitation(
        self, db: AsyncSession, *, invitation_id: uuid.UUID, current_user: UserModel
    ) -> GroupInvitationModel:
        """Відкликає запрошення (робить неактивним)."""
        invitation = await self.repository.get(db, id=invitation_id)
        if not invitation:
            raise NotFoundException("Запрошення не знайдено.")

        # Перевірка прав: адмін групи або той, хто створив запрошення
        from backend.app.src.services.groups.group_membership_service import group_membership_service
        if not (current_user.user_type_code == USER_TYPE_SUPERADMIN or \
                invitation.user_id_creator == current_user.id or \
                await group_membership_service.is_user_group_admin(db, user_id=current_user.id, group_id=invitation.group_id)):
            raise ForbiddenException("Ви не маєте прав відкликати це запрошення.")

        invitation.is_active = False
        cancelled_status = await status_repository.get_by_code(db, code="invite_cancelled") # Потрібна константа
        if cancelled_status:
            invitation.status_id = cancelled_status.id

        db.add(invitation)
        await db.commit()
        await db.refresh(invitation)
        return invitation

group_invitation_service = GroupInvitationService(group_invitation_repository)

# TODO: Додати константи для статусів запрошень (INVITATION_STATUS_ACCEPTED_CODE, INVITATION_STATUS_CANCELLED_CODE).
# TODO: В `accept_invitation` логіка додавання користувача до групи через `group_membership_service.add_member_to_group`
#       може потребувати уваги до перевірки прав всередині `add_member_to_group`. Можливо, потрібен окремий метод
#       в `GroupMembershipService` для приєднання за запрошенням, який не перевіряє адмінські права `accepting_user`.
#       Або `add_member_to_group` має параметр `added_by_system=True`.
#
# Все виглядає як хороший початок. Основні сценарії створення, отримання та прийняття/відкликання запрошень.
# Генерація коду, перевірка лімітів та терміну дії.
