# backend/app/src/models/dictionaries/bonus_types.py

"""
SQLAlchemy model for a 'BonusType' dictionary table.
This table stores different types or categories of bonuses or penalties
(e.g., TaskCompletionBonus, EarlyCompletionBonus, LateSubmissionPenalty).
"""

import logging
from typing import Optional # If adding specific optional fields
from datetime import datetime, timezone # For __main__ example

from sqlalchemy.orm import Mapped, mapped_column # If adding specific fields
from sqlalchemy import Boolean, Integer # If adding specific fields

from backend.app.src.models.dictionaries.base_dict import BaseDictionaryModel

# Configure logger for this module
logger = logging.getLogger(__name__)

class BonusType(BaseDictionaryModel):
    """
    Represents a type of bonus or penalty in a dictionary table.
    Examples: Task Completion, Streak Bonus, Late Penalty, Referral Bonus.
    Inherits common fields from BaseDictionaryModel.

    The 'code' field will be important (e.g., 'TASK_COMPLETION', 'STREAK_7_DAYS', 'LATE_PENALTY').
    """
    __tablename__ = "dict_bonus_types"

    # Add any fields specific to 'BonusType' that are not in BaseDictionaryModel.
    # For example, whether this type is typically a bonus (positive points) or penalty (negative points).
    # is_penalty_type: Mapped[bool] = mapped_column(
    #     Boolean,
    #     default=False,
    #     nullable=False,
    #     comment="True if this type typically results in negative points (a penalty)."
    # )
    # default_point_impact: Mapped[Optional[int]] = mapped_column(
    #     Integer,
    #     nullable=True,
    #     comment="Default points awarded or deducted for this bonus type. Can be overridden by specific BonusRule."
    # )

    def __repr__(self) -> str:
        return super().__repr__() # BaseDictionaryModel provides a good default

if __name__ == "__main__":
    # This block is for demonstration of the BonusType model structure.
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- BonusType Dictionary Model --- Demonstration")

    # Example instances of BonusType
    task_completion_bonus = BonusType(
        code="TASK_COMPLETION",
        name="Task Completion Bonus",
        description="Standard bonus awarded for successfully completing a task.",
        state="active",
        display_order=1
        # is_penalty_type=False, # If field was added
        # default_point_impact=20 # If field was added
    )
    task_completion_bonus.id = 1 # Simulate ORM-set ID
    task_completion_bonus.created_at = datetime.now(timezone.utc) # Simulate timestamp
    task_completion_bonus.updated_at = datetime.now(timezone.utc) # Simulate timestamp
    logger.info(f"Example BonusType: {task_completion_bonus!r}, Description: {task_completion_bonus.description}")
    # if hasattr(task_completion_bonus, 'is_penalty_type'):
    #     logger.info(f"  Is Penalty Type: {task_completion_bonus.is_penalty_type}")

    late_penalty = BonusType(
        code="LATE_SUBMISSION_PENALTY",
        name="Late Submission Penalty",
        description="Penalty applied for submitting a task after its due date.",
        state="active",
        display_order=10
        # is_penalty_type=True, # If field was added
        # default_point_impact=-5 # If field was added
    )
    late_penalty.id = 2
    late_penalty.created_at = datetime.now(timezone.utc)
    late_penalty.updated_at = datetime.now(timezone.utc)
    logger.info(f"Example BonusType: {late_penalty!r}, Name: {late_penalty.name}")

    streak_bonus = BonusType(
        code="STREAK_BONUS_7_DAY",
        name="7-Day Streak Bonus",
        description="Bonus for completing tasks consecutively for 7 days.",
        state="active",
        display_order=3
    )
    streak_bonus.id = 3
    streak_bonus.created_at = datetime.now(timezone.utc)
    streak_bonus.updated_at = datetime.now(timezone.utc)
    logger.info(f"Example BonusType: {streak_bonus!r}, Is Default: {streak_bonus.is_default}") # is_default is False by default

    # Show inherited and specific attributes (if any were added)
    # from sqlalchemy import create_engine
    # from backend.app.src.config.database import Base # Ensure Base is correctly imported
    # engine = create_engine("sqlite:///:memory:")
    # Base.metadata.create_all(engine) # This would create all tables defined using this Base
    # logger.info(f"Columns in BonusType ({BonusType.__tablename__}): {[c.name for c in BonusType.__table__.columns]}")
    logger.info("To see actual table columns, SQLAlchemy metadata needs to be initialized with an engine (e.g., Base.metadata.create_all(engine)).")
