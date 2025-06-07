# backend/app/src/models/tasks/review.py

"""
SQLAlchemy model for Task Reviews, allowing users to provide feedback or ratings on tasks.
"""

import logging
from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone # Added timezone for __main__

from sqlalchemy import ForeignKey, Text, Integer, CheckConstraint # Added Integer for FKs
from sqlalchemy.orm import Mapped, mapped_column, relationship
# from sqlalchemy.sql import func # Not strictly needed here unless using server_default for review_date

from backend.app.src.models.base import BaseModel

# Configure logger for this module
logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from backend.app.src.models.auth.user import User
    from backend.app.src.models.tasks.task import Task

class TaskReview(BaseModel):
    """
    Represents a review or feedback provided by a user for a specific task.
    This could be a star rating, a comment, or both.

    Attributes:
        task_id (int): Foreign key to the task being reviewed.
        user_id (int): Foreign key to the user who submitted the review.
        rating (Optional[int]): A numerical rating (e.g., 1 to 5 stars).
        comment (Optional[str]): Textual feedback or comment from the user.
        # `id`, `created_at` (review_date), `updated_at` are inherited from BaseModel.
        # `created_at` can effectively serve as `review_date`.
    """
    __tablename__ = "task_reviews"

    task_id: Mapped[int] = mapped_column(Integer, ForeignKey("tasks.id"), nullable=False, index=True, comment="FK to the task being reviewed")
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="FK to the user who submitted the review")

    rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="Numerical rating, e.g., 1-5 stars. Null if only comment provided.")
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="Textual comment or feedback provided by the user")

    # --- Relationships ---
    task: Mapped["Task"] = relationship(back_populates="reviews")
    user: Mapped["User"] = relationship() # One-way relationship to User, or add back_populates="task_reviews" to User model

    # --- Table Arguments ---
    __table_args__ = (
        CheckConstraint('rating IS NULL OR (rating >= 1 AND rating <= 5)', name='chk_rating_range'),
        # Potentially a UniqueConstraint to allow a user to review a task only once:
        # from sqlalchemy import UniqueConstraint # Import if using
        # UniqueConstraint('task_id', 'user_id', name='uq_user_task_review'),
    )

    def __repr__(self) -> str:
        id_val = getattr(self, 'id', 'N/A')
        return f"<TaskReview(id={id_val}, task_id={self.task_id}, user_id={self.user_id}, rating={self.rating})>"

if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- TaskReview Model --- Demonstration")

    # Example TaskReview instance
    # Assume Task id=1, User id=1 exist
    review1 = TaskReview(
        task_id=1,
        user_id=1,
        rating=5,
        comment="Excellent task, very clear instructions!"
    )
    review1.id = 1 # Simulate ORM-set ID
    review1.created_at = datetime.now(timezone.utc) # Simulate BaseModel field
    review1.updated_at = datetime.now(timezone.utc) # Simulate BaseModel field

    logger.info(f"Example TaskReview: {review1!r}")
    logger.info(f"  Task ID: {review1.task_id}, User ID: {review1.user_id}")
    logger.info(f"  Rating: {review1.rating}")
    logger.info(f"  Comment: {review1.comment}")
    logger.info(f"  Review Date (created_at): {review1.created_at.isoformat() if review1.created_at else 'N/A'}")


    review2_comment_only = TaskReview(
        task_id=2, # Assuming task 2 exists
        user_id=3, # Assuming user 3 exists
        comment="This task was a bit confusing at first."
    )
    review2_comment_only.id = 2
    logger.info(f"Example TaskReview (comment only): {review2_comment_only!r}")
    logger.info(f"  Rating (should be None): {review2_comment_only.rating}")

    # Example of a review that might fail a check constraint (if DB was active)
    # review_invalid_rating = TaskReview(task_id=1, user_id=2, rating=0)
    # logger.info(f"Example invalid rating (conceptual): {review_invalid_rating!r}")

    # The following line would error if run directly without SQLAlchemy engine and metadata setup for all related tables.
    # logger.info(f"TaskReview attributes (conceptual table columns): {[c.name for c in TaskReview.__table__.columns if not c.name.startswith('_')]}")
    logger.info("To see actual table columns, SQLAlchemy metadata needs to be initialized with an engine (e.g., Base.metadata.create_all(engine)).")
