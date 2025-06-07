# backend/app/src/models/auth/user.py

"""
SQLAlchemy model for User accounts.
"""

import logging
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime, timezone # Added timezone for __main__ example

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Integer # Added Integer for FKs
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.src.models.base import BaseMainModel # Using BaseMainModel for common fields
# User model typically doesn't need GroupAffiliationMixin directly unless users always belong to one primary group.
# Group membership is handled via the GroupMembership association table.

# Configure logger for this module
logger = logging.getLogger(__name__)

# Forward references for relationship type hints if models are in different files
if TYPE_CHECKING:
    from backend.app.src.models.auth.session import UserSession
    from backend.app.src.models.auth.token import RefreshToken
    from backend.app.src.models.groups.group import Group # For owned_groups
    from backend.app.src.models.groups.membership import GroupMembership
    from backend.app.src.models.tasks.assignment import TaskAssignment
    from backend.app.src.models.notifications.notification import Notification
    from backend.app.src.models.files.avatar import UserAvatar
    from backend.app.src.models.bonuses.account import UserAccount
    from backend.app.src.models.dictionaries.user_types import UserType # For user_type relationship
    # Add other related models as needed, e.g., for tasks created by user, etc.

class User(BaseMainModel): # Inherits id, name, description, state, notes, created_at, updated_at, deleted_at
    """
    Represents a user account in the system.
    """
    __tablename__ = "users"

    # Override name and description from BaseMainModel to make them optional for User, or adjust as needed.
    # BaseMainModel makes name non-nullable. If a user might not have a 'name' (e.g., uses username or email as primary id),
    # then User should inherit from BaseModel and pick mixins selectively, or override here.
    # For this implementation, we'll assume 'name' can be a display name and might be optional initially.
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, comment="Display name of the user (can be full name or a preferred nickname)")
    # description from BaseMainModel can be used for a user's bio or extended profile info.

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False, comment="User's email address (login identifier)")
    hashed_password: Mapped[str] = mapped_column(String(128), nullable=False, comment="Hashed password for the user") # Increased length for future hash algorithms

    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="User's first name")
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="User's last name")
    phone_number: Mapped[Optional[str]] = mapped_column(String(30), unique=True, index=True, nullable=True, comment="User's phone number (optional login or contact)")

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True, comment="Designates whether this user should be treated as active. Unselect this instead of deleting accounts.")
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True, comment="Designates that this user has all permissions without explicitly assigning them.")

    user_type_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("dict_user_types.id"), nullable=True, comment="FK to user_types dictionary (e.g., Human, Bot)")
    # `default_role_id` was in the plan, but roles are often context-dependent (e.g., system role vs group role).
    # A single `default_role_id` might be ambiguous. System-level role (like superuser) is handled by `is_superuser`.
    # Group-specific roles are in GroupMembership. For now, omitting `default_role_id` unless a clear system-wide default is defined.
    # Consider a `system_role_id` if there are non-superuser system roles like 'auditor', 'support_staff'.

    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, comment="Timestamp of the user's last successful login")
    email_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, comment="Timestamp when the user's email was verified")
    phone_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, comment="Timestamp when the user's phone was verified")

    # --- Relationships ---
    # Auth related
    sessions: Mapped[List["UserSession"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    # Group related
    # Assuming Group model has an 'owner_id' field that is a FK to User.id
    owned_groups: Mapped[List["Group"]] = relationship(back_populates="owner", foreign_keys="Group.owner_id")
    group_memberships: Mapped[List["GroupMembership"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    # Through 'group_memberships', you can access the groups a user is part of.

    # Task related
    # tasks_created: Mapped[List["Task"]] = relationship(back_populates="created_by_user") # If tasks have a created_by_user_id
    task_assignments: Mapped[List["TaskAssignment"]] = relationship(back_populates="user", cascade="all, delete-orphan") # Tasks assigned to this user

    # Notification related
    notifications: Mapped[List["Notification"]] = relationship(back_populates="user_recipient", cascade="all, delete-orphan")

    # File related
    avatar: Mapped[Optional["UserAvatar"]] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")

    # Bonus/Account related
    accounts: Mapped[List["UserAccount"]] = relationship(back_populates="user", cascade="all, delete-orphan") # Could be one-to-one if one account per user global

    # Relationships to dictionary tables (for convenience, if needed, though usually FKs are sufficient)
    user_type: Mapped[Optional["UserType"]] = relationship(foreign_keys=[user_type_id])
    # default_system_role: Mapped[Optional["UserRole"]] = relationship(foreign_keys=[default_role_id]) # If default_role_id was used

    # The 'state' field from BaseMainModel can represent user lifecycle states like 'pending_verification', 'active', 'suspended'.

    def __repr__(self) -> str:
        id_val = getattr(self, 'id', 'N/A')
        return f"<User(id={id_val}, email='{self.email}', name='{self.name}')>"

if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- User Model --- Demonstration")

    # Example User instance
    demo_user = User(
        name="John Doe",
        email="john.doe@example.com",
        hashed_password="a_very_secure_hash_placeholder",
        first_name="John",
        last_name="Doe",
        phone_number="+15551234567",
        is_active=True,
        is_superuser=False,
        # user_type_id=1, # Assuming a UserType with id=1 exists
        state="active", # from BaseMainModel
        description="A demo user account." # from BaseMainModel
    )
    demo_user.id = 1 # Simulate ORM-set ID
    demo_user.created_at = datetime.now(timezone.utc)
    demo_user.updated_at = datetime.now(timezone.utc)

    logger.info(f"Example User: {demo_user!r}")
    logger.info(f"  Email: {demo_user.email}")
    logger.info(f"  Full Name: {demo_user.first_name} {demo_user.last_name if demo_user.last_name else ''}")
    logger.info(f"  Is Superuser: {demo_user.is_superuser}")
    logger.info(f"  State: {demo_user.state}")
    logger.info(f"  Description: {demo_user.description}")
    logger.info(f"  Created At: {demo_user.created_at.isoformat() if demo_user.created_at else 'N/A'}")


    # To view relationships, a DB session and related objects would be needed.
    # The following line would error if run directly without SQLAlchemy engine and metadata setup for all related tables.
    # logger.info(f"User attributes (conceptual table columns): {[c.name for c in User.__table__.columns if not c.name.startswith('_')]}")
    logger.info("To see actual table columns, SQLAlchemy metadata needs to be initialized with an engine (e.g., Base.metadata.create_all(engine)).")
