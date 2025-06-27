# backend/app/src/api/graphql/context.py
# -*- coding: utf-8 -*-
"""
Модуль для визначення функції або класу для створення GraphQL контексту.

GraphQL контекст - це об'єкт, що передається в кожен GraphQL резолвер
під час виконання запиту. Він може містити корисні для резолверів об'єкти,
такі як:
- Сесія бази даних (`db_session`).
- Поточний автентифікований користувач (`current_user`).
- Екземпляри DataLoader'ів (`dataloaders`).
- Запит (`request` від FastAPI).
- Інші залежності або сервіси.

Контекст створюється для кожного GraphQL запиту.
"""

from typing import Dict, Any, Optional

from fastapi import Request
# from sqlalchemy.ext.asyncio import AsyncSession

# TODO: Імпортувати необхідні компоненти, коли вони будуть реалізовані
# from backend.app.src.api.dependencies import get_async_session, get_current_user # Приклади
# from backend.app.src.models.auth.user import UserModel # Приклад
# from backend.app.src.api.graphql.dataloaders import create_dataloaders # Приклад

# Для Strawberry, контекст часто визначається як клас:
# import strawberry
# from strawberry.fastapi import BaseContext

# @strawberry.type
# class GraphQLContext(BaseContext):
#     db_session: AsyncSession
#     current_user: Optional[UserModel]
#     dataloaders: Dict[str, Any] # 'Any' тут DataLoader
#     # Можна додати інші поля, наприклад, сам запит, якщо потрібно
#     # request: Request
#
#     def __init__(
#         self,
#         db_session: AsyncSession,
#         current_user: Optional[UserModel],
#         dataloaders: Dict[str, Any],
#         # request: Request # Якщо request потрібен в контексті
#     ):
#         super().__init__() # Для BaseContext
#         self.db_session = db_session
#         self.current_user = current_user
#         self.dataloaders = dataloaders
#         # self.request = request
#
# async def get_graphql_context(
#     # Залежності FastAPI для отримання необхідних даних
#     request: Request, # Запит FastAPI
#     # db_session: AsyncSession = Depends(get_async_session),
#     # current_user: Optional[UserModel] = Depends(get_current_user), # Може бути None, якщо не автентифікований
# ) -> GraphQLContext:
#     """
#     Асинхронна функція для створення та повернення GraphQL контексту.
#     Використовується FastAPI для ін'єкції залежностей.
#
#     Args:
#         request (Request): Об'єкт запиту FastAPI.
#         db_session (AsyncSession): Сесія бази даних.
#         current_user (Optional[UserModel]): Поточний користувач (може бути None).
#
#     Returns:
#         GraphQLContext: Об'єкт GraphQL контексту.
#     """
#     # TODO: Замінити заглушки на реальні значення
#     temp_db_session_placeholder = None # Замінити на db_session
#     temp_current_user_placeholder = None # Замінити на current_user
#
#     # Створення DataLoader'ів з поточною сесією
#     # dataloaders = create_dataloaders(db_session=temp_db_session_placeholder)
#     dataloaders_placeholder = {} # Замінити на dataloaders
#
#     return GraphQLContext(
#         db_session=temp_db_session_placeholder,
#         current_user=temp_current_user_placeholder,
#         dataloaders=dataloaders_placeholder,
#         # request=request # Якщо request потрібен в контексті
#     )


# Для Ariadne, контекст може бути простим словником або об'єктом,
# який повертається функцією `context_value_provider`.
# async def get_ariadne_context_value(request: Request, data: Any) -> Dict[str, Any]:
#     """
#     Функція для надання значення контексту для Ariadne.
#
#     Args:
#         request (Request): Об'єкт запиту (Starlette/FastAPI).
#         data (Any): Дані, передані з Ariadne (зазвичай порожні).
#
#     Returns:
#         Dict[str, Any]: Словник, що представляє контекст.
#     """
#     # TODO: Реалізувати отримання сесії, користувача та DataLoader'ів
#     # async with get_async_session() as db_session: # Приклад отримання сесії
#     #     current_user = await get_current_user(request=request, db_session=db_session) # Приклад
#     #     dataloaders = create_dataloaders(db_session=db_session)
#     #
#     #     return {
#     #         "request": request,
#     #         "db_session": db_session,
#     #         "current_user": current_user,
#     #         "dataloaders": dataloaders,
#     #     }
#     return {"request": request} # Заглушка


# Важливо: вибір реалізації залежить від обраної GraphQL бібліотеки (Strawberry, Ariadne тощо).
# Наведений вище код є прикладом і потребує адаптації.

pass # Щоб уникнути помилки порожнього файлу.
