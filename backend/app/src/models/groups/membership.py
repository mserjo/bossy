# backend/app/src/models/groups/membership.py

"""
SQLAlchemy model for GroupMembership, representing the association between Users and Groups.
This is an association object for a many-to-many relationship.
"""

import logging
from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone # Added timezone for __main__

from sqlalchemy import ForeignKey, DateTime, UniqueConstraint, Integer, Boolean, Text # Added Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func # For server_default=func.now()

from backend.app.src.models.base import BaseModel # Memberships are simpler entities

# Configure logger for this module
logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from backend.app.src.models.auth.user import User
    from backend.app.src.models.groups.group import Group
    from backend.app.src.models.dictionaries.user_roles import UserRole # For role relationship

class GroupMembership(BaseModel):
    """
    Represents the membership of a User in a Group.
    This acts as an association table for the many-to-many relationship
    between Users and Groups, and can hold additional data about the membership (e.g., role in group, join date).

    The `id` field from BaseModel serves as the surrogate primary key for this association record.
    A unique constraint on (user_id, group_id) ensures a user cannot have multiple membership records for the same group.

    Attributes:
        user_id (int): Foreign key to the user.
        group_id (int): Foreign key to the group.
        role_id (int): Foreign key to `dict_user_roles.id`, defining the user's role specifically within this group.
        join_date (datetime): Timestamp when the user joined the group.
        is_active (bool): Whether this membership is currently active.
        notes (Optional[str]): Any specific notes about this membership.
    """
    __tablename__ = "group_memberships"

    # `id` from BaseModel is the surrogate PK.
    # user_id and group_id are indexed FKs and part of a unique constraint.
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="FK to the user who is a member")
    group_id: Mapped[int] = mapped_column(Integer, ForeignKey("groups.id"), nullable=False, index=True, comment="FK to the group the user is a member of")

    role_id: Mapped[int] = mapped_column(Integer, ForeignKey("dict_user_roles.id"), nullable=False, index=True, comment="FK to user_roles dictionary, defining the user's role within this group")

    join_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp when the user joined the group (UTC)"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, comment="Is this membership currently active? (e.g., for suspensions)")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="Optional notes specific to this membership")

    # --- Relationships ---
    user: Mapped["User"] = relationship(back_populates="group_memberships")
    group: Mapped["Group"] = relationship(back_populates="memberships")
    role: Mapped["UserRole"] = relationship(foreign_keys=[role_id]) # Relationship to dict_user_roles

    # --- Table Arguments ---
    # Enforce that a user can only have one membership record per group.
    __table_args__ = (UniqueConstraint('user_id', 'group_id', name='uq_user_group_membership'),)

    def __repr__(self) -> str:
        id_val = getattr(self, 'id', 'N/A') # Use surrogate PK from BaseModel for repr
        return f"<GroupMembership(id={id_val}, user_id={self.user_id}, group_id={self.group_id}, role_id={self.role_id})>"

if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- GroupMembership Model --- Demonstration")

    # Example GroupMembership instance
    # Assume User with id=1, Group with id=1, and UserRole with id=3 (e.g., 'MEMBER') exist
    membership1 = GroupMembership(
        user_id=1,
        group_id=1,
        role_id=3, # Member role
        is_active=True,
        notes="First member of the group."
    )
    membership1.id = 1 # Simulate ORM-set surrogate ID from BaseModel
    membership1.join_date = datetime.now(timezone.utc) # Simulate (server_default handles this in DB)
    membership1.created_at = datetime.now(timezone.utc)
    membership1.updated_at = datetime.now(timezone.utc)

    logger.info(f"Example GroupMembership: {membership1!r}")
    logger.info(f"  User ID: {membership1.user_id}, Group ID: {membership1.group_id}, Role ID: {membership1.role_id}")
    logger.info(f"  Join Date: {membership1.join_date.isoformat() if membership1.join_date else 'N/A'}")
    logger.info(f"  Is Active: {membership1.is_active}")
    logger.info(f"  Notes: {membership1.notes}")
    logger.info(f"  Surrogate PK (id): {membership1.id}")
    logger.info(f"  Created At: {membership1.created_at.isoformat() if membership1.created_at else 'N/A'}")


    admin_membership = GroupMembership(
        user_id=2, # User 2
        group_id=1, # Same Group 1
        role_id=2,  # Admin role (assuming UserRole with id=2 is 'GROUP_ADMIN')
    )
    admin_membership.id = 2
    logger.info(f"Example Admin GroupMembership: {admin_membership!r}")

    # The following line would error if run directly without SQLAlchemy engine and metadata setup for all related tables.
    # logger.info(f"GroupMembership attributes (conceptual table columns): {[c.name for c in GroupMembership.__table__.columns if not c.name.startswith('_')]}")
    logger.info("To see actual table columns, SQLAlchemy metadata needs to be initialized with an engine (e.g., Base.metadata.create_all(engine)).")
