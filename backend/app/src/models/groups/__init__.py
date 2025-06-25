# backend/app/src/models/groups/__init__.py
# -*- coding: utf-8 -*-
"""
Ініціалізаційний файл для пакету моделей, пов'язаних з групами (`groups`).

Цей файл робить доступними основні моделі груп для імпорту з пакету
`backend.app.src.models.groups`. Це спрощує імпорти в інших частинах проекту.

Приклад імпорту:
from backend.app.src.models.groups import GroupModel, GroupMembershipModel

Також цей файл може використовуватися для визначення змінної `__all__`,
яка контролює, що саме експортується при використанні `from . import *`.
"""

# Імпорт конкретних моделей, пов'язаних з групами
from backend.app.src.models.groups.group import GroupModel
from backend.app.src.models.groups.settings import GroupSettingsModel
from backend.app.src.models.groups.membership import GroupMembershipModel
from backend.app.src.models.groups.invitation import GroupInvitationModel
from backend.app.src.models.groups.template import GroupTemplateModel
from backend.app.src.models.groups.poll import PollModel
from backend.app.src.models.groups.poll_option import PollOptionModel
from backend.app.src.models.groups.poll_vote import PollVoteModel

# Визначення змінної `__all__` для контролю публічного API пакету.
__all__ = [
    "GroupModel",
    "GroupSettingsModel",
    "GroupMembershipModel",
    "GroupInvitationModel",
    "GroupTemplateModel",
    "PollModel",
    "PollOptionModel",
    "PollVoteModel",
]

# TODO: Переконатися, що всі необхідні моделі з цього пакету створені та включені до `__all__`.
# На даний момент включені всі моделі, заплановані для створення в цьому пакеті.

# Цей `__init__.py` файл важливий для організації структури проекту та забезпечення
# зручного доступу до моделей, пов'язаних з групами.
# Він також може бути корисним для інструментів статичного аналізу або автодоповнення коду.
# При визначенні зв'язків (relationships) в SQLAlchemy, якщо моделі знаходяться в різних файлах,
# правильна організація імпортів через `__init__.py` може допомогти уникнути циклічних залежностей,
# хоча SQLAlchemy часто вирішує це через рядкові посилання на імена моделей.
