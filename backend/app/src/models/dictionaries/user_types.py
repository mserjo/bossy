# backend/app/src/models/dictionaries/user_types.py

"""
SQLAlchemy model for a 'UserType' dictionary table.
This table can store different classifications of users (e.g., Human, Bot, System).
"""

import logging
from typing import Optional # For Mapped[Optional[...]] if any field is optional
from datetime import datetime, timezone # For __main__ example

from sqlalchemy.orm import Mapped, mapped_column # If adding specific fields
from sqlalchemy import Boolean # If adding specific fields like can_login_via_ui

from backend.app.src.models.dictionaries.base_dict import BaseDictionaryModel

# Configure logger for this module
logger = logging.getLogger(__name__)

class UserType(BaseDictionaryModel):
    """
    Represents a type of user in a dictionary table (e.g., Human, Bot, System, ServiceAccount).
    Inherits common fields from BaseDictionaryModel.

    The 'code' field will be important (e.g., 'HUMAN', 'BOT', 'SYSTEM').
    The 'description' can clarify the purpose or nature of the user type.
    """
    __tablename__ = "dict_user_types"

    # Add any fields specific to 'UserType' that are not in BaseDictionaryModel.
    # For example, a flag to indicate if this user type can log in via UI:
    # can_login_via_ui: Mapped[bool] = mapped_column(
    #     Boolean,
    #     default=True,
    #     nullable=False,
    #     comment="Indicates if users of this type can typically log in through a user interface."
    # )

    def __repr__(self) -> str:
        return super().__repr__() # BaseDictionaryModel provides a good default

if __name__ == "__main__":
    # This block is for demonstration of the UserType model structure.
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- UserType Dictionary Model --- Demonstration")

    # Example instances of UserType
    human_user_type = UserType(
        code="HUMAN",
        name="Human User",
        description="A regular human user interacting with the system.",
        state="active",
        display_order=1
        # can_login_via_ui=True # If field was added
    )
    human_user_type.id = 1 # Simulate ORM-set ID
    human_user_type.created_at = datetime.now(timezone.utc) # Simulate timestamp
    human_user_type.updated_at = datetime.now(timezone.utc) # Simulate timestamp
    logger.info(f"Example UserType: {human_user_type!r}, Description: {human_user_type.description}")
    # if hasattr(human_user_type, 'can_login_via_ui'):
    #     logger.info(f"  Can login via UI: {human_user_type.can_login_via_ui}")

    bot_user_type = UserType(
        code="BOT_SERVICE",
        name="Bot/Service Account",
        description="An automated agent or service account performing actions.",
        state="active",
        display_order=2
        # can_login_via_ui=False # If field was added
    )
    bot_user_type.id = 2
    bot_user_type.created_at = datetime.now(timezone.utc)
    bot_user_type.updated_at = datetime.now(timezone.utc)
    logger.info(f"Example UserType: {bot_user_type!r}, Name: {bot_user_type.name}")

    system_user_type = UserType(
        code="SYSTEM_INTERNAL",
        name="System Internal User",
        description="Internal system user for automated processes not directly tied to a bot (e.g., Shadow user for cron jobs).",
        state="active",
        display_order=3
        # can_login_via_ui=False # If field was added
    )
    system_user_type.id = 3
    system_user_type.created_at = datetime.now(timezone.utc)
    system_user_type.updated_at = datetime.now(timezone.utc)
    logger.info(f"Example UserType: {system_user_type!r}, Is Default: {system_user_type.is_default}") # is_default is False by default

    # Show inherited and specific attributes (if any were added)
    # from sqlalchemy import create_engine
    # from backend.app.src.config.database import Base # Ensure Base is correctly imported
    # engine = create_engine("sqlite:///:memory:")
    # Base.metadata.create_all(engine) # This would create all tables defined using this Base
    # logger.info(f"Columns in UserType ({UserType.__tablename__}): {[c.name for c in UserType.__table__.columns]}")
    logger.info("To see actual table columns, SQLAlchemy metadata needs to be initialized with an engine (e.g., Base.metadata.create_all(engine)).")
