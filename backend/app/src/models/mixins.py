# backend/app/src/models/mixins.py

"""
This module defines common SQLAlchemy mixin classes.
Mixins provide a way to compose reusable sets of model fields and functionalities.
"""

import logging
from datetime import datetime, timezone
from typing import Optional # Added for Mapped[Optional[datetime]]

from sqlalchemy import Column, DateTime, String, Text, Integer, ForeignKey, func, Boolean
from sqlalchemy.orm import Mapped, mapped_column, declared_attr
from sqlalchemy.ext.hybrid import hybrid_property

# Configure logger for this module
logger = logging.getLogger(__name__)

class TimestampedMixin:
    """
    Mixin to add created_at and updated_at timestamp fields to a model.
    `created_at` is set once when the record is created.
    `updated_at` is set on creation and updated each time the record is modified.
    """
    @declared_attr
    def created_at(cls) -> Mapped[datetime]:
        return mapped_column(
            DateTime(timezone=True),
            server_default=func.now(), # Use database's now() function as default
            nullable=False,
            comment="Timestamp of when the record was created (UTC)"
        )

    @declared_attr
    def updated_at(cls) -> Mapped[datetime]:
        return mapped_column(
            DateTime(timezone=True),
            server_default=func.now(), # Use database's now() function as default
            onupdate=func.now(),       # Update with database's now() on modification
            nullable=False,
            comment="Timestamp of the last update to the record (UTC)"
        )

class SoftDeleteMixin:
    """
    Mixin for implementing soft delete functionality.
    Adds a `deleted_at` timestamp. When set, the record is considered deleted.
    """
    @declared_attr
    def deleted_at(cls) -> Mapped[Optional[datetime]]:
        return mapped_column(
            DateTime(timezone=True),
            nullable=True,
            comment="Timestamp of when the record was soft-deleted (UTC). Null if not deleted."
        )

    @hybrid_property
    def is_deleted(self) -> bool:
        """Returns True if the record is soft-deleted, False otherwise."""
        return self.deleted_at is not None

    @is_deleted.setter # type: ignore[no-redef]
    def is_deleted(self, value: bool) -> None:
        """Setter for is_deleted. Sets/clears deleted_at."""
        self.deleted_at = datetime.now(timezone.utc) if value else None

    # Optional: A method to query for active (not deleted) records easily
    # This might be better placed in a base repository or service class.
    # @classmethod
    # def query_active(cls, session):
    #     return session.query(cls).filter(cls.deleted_at.is_(None))

class NameDescriptionMixin:
    """
    Mixin to add common `name` and `description` fields.
    """
    @declared_attr
    def name(cls) -> Mapped[str]:
        return mapped_column(String(255), nullable=False, comment="Name of the entity (e.g., group name, task name)")

    @declared_attr
    def description(cls) -> Mapped[Optional[str]]:
        return mapped_column(Text, nullable=True, comment="Optional detailed description of the entity")

class StateMixin:
    """
    Mixin to add a `state` field, typically representing the status or state of an entity.
    The actual type of state (e.g., string, enum) might vary, so String is used here as a common default.
    Consider using SQLAlchemy's Enum type if states are fixed and known.
    """
    @declared_attr
    def state(cls) -> Mapped[Optional[str]]: # Or specific Enum(YourStateType) for stricter typing
        return mapped_column(String(50), nullable=True, comment="Current state or status of the entity")

class GroupAffiliationMixin:
    """
    Mixin to add a `group_id` foreign key, linking the entity to a group.
    Assumes a 'groups' table with an 'id' primary key.
    """
    @declared_attr
    def group_id(cls) -> Mapped[Optional[int]]:
        # The ForeignKey target 'groups.id' is a string. SQLAlchemy resolves this later.
        # Ensure you have a Group model with a table named 'groups'.
        return mapped_column(Integer, ForeignKey("groups.id"), nullable=True, index=True, comment="Identifier of the group this entity belongs to, if applicable")

    # If you also want to establish the relationship from this mixin, you could add:
    # from sqlalchemy.orm import relationship
    # @declared_attr
    # def group(cls) -> Mapped[Optional["Group"]]: # Forward reference to Group model
    #     return relationship("Group", primaryjoin=lambda: cls.group_id == foreign(Group.id))
    # However, managing relationships explicitly in the main model classes is often clearer.

class NotesMixin:
    """
    Mixin to add a `notes` field for general remarks or internal comments.
    """
    @declared_attr
    def notes(cls) -> Mapped[Optional[str]]:
        return mapped_column(Text, nullable=True, comment="Internal notes or general remarks about the entity")

