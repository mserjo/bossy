# backend/app/src/services/gamification/badge_service.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає сервіс `BadgeService` для управління налаштуваннями бейджів.
"""
from typing import List, Optional, Dict, Any
import uuid
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore

from backend.app.src.models.gamification.badge import BadgeModel
from backend.app.src.models.auth.user import UserModel
from backend.app.src.schemas.gamification.badge import BadgeCreateSchema, BadgeUpdateSchema, BadgeSchema
from backend.app.src.repositories.gamification.badge import BadgeRepository, badge_repository
from backend.app.src.repositories.groups.group import group_repository
from backend.app.src.repositories.dictionaries.status import status_repository
from backend.app.src.services.base import BaseService
from backend.app.src.core.exceptions import NotFoundException, ForbiddenException, BadRequestException
from backend.app.src.core.constants import USER_TYPE_SUPERADMIN, STATUS_ACTIVE_CODE
from backend.app.src.core.dicts import BadgeConditionTypeEnum # Для валідації condition_type_code

class BadgeService(BaseService[BadgeRepository]):
    """
    Сервіс для управління налаштуваннями бейджів.
    """

    async def get_badge_by_id(self, db: AsyncSession, badge_id: uuid.UUID) -> BadgeModel:
        badge = await self.repository.get(db, id=badge_id) # Репозиторій може завантажувати зв'язки
        if not badge:
            raise NotFoundException(f"Бейдж з ID {badge_id} не знайдено.")
        return badge

    async def create_badge(
        self, db: AsyncSession, *, obj_in: BadgeCreateSchema, group_id: uuid.UUID, current_user: UserModel
    ) -> BadgeModel:
        """
        Створює нове налаштування бейджа в групі.
        """
        # Перевірка прав: адмін групи або superuser
        from backend.app.src.services.groups.group_membership_service import group_membership_service # Відкладений імпорт
        if not await group_membership_service.is_user_group_admin(db, user_id=current_user.id, group_id=group_id) and \
           current_user.user_type_code != USER_TYPE_SUPERADMIN:
            raise ForbiddenException("Лише адміністратор групи може створювати налаштування бейджів.")

        group = await group_repository.get(db, id=group_id)
        if not group:
            raise NotFoundException(f"Групу з ID {group_id} не знайдено.")

        # Валідація condition_type_code (чи є він в Enum)
        try:
            BadgeConditionTypeEnum(obj_in.condition_type_code)
        except ValueError:
            raise BadRequestException(f"Невідомий тип умови для бейджа: {obj_in.condition_type_code}.")

        # TODO: Валідація `condition_details` на основі `condition_type_code`.
        # Це може бути складною логікою, можливо, з використанням JSON Schema.

        # Встановлення початкового статусу
        create_data = obj_in.model_dump(exclude_unset=True)
        if not obj_in.state_id:
            active_status = await status_repository.get_by_code(db, code=STATUS_ACTIVE_CODE)
            if not active_status:
                 raise BadRequestException(f"Дефолтний активний статус '{STATUS_ACTIVE_CODE}' не знайдено.")
            create_data['state_id'] = active_status.id

        # created_by_user_id встановлюється в репозиторії
        return await self.repository.create_badge_for_group(db, obj_in_data=create_data, group_id=group_id, creator_id=current_user.id) # type: ignore

    async def update_badge(
        self, db: AsyncSession, *, badge_id: uuid.UUID, obj_in: BadgeUpdateSchema, current_user: UserModel
    ) -> BadgeModel:
        """Оновлює існуюче налаштування бейджа."""
        db_badge = await self.get_badge_by_id(db, badge_id=badge_id)

        from backend.app.src.services.groups.group_membership_service import group_membership_service
        if not await group_membership_service.is_user_group_admin(db, user_id=current_user.id, group_id=db_badge.group_id) and \
           current_user.user_type_code != USER_TYPE_SUPERADMIN:
            raise ForbiddenException("Ви не маєте прав оновлювати це налаштування бейджа.")

        update_data = obj_in.model_dump(exclude_unset=True)
        if "condition_type_code" in update_data:
            try:
                BadgeConditionTypeEnum(update_data["condition_type_code"])
            except ValueError:
                raise BadRequestException(f"Невідомий тип умови для бейджа: {update_data['condition_type_code']}.")

        # TODO: Валідація `condition_details` при зміні `condition_type_code` або самих деталей.

        return await self.repository.update(db, db_obj=db_badge, obj_in=update_data)

    async def delete_badge(self, db: AsyncSession, *, badge_id: uuid.UUID, current_user: UserModel) -> BadgeModel:
        """Видаляє налаштування бейджа (м'яке видалення)."""
        db_badge = await self.get_badge_by_id(db, badge_id=badge_id)

        from backend.app.src.services.groups.group_membership_service import group_membership_service
        if not await group_membership_service.is_user_group_admin(db, user_id=current_user.id, group_id=db_badge.group_id) and \
           current_user.user_type_code != USER_TYPE_SUPERADMIN:
            raise ForbiddenException("Ви не маєте прав видаляти це налаштування бейджа.")

        # TODO: Перевірити, чи цей бейдж не використовується (чи не присуджений комусь).
        # achievements_count = await achievement_repository.count_achievements_for_badge(db, badge_id=badge_id)
        # if achievements_count > 0:
        #     raise BadRequestException("Неможливо видалити бейдж, оскільки він вже присуджений користувачам.")

        deleted_badge = await self.repository.soft_delete(db, db_obj=db_badge) # type: ignore
        if not deleted_badge:
            raise NotImplementedError("М'яке видалення не підтримується або не вдалося для налаштувань бейджів.")
        return deleted_badge

badge_service = BadgeService(badge_repository)

# TODO: Реалізувати TODO в методах (валідація condition_details, перевірка використання перед видаленням).
# TODO: Узгодити встановлення `created_by_user_id` в `BadgeRepository.create_badge_for_group`.
#       (Поточний `BadgeRepository` не має `create_badge_for_group`, використовує успадкований `create`.
#        Отже, `creator_id` має передаватися в `obj_in` для `create` або встановлюватися в моделі/хуками).
#       Виправлено: `BadgeRepository` тепер має `create_badge_for_group`, який приймає `creator_id`.
#
# Все виглядає як хороший початок для BadgeService.
