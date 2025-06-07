# backend/app/src/models/dictionaries/calendars.py

"""
SQLAlchemy model for a 'CalendarProvider' dictionary table.
This table stores different calendar services that the system might integrate with (e.g., Google Calendar, Outlook Calendar).
"""

import logging
from typing import Optional # If adding specific optional fields
from datetime import datetime, timezone # For __main__ example

from sqlalchemy.orm import Mapped, mapped_column # If adding specific fields
from sqlalchemy import String # If adding specific fields

from backend.app.src.models.dictionaries.base_dict import BaseDictionaryModel

# Configure logger for this module
logger = logging.getLogger(__name__)

class CalendarProvider(BaseDictionaryModel):
    """
    Represents a calendar provider service in a dictionary table (e.g., Google Calendar, Outlook Calendar, Apple Calendar).
    Inherits common fields from BaseDictionaryModel.

    The 'code' field will be important (e.g., 'GOOGLE_CALENDAR', 'OUTLOOK_CALENDAR').
    The 'name' would be 'Google Calendar', 'Outlook Calendar'.
    """
    __tablename__ = "dict_calendar_providers"

    # Add any fields specific to 'CalendarProvider' that are not in BaseDictionaryModel.
    # For example, an icon URL for the provider or specific API endpoint hints (though actual endpoints are better in config).
    # icon_url: Mapped[Optional[str]] = mapped_column(
    #     String(512),
    #     nullable=True,
    #     comment="URL to an icon representing this calendar provider."
    # )
    # integration_docs_url: Mapped[Optional[str]] = mapped_column(
    #     String(512),
    #     nullable=True,
    #     comment="Link to documentation for integrating with this provider."
    # )

    def __repr__(self) -> str:
        return super().__repr__() # BaseDictionaryModel provides a good default

if __name__ == "__main__":
    # This block is for demonstration of the CalendarProvider model structure.
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- CalendarProvider Dictionary Model --- Demonstration")

    # Example instances of CalendarProvider
    google_calendar = CalendarProvider(
        code="GOOGLE_CALENDAR",
        name="Google Calendar",
        description="Integration with Google Calendar for task and event synchronization.",
        state="active",
        display_order=1
        # icon_url="https://example.com/icons/google_calendar.png" # If field was added
    )
    google_calendar.id = 1 # Simulate ORM-set ID
    google_calendar.created_at = datetime.now(timezone.utc) # Simulate timestamp
    google_calendar.updated_at = datetime.now(timezone.utc) # Simulate timestamp
    logger.info(f"Example CalendarProvider: {google_calendar!r}, Description: {google_calendar.description}")
    # if hasattr(google_calendar, 'icon_url'):
    #     logger.info(f"  Icon URL: {google_calendar.icon_url}")

    outlook_calendar = CalendarProvider(
        code="OUTLOOK_CALENDAR",
        name="Outlook Calendar",
        description="Integration with Outlook Calendar.",
        state="active",
        display_order=2
    )
    outlook_calendar.id = 2
    outlook_calendar.created_at = datetime.now(timezone.utc)
    outlook_calendar.updated_at = datetime.now(timezone.utc)
    logger.info(f"Example CalendarProvider: {outlook_calendar!r}, Name: {outlook_calendar.name}")

    # Show inherited and specific attributes (if any were added)
    # from sqlalchemy import create_engine
    # from backend.app.src.config.database import Base # Ensure Base is correctly imported
    # engine = create_engine("sqlite:///:memory:")
    # Base.metadata.create_all(engine) # This would create all tables defined using this Base
    # logger.info(f"Columns in CalendarProvider ({CalendarProvider.__tablename__}): {[c.name for c in CalendarProvider.__table__.columns]}")
    logger.info("To see actual table columns, SQLAlchemy metadata needs to be initialized with an engine (e.g., Base.metadata.create_all(engine)).")
