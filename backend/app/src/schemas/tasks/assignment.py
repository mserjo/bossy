# backend/app/src/schemas/tasks/assignment.py

"""
Pydantic schemas for Task Assignments.
"""

import logging
from typing import Optional
from datetime import datetime, timezone, timedelta # For examples and BaseResponseSchema

from pydantic import Field

from backend.app.src.schemas.base import BaseSchema, BaseResponseSchema
from backend.app.src.models.tasks.assignment import AssignmentStatusEnum # Import Enum from model

# Configure logger for this module
logger = logging.getLogger(__name__)

# --- Locally defined Basic Info schemas for demonstration ---
class UserBasicInfo(BaseSchema): # Inherit BaseSchema for consistent config (e.g. camelCase)
    id: int = Field(..., example=101)
    name: Optional[str] = Field(None, example="Charlie Brown")

class TaskBasicInfo(BaseSchema): # Inherit BaseSchema
    id: int = Field(..., example=1)
    name: str = Field(..., example="Review Documentation")
# --- End of local Basic Info schemas ---


# --- TaskAssignment Schemas ---

class TaskAssignmentBase(BaseSchema):
    """
    Base schema for task assignment data.
    `task_id` is typically a path parameter for API endpoints managing assignments for a specific task.
    `user_id` is the user being assigned.
    """
    user_id: int = Field(..., description="ID of the user to whom the task is assigned.", example=101)
    status: Optional[AssignmentStatusEnum] = Field(AssignmentStatusEnum.PENDING, description="Current status of this assignment.", example=AssignmentStatusEnum.PENDING)
    # assigned_by_user_id is usually set by the system (current authenticated user).
    # assigned_at is usually set by the database on creation.

class TaskAssignmentCreate(TaskAssignmentBase):
    """
    Schema for creating a new task assignment.
    `task_id` is assumed to be part of the API path (e.g., /tasks/{task_id}/assignments).
    `assigned_by_user_id` is set by the service.
    """
    # user_id is mandatory from TaskAssignmentBase.
    # status can have a default or be set explicitly.
    pass

class TaskAssignmentUpdate(BaseSchema):
    """
    Schema for updating an existing task assignment, typically only its status.
    `task_id` and `user_id` (or assignment `id`) are typically path parameters.
    """
    status: AssignmentStatusEnum = Field(..., description="New status for the assignment (e.g., 'accepted', 'in_progress').")

class TaskAssignmentResponse(BaseResponseSchema):
    """
    Schema for representing a task assignment in API responses.
    Includes 'id' (of the assignment record), 'created_at', 'updated_at'.
    """
    task: TaskBasicInfo = Field(..., description="Basic information about the assigned task.")
    user: UserBasicInfo = Field(..., description="Basic information about the assignee.")
    assigned_by: Optional[UserBasicInfo] = Field(None, description="Basic information about the user who made the assignment (if applicable).")

    status: AssignmentStatusEnum = Field(..., description="Current status of the assignment.")
    assigned_at: datetime = Field(..., description="Timestamp when the assignment was made (UTC).")
    # Note: `created_at` from BaseResponseSchema will be when the assignment record was created,
    # which is typically the same or very close to `assigned_at`.


if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- TaskAssignment Schemas --- Demonstration")

    # TaskAssignmentCreate Example
    # Assume task_id=1 from path, assigned_by_user_id=current_user.id from service
    assign_create_data = {
        "userId": 205, # camelCase for user_id
        "status": AssignmentStatusEnum.PENDING # Pass Enum member
    }
    try:
        create_schema = TaskAssignmentCreate(**assign_create_data) # type: ignore[call-arg]
        logger.info(f"TaskAssignmentCreate valid: {create_schema.model_dump(by_alias=True)}")
    except Exception as e:
        logger.error(f"Error creating TaskAssignmentCreate: {e}")

    # TaskAssignmentUpdate Example
    # Assume task_id and user_id/assignment_id are from path
    assign_update_data = {"status": AssignmentStatusEnum.IN_PROGRESS} # Pass Enum member
    update_schema = TaskAssignmentUpdate(**assign_update_data)
    logger.info(f"TaskAssignmentUpdate (partial): {update_schema.model_dump(exclude_unset=True, by_alias=True)}")

    # TaskAssignmentResponse Example
    task_info_data = {"id": 1, "name": "Review Documentation"}
    assignee_info_data = {"id": 205, "name": "Charlie Brown"}
    assigner_info_data = {"id": 10, "name": "Admin User"}

    response_data = {
        "id": 301, # ID of the TaskAssignment record
        "createdAt": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "task": task_info_data,
        "user": assignee_info_data,
        "assignedBy": assigner_info_data, # camelCase for assigned_by
        "status": AssignmentStatusEnum.IN_PROGRESS, # Pass Enum member
        "assignedAt": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat() # camelCase for assigned_at
    }
    try:
        response_schema = TaskAssignmentResponse(**response_data) # type: ignore[call-arg]
        logger.info(f"TaskAssignmentResponse: {response_schema.model_dump_json(by_alias=True, indent=2)}")
        if response_schema.task:
            logger.info(f"  Assigned Task Name: {response_schema.task.name}")
        if response_schema.user:
            logger.info(f"  Assignee Name: {response_schema.user.name}")
    except Exception as e:
        logger.error(f"Error creating TaskAssignmentResponse: {e}")
