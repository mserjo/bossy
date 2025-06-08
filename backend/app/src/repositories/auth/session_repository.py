# backend/app/src/repositories/auth/session_repository.py

"""
Repository for UserSession entities.
Provides CRUD operations and specific methods for managing user sessions.
"""

import logging
from typing import Optional, List, Any # Added Any
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from backend.app.src.models.auth.session import UserSession
# Assuming UserSessionCreate and UserSessionUpdate schemas would be defined if needed.
# For now, using PydanticBaseModel as placeholders if direct manipulation is complex.
# Often, session creation is implicit with login, and updates are minimal (e.g., last_activity_at).
from pydantic import BaseModel as PydanticBaseModel # For placeholder schemas

from backend.app.src.repositories.base import BaseRepository

logger = logging.getLogger(__name__)

# Placeholder Create/Update schemas for UserSession if not explicitly defined in schemas/auth/session.py
# A UserSessionCreate schema would typically be used by the system internally when a session starts.
class UserSessionCreateSchema(PydanticBaseModel):
    user_id: int
    session_id_hash: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    last_activity_at: datetime
    expires_at: datetime

class UserSessionUpdateSchema(PydanticBaseModel): # For updating things like last_activity_at
    last_activity_at: Optional[datetime] = None
    # Other fields like expires_at could be updatable if session extension is allowed.


class UserSessionRepository(BaseRepository[UserSession, UserSessionCreateSchema, UserSessionUpdateSchema]):
    """
    Repository for managing UserSession records.
    """

    def __init__(self):
        super().__init__(UserSession)

    async def get_by_session_id_hash(self, db: AsyncSession, *, session_id_hash: str) -> Optional[UserSession]:
        """
        Retrieves a user session by its hashed session ID.

        Args:
            db: The SQLAlchemy asynchronous database session.
            session_id_hash: The hashed session ID.

        Returns:
            The UserSession object if found, otherwise None.
        """
        statement = select(self.model).where(self.model.session_id_hash == session_id_hash) # type: ignore[attr-defined]
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_all_for_user(
        self, db: AsyncSession, *, user_id: int, include_expired: bool = False, newest_first: bool = True
    ) -> List[UserSession]:
        """
        Retrieves all sessions for a specific user.

        Args:
            db: The SQLAlchemy asynchronous database session.
            user_id: The ID of the user.
            include_expired: Whether to include sessions that have already expired.
            newest_first: Order by last_activity_at descending if True.

        Returns:
            A list of UserSession objects.
        """
        conditions = [self.model.user_id == user_id] # type: ignore[attr-defined]
        if not include_expired:
            conditions.append(self.model.expires_at > datetime.now(timezone.utc)) # type: ignore[attr-defined]

        statement = select(self.model).where(*conditions)
        if newest_first:
            statement = statement.order_by(self.model.last_activity_at.desc()) # type: ignore[attr-defined]
        else:
            statement = statement.order_by(self.model.last_activity_at.asc()) # type: ignore[attr-defined]

        result = await db.execute(statement)
        return list(result.scalars().all())

    async def delete_session(self, db: AsyncSession, *, session_id_hash: str) -> Optional[UserSession]:
        """
        Deletes a specific user session by its hashed session ID.
        This is equivalent to `remove` if an object is first fetched.

        Args:
            db: The SQLAlchemy asynchronous database session.
            session_id_hash: The hashed session ID of the session to delete.

        Returns:
            The deleted UserSession object if found and deleted, otherwise None.
        """
        db_obj = await self.get_by_session_id_hash(db, session_id_hash=session_id_hash)
        if db_obj:
            await db.delete(db_obj)
            await db.commit()
            return db_obj
        return None

    async def delete_all_for_user(
        self, db: AsyncSession, *, user_id: int, exclude_session_id_hash: Optional[str] = None
    ) -> int:
        """
        Deletes all sessions for a specific user, with an option to exclude one (e.g., the current session).

        Args:
            db: The SQLAlchemy asynchronous database session.
            user_id: The ID of the user whose sessions are to be deleted.
            exclude_session_id_hash: Optional. If provided, sessions with this
                                     hashed ID will not be deleted.
        Returns:
            The number of sessions successfully deleted.
        """
        conditions = [self.model.user_id == user_id] # type: ignore[attr-defined]
        if exclude_session_id_hash:
            conditions.append(self.model.session_id_hash != exclude_session_id_hash) # type: ignore[attr-defined]

        statement = delete(self.model).where(*conditions).execution_options(synchronize_session=False)
        result = await db.execute(statement)
        await db.commit()
        return result.rowcount # type: ignore[no-any-return]

    async def delete_expired_sessions(self, db: AsyncSession) -> int:
        """
        Deletes all user sessions that have passed their 'expires_at' timestamp.

        Args:
            db: The SQLAlchemy asynchronous database session.

        Returns:
            The number of expired sessions successfully deleted.
        """
        now = datetime.now(timezone.utc)
        statement = delete(self.model).where(self.model.expires_at < now).execution_options(synchronize_session=False) # type: ignore[attr-defined]
        result = await db.execute(statement)
        await db.commit()
        return result.rowcount # type: ignore[no-any-return]

    async def update_last_activity(self, db: AsyncSession, *, session_id_hash: str) -> Optional[UserSession]:
        """
        Updates the last_activity_at timestamp for a given session.

        Args:
            db: The SQLAlchemy asynchronous database session.
            session_id_hash: The hashed session ID.

        Returns:
            The updated UserSession object if found, otherwise None.
        """
        db_obj = await self.get_by_session_id_hash(db, session_id_hash=session_id_hash)
        if db_obj:
            db_obj.last_activity_at = datetime.now(timezone.utc) # type: ignore[union-attr]
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        return None
