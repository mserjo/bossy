# backend/app/src/schemas/tasks/event.py

"""
Pydantic schemas for Events.
"""

import logging
from typing import Optional, List # For potential future use with assignees or similar
from datetime import datetime, timezone, timedelta # For examples and BaseResponseSchema

from pydantic import Field, HttpUrl # HttpUrl not used here, but good to have if URLs were present

from backend.app.src.schemas.base import BaseSchema, BaseMainResponseSchema
# from backend.app.src.core.dicts import EventFrequency # If events have recurrence

# Configure logger for this module
logger = logging.getLogger(__name__)

# --- Locally defined Basic Info schemas for demonstration ---
# (Ideally, these would be imported from their respective schema files or a shared location)
class GroupBasicInfo(BaseSchema):
    id: int = Field(..., example=1)
    name: str = Field(..., example="Marketing Department")

class EventTypeBasicInfo(BaseSchema): # Example if events have their own type dictionary
    id: int = Field(..., example=2)
    code: str = Field(..., example="WEBINAR")
    name: str = Field(..., example="Webinar")
# --- End of local Basic Info schemas ---


# --- Event Schemas ---

class EventBase(BaseSchema):
    """Base schema for event data, common to create and update operations."""
    name: str = Field(..., min_length=3, max_length=255, description="Name or title of the event.", example="Quarterly Review Meeting")
    description: Optional[str] = Field(None, description="Detailed description of the event.", example="Review of Q3 performance and planning for Q4.")
    # group_id is often a path parameter or set by service.
    # group_id: Optional[int] = Field(None, description="ID of the group this event belongs to.")
    # event_type_id: Optional[int] = Field(None, description="ID of the event type (e.g., from dict_event_types or dict_task_types).", example=1)
    start_time: datetime = Field(..., description="Start date and time of the event (UTC).", example=datetime.now(timezone.utc) + timedelta(days=10))
    end_time: Optional[datetime] = Field(None, description="Optional end date and time of the event (UTC).", example=datetime.now(timezone.utc) + timedelta(days=10, hours=2))
    location: Optional[str] = Field(None, max_length=512, description="Physical or virtual location of the event.", example="Board Room / Zoom")
    state: Optional[str] = Field("upcoming", max_length=50, description="State of the event (e.g., 'upcoming', 'ongoing', 'past', 'cancelled').", example="upcoming") # From BaseMainModel
    notes: Optional[str] = Field(None, description="Internal notes for the event.") # From BaseMainModel
    # Add recurrence fields here if events can be recurring, similar to TaskBase
    # is_recurring: Optional[bool] = Field(False)
    # recurrence_frequency: Optional[EventFrequency] = Field(None)
    # recurrence_interval: Optional[int] = Field(None, ge=1)

class EventCreate(EventBase):
    """
    Schema for creating a new event.
    `group_id` is assumed to be part of API path or context.
    """
    name: str = Field(..., min_length=3, max_length=255, description="Name or title of the event.") # Ensure name is mandatory
    start_time: datetime = Field(..., description="Start date and time of the event (UTC).") # Ensure start_time is mandatory
    pass

class EventUpdate(BaseSchema): # Does not inherit EventBase to make all fields truly optional
    """
    Schema for updating an existing event. All fields are optional for partial updates.
    """
    name: Optional[str] = Field(None, min_length=3, max_length=255, description="New name or title of the event.")
    description: Optional[str] = Field(None, description="New detailed description of the event.")
    # event_type_id: Optional[int] = Field(None, description="New ID of the event type.")
    start_time: Optional[datetime] = Field(None, description="New start date and time of the event (UTC).")
    end_time: Optional[datetime] = Field(None, description="New end date and time of the event (UTC).")
    location: Optional[str] = Field(None, max_length=512, description="New physical or virtual location of the event.")
    state: Optional[str] = Field(None, max_length=50, description="New state of the event.")
    notes: Optional[str] = Field(None, description="Updated internal notes for the event.")
    # Update recurrence fields if they exist


class EventResponse(BaseMainResponseSchema):
    """
    Schema for representing an event in API responses.
    Inherits common fields from BaseMainResponseSchema (id, created_at, updated_at, deleted_at, name, description, state, notes).
    """
    # name, description, state, notes are from BaseMainResponseSchema.
    name: str = Field(..., description="Name of the event.", example="Product Launch Webinar")
    description: Optional[str] = Field(None, description="Detailed description of the event.")
    state: Optional[str] = Field(None, description="Lifecycle state of the event (e.g., 'upcoming', 'past').", example="upcoming")

    group: Optional[GroupBasicInfo] = Field(None, description="Basic information about the group this event belongs to.") # Populated by service
    # event_type: Optional[EventTypeBasicInfo] = Field(None, description="Information about the event type.") # Populated by service

    start_time: datetime = Field(..., description="Start date and time of the event.", example=(datetime.now(timezone.utc) + timedelta(days=1)).isoformat())
    end_time: Optional[datetime] = Field(None, description="End date and time of the event.", example=(datetime.now(timezone.utc) + timedelta(days=1, hours=1)).isoformat())
    location: Optional[str] = Field(None, description="Location of the event.", example="Main Conference Hall")
    # Add recurrence fields if applicable
    # is_recurring: bool = Field(...)
    # recurrence_frequency: Optional[EventFrequency] = Field(None)
    # recurrence_interval: Optional[int] = Field(None)


if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- Event Schemas --- Demonstration")

    # EventCreate Example
    # Assume group_id=1 is context
    event_create_data = {
        "name": "Product Launch Webinar",
        "description": "Webinar to launch the new Product X features.",
        # "eventTypeId": 2, # If event types are used
        "startTime": (datetime.now(timezone.utc) + timedelta(weeks=2)).isoformat(), # camelCase for start_time
        "endTime": (datetime.now(timezone.utc) + timedelta(weeks=2, hours=1)).isoformat(),
        "location": "Online - Webinar Platform",
        "state": "upcoming"
    }
    try:
        create_schema = EventCreate(**event_create_data) # type: ignore[call-arg]
        logger.info(f"EventCreate valid: {create_schema.model_dump(by_alias=True)}")
    except Exception as e:
        logger.error(f"Error creating EventCreate: {e}")

    # EventUpdate Example
    event_update_data = {"location": "Online - Upgraded Webinar Platform", "state": "confirmed_upcoming"}
    update_schema = EventUpdate(**event_update_data)
    logger.info(f"EventUpdate (partial): {update_schema.model_dump(exclude_unset=True, by_alias=True)}")

    # EventResponse Example
    group_info_data = {"id": 1, "name": "Marketing Department"}
    # event_type_info_data = {"id": 2, "code": "WEBINAR", "name": "Webinar"}

    response_data = {
        "id": 201,
        "createdAt": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "name": "Product Launch Webinar",
        "description": "Webinar to launch the new Product X features.",
        "state": "confirmed_upcoming",
        "notes": "Final attendee list pending.",
        "deletedAt": None,
        "group": group_info_data,
        # "eventType": event_type_info,
        "startTime": (datetime.now(timezone.utc) + timedelta(weeks=2)).isoformat(),
        "endTime": (datetime.now(timezone.utc) + timedelta(weeks=2, hours=1)).isoformat(),
        "location": "Online - Upgraded Webinar Platform"
    }
    try:
        response_schema = EventResponse(**response_data) # type: ignore[call-arg]
        logger.info(f"EventResponse: {response_schema.model_dump_json(by_alias=True, indent=2)}")
        if response_schema.group:
            logger.info(f"  Event group name: {response_schema.group.name}")
    except Exception as e:
        logger.error(f"Error creating EventResponse: {e}")
