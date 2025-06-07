# backend/app/src/models/dictionaries/base_dict.py

"""
Defines the base model for all dictionary (lookup) tables.
"""

import logging
from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column, declared_attr
from sqlalchemy import String, Boolean, Integer # For is_active, display_order

from backend.app.src.models.base import BaseMainModel # Using BaseMainModel for name, description, state, notes, soft_delete, timestamps
from backend.app.src.models.mixins import CodeMixin # For a unique 'code' field

# Configure logger for this module
logger = logging.getLogger(__name__)

class BaseDictionaryModel(BaseMainModel, CodeMixin):
    """
    Base class for dictionary (lookup) models.
    Inherits from BaseMainModel to get common fields like id, name, description,
    state, notes, created_at, updated_at, deleted_at.
    Adds a `code` field from CodeMixin for a unique, human-readable identifier.
    Also includes `is_default` and `display_order` for common dictionary behaviors.

    Common fields for dictionary models:
    - id: Primary key (from BaseModel -> BaseMainModel).
    - code: Unique string identifier (from CodeMixin).
    - name: Human-readable name (from NameDescriptionMixin -> BaseMainModel).
    - description: Optional detailed description (from NameDescriptionMixin -> BaseMainModel).
    - state: Optional state (e.g., 'active', 'inactive') (from StateMixin -> BaseMainModel).
    - is_default: Boolean, if this is a default value for the dictionary.
    - display_order: Integer, for ordering items in UI lists.
    - created_at, updated_at: Timestamps (from TimestampedMixin -> BaseModel -> BaseMainModel).
    - deleted_at: For soft deletion (from SoftDeleteMixin -> BaseMainModel).
    - notes: Optional internal notes (from NotesMixin -> BaseMainModel).
    """
    __abstract__ = True

    # `code` is inherited from CodeMixin (unique, indexed string)
    # `name`, `description` are inherited from NameDescriptionMixin (via BaseMainModel)
    # `state` is inherited from StateMixin (via BaseMainModel)
    # `notes` is inherited from NotesMixin (via BaseMainModel)
    # `created_at`, `updated_at`, `deleted_at`, `is_deleted` are inherited via BaseMainModel

    is_default: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        default=False,
        nullable=True, # Can be True, False, or Null if not applicable/set
        comment="Indicates if this is a default value for the dictionary type."
    )

    display_order: Mapped[Optional[int]] = mapped_column(
        Integer,
        default=0,
        nullable=True, # Can be ordered or Null if not applicable/set
        comment="Order in which this item should be displayed in lists/dropdowns."
    )

    # Override tablename generation if dictionary tables should have a specific prefix or suffix
    # For example, if all dictionary tables should be like 'dict_statuses', 'dict_user_roles'
    # @declared_attr
    # def __tablename__(cls) -> str:
    #     import re
    #     # Default tablename generation from BaseModel is ClassName -> class_names
    #     # For dictionaries, we might prefer dict_class_names
    #     base_tablename = super().__tablename__
    #     return f"dict_{base_tablename}"
    # For now, it will use the default from BaseModel (e.g., UserRole -> user_roles)
    # which is often fine.

    def __repr__(self) -> str:
        # hasattr checks are to prevent errors if a subclass somehow doesn't have these (though they should)
        _id = getattr(self, 'id', 'N/A')
        _code = getattr(self, 'code', 'N/A')
        _name = getattr(self, 'name', 'N/A')
        return f"<{self.__class__.__name__}(id={_id}, code='{_code}', name='{_name}')>"

if __name__ == "__main__":
    # This block is for demonstration of the BaseDictionaryModel structure.
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- BaseDictionaryModel --- Demonstration")

    # Show how a concrete dictionary model would inherit fields
    class ExampleStatus(BaseDictionaryModel):
        # If __tablename__ is not set, it would be 'example_statuss' by default from BaseModel's logic
        # or 'dict_example_statuss' if the commented-out __tablename__ override in BaseDictionaryModel was active.
        __tablename__ = "example_statuses" # Explicit table name for example clarity

        # It automatically gets id, code, name, description, state, is_default, display_order,
        # created_at, updated_at, deleted_at, notes.
        custom_field_for_status: Mapped[Optional[str]] = mapped_column(String(100))

    logger.info(f"BaseDictionaryModel inherits from: {BaseDictionaryModel.__mro__}")
    logger.info(f"ExampleStatus inherits from: {ExampleStatus.__mro__}")
    logger.info(f"ExampleStatus default tablename if not overridden: {ExampleStatus.__tablename__}")


    # To inspect actual columns, you would need to initialize Base.metadata with an engine
    # and then access ExampleStatus.__table__.columns
    # from sqlalchemy import create_engine
    # from backend.app.src.config.database import Base # Ensure Base is the one used by models
    # engine = create_engine("sqlite:///:memory:")
    # Base.metadata.create_all(engine) # This would create all tables defined using this Base
    # logger.info(f"Columns in ExampleStatus: {[c.name for c in ExampleStatus.__table__.columns]}")
    # This list would include: id, created_at, updated_at, name, description, state, deleted_at, notes,
    #                          code, is_default, display_order, custom_field_for_status
    logger.info("To see actual table columns, SQLAlchemy metadata needs to be initialized with an engine (e.g., Base.metadata.create_all(engine)).")


    status_instance = ExampleStatus(
        code="ACTIVE",
        name="Active Status",
        description="Item is active and usable.",
        is_default=True,
        display_order=1,
        custom_field_for_status="Some custom data"
    )
    # Simulate ORM-set fields for demo
    status_instance.id = 1 # Typically set by DB
    # status_instance.created_at, .updated_at would be set by DB/ORM or TimestampedMixin defaults

    logger.info(f"Example instance: {status_instance!r}")
    logger.info(f"  Code: {status_instance.code}")
    logger.info(f"  Name: {status_instance.name}")
    logger.info(f"  Is Default: {status_instance.is_default}")
    logger.info(f"  Display Order: {status_instance.display_order}")
    logger.info(f"  Custom Field: {status_instance.custom_field_for_status}")
    logger.info(f"  State (from BaseMainModel): {status_instance.state}") # Initial state would be None unless set
    status_instance.state = "PUBLISHED"
    logger.info(f"  Updated State: {status_instance.state}")
