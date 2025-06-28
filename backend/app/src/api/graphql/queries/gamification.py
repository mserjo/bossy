# backend/app/src/api/graphql/queries/gamification.py
# -*- coding: utf-8 -*-
"""
GraphQL запити (Queries), пов'язані з гейміфікацією.
"""

import strawberry
from typing import Optional, List

# Імпорт GraphQL типів
from backend.app.src.api.graphql.types.gamification import (
    LevelDefinitionType, UserLevelType, BadgeType, UserAchievementType, UserGroupRatingEntryType
)
from backend.app.src.api.graphql.types.base import Node

# TODO: Імпортувати сервіси
# from backend.app.src.services.gamification.level_service import LevelService
# from backend.app.src.services.gamification.user_level_service import UserLevelService
# from backend.app.src.services.gamification.badge_service import BadgeService
# from backend.app.src.services.gamification.achievement_service import AchievementService
# from backend.app.src.services.gamification.rating_service import RatingService
# from backend.app.src.core.dependencies import get_current_active_user

@strawberry.input
class GamificationQueryArgsBase: # Базові аргументи для запитів у контексті групи
    group_id: strawberry.ID

@strawberry.input
class PaginatedQueryArgs(GamificationQueryArgsBase):
    page: Optional[int] = strawberry.field(default=1)
    page_size: Optional[int] = strawberry.field(default=20)

