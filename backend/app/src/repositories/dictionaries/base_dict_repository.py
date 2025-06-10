# backend/app/src/repositories/dictionaries/base_dict_repository.py

"""
Defines the BaseDictionaryRepository for common operations on dictionary models.
"""

import logging
from typing import Optional, TypeVar, Generic, Union, Dict, Any # Added Generic, Union, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.src.models.dictionaries.base_dict import BaseDictionaryModel
from backend.app.src.schemas.dictionaries.base_dict import DictionaryCreate, DictionaryUpdate
from backend.app.src.repositories.base import BaseRepository

logger = logging.getLogger(__name__)

# Define TypeVars for the model and schemas, specific to dictionary repositories
DictModelType = TypeVar("DictModelType", bound=BaseDictionaryModel)
DictCreateSchemaType = TypeVar("DictCreateSchemaType", bound=DictionaryCreate)
DictUpdateSchemaType = TypeVar("DictUpdateSchemaType", bound=DictionaryUpdate)


class BaseDictionaryRepository(
    BaseRepository[DictModelType, DictCreateSchemaType, DictUpdateSchemaType],
    Generic[DictModelType, DictCreateSchemaType, DictUpdateSchemaType] # Explicitly Generic
):
    """
    Base repository for dictionary models.
    Inherits from BaseRepository and adds common methods specific to
    dictionary entities that have a 'code' attribute.

    It's generic and expects DictModelType to be a subclass of BaseDictionaryModel,
    and schema types to be subclasses of common dictionary Pydantic schemas.
    """

    # __init__ is inherited from BaseRepository, which takes the model type.

    async def get_by_code(self, db: AsyncSession, *, code: str) -> Optional[DictModelType]:
        """
        Retrieves a dictionary item by its unique code.

        Args:
            db: The SQLAlchemy asynchronous database session.
            code: The unique code of the dictionary item.

        Returns:
            The dictionary model instance if found, otherwise None.
        """
        # BaseDictionaryModel (which DictModelType is bound to) includes CodeMixin, so 'code' is expected.
        statement = select(self.model).where(self.model.code == code) # type: ignore[attr-defined]
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_name(self, db: AsyncSession, *, name: str) -> Optional[DictModelType]:
        """
        Retrieves a dictionary item by its name.
        Note: Names might not always be unique. This returns the first match.

        Args:
            db: The SQLAlchemy asynchronous database session.
            name: The name of the dictionary item.

        Returns:
            The dictionary model instance if found (first match), otherwise None.
        """
        # BaseDictionaryModel inherits from BaseMainModel, which has NameDescriptionMixin, so 'name' is expected.
        statement = select(self.model).where(self.model.name == name) # type: ignore[attr-defined]
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_default(self, db: AsyncSession) -> Optional[DictModelType]:
        """
        Retrieves the default dictionary item for this type (where is_default is True).

        Args:
            db: The SQLAlchemy asynchronous database session.

        Returns:
            The default dictionary model instance if one is set, otherwise None.
        """
        # BaseDictionaryModel has 'is_default' attribute.
        statement = select(self.model).where(self.model.is_default == True) # type: ignore[attr-defined]
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    # Example of overriding create/update if 'code' needs to be uppercased automatically.
    # By default, the base methods from BaseRepository will be used.
    # If such transformations are needed, they should be consistently applied.

    # async def create(self, db: AsyncSession, *, obj_in: DictCreateSchemaType) -> DictModelType:
    #     """
    #     Creates a new dictionary item, ensuring 'code' is uppercase if provided.
    #     """
    #     # obj_in_data = obj_in.model_dump()
    #     # if 'code' in obj_in_data and isinstance(obj_in_data['code'], str):
    #     #     obj_in_data['code'] = obj_in_data['code'].upper()
    #     #
    #     # # Re-create schema or pass dict if super method allows
    #     # # This example assumes super().create can handle a modified dict or that
    #     # # you'd create a new schema instance from obj_in_data if necessary.
    #     # # For simplicity, if passing obj_in directly and modifying it:
    #     if hasattr(obj_in, 'code') and isinstance(obj_in.code, str):
    #         obj_in.code = obj_in.code.upper() # Modify the schema instance directly
    #
    #     return await super().create(db, obj_in=obj_in)

    # async def update(
    #     self,
    #     db: AsyncSession,
    #     *,
    #     db_obj: DictModelType,
    #     obj_in: Union[DictUpdateSchemaType, Dict[str, Any]]
    # ) -> DictModelType:
    #     """
    #     Updates a dictionary item, ensuring 'code' is uppercase if being updated.
    #     """
    #     update_data: Dict[str, Any]
    #     if isinstance(obj_in, dict):
    #         # If obj_in is already a dict, work with it directly
    #         if 'code' in obj_in and isinstance(obj_in['code'], str):
    #             obj_in['code'] = obj_in['code'].upper()
    #         return await super().update(db, db_obj=db_obj, obj_in=obj_in)
    #     else:
    #         # If obj_in is a Pydantic schema, dump it, modify, then pass dict to super
    #         # This assumes super().update can handle a dict.
    #         # If super().update strictly needs a schema, this logic needs adjustment.
    #         update_data_dict = obj_in.model_dump(exclude_unset=True)
    #         if 'code' in update_data_dict and isinstance(update_data_dict['code'], str):
    #             update_data_dict['code'] = update_data_dict['code'].upper()
    #         return await super().update(db, db_obj=db_obj, obj_in=update_data_dict)
