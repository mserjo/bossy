# backend/app/src/models/gamification/user_achievement.py

"""
SQLAlchemy model for UserAchievement, linking Users to Badges they have earned.
This was referred to as 'achievement.py' in the original plan, renamed for clarity.
"""

import logging
from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone # Added timezone for __main__

from sqlalchemy import ForeignKey, DateTime, UniqueConstraint, Integer # Added Integer for FKs
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func # For server_default on achieved_at

from backend.app.src.models.base import BaseModel # UserAchievements are simpler records

# Configure logger for this module
logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from backend.app.src.models.auth.user import User
    from backend.app.src.models.gamification.badge import Badge
    from backend.app.src.models.tasks.task import Task # If achievement is linked to a specific task
    from backend.app.src.models.groups.group import Group # If achievements are group-contextual

class UserAchievement(BaseModel):
    """
    Represents a badge earned by a user, possibly within a specific group context
    and potentially linked to a specific task that triggered the achievement.

    Attributes:
        user_id (int): Foreign key to the user who earned the badge.
        badge_id (int): Foreign key to the badge that was earned.
        group_id (Optional[int]): Foreign key to the group in which this achievement was earned (if applicable).
        achieved_at (datetime): Timestamp when the user earned this badge.
        related_task_id (Optional[int]): FK to a task that specifically triggered this achievement (if any).
        # `id`, `created_at`, `updated_at` from BaseModel.
    """
    __tablename__ = "gamification_user_achievements"

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="FK to the user who earned the badge")
    badge_id: Mapped[int] = mapped_column(Integer, ForeignKey("gamification_badges.id"), nullable=False, index=True, comment="FK to the badge earned")
    group_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("groups.id"), nullable=True, index=True, comment="FK to the group where badge was earned (if group-specific badge or context)")

    achieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp when the user earned this badge (UTC)"
    )

    related_task_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("tasks.id"), nullable=True, index=True, comment="Optional FK to a task that triggered this achievement")
    # notification_sent (bool): Could be a field to track if user was notified.

    # --- Relationships ---
    user: Mapped["User"] = relationship() # One-way or add back_populates="user_achievements" to User
    badge: Mapped["Badge"] = relationship(back_populates="user_achievements") # Two-way with Badge
    group: Mapped[Optional["Group"]] = relationship() # One-way or add back_populates to Group
    related_task: Mapped[Optional["Task"]] = relationship() # One-way or add back_populates to Task

    # --- Table Arguments ---
    # A user typically earns a specific badge only once, possibly per group if badges are group-contextual.
    __table_args__ = (
        UniqueConstraint('user_id', 'badge_id', 'group_id', name='uq_user_badge_group_achievement'),
        # If group_id is nullable and a badge can be global or group-specific, this constraint needs care.
        # For purely global badges (badge.group_id is NULL), then UniqueConstraint('user_id', 'badge_id') might be better
        # if achieved globally once. This setup assumes achievement uniqueness includes group context if group_id is present.
        # A more robust way for databases that support NULLs in unique constraints correctly is to have this constraint.
        # For others, two partial unique constraints might be needed (one where group_id IS NULL, one where group_id IS NOT NULL).
    )

    def __repr__(self) -> str:
        id_val = getattr(self, 'id', 'N/A')
        return f"<UserAchievement(id={id_val}, user_id={self.user_id}, badge_id={self.badge_id}, group_id={self.group_id})>"

if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- UserAchievement Model (Gamification) --- Demonstration")

    # Example UserAchievement instance
    # Assume User id=1, Badge id=1 (First Task Conqueror), Group id=1, Task id=101 exist
    achievement1 = UserAchievement(
        user_id=1,
        badge_id=1,
        group_id=1, # Context of the achievement, even if badge is global
        related_task_id=101
        # achieved_at is auto-set by server_default
    )
    achievement1.id = 1 # Simulate ORM-set ID
    achievement1.created_at = datetime.now(timezone.utc) # Simulate BaseModel field
    achievement1.updated_at = datetime.now(timezone.utc) # Simulate BaseModel field
    if not getattr(achievement1, 'achieved_at', None): # For demo if server_default not active
        achievement1.achieved_at = datetime.now(timezone.utc)

    logger.info(f"Example UserAchievement: {achievement1!r}")
    logger.info(f"  User ID: {achievement1.user_id}, Badge ID: {achievement1.badge_id}, Group ID: {achievement1.group_id}")
    logger.info(f"  Achieved At: {achievement1.achieved_at.isoformat() if achievement1.achieved_at else 'N/A'}")
    logger.info(f"  Related Task ID: {achievement1.related_task_id}")
    logger.info(f"  Created At: {achievement1.created_at.isoformat() if achievement1.created_at else 'N/A'}")

    # The following line would error if run directly without SQLAlchemy engine and metadata setup for all related tables.
    # logger.info(f"UserAchievement attributes (conceptual table columns): {[c.name for c in UserAchievement.__table__.columns if not c.name.startswith('_')]}")
    logger.info("To see actual table columns, SQLAlchemy metadata needs to be initialized with an engine (e.g., Base.metadata.create_all(engine)).")
