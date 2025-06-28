# backend/app/src/repositories/groups/group.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає репозиторій для моделі `GroupModel`.
Надає методи для взаємодії з таблицею груп в базі даних.
"""

from typing import Optional, List
import uuid
from sqlalchemy import select # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore
from sqlalchemy.orm import selectinload, joinedload # type: ignore

from backend.app.src.models.groups.group import GroupModel
from backend.app.src.schemas.groups.group import GroupCreateSchema, GroupUpdateSchema
from backend.app.src.repositories.base import BaseRepository

class GroupRepository(BaseRepository[GroupModel, GroupCreateSchema, GroupUpdateSchema]):
    """
    Репозиторій для роботи з моделлю груп (`GroupModel`).
    """

    async def get_with_details(self, db: AsyncSession, id: uuid.UUID) -> Optional[GroupModel]:
        """
        Отримує групу з деякими розгорнутими зв'язками.
        Наприклад, з типом групи, налаштуваннями, іконкою.
        """
        statement = select(self.model).where(self.model.id == id).options(
            selectinload(self.model.group_type),
            selectinload(self.model.settings),
            selectinload(self.model.icon_file),
            selectinload(self.model.parent_group), # Для ієрархії
            # selectinload(self.model.child_groups) # Може бути багато, завантажувати окремо, якщо потрібно
        )
        try:
            result = await db.execute(statement)
            return result.scalar_one_or_none()
        except Exception as e:
            self.logger.error(f"Помилка отримання групи з деталями (ID: {id}): {e}", exc_info=True)
            return None


    async def get_user_groups(self, db: AsyncSession, *, user_id: uuid.UUID) -> List[GroupModel]:
        """
        Отримує список груп, до яких належить користувач.
        """
        from backend.app.src.models.groups.membership import GroupMembershipModel
        from backend.app.src.models.dictionaries.status import StatusModel # Для JOIN по статусу членства
        from backend.app.src.core.constants import STATUS_ACTIVE_CODE # Припускаємо, що це код активного статусу

        try:
            statement = (
                select(self.model)
                .join(GroupMembershipModel, self.model.id == GroupMembershipModel.group_id)
                .join(StatusModel, GroupMembershipModel.status_in_group_id == StatusModel.id) # Приєднуємо статуси членства
                .where(GroupMembershipModel.user_id == user_id)
                .where(StatusModel.code == STATUS_ACTIVE_CODE) # Фільтруємо за активним статусом членства
            )
            # self.logger.debug(f"Запит для get_user_groups (user_id: {user_id}): {statement}")
            result = await db.execute(statement)
            return result.scalars().all() # type: ignore
        except Exception as e:
            self.logger.error(f"Помилка отримання груп для користувача {user_id}: {e}", exc_info=True)
            return []


    async def get_child_groups(self, db: AsyncSession, *, parent_group_id: uuid.UUID) -> List[GroupModel]:
        """
        Отримує список дочірніх груп для вказаної батьківської групи.
        """
        try:
            statement = select(self.model).where(self.model.parent_group_id == parent_group_id)
            result = await db.execute(statement)
            return result.scalars().all() # type: ignore
        except Exception as e:
            self.logger.error(f"Помилка отримання дочірніх груп для {parent_group_id}: {e}", exc_info=True)
            return []


    async def search_by_name(self, db: AsyncSession, *, name_query: str, skip: int = 0, limit: int = 100) -> List[GroupModel]:
        """
        Шукає групи за назвою (часткове співпадіння, без урахування регістру).
        """
        # Використовуємо get_multi з BaseRepository, передаючи відповідний фільтр
        filters = {"name__ilike": f"%{name_query}%"} # Потрібно, щоб _apply_filters підтримував __ilike
        # Поки _apply_filters не підтримує __ilike, робимо прямий запит:
        try:
            statement = select(self.model).where(self.model.name.ilike(f"%{name_query}%")).offset(skip).limit(limit)
            result = await db.execute(statement)
            return result.scalars().all() # type: ignore
        except Exception as e:
            self.logger.error(f"Помилка пошуку груп за назвою '{name_query}': {e}", exc_info=True)
            return []

    # TODO: Додати метод для отримання групи разом з усіма її членами (якщо потрібно).
    # async def get_group_with_members(self, db: AsyncSession, id: uuid.UUID) -> Optional[GroupModel]:
    #     statement = select(self.model).where(self.model.id == id).options(
    #         selectinload(self.model.memberships).selectinload(GroupMembershipModel.user),
    #         selectinload(self.model.memberships).selectinload(GroupMembershipModel.role)
    #     )
    #     result = await db.execute(statement)
    #     return result.scalar_one_or_none()

    # TODO: Додати метод для отримання групи разом з її адміністраторами.

group_repository = GroupRepository(GroupModel)

# Все виглядає добре.
# Додано специфічні методи:
# - `get_with_details` для отримання групи з деякими важливими зв'язками.
# - `get_user_groups` для отримання списку груп користувача.
# - `get_child_groups` для ієрархії.
# Залишено TODO для інших потенційно корисних методів.
# Використано `selectinload` для ефективного завантаження зв'язків.
# Локальний імпорт `GroupMembershipModel` в `get_user_groups` для уникнення можливих циклічних залежностей
# на рівні імпорту модулів (хоча для репозиторіїв це менш критично, ніж для моделей).
