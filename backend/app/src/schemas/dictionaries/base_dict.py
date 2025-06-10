# backend/app/src/schemas/dictionaries/base_dict.py

"""
This module defines base Pydantic schemas specifically for dictionary/lookup table entries.
"""

import logging
from typing import Optional
from datetime import datetime, timezone # Added timezone for __main__

from pydantic import Field

from backend.app.src.schemas.base import BaseSchema, BaseDictionaryResponseSchema # Import more generic bases

# Configure logger for this module
logger = logging.getLogger(__name__)

# --- Base Schemas for Dictionary Entries ---

class DictionaryBase(BaseSchema):
    """
    Base schema for creating and updating dictionary entries.
    Contains fields common to most dictionary items, mirroring `BaseDictionaryModel` fields
    excluding ORM-specific ones like id, created_at, updated_at, deleted_at.
    """
    code: str = Field(..., min_length=1, max_length=100,
                      description="Unique code or short identifier for the dictionary item.",
                      example="ITEM_CODE_001")
    name: str = Field(..., min_length=1, max_length=255,
                      description="Human-readable name of the dictionary item.",
                      example="My Dictionary Item")
    description: Optional[str] = Field(None,
                                       description="Optional detailed description of the dictionary item.",
                                       example="This item is used for general purposes.")
    state: Optional[str] = Field(None, max_length=50,
                                 description="Optional state or status of the dictionary item (e.g., 'active', 'deprecated').",
                                 example="active")
    is_default: Optional[bool] = Field(None,
                                       description="Indicates if this is a default value for the dictionary type.",
                                       example=False)
    display_order: Optional[int] = Field(None,
                                         description="Order in which this item should be displayed in lists/dropdowns.",
                                         example=1)
    notes: Optional[str] = Field(None,
                                 description="Optional internal notes or general remarks about the dictionary item.",
                                 example="Internal system note.")

class DictionaryCreate(DictionaryBase):
    """
    Schema for creating a new dictionary entry.
    All fields from DictionaryBase are typically required or have defaults suitable for creation.
    `code` and `name` are usually always required.
    """
    # `code` and `name` are already marked as required (no Optional, no default that makes them optional) in DictionaryBase.
    # Other fields can remain optional if they can be omitted on creation.
    # Example: if state must be set on creation and is not optional:
    # state: str = Field(..., max_length=50, description="State of the dictionary item.", example="active")
    pass

class DictionaryUpdate(DictionaryBase):
    """
    Schema for updating an existing dictionary entry.
    All fields are optional to allow for partial updates.
    """
    code: Optional[str] = Field(None, min_length=1, max_length=100, description="Unique code or short identifier for the dictionary item.")
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Human-readable name of the dictionary item.")
    # description, state, is_default, display_order, notes are already Optional in DictionaryBase, so they are fine for updates.

# The response schema for dictionary items is already well-defined by
# `BaseDictionaryResponseSchema` in `schemas.base.py`.
# We can re-export it here for convenience or if we want to alias it.
DictionaryResponse = BaseDictionaryResponseSchema


if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- Dictionary Base Schemas --- Demonstration")

    # DictionaryCreate Example
    create_data = {
        "code": "NEW_ITEM",
        "name": "New Dictionary Item",
        "description": "Just created this item.",
        "state": "pending",
        "isDefault": True, # camelCase alias for is_default
        "displayOrder": 10 # camelCase alias for display_order
    }
    try:
        dict_create_schema = DictionaryCreate(**create_data) # type: ignore[call-arg] # Pydantic handles alias
        logger.info(f"DictionaryCreate valid: {dict_create_schema.model_dump(by_alias=True)}")
    except Exception as e:
        logger.error(f"Error creating DictionaryCreate: {e}")

    # DictionaryUpdate Example (partial update)
    update_data = {"name": "Updated Item Name", "state": "active"}
    dict_update_schema = DictionaryUpdate(**update_data)
    logger.info(f"DictionaryUpdate (partial): {dict_update_schema.model_dump(exclude_unset=True, by_alias=True)}")

    # DictionaryResponse Example (using the re-exported BaseDictionaryResponseSchema)
    response_data = {
        "id": 101,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "code": "EXISTING_ITEM",
        "name": "Existing Item",
        "description": "This item has been here a while.",
        "state": "active",
        "isDefault": False,
        "displayOrder": 1,
        "notes": "No special notes.",
        # "deletedAt": None # from BaseMainResponseSchema which BaseDictionaryResponseSchema inherits
    }
    try:
        dict_response_schema = DictionaryResponse(**response_data) # type: ignore[call-arg]
        logger.info(f"DictionaryResponse: {dict_response_schema.model_dump_json(by_alias=True, indent=2)}")
    except Exception as e:
        logger.error(f"Error creating DictionaryResponse: {e}")
