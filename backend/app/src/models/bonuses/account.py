# backend/app/src/models/bonuses/account.py

"""
SQLAlchemy model for User Accounts, which store the balance of points/currency for users.
"""

import logging
from typing import Optional, List, TYPE_CHECKING # For Mapped type hints
from datetime import datetime, timezone, timedelta # Added timezone, timedelta for __main__
from decimal import Decimal # For balance field

from sqlalchemy import ForeignKey, String, Numeric, DateTime, UniqueConstraint, Integer # Added Integer for FKs
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.src.models.base import BaseModel # Accounts are simpler than full BaseMainModel

# Configure logger for this module
logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from backend.app.src.models.auth.user import User
    from backend.app.src.models.groups.group import Group # If accounts are per-group
    from backend.app.src.models.bonuses.transaction import AccountTransaction

class UserAccount(BaseModel):
    """
    Represents a user's account for bonuses/points/currency.
    A user might have one global account or one account per group they are a member of.
    This implementation supports one account per user per group.

    Attributes:
        user_id (int): Foreign key to the user who owns this account.
        group_id (int): Foreign key to the group this account is associated with.
                       If set to a special 'system' group_id or made nullable, can represent a global account.
        balance (Decimal): The current balance of points/currency in the account. Using Numeric for precision.
        currency_name (str): The name of the currency held in this account (e.g., 'points', 'kudos', 'stars').
                             This might be inherited from group settings in practice.
        last_transaction_at (Optional[datetime]): Timestamp of the last transaction on this account.
        # `id`, `created_at`, `updated_at` from BaseModel.
    """
    __tablename__ = "user_accounts"

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="FK to the user owning this account")
    group_id: Mapped[int] = mapped_column(Integer, ForeignKey("groups.id"), nullable=False, index=True, comment="FK to the group this account belongs to. Ensures account is group-specific.")

    # Using Numeric for currency/points to handle precision properly, avoiding float issues.
    # Precision and scale can be adjusted based on requirements (e.g., if fractional points are allowed).
    balance: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal('0.00'), nullable=False, comment="Current balance of points/currency. Precision 10, 2 decimal places.")

    currency_name: Mapped[str] = mapped_column(String(50), default="points", nullable=False, comment="Name of the currency (e.g., 'points', 'kudos')")

    last_transaction_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, comment="Timestamp of the last transaction on this account (UTC)")

    # --- Relationships ---
    user: Mapped["User"] = relationship(back_populates="accounts")
    group: Mapped["Group"] = relationship() # One-way or add back_populates="user_accounts" to Group
    transactions: Mapped[List["AccountTransaction"]] = relationship(back_populates="account", cascade="all, delete-orphan", order_by="AccountTransaction.created_at.desc()")

    # --- Table Arguments ---
    # A user should have only one account per group.
    __table_args__ = (
        UniqueConstraint('user_id', 'group_id', name='uq_user_group_account'),
    )

    def __repr__(self) -> str:
        id_val = getattr(self, 'id', 'N/A')
        return f"<UserAccount(id={id_val}, user_id={self.user_id}, group_id={self.group_id}, balance={self.balance} {self.currency_name})>"

if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- UserAccount Model --- Demonstration")

    # Example UserAccount instance
    # Assume User id=1 and Group id=1 exist
    account1 = UserAccount(
        user_id=1,
        group_id=1,
        balance=Decimal('100.50'),
        currency_name="Kudos Points",
        last_transaction_at=datetime.now(timezone.utc) - timedelta(hours=1)
    )
    account1.id = 1 # Simulate ORM-set ID
    account1.created_at = datetime.now(timezone.utc) - timedelta(days=1)
    account1.updated_at = datetime.now(timezone.utc) - timedelta(hours=1)

    logger.info(f"Example UserAccount: {account1!r}")
    logger.info(f"  User ID: {account1.user_id}, Group ID: {account1.group_id}")
    logger.info(f"  Balance: {account1.balance} {account1.currency_name}")
    logger.info(f"  Last Transaction At: {account1.last_transaction_at.isoformat() if account1.last_transaction_at else 'N/A'}")
    logger.info(f"  Created At: {account1.created_at.isoformat() if account1.created_at else 'N/A'}")


    account2_zero_balance = UserAccount(
        user_id=2, # User 2
        group_id=1, # Same Group 1
        currency_name="Stars"
        # balance defaults to 0.00
    )
    account2_zero_balance.id = 2
    logger.info(f"Example UserAccount (zero balance): {account2_zero_balance!r}")
    logger.info(f"  Balance (defaulted): {account2_zero_balance.balance}")


    # The following line would error if run directly without SQLAlchemy engine and metadata setup for all related tables.
    # logger.info(f"UserAccount attributes (conceptual table columns): {[c.name for c in UserAccount.__table__.columns if not c.name.startswith('_')]}")
    logger.info("To see actual table columns, SQLAlchemy metadata needs to be initialized with an engine (e.g., Base.metadata.create_all(engine)).")
