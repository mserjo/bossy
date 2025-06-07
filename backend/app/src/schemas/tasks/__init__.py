# backend/app/src/schemas/tasks/__init__.py

"""
This package contains Pydantic schemas related to tasks, events, assignments,
completions, and reviews.
"""

import logging

logger = logging.getLogger(__name__)
logger.debug("Task schemas package initialized.")

# Example of re-exporting for easier access:
# from .task import TaskResponse, TaskCreate, TaskUpdate
# from .event import EventResponse
# from .assignment import TaskAssignmentResponse
# from .completion import TaskCompletionResponse
# from .review import TaskReviewResponse

# __all__ = [
#     "TaskResponse", "TaskCreate", "TaskUpdate",
#     "EventResponse",
#     # ... other task-related schemas
# ]
