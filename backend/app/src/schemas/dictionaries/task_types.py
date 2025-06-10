# backend/app/src/schemas/dictionaries/task_types.py

"""
Pydantic schemas for TaskType dictionary entries.
"""

import logging
from typing import Optional # For optional custom fields if any
from datetime import datetime, timezone # For example values in __main__ and BaseResponseSchema

from pydantic import Field
from backend.app.src.schemas.dictionaries.base_dict import (
    DictionaryBase,
    # DictionaryCreate as BaseDictionaryCreate, # Not directly used if TaskTypeCreate inherits TaskTypeBase
    # DictionaryUpdate as BaseDictionaryUpdate, # Not directly used if TaskTypeUpdate inherits TaskTypeBase
    DictionaryResponse as BaseDictionaryResponse
)

# Configure logger for this module
logger = logging.getLogger(__name__)

# --- TaskType Schemas ---

class TaskTypeBase(DictionaryBase):
    """Base schema for TaskType, inherits all fields from DictionaryBase."""
    # Example of custom fields if TaskType model had them:
    # awards_points_by_default: Optional[bool] = Field(None,
    #                                                  description="Does this task type generally award points?",
    #                                                  example=True)
    # default_points_value: Optional[int] = Field(None,
    #                                             description="Default points for tasks of this type.",
    #                                             example=10)
    pass

class TaskTypeCreate(TaskTypeBase):
    """
    Schema for creating a new TaskType.
    Inherits fields from TaskTypeBase. 'code' and 'name' are effectively required.
    """
    pass

class TaskTypeUpdate(TaskTypeBase):
    """
    Schema for updating an existing TaskType.
    All fields from TaskTypeBase are made optional here for partial updates.
    """
    code: Optional[str] = Field(None, min_length=1, max_length=100, description="Unique code or short identifier.")
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Human-readable name.")
    description: Optional[str] = Field(None)
    state: Optional[str] = Field(None, max_length=50)
    is_default: Optional[bool] = Field(None)
    display_order: Optional[int] = Field(None)
    notes: Optional[str] = Field(None)
    # If custom fields were in TaskTypeBase:
    # awards_points_by_default: Optional[bool] = Field(None)
    # default_points_value: Optional[int] = Field(None)


class TaskTypeResponse(BaseDictionaryResponse):
    """
    Schema for representing a TaskType in API responses.
    Inherits all fields from BaseDictionaryResponse.
    Add any TaskType-specific response fields here if TaskTypeBase had custom fields.
    """
    # If custom fields were in TaskTypeBase and should be in response:
    # awards_points_by_default: Optional[bool] = Field(None, description="Awards points by default?")
    # default_points_value: Optional[int] = Field(None, description="Default points value.")
    pass


if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- TaskType Schemas (Dictionary) --- Demonstration")

    # TaskTypeCreate Example
    type_create_data = {
        "code": "CHORE_DAILY",
        "name": "Daily Chore",
        "description": "A task that needs to be done daily.",
        "state": "active",
        # "awardsPointsByDefault": True, # camelCase alias example if field existed
        # "defaultPointsValue": 5
    }
    try:
        type_create_schema = TaskTypeCreate(**type_create_data)
        logger.info(f"TaskTypeCreate valid: {type_create_schema.model_dump(by_alias=True)}")
    except Exception as e:
        logger.error(f"Error creating TaskTypeCreate: {e}")

    # TaskTypeUpdate Example
    type_update_data = {"description": "A recurring daily task for household members."}
    type_update_schema = TaskTypeUpdate(**type_update_data)
    logger.info(f"TaskTypeUpdate (partial): {type_update_schema.model_dump(exclude_unset=True, by_alias=True)}")

    # TaskTypeResponse Example
    type_response_data = {
        "id": 1,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "code": "WORK_PROJECT_TASK",
        "name": "Project Task",
        "description": "A task related to a specific work project.",
        "state": "active",
        "isDefault": False,
        "displayOrder": 1,
        # "awardsPointsByDefault": True, # If field existed
        # "defaultPointsValue": 25
    }
    try:
        type_response_schema = TaskTypeResponse(**type_response_data) # type: ignore[call-arg]
        logger.info(f"TaskTypeResponse: {type_response_schema.model_dump_json(by_alias=True, indent=2)}")
    except Exception as e:
        logger.error(f"Error creating TaskTypeResponse: {e}")
