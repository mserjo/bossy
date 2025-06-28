# backend/app/src/models/dictionaries/__init__.py
# -*- coding: utf-8 -*-
"""
Ініціалізаційний файл для пакету моделей довідників (`dictionaries`).

Цей файл робить доступними основні моделі довідників для імпорту з пакету
`backend.app.src.models.dictionaries`. Це спрощує імпорти в інших частинах проекту.

Приклад імпорту:
from backend.app.src.models.dictionaries import StatusModel, UserRoleModel

Також цей файл може використовуватися для визначення змінної `__all__`,
яка контролює, що саме експортується при використанні `from . import *`.
"""

# Імпорт базової моделі для довідників, якщо вона потрібна для прямого використання
# або для типізації в цьому пакеті. Зазвичай вона використовується всередині конкретних моделей.
from backend.app.src.models.dictionaries.base import BaseDictModel

# Імпорт конкретних моделей довідників
from backend.app.src.models.dictionaries.status import StatusModel
from backend.app.src.models.dictionaries.user_role import UserRoleModel
from backend.app.src.models.dictionaries.user_type import UserTypeModel # Додано UserTypeModel
from backend.app.src.models.dictionaries.group_type import GroupTypeModel
from backend.app.src.models.dictionaries.task_type import TaskTypeModel
from backend.app.src.models.dictionaries.bonus_type import BonusTypeModel
from backend.app.src.models.dictionaries.integration import IntegrationModel

# Визначення змінної `__all__` для контролю публічного API пакету.
# Це список рядків, що містять імена атрибутів (моделей, функцій, змінних),
# які будуть імпортовані, коли використовується `from backend.app.src.models.dictionaries import *`.
# Рекомендується явно визначати `__all__` для кращої читабельності та контролю.
__all__ = [
    "BaseDictModel",  # Експортуємо базову модель довідника, може бути корисною
    "StatusModel",
    "UserRoleModel",
    "UserTypeModel", # Додано UserTypeModel
    "GroupTypeModel",
    "TaskTypeModel",
    "BonusTypeModel",
    "IntegrationModel",
]

# TODO: Переконатися, що всі необхідні моделі довідників створені та включені до `__all__`.
# UserTypeModel додано.

# TODO: Додати коментар про те, що цей `__init__.py` також важливий для правильної роботи Alembic,
# якщо конфігурація Alembic (`env.py`) сканує моделі шляхом імпорту пакетів.
# Хоча зазвичай `env.py` імпортує `Base` з `models.base` та метадані з нього.
# Але для чистоти структури та можливості імпорту всіх моделей довідників з одного місця,
# цей файл є важливим.
