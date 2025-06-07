# backend/app/src/schemas/tasks/review.py

"""
Pydantic schemas for Task Reviews.
"""

import logging
from typing import Optional
from datetime import datetime, timezone, timedelta # For examples and BaseResponseSchema

from pydantic import Field, conint

from backend.app.src.schemas.base import BaseSchema, BaseResponseSchema

# Configure logger for this module
logger = logging.getLogger(__name__)

# --- Locally defined Basic Info schemas for demonstration ---
class UserBasicInfo(BaseSchema): # Inherit BaseSchema for consistent config (e.g. camelCase)
    id: int = Field(..., example=105)
    name: Optional[str] = Field(None, example="CriticalCarl")

class TaskBasicInfo(BaseSchema): # Inherit BaseSchema
    id: int = Field(..., example=1)
    name: str = Field(..., example="Research Competitors")
# --- End of local Basic Info schemas ---


# --- TaskReview Schemas ---

class TaskReviewBase(BaseSchema):
    """
    Base schema for task review data.
    `task_id` and `user_id` (reviewer) are usually context-derived or path parameters.
    """
    rating: Optional[conint(ge=1, le=5)] = Field(None, description="Numerical rating (e.g., 1 to 5 stars). Null if only comment provided.", example=5)
    comment: Optional[str] = Field(None, description="Textual feedback or comment from the user.", example="Great task, very challenging!")

class TaskReviewCreate(TaskReviewBase):
    """
    Schema for creating a new task review.
    `task_id` from path, `user_id` from authenticated user.
    At least one of rating or comment should typically be required by service layer.
    """
    # Service layer should validate that at least rating or comment is provided.
    # If strictness is desired at schema level, a model_validator could be added here.
    # Example:
    # @model_validator(mode='after')
    # def check_rating_or_comment_exists(self) -> 'TaskReviewCreate':
    #     if self.rating is None and self.comment is None:
    #         raise ValueError("At least one of 'rating' or 'comment' must be provided.")
    #     return self
    pass

class TaskReviewUpdate(TaskReviewBase): # Inherits from TaskReviewBase, fields are already Optional
    """
    Schema for updating an existing task review.
    All fields are optional for partial updates.
    """
    # rating and comment are already optional in TaskReviewBase for this purpose.
    # If you want to make sure that at least one field is provided for update,
    # a model_validator could be added here as well, checking if model_dump(exclude_unset=True) is empty.
    pass

class TaskReviewResponse(BaseResponseSchema):
    """
    Schema for representing a task review in API responses.
    Includes 'id' (of the review record), 'created_at', 'updated_at'.
    `created_at` effectively serves as the review_date.
    """
    task: TaskBasicInfo = Field(..., description="Basic information about the reviewed task.")
    user: UserBasicInfo = Field(..., description="Basic information about the user who submitted the review.")

    rating: Optional[int] = Field(None, description="Numerical rating given.") # conint is for validation, output can be int
    comment: Optional[str] = Field(None, description="Textual comment provided.")
    # review_date: datetime = Field(alias="createdAt", ...) # Alias if preferred, but createdAt is standard


if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- TaskReview Schemas --- Demonstration")

    # TaskReviewCreate Example
    # Assume task_id=1, user_id=1 (reviewer) from context
    review_create_data = {
        "rating": 4,
        "comment": "Good task, but the instructions could be a bit clearer on step 3."
    }
    try:
        create_schema = TaskReviewCreate(**review_create_data)
        logger.info(f"TaskReviewCreate valid: {create_schema.model_dump(by_alias=True)}")
    except Exception as e:
        logger.error(f"Error creating TaskReviewCreate: {e}")

    review_create_comment_only = {"comment": "Just a comment, no rating."}
    try:
        create_comment_schema = TaskReviewCreate(**review_create_comment_only)
        logger.info(f"TaskReviewCreate (comment only) valid: {create_comment_schema.model_dump(by_alias=True)}")
    except Exception as e:
        logger.error(f"Error creating TaskReviewCreate (comment only): {e}")

    # TaskReviewUpdate Example
    # Assume review_id from path
    review_update_data = {"comment": "Updated comment: Actually, step 3 was fine after re-reading!"}
    update_schema = TaskReviewUpdate(**review_update_data)
    logger.info(f"TaskReviewUpdate (partial): {update_schema.model_dump(exclude_unset=True, by_alias=True)}")

    # TaskReviewResponse Example
    task_info_data = {"id": 1, "name": "Research Competitors"}
    reviewer_info_data = {"id": 105, "name": "CriticalCarl"}

    response_data = {
        "id": 707, # ID of the TaskReview record
        "createdAt": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "task": task_info_data,
        "user": reviewer_info_data,
        "rating": 5,
        "comment": "This task provided excellent insights!"
    }
    try:
        response_schema = TaskReviewResponse(**response_data) # type: ignore[call-arg]
        logger.info(f"TaskReviewResponse: {response_schema.model_dump_json(by_alias=True, indent=2)}")
        if response_schema.task and response_schema.user:
            logger.info(f"  Task '{response_schema.task.name}' reviewed by '{response_schema.user.name}' with rating {response_schema.rating}")
    except Exception as e:
        logger.error(f"Error creating TaskReviewResponse: {e}")
