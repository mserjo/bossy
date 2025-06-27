# backend/app/src/services/gamification/achievement_service.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає сервіс `AchievementService` для управління
досягненнями користувачів (отриманими бейджами).
"""
from typing import List, Optional, Dict, Any
import uuid
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore

from backend.app.src.models.gamification.achievement import AchievementModel
from backend.app.src.models.auth.user import UserModel
from backend.app.src.models.gamification.badge import BadgeModel # Для перевірки бейджа
from backend.app.src.schemas.gamification.achievement import AchievementCreateSchema, AchievementSchema # UpdateSchema не дуже релевантна
from backend.app.src.repositories.gamification.achievement import AchievementRepository, achievement_repository
from backend.app.src.repositories.gamification.badge import badge_repository # Для отримання деталей бейджа
from backend.app.src.repositories.auth.user import user_repository # Для перевірки користувача
from backend.app.src.services.base import BaseService
from backend.app.src.core.exceptions import NotFoundException, ForbiddenException, BadRequestException
from backend.app.src.core.constants import USER_TYPE_SUPERADMIN

class AchievementService(BaseService[AchievementRepository]):
    """
    Сервіс для управління досягненнями користувачів (отриманими бейджами).
    """

    async def get_achievement_by_id(self, db: AsyncSession, achievement_id: uuid.UUID) -> AchievementModel:
        achievement = await self.repository.get(db, id=achievement_id) # Репозиторій може завантажувати зв'язки
        if not achievement:
            raise NotFoundException(f"Досягнення з ID {achievement_id} не знайдено.")
        return achievement

    async def award_badge_to_user(
        self, db: AsyncSession, *,
        user_id: uuid.UUID,
        badge_id: uuid.UUID,
        context_details: Optional[Dict[str, Any]] = None,
        awarded_by_user: Optional[UserModel] = None, # Адмін, що вручну присуджує, або None для системного
        award_reason: Optional[str] = None
    ) -> AchievementModel:
        """
        Присуджує бейдж користувачеві.
        Перевіряє, чи можна присудити цей бейдж (is_repeatable).
        """
        user = await user_repository.get(db, id=user_id)
        if not user: raise NotFoundException(f"Користувач з ID {user_id} не знайдений.")

        badge = await badge_repository.get_badge_by_id(db, badge_id=badge_id) # Використовуємо сервіс або репо бейджів
        if not badge: raise NotFoundException(f"Бейдж з ID {badge_id} не знайдений.")

        # Перевірка, чи можна повторно присуджувати цей бейдж
        if not badge.is_repeatable:
            existing_achievement = await self.repository.get_user_achievement_for_badge(db, user_id=user_id, badge_id=badge_id)
            if existing_achievement:
                raise BadRequestException(f"Користувач {user_id} вже має бейдж '{badge.name}'. Цей бейдж не є повторюваним.")

        # Перевірка прав, якщо це ручне нагородження
        awarded_by_id = None
        if awarded_by_user:
            # Припускаємо, що лише адмін групи бейджа або superuser може вручну нагороджувати
            from backend.app.src.services.groups.group_membership_service import group_membership_service
            if badge.group_id: # Бейдж належить групі
                 if not await group_membership_service.is_user_group_admin(db, user_id=awarded_by_user.id, group_id=badge.group_id) and \
                    awarded_by_user.user_type_code != USER_TYPE_SUPERADMIN:
                    raise ForbiddenException("Лише адміністратор групи бейджа або супер-адміністратор може вручну присуджувати цей бейдж.")
            elif awarded_by_user.user_type_code != USER_TYPE_SUPERADMIN: # Глобальний бейдж - лише superuser
                 raise ForbiddenException("Лише супер-адміністратор може вручну присуджувати глобальні бейджі.")
            awarded_by_id = awarded_by_user.id

        create_schema = AchievementCreateSchema(
            user_id=user_id,
            badge_id=badge_id,
            context_details=context_details,
            awarded_by_user_id=awarded_by_id,
            award_reason=award_reason
        )
        # Використовуємо кастомний метод репозиторію, який просто створює запис.
        # Або успадкований self.repository.create(db, obj_in=create_schema)
        return await self.repository.create_achievement(db, obj_in=create_schema)


    async def revoke_achievement(
        self, db: AsyncSession, *, achievement_id: uuid.UUID, current_user: UserModel # Адмін
    ) -> Optional[AchievementModel]:
        """
        Відкликає (видаляє) досягнення/бейдж у користувача.
        Потребує прав адміністратора.
        """
        achievement_to_revoke = await self.get_achievement_by_id(db, achievement_id=achievement_id)

        # Потрібно отримати групу бейджа для перевірки прав
        badge = await badge_repository.get_badge_by_id(db, badge_id=achievement_to_revoke.badge_id)
        if not badge: # Малоймовірно
            raise NotFoundException("Пов'язаний бейдж для досягнення не знайдено.")

        from backend.app.src.services.groups.group_membership_service import group_membership_service
        if badge.group_id:
            if not await group_membership_service.is_user_group_admin(db, user_id=current_user.id, group_id=badge.group_id) and \
               current_user.user_type_code != USER_TYPE_SUPERADMIN:
                raise ForbiddenException("Ви не маєте прав відкликати це досягнення.")
        elif current_user.user_type_code != USER_TYPE_SUPERADMIN: # Для глобальних бейджів
             raise ForbiddenException("Лише супер-адміністратор може відкликати глобальні досягнення.")

        return await self.repository.delete(db, id=achievement_id)

    # TODO: Додати метод для отримання всіх досягнень користувача з пагінацією.
    # TODO: Додати метод для отримання всіх користувачів, що мають певний бейдж.
    #       (Ці методи вже є в репозиторії, їх потрібно лише викликати з пагінацією/фільтрами).

achievement_service = AchievementService(achievement_repository)

# TODO: Реалізувати логіку автоматичного присудження бейджів на основі
#       `BadgeModel.condition_type_code` та `condition_details`.
#       Це може бути в окремому "GamificationEngineService" або тут,
#       викликатися при певних подіях (виконання завдання, зміна балансу тощо).
#
# TODO: Переконатися, що `AchievementCreateSchema` коректно обробляє всі поля.
#
# Все виглядає як хороший початок для AchievementService.
# Основні методи - присудження та відкликання бейджа.
# Перевірка прав для ручного присудження та відкликання.
# Логіка перевірки `is_repeatable` для бейджа.
