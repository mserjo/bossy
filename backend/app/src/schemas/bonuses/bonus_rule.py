# backend/app/src/schemas/bonuses/bonus_rule.py

"""
Pydantic schemas for Bonus Rules.
"""

import logging
from typing import Optional, Dict, Any # For Dict, Any in condition_config
from datetime import datetime, timezone, timedelta # For examples and BaseResponseSchema

from pydantic import Field

from backend.app.src.schemas.base import BaseSchema, BaseMainResponseSchema
# Assuming BonusRule model inherits from BaseGroupAffiliatedMainModel, so response can use BaseMainResponseSchema + group info.

# Configure logger for this module
logger = logging.getLogger(__name__)

# --- Locally defined Basic Info schemas for demonstration ---
class GroupBasicInfo(BaseSchema): # Inherit BaseSchema for consistent config (e.g. camelCase)
    id: int = Field(..., example=1)
    name: str = Field(..., example="The Great Testers")

class BonusTypeBasicInfo(BaseSchema): # Inherit BaseSchema
    id: int = Field(..., example=1)
    code: str = Field(..., example="TASK_STREAK")
    name: str = Field(..., example="Task Streak Bonus")
# --- End of local Basic Info schemas ---


# --- BonusRule Schemas ---

class BonusRuleBase(BaseSchema):
    """Base schema for bonus rule data."""
    name: str = Field(..., min_length=3, max_length=255, description="Name of the bonus rule.", example="Weekly Task Completion Streak")
    description: Optional[str] = Field(None, description="Detailed description of the bonus rule.", example="Awarded for completing 5 tasks every week.")
    # group_id is often a path parameter or set by service for group-specific rules.
    # If it can be global (None) or set in payload, include it here.
    # group_id: Optional[int] = Field(None, description="ID of the group this rule applies to. Null if global.")
    bonus_type_id: int = Field(..., description="ID of the bonus type (from dict_bonus_types).", example=1)
    points_amount: int = Field(..., description="Points awarded (positive) or deducted (negative) by this rule.", example=100)
    condition_description: Optional[str] = Field(None, description="Human-readable description of the rule's conditions.", example="Complete 5 tasks of type 'CHORE' within 7 days.")
    condition_config: Optional[Dict[str, Any]] = Field(None, description="Structured JSON configuration for rule conditions.", example={"min_tasks": 5, "task_type_code": "CHORE", "period_days": 7})
    is_active: Optional[bool] = Field(True, description="Is this bonus rule currently active?")
    state: Optional[str] = Field("active", max_length=50, description="Lifecycle state of the rule (e.g., 'active', 'inactive', 'expired').", example="active") # From BaseMainModel
    notes: Optional[str] = Field(None, description="Internal notes for the bonus rule.") # From BaseMainModel

class BonusRuleCreate(BonusRuleBase):
    """
    Schema for creating a new bonus rule.
    `group_id` is assumed to be part of API path or context if rule is group-specific.
    """
    # name, bonus_type_id, points_amount are mandatory from BonusRuleBase.
    # group_id: int # If it must be in payload for group-specific rule creation.
    pass

class BonusRuleUpdate(BaseSchema): # Does not inherit BonusRuleBase to make all fields truly optional by default
    """
    Schema for updating an existing bonus rule. All fields are optional.
    """
    name: Optional[str] = Field(None, min_length=3, max_length=255, description="New name of the bonus rule.")
    description: Optional[str] = Field(None, description="New detailed description of the bonus rule.")
    bonus_type_id: Optional[int] = Field(None, description="New ID of the bonus type.")
    points_amount: Optional[int] = Field(None, description="New points awarded or deducted by this rule.")
    condition_description: Optional[str] = Field(None, description="New human-readable description of the rule's conditions.")
    condition_config: Optional[Dict[str, Any]] = Field(None, description="New structured JSON configuration for rule conditions.")
    is_active: Optional[bool] = Field(None, description="Update active status of this bonus rule.")
    state: Optional[str] = Field(None, max_length=50, description="Update lifecycle state of the rule.")
    notes: Optional[str] = Field(None, description="Update internal notes for the bonus rule.")
    # group_id is typically not changed once a rule is created for a specific group.

