# backend/app/src/schemas/__init__.py
# -*- coding: utf-8 -*-
"""
Головний ініціалізаційний файл для пакету схем Pydantic (`schemas`).

Цей файл агрегує та експортує основні схеми даних з усіх підпакетів.
Це дозволяє імпортувати схеми з одного централізованого місця, наприклад:

from backend.app.src.schemas import UserSchema, GroupCreateSchema, TaskSchema

Також цей файл може використовуватися для глобального виклику `model_rebuild()`
для всіх схем, що використовують `ForwardRef`, хоча Pydantic v2
зазвичай обробляє це автоматично.
"""

# Імпорт базових схем
from backend.app.src.schemas.base import (
    BaseSchema,
    IdentifiedSchema,
    TimestampedSchema,
    AuditDatesSchema,
    BaseMainSchema,
    PaginatedResponse,
    MessageResponse,
    DetailResponse,
)

# Імпорт схем з підпакетів
from backend.app.src.schemas.auth import *
from backend.app.src.schemas.bonuses import *
from backend.app.src.schemas.dictionaries import *
from backend.app.src.schemas.files import *
from backend.app.src.schemas.gamification import *
from backend.app.src.schemas.groups import *
from backend.app.src.schemas.notifications import *
from backend.app.src.schemas.reports import *
from backend.app.src.schemas.system import *
from backend.app.src.schemas.tasks import *
from backend.app.src.schemas.teams import *

# Визначення змінної `__all__` для контролю публічного API пакету `schemas`.
# Це агрегація `__all__` з усіх підпакетів плюс базові схеми.

_base_schemas_all = [
    "BaseSchema", "IdentifiedSchema", "TimestampedSchema", "AuditDatesSchema",
    "BaseMainSchema", "PaginatedResponse", "MessageResponse", "DetailResponse",
]

# Динамічне збирання __all__ з підключених модулів
# (або можна просто скопіювати їх сюди, якщо імпорт * не використовується для __all__ в підмодулях)
# Поки що припускаємо, що __all__ визначено в кожному __init__.py підпакету.
import backend.app.src.schemas.auth as auth_schemas
import backend.app.src.schemas.bonuses as bonuses_schemas
import backend.app.src.schemas.dictionaries as dictionaries_schemas
import backend.app.src.schemas.files as files_schemas
import backend.app.src.schemas.gamification as gamification_schemas
import backend.app.src.schemas.groups as groups_schemas
import backend.app.src.schemas.notifications as notifications_schemas
import backend.app.src.schemas.reports as reports_schemas
import backend.app.src.schemas.system as system_schemas
import backend.app.src.schemas.tasks as tasks_schemas
import backend.app.src.schemas.teams as teams_schemas

__all__ = _base_schemas_all + \
    auth_schemas.__all__ + \
    bonuses_schemas.__all__ + \
    dictionaries_schemas.__all__ + \
    files_schemas.__all__ + \
    gamification_schemas.__all__ + \
    groups_schemas.__all__ + \
    notifications_schemas.__all__ + \
    reports_schemas.__all__ + \
    system_schemas.__all__ + \
    tasks_schemas.__all__ + \
    teams_schemas.__all__

# Глобальний виклик model_rebuild для всіх схем, що можуть містити ForwardRef.
# Це може бути корисним, щоб гарантувати, що всі посилання розв'язані.
# Pydantic v2 зазвичай робить це "ліниво" при першому доступі.
# Якщо виникають проблеми, цей блок можна розкоментувати та адаптувати.
#
# from pydantic import BaseModel as PydanticBaseModel_
# import inspect
#
# all_schemas_to_rebuild = []
# modules_to_scan = [
#     auth_schemas, bonuses_schemas, dictionaries_schemas, files_schemas,
#     gamification_schemas, groups_schemas, notifications_schemas,
#     reports_schemas, system_schemas, tasks_schemas, teams_schemas
# ]
#
# for module in modules_to_scan:
#     for name, obj in inspect.getmembers(module):
#         if inspect.isclass(obj) and issubclass(obj, PydanticBaseModel_) and obj is not PydanticBaseModel_:
#             # Перевірка, чи схема має ForwardRef або потребує оновлення
#             # Це складно визначити автоматично без глибокого аналізу.
#             # Простіше додати всі схеми, які потенційно можуть мати ForwardRef.
#             # Або ж, якщо Pydantic v2 справляється, то це не потрібно.
#             # if hasattr(obj, 'model_fields'): # Pydantic v2
#             #     for field_info in obj.model_fields.values():
#             #         # Проста перевірка наявності ForwardRef у анотаціях
#             #         # (потребує більш ретельної реалізації для вкладених типів)
#             #         if isinstance(field_info.annotation, str) or isinstance(field_info.annotation, ForwardRef):
#             #             all_schemas_to_rebuild.append(obj)
#             #             break
#             #         if hasattr(field_info.annotation, '__args__'): # Для Optional, List, Union
#             #             for arg_type in field_info.annotation.__args__:
#             #                 if isinstance(arg_type, str) or isinstance(arg_type, ForwardRef):
#             #                     all_schemas_to_rebuild.append(obj)
#             #                     break
#             #             if obj in all_schemas_to_rebuild: break # Вже додано
#             pass # Поки що не робимо автоматичний пошук, покладаємося на Pydantic v2

# for schema_class in all_schemas_to_rebuild:
#     try:
#         # schema_class.model_rebuild(force=True) # Для Pydantic v2
#         pass
#     except Exception as e:
#         print(f"Warning: Could not rebuild schema {schema_class.__name__} in global __init__.py: {e}")

# Фіналізація стратегії `model_rebuild`:
# Оскільки `model_rebuild()` вже викликається в `__init__.py` кожного підпакету схем
# (наприклад, `schemas/groups/__init__.py`), глобальний виклик тут, ймовірно,
# не потрібен і може бути навіть шкідливим, якщо порядок не гарантований.
# Pydantic v2 має ефективно обробляти ForwardRef, якщо всі типи імпортовані
# до моменту валідації або генерації схеми OpenAPI.
# Залишаємо цей блок закоментованим. Якщо виникнуть проблеми з нерозв'язаними
# ForwardRef на глобальному рівні, можна буде повернутися до цього питання.
# Основна мета цього файлу - агрегація та реекспорт схем.

# Цей файл є важливою частиною структури проекту, забезпечуючи єдину точку
# доступу до всіх схем даних, що використовуються для валідації API запитів/відповідей
# та взаємодії з ORM моделями.
# Це також допомагає уникнути довгих шляхів імпорту в інших частинах коду.
