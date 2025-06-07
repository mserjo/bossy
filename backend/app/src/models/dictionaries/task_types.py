# backend/app/src/models/dictionaries/task_types.py

"""
SQLAlchemy model for a 'TaskType' dictionary table.
This table stores different types or categories of tasks (e.g., Chore, Work Item, Reminder, Event Sub-Type).
"""

import logging
from typing import Optional # If adding specific optional fields
from datetime import datetime, timezone # For __main__ example

from sqlalchemy.orm import Mapped, mapped_column # If adding specific fields
from sqlalchemy import Boolean, Integer # If adding specific fields

from backend.app.src.models.dictionaries.base_dict import BaseDictionaryModel

# Configure logger for this module
logger = logging.getLogger(__name__)

class TaskType(BaseDictionaryModel):
    """
    Represents a type of task in a dictionary table (e.g., Chore, Work Item, Bug, Feature, Reminder).
    Inherits common fields from BaseDictionaryModel.

    The 'code' field will be key (e.g., 'CHORE', 'WORK_ITEM', 'BUG').
    The 'description' can explain what this type of task generally entails.
    """
    __tablename__ = "dict_task_types"

    # Add any fields specific to 'TaskType' that are not in BaseDictionaryModel.
    # For example, a flag to indicate if tasks of this type typically award points:
    # awards_points_by_default: Mapped[bool] = mapped_column(
    #     Boolean,
    #     default=True,
    #     nullable=False,
    #     comment="Does this task type generally result in points/bonus upon completion?"
    # )
    # default_points_value: Mapped[Optional[int]] = mapped_column(
    #     Integer,
    #     nullable=True,
    #     comment="Default points value for tasks of this type, if applicable."
    # )

    def __repr__(self) -> str:
        return super().__repr__() # BaseDictionaryModel provides a good default

if __name__ == "__main__":
    # This block is for demonstration of the TaskType model structure.
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- TaskType Dictionary Model --- Demonstration")

    # Example instances of TaskType
    chore_type = TaskType(
        code="CHORE",
        name="Chore",
        description="A routine household task or personal errand.",
        state="active",
        display_order=1
        # awards_points_by_default=True, # If field was added
        # default_points_value=10      # If field was added
    )
    chore_type.id = 1 # Simulate ORM-set ID
    chore_type.created_at = datetime.now(timezone.utc) # Simulate timestamp
    chore_type.updated_at = datetime.now(timezone.utc) # Simulate timestamp
    logger.info(f"Example TaskType: {chore_type!r}, Description: {chore_type.description}")
    # if hasattr(chore_type, 'awards_points_by_default'):
    #     logger.info(f"  Awards Points by Default: {chore_type.awards_points_by_default}")

    work_item_type = TaskType(
        code="WORK_ITEM",
        name="Work Item",
        description="A task related to professional work or a project.",
        state="active",
        display_order=2
        # awards_points_by_default=False # If field was added
    )
    work_item_type.id = 2
    work_item_type.created_at = datetime.now(timezone.utc)
    work_item_type.updated_at = datetime.now(timezone.utc)
    logger.info(f"Example TaskType: {work_item_type!r}, Name: {work_item_type.name}")

    reminder_type = TaskType(
        code="REMINDER",
        name="Reminder",
        description="A simple reminder for an upcoming event or action.",
        state="active",
        display_order=3,
        # awards_points_by_default=False # If field was added
    )
    reminder_type.id = 3
    reminder_type.created_at = datetime.now(timezone.utc)
    reminder_type.updated_at = datetime.now(timezone.utc)
    logger.info(f"Example TaskType: {reminder_type!r}, Is Default: {reminder_type.is_default}") # is_default is False by default

    # Show inherited and specific attributes (if any were added)
    # from sqlalchemy import create_engine
    # from backend.app.src.config.database import Base # Ensure Base is correctly imported
    # engine = create_engine("sqlite:///:memory:")
    # Base.metadata.create_all(engine) # This would create all tables defined using this Base
    # logger.info(f"Columns in TaskType ({TaskType.__tablename__}): {[c.name for c in TaskType.__table__.columns]}")
    logger.info("To see actual table columns, SQLAlchemy metadata needs to be initialized with an engine (e.g., Base.metadata.create_all(engine)).")
