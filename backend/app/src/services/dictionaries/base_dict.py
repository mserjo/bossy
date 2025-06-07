# backend/app/src/services/dictionaries/base_dict.py
import logging
from typing import TypeVar, Generic, List, Optional, Type, Any # Added Any for setattr
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel

from app.src.services.base import BaseService
# Assuming dictionary models will have at least these fields from a base model:
# id (UUID), code (str), name (str), description (Optional[str])
# from app.src.models.dictionaries.base_dict import BaseDictionaryModel # Example base for dictionary ORM models

# Define generic types for the model and Pydantic schemas
ModelType = TypeVar("ModelType") # Should be a SQLAlchemy model (e.g., subclass of BaseDictionaryModel)
SchemaCreateType = TypeVar("SchemaCreateType", bound=BaseModel)
SchemaUpdateType = TypeVar("SchemaUpdateType", bound=BaseModel)
SchemaResponseType = TypeVar("SchemaResponseType", bound=BaseModel)

# Initialize logger for this module
logger = logging.getLogger(__name__)

class BaseDictionaryService(
    BaseService,
    Generic[ModelType, SchemaCreateType, SchemaUpdateType, SchemaResponseType]
):
    """
    Generic base service for dictionary-like models.
    Provides common CRUD operations for models that typically have 'id', 'code', 'name',
    and 'description' fields.

    Assumes the ModelType has 'id', 'code', and 'name' attributes.
    The Pydantic schemas should correspond to the ModelType structure.
    """

    def __init__(self, db_session: AsyncSession, model: Type[ModelType], response_schema: Type[SchemaResponseType]):
        """
        Initializes the BaseDictionaryService.

        Args:
            db_session (AsyncSession): The SQLAlchemy asynchronous database session.
            model (Type[ModelType]): The SQLAlchemy model class for this dictionary.
            response_schema (Type[SchemaResponseType]): The Pydantic schema for responses.
        """
        super().__init__(db_session)
        self.model = model
        self.response_schema = response_schema
        self._model_name = self.model.__name__ # For logging
        logger.info(f"BaseDictionaryService initialized for model: {self._model_name}")

    async def get_by_id(self, item_id: UUID) -> Optional[SchemaResponseType]:
        """Retrieves a dictionary item by its ID."""
        logger.debug(f"Attempting to retrieve {self._model_name} by ID: {item_id}")
        stmt = select(self.model).where(self.model.id == item_id) # type: ignore
        result = await self.db_session.execute(stmt)
        item_db = result.scalar_one_or_none()

        if item_db:
            logger.info(f"{self._model_name} with ID '{item_id}' found.")
            # return self.response_schema.model_validate(item_db) # Pydantic v2
            return self.response_schema.from_orm(item_db) # Pydantic v1
        logger.info(f"{self._model_name} with ID '{item_id}' not found.")
        return None

    async def get_by_code(self, code: str) -> Optional[SchemaResponseType]:
        """Retrieves a dictionary item by its unique code."""
        logger.debug(f"Attempting to retrieve {self._model_name} by code: {code}")
        # Ensure the model actually has a 'code' attribute. This is an assumption for dictionary items.
        if not hasattr(self.model, 'code'):
            logger.error(f"Model {self._model_name} does not have a 'code' attribute. Cannot get_by_code.")
            # Or raise an appropriate error, e.g., AttributeError or NotImplementedError
            return None

        stmt = select(self.model).where(self.model.code == code) # type: ignore
        result = await self.db_session.execute(stmt)
        item_db = result.scalar_one_or_none()

        if item_db:
            logger.info(f"{self._model_name} with code '{code}' found.")
            # return self.response_schema.model_validate(item_db) # Pydantic v2
            return self.response_schema.from_orm(item_db) # Pydantic v1
        logger.info(f"{self._model_name} with code '{code}' not found.")
        return None

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[SchemaResponseType]:
        """Retrieves all items for this dictionary type, with pagination."""
        logger.debug(f"Attempting to retrieve all {self._model_name} items with skip={skip}, limit={limit}")
        order_by_attr = getattr(self.model, 'name', self.model.id) # type: ignore
        stmt = select(self.model).order_by(order_by_attr).offset(skip).limit(limit)
        result = await self.db_session.execute(stmt)
        items_db = result.scalars().all()

        # response_list = [self.response_schema.model_validate(item) for item in items_db] # Pydantic v2
        response_list = [self.response_schema.from_orm(item) for item in items_db] # Pydantic v1
        logger.info(f"Retrieved {len(response_list)} {self._model_name} items.")
        return response_list

    async def create(self, data: SchemaCreateType) -> SchemaResponseType:
        """
        Creates a new dictionary item.
        Checks for uniqueness of 'code' and 'name' if they exist in the creation schema.
        """
        logger.debug(f"Attempting to create new {self._model_name} with data: {data}")

        # Check for uniqueness of 'code' if model and data have it
        if hasattr(self.model, 'code') and hasattr(data, 'code'):
            existing_by_code = await self.get_by_code(data.code) # type: ignore
            if existing_by_code:
                logger.warning(f"{self._model_name} with code '{data.code}' already exists. Creation aborted.") # type: ignore
                raise ValueError(f"{self._model_name} with code '{data.code}' already exists.") # type: ignore

        # Check for uniqueness of 'name' if model and data have it
        # This might be too restrictive for some dictionaries, adjust if needed.
        if hasattr(self.model, 'name') and hasattr(data, 'name'):
            stmt_name = select(self.model).where(self.model.name == data.name) # type: ignore
            existing_by_name = (await self.db_session.execute(stmt_name)).scalar_one_or_none()
            if existing_by_name:
                logger.warning(f"{self._model_name} with name '{data.name}' already exists. Creation aborted.") # type: ignore
                raise ValueError(f"{self._model_name} with name '{data.name}' already exists.") # type: ignore

        # new_item_db = self.model(**data.model_dump()) # Pydantic v2
        new_item_db = self.model(**data.dict()) # Pydantic v1

        self.db_session.add(new_item_db)
        await self.commit()
        await self.db_session.refresh(new_item_db)

        logger.info(f"{self._model_name} created successfully with ID: {new_item_db.id}") # type: ignore
        # return self.response_schema.model_validate(new_item_db) # Pydantic v2
        return self.response_schema.from_orm(new_item_db) # Pydantic v1

    async def update(self, item_id: UUID, data: SchemaUpdateType) -> Optional[SchemaResponseType]:
        """
        Updates an existing dictionary item by its ID.
        Checks for uniqueness if 'code' or 'name' are being changed.
        """
        logger.debug(f"Attempting to update {self._model_name} with ID: {item_id}")

        stmt = select(self.model).where(self.model.id == item_id) # type: ignore
        item_db = (await self.db_session.execute(stmt)).scalar_one_or_none()

        if not item_db:
            logger.warning(f"{self._model_name} with ID '{item_id}' not found for update.")
            return None

        # update_data = data.model_dump(exclude_unset=True) # Pydantic v2
        update_data = data.dict(exclude_unset=True) # Pydantic v1

        # Check for 'code' uniqueness if it's being changed
        if 'code' in update_data and hasattr(self.model, 'code') and update_data['code'] != item_db.code: # type: ignore
            existing_by_code = await self.get_by_code(update_data['code'])
            if existing_by_code and existing_by_code.id != item_id: # Check if found code belongs to another item # type: ignore
                logger.warning(f"Cannot update code for {self._model_name} ID '{item_id}' to '{update_data['code']}' as it's used by another item.")
                raise ValueError(f"Another {self._model_name} with code '{update_data['code']}' already exists.")

        # Check for 'name' uniqueness if it's being changed
        if 'name' in update_data and hasattr(self.model, 'name') and update_data['name'] != item_db.name: # type: ignore
            stmt_name = select(self.model).where(self.model.name == update_data['name']) # type: ignore
            existing_by_name = (await self.db_session.execute(stmt_name)).scalar_one_or_none()
            if existing_by_name and existing_by_name.id != item_id: # type: ignore
                logger.warning(f"Cannot update name for {self._model_name} ID '{item_id}' to '{update_data['name']}' as it's used by another item.")
                raise ValueError(f"Another {self._model_name} with name '{update_data['name']}' already exists.")

        for field, value in update_data.items():
            setattr(item_db, field, value)

        self.db_session.add(item_db)
        await self.commit()
        await self.db_session.refresh(item_db)

        logger.info(f"{self._model_name} with ID '{item_id}' updated successfully.")
        # return self.response_schema.model_validate(item_db) # Pydantic v2
        return self.response_schema.from_orm(item_db) # Pydantic v1

    async def delete(self, item_id: UUID) -> bool:
        """
        Deletes a dictionary item by its ID.
        Consider implications like foreign key constraints if items are linked.
        A soft delete (setting an 'is_active' or 'deleted_at' field) might be
        preferable for some dictionaries and would require a different implementation.
        This implements a hard delete.
        """
        logger.debug(f"Attempting to delete {self._model_name} with ID: {item_id}")
        stmt = select(self.model).where(self.model.id == item_id) # type: ignore
        item_db = (await self.db_session.execute(stmt)).scalar_one_or_none()

        if not item_db:
            logger.warning(f"{self._model_name} with ID '{item_id}' not found for deletion.")
            return False

        try:
            await self.db_session.delete(item_db)
            await self.commit()
            logger.info(f"{self._model_name} with ID '{item_id}' (Code: {getattr(item_db, 'code', 'N/A')}) deleted successfully.")
            return True
        except IntegrityError as e: # Catch foreign key violations if item is in use
            await self.rollback() # Rollback the failed delete attempt
            logger.error(f"IntegrityError deleting {self._model_name} ID '{item_id}': {e}. It might be in use.", exc_info=True)
            # Depending on policy, could raise a custom business logic error here.
            # e.g., raise CannotDeleteInUseError(f"{self._model_name} ID '{item_id}' is in use and cannot be deleted.")
            # For now, just returning False and logging.
            return False
        except Exception as e:
            await self.rollback()
            logger.error(f"Unexpected error deleting {self._model_name} ID '{item_id}': {e}", exc_info=True)
            raise


logger.info("BaseDictionaryService class defined successfully.")
