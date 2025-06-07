# backend/app/src/models/dictionaries/statuses.py

"""
SQLAlchemy model for a 'Status' dictionary table.
This table can store various statuses used across the application (e.g., task status, user status).
"""

import logging
from typing import Optional # For Mapped[Optional[str]] if any field is optional
from datetime import datetime, timezone # For __main__ example

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String # Example if adding specific fields not in base

from backend.app.src.models.dictionaries.base_dict import BaseDictionaryModel

# Configure logger for this module
logger = logging.getLogger(__name__)

class Status(BaseDictionaryModel):
    """
    Represents a status entry in a dictionary table.
    Inherits common fields (id, code, name, description, state, is_default, display_order, etc.)
    from BaseDictionaryModel.

    This model can be used to define statuses for various entities like tasks, users, orders, etc.
    The 'state' field from BaseDictionaryModel can be used to further categorize statuses
    (e.g., a status with code 'COMPLETED' might have a state 'final').
    """
    __tablename__ = "dict_statuses" # Explicitly naming dictionary tables with a prefix can be good practice

    # Add any fields specific to 'Status' that are not in BaseDictionaryModel.
    # For example, you might want a color associated with a status for UI purposes:
    # color_hex: Mapped[Optional[str]] = mapped_column(String(7), comment="Hex color code for UI representation (e.g., #FF0000)")

    # Or a field to categorize the status itself, if 'state' on BaseDictionaryModel is used differently:
    # category: Mapped[Optional[str]] = mapped_column(String(100), index=True, comment="Category this status belongs to (e.g., 'TaskWorkflow', 'UserLifecycle')")

    def __repr__(self) -> str:
        # BaseDictionaryModel already provides a good __repr__
        # You can override it if you want to include more Status-specific fields
        return super().__repr__()

if __name__ == "__main__":
    # This block is for demonstration of the Status model structure.
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- Status Dictionary Model --- Demonstration")

    # Example instance of Status
    active_status = Status(
        code="ACTIVE",
        name="Active",
        description="Indicates that an entity is currently active and operational.",
        state="enabled", # Example usage of the 'state' field from BaseDictionaryModel
        is_default=True,
        display_order=1,
        # color_hex="#00FF00" # If 'color_hex' field were added
    )
    # Simulate ORM-set fields for demo
    active_status.id = 1
    active_status.created_at = datetime.now(timezone.utc) # Simulate timestamp
    active_status.updated_at = datetime.now(timezone.utc) # Simulate timestamp

    logger.info(f"Example Status instance: {active_status!r}")
    logger.info(f"  Code: {active_status.code}")
    logger.info(f"  Name: {active_status.name}")
    logger.info(f"  Description: {active_status.description}")
    logger.info(f"  State: {active_status.state}")
    logger.info(f"  Is Default: {active_status.is_default}")
    logger.info(f"  Display Order: {active_status.display_order}")
    # logger.info(f"  Color: {active_status.color_hex}") # If 'color_hex' field were added
    logger.info(f"  Created At: {active_status.created_at.isoformat() if active_status.created_at else 'N/A'}")


    pending_status = Status(
        code="PENDING_APPROVAL",
        name="Pending Approval",
        description="Item is awaiting approval before becoming active.",
        state="awaiting_action",
        display_order=2
    )
    pending_status.id = 2
    pending_status.created_at = datetime.now(timezone.utc)
    pending_status.updated_at = datetime.now(timezone.utc)
    logger.info(f"Another Status instance: {pending_status!r}")
    logger.info(f"  Is Default (not set, defaults to False via Mapped): {pending_status.is_default}")


    # Show inherited and specific attributes
    # To inspect actual columns, you would need to initialize Base.metadata with an engine
    # from sqlalchemy import create_engine
    # from backend.app.src.config.database import Base # Ensure Base is correctly imported
    # engine = create_engine("sqlite:///:memory:")
    # Base.metadata.create_all(engine) # This would create all tables defined using this Base
    # logger.info(f"Columns in Status ({Status.__tablename__}): {[c.name for c in Status.__table__.columns]}")
    # Expected columns: id, created_at, updated_at, name, description, state, deleted_at, notes, code, is_default, display_order
    # Plus any custom fields like 'color_hex' or 'category' if added.
    logger.info("To see actual table columns, SQLAlchemy metadata needs to be initialized with an engine (e.g., Base.metadata.create_all(engine)).")
