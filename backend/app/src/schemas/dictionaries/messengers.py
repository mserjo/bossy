# backend/app/src/schemas/dictionaries/messengers.py

"""
Pydantic schemas for MessengerPlatform dictionary entries.
"""

import logging
from typing import Optional # For optional custom fields if any
from datetime import datetime, timezone # For example values in __main__ and BaseResponseSchema

from pydantic import Field
from backend.app.src.schemas.dictionaries.base_dict import (
    DictionaryBase,
    # DictionaryCreate as BaseDictionaryCreate, # Not directly used if MessengerPlatformCreate inherits MessengerPlatformBase
    # DictionaryUpdate as BaseDictionaryUpdate, # Not directly used if MessengerPlatformUpdate inherits MessengerPlatformBase
    DictionaryResponse as BaseDictionaryResponse
)

# Configure logger for this module
logger = logging.getLogger(__name__)

# --- MessengerPlatform Schemas ---

class MessengerPlatformBase(DictionaryBase):
    """Base schema for MessengerPlatform, inherits all fields from DictionaryBase."""
    # Example of custom fields if MessengerPlatform model had them:
    # supports_rich_text: Optional[bool] = Field(None,
    #                                               description="Does this platform support rich text formatting?",
    #                                               example=True)
    # api_docs_url: Optional[str] = Field(None, max_length=512,
    #                                      description="URL to API documentation for this platform.")
    pass

class MessengerPlatformCreate(MessengerPlatformBase):
    """
    Schema for creating a new MessengerPlatform.
    Inherits fields from MessengerPlatformBase. 'code' and 'name' are effectively required.
    """
    pass

class MessengerPlatformUpdate(MessengerPlatformBase):
    """
    Schema for updating an existing MessengerPlatform.
    All fields from MessengerPlatformBase are made optional here for partial updates.
    """
    code: Optional[str] = Field(None, min_length=1, max_length=100, description="Unique code or short identifier.")
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Human-readable name.")
    description: Optional[str] = Field(None)
    state: Optional[str] = Field(None, max_length=50)
    is_default: Optional[bool] = Field(None)
    display_order: Optional[int] = Field(None)
    notes: Optional[str] = Field(None)
    # If custom fields were in MessengerPlatformBase:
    # supports_rich_text: Optional[bool] = Field(None)
    # api_docs_url: Optional[str] = Field(None)


class MessengerPlatformResponse(BaseDictionaryResponse):
    """
    Schema for representing a MessengerPlatform in API responses.
    Inherits all fields from BaseDictionaryResponse.
    Add any MessengerPlatform-specific response fields here if MessengerPlatformBase had custom fields.
    """
    # If custom fields were in MessengerPlatformBase and should be in response:
    # supports_rich_text: Optional[bool] = Field(None, description="Supports rich text formatting?")
    # api_docs_url: Optional[str] = Field(None, description="Link to API documentation.")
    pass


if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- MessengerPlatform Schemas (Dictionary) --- Demonstration")

    # MessengerPlatformCreate Example
    platform_create_data = {
        "code": "TELEGRAM_BOT",
        "name": "Telegram Bot",
        "description": "Notifications via a Telegram Bot integration.",
        "state": "active",
        # "supportsRichText": True, # camelCase alias if field existed
        # "apiDocsUrl": "https://core.telegram.org/bots/api"
    }
    try:
        platform_create_schema = MessengerPlatformCreate(**platform_create_data)
        logger.info(f"MessengerPlatformCreate valid: {platform_create_schema.model_dump(by_alias=True)}")
    except Exception as e:
        logger.error(f"Error creating MessengerPlatformCreate: {e}")

    # MessengerPlatformUpdate Example
    platform_update_data = {"description": "Notifications and interactions via a Telegram Bot."}
    platform_update_schema = MessengerPlatformUpdate(**platform_update_data)
    logger.info(f"MessengerPlatformUpdate (partial): {platform_update_schema.model_dump(exclude_unset=True, by_alias=True)}")

    # MessengerPlatformResponse Example
    platform_response_data = {
        "id": 1,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "code": "SLACK_WEBHOOK",
        "name": "Slack Webhook",
        "description": "Notifications sent to Slack via Incoming Webhooks.",
        "state": "active",
        "isDefault": False,
        "displayOrder": 2,
        # "supportsRichText": True # If field existed
    }
    try:
        platform_response_schema = MessengerPlatformResponse(**platform_response_data) # type: ignore[call-arg]
        logger.info(f"MessengerPlatformResponse: {platform_response_schema.model_dump_json(by_alias=True, indent=2)}")
    except Exception as e:
        logger.error(f"Error creating MessengerPlatformResponse: {e}")
