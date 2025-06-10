# backend/app/src/schemas/tasks/task.py

"""
Pydantic schemas for Tasks.
"""

import logging
from typing import Optional, List # For list of sub-tasks etc.
from datetime import datetime, timezone, timedelta # For examples and BaseResponseSchema

from pydantic import Field, HttpUrl # HttpUrl not used here, but good to have if URLs were present

from backend.app.src.schemas.base import BaseSchema, BaseMainResponseSchema
from backend.app.src.core.dicts import EventFrequency # Enum for recurrence

# Configure logger for this module
logger = logging.getLogger(__name__)

# --- Locally defined Basic Info schemas for demonstration ---
# (Ideally, these would be imported from their respective schema files or a shared location)
class GroupBasicInfo(BaseSchema):
    id: int = Field(..., example=1)
    name: str = Field(..., example="Household Chores")

class TaskTypeBasicInfo(BaseSchema):
    id: int = Field(..., example=1)
    code: str = Field(..., example="CHORE")
    name: str = Field(..., example="Chore")

class StatusBasicInfo(BaseSchema):
    id: int = Field(..., example=2)
    code: str = Field(..., example="IN_PROGRESS")
    name: str = Field(..., example="In Progress")

class ParentTaskBasicInfo(BaseSchema):
    id: int = Field(..., example=5)
    name: str = Field(..., example="Spring Cleaning Project")
# --- End of local Basic Info schemas ---


# --- Task Schemas ---

class TaskBase(BaseSchema):
    """Base schema for task data, common to create and update operations."""
    name: str = Field(..., min_length=3, max_length=255, description="Name or title of the task.", example="Organize Project Files")
    description: Optional[str] = Field(None, description="Detailed description of the task.", example="Organize all project-related files into a new directory structure.")
    task_type_id: int = Field(..., description="ID of the task type (from dict_task_types).", example=1)
    status_id: int = Field(..., description="ID of the task's current status (from dict_statuses).", example=1)
    points_value: Optional[int] = Field(0, ge=0, description="Points awarded or deducted for this task.", example=50)
    due_date: Optional[datetime] = Field(None, description="Optional due date and time for the task (UTC).", example=datetime.now(timezone.utc) + timedelta(days=7))
    is_recurring: Optional[bool] = Field(False, description="Is this a recurring task?")
    recurrence_frequency: Optional[EventFrequency] = Field(None, description="Frequency of recurrence if is_recurring is True.", example=EventFrequency.WEEKLY)
    recurrence_interval: Optional[int] = Field(None, ge=1, description="Interval for recurrence (e.g., every 2 if frequency is weekly).", example=1)
    parent_task_id: Optional[int] = Field(None, description="ID of the parent task, if this is a subtask.", example=None)
    state: Optional[str] = Field("active", max_length=50, description="State of the task (e.g. 'active', 'archived' - distinct from workflow status_id).", example="active") # From BaseMainModel
    notes: Optional[str] = Field(None, description="Internal notes for the task.") # From BaseMainModel

class TaskCreate(TaskBase):
    """
    Schema for creating a new task.
    `group_id` is assumed to be part of API path or context.
    `status_id` might be defaulted by the service (e.g., to an 'Open' status).
    """
    name: str = Field(..., min_length=3, max_length=255, description="Name or title of the task.") # Ensure name is mandatory on create
    task_type_id: int = Field(..., description="ID of the task type.") # Ensure type is mandatory
    status_id: Optional[int] = Field(None, description="Initial status ID for the task. If None, service may set a default (e.g., 'Open').")
    # group_id: int # If it must be in payload for some API design, make it mandatory here. Usually from path.
    pass

class TaskUpdate(BaseSchema): # Does not inherit TaskBase to make all fields truly optional
    """
    Schema for updating an existing task. All fields are optional for partial updates.
    """
    name: Optional[str] = Field(None, min_length=3, max_length=255, description="New name or title of the task.")
    description: Optional[str] = Field(None, description="New detailed description of the task.")
    task_type_id: Optional[int] = Field(None, description="New ID of the task type.")
    status_id: Optional[int] = Field(None, description="New ID of the task's current status.")
    points_value: Optional[int] = Field(None, ge=0, description="New points value for this task.")
    due_date: Optional[datetime] = Field(None, description="New due date and time for the task (UTC).")
    is_recurring: Optional[bool] = Field(None, description="Update if the task is recurring.")
    recurrence_frequency: Optional[EventFrequency] = Field(None, description="New frequency of recurrence.")
    recurrence_interval: Optional[int] = Field(None, ge=1, description="New interval for recurrence.")
    parent_task_id: Optional[int] = Field(None, description="New ID of the parent task. Use null to remove parent.")
    state: Optional[str] = Field(None, max_length=50, description="New state of the task (e.g. 'active', 'archived').")
    notes: Optional[str] = Field(None, description="Updated internal notes for the task.")


