# backend/app/src/models/bonuses/reward.py

"""
SQLAlchemy model for Rewards that users can redeem with their points/currency.
"""

import logging
from typing import Optional, TYPE_CHECKING # For Mapped type hints
from datetime import datetime, timezone # Added timezone for __main__

from sqlalchemy import String, Text, Boolean, ForeignKey, Integer # Added Integer for FKs
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.src.models.base import BaseGroupAffiliatedMainModel # Rewards are often group-specific main entities

# Configure logger for this module
logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    # from backend.app.src.models.groups.group import Group # Handled by BaseGroupAffiliatedMainModel
    # from backend.app.src.models.files.file import FileRecord # If icon_url is a FK to a FileRecord
    pass

class Reward(BaseGroupAffiliatedMainModel): # Inherits id, name, description, state, notes, group_id, created_at, updated_at, deleted_at
    """
    Represents a reward that users can redeem using their accumulated points/currency.
    Examples: 'Coffee Coupon', 'Day Off Pass', 'Gift Card'.
    """
    __tablename__ = "rewards"

    # 'name', 'description', 'state', 'notes', 'group_id' are inherited.
    # 'state' can be 'available', 'unavailable', 'archived'.

    cost_in_points: Mapped[int] = mapped_column(Integer, nullable=False, comment="Number of points/currency required to redeem this reward")
    icon_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True, comment="URL or path to an icon representing the reward")
    # Alternatively, icon_file_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("file_records.id"), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True, comment="Is this reward currently available for redemption?")
    stock_quantity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="Available stock for this reward. Null if unlimited.")
    # redemption_limit_per_user: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="Max times a single user can redeem this reward. Null if unlimited.")
    # valid_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, comment="Date from which this reward is available")
    # valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, comment="Date until which this reward is available")

    # --- Relationships ---
    # Group relationship is inherited via BaseGroupAffiliatedMainModel if that base defines the relationship object.
    # If not, and group_id is just an FK from a mixin, define it here:
    # from backend.app.src.models.groups.group import Group # Ensure Group is imported
    # group: Mapped["Group"] = relationship(foreign_keys="Reward.group_id") # Assuming group_id is on Reward (it is via BaseGroupAffiliatedMainModel)


    # If icon is a FileRecord:
    # icon_file: Mapped[Optional["FileRecord"]] = relationship(foreign_keys=[icon_file_id])

    # Transactions related to redemption of this reward could be found by querying AccountTransaction.related_entity_id == Reward.id
    # and AccountTransaction.related_entity_type == 'reward'. No direct ORM relationship needed here typically.

    def __repr__(self) -> str:
        id_val = getattr(self, 'id', 'N/A')
        group_id_val = getattr(self, 'group_id', 'N/A')
        return f"<Reward(id={id_val}, name='{self.name}', group_id={group_id_val}, cost={self.cost_in_points})>"

if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- Reward Model --- Demonstration")

    # Example Reward instance
    # Assume Group id=1 exists
    coffee_coupon = Reward(
        name="Free Coffee Coupon",
        description="Redeem for one free coffee at the office cafeteria.",
        group_id=1,
        cost_in_points=100,
        icon_url="/static/icons/rewards/coffee_coupon.png",
        is_active=True,
        stock_quantity=50, # Limited stock
        state="available" # from BaseGroupAffiliatedMainModel
    )
    coffee_coupon.id = 1 # Simulate ORM-set ID
    coffee_coupon.created_at = datetime.now(timezone.utc) # Simulate timestamp
    coffee_coupon.updated_at = datetime.now(timezone.utc) # Simulate timestamp

    logger.info(f"Example Reward: {coffee_coupon!r}")
    logger.info(f"  Name: {coffee_coupon.name}")
    logger.info(f"  Cost: {coffee_coupon.cost_in_points} points")
    logger.info(f"  Stock: {coffee_coupon.stock_quantity}")
    logger.info(f"  Is Active: {coffee_coupon.is_active}")
    logger.info(f"  State: {coffee_coupon.state}")
    logger.info(f"  Created At: {coffee_coupon.created_at.isoformat() if coffee_coupon.created_at else 'N/A'}")


    day_off_pass = Reward(
        name="Half-Day Off Pass",
        group_id=1,
        cost_in_points=1000,
        is_active=True,
        stock_quantity=None, # Unlimited stock
        state="available"
    )
    day_off_pass.id = 2
    logger.info(f"Example Reward (unlimited stock): {day_off_pass!r}")
    logger.info(f"  Stock: {day_off_pass.stock_quantity if day_off_pass.stock_quantity is not None else 'Unlimited'}")

    # The following line would error if run directly without SQLAlchemy engine and metadata setup for all related tables.
    # logger.info(f"Reward attributes (conceptual table columns): {[c.name for c in Reward.__table__.columns if not c.name.startswith('_')]}")
    logger.info("To see actual table columns, SQLAlchemy metadata needs to be initialized with an engine (e.g., Base.metadata.create_all(engine)).")
