# backend/app/src/schemas/dictionaries/bonus_types.py

"""
Pydantic schemas for BonusType dictionary entries.
"""

import logging
from typing import Optional # For optional custom fields if any
from datetime import datetime, timezone # For example values in __main__ and BaseResponseSchema

from pydantic import Field
from backend.app.src.schemas.dictionaries.base_dict import (
    DictionaryBase,
    # DictionaryCreate as BaseDictionaryCreate, # Not directly used if BonusTypeCreate inherits BonusTypeBase
    # DictionaryUpdate as BaseDictionaryUpdate, # Not directly used if BonusTypeUpdate inherits BonusTypeBase
    DictionaryResponse as BaseDictionaryResponse
)

# Configure logger for this module
logger = logging.getLogger(__name__)

# --- BonusType Schemas ---

class BonusTypeBase(DictionaryBase):
    """Base schema for BonusType, inherits all fields from DictionaryBase."""
    # Example of custom fields if BonusType model had them:
    # is_penalty_type: Optional[bool] = Field(None,
    #                                            description="Is this type typically a penalty (negative points)?",
    #                                            example=False)
    # default_point_impact: Optional[int] = Field(None,
    #                                               description="Default points impact (positive or negative).",
    #                                               example=20)
    pass

class BonusTypeCreate(BonusTypeBase):
    """
    Schema for creating a new BonusType.
    Inherits fields from BonusTypeBase. 'code' and 'name' are effectively required.
    """
    pass

class BonusTypeUpdate(BonusTypeBase):
    """
    Schema for updating an existing BonusType.
    All fields from BonusTypeBase are made optional here for partial updates.
    """
    code: Optional[str] = Field(None, min_length=1, max_length=100, description="Unique code or short identifier.")
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Human-readable name.")
    description: Optional[str] = Field(None)
    state: Optional[str] = Field(None, max_length=50)
    is_default: Optional[bool] = Field(None)
    display_order: Optional[int] = Field(None)
    notes: Optional[str] = Field(None)
    # If custom fields were in BonusTypeBase:
    # is_penalty_type: Optional[bool] = Field(None)
    # default_point_impact: Optional[int] = Field(None)

class BonusTypeResponse(BaseDictionaryResponse):
    """
    Schema for representing a BonusType in API responses.
    Inherits all fields from BaseDictionaryResponse.
    Add any BonusType-specific response fields here if BonusTypeBase had custom fields.
    """
    # If custom fields were in BonusTypeBase and should be in response:
    # is_penalty_type: Optional[bool] = Field(None, description="Is this a penalty type?")
    # default_point_impact: Optional[int] = Field(None, description="Default point impact.")
    pass


if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- BonusType Schemas (Dictionary) --- Demonstration")

    # BonusTypeCreate Example
    type_create_data = {
        "code": "STREAK_BONUS",
        "name": "Streak Bonus",
        "description": "Bonus awarded for completing a streak of tasks.",
        "state": "active",
        # "isPenaltyType": False, # camelCase alias if field existed
        # "defaultPointImpact": 50
    }
    try:
        type_create_schema = BonusTypeCreate(**type_create_data)
        logger.info(f"BonusTypeCreate valid: {type_create_schema.model_dump(by_alias=True)}")
    except Exception as e:
        logger.error(f"Error creating BonusTypeCreate: {e}")

    # BonusTypeUpdate Example
    type_update_data = {"description": "Bonus awarded for completing a 7-day streak of tasks."}
    type_update_schema = BonusTypeUpdate(**type_update_data)
    logger.info(f"BonusTypeUpdate (partial): {type_update_schema.model_dump(exclude_unset=True, by_alias=True)}")

    # BonusTypeResponse Example
    type_response_data = {
        "id": 1,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "code": "LATE_PENALTY",
        "name": "Late Submission Penalty",
        "description": "Penalty applied for late task submissions.",
        "state": "active",
        "isDefault": False,
        "displayOrder": 10,
        # "isPenaltyType": True, # If field existed
        # "defaultPointImpact": -10
    }
    try:
        type_response_schema = BonusTypeResponse(**type_response_data) # type: ignore[call-arg]
        logger.info(f"BonusTypeResponse: {type_response_schema.model_dump_json(by_alias=True, indent=2)}")
    except Exception as e:
        logger.error(f"Error creating BonusTypeResponse: {e}")
