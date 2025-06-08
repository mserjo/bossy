# backend/app/src/repositories/base.py
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

# Assuming your SQLAlchemy models inherit from a base model that includes an 'id' attribute.
# Adjust the import path according to your project structure.
# Based on structure-claude-v2.md: backend/app/src/models/base.py
from app.src.models.base import BaseModel as DBBaseModel


ModelType = TypeVar("ModelType", bound=DBBaseModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Generic base class for data repositories.

    This class provides common CRUD (Create, Read, Update, Delete) operations
    for SQLAlchemy models. It is designed to be inherited by specific
    repository classes for each model.

    Attributes:
        model (Type[ModelType]): The SQLAlchemy model type that this
                                 repository handles.
    """

    def __init__(self, model: Type[ModelType]):
        """
        Initializes the BaseRepository.

        Args:
            model: The SQLAlchemy model type.
        """
        self.model = model

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> ModelType:
        """
        Creates a new record in the database.

        Args:
            db: The SQLAlchemy asynchronous database session.
            obj_in: The Pydantic schema containing the data for the new record.

        Returns:
            The newly created SQLAlchemy model instance.
        """
        # Convert Pydantic model to dictionary
        obj_in_data = jsonable_encoder(obj_in)
        # Create SQLAlchemy model instance
        db_obj = self.model(**obj_in_data)  # type: ignore[call-arg]
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        """
        Retrieves a single record by its ID.

        Args:
            db: The SQLAlchemy asynchronous database session.
            id: The ID of the record to retrieve.

        Returns:
            The SQLAlchemy model instance if found, otherwise None.
        """
        statement = select(self.model).where(self.model.id == id)
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """
        Retrieves multiple records with optional pagination.

        Args:
            db: The SQLAlchemy asynchronous database session.
            skip: The number of records to skip (for pagination). Defaults to 0.
            limit: The maximum number of records to return (for pagination). Defaults to 100.

        Returns:
            A list of SQLAlchemy model instances.
        """
        statement = select(self.model).offset(skip).limit(limit)
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        Updates an existing record in the database.

        Args:
            db: The SQLAlchemy asynchronous database session.
            db_obj: The SQLAlchemy model instance to update.
            obj_in: The Pydantic schema or dictionary containing the data
                    to update. Unset fields in Pydantic schema are ignored.

        Returns:
            The updated SQLAlchemy model instance.
        """
        obj_data = jsonable_encoder(db_obj) # Current state of the db_obj
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            # For Pydantic models, model_dump(exclude_unset=True) ensures
            # that only fields explicitly set in obj_in are used for update.
            update_data = obj_in.model_dump(exclude_unset=True)

        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])

        db.add(db_obj) # Add the modified object to the session
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def remove(self, db: AsyncSession, *, id: Any) -> Optional[ModelType]:
        """
        Removes a record from the database by its ID.
        This performs a hard delete.

        Args:
            db: The SQLAlchemy asynchronous database session.
            id: The ID of the record to remove.

        Returns:
            The removed SQLAlchemy model instance if found and removed,
            otherwise None. If the object does not exist, returns None.
        """
        obj = await self.get(db, id=id)
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj

    async def get_by_attribute(
        self, db: AsyncSession, attribute_name: str, attribute_value: Any
    ) -> Optional[ModelType]:
        """
        Retrieves a single record by a specific attribute and its value.

        Args:
            db: The SQLAlchemy asynchronous database session.
            attribute_name: The name of the attribute (column) to filter by.
            attribute_value: The value of the attribute to filter by.

        Returns:
            The SQLAlchemy model instance if found, otherwise None.
        Raises:
            AttributeError: if the model does not have the specified attribute.
        """
        if not hasattr(self.model, attribute_name):
            raise AttributeError(
                f"Model {self.model.__name__} does not have attribute {attribute_name}"
            )
        statement = select(self.model).where(
            getattr(self.model, attribute_name) == attribute_value
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_multi_by_attribute(
        self,
        db: AsyncSession,
        attribute_name: str,
        attribute_value: Any,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ModelType]:
        """
        Retrieves multiple records by a specific attribute and its value
        with optional pagination.

        Args:
            db: The SQLAlchemy asynchronous database session.
            attribute_name: The name of the attribute (column) to filter by.
            attribute_value: The value of the attribute to filter by.
            skip: The number of records to skip (for pagination). Defaults to 0.
            limit: The maximum number of records to return (for pagination). Defaults to 100.

        Returns:
            A list of SQLAlchemy model instances.
        Raises:
            AttributeError: if the model does not have the specified attribute.
        """
        if not hasattr(self.model, attribute_name):
            raise AttributeError(
                f"Model {self.model.__name__} does not have attribute {attribute_name}"
            )
        statement = (
            select(self.model)
            .where(getattr(self.model, attribute_name) == attribute_value)
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def get_by_attributes(
        self, db: AsyncSession, attributes: Dict[str, Any], include_soft_deleted: bool = False
    ) -> Optional[ModelType]:
        """
        Retrieves a single record by multiple attributes and their values.

        Args:
            db: The SQLAlchemy asynchronous database session.
            attributes: A dictionary where keys are attribute names and
                        values are the attribute values to filter by.
            include_soft_deleted: If True, includes soft-deleted records in the search.
                                 Requires the model to have a 'deleted_at' attribute.
                                 Defaults to False.
        Returns:
            The SQLAlchemy model instance if found, otherwise None.
        Raises:
            AttributeError: if any of the specified attributes do not exist on the model.
        """
        conditions = []
        for attr, value in attributes.items():
            if not hasattr(self.model, attr):
                raise AttributeError(
                    f"Model {self.model.__name__} does not have attribute {attr}"
                )
            conditions.append(getattr(self.model, attr) == value)

        if not include_soft_deleted and hasattr(self.model, "deleted_at"):
            conditions.append(self.model.deleted_at.is_(None)) # type: ignore[attr-defined]

        statement = select(self.model).where(*conditions)
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_multi_by_attributes(
        self,
        db: AsyncSession,
        attributes: Dict[str, Any],
        *,
        skip: int = 0,
        limit: int = 100,
        include_soft_deleted: bool = False
    ) -> List[ModelType]:
        """
        Retrieves multiple records by multiple attributes and their values
        with optional pagination.

        Args:
            db: The SQLAlchemy asynchronous database session.
            attributes: A dictionary where keys are attribute names and
                        values are the attribute values to filter by.
            skip: The number of records to skip (for pagination). Defaults to 0.
            limit: The maximum number of records to return (for pagination). Defaults to 100.
            include_soft_deleted: If True, includes soft-deleted records in the search.
                                 Requires the model to have a 'deleted_at' attribute.
                                 Defaults to False.
        Returns:
            A list of SQLAlchemy model instances.
        Raises:
            AttributeError: if any of the specified attributes do not exist on the model.
        """
        conditions = []
        for attr, value in attributes.items():
            if not hasattr(self.model, attr):
                raise AttributeError(
                    f"Model {self.model.__name__} does not have attribute {attr}"
                )
            conditions.append(getattr(self.model, attr) == value)

        if not include_soft_deleted and hasattr(self.model, "deleted_at"):
            conditions.append(self.model.deleted_at.is_(None)) # type: ignore[attr-defined]

        statement = (
            select(self.model)
            .where(*conditions)
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())


    async def count(self, db: AsyncSession, attributes: Optional[Dict[str, Any]] = None, include_soft_deleted: bool = False) -> int:
        """
        Counts the total number of records for the model, optionally filtered by attributes.

        Args:
            db: The SQLAlchemy asynchronous database session.
            attributes: Optional dictionary of attributes to filter by.
            include_soft_deleted: If True and attributes are provided, includes soft-deleted records.
                                 If attributes are not provided, this flag determines if all records
                                 or only active ones are counted. Defaults to False.
        Returns:
            The total number of records matching the criteria.
        """
        conditions = []
        if attributes:
            for attr, value in attributes.items():
                if not hasattr(self.model, attr):
                    raise AttributeError(
                        f"Model {self.model.__name__} does not have attribute {attr}"
                    )
                conditions.append(getattr(self.model, attr) == value)

        if not include_soft_deleted and hasattr(self.model, "deleted_at"):
            conditions.append(self.model.deleted_at.is_(None)) # type: ignore[attr-defined]

        statement = select(func.count()).select_from(self.model)
        if conditions:
            statement = statement.where(*conditions)

        result = await db.execute(statement)
        count = result.scalar_one()
        return count if count is not None else 0


    async def soft_delete(self, db: AsyncSession, *, id: Any) -> Optional[ModelType]:
        """
        Marks a record as deleted by setting the 'deleted_at' attribute.
        This assumes the model has a 'deleted_at' field (SQLAlchemy Column).

        Args:
            db: The SQLAlchemy asynchronous database session.
            id: The ID of the record to soft delete.

        Returns:
            The SQLAlchemy model instance if found and soft-deleted,
            otherwise None.
        Raises:
            AttributeError: if the model does not have a 'deleted_at' attribute.
        """
        from datetime import datetime, timezone  # Import here for clarity or at module level

        if not hasattr(self.model, "deleted_at"):
            raise AttributeError(
                f"Model {self.model.__name__} does not have 'deleted_at' attribute for soft delete."
            )

        db_obj = await self.get(db, id=id) # Use get to ensure it exists first
        if db_obj:
            # Check if already soft-deleted (optional, depends on desired behavior)
            if getattr(db_obj, "deleted_at") is not None:
                # Already soft-deleted, return the object as is or handle as an error/noop
                return db_obj # Or raise an exception, or return None if it implies "not newly soft-deleted"

            setattr(db_obj, "deleted_at", datetime.now(timezone.utc))
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        return None

    async def get_active(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        """
        Retrieves a single record by its ID, ensuring it's not soft-deleted.
        Assumes the model has a 'deleted_at' field.

        Args:
            db: The SQLAlchemy asynchronous database session.
            id: The ID of the record to retrieve.

        Returns:
            The SQLAlchemy model instance if found and not soft-deleted,
            otherwise None.
        Raises:
            AttributeError: if the model does not have 'deleted_at' attribute.
        """
        if not hasattr(self.model, "deleted_at"):
            raise AttributeError(
                f"Model {self.model.__name__} does not have 'deleted_at' attribute."
            )

        statement = select(self.model).where(
            self.model.id == id,
            self.model.deleted_at.is_(None)  # type: ignore[attr-defined]
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_multi_active(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """
        Retrieves multiple records with optional pagination,
        excluding soft-deleted records.
        Assumes the model has a 'deleted_at' field.

        Args:
            db: The SQLAlchemy asynchronous database session.
            skip: The number of records to skip (for pagination). Defaults to 0.
            limit: The maximum number of records to return (for pagination). Defaults to 100.

        Returns:
            A list of SQLAlchemy model instances that are not soft-deleted.
        Raises:
            AttributeError: if the model does not have 'deleted_at' attribute.
        """
        if not hasattr(self.model, "deleted_at"):
            raise AttributeError(
                f"Model {self.model.__name__} does not have 'deleted_at' attribute."
            )

        statement = (
            select(self.model)
            .where(self.model.deleted_at.is_(None)) # type: ignore[attr-defined]
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def bulk_create(
        self, db: AsyncSession, *, objs_in: List[CreateSchemaType]
    ) -> List[ModelType]:
        """
        Creates multiple new records in the database in a single transaction
        using `db.add_all()`.

        Args:
            db: The SQLAlchemy asynchronous database session.
            objs_in: A list of Pydantic schemas containing the data for the
                     new records.

        Returns:
            A list of the newly created SQLAlchemy model instances.
            Note: Refreshing objects after bulk insert with `add_all` might require
                  individual refresh calls if primary keys are auto-generated by the DB
                  and not available until after commit. This implementation refreshes
                  them individually. For performance with very large lists, consider
                  alternative strategies if refresh is strictly needed immediately.
        """
        db_objs = [self.model(**jsonable_encoder(obj_in)) for obj_in in objs_in]
        db.add_all(db_objs)
        await db.commit()
        # Refresh each object to get DB-generated values (e.g., IDs, defaults)
        for db_obj in db_objs:
            await db.refresh(db_obj)
        return db_objs

    async def bulk_update_by_id(
        self, db: AsyncSession, *, updates: List[Dict[str, Any]]
    ) -> List[ModelType]:
        """
        Updates multiple records identified by 'id' in a list of dictionaries.
        Each dictionary must contain an 'id' key and other keys for fields to update.

        This method fetches each object, updates its fields, and commits once.
        For very large bulk updates, consider more optimized approaches if performance
        is critical, such as using `sqlalchemy.update()` statements per object or
        a more complex single update statement if applicable.

        Args:
            db: The SQLAlchemy asynchronous database session.
            updates: A list of dictionaries. Each dictionary must have an 'id'
                     key specifying the record to update, and other key-value
                     pairs for the fields to be updated.

        Returns:
            A list of the updated SQLAlchemy model instances.
        Raises:
            ValueError: if a dictionary in 'updates' does not contain an 'id' key.
        """
        updated_db_objs = []
        for update_data in updates:
            obj_id = update_data.get("id")
            if obj_id is None:
                raise ValueError("Each dictionary in 'updates' must contain an 'id' key.")

            db_obj = await self.get(db, id=obj_id)
            if db_obj:
                update_payload = {k: v for k, v in update_data.items() if k != "id"}
                for field, value in update_payload.items():
                    if hasattr(db_obj, field):
                        setattr(db_obj, field, value)
                    else:
                        # Optionally, raise an error or log a warning for non-existent fields
                        pass # Or: print(f"Warning: Field {field} not found on model {self.model.__name__}")
                db.add(db_obj) # Add to session to mark as dirty
                updated_db_objs.append(db_obj)
            else:
                # Optionally, handle cases where an ID is not found
                pass # Or: print(f"Warning: Object with ID {obj_id} not found for update.")

        if updated_db_objs: # Only commit if there are objects to update
            await db.commit()
            for db_obj in updated_db_objs: # Refresh after commit
                await db.refresh(db_obj)
        return updated_db_objs


    async def bulk_remove_by_ids(self, db: AsyncSession, *, ids: List[Any]) -> int:
        """
        Removes multiple records from the database by their IDs using a
        single delete statement. This performs a hard delete.

        Args:
            db: The SQLAlchemy asynchronous database session.
            ids: A list of IDs of the records to remove.

        Returns:
            The number of records successfully removed.
        """
        if not ids:
            return 0
        statement = delete(self.model).where(self.model.id.in_(ids))
        result = await db.execute(statement)
        await db.commit()
        return result.rowcount # type: ignore[no-any-return]

    async def soft_bulk_delete_by_ids(self, db: AsyncSession, *, ids: List[Any]) -> int:
        """
        Soft deletes multiple records by setting their 'deleted_at' attribute
        using a single update statement.
        Assumes the model has a 'deleted_at' field.

        Args:
            db: The SQLAlchemy asynchronous database session.
            ids: A list of IDs of the records to soft delete.

        Returns:
            The number of records successfully soft-deleted.
        Raises:
            AttributeError: if the model does not have 'deleted_at' attribute.
        """
        from datetime import datetime, timezone

        if not hasattr(self.model, "deleted_at"):
            raise AttributeError(
                f"Model {self.model.__name__} does not have 'deleted_at' attribute for soft delete."
            )
        if not ids:
            return 0

        statement = (
            update(self.model)
            .where(self.model.id.in_(ids))
            .where(self.model.deleted_at.is_(None))  # type: ignore[attr-defined] # Only soft-delete if not already deleted
            .values(deleted_at=datetime.now(timezone.utc))
            # synchronize_session='fetch' might be needed if session needs to be aware of changes
            # For soft delete, usually 'evaluate' or False is fine if not immediately querying from same session.
            .execution_options(synchronize_session=False)
        )
        result = await db.execute(statement)
        await db.commit()
        return result.rowcount # type: ignore[no-any-return]
