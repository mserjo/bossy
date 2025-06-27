# backend/app/src/api/graphql/types/__init__.py
# -*- coding: utf-8 -*-
"""
Ініціалізаційний файл для пакету GraphQL типів.

Цей пакет містить визначення GraphQL типів (`ObjectType`, `InputType`,
`InterfaceType`, `UnionType`, `EnumType`), які використовуються у схемі.
Кожен файл у цьому каталозі зазвичай відповідає за типи, пов'язані
з певною доменною сутністю (наприклад, `user.py`, `group.py`, `task.py`).

Цей `__init__.py` може експортувати всі типи для зручного імпорту в
`schema.py` або в інші файли типів (для уникнення циклічних залежностей
можуть використовуватися forward references або `strawberry.LazyType`).
"""

# TODO: Імпортувати та експортувати GraphQL типи, коли вони будуть створені.
# Приклади:
# from backend.app.src.api.graphql.types.user import UserType, UserCreateInputType # Приклад для Strawberry
# from backend.app.src.api.graphql.types.group import GroupType
# from backend.app.src.api.graphql.types.task import TaskType
# ... і так далі для всіх файлів з типами ...

# Можна визначити __all__ для контролю над тим, що експортується:
# __all__ = (
#     "UserType",
#     "UserCreateInputType",
#     "GroupType",
#     "TaskType",
#     # ...
# )

# Також тут може бути імпортований базовий тип або інтерфейс, якщо він є.
# from backend.app.src.api.graphql.types.base import NodeInterface # Приклад

# На даному етапі, поки конкретні типи не визначені, файл може
# містити переважно документацію.
pass
