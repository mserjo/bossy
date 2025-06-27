# backend/app/src/services/tasks/__init__.py
# -*- coding: utf-8 -*-
"""
Пакет сервісів для сутностей, пов'язаних із завданнями та подіями.
"""

from .task_service import TaskService, task_service
from .task_assignment_service import TaskAssignmentService, task_assignment_service
from .task_completion_service import TaskCompletionService, task_completion_service
from .task_dependency_service import TaskDependencyService, task_dependency_service
from .task_proposal_service import TaskProposalService, task_proposal_service
from .task_review_service import TaskReviewService, task_review_service

__all__ = [
    "TaskService",
    "task_service",
    "TaskAssignmentService",
    "task_assignment_service",
    "TaskCompletionService",
    "task_completion_service",
    "TaskDependencyService",
    "task_dependency_service",
    "TaskProposalService",
    "task_proposal_service",
    "TaskReviewService",
    "task_review_service",
]

from backend.app.src.config.logging import logger
logger.debug("Пакет 'services.tasks' ініціалізовано.")
