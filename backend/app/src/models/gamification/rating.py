# backend/app/src/models/gamification/rating.py

"""
SQLAlchemy model for UserGroupRating, storing user ratings or scores within groups for specific periods.
"""

import logging
from typing import Optional, TYPE_CHECKING
from datetime import datetime, date, timezone # Added date for period_start/end and timezone for __main__
from decimal import Decimal # For score, to maintain precision

from sqlalchemy import ForeignKey, Date, Numeric, Integer, String, Index, UniqueConstraint # Added Integer, String, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.src.models.base import BaseModel # Ratings are simpler records

# Configure logger for this module
logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from backend.app.src.models.auth.user import User
    from backend.app.src.models.groups.group import Group

class UserGroupRating(BaseModel):
    """
    Represents a user's rating or score within a specific group, often for a defined period (e.g., weekly, monthly leaderboard).

    Attributes:
        user_id (int): Foreign key to the user.
        group_id (int): Foreign key to the group where the rating is applicable.
        rating_period_identifier (str): A string identifier for the rating period (e.g., '2023-W52', '2023-12', 'overall').
        score (Decimal): The calculated score or rating for the user in this group for this period.
        rank (Optional[int]): The user's rank within the group for this period and score.
        # `id`, `created_at`, `updated_at` from BaseModel.
        # `created_at` can signify when the rating was calculated/recorded.
    """
    __tablename__ = "gamification_user_group_ratings"

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="FK to the user being rated")
    group_id: Mapped[int] = mapped_column(Integer, ForeignKey("groups.id"), nullable=False, index=True, comment="FK to the group context of the rating")

    # Instead of separate start/end dates, a period identifier might be more flexible for various schemes (weekly, monthly, all-time)
    # Or, define specific period tables if periods are complex entities themselves.
    rating_period_identifier: Mapped[str] = mapped_column(String(100), nullable=False, index=True, comment="Identifier for the rating period (e.g., '2023-W52', '2023-12', 'SEASON_1')")
    # rating_period_start: Mapped[date] = mapped_column(Date, nullable=False, index=True, comment="Start date of the rating period")
    # rating_period_end: Mapped[date] = mapped_column(Date, nullable=False, index=True, comment="End date of the rating period")

    score: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal('0.00'), comment="Calculated score for the user in this group/period. Precision 12, 2 decimal places.")
    rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="User's rank for this group/period based on the score")

    # --- Relationships ---
    user: Mapped["User"] = relationship() # One-way or add back_populates="group_ratings" to User
    group: Mapped["Group"] = relationship() # One-way or add back_populates="user_ratings" to Group

    # --- Table Arguments ---
    # A user should have one rating entry per group per defined rating period.
    __table_args__ = (
        UniqueConstraint('user_id', 'group_id', 'rating_period_identifier', name='uq_user_group_period_rating'),
        Index('ix_user_group_rating_score_rank', 'group_id', 'rating_period_identifier', 'score', 'rank'), # For leaderboards
    )

    def __repr__(self) -> str:
        id_val = getattr(self, 'id', 'N/A')
        return f"<UserGroupRating(id={id_val}, user_id={self.user_id}, group_id={self.group_id}, period='{self.rating_period_identifier}', score={self.score})>"

if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- UserGroupRating Model (Gamification) --- Demonstration")

    # Example UserGroupRating instance
    # Assume User id=1, Group id=1 exist
    rating_current_month = UserGroupRating(
        user_id=1,
        group_id=1,
        rating_period_identifier="2024-03", # March 2024 rating
        score=Decimal("1250.75"),
        rank=5
    )
    rating_current_month.id = 1 # Simulate ORM-set ID
    rating_current_month.created_at = datetime.now(timezone.utc) # Simulate BaseModel field
    rating_current_month.updated_at = datetime.now(timezone.utc) # Simulate BaseModel field

    logger.info(f"Example UserGroupRating: {rating_current_month!r}")
    logger.info(f"  User ID: {rating_current_month.user_id}, Group ID: {rating_current_month.group_id}")
    logger.info(f"  Period: {rating_current_month.rating_period_identifier}")
    logger.info(f"  Score: {rating_current_month.score}, Rank: {rating_current_month.rank}")
    logger.info(f"  Created At: {rating_current_month.created_at.isoformat() if rating_current_month.created_at else 'N/A'}")


    rating_weekly = UserGroupRating(
        user_id=2,
        group_id=1,
        rating_period_identifier="2024-W10", # Week 10 of 2024
        score=Decimal("300.00"),
        rank=1
    )
    rating_weekly.id = 2
    logger.info(f"Example Weekly UserGroupRating: {rating_weekly!r}")

    # The following line would error if run directly without SQLAlchemy engine and metadata setup for all related tables.
    # logger.info(f"UserGroupRating attributes (conceptual table columns): {[c.name for c in UserGroupRating.__table__.columns if not c.name.startswith('_')]}")
    logger.info("To see actual table columns, SQLAlchemy metadata needs to be initialized with an engine (e.g., Base.metadata.create_all(engine)).")
