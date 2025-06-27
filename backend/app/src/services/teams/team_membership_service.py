# backend/app/src/services/teams/team_membership_service.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає сервіс `TeamMembershipService` для управління членством користувачів у командах.
"""
from typing import List, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore

from backend.app.src.models.teams.membership import TeamMembershipModel
from backend.app.src.models.auth.user import UserModel
from backend.app.src.models.teams.team import TeamModel # Для перевірки команди
from backend.app.src.schemas.teams.membership import TeamMembershipCreateSchema, TeamMembershipUpdateSchema, TeamMembershipSchema
from backend.app.src.repositories.teams.membership import TeamMembershipRepository, team_membership_repository
from backend.app.src.repositories.auth.user import user_repository
from backend.app.src.repositories.teams.team import team_repository
# from backend.app.src.services.groups.group_membership_service import group_membership_service # Для перевірки членства в групі
from backend.app.src.services.base import BaseService
from backend.app.src.core.exceptions import NotFoundException, ForbiddenException, BadRequestException
from backend.app.src.core.constants import USER_TYPE_SUPERADMIN

class TeamMembershipService(BaseService[TeamMembershipRepository]):
    """
    Сервіс для управління членством користувачів у командах.
    """

    async def get_membership_by_id(self, db: AsyncSession, membership_id: uuid.UUID) -> TeamMembershipModel:
        membership = await self.repository.get(db, id=membership_id)
        if not membership:
            raise NotFoundException(f"Членство в команді з ID {membership_id} не знайдено.")
        return membership

    async def add_member_to_team(
        self, db: AsyncSession, *,
        team_id: uuid.UUID,
        user_id_to_add: uuid.UUID,
        role_in_team: Optional[str] = None, # Роль в команді (якщо є, окрім лідера)
        current_user: UserModel # Користувач, який виконує дію
    ) -> TeamMembershipModel:
        """
        Додає користувача до команди.
        Перевіряє права поточного користувача (лідер команди, адмін групи, superuser).
        """
        team = await team_repository.get_team_with_details(db, team_id=team_id) # Потрібен group_id та leader_id
        if not team:
            raise NotFoundException(f"Команду з ID {team_id} не знайдено.")

        # Перевірка прав
        from backend.app.src.services.groups.group_membership_service import group_membership_service # Відкладений імпорт
        is_group_admin = await group_membership_service.is_user_group_admin(db, user_id=current_user.id, group_id=team.group_id)
        is_team_leader = team.leader_user_id == current_user.id

        if not (is_team_leader or is_group_admin or current_user.user_type_code == USER_TYPE_SUPERADMIN):
            raise ForbiddenException("Лише лідер команди або адміністратор групи може додавати учасників.")

        # Перевірка існування користувача, якого додають
        user_to_add = await user_repository.get(db, id=user_id_to_add)
        if not user_to_add:
            raise NotFoundException(f"Користувач з ID {user_id_to_add} для додавання не знайдений.")

        # Перевірка, чи користувач є членом групи, до якої належить команда
        if not await group_membership_service.is_user_member_of_group(db, user_id=user_id_to_add, group_id=team.group_id):
            raise BadRequestException(f"Користувач {user_id_to_add} не є членом групи, до якої належить команда.")

        # Перевірка, чи користувач вже не є членом команди
        existing_membership = await self.repository.get_by_user_and_team(db, user_id=user_id_to_add, team_id=team_id)
        if existing_membership:
            raise BadRequestException(f"Користувач {user_id_to_add} вже є членом команди {team_id}.")

        # Перевірка максимальної кількості учасників
        if team.max_members is not None:
            current_members_count = await self.repository.count_members_in_team(db, team_id=team_id) # Потрібен такий метод в репо
            if current_members_count >= team.max_members:
                raise BadRequestException(f"Досягнуто максимальну кількість учасників ({team.max_members}) для команди {team.name}.")

        create_schema = TeamMembershipCreateSchema(user_id=user_id_to_add, role_in_team=role_in_team)
        # `team_id` передається в кастомний метод репозиторію
        return await self.repository.add_member_to_team(db, team_id=team_id, obj_in=create_schema)

    async def add_member_to_team_internal( # Для використання іншими сервісами без перевірки прав
        self, db: AsyncSession, *, team_id: uuid.UUID, user_id: uuid.UUID, role_in_team: Optional[str] = None
    ) -> TeamMembershipModel:
        """Внутрішній метод для додавання учасника, без перевірки прав."""
        # Перевірки існування user, team, членства в групі мають бути зроблені викликаючим кодом, якщо потрібно.
        existing_membership = await self.repository.get_by_user_and_team(db, user_id=user_id, team_id=team_id)
        if existing_membership:
            return existing_membership # Вже член

        # TODO: Перевірка max_members, якщо потрібно і тут.

        create_schema = TeamMembershipCreateSchema(user_id=user_id, role_in_team=role_in_team)
        return await self.repository.add_member_to_team(db, team_id=team_id, obj_in=create_schema)


    async def remove_member_from_team(
        self, db: AsyncSession, *,
        team_id: uuid.UUID,
        user_id_to_remove: uuid.UUID,
        current_user: UserModel
    ) -> Optional[TeamMembershipModel]:
        """Видаляє користувача з команди."""
        membership = await self.repository.get_by_user_and_team(db, user_id=user_id_to_remove, team_id=team_id)
        if not membership:
            raise NotFoundException(f"Користувач {user_id_to_remove} не є членом команди {team_id}.")

        team = await team_repository.get(db, id=team_id) # Потрібен для перевірки лідера та group_id
        if not team: raise NotFoundException(f"Команда {team_id} не знайдена.") # Малоймовірно

        # Перевірка прав
        from backend.app.src.services.groups.group_membership_service import group_membership_service
        is_group_admin = await group_membership_service.is_user_group_admin(db, user_id=current_user.id, group_id=team.group_id)
        is_current_user_team_leader = team.leader_user_id == current_user.id

        can_remove = False
        if current_user.user_type_code == USER_TYPE_SUPERADMIN:
            can_remove = True
        elif is_group_admin:
            can_remove = True
        elif is_current_user_team_leader: # Лідер може видаляти інших
            if current_user.id == user_id_to_remove: # Лідер намагається видалити себе
                # TODO: Логіка, якщо лідер видаляє себе (наприклад, команда розпускається або потрібен новий лідер)
                raise BadRequestException("Лідер команди не може видалити себе з команди таким чином. Спочатку змініть лідера або розпустіть команду.")
            can_remove = True
        elif current_user.id == user_id_to_remove: # Сам користувач виходить
            if team.leader_user_id == user_id_to_remove: # Лідер намагається вийти
                 raise BadRequestException("Лідер команди не може просто покинути команду. Спочатку змініть лідера або розпустіть команду.")
            can_remove = True

        if not can_remove:
            raise ForbiddenException("Ви не маєте прав видаляти цього учасника з команди.")

        return await self.repository.delete(db, id=membership.id)

    async def update_member_role_in_team(
        self, db: AsyncSession, *,
        team_id: uuid.UUID,
        user_id_to_update: uuid.UUID,
        obj_in: TeamMembershipUpdateSchema, # Містить нову role_in_team
        current_user: UserModel
    ) -> TeamMembershipModel:
        """Оновлює роль користувача в команді."""
        membership = await self.repository.get_by_user_and_team(db, user_id=user_id_to_update, team_id=team_id)
        if not membership:
            raise NotFoundException(f"Користувач {user_id_to_update} не є членом команди {team_id}.")

        team = await team_repository.get(db, id=team_id)
        if not team: raise NotFoundException(f"Команда {team_id} не знайдена.")

        # Перевірка прав (лідер команди, адмін групи, superuser)
        from backend.app.src.services.groups.group_membership_service import group_membership_service
        is_group_admin = await group_membership_service.is_user_group_admin(db, user_id=current_user.id, group_id=team.group_id)
        is_team_leader = team.leader_user_id == current_user.id

        if not (is_team_leader or is_group_admin or current_user.user_type_code == USER_TYPE_SUPERADMIN):
            raise ForbiddenException("Лише лідер команди або адміністратор групи може змінювати ролі в команді.")

        # Перевірка, чи не намагаються змінити роль лідера через це поле
        if team.leader_user_id == user_id_to_update and obj_in.role_in_team is not None:
            # Роль лідера визначається полем TeamModel.leader_user_id, а не TeamMembershipModel.role_in_team
            self.logger.warning(f"Спроба змінити role_in_team для лідера команди {team_id}. Це поле ігнорується для лідера.")
            # Можна або ігнорувати, або кинути помилку, якщо role_in_team не None
            # obj_in.role_in_team = None # Ігноруємо

        return await self.repository.update(db, db_obj=membership, obj_in=obj_in)

    # TODO: Додати метод `ensure_member_in_team` для використання в TeamService.
    #       async def ensure_member_in_team(self, db: AsyncSession, *, team_id: uuid.UUID, user_id: uuid.UUID, role_in_team: Optional[str] = None): ...

team_membership_service = TeamMembershipService(team_membership_repository)

# TODO: Реалізувати метод `count_members_in_team` в `TeamMembershipRepository`.
# TODO: Узгодити логіку виходу/видалення лідера команди.
#
# Все виглядає як хороший початок для TeamMembershipService.
# Основні операції: додавання, видалення, оновлення ролі учасника.
# Перевірка прав.
# Інтеграція з іншими сервісами/репозиторіями для перевірок.
