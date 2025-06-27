# backend/app/src/api/graphql/scalars.py
# -*- coding: utf-8 -*-
"""
Модуль для визначення кастомних скалярних типів GraphQL (опціонально).

Стандартні скалярні типи GraphQL (`String`, `Int`, `Float`, `Boolean`, `ID`)
можуть бути недостатніми для представлення всіх типів даних.
Кастомні скаляри дозволяють визначати власні типи даних з логікою
серіалізації, десеріалізації та валідації.

Приклади кастомних скалярів:
- `DateTime`: для представлення дати та часу.
- `Date`: для представлення дати.
- `UUID`: для представлення UUID.
- `JSONString`: для представлення JSON об'єктів як рядків.
- `PositiveInt`: для цілих чисел, що більші за нуль.

Реалізація кастомних скалярів залежить від обраної GraphQL бібліотеки.
"""

# import strawberry # Приклад для Strawberry
# from typing import NewType
# from datetime import datetime, date
# import uuid
# import json

# # Приклад для Strawberry:

# # DateTime скаляр
# # Strawberry має вбудований `strawberry.scalars.Datetime` (або `datetime.datetime`),
# # але якщо потрібна кастомна логіка, можна визначити свій.
# # DateTimeScalar = strawberry.scalar(
# #     NewType("DateTimeScalar", datetime),
# #     serialize=lambda value: value.isoformat(),
# #     parse_value=lambda value: datetime.fromisoformat(value) if isinstance(value, str) else None,
# #     description="Скалярний тип для представлення дати та часу у форматі ISO."
# # )

# # Date скаляр
# # DateScalar = strawberry.scalar(
# #     NewType("DateScalar", date),
# #     serialize=lambda value: value.isoformat(),
# #     parse_value=lambda value: date.fromisoformat(value) if isinstance(value, str) else None,
# #     description="Скалярний тип для представлення дати у форматі ISO."
# # )

# # UUID скаляр
# # Strawberry має вбудований `strawberry.scalars.UUID` (або `uuid.UUID`).
# # UUIDScalar = strawberry.scalar(
# #     NewType("UUIDScalar", uuid.UUID),
# #     serialize=lambda value: str(value),
# #     parse_value=lambda value: uuid.UUID(value) if isinstance(value, str) else None,
# #     description="Скалярний тип для представлення UUID."
# # )

# # JSONString скаляр (для передачі JSON як рядка)
# # JSONScalar = strawberry.scalar(
# #     NewType("JSONScalar", object), # Може бути будь-який тип, що серіалізується в JSON
# #     serialize=lambda value: json.dumps(value),
# #     parse_value=lambda value: json.loads(value) if isinstance(value, str) else None,
# #     description="Скалярний тип для представлення JSON об'єкта як рядка."
# # )


# # Приклад для Ariadne:
# # from graphql import GraphQLScalarType, ValueNode, GraphQLError
# # from typing import Any

# # def serialize_datetime(value: Any) -> str:
# #     if isinstance(value, datetime):
# #         return value.isoformat()
# #     raise GraphQLError(f"DateTime не може серіалізувати значення: {value}")

# # def parse_datetime_value(value: Any) -> datetime:
# #     if isinstance(value, str):
# #         try:
# #             return datetime.fromisoformat(value)
# #         except ValueError:
# #             raise GraphQLError(f"Некоректний формат DateTime: {value}")
# #     raise GraphQLError(f"DateTime не може розпарсити значення: {value}")

# # def parse_datetime_literal(ast: ValueNode, variables: Any = None) -> datetime:
# #     # TODO: Перевірити тип ValueNode (StringValueNode)
# #     return parse_datetime_value(ast.value) # type: ignore

# # DateTimeScalar = GraphQLScalarType(
# #     name="DateTime",
# #     description="Скалярний тип для представлення дати та часу у форматі ISO.",
# #     serialize=serialize_datetime,
# #     parse_value=parse_datetime_value,
# #     parse_literal=parse_datetime_literal
# # )

# # Кастомні скаляри реєструються при створенні схеми.
# # Для Strawberry: schema = strawberry.Schema(..., types=[DateTimeScalar, UUIDScalar])
# # Для Ariadne: потрібно додати їх до `bindables` або передати в `make_executable_schema`.

# # На даному етапі файл є опціональним і містить лише приклади.
# # Якщо кастомні скаляри не потрібні, цей файл може бути порожнім або видаленим.
pass
