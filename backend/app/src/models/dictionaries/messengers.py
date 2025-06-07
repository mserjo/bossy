# backend/app/src/models/dictionaries/messengers.py

"""
SQLAlchemy model for a 'MessengerPlatform' dictionary table.
This table stores different messaging platforms that the system might integrate with for notifications (e.g., Telegram, Slack, Viber).
"""

import logging
from typing import Optional # If adding specific optional fields
from datetime import datetime, timezone # For __main__ example

from sqlalchemy.orm import Mapped, mapped_column # If adding specific fields
from sqlalchemy import Boolean, Text # If adding specific fields

from backend.app.src.models.dictionaries.base_dict import BaseDictionaryModel

# Configure logger for this module
logger = logging.getLogger(__name__)

class MessengerPlatform(BaseDictionaryModel):
    """
    Represents a messaging platform in a dictionary table (e.g., Telegram, Slack, Viber, Email, SMS).
    Inherits common fields from BaseDictionaryModel.

    The 'code' field will be important (e.g., 'TELEGRAM', 'SLACK', 'EMAIL_INTERNAL').
    The 'name' would be 'Telegram', 'Slack', etc.
    """
    __tablename__ = "dict_messenger_platforms"

    # Add any fields specific to 'MessengerPlatform' that are not in BaseDictionaryModel.
    # For example, capabilities of the platform or typical use cases.
    # supports_rich_text: Mapped[bool] = mapped_column(
    #     Boolean,
    #     default=False,
    #     nullable=False,
    #     comment="Does this platform support rich text formatting for notifications?"
    # )
    # api_rate_limit_notes: Mapped[Optional[str]] = mapped_column(
    #     Text,
    #     nullable=True,
    #     comment="Notes on API rate limits or specific integration considerations."
    # )

    def __repr__(self) -> str:
        return super().__repr__() # BaseDictionaryModel provides a good default

if __name__ == "__main__":
    # This block is for demonstration of the MessengerPlatform model structure.
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- MessengerPlatform Dictionary Model --- Demonstration")

    # Example instances of MessengerPlatform
    telegram_platform = MessengerPlatform(
        code="TELEGRAM",
        name="Telegram",
        description="Integration with Telegram for sending notifications.",
        state="active",
        display_order=1
        # supports_rich_text=True, # If field was added
    )
    telegram_platform.id = 1 # Simulate ORM-set ID
    telegram_platform.created_at = datetime.now(timezone.utc) # Simulate timestamp
    telegram_platform.updated_at = datetime.now(timezone.utc) # Simulate timestamp
    logger.info(f"Example MessengerPlatform: {telegram_platform!r}, Description: {telegram_platform.description}")
    # if hasattr(telegram_platform, 'supports_rich_text'):
    #     logger.info(f"  Supports Rich Text: {telegram_platform.supports_rich_text}")

    slack_platform = MessengerPlatform(
        code="SLACK",
        name="Slack",
        description="Integration with Slack for team notifications.",
        state="active",
        display_order=2
    )
    slack_platform.id = 2
    slack_platform.created_at = datetime.now(timezone.utc)
    slack_platform.updated_at = datetime.now(timezone.utc)
    logger.info(f"Example MessengerPlatform: {slack_platform!r}, Name: {slack_platform.name}")

    email_platform = MessengerPlatform(
        code="EMAIL_INTERNAL", # Using 'INTERNAL' to distinguish from general email if needed
        name="Email (via Internal SMTP)",
        description="Sending notifications via the configured SMTP email service.",
        state="active",
        display_order=3
    )
    email_platform.id = 3
    email_platform.created_at = datetime.now(timezone.utc)
    email_platform.updated_at = datetime.now(timezone.utc)
    logger.info(f"Example MessengerPlatform: {email_platform!r}, Is Default: {email_platform.is_default}")

    # Show inherited and specific attributes (if any were added)
    # from sqlalchemy import create_engine
    # from backend.app.src.config.database import Base # Ensure Base is correctly imported
    # engine = create_engine("sqlite:///:memory:")
    # Base.metadata.create_all(engine) # This would create all tables defined using this Base
    # logger.info(f"Columns in MessengerPlatform ({MessengerPlatform.__tablename__}): {[c.name for c in MessengerPlatform.__table__.columns]}")
    logger.info("To see actual table columns, SQLAlchemy metadata needs to be initialized with an engine (e.g., Base.metadata.create_all(engine)).")
