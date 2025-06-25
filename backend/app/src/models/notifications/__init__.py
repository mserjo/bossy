# backend/app/src/models/notifications/__init__.py
# -*- coding: utf-8 -*-
"""
Ініціалізаційний файл для пакету моделей, пов'язаних зі сповіщеннями (`notifications`).

Цей файл робить доступними основні моделі сповіщень для імпорту з пакету
`backend.app.src.models.notifications`.

Приклад імпорту:
from backend.app.src.models.notifications import NotificationModel, NotificationTemplateModel

Також цей файл може використовуватися для визначення змінної `__all__`,
яка контролює, що саме експортується при використанні `from . import *`.
"""

# Імпорт конкретних моделей, пов'язаних зі сповіщеннями
from backend.app.src.models.notifications.notification import NotificationModel
from backend.app.src.models.notifications.template import NotificationTemplateModel
from backend.app.src.models.notifications.delivery import NotificationDeliveryModel

# Визначення змінної `__all__` для контролю публічного API пакету.
__all__ = [
    "NotificationModel",
    "NotificationTemplateModel",
    "NotificationDeliveryModel",
]

# TODO: Переконатися, що всі необхідні моделі з цього пакету створені та включені до `__all__`.
# На даний момент включені всі моделі, заплановані для створення в цьому пакеті.

# Цей `__init__.py` файл важливий для організації структури проекту та забезпечення
# зручного доступу до моделей, пов'язаних зі сповіщеннями.
# Він також може бути корисним для інструментів статичного аналізу або автодоповнення коду.