class BonusRuleResponse(BaseMainResponseSchema):
    """
    Schema for representing a bonus rule in API responses.
    Inherits common fields from BaseMainResponseSchema (id, created_at, updated_at, deleted_at, name, description, state, notes).
    """
    # name, description, state, notes are from BaseMainResponseSchema.
    # Ensure their descriptions and examples here match or enhance the base.
    name: str = Field(..., description="Name of the bonus rule.", example="Weekly Task Completion Streak")

    group: Optional[GroupBasicInfo] = Field(None, description="Basic information about the group this rule belongs to (if group-specific).") # Populated by service
    bonus_type: Optional[BonusTypeBasicInfo] = Field(None, description="Information about the bonus type.") # Populated by service

    points_amount: int = Field(..., description="Points awarded or deducted.", example=100)
    condition_description: Optional[str] = Field(None, description="Human-readable conditions.", example="Complete 5 tasks of type 'CHORE' within 7 days.")
    condition_config: Optional[Dict[str, Any]] = Field(None, description="Structured condition configuration.", example={"min_tasks": 5, "task_type_codes": ["CHORE"], "period_days": 7})
    is_active: bool = Field(..., description="Is the rule active?", example=True)

if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- BonusRule Schemas --- Demonstration")

    # BonusRuleCreate Example
    # Assume group_id=1 is context, bonus_type_id=1 ('STREAK_BONUS')
    rule_create_data = {
        "name": "Early Bird Task Bonus",
        "description": "Bonus for completing tasks before 9 AM.",
        "bonusTypeId": 1, # camelCase for bonus_type_id
        "pointsAmount": 25,
        "conditionDescription": "Complete any task marked as 'Morning Task' before 9:00 AM on the due date.",
        "conditionConfig": {"task_tag": "Morning Task", "complete_before_time": "09:00"},
        "isActive": True,
        "state": "active"
    }
    try:
        create_schema = BonusRuleCreate(**rule_create_data) # type: ignore[call-arg]
        logger.info(f"BonusRuleCreate valid: {create_schema.model_dump(by_alias=True)}")
    except Exception as e:
        logger.error(f"Error creating BonusRuleCreate: {e}")

    # BonusRuleUpdate Example
    rule_update_data = {"pointsAmount": 30, "isActive": False}
    update_schema = BonusRuleUpdate(**rule_update_data) # type: ignore[call-arg]
    logger.info(f"BonusRuleUpdate (partial): {update_schema.model_dump(exclude_unset=True, by_alias=True)}")

    # BonusRuleResponse Example
    group_info_data = {"id": 1, "name": "Marketing Team Campaigns"}
    bonus_type_info_data = {"id": 1, "code": "EARLY_COMPLETION", "name": "Early Completion Bonus"}

    response_data = {
        "id": 51,
        "createdAt": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "deletedAt": None,
        "name": "Early Bird Task Bonus",
        "description": "Bonus for completing tasks before 9 AM.",
        "state": "active",
        "notes": "Recently revised.",
        "group": group_info_data,
        "bonusType": bonus_type_info_data,
        "pointsAmount": 30,
        "conditionDescription": "Complete any task marked as 'Morning Task' before 9:00 AM on the due date.",
        "conditionConfig": {"task_tag": "Morning Task", "complete_before_time": "09:00"},
        "isActive": False # Reflects update
    }
    try:
        response_schema = BonusRuleResponse(**response_data) # type: ignore[call-arg]
        logger.info(f"BonusRuleResponse: {response_schema.model_dump_json(by_alias=True, indent=2)}")
        if response_schema.group and response_schema.bonus_type:
            logger.info(f"  Rule for Group: '{response_schema.group.name}', Bonus Type: '{response_schema.bonus_type.name}'")
    except Exception as e:
        logger.error(f"Error creating BonusRuleResponse: {e}")
