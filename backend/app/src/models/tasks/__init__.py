# backend/app/src/models/tasks/__init__.py
"""
Пакет моделей SQLAlchemy для сутностей, пов'язаних із "Завданнями".

Цей пакет містить моделі для представлення завдань (або подій),
призначень завдань користувачам, записів про виконання завдань
та відгуків на завдання в програмі Kudos.

Моделі експортуються для зручного доступу з інших частин програми.
"""

from .task import Task
from .assignment import TaskAssignment
from .completion import TaskCompletion
from .review import TaskReview
# Модель Event була інтегрована в модель Task.
# Якщо в майбутньому Event знову стане окремою сутністю з власною таблицею,
# її потрібно буде імпортувати та експортувати тут.
# from .event import Event # Наразі закоментовано

__all__ = [
    "Task",
    "TaskAssignment",
    "TaskCompletion",
    "TaskReview",
    # "Event", # Наразі закоментовано
]

# Майбутні моделі, пов'язані із завданнями (наприклад, TaskDependency, TaskTag),
# також можуть бути додані сюди для експорту.