@strawberry.type
class GamificationQueries:
    """
    Клас, що групує GraphQL запити, пов'язані з гейміфікацією.
    """

    # --- Рівні ---
    @strawberry.field(description="Отримати список налаштувань рівнів для групи.")
    async def level_definitions_in_group(self, info: strawberry.Info, group_id: strawberry.ID) -> List[LevelDefinitionType]:
        # context = info.context
        # current_user = context.current_user # Потрібен для перевірки членства в групі
        # group_db_id = Node.decode_id_to_int(group_id, "GroupType")
        # level_service = LevelService(context.db_session)
        # # Перевірка доступу
        # configs = await level_service.get_level_configs_for_group(group_id=group_db_id)
        # return [LevelDefinitionType.from_orm(c) for c in configs]
        return [] # Заглушка

    @strawberry.field(description="Отримати поточний рівень та прогрес поточного користувача в групі.")
    async def my_level_in_group(self, info: strawberry.Info, group_id: strawberry.ID) -> Optional[UserLevelType]:
        # context = info.context
        # current_user = context.current_user
        # if not current_user: return None
        # group_db_id = Node.decode_id_to_int(group_id, "GroupType")
        # user_level_service = UserLevelService(context.db_session)
        # data = await user_level_service.get_user_level_and_progress(user_id=current_user.id, group_id=group_db_id)
        # return UserLevelType.from_pydantic(data) if data else None # Припускаючи, що сервіс повертає Pydantic схему
        return None # Заглушка

    @strawberry.field(description="Отримати рівень та прогрес конкретного користувача в групі.")
    async def user_level_in_group(self, info: strawberry.Info, user_id: strawberry.ID, group_id: strawberry.ID) -> Optional[UserLevelType]:
        # context = info.context
        # # Перевірка доступу (наприклад, чи є поточний користувач членом групи)
        # user_db_id = Node.decode_id_to_int(user_id, "UserType")
        # group_db_id = Node.decode_id_to_int(group_id, "GroupType")
        # user_level_service = UserLevelService(context.db_session)
        # data = await user_level_service.get_user_level_and_progress(user_id=user_db_id, group_id=group_db_id)
        # return UserLevelType.from_pydantic(data) if data else None
        return None # Заглушка

    # --- Бейджі та Досягнення ---
    @strawberry.field(description="Отримати список всіх доступних бейджів у групі.")
    async def badges_in_group(self, info: strawberry.Info, args: PaginatedQueryArgs) -> List[BadgeType]: # TODO: Connection
        # context = info.context
        # group_db_id = Node.decode_id_to_int(args.group_id, "GroupType")
        # badge_service = BadgeService(context.db_session)
        # badges_data = await badge_service.get_badges_for_group(group_id=group_db_id, skip=(args.page-1)*args.page_size, limit=args.page_size)
        # return [BadgeType.from_orm(b) for b in badges_data.get("badges", [])]
        return [] # Заглушка

    @strawberry.field(description="Отримати досягнення (зароблені бейджі) поточного користувача в групі.")
    async def my_achievements_in_group(self, info: strawberry.Info, args: PaginatedQueryArgs) -> List[UserAchievementType]: # TODO: Connection
        # context = info.context
        # current_user = context.current_user
        # if not current_user: return []
        # group_db_id = Node.decode_id_to_int(args.group_id, "GroupType")
        # achievement_service = AchievementService(context.db_session)
        # achievements_data = await achievement_service.get_user_achievements_in_group(
        #     user_id=current_user.id, group_id=group_db_id,
        #     skip=(args.page-1)*args.page_size, limit=args.page_size
        # )
        # return [UserAchievementType.from_orm(a) for a in achievements_data.get("achievements", [])]
        return [] # Заглушка

    @strawberry.field(description="Отримати досягнення (зароблені бейджі) конкретного користувача в групі.")
    async def user_achievements_in_group(self, info: strawberry.Info, user_id: strawberry.ID, args: PaginatedQueryArgs) -> List[UserAchievementType]: # TODO: Connection
        # context = info.context
        # user_db_id = Node.decode_id_to_int(user_id, "UserType")
        # group_db_id = Node.decode_id_to_int(args.group_id, "GroupType")
        # achievement_service = AchievementService(context.db_session)
        # achievements_data = await achievement_service.get_user_achievements_in_group(
        #     user_id=user_db_id, group_id=group_db_id,
        #     skip=(args.page-1)*args.page_size, limit=args.page_size
        # )
        # return [UserAchievementType.from_orm(a) for a in achievements_data.get("achievements", [])]
        return [] # Заглушка

    # --- Рейтинги ---
    @strawberry.field(description="Отримати рейтинг користувачів у групі.")
    async def group_rating(
        self, info: strawberry.Info, group_id: strawberry.ID,
        rating_type_code: str = strawberry.field(description="Код типу рейтингу (напр., 'total_score', 'tasks_completed')."),
        limit: Optional[int] = strawberry.field(default=10, description="Кількість позицій в топі.")
    ) -> List[UserGroupRatingEntryType]:
        # context = info.context
        # group_db_id = Node.decode_id_to_int(group_id, "GroupType")
        # rating_service = RatingService(context.db_session)
        # ratings = await rating_service.get_group_ratings(group_id=group_db_id, rating_type=rating_type_code, limit=limit)
        # return [UserGroupRatingEntryType.from_pydantic(r) for r in ratings] # Припускаючи, що сервіс повертає Pydantic
        return [] # Заглушка

    @strawberry.field(description="Отримати позицію поточного користувача в рейтингу групи.")
    async def my_rating_position_in_group(
        self, info: strawberry.Info, group_id: strawberry.ID,
        rating_type_code: str = strawberry.field(description="Код типу рейтингу.")
    ) -> Optional[UserGroupRatingEntryType]:
        # context = info.context
        # current_user = context.current_user
        # if not current_user: return None
        # group_db_id = Node.decode_id_to_int(group_id, "GroupType")
        # rating_service = RatingService(context.db_session)
        # position_data = await rating_service.get_user_rating_position(user_id=current_user.id, group_id=group_db_id, rating_type=rating_type_code)
        # return UserGroupRatingEntryType.from_pydantic(position_data) if position_data else None
        return None # Заглушка

__all__ = [
    "GamificationQueries",
    "GamificationQueryArgsBase",
    "PaginatedQueryArgs",
]
