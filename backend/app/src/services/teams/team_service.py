# backend/app/src/services/teams/team_service.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає сервіс `TeamService` для управління командами в групах.
"""
from typing import List, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore

from backend.app.src.models.teams.team import TeamModel
from backend.app.src.models.auth.user import UserModel
from backend.app.src.schemas.teams.team import TeamCreateSchema, TeamUpdateSchema, TeamSchema
from backend.app.src.repositories.teams.team import TeamRepository, team_repository
from backend.app.src.repositories.groups.group import group_repository
from backend.app.src.repositories.auth.user import user_repository # Для перевірки лідера
from backend.app.src.repositories.dictionaries.status import status_repository # Для статусу
from backend.app.src.services.base import BaseService
from backend.app.src.core.exceptions import NotFoundException, ForbiddenException, BadRequestException
from backend.app.src.core.constants import USER_TYPE_SUPERADMIN, STATUS_ACTIVE_CODE
# from backend.app.src.services.groups.group_membership_service import group_membership_service
# from backend.app.src.services.teams.team_membership_service import team_membership_service # Для додавання лідера

class TeamService(BaseService[TeamRepository]):
    """
    Сервіс для управління командами.
    """

    async def get_team_by_id(self, db: AsyncSession, team_id: uuid.UUID, include_details: bool = True) -> TeamModel:
        team = None
        if include_details:
            team = await self.repository.get_team_with_details(db, team_id=team_id)
        else:
            team = await self.repository.get(db, id=team_id)

        if not team:
            raise NotFoundException(f"Команду з ID {team_id} не знайдено.")
        return team

    async def create_team_in_group(
        self, db: AsyncSession, *, obj_in: TeamCreateSchema, group_id: uuid.UUID, current_user: UserModel
    ) -> TeamModel:
        """
        Створює нову команду в групі.
        """
        # Перевірка прав: адмін групи або superuser
        from backend.app.src.services.groups.group_membership_service import group_membership_service # Відкладений імпорт
        if not await group_membership_service.is_user_group_admin(db, user_id=current_user.id, group_id=group_id) and \
           current_user.user_type_code != USER_TYPE_SUPERADMIN:
            raise ForbiddenException("Лише адміністратор групи може створювати команди.")

        # Перевірка існування групи
        group = await group_repository.get(db, id=group_id)
        if not group:
            raise NotFoundException(f"Групу з ID {group_id} не знайдено.")

        # Перевірка унікальності назви команди в групі (реалізовано в моделі через UniqueConstraint)
        existing_team_name = await self.repository.get_team_by_name_and_group(db, name=obj_in.name, group_id=group_id)
        if existing_team_name:
            raise BadRequestException(f"Команда з назвою '{obj_in.name}' вже існує в цій групі.")

        # Перевірка лідера, якщо вказаний
        if obj_in.leader_user_id:
            leader = await user_repository.get(db, id=obj_in.leader_user_id)
            if not leader:
                raise BadRequestException(f"Користувач-лідер з ID {obj_in.leader_user_id} не знайдений.")
            # Перевірка, чи лідер є членом групи
            if not await group_membership_service.is_user_member_of_group(db, user_id=obj_in.leader_user_id, group_id=group_id):
                 raise BadRequestException(f"Призначений лідер (ID: {obj_in.leader_user_id}) не є членом групи {group_id}.")

        # Встановлення початкового статусу
        create_data = obj_in.model_dump(exclude_unset=True)
        if not obj_in.state_id: # state_id опціональне в схемі
            active_status = await status_repository.get_by_code(db, code=STATUS_ACTIVE_CODE)
            if active_status:
                create_data['state_id'] = active_status.id

        # Створення команди
        # `group_id` та `created_by_user_id` мають бути встановлені.
        # Модель TeamModel успадковує їх з BaseMainModel.
        # Репозиторій BaseRepository.create приймає схему.
        # Потрібно, щоб TeamCreateSchema не мала group_id, а він передавався окремо.
        # Або щоб сервіс додавав group_id до даних перед передачею в create.
        # Поточна TeamCreateSchema не має group_id.

        # Створюємо модель напряму, передаючи group_id та created_by_user_id
        db_team = self.repository.model(
            group_id=group_id,
            created_by_user_id=current_user.id,
            **create_data
        )
        db.add(db_team)
        await db.flush() # Потрібен ID команди для додавання лідера як члена

        # Якщо призначено лідера, автоматично додаємо його до команди
        if db_team.leader_user_id:
            from backend.app.src.services.teams.team_membership_service import team_membership_service # Відкладений імпорт
            from backend.app.src.schemas.teams.membership import TeamMembershipCreateSchema
            # Перевірка, чи лідер вже не є членом (малоймовірно для нової команди)
            # `add_member_to_team` в TeamMembershipService має це обробити.
            # Роль лідера в команді може бути просто "member" або спеціальна.
            # Поки що без спеціальної ролі, TeamModel.leader_user_id визначає лідера.
            try:
                await team_membership_service.add_member_to_team_internal(
                    db, team_id=db_team.id, user_id=db_team.leader_user_id, role_in_team="leader" # або None
                )
            except BadRequestException as e: # Наприклад, якщо вже член
                self.logger.warning(f"Лідер {db_team.leader_user_id} вже міг бути доданий до команди {db_team.id} або інша помилка: {e}")


        await db.commit()
        await db.refresh(db_team)
        # Завантажуємо зв'язки для відповіді
        await db.refresh(db_team, attribute_names=['leader', 'group', 'state'])
        return db_team

    async def update_team(
        self, db: AsyncSession, *, team_id: uuid.UUID, obj_in: TeamUpdateSchema, current_user: UserModel
    ) -> TeamModel:
        """Оновлює існуючу команду."""
        db_team = await self.get_team_by_id(db, team_id=team_id, include_details=False)

        # Перевірка прав
        from backend.app.src.services.groups.group_membership_service import group_membership_service
        if not await group_membership_service.is_user_group_admin(db, user_id=current_user.id, group_id=db_team.group_id) and \
           current_user.user_type_code != USER_TYPE_SUPERADMIN:
            raise ForbiddenException("Ви не маєте прав оновлювати цю команду.")

        update_data = obj_in.model_dump(exclude_unset=True)

        # Перевірка унікальності назви, якщо вона змінюється
        if "name" in update_data and update_data["name"] != db_team.name:
            existing_team_name = await self.repository.get_team_by_name_and_group(db, name=update_data["name"], group_id=db_team.group_id)
            if existing_team_name and existing_team_name.id != team_id:
                raise BadRequestException(f"Команда з назвою '{update_data['name']}' вже існує в цій групі.")

        # Перевірка нового лідера, якщо він змінюється
        if "leader_user_id" in update_data and update_data["leader_user_id"] != db_team.leader_user_id:
            new_leader_id = update_data["leader_user_id"]
            if new_leader_id: # Якщо встановлюється новий лідер
                leader = await user_repository.get(db, id=new_leader_id)
                if not leader:
                    raise BadRequestException(f"Новий користувач-лідер з ID {new_leader_id} не знайдений.")
                if not await group_membership_service.is_user_member_of_group(db, user_id=new_leader_id, group_id=db_team.group_id):
                    raise BadRequestException(f"Новий лідер (ID: {new_leader_id}) не є членом групи команди.")
                # TODO: Додати нового лідера до команди, якщо його там ще немає.
                # from backend.app.src.services.teams.team_membership_service import team_membership_service
                # await team_membership_service.ensure_member_in_team(db, team_id=team_id, user_id=new_leader_id)
            # Якщо leader_user_id встановлюється в None, старий лідер просто перестає бути лідером.
            # Його членство в команді залишається (якщо було).

        # update_data["updated_by_user_id"] = current_user.id # Якщо потрібно

        updated_team = await self.repository.update(db, db_obj=db_team, obj_in=update_data)
        await db.refresh(updated_team, attribute_names=['leader', 'group', 'state', 'memberships'])
        return updated_team


    async def delete_team(self, db: AsyncSession, *, team_id: uuid.UUID, current_user: UserModel) -> TeamModel:
        """Видаляє команду (м'яке видалення)."""
        db_team = await self.get_team_by_id(db, team_id=team_id, include_details=False)

        from backend.app.src.services.groups.group_membership_service import group_membership_service
        if not await group_membership_service.is_user_group_admin(db, user_id=current_user.id, group_id=db_team.group_id) and \
           current_user.user_type_code != USER_TYPE_SUPERADMIN:
            raise ForbiddenException("Ви не маєте прав видаляти цю команду.")

        # TODO: Перевірити, чи команда не має активних завдань, перш ніж видаляти.
        # if db_team.tasks_assigned and any(not task.is_deleted for task in db_team.tasks_assigned): # Потребує завантаження tasks_assigned
        #     raise BadRequestException("Неможливо видалити команду, оскільки їй призначені активні завдання.")

        deleted_team = await self.repository.soft_delete(db, db_obj=db_team) # type: ignore
        if not deleted_team:
            raise NotImplementedError("М'яке видалення не підтримується або не вдалося для команд.")
        return deleted_team

team_service = TeamService(team_repository)

# TODO: Реалізувати перевірку прав та умов у всіх методах.
# TODO: Доопрацювати логіку додавання лідера до учасників команди при створенні/оновленні.
#       Потрібен метод `ensure_member_in_team` в `TeamMembershipService`.
# TODO: Реалізувати перевірку на активні завдання перед видаленням команди.
# TODO: Узгодити встановлення `created_by_user_id` / `updated_by_user_id`.
#       (Вирішено: сервіс встановлює `created_by_user_id` при створенні моделі напряму).
#
# Все виглядає як хороший початок для TeamService.
# Основні CRUD операції з перевірками прав та існування сутностей.
# Інтеграція з TeamMembershipService для управління учасниками (особливо лідером).
