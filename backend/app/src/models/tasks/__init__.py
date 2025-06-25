# backend/app/src/models/tasks/__init__.py
# -*- coding: utf-8 -*-
"""
Ініціалізаційний файл для пакету моделей, пов'язаних із завданнями та подіями (`tasks`).

Цей файл робить доступними основні моделі завдань для імпорту з пакету
`backend.app.src.models.tasks`. Це спрощує імпорти в інших частинах проекту.

Приклад імпорту:
from backend.app.src.models.tasks import TaskModel, TaskCompletionModel

Також цей файл може використовуватися для визначення змінної `__all__`,
яка контролює, що саме експортується при використанні `from . import *`.
"""

# Імпорт конкретних моделей, пов'язаних із завданнями та подіями
from backend.app.src.models.tasks.task import TaskModel
from backend.app.src.models.tasks.assignment import TaskAssignmentModel
from backend.app.src.models.tasks.completion import TaskCompletionModel
from backend.app.src.models.tasks.dependency import TaskDependencyModel
from backend.app.src.models.tasks.proposal import TaskProposalModel
from backend.app.src.models.tasks.review import TaskReviewModel

# Визначення змінної `__all__` для контролю публічного API пакету.
__all__ = [
    "TaskModel",
    "TaskAssignmentModel",
    "TaskCompletionModel",
    "TaskDependencyModel",
    "TaskProposalModel",
    "TaskReviewModel",
]

# TODO: Переконатися, що всі необхідні моделі з цього пакету створені та включені до `__all__`.
# На даний момент включені всі моделі, заплановані для створення в цьому пакеті.

# Цей `__init__.py` файл важливий для організації структури проекту та забезпечення
# зручного доступу до моделей, пов'язаних із завданнями.
# Він також може бути корисним для інструментів статичного аналізу або автодоповнення коду.
# При визначенні зв'язків (relationships) в SQLAlchemy, якщо моделі знаходяться в різних файлах,
# правильна організація імпортів через `__init__.py` може допомогти уникнути циклічних залежностей,
# хоча SQLAlchemy часто вирішує це через рядкові посилання на імена моделей.
