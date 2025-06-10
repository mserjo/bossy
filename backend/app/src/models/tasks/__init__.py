# backend/app/src/models/tasks/__init__.py

"""
This package contains SQLAlchemy models related to tasks, events, assignments,
completions, and reviews.
"""

import logging

logger = logging.getLogger(__name__)
logger.debug("Task models package initialized.")

# Example of re-exporting for easier access:
# from .task import Task
# from .event import Event
# from .assignment import TaskAssignment
# from .completion import TaskCompletion
# from .review import TaskReview

# __all__ = [
#     "Task",
#     "Event",
#     "TaskAssignment",
#     "TaskCompletion",
#     "TaskReview",
# ]
