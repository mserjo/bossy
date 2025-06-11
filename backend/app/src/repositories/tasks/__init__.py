# backend/app/src/repositories/tasks/__init__.py
"""
Репозиторії для моделей, пов'язаних із "Завданнями", в програмі Kudos.

Цей пакет містить класи репозиторіїв для кожної моделі, що стосується
завдань/подій, їх призначень, виконань та відгуків.

Кожен репозиторій успадковує `BaseRepository` та надає спеціалізований
інтерфейс для роботи з конкретною моделлю даних.
"""

from .task_repository import TaskRepository
from .assignment_repository import TaskAssignmentRepository
from .completion_repository import TaskCompletionRepository
from .review_repository import TaskReviewRepository
# EventRepository було видалено, оскільки модель Event об'єднана з Task.

__all__ = [
    "TaskRepository",
    "TaskAssignmentRepository",
    "TaskCompletionRepository",
    "TaskReviewRepository",
]
