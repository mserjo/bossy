# backend/app/src/models/tasks/__init__.py
# -*- coding: utf-8 -*-
"""Пакет моделей SQLAlchemy для сутностей, пов'язаних із завданнями та подіями.

Цей пакет містить моделі даних для представлення:
- Завдань (`TaskModel`).
- Подій (`EventModel`), які можуть розглядатися як специфічний тип завдань або окрема сутність.
- Призначень завдань користувачам (`TaskAssignmentModel`).
- Записів про виконання завдань (`TaskCompletionModel`).
- Відгуків або рецензій на виконання завдань (`TaskReviewModel`).

Моделі з цього пакету експортуються для використання в сервісному шарі,
API ендпоінтах та інших частинах додатку, що реалізують логіку управління
завданнями та подіями.
"""

# Імпорт моделей з відповідних файлів цього пакету.
from backend.app.src.models.tasks.task import Task
from backend.app.src.models.tasks.event import Event
from backend.app.src.models.tasks.assignment import TaskAssignment
from backend.app.src.models.tasks.completion import TaskCompletion
from backend.app.src.models.tasks.review import TaskReview
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

# Визначаємо, які символи будуть експортовані при використанні `from backend.app.src.models.tasks import *`.
__all__ = [
    "Task",
    "Event",
    "TaskAssignment",
    "TaskCompletion",
    "TaskReview",
]

logger.debug("Ініціалізація пакету моделей `tasks`...")

# Коментар щодо можливого розширення:
# В майбутньому сюди можуть бути додані інші моделі, пов'язані із завданнями,
# наприклад, для залежностей між завданнями (TaskDependencyModel)
# або для тегування завдань (TaskTagModel).
