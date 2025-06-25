# backend/app/src/models/system/__init__.py
# -*- coding: utf-8 -*-
"""
Ініціалізаційний файл для пакету системних моделей (`system`).

Цей файл робить доступними основні системні моделі для імпорту з пакету
`backend.app.src.models.system`. Це спрощує імпорти в інших частинах проекту.

Приклад імпорту:
from backend.app.src.models.system import SystemSettingModel, CronTaskModel

Також цей файл може використовуватися для визначення змінної `__all__`,
яка контролює, що саме експортується при використанні `from . import *`.
"""

# Імпорт конкретних системних моделей
from backend.app.src.models.system.settings import SystemSettingModel
from backend.app.src.models.system.cron import CronTaskModel
from backend.app.src.models.system.monitoring import SystemEventLogModel # , PerformanceMetricModel (якщо буде реалізована)
from backend.app.src.models.system.health import ServiceHealthStatusModel

# Визначення змінної `__all__` для контролю публічного API пакету.
# Це список рядків, що містять імена атрибутів (моделей, функцій, змінних),
# які будуть імпортовані, коли використовується `from backend.app.src.models.system import *`.
# Рекомендується явно визначати `__all__` для кращої читабельності та контролю.
__all__ = [
    "SystemSettingModel",
    "CronTaskModel",
    "SystemEventLogModel",
    # "PerformanceMetricModel", # Якщо буде додана
    "ServiceHealthStatusModel",
]

# TODO: Переконатися, що всі необхідні системні моделі створені та включені до `__all__`.
# На даний момент включені всі моделі, заплановані для створення в цьому пакеті.

# TODO: Додати коментар про важливість цього `__init__.py` для структури проекту
# та потенційної взаємодії з інструментами, такими як Alembic (хоча Alembic
# зазвичай орієнтується на `Base.metadata`).
# Цей файл забезпечує чистий та організований спосіб доступу до системних моделей.
