# backend/app/src/models/dictionaries/group_types.py

"""
SQLAlchemy model for a 'GroupType' dictionary table.
This table stores different types or categories of groups (e.g., Family, Department, Organization).
"""

import logging
from typing import Optional # If adding specific optional fields
from datetime import datetime, timezone # For __main__ example

from sqlalchemy.orm import Mapped, mapped_column # If adding specific fields
from sqlalchemy import Integer, Boolean # If adding specific fields like default_max_members

from backend.app.src.models.dictionaries.base_dict import BaseDictionaryModel

# Configure logger for this module
logger = logging.getLogger(__name__)

class GroupType(BaseDictionaryModel):
    """
    Represents a type of group in a dictionary table (e.g., Family, Team, Department, Organization).
    Inherits common fields from BaseDictionaryModel.

    The 'code' field will be important (e.g., 'FAMILY', 'TEAM', 'DEPARTMENT').
    The 'description' can clarify the typical use case or characteristics of this group type.
    """
    __tablename__ = "dict_group_types"

    # Add any fields specific to 'GroupType' that are not in BaseDictionaryModel.
    # For example, you might want to specify default permissions or features enabled for this group type:
    # default_max_members: Mapped[Optional[int]] = mapped_column(
    #     Integer,
    #     nullable=True,
    #     comment="Default maximum number of members for groups of this type (can be overridden at group level)."
    # )
    # allows_subgroups: Mapped[bool] = mapped_column(
    #     Boolean,
    #     default=False,
    #     nullable=False,
    #     comment="Whether groups of this type can have subgroups."
    # )

    def __repr__(self) -> str:
        return super().__repr__() # BaseDictionaryModel provides a good default

if __name__ == "__main__":
    # This block is for demonstration of the GroupType model structure.
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- GroupType Dictionary Model --- Demonstration")

    # Example instances of GroupType
    family_type = GroupType(
        code="FAMILY",
        name="Family",
        description="A group for family members to share tasks and rewards.",
        state="active",
        display_order=1
        # default_max_members=10, # If field was added
        # allows_subgroups=False   # If field was added
    )
    family_type.id = 1 # Simulate ORM-set ID
    family_type.created_at = datetime.now(timezone.utc) # Simulate timestamp
    family_type.updated_at = datetime.now(timezone.utc) # Simulate timestamp
    logger.info(f"Example GroupType: {family_type!r}, Description: {family_type.description}")
    # if hasattr(family_type, 'default_max_members'):
    #     logger.info(f"  Default Max Members: {family_type.default_max_members}")

    department_type = GroupType(
        code="DEPARTMENT",
        name="Department",
        description="A group representing a department within an organization.",
        state="active",
        display_order=2
    )
    department_type.id = 2
    department_type.created_at = datetime.now(timezone.utc)
    department_type.updated_at = datetime.now(timezone.utc)
    logger.info(f"Example GroupType: {department_type!r}, Name: {department_type.name}")

    organization_type = GroupType(
        code="ORGANIZATION",
        name="Organization",
        description="A top-level group representing an entire organization.",
        state="active",
        display_order=3,
        # allows_subgroups=True # If field was added
    )
    organization_type.id = 3
    organization_type.created_at = datetime.now(timezone.utc)
    organization_type.updated_at = datetime.now(timezone.utc)
    logger.info(f"Example GroupType: {organization_type!r}, Is Default: {organization_type.is_default}")

    # Show inherited and specific attributes (if any were added)
    # from sqlalchemy import create_engine
    # from backend.app.src.config.database import Base # Ensure Base is correctly imported
    # engine = create_engine("sqlite:///:memory:")
    # Base.metadata.create_all(engine) # This would create all tables defined using this Base
    # logger.info(f"Columns in GroupType ({GroupType.__tablename__}): {[c.name for c in GroupType.__table__.columns]}")
    logger.info("To see actual table columns, SQLAlchemy metadata needs to be initialized with an engine (e.g., Base.metadata.create_all(engine)).")
