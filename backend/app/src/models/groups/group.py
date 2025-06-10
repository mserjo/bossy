# backend/app/src/models/groups/group.py

"""
SQLAlchemy model for Groups.
"""

import logging
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime, timezone # Added timezone for __main__ example

from sqlalchemy import String, ForeignKey, Integer # Added Integer for FKs
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.src.models.base import BaseMainModel # Groups are main entities
# A Group itself doesn't usually belong to another group via GroupAffiliationMixin in its primary definition.
# If subgroups are a feature, that's a self-referential FK or a separate linkage.

# Configure logger for this module
logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from backend.app.src.models.auth.user import User # For owner relationship
    from backend.app.src.models.groups.membership import GroupMembership
    from backend.app.src.models.groups.settings import GroupSetting
    from backend.app.src.models.groups.invitation import GroupInvitation
    from backend.app.src.models.tasks.task import Task
    from backend.app.src.models.tasks.event import Event
    from backend.app.src.models.bonuses.reward import Reward
    from backend.app.src.models.dictionaries.group_types import GroupType # For group_type relationship

class Group(BaseMainModel): # Inherits id, name, description, state, notes, created_at, updated_at, deleted_at
    """
    Represents a group in the system (e.g., a family, a team, an organization department).
    """
    __tablename__ = "groups"

    # 'name' and 'description' inherited from BaseMainModel are suitable for group name and description.
    # 'state' can be used for 'active', 'archived', etc.

    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="The user who owns/created this group")
    group_type_id: Mapped[int] = mapped_column(Integer, ForeignKey("dict_group_types.id"), nullable=False, index=True, comment="FK to group_types dictionary")

    icon_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True, comment="URL to an icon for the group")
    currency_name: Mapped[Optional[str]] = mapped_column(String(50), default="points", comment="Custom name for the group's currency/points (e.g., Kudos, Stars)")
    # Consider settings like max_debt in GroupSetting if they are numerous or complex.

    # --- Relationships ---
    owner: Mapped["User"] = relationship(back_populates="owned_groups", foreign_keys=[owner_id])
    group_type: Mapped["GroupType"] = relationship(foreign_keys=[group_type_id]) # Relationship to dict_group_types

    # Members of the group (via association table GroupMembership)
    memberships: Mapped[List["GroupMembership"]] = relationship(back_populates="group", cascade="all, delete-orphan")
    # To get User objects directly, you might need a secondary relationship or iterate through memberships.
    # users: Mapped[List["User"]] = relationship(secondary="group_memberships", viewonly=True,
    #                                           primaryjoin="Group.id == GroupMembership.group_id",
    #                                           secondaryjoin="GroupMembership.user_id == User.id")
    # This common setup for many-to-many with association object needs careful primary/secondary join conditions.

    settings: Mapped[List["GroupSetting"]] = relationship(back_populates="group", cascade="all, delete-orphan")
    invitations: Mapped[List["GroupInvitation"]] = relationship(back_populates="group", cascade="all, delete-orphan")

    tasks: Mapped[List["Task"]] = relationship(back_populates="group", foreign_keys="Task.group_id")
    events: Mapped[List["Event"]] = relationship(back_populates="group", foreign_keys="Event.group_id")
    rewards: Mapped[List["Reward"]] = relationship(back_populates="group", foreign_keys="Reward.group_id")

    # If groups can have sub-groups (parent-child relationship):
    # parent_group_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("groups.id"), nullable=True)
    # parent_group: Mapped[Optional["Group"]] = relationship(remote_side=[id], back_populates="sub_groups")
    # sub_groups: Mapped[List["Group"]] = relationship(back_populates="parent_group", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        id_val = getattr(self, 'id', 'N/A')
        return f"<Group(id={id_val}, name='{self.name}', owner_id={self.owner_id})>"

if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- Group Model --- Demonstration")

    # Example Group instance
    # Assume User with id=1 and GroupType with id=1 exist for FKs
    demo_group = Group(
        name="The Cool Family",
        description="A group for the coolest family to manage chores and fun.",
        owner_id=1,
        group_type_id=1,
        icon_url="https://example.com/icons/cool_family.png",
        currency_name="Coolness Points",
        state="active" # from BaseMainModel
    )
    demo_group.id = 1 # Simulate ORM-set ID
    demo_group.created_at = datetime.now(timezone.utc) # Simulate timestamp
    demo_group.updated_at = datetime.now(timezone.utc) # Simulate timestamp

    logger.info(f"Example Group: {demo_group!r}")
    logger.info(f"  Name: {demo_group.name}")
    logger.info(f"  Currency: {demo_group.currency_name}")
    logger.info(f"  Owner ID: {demo_group.owner_id}")
    logger.info(f"  State: {demo_group.state}")
    logger.info(f"  Description: {demo_group.description}")
    logger.info(f"  Created At: {demo_group.created_at.isoformat() if demo_group.created_at else 'N/A'}")


    # To view relationships, a DB session and related objects would be needed.
    # The following line would error if run directly without SQLAlchemy engine and metadata setup for all related tables.
    # logger.info(f"Group attributes (conceptual table columns): {[c.name for c in Group.__table__.columns if not c.name.startswith('_')]}")
    logger.info("To see actual table columns, SQLAlchemy metadata needs to be initialized with an engine (e.g., Base.metadata.create_all(engine)).")
