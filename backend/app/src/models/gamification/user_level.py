# backend/app/src/models/gamification/user_level.py

"""
SQLAlchemy model for UserLevel, representing the levels achieved by users.
This acts as an association between Users and Levels, potentially storing when a level was achieved.
"""

import logging
from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone # Added timezone for __main__

from sqlalchemy import ForeignKey, DateTime, UniqueConstraint, Integer # Added Integer for FKs
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func # For server_default on achieved_at

from backend.app.src.models.base import BaseModel # UserLevel records are simpler entities

# Configure logger for this module
logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from backend.app.src.models.auth.user import User
    from backend.app.src.models.gamification.level import Level
    from backend.app.src.models.groups.group import Group # If user's level is tracked per group

class UserLevel(BaseModel):
    """
    Represents a user achieving a specific gamification level, potentially within a group context.
    If a user can have different levels in different groups, group_id is crucial.
    If levels are global, group_id might be omitted or nullable.

    Attributes:
        user_id (int): Foreign key to the user who achieved the level.
        level_id (int): Foreign key to the gamification level achieved.
        group_id (int): Foreign key to the group in which this level was achieved.
        achieved_at (datetime): Timestamp when the user achieved this level.
        # `id`, `created_at`, `updated_at` from BaseModel.
    """
    __tablename__ = "gamification_user_levels"

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="FK to the user")
    level_id: Mapped[int] = mapped_column(Integer, ForeignKey("gamification_levels.id"), nullable=False, index=True, comment="FK to the achieved level")
    group_id: Mapped[int] = mapped_column(Integer, ForeignKey("groups.id"), nullable=False, index=True, comment="FK to the group where this level was achieved")

    achieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp when the user achieved this level (UTC)"
    )
    # is_current_level: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True, comment="Is this the user's current highest level in this group? Might need logic to maintain.")

    # --- Relationships ---
    user: Mapped["User"] = relationship() # One-way or add back_populates="achieved_levels" to User
    level: Mapped["Level"] = relationship() # One-way or add back_populates="user_level_achievements" to Level
    group: Mapped["Group"] = relationship() # One-way or add back_populates="user_levels_in_group" to Group

    # --- Table Arguments ---
    # A user should typically only achieve a specific level within a specific group once.
    # Or, if levels are progressive, this table might only store the *current* level.
    # If it stores history, then (user_id, level_id, group_id) might not be unique if re-achievable.
    # For now, assume it's the record of achieving a level.
    # If only current level is stored per user per group, then (user_id, group_id) should be unique.
    # If UserLevel stores each level progression, then (user_id, level_id, group_id) could be unique.
    __table_args__ = (
        UniqueConstraint('user_id', 'group_id', 'level_id', name='uq_user_group_level_achievement'),
        # If storing only the current level per user per group:
        # UniqueConstraint('user_id', 'group_id', name='uq_user_current_level_in_group'),
    )

    def __repr__(self) -> str:
        id_val = getattr(self, 'id', 'N/A')
        return f"<UserLevel(id={id_val}, user_id={self.user_id}, group_id={self.group_id}, level_id={self.level_id})>"

if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- UserLevel Model (Gamification) --- Demonstration")

    # Example UserLevel instance
    # Assume User id=1, Level id=1 (Apprentice), Group id=1 exist
    user_achieved_level1 = UserLevel(
        user_id=1,
        level_id=1,
        group_id=1
        # achieved_at is auto-set by server_default
    )
    user_achieved_level1.id = 1 # Simulate ORM-set ID
    user_achieved_level1.created_at = datetime.now(timezone.utc) # Simulate BaseModel field
    user_achieved_level1.updated_at = datetime.now(timezone.utc) # Simulate BaseModel field
    if not getattr(user_achieved_level1, 'achieved_at', None): # For demo if server_default not active
        user_achieved_level1.achieved_at = datetime.now(timezone.utc)

    logger.info(f"Example UserLevel: {user_achieved_level1!r}")
    logger.info(f"  User ID: {user_achieved_level1.user_id}, Group ID: {user_achieved_level1.group_id}, Level ID: {user_achieved_level1.level_id}")
    logger.info(f"  Achieved At: {user_achieved_level1.achieved_at.isoformat() if user_achieved_level1.achieved_at else 'N/A'}")
    logger.info(f"  Created At: {user_achieved_level1.created_at.isoformat() if user_achieved_level1.created_at else 'N/A'}")


    # The following line would error if run directly without SQLAlchemy engine and metadata setup for all related tables.
    # logger.info(f"UserLevel attributes (conceptual table columns): {[c.name for c in UserLevel.__table__.columns if not c.name.startswith('_')]}")
    logger.info("To see actual table columns, SQLAlchemy metadata needs to be initialized with an engine (e.g., Base.metadata.create_all(engine)).")
