# backend/app/src/repositories/tasks/__init__.py
"""
Репозиторії для моделей, пов'язаних із "Завданнями", в програмі Kudos.

Цей пакет містить класи репозиторіїв для кожної моделі, що стосується
завдань/подій, їх призначень, виконань та відгуків.

Кожен репозиторій успадковує `BaseRepository` та надає спеціалізований
інтерфейс для роботи з конкретною моделлю даних.
"""

from backend.app.src.repositories.tasks.task_repository import TaskRepository
from backend.app.src.repositories.tasks.assignment_repository import TaskAssignmentRepository
from backend.app.src.repositories.tasks.completion_repository import TaskCompletionRepository
from backend.app.src.repositories.tasks.review_repository import TaskReviewRepository
# EventRepository було видалено, оскільки модель Event об'єднана з Task.

__all__ = [
    "TaskRepository",
    "TaskAssignmentRepository",
    "TaskCompletionRepository",
    "TaskReviewRepository",
]
