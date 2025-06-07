# backend/app/src/schemas/tasks/completion.py

"""
Pydantic schemas for Task Completions.
"""

import logging
from typing import Optional
from datetime import datetime, timezone, timedelta # For examples and BaseResponseSchema

from pydantic import Field

from backend.app.src.schemas.base import BaseSchema, BaseResponseSchema

# Configure logger for this module
logger = logging.getLogger(__name__)

# --- Locally defined Basic Info schemas for demonstration ---
class UserBasicInfo(BaseSchema): # Inherit BaseSchema for consistent config (e.g. camelCase)
    id: int = Field(..., example=101)
    name: Optional[str] = Field(None, example="Alice")

class TaskBasicInfo(BaseSchema): # Inherit BaseSchema
    id: int = Field(..., example=1)
    name: str = Field(..., example="Generate Q1 Report")
# --- End of local Basic Info schemas ---


# --- TaskCompletion Schemas ---

class TaskCompletionBase(BaseSchema):
    """
    Base schema for task completion data.
    `task_id` and `user_id` (completer) are usually context-derived or path parameters.
    """
    # completed_at is often server-set when the user submits the completion.
    # If user can backdate, then it can be in a Create schema.
    # For now, assuming server sets completed_at on creation of the record.
    verification_notes: Optional[str] = Field(None, description="Notes from the user submitting the completion.", example="All steps completed as per instructions.")
    # awarded_points: Optional[int] = Field(None, ge=0, description="Points to request or suggest for this completion. Final points set by verifier.") # User typically doesn't set awarded_points

class TaskCompletionCreate(TaskCompletionBase):
    """
    Schema for a user to mark a task as completed.
    `task_id` from path, `user_id` from authenticated user.
    May include minimal fields like notes from the user.
    """
    # verification_notes can be used by the user to add comments upon completion.
    pass

class TaskCompletionVerify(BaseSchema):
    """
    Schema for an admin/verifier to verify or reject a task completion.
    `task_completion_id` is typically a path parameter.
    """
    is_verified: bool = Field(..., description="Set to true to verify, false to reject (or use a separate 'reject' endpoint/status).")
    awarded_points: Optional[int] = Field(None, ge=0, description="Actual points awarded for this completion. Can override task's default points.")
    verification_notes: Optional[str] = Field(None, description="Notes from the verifier regarding the approval or rejection.")

class TaskCompletionResponse(BaseResponseSchema):
    """
    Schema for representing a task completion in API responses.
    Includes 'id' (of the completion record), 'created_at', 'updated_at'.
    """
    task: TaskBasicInfo = Field(..., description="Basic information about the completed task.")
    user: UserBasicInfo = Field(..., description="Basic information about the user who completed the task.")

    completed_at: datetime = Field(..., description="Timestamp when the user marked the task as completed (UTC).")
    is_verified: bool = Field(..., description="Whether the completion has been verified.")
    verified_at: Optional[datetime] = Field(None, description="Timestamp when the verification occurred (UTC).")
    verifier: Optional[UserBasicInfo] = Field(None, description="Basic information about the user who verified the completion (if verified).")
    verification_notes: Optional[str] = Field(None, description="Notes from the verifier or user upon completion.")
    awarded_points: Optional[int] = Field(None, description="Points actually awarded for this completion.")


if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- TaskCompletion Schemas --- Demonstration")

    # TaskCompletionCreate Example
    # Assume task_id=1, user_id=1 (completer) from context
    completion_create_data = {
        "verificationNotes": "Finished the report generation and sent to stakeholders." # camelCase for verification_notes
    }
    try:
        create_schema = TaskCompletionCreate(**completion_create_data) # type: ignore[call-arg]
        logger.info(f"TaskCompletionCreate valid: {create_schema.model_dump(by_alias=True)}")
    except Exception as e:
        logger.error(f"Error creating TaskCompletionCreate: {e}")

    # TaskCompletionVerify Example
    # Assume task_completion_id=1 from path
    completion_verify_data = {
        "isVerified": True,
        "awardedPoints": 75, # Overriding default task points
        "verificationNotes": "Excellent work, above and beyond!"
    }
    try:
        verify_schema = TaskCompletionVerify(**completion_verify_data) # type: ignore[call-arg]
        logger.info(f"TaskCompletionVerify valid: {verify_schema.model_dump(by_alias=True)}")
    except Exception as e:
        logger.error(f"Error creating TaskCompletionVerify: {e}")

    # TaskCompletionResponse Example
    task_info_data = {"id": 1, "name": "Generate Q1 Report"}
    completer_info_data = {"id": 101, "name": "Alice"}
    verifier_info_data = {"id": 10, "name": "Admin Bob"}

    response_data = {
        "id": 501, # ID of the TaskCompletion record
        "createdAt": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
        "updatedAt": (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat(),
        "task": task_info_data,
        "user": completer_info_data,
        "completedAt": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(), # camelCase
        "isVerified": True,
        "verifiedAt": (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat(), # camelCase
        "verifier": verifier_info_data,
        "verificationNotes": "Approved. Great job!", # camelCase
        "awardedPoints": 50 # camelCase
    }
    try:
        response_schema = TaskCompletionResponse(**response_data) # type: ignore[call-arg]
        logger.info(f"TaskCompletionResponse: {response_schema.model_dump_json(by_alias=True, indent=2)}")
        if response_schema.task and response_schema.user:
            logger.info(f"  Task '{response_schema.task.name}' completed by '{response_schema.user.name}'")
        if response_schema.verifier:
            logger.info(f"  Verified by: {response_schema.verifier.name}")
    except Exception as e:
        logger.error(f"Error creating TaskCompletionResponse: {e}")
