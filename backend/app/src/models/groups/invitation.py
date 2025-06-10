# backend/app/src/models/groups/invitation.py

"""
SQLAlchemy model for Group Invitations.
"""

import logging
from typing import Optional, TYPE_CHECKING
from datetime import datetime, timedelta, timezone # Added timezone
from enum import Enum as PythonEnum # For InvitationStatusEnum definition

from sqlalchemy import String, DateTime, ForeignKey, Enum as SQLAlchemyEnum, Integer # Added Integer for FKs
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func # For server_default for created_at/updated_at in BaseModel

from backend.app.src.models.base import BaseModel
from backend.app.src.core.utils import generate_random_string # For generating invitation_code

# Configure logger for this module
logger = logging.getLogger(__name__)

class InvitationStatusEnum(PythonEnum): # Changed to inherit from PythonEnum
    """ Defines the possible statuses for a group invitation. """
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"
    REVOKED = "revoked"

if TYPE_CHECKING:
    from backend.app.src.models.auth.user import User
    from backend.app.src.models.groups.group import Group

def default_invitation_code() -> str:
    """Generates a default random string for invitation code."""
    return generate_random_string(12) # 12-character random string

def default_expires_at() -> datetime:
    """Default expiration for an invitation (e.g., 7 days from now)."""
    return datetime.now(timezone.utc) + timedelta(days=7)

class GroupInvitation(BaseModel):
    """
    Represents an invitation sent to a user (or external email/phone)
    to join a specific group.

    Attributes:
        group_id (int): Foreign key to the group the invitation is for.
        invited_by_user_id (Optional[int]): Foreign key to the user who sent the invitation.
                                          Null if system-generated or anonymous invite.
        email_invited (Optional[str]): Email address of the invitee if not yet a system user.
        phone_invited (Optional[str]): Phone number of the invitee if not yet a system user.
        target_user_id (Optional[int]): FK to users.id if inviting an existing system user directly.
        invitation_code (str): A unique code for this invitation (e.g., for link-based invites).
        status (InvitationStatusEnum): Current status of the invitation.
        expires_at (datetime): Timestamp when the invitation expires.
        accepted_at (Optional[datetime]): Timestamp when the invitation was accepted.
        # `id`, `created_at`, `updated_at` are inherited from BaseModel.
    """
    __tablename__ = "group_invitations"

    group_id: Mapped[int] = mapped_column(Integer, ForeignKey("groups.id"), nullable=False, index=True, comment="The group for which the invitation is made")
    invited_by_user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True, comment="The user who sent the invitation (if applicable)")

    email_invited: Mapped[Optional[str]] = mapped_column(String(320), nullable=True, index=True, comment="Email of the person invited (if not yet a user or for direct email invite)")
    phone_invited: Mapped[Optional[str]] = mapped_column(String(30), nullable=True, index=True, comment="Phone number of the person invited (if not yet a user)")
    target_user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True, comment="Direct invitation to an existing system user")

    invitation_code: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
        default=default_invitation_code,
        comment="Unique code for this invitation (for link-based invites)"
    )

    status: Mapped[InvitationStatusEnum] = mapped_column(
        SQLAlchemyEnum(InvitationStatusEnum, name="invitationstatusenum", create_constraint=True, native_enum=False), # native_enum=False for string storage
        nullable=False,
        default=InvitationStatusEnum.PENDING,
        index=True,
        comment="Current status of the invitation (pending, accepted, expired, etc.)"
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=default_expires_at,
        comment="Timestamp when the invitation expires (UTC)"
    )
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, comment="Timestamp when the invitation was accepted (UTC)")
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, comment="Timestamp when the invitation was revoked (UTC)")

    # --- Relationships ---
    group: Mapped["Group"] = relationship(back_populates="invitations")
    invited_by: Mapped[Optional["User"]] = relationship(foreign_keys=[invited_by_user_id]) # One-way, or define back_populates on User if needed
    target_user: Mapped[Optional["User"]] = relationship(foreign_keys=[target_user_id]) # One-way, or define back_populates on User if needed

    def __repr__(self) -> str:
        id_val = getattr(self, 'id', 'N/A')
        return f"<GroupInvitation(id={id_val}, group_id={self.group_id}, code='{self.invitation_code}', status='{self.status.value}')>"

if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- GroupInvitation Model --- Demonstration")

    # Example GroupInvitation instance
    invitation1 = GroupInvitation(
        group_id=1, # Assuming group with id=1 exists
        invited_by_user_id=1, # Assuming user with id=1 sent it
        email_invited="new_user@example.com",
        # invitation_code is auto-generated by default via default_invitation_code
        # expires_at is auto-generated by default via default_expires_at
    )
    invitation1.id = 1 # Simulate ORM-set ID
    invitation1.created_at = datetime.now(timezone.utc)
    invitation1.updated_at = datetime.now(timezone.utc)

    logger.info(f"Example GroupInvitation 1: {invitation1!r}")
    logger.info(f"  Group ID: {invitation1.group_id}")
    logger.info(f"  Invited Email: {invitation1.email_invited}")
    logger.info(f"  Code: {invitation1.invitation_code}") # Will be auto-generated
    logger.info(f"  Status: {invitation1.status.value}")
    logger.info(f"  Expires At: {invitation1.expires_at.isoformat() if invitation1.expires_at else 'N/A'}")
    logger.info(f"  Created At: {invitation1.created_at.isoformat() if invitation1.created_at else 'N/A'}")


    invitation2_to_existing_user = GroupInvitation(
        group_id=2,
        invited_by_user_id=3,
        target_user_id=5, # Inviting existing user with id=5
        status=InvitationStatusEnum.ACCEPTED,
        accepted_at=datetime.now(timezone.utc) - timedelta(hours=1)
    )
    invitation2_to_existing_user.id = 2
    logger.info(f"Example GroupInvitation 2 (to existing user, accepted): {invitation2_to_existing_user!r}")
    logger.info(f"  Target User ID: {invitation2_to_existing_user.target_user_id}")
    logger.info(f"  Status: {invitation2_to_existing_user.status.value}")
    logger.info(f"  Accepted At: {invitation2_to_existing_user.accepted_at.isoformat() if invitation2_to_existing_user.accepted_at else 'N/A'}")

    # The following line would error if run directly without SQLAlchemy engine and metadata setup for all related tables.
    # logger.info(f"GroupInvitation attributes (conceptual table columns): {[c.name for c in GroupInvitation.__table__.columns if not c.name.startswith('_')]}")
    logger.info("To see actual table columns, SQLAlchemy metadata needs to be initialized with an engine (e.g., Base.metadata.create_all(engine)).")