class TaskResponse(BaseMainResponseSchema):
    """
    Schema for representing a task in API responses.
    Inherits common fields from BaseMainResponseSchema (id, created_at, updated_at, deleted_at, name, description, state, notes).
    """
    # name, description, state, notes are from BaseMainResponseSchema.
    # Ensure their descriptions and examples here match or enhance the base.
    name: str = Field(..., description="Name of the task.", example="Weekly Kitchen Cleaning")
    description: Optional[str] = Field(None, description="Detailed description of the task.", example="Clean all surfaces, floor, and microwave.")
    state: Optional[str] = Field(None, description="Lifecycle state of the task (e.g., 'active', 'archived').", example="active")

    group: Optional[GroupBasicInfo] = Field(None, description="Basic information about the group this task belongs to.") # Populated by service
    task_type: Optional[TaskTypeBasicInfo] = Field(None, description="Information about the task type.") # Populated by service
    status: Optional[StatusBasicInfo] = Field(None, description="Information about the task's current workflow status.") # Populated by service

    points_value: int = Field(..., description="Points for this task.", example=50)
    due_date: Optional[datetime] = Field(None, description="Due date of the task.", example=(datetime.now(timezone.utc) + timedelta(days=3)).isoformat())
    is_recurring: bool = Field(..., description="Is this task recurring?", example=False)
    recurrence_frequency: Optional[EventFrequency] = Field(None, description="Frequency of recurrence.", example=EventFrequency.WEEKLY)
    recurrence_interval: Optional[int] = Field(None, description="Interval for recurrence.", example=1)

    parent_task: Optional[ParentTaskBasicInfo] = Field(None, description="Basic info about the parent task, if this is a subtask.") # Populated by service
    sub_task_ids: Optional[List[int]] = Field(None, description="List of IDs of subtasks.", example=[102, 103])
    # assigned_users: Optional[List[UserBasicInfo]] = Field(None, description="Users assigned to this task.") # Populated via TaskAssignment


if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- Task Schemas --- Demonstration")

    # TaskCreate Example
    task_create_data = {
        "name": "Wash the Dishes",
        "description": "Load and run the dishwasher.",
        "taskTypeId": 1, # camelCase for task_type_id
        "pointsValue": 10,
        "dueDate": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(),
        "isRecurring": False,
        "state": "active"
        # status_id is optional, service might set it to 'OPEN'
    }
    try:
        create_schema = TaskCreate(**task_create_data) # type: ignore[call-arg]
        logger.info(f"TaskCreate valid: {create_schema.model_dump(by_alias=True)}")
    except Exception as e:
        logger.error(f"Error creating TaskCreate: {e}")

    # TaskUpdate Example
    task_update_data = {"pointsValue": 15, "statusId": 2}
    update_schema = TaskUpdate(**task_update_data) # type: ignore[call-arg]
    logger.info(f"TaskUpdate (partial): {update_schema.model_dump(exclude_unset=True, by_alias=True)}")

    # TaskResponse Example
    group_info_data = {"id": 1, "name": "Household Chores"}
    task_type_info_data = {"id": 1, "code": "CHORE", "name": "Chore"}
    status_info_data = {"id": 2, "code": "IN_PROGRESS", "name": "In Progress"}
    parent_task_info_data = {"id": 5, "name": "Spring Cleaning Project"}

    response_data = {
        "id": 101,
        "createdAt": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "name": "Wash the Dishes",
        "description": "Load and run the dishwasher.",
        "state": "active",
        "notes": "Remember to use the new detergent.",
        "deletedAt": None,
        "group": group_info_data,
        "taskType": task_type_info_data,
        "status": status_info_data,
        "pointsValue": 15,
        "dueDate": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        "isRecurring": False,
        "recurrenceFrequency": None, # Example if not recurring
        "recurrenceInterval": None,
        "parentTask": parent_task_info_data,
        "subTaskIds": [102, 103]
    }
    try:
        response_schema = TaskResponse(**response_data) # type: ignore[call-arg]
        logger.info(f"TaskResponse: {response_schema.model_dump_json(by_alias=True, indent=2)}")
        if response_schema.group:
            logger.info(f"  Task group name: {response_schema.group.name}")
        if response_schema.parent_task:
            logger.info(f"  Parent task name: {response_schema.parent_task.name}")
    except Exception as e:
        logger.error(f"Error creating TaskResponse: {e}")
