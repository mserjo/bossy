# backend/app/src/services/auth/token.py
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List # Added List for scopes
from uuid import UUID, uuid4

from jose import JWTError, jwt # python-jose for JWT handling
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload # Added for process_refresh_token

from app.src.services.base import BaseService # For potential DB interaction (e.g. refresh token storage)
from app.src.config.settings import settings # To access JWT secret, algorithm, expiry times
from app.src.schemas.auth.token import TokenResponse, RefreshTokenCreate, RefreshTokenResponse # Pydantic schemas
from app.src.models.auth.token import RefreshToken # SQLAlchemy model for refresh tokens
from app.src.models.auth.user import User # To link refresh token to user
# from app.src.services.auth.user import UserService # Potential dependency, but avoid circular if possible

# Initialize logger for this module
logger = logging.getLogger(__name__)

class TokenService(BaseService): # Inherits BaseService for db_session if storing refresh tokens
    """
    Service for handling JWT (access and refresh) token generation, validation,
    and management of refresh tokens if stored in the database.
    """

    def __init__(self, db_session: AsyncSession): # db_session needed for refresh token DB operations
        super().__init__(db_session)
        logger.info("TokenService initialized.")

    def create_access_token(self, subject: str, # Typically user ID or username
                              expires_delta: Optional[timedelta] = None,
                              scopes: Optional[List[str]] = None, # For role/permission based access
                              additional_claims: Optional[Dict[str, Any]] = None
                             ) -> str:
        """
        Generates a new JWT access token.

        Args:
            subject (str): The subject of the token (e.g., user_id).
            expires_delta (Optional[timedelta]): Lifetime of the token. Defaults to ACCESS_TOKEN_EXPIRE_MINUTES.
            scopes (Optional[List[str]]): List of scopes (permissions/roles) for the token.
            additional_claims (Optional[Dict[str, Any]]): Any other custom claims to include.

        Returns:
            str: The encoded JWT access token.
        """
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode: Dict[str, Any] = {"exp": expire, "sub": str(subject), "type": "access"}
        if scopes:
            to_encode["scopes"] = scopes
        if additional_claims:
            to_encode.update(additional_claims)

        # Add 'jti' (JWT ID) claim for unique token identification, useful for revocation lists
        to_encode["jti"] = str(uuid4())

        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        logger.info(f"Access token created for subject '{subject}' with JTI '{to_encode['jti']}'. Expires at {expire.isoformat()}")
        return encoded_jwt

    async def create_refresh_token(
        self,
        user_id: UUID,
        expires_delta: Optional[timedelta] = None,
        device_info: Optional[str] = None # Optional: for tracking device associated with refresh token
    ) -> str:
        """
        Generates a new refresh token and stores its record in the database.

        Args:
            user_id (UUID): The user ID for whom the refresh token is created.
            expires_delta (Optional[timedelta]): Lifetime of the refresh token. Defaults to REFRESH_TOKEN_EXPIRE_DAYS.
            device_info (Optional[str]): Information about the device using the refresh token.

        Returns:
            str: The refresh token string (this is the JTI, not a JWT itself for refresh usually).
                 The actual JWT refresh token can also be generated if preferred.
                 Here, we'll use a simple UUID as the refresh token value and store its metadata.
        """
        if expires_delta:
            expire_at = datetime.now(timezone.utc) + expires_delta
        else:
            expire_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        # Generate a unique JTI (JWT ID) for this refresh token. This JTI will be the actual refresh token value.
        jti = uuid4()

        # Check if user exists (optional, but good practice if user_id is passed directly)
        user_db = await self.db_session.get(User, user_id)
        if not user_db:
            logger.error(f"User with ID '{user_id}' not found. Cannot create refresh token.")
            raise ValueError(f"User with ID '{user_id}' not found.")

        refresh_token_db = RefreshToken(
            jti=jti,
            user_id=user_id,
            expires_at=expire_at,
            is_revoked=False,
            device_info=device_info
        )

        self.db_session.add(refresh_token_db)
        await self.commit() # Commit to save the refresh token record
        # await self.db_session.refresh(refresh_token_db) # Not strictly needed if not returning its DB fields

        logger.info(f"Refresh token (JTI: {jti}) created for user ID '{user_id}'. Expires at {expire_at.isoformat()}")
        return str(jti) # Return the JTI string as the refresh token


    async def validate_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validates an access token.

        Args:
            token (str): The JWT access token to validate.

        Returns:
            Optional[Dict[str, Any]]: The decoded token payload if valid, otherwise None.
        """
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

            # Check token type
            if payload.get("type") != "access":
                logger.warning("Invalid token type provided for access token validation.")
                return None # Or raise specific error

            # Check expiration (already handled by jwt.decode, but explicit check can be added if needed)
            # exp = payload.get("exp")
            # if exp and datetime.fromtimestamp(exp, timezone.utc) < datetime.now(timezone.utc):
            # logger.warning(f"Access token has expired. JTI: {payload.get('jti')}")
            # return None # Or raise specific error: raise credentials_exception ("Token has expired")

            # Check if token is on a denylist (if implemented)
            # jti = payload.get("jti")
            # if jti and await self.is_token_denylisted(jti):
            #     logger.warning(f"Access token JTI '{jti}' is denylisted.")
            #     return None # Or raise

            logger.info(f"Access token validated successfully. Subject: {payload.get('sub')}, JTI: {payload.get('jti')}")
            return payload
        except JWTError as e:
            logger.warning(f"Access token validation failed: {e}", exc_info=True)
            return None # Or raise specific error like credentials_exception(f"Invalid token: {e}")

    async def process_refresh_token(self, refresh_token_jti: str) -> Optional[User]:
        """
        Processes a refresh token (JTI string).
        Validates it against the database, checks expiry and revocation.
        If valid, it marks the old token as used (or revokes it) and can issue new tokens.
        This method primarily validates and returns the associated User model.
        New token issuance should be handled by the calling logic (e.g., in an API endpoint).

        Args:
            refresh_token_jti (str): The JTI string of the refresh token.

        Returns:
            Optional[User]: The User object associated with the valid refresh token, otherwise None.
        """
        try:
            jti_uuid = UUID(refresh_token_jti) # Ensure it's a valid UUID
        except ValueError:
            logger.warning(f"Invalid JTI format for refresh token: {refresh_token_jti}")
            return None

        stmt = select(RefreshToken).options(selectinload(RefreshToken.user)).where(RefreshToken.jti == jti_uuid)
        result = await self.db_session.execute(stmt)
        token_db = result.scalar_one_or_none()

        if not token_db:
            logger.warning(f"Refresh token JTI '{refresh_token_jti}' not found in database.")
            return None

        if token_db.is_revoked:
            logger.warning(f"Refresh token JTI '{refresh_token_jti}' has been revoked.")
            # Potentially implement logic to revoke all tokens for this user if a revoked token is used.
            return None

        if token_db.expires_at < datetime.now(timezone.utc):
            logger.warning(f"Refresh token JTI '{refresh_token_jti}' has expired at {token_db.expires_at.isoformat()}.")
            # Optionally, clean up expired tokens here or via a background task
            # await self.db_session.delete(token_db)
            # await self.commit()
            return None

        # Refresh token is valid.
        # Standard practice: Revoke this refresh token to prevent reuse (one-time use).
        # A new refresh token should be issued along with a new access token.
        token_db.is_revoked = True
        self.db_session.add(token_db)
        await self.commit() # Commit revocation of this token

        logger.info(f"Refresh token JTI '{refresh_token_jti}' processed successfully for user ID '{token_db.user_id}'. Token has been revoked.")
        return token_db.user # Return the associated user object

    async def revoke_refresh_token(self, refresh_token_jti: str, user_id: Optional[UUID] = None) -> bool:
        """
        Revokes a specific refresh token.
        If user_id is provided, it also verifies that the token belongs to the user.
        """
        logger.debug(f"Attempting to revoke refresh token JTI: {refresh_token_jti} for user: {user_id if user_id else 'any'}")
        try:
            jti_uuid = UUID(refresh_token_jti)
        except ValueError:
            logger.warning(f"Invalid JTI format for revocation: {refresh_token_jti}")
            return False

        stmt = select(RefreshToken).where(RefreshToken.jti == jti_uuid)
        if user_id:
            stmt = stmt.where(RefreshToken.user_id == user_id)

        token_db = (await self.db_session.execute(stmt)).scalar_one_or_none()

        if not token_db:
            logger.warning(f"Refresh token JTI '{refresh_token_jti}' not found or does not belong to user '{user_id}'.")
            return False

        if token_db.is_revoked:
            logger.info(f"Refresh token JTI '{refresh_token_jti}' was already revoked.")
            return True # Already revoked, consider it a success

        token_db.is_revoked = True
        self.db_session.add(token_db)
        await self.commit()
        logger.info(f"Refresh token JTI '{refresh_token_jti}' successfully revoked for user ID '{token_db.user_id}'.")
        return True

    async def revoke_all_refresh_tokens_for_user(self, user_id: UUID) -> int:
        """
        Revokes all active refresh tokens for a given user.
        Useful for "log out all devices" functionality or security events.
        """
        logger.info(f"Attempting to revoke all refresh tokens for user ID: {user_id}")
        stmt = select(RefreshToken).where(RefreshToken.user_id == user_id, RefreshToken.is_revoked == False)
        tokens_to_revoke_db = (await self.db_session.execute(stmt)).scalars().all()

        if not tokens_to_revoke_db:
            logger.info(f"No active refresh tokens found for user ID '{user_id}' to revoke.")
            return 0

        for token_db in tokens_to_revoke_db:
            token_db.is_revoked = True
            self.db_session.add(token_db)

        await self.commit()
        count = len(tokens_to_revoke_db)
        logger.info(f"Successfully revoked {count} refresh tokens for user ID '{user_id}'.")
        return count

    # Optional: Method to manage JWT denylist (if storing JTI of logged-out access tokens)
    # async def is_token_denylisted(self, jti: str) -> bool: ...
    # async def add_token_to_denylist(self, jti: str, expires_at: datetime) -> None: ...

logger.info("TokenService class defined.")
