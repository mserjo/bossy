# backend/app/src/models/gamification/badge.py

"""
SQLAlchemy model for Badges in the gamification system.
Badges are visual representations of achievements or recognitions.
"""

import logging
from typing import Optional, TYPE_CHECKING, List, Dict, Any # Added List, Dict, Any for potential fields
from datetime import datetime, timezone # Added for __main__

from sqlalchemy import String, Text, ForeignKey, Integer, JSON # Added Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.src.models.base import BaseGroupAffiliatedMainModel # Badges can be group-specific

# Configure logger for this module
logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    # from backend.app.src.models.groups.group import Group # Handled by BaseGroupAffiliatedMainModel
    from backend.app.src.models.gamification.user_achievement import UserAchievement # For back_populates
    # from backend.app.src.models.files.file import FileRecord # If icon_url is a FK to a FileRecord


class Badge(BaseGroupAffiliatedMainModel): # Inherits id, name, description, state, notes, group_id, created_at, updated_at, deleted_at
    """
    Represents a badge that users can earn as a form of achievement or recognition.
    The 'name' (e.g., "Task Master", "Helpful Hand") and 'description' (criteria) are inherited.
    """
    __tablename__ = "gamification_badges"

    # 'name' (e.g., "First Task Completed", "Community Helper") & 'description' inherited.
    # 'group_id' inherited, making badges potentially specific to a group.
    # If BaseGroupAffiliatedMainModel.group_id is not nullable, global badges would need a different base or a sentinel 'global' group ID.
    # 'state' can be 'active', 'retired'.

    icon_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True, comment="URL or path to an icon representing this badge")
    # Alternatively, icon_file_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("file_records.id"), nullable=True)

    criteria_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="Detailed, human-readable criteria for earning this badge (supplements the main description)")
    # For more complex, machine-readable criteria, a JSON field or separate criteria models might be used.
    # criteria_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True, comment="Structured criteria for automatic awarding")

    # --- Relationships ---
    # Group relationship is inherited via BaseGroupAffiliatedMainModel if that base defines the relationship object.
    # If not, and group_id is just an FK from a mixin, define it here:
    # from backend.app.src.models.groups.group import Group # Ensure Group is imported
    # group: Mapped["Group"] = relationship(foreign_keys="Badge.group_id") # Assuming group_id is on Badge (it is via BaseGroupAffiliatedMainModel)


    # If icon is a FileRecord:
    # icon_file: Mapped[Optional["FileRecord"]] = relationship(foreign_keys=[icon_file_id])

    # Relationship to UserAchievement (users who have earned this badge)
    user_achievements: Mapped[List["UserAchievement"]] = relationship(back_populates="badge")

    def __repr__(self) -> str:
        id_val = getattr(self, 'id', 'N/A')
        group_id_val = getattr(self, 'group_id', 'N/A') # group_id might be None if allowed by base
        return f"<Badge(id={id_val}, name='{self.name}', group_id={group_id_val})>"

if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- Badge Model (Gamification) --- Demonstration")

    # Example Badge instances
    # Assume Group id=1 exists
    # For global badges, group_id might be None if BaseGroupAffiliatedMainModel allows it.
    # If not, a sentinel global group ID or a different base model for global badges would be needed.
    # Let's assume BaseGroupAffiliatedMainModel.group_id is nullable for this demo.

    # Check if group_id is nullable in the base model.
    # This is a conceptual check; direct inspection of SQLAlchemy column properties is more complex outside a session.
    is_group_id_nullable_in_base = True # Assume true for demo, or check BaseGroupAffiliatedMainModel.group_id.nullable

    global_badge_group_id = None
    if not is_group_id_nullable_in_base:
        logger.warning("BaseGroupAffiliatedMainModel.group_id is not nullable. Using placeholder '0' for global badge's group_id.")
        global_badge_group_id = 0 # Placeholder for a 'global' group if group_id is not nullable

    first_task_badge = Badge(
        name="First Task Conqueror",
        description="Awarded for completing your very first task in any group.",
        group_id=global_badge_group_id,
        icon_url="/static/icons/badges/first_task.png",
        criteria_description="Complete any one task successfully.",
        state="active" # From BaseGroupAffiliatedMainModel
    )
    first_task_badge.id = 1 # Simulate ORM-set ID
    first_task_badge.created_at = datetime.now(timezone.utc) # Simulate timestamp
    first_task_badge.updated_at = datetime.now(timezone.utc) # Simulate timestamp


    logger.info(f"Example Global Badge: {first_task_badge!r}")
    logger.info(f"  Name: {first_task_badge.name}")
    logger.info(f"  Criteria: {first_task_badge.criteria_description}")
    logger.info(f"  Group ID (for global): {first_task_badge.group_id}")
    logger.info(f"  Created At: {first_task_badge.created_at.isoformat() if first_task_badge.created_at else 'N/A'}")


    group_streak_badge = Badge(
        name="Group Task Streak (5)",
        description="Awarded for completing 5 tasks in a row within this group.",
        group_id=1, # Specific to group 1
        icon_url="/static/icons/badges/group_streak_5.png",
        state="active"
    )
    group_streak_badge.id = 2
    logger.info(f"Example Group-Specific Badge: {group_streak_badge!r}")

    # The following line would error if run directly without SQLAlchemy engine and metadata setup for all related tables.
    # logger.info(f"Badge attributes (conceptual table columns): {[c.name for c in Badge.__table__.columns if not c.name.startswith('_')]}")
    logger.info("To see actual table columns, SQLAlchemy metadata needs to be initialized with an engine (e.g., Base.metadata.create_all(engine)).")
