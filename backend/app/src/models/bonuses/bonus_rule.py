# backend/app/src/models/bonuses/bonus_rule.py

"""
SQLAlchemy model for Bonus Rules.
Bonus rules define conditions under which points/bonuses are awarded or deducted.
"""

import logging
from typing import Optional, TYPE_CHECKING, Dict, Any # For Mapped type hints
from datetime import datetime, timezone # For __main__ example

from sqlalchemy import String, Text, Boolean, ForeignKey, Integer, JSON # Added Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.src.models.base import BaseGroupAffiliatedMainModel # Bonus rules can be group-specific

# Configure logger for this module
logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from backend.app.src.models.dictionaries.bonus_types import BonusType
    from backend.app.src.models.dictionaries.task_types import TaskType # If rule is tied to task type
    # from backend.app.src.models.groups.group import Group # For group relationship if not from BaseGroupAffiliatedMainModel

class BonusRule(BaseGroupAffiliatedMainModel): # Inherits id, name, description, state, notes, group_id, created_at, updated_at, deleted_at
    """
    Represents a rule for awarding or deducting bonuses/points within a group.
    Examples: 'Bonus for completing 5 tasks in a week', 'Penalty for late task submission'.
    """
    __tablename__ = "bonus_rules"

    # 'name', 'description', 'state', 'notes', 'group_id' are inherited.
    # 'state' can be 'active', 'inactive', 'expired'.

    bonus_type_id: Mapped[int] = mapped_column(Integer, ForeignKey("dict_bonus_types.id"), nullable=False, index=True, comment="FK to bonus_types dictionary, categorizing the rule (e.g., task completion, streak, manual)")

    points_amount: Mapped[int] = mapped_column(Integer, nullable=False, comment="Points to be awarded (positive) or deducted (negative) by this rule")

    # Conditions for applying the rule. This can be complex.
    # Simple approach: store as text. Complex: store as JSON structure or use a rules engine.
    condition_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="Human-readable description of the conditions under which this rule applies")
    condition_config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True, comment="Structured (JSON) configuration for rule conditions, e.g., {'task_type_code': 'CHORE', 'min_completed': 5, 'period_days': 7}")

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True, comment="Is this bonus rule currently active and applicable?")

    # Optional: If a rule is tied to a specific task type or other entity type
    # applicable_task_type_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("dict_task_types.id"), nullable=True, index=True, comment="If this rule applies only to a specific task type")

    # --- Relationships ---
    bonus_type: Mapped["BonusType"] = relationship(foreign_keys=[bonus_type_id])
    # applicable_task_type: Mapped[Optional["TaskType"]] = relationship(foreign_keys=[applicable_task_type_id])
    # Group relationship is inherited via BaseGroupAffiliatedMainModel if that base defines the relationship object.
    # If not, and group_id is just an FK from a mixin, define it here:
    # group: Mapped["Group"] = relationship(foreign_keys="BonusRule.group_id") # Assuming group_id is on BonusRule

    def __repr__(self) -> str:
        id_val = getattr(self, 'id', 'N/A')
        group_id_val = getattr(self, 'group_id', 'N/A')
        return f"<BonusRule(id={id_val}, name='{self.name}', group_id={group_id_val}, points={self.points_amount})>"

if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- BonusRule Model --- Demonstration")

    # Example BonusRule instance
    # Assume Group id=1, BonusType id=1 (e.g., 'MANUAL_BONUS') exist
    manual_bonus = BonusRule(
        name="Manual Admin Bonus",
        description="A bonus manually awarded by a group admin for exceptional performance.",
        group_id=1,
        bonus_type_id=1,
        points_amount=100,
        condition_description="Awarded at admin's discretion.",
        condition_config={"requires_admin_approval": True},
        is_active=True,
        state="active" # from BaseGroupAffiliatedMainModel
    )
    manual_bonus.id = 1 # Simulate ORM-set ID
    manual_bonus.created_at = datetime.now(timezone.utc) # Simulate timestamp
    manual_bonus.updated_at = datetime.now(timezone.utc) # Simulate timestamp

    logger.info(f"Example BonusRule: {manual_bonus!r}")
    logger.info(f"  Name: {manual_bonus.name}")
    logger.info(f"  Points: {manual_bonus.points_amount}")
    logger.info(f"  Condition Config: {manual_bonus.condition_config}")
    logger.info(f"  Is Active: {manual_bonus.is_active}")
    logger.info(f"  Created At: {manual_bonus.created_at.isoformat() if manual_bonus.created_at else 'N/A'}")


    streak_bonus_rule = BonusRule(
        name="5 Task Weekly Streak Bonus",
        group_id=1,
        bonus_type_id=2, # Assuming BonusType id=2 is 'STREAK_BONUS'
        points_amount=250,
        condition_description="Complete at least 5 tasks of type 'CHORE' or 'WORK_ITEM' within a 7-day rolling window.",
        condition_config={
            "min_tasks": 5,
            "task_type_codes": ["CHORE", "WORK_ITEM"],
            "period_days": 7,
            "streak_type": "rolling"
        },
        is_active=True,
        state="active"
    )
    streak_bonus_rule.id = 2
    logger.info(f"Example Streak BonusRule: {streak_bonus_rule!r}")
    logger.info(f"  Condition Description: {streak_bonus_rule.condition_description}")

    # The following line would error if run directly without SQLAlchemy engine and metadata setup for all related tables.
    # logger.info(f"BonusRule attributes (conceptual table columns): {[c.name for c in BonusRule.__table__.columns if not c.name.startswith('_')]}")
    logger.info("To see actual table columns, SQLAlchemy metadata needs to be initialized with an engine (e.g., Base.metadata.create_all(engine)).")
