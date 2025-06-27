# backend/app/src/api/graphql/dataloaders.py
# -*- coding: utf-8 -*-
"""
Модуль для визначення класів DataLoader.

DataLoaders використовуються для ефективного пакетного завантаження пов'язаних даних
та вирішення проблеми N+1 запитів до бази даних в межах одного GraphQL запиту.
Кожен DataLoader зазвичай відповідає за завантаження певного типу даних
(наприклад, `UserLoaderById`, `GroupLoaderByUserId`).

Екземпляри DataLoader створюються для кожного запиту і передаються через GraphQL контекст.
Бібліотека `aiodataloader` є популярним вибором для асинхронних DataLoader.
"""

from typing import List, Any, Dict
from collections import defaultdict
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.future import select
#
# from backend.app.src.models.auth.user import UserModel # Приклад
# from backend.app.src.models.groups.group import GroupModel # Приклад

# TODO: Використовувати aiodataloader або аналогічну бібліотеку.
# from dataloader import DataLoader # з aiodataloader

# class BaseDataLoader(DataLoader):
#     """
#     Базовий клас для DataLoader з загальною логікою, якщо потрібно.
#     """
#     def __init__(self, db_session: AsyncSession, cache_key_prefix: str = None, **kwargs):
#         super().__init__(**kwargs)
#         self.db_session = db_session
#         # TODO: Можна додати логіку кешування, якщо потрібно, використовуючи cache_map
#         # self.cache_map = {} # Або використовувати вбудований кеш DataLoader
#         if cache_key_prefix:
#             self.cache_key_prefix = cache_key_prefix


# TODO: Приклади DataLoader. Їх потрібно буде реалізувати для конкретних моделей.

# class UserLoaderById(BaseDataLoader):
#     """
#     Завантажує користувачів за їх ID.
#     """
#     cache_key_prefix = "user_by_id"
#
#     async def batch_load_fn(self, keys: List[Any]) -> List[UserModel | None]:
#         """
#         Асинхронно завантажує користувачів за списком ID.
#
#         Args:
#             keys (List[Any]): Список ID користувачів.
#
#         Returns:
#             List[UserModel | None]: Список моделей користувачів, що відповідає порядку ключів.
#                                     Якщо користувач не знайдений, повертається None для цього ключа.
#         """
#         async with self.db_session.begin(): # Використовуємо сесію, передану в конструктор
#             stmt = select(UserModel).where(UserModel.id.in_(keys))
#             result = await self.db_session.execute(stmt)
#             users_by_id: Dict[Any, UserModel] = {user.id: user for user in result.scalars().all()}
#
#         # Повертаємо користувачів у тому ж порядку, що й ключі
#         return [users_by_id.get(key) for key in keys]

# class GroupsByUserIdLoader(BaseDataLoader):
#     """
#     Завантажує групи, до яких належить користувач.
#     Оскільки один користувач може належати до багатьох груп,
#     цей DataLoader повертатиме список груп для кожного ID користувача.
#     """
#     cache_key_prefix = "groups_by_user_id"
#
#     async def batch_load_fn(self, user_ids: List[Any]) -> List[List[GroupModel]]:
#         """
#         Асинхронно завантажує списки груп для кожного ID користувача.
#
#         Args:
#             user_ids (List[Any]): Список ID користувачів.
#
#         Returns:
#             List[List[GroupModel]]: Список списків моделей груп.
#                                      Кожен внутрішній список відповідає групам одного користувача.
#         """
#         # TODO: Реалізувати логіку завантаження груп на основі user_ids.
#         # Це може включати JOIN з таблицею членства в групах (GroupMembershipModel).
#         # Приклад спрощеної логіки (потребує адаптації):
#         #
#         # from backend.app.src.models.groups.membership import GroupMembershipModel # Приклад
#         #
#         # async with self.db_session.begin():
#         #     stmt = (
#         #         select(GroupModel, GroupMembershipModel.user_id)
#         #         .join(GroupMembershipModel, GroupModel.id == GroupMembershipModel.group_id)
#         #         .where(GroupMembershipModel.user_id.in_(user_ids))
#         #     )
#         #     result = await self.db_session.execute(stmt)
#         #     groups_by_user_id = defaultdict(list)
#         #     for group, user_id_assoc in result.all():
#         #         groups_by_user_id[user_id_assoc].append(group)
#         #
#         # return [groups_by_user_id.get(user_id, []) for user_id in user_ids]
#         pass # Заглушка

# def create_dataloaders(db_session: AsyncSession) -> Dict[str, Any]: # 'Any' тут DataLoader
#     """
#     Фабрична функція для створення та повернення словника всіх DataLoader'ів.
#     Цей словник потім додається до GraphQL контексту.
#
#     Args:
#         db_session (AsyncSession): Сесія бази даних, яка буде використовуватися DataLoader'ами.
#
#     Returns:
#         Dict[str, Any]: Словник, де ключі - назви DataLoader'ів, а значення - їх екземпляри.
#     """
#     return {
#         "user_loader_by_id": UserLoaderById(db_session=db_session),
#         "groups_by_user_id_loader": GroupsByUserIdLoader(db_session=db_session),
#         # TODO: Додати інші DataLoader'и тут
#     }

# На даному етапі файл містить структуру та приклади.
# Конкретні DataLoader'и будуть реалізовані пізніше.
pass
