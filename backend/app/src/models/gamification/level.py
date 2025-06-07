# backend/app/src/models/gamification/level.py

"""
SQLAlchemy model for Levels in the gamification system.
Levels represent milestones achieved by users, typically based on points or experience.
"""

import logging
from typing import Optional, TYPE_CHECKING, List # Added List for user_levels if uncommented
from datetime import datetime, timezone # Added for __main__

from sqlalchemy import String, ForeignKey, Integer # Added Integer for FKs
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.src.models.base import BaseGroupAffiliatedMainModel # Levels can be group-specific

# Configure logger for this module
logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    # from backend.app.src.models.groups.group import Group # Handled by BaseGroupAffiliatedMainModel
    from backend.app.src.models.gamification.user_level import UserLevel # For back_populates if needed
    # from backend.app.src.models.gamification.badge import Badge # If badge_awarded_id is used

class Level(BaseGroupAffiliatedMainModel): # Inherits id, name, description, state, notes, group_id, created_at, updated_at, deleted_at
    """
    Represents a level that users can achieve within a group's gamification system.
    The 'name' (e.g., "Novice", "Expert", "Level 1", "Level 2") and 'description' are inherited.
    """
    __tablename__ = "gamification_levels"

    # 'name' (e.g., "Level 1", "Bronze Tier") & 'description' inherited.
    # 'group_id' inherited, making levels potentially specific to a group.
    # 'state' can be 'active', 'archived'.

    level_number: Mapped[Optional[int]] = mapped_column(Integer, index=True, nullable=True, comment="Optional numerical representation of the level (e.g., 1, 2, 3). Name can be 'Bronze', 'Silver' etc.")
    min_points_required: Mapped[int] = mapped_column(Integer, nullable=False, comment="Minimum points required to achieve this level")

    # A title or badge might be associated with achieving this level.
    # If a Badge model exists, this could be a ForeignKey to a specific 'level-up' badge.
    title_awarded: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="Title awarded to the user upon reaching this level (e.g., 'Grand Master')")
    # badge_awarded_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("gamification_badges.id"), nullable=True, comment="FK to a badge awarded upon reaching this level")

    icon_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True, comment="URL or path to an icon representing this level")

    # --- Relationships ---
    # Group relationship is inherited via BaseGroupAffiliatedMainModel if that base defines the relationship object.
    # If not, and group_id is just an FK from a mixin, define it here:
    # from backend.app.src.models.groups.group import Group # Ensure Group is imported
    # group: Mapped["Group"] = relationship(foreign_keys="Level.group_id") # Assuming group_id is on Level (it is via BaseGroupAffiliatedMainModel)


    # If badge_awarded_id is used:
    # badge_awarded: Mapped[Optional["Badge"]] = relationship(foreign_keys=[badge_awarded_id])

    # Relationship to UserLevel (users who have achieved this level)
    # user_levels: Mapped[List["UserLevel"]] = relationship(back_populates="level")
    # This back_populates would be on UserLevel.level referencing this Level model.

    def __repr__(self) -> str:
        id_val = getattr(self, 'id', 'N/A')
        group_id_val = getattr(self, 'group_id', 'N/A')
        return f"<Level(id={id_val}, name='{self.name}', group_id={group_id_val}, points_req={self.min_points_required})>"

if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- Level Model (Gamification) --- Demonstration")

    # Example Level instances
    # Assume Group id=1 exists
    level1 = Level(
        name="Apprentice",
        description="Starting your journey, learning the ropes.",
        group_id=1,
        level_number=1,
        min_points_required=0,
        title_awarded="Newcomer",
        icon_url="/static/icons/levels/apprentice.png",
        state="active" # from BaseGroupAffiliatedMainModel
    )
    level1.id = 1 # Simulate ORM-set ID
    level1.created_at = datetime.now(timezone.utc) # Simulate timestamp
    level1.updated_at = datetime.now(timezone.utc) # Simulate timestamp

    logger.info(f"Example Level: {level1!r}")
    logger.info(f"  Name: {level1.name}, Level Number: {level1.level_number}")
    logger.info(f"  Min Points: {level1.min_points_required}")
    logger.info(f"  Title Awarded: {level1.title_awarded}")
    logger.info(f"  Created At: {level1.created_at.isoformat() if level1.created_at else 'N/A'}")


    level5_master = Level(
        name="Master Contributor",
        description="You are a true master of tasks and contributions!",
        group_id=1,
        level_number=5,
        min_points_required=10000,
        title_awarded="Task Master",
        state="active"
    )
    level5_master.id = 2
    logger.info(f"Example Level: {level5_master!r}")

    # The following line would error if run directly without SQLAlchemy engine and metadata setup for all related tables.
    # logger.info(f"Level attributes (conceptual table columns): {[c.name for c in Level.__table__.columns if not c.name.startswith('_')]}")
    logger.info("To see actual table columns, SQLAlchemy metadata needs to be initialized with an engine (e.g., Base.metadata.create_all(engine)).")
