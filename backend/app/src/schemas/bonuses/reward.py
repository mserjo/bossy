# backend/app/src/schemas/bonuses/reward.py

"""
Pydantic schemas for Rewards that users can redeem with points.
"""

import logging
from typing import Optional, Dict, Any # Added Dict, Any for RedeemRewardRequest
from datetime import datetime, timezone, timedelta # For examples and BaseResponseSchema

from pydantic import Field, HttpUrl

from backend.app.src.schemas.base import BaseSchema, BaseMainResponseSchema
# Assuming Reward model inherits from BaseGroupAffiliatedMainModel

# Configure logger for this module
logger = logging.getLogger(__name__)

# --- Locally defined Basic Info schemas for demonstration ---
class GroupBasicInfo(BaseSchema): # Inherit BaseSchema for consistent config (e.g. camelCase)
    id: int = Field(..., example=1)
    name: str = Field(..., example="Company Rewards Program")
# --- End of local Basic Info schemas ---


# --- Reward Schemas ---

class RewardBase(BaseSchema):
    """Base schema for reward data."""
    name: str = Field(..., min_length=3, max_length=255, description="Name of the reward.", example="Free Coffee Coupon")
    description: Optional[str] = Field(None, description="Detailed description of the reward.", example="Redeemable for one large coffee at the cafeteria.")
    # group_id is often a path parameter or set by service for group-specific rewards.
    # If it can be global (None) or set in payload, include it here.
    # group_id: Optional[int] = Field(None, description="ID of the group this reward belongs to. Null if global.")
    cost_in_points: int = Field(..., gt=0, description="Number of points/currency required to redeem this reward.", example=100)
    icon_url: Optional[HttpUrl] = Field(None, description="Optional URL or path to an icon representing the reward.", example="https://example.com/icons/coffee_reward.png")
    is_active: Optional[bool] = Field(True, description="Is this reward currently available for redemption?")
    stock_quantity: Optional[int] = Field(None, ge=0, description="Available stock for this reward. Null if unlimited.", example=50)
    state: Optional[str] = Field("available", max_length=50, description="Lifecycle state of the reward (e.g., 'available', 'unavailable', 'archived').", example="available") # From BaseMainModel
    notes: Optional[str] = Field(None, description="Internal notes for the reward.") # From BaseMainModel

class RewardCreate(RewardBase):
    """
    Schema for creating a new reward.
    `group_id` is assumed to be part of API path or context if reward is group-specific.
    """
    # name and cost_in_points are mandatory from RewardBase.
    # group_id: int # If it must be in payload for group-specific reward creation.
    pass

class RewardUpdate(BaseSchema): # Does not inherit RewardBase to make all fields truly optional
    """
    Schema for updating an existing reward. All fields are optional.
    """
    name: Optional[str] = Field(None, min_length=3, max_length=255, description="New name of the reward.")
    description: Optional[str] = Field(None, description="New detailed description of the reward.")
    cost_in_points: Optional[int] = Field(None, gt=0, description="New cost in points for this reward.")
    icon_url: Optional[HttpUrl] = Field(None, description="New URL or path to an icon for the reward.")
    is_active: Optional[bool] = Field(None, description="Update active status of this reward.")
    stock_quantity: Optional[int] = Field(None, ge=0, description="Update available stock. Null if unlimited.")
    state: Optional[str] = Field(None, max_length=50, description="Update lifecycle state of the reward.")
    notes: Optional[str] = Field(None, description="Update internal notes for the reward.")
    # group_id is typically not changed.

class RewardResponse(BaseMainResponseSchema):
    """
    Schema for representing a reward in API responses.
    Inherits common fields from BaseMainResponseSchema (id, created_at, updated_at, deleted_at, name, description, state, notes).
    """
    # name, description, state, notes are from BaseMainResponseSchema.
    name: str = Field(..., description="Name of the reward.", example="Free Coffee Coupon")

    group: Optional[GroupBasicInfo] = Field(None, description="Basic information about the group this reward belongs to (if group-specific).") # Populated by service

    cost_in_points: int = Field(..., description="Points required to redeem.", example=100)
    icon_url: Optional[HttpUrl] = Field(None, description="Icon URL for the reward.", example="https://example.com/icons/coffee_reward.png")
    is_active: bool = Field(..., description="Is the reward currently active?", example=True)
    stock_quantity: Optional[int] = Field(None, description="Available stock. Null if unlimited.", example=50)

class RedeemRewardRequest(BaseSchema):
    """
    Schema for a user request to redeem a specific reward.
    `reward_id` is typically a path parameter.
    `user_id` is from the authenticated user context.
    """
    quantity: Optional[int] = Field(1, ge=1, description="Number of this reward item to redeem.", example=1)
    # Any other specific details needed for redemption, e.g., delivery address if physical good.
    delivery_details: Optional[Dict[str, Any]] = Field(None, description="Details for reward delivery, if applicable.", example={"address_line_1": "123 Main St", "city": "Anytown"})

# RedeemRewardResponse could be a MessageResponse or include details of the transaction/updated balance.
# For example, it could be an AccountTransactionResponse or a wrapper around it.

if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- Reward Schemas --- Demonstration")

    # RewardCreate Example
    # Assume group_id=1 is context
    reward_create_data = {
        "name": "Premium Feature Access (1 Month)",
        "description": "Unlock all premium features for one month.",
        # "groupId": 1, # If needed in payload
        "costInPoints": 500, # camelCase for cost_in_points
        "isActive": True,
        "stockQuantity": None, # Unlimited
        "state": "available"
    }
    try:
        create_schema = RewardCreate(**reward_create_data) # type: ignore[call-arg]
        logger.info(f"RewardCreate valid: {create_schema.model_dump(by_alias=True)}")
    except Exception as e:
        logger.error(f"Error creating RewardCreate: {e}")

    # RewardUpdate Example
    reward_update_data = {"costInPoints": 450, "description": "Special offer: Unlock premium features for one month at a reduced price!"}
    update_schema = RewardUpdate(**reward_update_data) # type: ignore[call-arg]
    logger.info(f"RewardUpdate (partial): {update_schema.model_dump(exclude_unset=True, by_alias=True)}")

    # RewardResponse Example
    group_info_data = {"id": 1, "name": "Global Rewards Catalog"}
    response_data = {
        "id": 77,
        "createdAt": (datetime.now(timezone.utc) - timedelta(days=10)).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "deletedAt": None,
        "name": "Premium Feature Access (1 Month)",
        "description": "Special offer: Unlock premium features for one month at a reduced price!",
        "state": "available",
        "notes": "Popular item.",
        "group": group_info_data, # Or null if truly global and not group-affiliated via BaseGroupAffiliatedMainModel
        "costInPoints": 450,
        "isActive": True,
        "stockQuantity": None
    }
    try:
        response_schema = RewardResponse(**response_data) # type: ignore[call-arg]
        logger.info(f"RewardResponse: {response_schema.model_dump_json(by_alias=True, indent=2)}")
        if response_schema.group:
            logger.info(f"  Reward Group: {response_schema.group.name}")
    except Exception as e:
        logger.error(f"Error creating RewardResponse: {e}")

    # RedeemRewardRequest Example
    redeem_request_data = {"quantity": 2, "deliveryDetails": {"address_line_1": "123 Main St"}}
    redeem_schema = RedeemRewardRequest(**redeem_request_data) # type: ignore[call-arg]
    logger.info(f"RedeemRewardRequest: {redeem_schema.model_dump(by_alias=True)}")
