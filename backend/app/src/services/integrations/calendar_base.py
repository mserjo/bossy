# backend/app/src/services/integrations/calendar_base.py
import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession # For potential DB interaction with tokens/settings

from app.src.services.base import BaseService # Optional: inherit if needs DB session for common tasks like storing tokens
from app.src.models.auth.user import User # For user context
# Define Pydantic models for Calendar Event data structures if not using external library models directly
# For example:
from pydantic import BaseModel, Field

class CalendarEventData(BaseModel):
    id: Optional[str] = Field(None, description="Provider's unique ID for the event")
    title: str = Field(..., description="Title or summary of the event")
    start_time: datetime = Field(..., description="Event start_time (timezone-aware)")
    end_time: datetime = Field(..., description="Event end_time (timezone-aware)")
    description: Optional[str] = Field(None, description="Detailed description of the event")
    location: Optional[str] = Field(None, description="Location of the event")
    is_all_day: bool = Field(False, description="True if it's an all-day event")
    # attendees: Optional[List[str]] = Field(None, description="List of attendee emails") # Example
    # meeting_link: Optional[str] = Field(None, description="Link to online meeting") # Example
    # raw: Optional[Dict[str, Any]] = Field(None, description="Original raw event data from provider") # For debugging or unprocessed fields

class CalendarInfo(BaseModel):
    id: str = Field(..., description="Provider's unique ID for the calendar")
    name: str = Field(..., description="Display name of the calendar (e.g., 'Primary', 'Work')")
    is_primary: bool = Field(False, description="True if this is the user's primary calendar on the platform")
    can_edit: bool = Field(False, description="True if the application has write access to this calendar")


# Initialize logger for this module
logger = logging.getLogger(__name__)

class BaseCalendarIntegrationService(BaseService, ABC): # Inherit BaseService for db_session
    """
    Abstract Base Class for calendar integration services.
    Defines a common interface for interacting with different calendar platforms
    like Google Calendar, Outlook Calendar, etc.

    Requires concrete implementations for each specific calendar provider.
    May need to store OAuth tokens or API keys, potentially in a UserIntegrationSetting model.
    """

    service_name: str # To be defined by concrete class, e.g., "GOOGLE_CALENDAR"

    def __init__(self, db_session: AsyncSession, user_id_for_context: Optional[UUID] = None):
        """
        Initialize with a DB session (for token/settings storage via BaseService)
        and optionally a user_id if operations are user-specific.
        """
        super().__init__(db_session) # BaseService provides self.db_session
        self.user_id_for_context = user_id_for_context # For user-specific operations
        logger.info(f"BaseCalendarIntegrationService (subclass: {self.__class__.__name__}) initialized for user: {user_id_for_context or 'N/A'}.")

    @abstractmethod
    async def connect_account(self, auth_code: str, redirect_uri: str, user_id: UUID) -> Dict[str, Any]: # Added user_id
        """
        Connects a user's calendar account using an authorization code (OAuth2 flow).
        Should store tokens securely (e.g., in DB, encrypted).

        Args:
            auth_code (str): The authorization code received from OAuth provider.
            redirect_uri (str): The redirect URI used in the OAuth flow.
            user_id (UUID): The ID of the user connecting their account.

        Returns:
            Dict[str, Any]: Status of connection, user's calendar email/ID.
        """
        pass

    @abstractmethod
    async def disconnect_account(self, user_id: UUID) -> bool:
        """
        Disconnects a user's calendar account, revoking tokens.
        Should remove stored tokens.
        """
        pass

    @abstractmethod
    async def refresh_access_token_if_needed(self, user_id: UUID) -> bool:
        """
        Checks if the access token for a user is expired and refreshes it using the refresh token.
        Updates stored tokens.
        """
        pass

    @abstractmethod
    async def list_user_calendars(self, user_id: UUID) -> List[CalendarInfo]:
        """
        Lists all calendars accessible for the connected user account.
        """
        pass

    @abstractmethod
    async def create_event(
        self,
        user_id: UUID,
        calendar_id: str,
        event_data: CalendarEventData
    ) -> Optional[CalendarEventData]:
        """
        Creates a new event in the specified user's calendar.
        """
        pass

    @abstractmethod
    async def get_event(
        self,
        user_id: UUID,
        calendar_id: str,
        event_id: str
    ) -> Optional[CalendarEventData]:
        """
        Retrieves a specific event from the user's calendar.
        """
        pass

    @abstractmethod
    async def update_event(
        self,
        user_id: UUID,
        calendar_id: str,
        event_id: str,
        event_data: CalendarEventData
    ) -> Optional[CalendarEventData]:
        """
        Updates an existing event in the user's calendar.
        """
        pass

    @abstractmethod
    async def delete_event(
        self,
        user_id: UUID,
        calendar_id: str,
        event_id: str
    ) -> bool:
        """
        Deletes an event from the user's calendar.
        """
        pass

    @abstractmethod
    async def list_events(
        self,
        user_id: UUID,
        calendar_id: str,
        start_time: datetime,
        end_time: datetime,
        query: Optional[str] = None
    ) -> List[CalendarEventData]:
        """
        Lists events from a specific calendar within a given time range.
        """
        pass

    # Example helper methods for token management (to be implemented in concrete or another base class)
    # async def _get_user_tokens(self, user_id: UUID) -> Optional[Dict[str, Any]]:
    #     # Placeholder: Fetch from a UserIntegrationToken model using self.db_session
    #     # stmt = select(UserIntegrationToken).where(
    #     #     UserIntegrationToken.user_id == user_id,
    #     #     UserIntegrationToken.service_name == self.service_name
    #     # )
    #     # token_record = (await self.db_session.execute(stmt)).scalar_one_or_none()
    #     # if token_record:
    #     #     return {
    #     #         "access_token": token_record.access_token,
    #     #         "refresh_token": token_record.refresh_token,
    #     #         "expires_at": token_record.token_expires_at # Assuming datetime object
    #     #     }
    #     logger.warning(f"Token retrieval placeholder: No stored tokens found for user {user_id} and service {getattr(self, 'service_name', 'UnknownService')}.")
    #     return None

    # async def _store_user_tokens(self, user_id: UUID, tokens: Dict[str, Any], token_expires_at: Optional[datetime]) -> bool:
    #     # Placeholder: Store/update tokens in UserIntegrationToken model using self.db_session
    #     # Needs to handle creation or update (upsert).
    #     # Example:
    #     # existing_token_record = ... fetch ...
    #     # if existing_token_record:
    #     #    existing_token_record.access_token = tokens['access_token']
    #     #    if 'refresh_token' in tokens: existing_token_record.refresh_token = tokens['refresh_token']
    #     #    existing_token_record.token_expires_at = token_expires_at
    #     #    self.db_session.add(existing_token_record)
    #     # else:
    #     #    new_token_record = UserIntegrationToken(user_id=user_id, service_name=self.service_name, ...)
    #     #    self.db_session.add(new_token_record)
    #     # await self.commit() # Or caller commits if part of larger transaction
    #     logger.info(f"Token storage placeholder: Storing tokens for user {user_id}, service {getattr(self, 'service_name', 'UnknownService')}.")
    #     return True


logger.info("BaseCalendarIntegrationService (ABC) and CalendarEventData/CalendarInfo (Pydantic) defined.")
