# backend/app/src/repositories/tasks/__init__.py

"""
This package contains repository classes for task-related entities.

Modules within this package will define repositories for tasks, events,
assignments, completions, reviews, etc.
"""

# Import and re-export repository classes here as they are created.
# This allows for cleaner imports from other parts of the application,
# e.g., `from app.src.repositories.tasks import TaskRepository`.

from .task_repository import TaskRepository
from .event_repository import EventRepository
from .assignment_repository import TaskAssignmentRepository
from .completion_repository import TaskCompletionRepository
# from .review_repository import TaskReviewRepository


# Define __all__ to specify which names are exported when `from .tasks import *` is used.
# This also helps linters and IDEs understand the public API of this package.
__all__ = [
    "TaskRepository",
    "EventRepository",
    "TaskAssignmentRepository",
    "TaskCompletionRepository",
    # "TaskReviewRepository",
]

# Detailed comments:
# This __init__.py file initializes the 'tasks' sub-package within the
# 'repositories' package. Its primary roles are:
#
# 1. Package Recognition:
#    It makes Python treat the 'repositories/tasks' directory as a sub-package.
#
# 2. Namespace Management:
#    It serves as a central point for importing and re-exporting repository
#    classes defined in other modules within this sub-package. This simplifies
#    access for other application layers.
#
# 3. Public API Definition (`__all__`):
#    The `__all__` list explicitly declares which symbols are part of the public
#    interface of this sub-package.
#
# This structure promotes a clean and organized data access layer for
# task-related components.
