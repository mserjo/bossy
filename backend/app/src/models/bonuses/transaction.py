# backend/app/src/models/bonuses/transaction.py

"""
SQLAlchemy model for Account Transactions, recording movements in UserAccounts.
"""

import logging
from typing import Optional, TYPE_CHECKING, Any # For Mapped type hints
from datetime import datetime, timezone # Added timezone for __main__
from decimal import Decimal # For amount type hint
from enum import Enum as PythonEnum # For TransactionTypeEnum

from sqlalchemy import ForeignKey, String, Text, Numeric, Enum as SQLAlchemyEnum, Integer # Added Integer for FKs
from sqlalchemy.orm import Mapped, mapped_column, relationship
# from sqlalchemy.sql import func # Not strictly needed here as created_at from BaseModel has server_default

from backend.app.src.models.base import BaseModel

# Configure logger for this module
logger = logging.getLogger(__name__)

class TransactionTypeEnum(PythonEnum): # Changed to inherit from PythonEnum
    """ Defines the types of account transactions. """
    CREDIT_TASK_COMPLETION = "credit_task_completion"
    CREDIT_MANUAL_BONUS = "credit_manual_bonus"
    CREDIT_STREAK_BONUS = "credit_streak_bonus"
    CREDIT_REFERRAL_BONUS = "credit_referral_bonus"
    DEBIT_REWARD_REDEMPTION = "debit_reward_redemption"
    DEBIT_PENALTY_LATE_TASK = "debit_penalty_late_task"
    DEBIT_PENALTY_MANUAL = "debit_penalty_manual"
    ADJUSTMENT_CREDIT = "adjustment_credit" # Admin correction
    ADJUSTMENT_DEBIT = "adjustment_debit"  # Admin correction
    INITIAL_BALANCE_SETUP = "initial_balance_setup"
    OTHER = "other"

if TYPE_CHECKING:
    from backend.app.src.models.bonuses.account import UserAccount
    from backend.app.src.models.auth.user import User # e.g. for manual transactions by admin
    # For related_entity, if you want to link directly to specific models:
    # from backend.app.src.models.tasks.task import Task
    # from backend.app.src.models.bonuses.reward import Reward


class AccountTransaction(BaseModel):
    """
    Represents a transaction on a UserAccount, detailing credits or debits.

    Attributes:
        account_id (int): Foreign key to the UserAccount this transaction belongs to.
        transaction_type (TransactionTypeEnum): The type of transaction (e.g., credit, debit, reward redemption).
        amount (Decimal): The amount of points/currency for this transaction. Positive for credits, negative for debits.
        balance_after_transaction (Optional[Decimal]): Account balance after this transaction. For auditing.
        description (Optional[str]): A human-readable description or reason for the transaction.
        related_entity_type (Optional[str]): Type of entity related to this transaction (e.g., 'task', 'reward', 'manual_adjustment').
        related_entity_id (Optional[int]): ID of the related entity.
        performed_by_user_id (Optional[int]): FK to User who initiated or performed this transaction (e.g., an admin for manual adjustment).
        # `id`, `created_at` (transaction_date), `updated_at` from BaseModel.
        # `created_at` effectively serves as the transaction_date.
    """
    __tablename__ = "account_transactions"

    account_id: Mapped[int] = mapped_column(Integer, ForeignKey("user_accounts.id"), nullable=False, index=True, comment="FK to the UserAccount this transaction affects")

    transaction_type: Mapped[TransactionTypeEnum] = mapped_column(
        SQLAlchemyEnum(TransactionTypeEnum, name="transactiontypeenum", create_constraint=True, native_enum=False), # native_enum=False for string storage
        nullable=False,
        index=True,
        comment="Type of the transaction (e.g., credit_task_completion, debit_reward_redemption)"
    )

    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, comment="Transaction amount; positive for credit, negative for debit")
    balance_after_transaction: Mapped[Optional[Decimal]] = mapped_column(Numeric(10,2), nullable=True, comment="Account balance immediately after this transaction was applied. For auditing.")

    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="Human-readable description or reason for the transaction")

    related_entity_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True, comment="Type of entity related to this transaction (e.g., 'task', 'reward')")
    related_entity_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True, comment="ID of the related entity (e.g., task.id, reward.id)")

    performed_by_user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True, comment="User who performed/authorized this transaction (e.g., admin for manual adjustment)")

    # --- Relationships ---
    account: Mapped["UserAccount"] = relationship(back_populates="transactions")
    performed_by: Mapped[Optional["User"]] = relationship(foreign_keys=[performed_by_user_id]) # One-way or add back_populates to User

    # Generic relationship to related_entity is complex with SQLAlchemy's ORM if you want direct object access.
    # Usually, related_entity_type and related_entity_id are used by services to fetch the related object manually.
    # If you need a polymorphic relationship, SQLAlchemy has patterns for that (e.g., using a common base or specific join conditions).

    def __repr__(self) -> str:
        id_val = getattr(self, 'id', 'N/A')
        return f"<AccountTransaction(id={id_val}, account_id={self.account_id}, type='{self.transaction_type.value}', amount={self.amount})>"

if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- AccountTransaction Model --- Demonstration")

    # Example AccountTransaction instances
    # Assume UserAccount id=1 exists
    tx1_credit = AccountTransaction(
        account_id=1,
        transaction_type=TransactionTypeEnum.CREDIT_TASK_COMPLETION,
        amount=Decimal("50.00"),
        balance_after_transaction=Decimal("150.50"),
        description="Completed 'Weekly Kitchen Cleaning' task.",
        related_entity_type="task",
        related_entity_id=101 # Assuming task with id=101
    )
    tx1_credit.id = 1 # Simulate ORM ID
    tx1_credit.created_at = datetime.now(timezone.utc)
    tx1_credit.updated_at = datetime.now(timezone.utc)
    logger.info(f"Example Credit Transaction: {tx1_credit!r}")
    logger.info(f"  Amount: {tx1_credit.amount}, Type: {tx1_credit.transaction_type.value}")
    logger.info(f"  Related: {tx1_credit.related_entity_type} ID {tx1_credit.related_entity_id}")
    logger.info(f"  Balance After: {tx1_credit.balance_after_transaction}")
    logger.info(f"  Created At: {tx1_credit.created_at.isoformat() if tx1_credit.created_at else 'N/A'}")


    tx2_debit = AccountTransaction(
        account_id=1,
        transaction_type=TransactionTypeEnum.DEBIT_REWARD_REDEMPTION,
        amount=Decimal("-25.00"), # Negative for debit
        balance_after_transaction=Decimal("125.50"),
        description="Redeemed 'Coffee Coupon' reward.",
        related_entity_type="reward",
        related_entity_id=201, # Assuming reward with id=201
        performed_by_user_id=1 # User themselves redeemed it
    )
    tx2_debit.id = 2
    logger.info(f"Example Debit Transaction: {tx2_debit!r}")
    logger.info(f"  Amount: {tx2_debit.amount}, Performed by User ID: {tx2_debit.performed_by_user_id}")
    logger.info(f"  Balance After: {tx2_debit.balance_after_transaction}")

    # The following line would error if run directly without SQLAlchemy engine and metadata setup for all related tables.
    # logger.info(f"AccountTransaction attributes (conceptual table columns): {[c.name for c in AccountTransaction.__table__.columns if not c.name.startswith('_')]}")
    logger.info("To see actual table columns, SQLAlchemy metadata needs to be initialized with an engine (e.g., Base.metadata.create_all(engine)).")
