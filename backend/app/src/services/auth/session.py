# backend/app/src/services/auth/session.py
import logging
from typing import List, Optional
from uuid import UUID, uuid4 # uuid4 was used but not imported
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload # Added for get_session_by_token

from app.src.services.base import BaseService
from app.src.models.auth.session import UserSession # SQLAlchemy model
from app.src.models.auth.user import User # For linking session to user
# from app.src.schemas.auth.session import UserSessionResponse, UserSessionCreate # Pydantic Schemas (if defined)
# Structure doc v2 doesn't explicitly list UserSession schemas, so we'll assume basic operations for now
# or that responses might directly use model data or a generic dict.
# For a more complete implementation, Pydantic schemas would be beneficial.

# Initialize logger for this module
logger = logging.getLogger(__name__)

# Default session duration if not specified (e.g., for "remember me")
DEFAULT_SESSION_DURATION_DAYS = 30

class UserSessionService(BaseService):
    """
    Service for managing user sessions, if a stateful session mechanism is employed.
    This can be used for features like "remember me", tracking active devices/sessions,
    and server-side session revocation, complementing stateless JWTs.

    If the primary authentication mechanism is purely stateless JWTs without database-backed
    refresh tokens that also serve as session identifiers, this service might be minimal
    or not used. However, `structure-claude-v2.md` lists `models/auth/session.py`,
    implying some form of server-side session tracking.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        logger.info("UserSessionService initialized.")

    async def create_session(
        self,
        user_id: UUID,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        duration_days: int = DEFAULT_SESSION_DURATION_DAYS
    ) -> UserSession: # Returning the ORM model for now, or a UserSessionResponse if defined
        """
        Creates a new user session and stores it in the database.

        Args:
            user_id (UUID): The ID of the user for whom the session is created.
            user_agent (Optional[str]): User agent string of the client.
            ip_address (Optional[str]): IP address of the client.
            duration_days (int): Duration of the session in days.

        Returns:
            UserSession: The created UserSession ORM object.
        """
        logger.debug(f"Creating new session for user ID: {user_id}")

        # Check if user exists
        user = await self.db_session.get(User, user_id)
        if not user:
            logger.error(f"User with ID '{user_id}' not found. Cannot create session.")
            raise ValueError(f"User with ID '{user_id}' not found.")

        session_token = uuid4() # Generate a unique session token (UUID object)
        expires_at = datetime.now(timezone.utc) + timedelta(days=duration_days)

        new_session_db = UserSession(
            session_token=session_token, # This is the actual token client might store
            user_id=user_id,
            user_agent=user_agent,
            ip_address=ip_address,
            expires_at=expires_at,
            last_active_at=datetime.now(timezone.utc)
        )

        self.db_session.add(new_session_db)
        await self.commit()
        await self.db_session.refresh(new_session_db)

        logger.info(f"Session created successfully for user ID '{user_id}' with session token (UUID): {new_session_db.session_token}")
        # If UserSessionResponse schema exists:
        # return UserSessionResponse.model_validate(new_session_db) # Pydantic v2
        # return UserSessionResponse.from_orm(new_session_db) # Pydantic v1
        return new_session_db # Return ORM model

    async def get_session_by_token(self, session_token: UUID) -> Optional[UserSession]: # Or UserSessionResponse
        """
        Retrieves a user session by its session token.
        Checks for expiry and validity.
        Updates last_active_at if session is valid and accessed.
        """
        logger.debug(f"Attempting to retrieve session by token: {session_token}")

        stmt = select(UserSession).options(selectinload(UserSession.user)).where(UserSession.session_token == session_token)
        result = await self.db_session.execute(stmt)
        session_db = result.scalar_one_or_none()

        if not session_db:
            logger.warning(f"Session with token '{session_token}' not found.")
            return None

        if session_db.expires_at < datetime.now(timezone.utc):
            logger.info(f"Session token '{session_token}' for user ID '{session_db.user_id}' has expired at {session_db.expires_at.isoformat()}. Deleting.")
            await self.db_session.delete(session_db) # Clean up expired session
            await self.commit()
            return None

        # Session is valid, update last_active_at
        session_db.last_active_at = datetime.now(timezone.utc)
        self.db_session.add(session_db)
        await self.commit() # Commit the update to last_active_at
        # await self.db_session.refresh(session_db) # Refresh if needed for response

        logger.info(f"Session token '{session_token}' validated for user ID '{session_db.user_id}'. Last active updated.")
        # If UserSessionResponse schema exists:
        # return UserSessionResponse.model_validate(session_db) # Pydantic v2
        # return UserSessionResponse.from_orm(session_db) # Pydantic v1
        return session_db

    async def invalidate_session(self, session_token: UUID, user_id: Optional[UUID] = None) -> bool:
        """
        Invalidates/deletes a specific user session by its token.
        If user_id is provided, it ensures the session belongs to that user.

        Args:
            session_token (UUID): The session token to invalidate.
            user_id (Optional[UUID]): If provided, verify session belongs to this user.

        Returns:
            bool: True if session was found and invalidated, False otherwise.
        """
        logger.debug(f"Attempting to invalidate session token: {session_token} for user: {user_id or 'any'}")

        stmt = select(UserSession).where(UserSession.session_token == session_token)
        if user_id:
            stmt = stmt.where(UserSession.user_id == user_id)

        session_db = (await self.db_session.execute(stmt)).scalar_one_or_none()

        if not session_db:
            logger.warning(f"Session token '{session_token}' not found or does not belong to user '{user_id}'. Cannot invalidate.")
            return False

        await self.db_session.delete(session_db)
        await self.commit()
        logger.info(f"Session token '{session_token}' for user ID '{session_db.user_id}' invalidated (deleted) successfully.")
        return True

    async def list_user_sessions(self, user_id: UUID, skip: int = 0, limit: int = 10) -> List[UserSession]: # Or List[UserSessionResponse]
        """
        Lists all active (non-expired) sessions for a given user.

        Args:
            user_id (UUID): The ID of the user.
            skip (int): Number of sessions to skip for pagination.
            limit (int): Maximum number of sessions to return.

        Returns:
            List[UserSession]: A list of active UserSession ORM objects.
        """
        logger.debug(f"Listing active sessions for user ID: {user_id}, skip={skip}, limit={limit}")

        now = datetime.now(timezone.utc)
        stmt = select(UserSession).where(
            UserSession.user_id == user_id,
            UserSession.expires_at > now # Only active sessions
        ).order_by(UserSession.last_active_at.desc()).offset(skip).limit(limit)

        result = await self.db_session.execute(stmt)
        sessions_db = result.scalars().all()

        # If UserSessionResponse schema exists:
        # response_list = [UserSessionResponse.from_orm(s) for s in sessions_db] # Pydantic v1
        # logger.info(f"Retrieved {len(response_list)} active sessions for user ID '{user_id}'.")
        # return response_list
        logger.info(f"Retrieved {len(sessions_db)} active sessions for user ID '{user_id}'.")
        return sessions_db

    async def invalidate_all_user_sessions(self, user_id: UUID, exclude_session_token: Optional[UUID] = None) -> int:
        """
        Invalidates/deletes all sessions for a given user, optionally excluding one session token.
        Useful for "log out all other devices".

        Args:
            user_id (UUID): The ID of the user whose sessions to invalidate.
            exclude_session_token (Optional[UUID]): A session token to keep active (e.g., the current one).

        Returns:
            int: The number of sessions invalidated.
        """
        logger.info(f"Invalidating all sessions for user ID: {user_id}, excluding token: {exclude_session_token}")

        stmt = select(UserSession).where(UserSession.user_id == user_id)
        if exclude_session_token:
            stmt = stmt.where(UserSession.session_token != exclude_session_token)

        sessions_to_delete_db = (await self.db_session.execute(stmt)).scalars().all()

        if not sessions_to_delete_db:
            logger.info(f"No sessions found to invalidate for user ID '{user_id}' (excluding: {exclude_session_token}).")
            return 0

        count = 0
        for session_db in sessions_to_delete_db:
            await self.db_session.delete(session_db)
            count +=1 # Increment count for each deletion attempt that will be committed

        if count > 0: # Only commit if there's something to delete
            await self.commit()
        logger.info(f"Successfully invalidated {count} sessions for user ID '{user_id}'.")
        return count

    async def cleanup_expired_sessions(self) -> int:
        """
        Deletes all expired sessions from the database.
        This is a maintenance task, could be run periodically by a background job.
        """
        logger.info("Cleaning up expired user sessions...")
        now = datetime.now(timezone.utc)

        # Select IDs of expired sessions to count them accurately before deletion
        select_expired_stmt = select(UserSession.id).where(UserSession.expires_at < now)
        expired_ids_result = await self.db_session.execute(select_expired_stmt)
        expired_ids = [row[0] for row in expired_ids_result.fetchall()]

        count = 0
        if expired_ids:
            # Now delete them
            delete_stmt = UserSession.__table__.delete().where(UserSession.id.in_(expired_ids))
            # For some databases, execute might return a rowcount, but it's not always reliable
            # for bulk deletes with conditions across all SQLAlchemy supported DBs.
            # Re-fetching count from selected IDs is more robust.
            await self.db_session.execute(delete_stmt)
            await self.commit()
            count = len(expired_ids)
            logger.info(f"Successfully cleaned up {count} expired user sessions.")
        else:
            logger.info("No expired user sessions found to clean up.")
        return count

logger.info("UserSessionService class defined.")
