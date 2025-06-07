# backend/app/src/schemas/dictionaries/calendars.py

"""
Pydantic schemas for CalendarProvider dictionary entries.
"""

import logging
from typing import Optional # For optional custom fields if any
from datetime import datetime, timezone # For example values in __main__ and BaseResponseSchema

from pydantic import Field
from backend.app.src.schemas.dictionaries.base_dict import (
    DictionaryBase,
    # DictionaryCreate as BaseDictionaryCreate, # Not directly used if CalendarProviderCreate inherits CalendarProviderBase
    # DictionaryUpdate as BaseDictionaryUpdate, # Not directly used if CalendarProviderUpdate inherits CalendarProviderBase
    DictionaryResponse as BaseDictionaryResponse
)

# Configure logger for this module
logger = logging.getLogger(__name__)

# --- CalendarProvider Schemas ---

class CalendarProviderBase(DictionaryBase):
    """Base schema for CalendarProvider, inherits all fields from DictionaryBase."""
    # Example of custom fields if CalendarProvider model had them:
    # icon_url: Optional[str] = Field(None, max_length=512, description="URL to an icon for the provider.", example="https://example.com/icons/google_calendar.png")
    # integration_docs_url: Optional[str] = Field(None, max_length=512, description="Link to integration documentation.")
    pass

class CalendarProviderCreate(CalendarProviderBase):
    """
    Schema for creating a new CalendarProvider.
    Inherits fields from CalendarProviderBase. 'code' and 'name' are effectively required.
    """
    pass

class CalendarProviderUpdate(CalendarProviderBase):
    """
    Schema for updating an existing CalendarProvider.
    All fields from CalendarProviderBase are made optional here for partial updates.
    """
    code: Optional[str] = Field(None, min_length=1, max_length=100, description="Unique code or short identifier.")
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Human-readable name.")
    description: Optional[str] = Field(None)
    state: Optional[str] = Field(None, max_length=50)
    is_default: Optional[bool] = Field(None)
    display_order: Optional[int] = Field(None)
    notes: Optional[str] = Field(None)
    # If custom fields were in CalendarProviderBase:
    # icon_url: Optional[str] = Field(None)
    # integration_docs_url: Optional[str] = Field(None)


class CalendarProviderResponse(BaseDictionaryResponse):
    """
    Schema for representing a CalendarProvider in API responses.
    Inherits all fields from BaseDictionaryResponse.
    Add any CalendarProvider-specific response fields here if CalendarProviderBase had custom fields.
    """
    # If custom fields were in CalendarProviderBase and should be in response:
    # icon_url: Optional[str] = Field(None, description="URL to an icon for the provider.")
    # integration_docs_url: Optional[str] = Field(None, description="Link to integration documentation.")
    pass


if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- CalendarProvider Schemas (Dictionary) --- Demonstration")

    # CalendarProviderCreate Example
    provider_create_data = {
        "code": "GOOGLE_CALENDAR",
        "name": "Google Calendar",
        "description": "Integration with Google Calendar services.",
        "state": "active",
        # "iconUrl": "https://static.googleusercontent.com/media/www.google.com/en//calendar/images/manifest/logo_2020q4_192.png" # camelCase alias if field existed
    }
    try:
        provider_create_schema = CalendarProviderCreate(**provider_create_data)
        logger.info(f"CalendarProviderCreate valid: {provider_create_schema.model_dump(by_alias=True)}")
    except Exception as e:
        logger.error(f"Error creating CalendarProviderCreate: {e}")

    # CalendarProviderUpdate Example
    provider_update_data = {"description": "Enhanced integration with Google Calendar services including event synchronization."}
    provider_update_schema = CalendarProviderUpdate(**provider_update_data)
    logger.info(f"CalendarProviderUpdate (partial): {provider_update_schema.model_dump(exclude_unset=True, by_alias=True)}")

    # CalendarProviderResponse Example
    provider_response_data = {
        "id": 1,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "code": "OUTLOOK_CALENDAR",
        "name": "Outlook Calendar",
        "description": "Integration with Microsoft Outlook Calendar.",
        "state": "active",
        "isDefault": False,
        "displayOrder": 2,
        # "iconUrl": "https://example.com/icons/outlook_calendar.png" # If field existed
    }
    try:
        provider_response_schema = CalendarProviderResponse(**provider_response_data) # type: ignore[call-arg]
        logger.info(f"CalendarProviderResponse: {provider_response_schema.model_dump_json(by_alias=True, indent=2)}")
    except Exception as e:
        logger.error(f"Error creating CalendarProviderResponse: {e}")
