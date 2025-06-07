# backend/app/src/models/base.py

"""
This module defines the base model classes for the application.
- `Base` is imported from `config.database` and is the declarative base for all models.
- `BaseModel` provides common fields like `id` and timestamps.
- `BaseMainModel` extends `BaseModel` with additional common fields for main business entities.
"""

import logging
from typing import Optional, TypeVar

from sqlalchemy.orm import Mapped, mapped_column, declared_attr
from sqlalchemy import Integer

from backend.app.src.config.database import Base # Declarative base from SQLAlchemy setup
from backend.app.src.models.mixins import (
    TimestampedMixin,
    SoftDeleteMixin,
    NameDescriptionMixin,
    StateMixin,
    GroupAffiliationMixin,
    NotesMixin
)

# Configure logger for this module
logger = logging.getLogger(__name__)

# Generic TypeVariable that can be used for ORM models in services/repositories
ModelT = TypeVar("ModelT", bound="BaseModel")

class BaseModel(Base, TimestampedMixin):
    """
    Base class for all SQLAlchemy models in the application.
    Inherits from the global `Base` (declarative_base()) and `TimestampedMixin`.

    Includes:
        - id: Primary key integer column.
        - created_at: Timestamp of creation (from TimestampedMixin).
        - updated_at: Timestamp of last update (from TimestampedMixin).
    """
    __abstract__ = True  # Indicates that this class should not be mapped to a database table itself

    @declared_attr
    def __tablename__(cls) -> str:
        # Automatically generate table name from class name (e.g., UserProfile -> user_profiles)
        # This is a common convention but can be overridden in subclasses if needed.
        import re
        name_parts = re.findall(r'[A-Z][^A-Z]*', cls.__name__)
        # Handle case where a class name might be all caps like "URLShortener" -> "url_shorteners"
        if not name_parts: # If class name is all uppercase or single word
            return cls.__name__.lower() + "s"
        return "_".join(part.lower() for part in name_parts) + "s" # Simple pluralization by adding 's'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True, comment="Unique identifier for the record")

class BaseMainModel(BaseModel, NameDescriptionMixin, StateMixin, SoftDeleteMixin, NotesMixin):
    """
    Base class for main business entities in the application.
    Inherits from `BaseModel` and includes other common mixins.

    Includes (in addition to BaseModel fields):
        - name: Name of the entity (from NameDescriptionMixin).
        - description: Optional detailed description (from NameDescriptionMixin).
        - state: Current state or status (from StateMixin).
        - deleted_at: Timestamp for soft deletion (from SoftDeleteMixin).
        - is_deleted: Hybrid property for soft deletion status (from SoftDeleteMixin).
        - notes: Internal notes or general remarks (from NotesMixin).

    The `GroupAffiliationMixin` is intentionally omitted here to make this base model
    more generally applicable. Models that are group-affiliated can include
    `GroupAffiliationMixin` explicitly.
    Alternatively, another base class like `BaseGroupAffiliatedMainModel` could be created.
    """
    __abstract__ = True

    # No additional fields are defined here directly, they come from the inherited mixins.
    # Specific models inheriting from this will add their own unique fields and relationships.

# Example of a more specific base model that includes group affiliation
class BaseGroupAffiliatedMainModel(BaseMainModel, GroupAffiliationMixin):
    """
    Base class for main business entities that are directly affiliated with a group.
    Inherits from `BaseMainModel` and adds `GroupAffiliationMixin`.
    """
    __abstract__ = True


if __name__ == "__main__":
    # This block is for demonstration of the base model structure.
    # It does not interact with the database directly here.

    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- SQLAlchemy Base Models --- demonstrating structure")

    logger.info(f"BaseModel inherits from: {BaseModel.__mro__}")
    logger.info(f"BaseMainModel inherits from: {BaseMainModel.__mro__}")
    logger.info(f"BaseGroupAffiliatedMainModel inherits from: {BaseGroupAffiliatedMainModel.__mro__}")

    # Show generated tablenames (conceptual)
    class User(BaseModel):
        __tablename__ = "users" # Explicitly set for this common case
        username: Mapped[str]

    class ProductOffering(BaseModel):
        # Tablename will be 'product_offerings' by default
        pass

    class URLShortener(BaseModel):
        # Tablename will be 'url_shorteners' by default
        pass

    class SomeGroupedItem(BaseGroupAffiliatedMainModel):
        # Tablename will be 'some_grouped_items' by default
        # Will have id, created_at, updated_at, name, description, state, deleted_at, notes, group_id
        specific_field: Mapped[Optional[str]]

    logger.debug(f"Example User tablename (explicit): {User.__tablename__}")
    logger.debug(f"Example ProductOffering tablename (generated): {ProductOffering.__tablename__}")
    logger.debug(f"Example URLShortener tablename (generated): {URLShortener.__tablename__}")
    logger.debug(f"Example SomeGroupedItem tablename (generated): {SomeGroupedItem.__tablename__}")

    # To inspect actual columns, you would need to initialize Base.metadata with an engine
    # and then access SomeGroupedItem.__table__.columns
    # For example:
    # from sqlalchemy import create_engine
    # engine = create_engine("sqlite:///:memory:")
    # Base.metadata.create_all(engine) # This would require all referenced tables (like 'groups' for SomeGroupedItem) to be defined.
    # logger.info(f"Columns in SomeGroupedItem: {[c.name for c in SomeGroupedItem.__table__.columns]}")

    logger.info("BaseModel provides 'id', 'created_at', 'updated_at'.")
    logger.info("BaseMainModel adds 'name', 'description', 'state', 'deleted_at', 'is_deleted' (hybrid), 'notes'.")
    logger.info("BaseGroupAffiliatedMainModel further adds 'group_id'.")
