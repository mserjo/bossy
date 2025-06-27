# backend/app/src/services/gamification/user_level_service.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає сервіс `UserLevelService` для управління рівнями,
досягнутими користувачами.
"""
from typing import List, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore

from backend.app.src.models.gamification.user_level import UserLevelModel
from backend.app.src.models.auth.user import UserModel
from backend.app.src.models.gamification.level import LevelModel # Для перевірки
from backend.app.src.schemas.gamification.user_level import UserLevelCreateSchema, UserLevelSchema # UpdateSchema не дуже релевантна
from backend.app.src.repositories.gamification.user_level import UserLevelRepository, user_level_repository
from backend.app.src.repositories.gamification.level import level_repository # Для перевірки рівня
from backend.app.src.repositories.auth.user import user_repository # Для перевірки користувача
from backend.app.src.repositories.groups.group import group_repository # Для перевірки групи
from backend.app.src.services.base import BaseService
from backend.app.src.core.exceptions import NotFoundException, ForbiddenException, BadRequestException
from backend.app.src.core.constants import USER_TYPE_SUPERADMIN

class UserLevelService(BaseService[UserLevelRepository]):
    """
    Сервіс для управління досягненнями рівнів користувачами.
    """

    async def get_user_level_by_id(self, db: AsyncSession, user_level_id: uuid.UUID) -> UserLevelModel:
        user_level = await self.repository.get(db, id=user_level_id)
        if not user_level:
            raise NotFoundException(f"Запис про досягнення рівня з ID {user_level_id} не знайдено.")
        return user_level

    async def grant_level_to_user(
        self, db: AsyncSession, *,
        user_id: uuid.UUID,
        group_id: uuid.UUID, # Група, в контексті якої надається рівень
        level_id: uuid.UUID,
        # current_admin_user: UserModel # Якщо рівні надаються лише адміном
    ) -> UserLevelModel:
        """
        Надає користувачеві вказаний рівень в групі.
        Оновлює прапорець `is_current` для рівнів цього користувача в цій групі.
        """
        # Перевірка існування користувача, групи, рівня
        user = await user_repository.get(db, id=user_id)
        if not user: raise NotFoundException(f"Користувач з ID {user_id} не знайдений.")

        group = await group_repository.get(db, id=group_id)
        if not group: raise NotFoundException(f"Група з ID {group_id} не знайдена.")

        level_to_grant = await level_repository.get(db, id=level_id)
        if not level_to_grant: raise NotFoundException(f"Рівень з ID {level_id} не знайдений.")
        if level_to_grant.group_id != group_id:
            raise BadRequestException(f"Рівень {level_id} не належить групі {group_id}.")

        # Перевірка, чи користувач вже не досяг цього рівня
        existing_achievement = await self.repository.get_achieved_level(db, user_id=user_id, level_id=level_id)
        if existing_achievement:
            # Якщо вже досягнуто, і він не поточний, можна зробити його поточним.
            # Або просто повернути існуючий, якщо логіка не дозволяє "повторно досягати".
            if not existing_achievement.is_current:
                return await self.repository.set_level_as_current(db, user_id=user_id, group_id=group_id, level_id_to_set_current=level_id) # type: ignore
            return existing_achievement # Вже досягнуто і є поточним

        # Якщо рівень ще не досягнуто, створюємо новий запис
        create_schema = UserLevelCreateSchema(
            user_id=user_id,
            group_id=group_id, # group_id потрібен для UserLevelModel та для логіки is_current
            level_id=level_id,
            is_current=True # Новий рівень стає поточним
        )
        # Метод achieve_level в репозиторії має обробити is_current для інших рівнів
        return await self.repository.achieve_level(db, obj_in=create_schema)


    async def get_current_user_level_in_group(
        self, db: AsyncSession, *, user_id: uuid.UUID, group_id: uuid.UUID
    ) -> Optional[UserLevelSchema]: # Повертаємо схему для API
        """
        Отримує поточний рівень користувача в групі, розгорнутий з деталями рівня.
        """
        user_level_db = await self.repository.get_current_level_for_user_in_group(db, user_id=user_id, group_id=group_id)
        if user_level_db:
            return UserLevelSchema.model_validate(user_level_db)
        return None

    async def get_user_level_history_in_group(
        self, db: AsyncSession, *, user_id: uuid.UUID, group_id: uuid.UUID,
        page: int = 1, size: int = 10
    ) -> PaginatedResponse[UserLevelSchema]: # type: ignore
        """Отримує історію досягнутих рівнів користувачем в групі з пагінацією."""
        # TODO: Реалізувати пагінацію в репозиторії або тут.
        # Поки що простий виклик з лімітом.
        offset = (page - 1) * size
        history_db = await self.repository.get_all_achieved_levels_for_user_in_group(
            db, user_id=user_id, group_id=group_id, skip=offset, limit=size
        )

        # Для пагінації потрібен загальний підрахунок
        # count_statement = select(func.count(self.repository.model.id)).where(
        #     self.repository.model.user_id == user_id,
        #     self.repository.model.group_id == group_id
        # )
        # total_items = (await db.execute(count_statement)).scalar_one()
        # Поки що заглушка для total_items
        total_items = len(history_db) if page == 1 and len(history_db) < size else (size * page + (1 if len(history_db) == size else 0) )


        items_schema = [UserLevelSchema.model_validate(item) for item in history_db]

        from backend.app.src.schemas.base import PaginatedResponse # Локальний імпорт
        return PaginatedResponse(
            total=total_items, # TODO: Замінити на реальний підрахунок
            page=page,
            size=len(items_schema),
            pages=(total_items + size - 1) // size if total_items > 0 else 0, # TODO: Замінити
            items=items_schema
        )

    # Зазвичай рівні досягаються автоматично, а не видаляються.
    # Якщо потрібне "скасування" рівня, це може бути окрема логіка.

user_level_service = UserLevelService(user_level_repository)

# TODO: Реалізувати логіку автоматичного надання рівнів на основі умов (бали, завдання).
#       Це може бути в окремому "GamificationEngineService" або тут,
#       викликатися при зміні балів користувача або виконанні завдань.
#
# TODO: Перевірити та доопрацювати логіку пагінації в `get_user_level_history_in_group`.
#
# TODO: `grant_level_to_user` зараз не має `current_admin_user` для перевірки прав,
#       оскільки передбачається, що рівні можуть надаватися системно.
#       Якщо потрібне ручне надання рівнів адміном, додати перевірку прав.
#
# Все виглядає як хороший початок для UserLevelService.
# Основні методи для надання рівня та отримання інформації про рівні користувача.
# Використовує методи репозиторію для оновлення `is_current`.
