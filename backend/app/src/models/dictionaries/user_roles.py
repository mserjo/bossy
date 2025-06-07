# backend/app/src/models/dictionaries/user_roles.py

"""
SQLAlchemy model for a 'UserRole' dictionary table.
This table stores different roles that can be assigned to users within the system or within groups.
"""

import logging
from typing import Optional, List # For Mapped[Optional[List[str]]] if using JSON for permissions
from datetime import datetime, timezone # For __main__ example

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import JSON, Boolean # If storing permissions as JSON or adding is_system_role

from backend.app.src.models.dictionaries.base_dict import BaseDictionaryModel

# Configure logger for this module
logger = logging.getLogger(__name__)

class UserRole(BaseDictionaryModel):
    """
    Represents a user role in a dictionary table (e.g., Superuser, Admin, User, Guest, Bot).
    Inherits common fields from BaseDictionaryModel.

    The 'state' field from BaseDictionaryModel could be used to mark a role as 'active' or 'deprecated'.
    The 'code' field from BaseDictionaryModel will be crucial (e.g., 'SUPERUSER', 'GROUP_ADMIN', 'MEMBER').
    """
    __tablename__ = "dict_user_roles"

    # Add any fields specific to 'UserRole'.
    # For example, a list of permissions associated with this role.
    # Storing permissions directly in the role table might be simple for some cases,
    # but a more complex RBAC might involve separate permission and role_permission tables.
    # permissions: Mapped[Optional[List[str]]] = mapped_column(
    #     JSON,
    #     nullable=True,
    #     comment="List of permission strings or keys associated with this role."
    # )

    # Another example: is_system_role, if some roles are fundamental and not user-deletable.
    # is_system_role: Mapped[bool] = mapped_column(
    #     Boolean,
    #     default=False,
    #     nullable=False,
    #     comment="True if this is a core system role and cannot be deleted by users."
    # )

    def __repr__(self) -> str:
        return super().__repr__() # BaseDictionaryModel provides a good default

if __name__ == "__main__":
    # This block is for demonstration of the UserRole model structure.
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- UserRole Dictionary Model --- Demonstration")

    # Example instances of UserRole
    superuser_role = UserRole(
        code="SUPERUSER",
        name="Superuser",
        description="Has all permissions across the entire system.",
        state="active",
        is_default=False, # Typically not a 'default' role for new users
        display_order=1,
        # permissions=["system:admin", "user:manage", "group:manage_all"], # If permissions field was added
        # is_system_role=True # If field was added
    )
    superuser_role.id = 1 # Simulate ORM-set ID
    superuser_role.created_at = datetime.now(timezone.utc) # Simulate timestamp
    superuser_role.updated_at = datetime.now(timezone.utc) # Simulate timestamp
    logger.info(f"Example UserRole: {superuser_role!r}, Description: {superuser_role.description}")
    # if hasattr(superuser_role, 'permissions'):
    #     logger.info(f"  Permissions: {superuser_role.permissions}")

    group_admin_role = UserRole(
        code="GROUP_ADMIN",
        name="Group Administrator",
        description="Manages a specific group, its members, and tasks.",
        state="active",
        display_order=2
    )
    group_admin_role.id = 2
    group_admin_role.created_at = datetime.now(timezone.utc)
    group_admin_role.updated_at = datetime.now(timezone.utc)
    logger.info(f"Example UserRole: {group_admin_role!r}, Name: {group_admin_role.name}")

    member_role = UserRole(
        code="MEMBER",
        name="Member",
        description="Regular user within a group, can complete tasks.",
        state="active",
        is_default=True, # Could be the default role for new group members
        display_order=3
    )
    member_role.id = 3
    member_role.created_at = datetime.now(timezone.utc)
    member_role.updated_at = datetime.now(timezone.utc)
    logger.info(f"Example UserRole: {member_role!r}, Is Default: {member_role.is_default}")

    # Show inherited and specific attributes (if any were added)
    # from sqlalchemy import create_engine
    # from backend.app.src.config.database import Base # Ensure Base is correctly imported
    # engine = create_engine("sqlite:///:memory:")
    # Base.metadata.create_all(engine) # This would create all tables defined using this Base
    # logger.info(f"Columns in UserRole ({UserRole.__tablename__}): {[c.name for c in UserRole.__table__.columns]}")
    logger.info("To see actual table columns, SQLAlchemy metadata needs to be initialized with an engine (e.g., Base.metadata.create_all(engine)).")
