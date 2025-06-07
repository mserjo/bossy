import uuid
import datetime
import logging
from pydantic import BaseModel, Field

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO) # Basic config for demonstration

# Forward declaration for UserResponse if it's defined elsewhere and needed for nesting.
# For now, we'll assume user details might be represented by user_id,
# or a simplified User schema could be defined here if necessary.
# class UserResponseSimple(BaseModel):
#     id: uuid.UUID
#     username: str

class UserGroupRatingBase(BaseModel):
    """
    Base schema for a User's Rating within a Group.
    Identifies the user, the group, and their rating score.
    """
    user_id: uuid.UUID = Field(..., description="The unique identifier of the user being rated.")
    group_id: uuid.UUID = Field(..., description="The unique identifier of the group in which the user is rated.")
    # Depending on the system, rating_score could be an average, total, or some other metric.
    rating_score: int = Field(..., description="The user's calculated rating score within the group.", ge=0) # Assuming positive scores

    class Config:
        orm_mode = True
        # For Pydantic V2:
        # model_config = { "from_attributes": True }

class UserGroupRatingCreate(UserGroupRatingBase):
    """
    Schema for creating or updating a User's Group Rating.
    This might be used when a new rating is submitted or calculated.
    """
    # last_rated_at could be set automatically by the server on creation/update.
    # If this schema is for *submitting* a single rating that gets aggregated,
    # then a different model for the raw rating submission might be needed.
    # This schema assumes rating_score is the actual score to be stored.
    pass

class UserGroupRatingUpdate(BaseModel):
    """
    Schema for updating a User's Group Rating.
    Typically, only the rating_score would be updated.
    """
    rating_score: int | None = Field(None, description="The new rating score for the user in the group.", ge=0)
    # group_id and user_id are identifiers, usually not updatable for an existing rating record.

class UserGroupRatingResponse(UserGroupRatingBase):
    """
    Schema for representing a User's Group Rating in API responses.
    Includes details from UserGroupRatingBase plus database-generated fields.
    """
    id: uuid.UUID = Field(..., description="The unique identifier of this rating record.")
    # user: UserResponseSimple | None = Field(None, description="Simplified User details, if needed.") # Example of nested user
    last_updated_at: datetime.datetime = Field(..., description="Timestamp when this rating was last updated or calculated.")

    # For Pydantic V2, the Config class would be nested here too if needed.
    # class Config:
    #     from_attributes = True
    #
    #     model_config = {
    #         "from_attributes": True,
    #         "json_schema_extra": {
    #             "examples": [
    #                 {
    #                     "id": "r1b2c3d4-e5f6-7890-1234-567890abcdef",
    #                     "user_id": "u1a2b3c4-d5e6-f789-0123-456789abcdef",
    #                     "group_id": "g1a2b3c4-d5e6-f789-0123-456789abcdef",
    #                     "rating_score": 1250,
    #                     "last_updated_at": "2023-05-10T09:00:00Z"
    #                     # "user": { "id": "u1a2b3c4-d5e6-f789-0123-456789abcdef", "username": "CoolUser123" }
    #                 }
    #             ]
    #         }
    #     }

# Example usage
if __name__ == "__main__":
    logger.info("Logging example from rating.py")

    # Example of creating a UserGroupRatingCreate instance
    try:
        rating_data = {
            "user_id": uuid.uuid4(),
            "group_id": uuid.uuid4(),
            "rating_score": 1500
        }
        new_rating = UserGroupRatingCreate(**rating_data)
        logger.info(f"Successfully created UserGroupRatingCreate instance: {new_rating.model_dump_json(indent=2)}")
    except Exception as e:
        logger.error(f"Error creating UserGroupRatingCreate instance: {e}")

    # Example of a UserGroupRatingResponse instance
    try:
        rating_response_data = {
            "id": uuid.uuid4(),
            "user_id": uuid.uuid4(),
            "group_id": uuid.uuid4(),
            "rating_score": 2200,
            "last_updated_at": datetime.datetime.now()
        }
        rating_resp = UserGroupRatingResponse(**rating_response_data)
        logger.info(f"Successfully created UserGroupRatingResponse instance: {rating_resp.model_dump_json(indent=2)}")
    except Exception as e:
        logger.error(f"Error creating UserGroupRatingResponse instance: {e}")
