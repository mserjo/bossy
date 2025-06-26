# backend/app/src/repositories/tasks/__init__.py
# -*- coding: utf-8 -*-
"""
Пакет репозиторіїв для сутностей, пов'язаних із завданнями та подіями.
"""

from .task import TaskRepository, task_repository
from .assignment import TaskAssignmentRepository, task_assignment_repository
from .completion import TaskCompletionRepository, task_completion_repository
from .dependency import TaskDependencyRepository, task_dependency_repository
from .proposal import TaskProposalRepository, task_proposal_repository
from .review import TaskReviewRepository, task_review_repository

__all__ = [
    "TaskRepository",
    "task_repository",
    "TaskAssignmentRepository",
    "task_assignment_repository",
    "TaskCompletionRepository",
    "task_completion_repository",
    "TaskDependencyRepository",
    "task_dependency_repository",
    "TaskProposalRepository",
    "task_proposal_repository",
    "TaskReviewRepository",
    "task_review_repository",
]

from backend.app.src.config.logging import logger
logger.debug("Пакет 'repositories.tasks' ініціалізовано.")
