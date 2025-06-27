# backend/app/src/api/graphql/directives.py
# -*- coding: utf-8 -*-
"""
Модуль для визначення кастомних GraphQL директив (опціонально).

GraphQL директиви дозволяють додавати декларативну логіку до схеми.
Вони можуть використовуватися для:
- Перевірки прав доступу (наприклад, `@isAuthenticated`, `@hasRole(role: "admin")`).
- Форматування даних (наприклад, `@uppercase`, `@dateFormat(format: "YYYY-MM-DD")`).
- Контролю кешування.
- Інших аспектів модифікації поведінки полів або типів.

Реалізація директив залежить від обраної GraphQL бібліотеки (Strawberry, Ariadne).
"""

# Приклад для Strawberry:
# import strawberry
# from strawberry.directive import DirectiveLocation
# from typing import Any, Callable, Optional
# from strawberry.types import Info
# from backend.app.src.api.graphql.context import GraphQLContext # Потрібен для доступу до current_user

# @strawberry.directive(
#     locations=[DirectiveLocation.FIELD_DEFINITION, DirectiveLocation.OBJECT],
#     description="Перевіряє, чи користувач автентифікований."
# )
# class IsAuthenticated:
#     message: Optional[str] = "Користувач не автентифікований."
#
#     # Strawberry викликає `resolve` для директив на полях
#     # Для директив на об'єктах, логіка може бути складнішою і вимагати
#     # обробки на рівні розширення схеми (SchemaExtension).
#     # Тут наведено спрощений приклад для поля.
#
#     # def resolve(self, next_: Callable, source: Any, info: Info[GraphQLContext, Any], **kwargs: Any) -> Any:
#     #     # TODO: Перевірити, чи є current_user в контексті і чи він не None
#     #     context: GraphQLContext = info.context
#     #     if not context.current_user:
#     #         # TODO: Замість простого винятку, краще повернути помилку GraphQL
#     #         # або модифікувати результат, залежно від вимог.
#     #         # Strawberry може автоматично обробляти винятки і перетворювати їх на помилки GraphQL.
#     #         raise PermissionError(self.message or "Доступ заборонено.") # Приклад
#     #
#     #     return next_(source, info, **kwargs) # Викликати наступний резолвер у ланцюжку

# @strawberry.directive(
#     locations=[DirectiveLocation.FIELD_DEFINITION],
#     description="Перетворює текстове поле на верхній регістр."
# )
# class Uppercase:
#     # def resolve(self, next_: Callable, source: Any, info: Info, **kwargs: Any) -> Any:
#     #     result = next_(source, info, **kwargs)
#     #     if isinstance(result, str):
#     #         return result.upper()
#     #     # TODO: Додати обробку для асинхронних резолверів, якщо result є awaitable
#     #     return result
#     pass


# Приклад для Ariadne:
# from typing import Any, Callable
# from graphql import GraphQLSchema, default_field_resolver
# from ariadne import SchemaDirectiveVisitor # Для старіших версій Ariadne
# from ariadne.contrib.directives importเย็น Directive # Для новіших версій

# class IsAuthenticatedDirective(Directive): # Для новіших версій Ariadne
#     async def resolve(self, next_directive: Callable, obj: Any, info: GraphQLResolveInfo, **kwargs):
#         context = info.context
#         if not context.get("current_user"):
#             # Повернути помилку GraphQL або викликати виняток
#             raise GraphQLError("Користувач не автентифікований.")
#         return await next_directive(obj, info, **kwargs)

# class UppercaseDirective(SchemaDirectiveVisitor): # Для старіших версій Ariadne
#     def visit_field_definition(self, field, object_type):
#         original_resolver = field.resolve or default_field_resolver
#
#         async def resolve_uppercase(obj, info, **kwargs):
#             result = await original_resolver(obj, info, **kwargs)
#             if isinstance(result, str):
#                 return result.upper()
#             return result
#
#         field.resolve = resolve_uppercase
#         return field

# Директиви реєструються при створенні схеми.
# Для Strawberry: schema = strawberry.Schema(..., directives=[IsAuthenticated, Uppercase])
# Для Ariadne: schema = make_executable_schema(type_defs, ..., directives={"isAuthenticated": IsAuthenticatedDirective})

# На даному етапі файл є опціональним і містить лише приклади.
# Якщо кастомні директиви не потрібні, цей файл може бути порожнім або видаленим.
pass