class UserAffiliationMixin:
    """
    Mixin to add a `user_id` foreign key, linking the entity to a user.
    Assumes a 'users' table with an 'id' primary key.
    """
    @declared_attr
    def user_id(cls) -> Mapped[int]: # Assuming user_id is usually mandatory if this mixin is used
        return mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="Identifier of the user associated with this entity")

    # Similar to GroupAffiliationMixin, relationships can be defined here or in the main model.
    # @declared_attr
    # def user(cls) -> Mapped["User"]:
    #     return relationship("User", primaryjoin=lambda: cls.user_id == foreign(User.id))

class CodeMixin:
    """
    Mixin to add a `code` field, often used for unique, human-readable identifiers.
    """
    @declared_attr
    def code(cls) -> Mapped[str]:
        return mapped_column(String(100), nullable=False, unique=True, index=True, comment="Unique code or short identifier for the entity")

if __name__ == "__main__":
    # This block is for demonstration and basic testing of mixin definitions.
    # To run this, you'd need a SQLAlchemy Base and an engine setup.
    # For now, it just logs information about the mixins.

    # Configure basic logging for demonstration if no handlers are configured by setup_logging
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- SQLAlchemy Model Mixins --- demonstrating structure (not DB interaction)")

    mixins_info = {
        "TimestampedMixin": [col for col in dir(TimestampedMixin) if not col.startswith('_') and col not in ['metadata']],
        "SoftDeleteMixin": [col for col in dir(SoftDeleteMixin) if not col.startswith('_') and col not in ['metadata', 'is_deleted']], # is_deleted is a hybrid_property, not a direct column
        "NameDescriptionMixin": [col for col in dir(NameDescriptionMixin) if not col.startswith('_') and col not in ['metadata']],
        "StateMixin": [col for col in dir(StateMixin) if not col.startswith('_') and col not in ['metadata']],
        "GroupAffiliationMixin": [col for col in dir(GroupAffiliationMixin) if not col.startswith('_') and col not in ['metadata']],
        "NotesMixin": [col for col in dir(NotesMixin) if not col.startswith('_') and col not in ['metadata']],
        "UserAffiliationMixin": [col for col in dir(UserAffiliationMixin) if not col.startswith('_') and col not in ['metadata']],
        "CodeMixin": [col for col in dir(CodeMixin) if not col.startswith('_') and col not in ['metadata']],
    }

    for mixin_name, attributes in mixins_info.items():
        # For declared_attr, these are methods on the class, not instance attributes yet
        actual_attrs = []
        mixin_class = globals()[mixin_name]
        for attr_name in attributes:
            attr = getattr(mixin_class, attr_name)
            if isinstance(attr, declared_attr) or isinstance(attr, hybrid_property):
                 actual_attrs.append(attr_name)
            elif callable(attr) and not attr_name.startswith('_'): # methods from declared_attr
                 actual_attrs.append(attr_name + "()")


        logger.debug(f"{mixin_name} provides attributes/methods: {actual_attrs}")


    # Example of how a mixin would be used (conceptual, without full SQLAlchemy setup here)
    # Need a Base for this to be more meaningful
    # from sqlalchemy.orm import DeclarativeBase
    # class Base(DeclarativeBase): pass

    class ExampleModel(TimestampedMixin, NameDescriptionMixin, SoftDeleteMixin): # Add Base if testing with SQLAlchemy
        # __tablename__ = "examples" # Needed for real SQLAlchemy model
        id: Mapped[int] = mapped_column(primary_key=True) # Example primary key
        # To make this runnable for attribute inspection, we'd need Base
        # and to define __table_args__ or similar if not using Base.
        # For now, this is conceptual.

    logger.info(f"Conceptual ExampleModel would inherit fields from TimestampedMixin, NameDescriptionMixin, SoftDeleteMixin.")
    # To actually see the columns, one would need to inspect ExampleModel.__table__.columns
    # after Base.metadata.create_all(engine) or by compiling the model.

    # Testing SoftDeleteMixin's hybrid property (conceptual)
    class DummyDeletable(SoftDeleteMixin): # Add Base if testing with SQLAlchemy
        pass # No primary key, so can't be mapped directly

    dummy = DummyDeletable()
    logger.debug(f"Initial dummy.is_deleted: {dummy.is_deleted}, dummy.deleted_at: {dummy.deleted_at}")
    dummy.is_deleted = True
    logger.debug(f"After dummy.is_deleted = True: dummy.is_deleted: {dummy.is_deleted}, dummy.deleted_at: {str(dummy.deleted_at)[:19] if dummy.deleted_at else None}}") # Truncate for cleaner log
    dummy.is_deleted = False
    logger.debug(f"After dummy.is_deleted = False: dummy.is_deleted: {dummy.is_deleted}, dummy.deleted_at: {dummy.deleted_at}")
