# backend/app/src/api/graphql/mutations/gamification.py
# -*- coding: utf-8 -*-
"""
GraphQL мутації (Mutations), пов'язані з гейміфікацією.
Зазвичай це стосується адміністративних дій з налаштування рівнів, бейджів.
Самі досягнення (рівні, бейджі) користувачами заробляються автоматично.
"""

import strawberry
from typing import Optional, List

# Імпорт GraphQL типів
from backend.app.src.api.graphql.types.gamification import (
    LevelDefinitionType, LevelDefinitionCreateInput, LevelDefinitionUpdateInput,
    BadgeType, BadgeCreateInput, BadgeUpdateInput
)
from backend.app.src.api.graphql.types.base import Node

# TODO: Імпортувати сервіси
# from backend.app.src.services.gamification.level_service import LevelService
# from backend.app.src.services.gamification.badge_service import BadgeService
# from backend.app.src.core.dependencies import get_current_group_admin_for_group_id

@strawberry.type
class GamificationMutations:
    """
    Клас, що групує GraphQL мутації для налаштувань гейміфікації.
    Доступно адміністраторам груп.
    """

    # --- Мутації для налаштувань рівнів (LevelDefinition) ---
    @strawberry.mutation(description="Створити нове визначення рівня в групі.")
    async def create_level_definition(self, info: strawberry.Info, input: LevelDefinitionCreateInput) -> Optional[LevelDefinitionType]:
        # context = info.context
        # current_admin = context.current_user # Потрібна перевірка, що це адмін групи input.group_id
        # group_db_id = Node.decode_id_to_int(input.group_id, "GroupType")
        #
        # level_service = LevelService(context.db_session)
        # new_level_def = await level_service.create_level_config_graphql(
        #     level_create_data=input, group_id=group_db_id, actor_id=current_admin.id
        # )
        # return LevelDefinitionType.from_orm(new_level_def) if new_level_def else None
        raise NotImplementedError("Створення визначення рівня ще не реалізовано.")

    @strawberry.mutation(description="Оновити існуюче визначення рівня в групі.")
    async def update_level_definition(self, info: strawberry.Info, id: strawberry.ID, input: LevelDefinitionUpdateInput) -> Optional[LevelDefinitionType]:
        # context = info.context
        # # Перевірка прав адміна групи
        # level_def_db_id = Node.decode_id_to_int(id, "LevelDefinitionType")
        # level_service = LevelService(context.db_session)
        # # Сервіс має перевірити, що level_def_db_id належить групі, де користувач адмін
        # updated_level_def = await level_service.update_level_config_graphql(
        #     level_config_id=level_def_db_id, level_update_data=input, actor_id=current_user.id
        # )
        # return LevelDefinitionType.from_orm(updated_level_def) if updated_level_def else None
        raise NotImplementedError("Оновлення визначення рівня ще не реалізовано.")

    @strawberry.mutation(description="Видалити визначення рівня з групи.")
    async def delete_level_definition(self, info: strawberry.Info, id: strawberry.ID) -> bool:
        # context = info.context
        # # Перевірка прав адміна групи
        # level_def_db_id = Node.decode_id_to_int(id, "LevelDefinitionType")
        # level_service = LevelService(context.db_session)
        # success = await level_service.delete_level_config_graphql(level_config_id=level_def_db_id, actor_id=current_user.id)
        # return success
        raise NotImplementedError("Видалення визначення рівня ще не реалізовано.")

    # --- Мутації для визначень бейджів (BadgeDefinition) ---
    @strawberry.mutation(description="Створити новий бейдж (визначення) в групі.")
    async def create_badge_definition(self, info: strawberry.Info, input: BadgeCreateInput) -> Optional[BadgeType]:
        # context = info.context
        # # Перевірка прав адміна групи input.group_id
        # group_db_id = Node.decode_id_to_int(input.group_id, "GroupType")
        # badge_service = BadgeService(context.db_session)
        # new_badge = await badge_service.create_badge_graphql(
        #     badge_create_data=input, group_id=group_db_id, actor_id=current_user.id
        # )
        # return BadgeType.from_orm(new_badge) if new_badge else None
        raise NotImplementedError("Створення визначення бейджа ще не реалізовано.")

    @strawberry.mutation(description="Оновити існуючий бейдж (визначення) в групі.")
    async def update_badge_definition(self, info: strawberry.Info, id: strawberry.ID, input: BadgeUpdateInput) -> Optional[BadgeType]:
        # context = info.context
        # # Перевірка прав адміна групи
        # badge_db_id = Node.decode_id_to_int(id, "BadgeType")
        # badge_service = BadgeService(context.db_session)
        # updated_badge = await badge_service.update_badge_graphql(
        #     badge_id=badge_db_id, badge_update_data=input, actor_id=current_user.id
        # )
        # return BadgeType.from_orm(updated_badge) if updated_badge else None
        raise NotImplementedError("Оновлення визначення бейджа ще не реалізовано.")

    @strawberry.mutation(description="Видалити бейдж (визначення) з групи.")
    async def delete_badge_definition(self, info: strawberry.Info, id: strawberry.ID) -> bool:
        # context = info.context
        # # Перевірка прав адміна групи
        # badge_db_id = Node.decode_id_to_int(id, "BadgeType")
        # badge_service = BadgeService(context.db_session)
        # success = await badge_service.delete_badge_graphql(badge_id=badge_db_id, actor_id=current_user.id)
        # return success
        raise NotImplementedError("Видалення визначення бейджа ще не реалізовано.")

    # Примітка: Присвоєння бейджів та рівнів користувачам зазвичай відбувається автоматично
    # на основі дій користувачів та правил, а не через прямі GraphQL мутації.
    # Якщо потрібні мутації для ручного присвоєння (наприклад, адміном), їх можна додати.

# Експорт класу для агрегації в mutations/__init__.py
__all__ = [
    "GamificationMutations",
]
