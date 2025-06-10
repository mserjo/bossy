# backend/app/src/services/auth/password.py
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID, uuid4
import secrets # For generating secure random tokens

from sqlalchemy.ext.asyncio import AsyncSession # Needed if interacting with User model directly
from sqlalchemy.future import select
from sqlalchemy.dialects.postgresql import insert as pg_insert # For potential upsert logic if needed

from app.src.services.base import BaseService # For db_session if needed for token storage or user updates
from app.src.models.auth.user import User # To update user's password
from app.src.models.auth.password_reset_token import PasswordResetToken # SQLAlchemy model for reset tokens
from app.src.core.security import get_password_hash, verify_password # Core password utilities
# from app.src.services.auth.user import UserService # Avoid direct import if possible to prevent circularity
# from app.src.config.settings import settings # For token expiry times if configured globally

# Initialize logger for this module
logger = logging.getLogger(__name__)

# Configuration for password reset token expiry (can be moved to settings.py)
PASSWORD_RESET_TOKEN_EXPIRE_HOURS = 1

class PasswordService(BaseService): # Inherits BaseService for db_session
    """
    Service for handling password-related operations such as hashing, verification,
    and password reset token management.
    """

    def __init__(self, db_session: AsyncSession): # db_session for PasswordResetToken model
        super().__init__(db_session)
        logger.info("PasswordService initialized.")

    def get_hashed_password(self, password: str) -> str:
        """Hashes a plain password using the configured algorithm."""
        hashed_password = get_password_hash(password)
        logger.info("Password hashed successfully.")
        return hashed_password

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verifies a plain password against a hashed password."""
        is_valid = verify_password(plain_password, hashed_password)
        if is_valid:
            logger.info("Password verification successful.")
        else:
            logger.warning("Password verification failed.")
        return is_valid

    async def create_password_reset_token(self, user_id: UUID) -> str:
        """
        Generates a secure password reset token, stores its hash, and returns the plain token.
        The plain token is for sending to the user (e.g., via email) and should be short-lived.
        The hash is stored in the database to verify the token later.
        """
        # Check if user exists
        user = await self.db_session.get(User, user_id)
        if not user:
            logger.error(f"User with ID '{user_id}' not found. Cannot create password reset token.")
            raise ValueError(f"User with ID '{user_id}' not found.")

        # Invalidate any existing, non-expired, non-used tokens for this user
        # This is good practice to ensure only the latest token is valid.
        update_stmt = (
            PasswordResetToken.__table__.update()
            .where(
                PasswordResetToken.user_id == user_id,
                PasswordResetToken.expires_at > datetime.now(timezone.utc),
                PasswordResetToken.is_used == False
            )
            .values(is_used=True, used_at=datetime.now(timezone.utc)) # Mark as used instead of deleting
        )
        await self.db_session.execute(update_stmt)
        logger.info(f"Existing active password reset tokens for user ID '{user_id}' marked as used.")
        # No commit here yet, will be part of the transaction for creating the new token.

        plain_token = secrets.token_urlsafe(32) # Generate a secure, URL-safe plain token
        hashed_token = get_password_hash(plain_token) # Hash the plain token for DB storage

        expires_at = datetime.now(timezone.utc) + timedelta(hours=PASSWORD_RESET_TOKEN_EXPIRE_HOURS)

        reset_token_db = PasswordResetToken(
            user_id=user_id,
            token_hash=hashed_token,
            expires_at=expires_at,
            is_used=False
        )

        self.db_session.add(reset_token_db)
        await self.commit() # Commit both invalidation of old tokens and creation of new one

        logger.info(f"Password reset token created for user ID '{user_id}'. Plain token (first 8 chars for log): {plain_token[:8]}...")
        return plain_token # Return the plain token to be sent to the user

    async def _get_valid_reset_token_db(self, plain_token: str, user_id: UUID) -> Optional[PasswordResetToken]:
        """
        Internal helper: Finds a non-expired, non-used password reset token record
        by matching the hash of the plain_token for a specific user.
        """
        # Iterate through tokens for the user to find a match for the plain_token's hash.
        # This is necessary because we only store hashes.
        # To optimize, we could add a selector (first few chars of hash) if many tokens per user are expected.

        stmt = select(PasswordResetToken).where(
            PasswordResetToken.user_id == user_id,
            PasswordResetToken.is_used == False,
            PasswordResetToken.expires_at > datetime.now(timezone.utc)
        ).order_by(PasswordResetToken.created_at.desc()) # Check newest first

        potential_tokens_db = (await self.db_session.execute(stmt)).scalars().all()

        for token_db in potential_tokens_db:
            if verify_password(plain_token, token_db.token_hash):
                return token_db
        return None


    async def validate_password_reset_token(self, plain_token: str, user_id: UUID) -> bool:
        """
        Validates a plain password reset token for a user.
        Checks if it matches a stored hash, is not expired, and not already used.
        """
        logger.debug(f"Validating password reset token for user ID '{user_id}'. Token (first 8 chars): {plain_token[:8]}...")

        token_db = await self._get_valid_reset_token_db(plain_token, user_id)

        if token_db:
            logger.info(f"Password reset token for user ID '{user_id}' is valid.")
            return True

        logger.warning(f"Password reset token for user ID '{user_id}' is invalid, expired, used, or not found.")
        return False

    async def reset_password_with_token(self, plain_token: str, user_id: UUID, new_password: str) -> bool:
        """
        Resets a user's password using a valid plain reset token.
        The token must be valid (not expired, not used).
        Marks the token as used after successful password reset.
        """
        logger.info(f"Attempting to reset password for user ID '{user_id}' using token (first 8 chars): {plain_token[:8]}...")

        token_db = await self._get_valid_reset_token_db(plain_token, user_id)
        if not token_db:
            logger.warning(f"Invalid, expired, or used password reset token provided for user ID '{user_id}'. Password not reset.")
            return False # Or raise an error

        # Token is valid, proceed to fetch user and update password
        user_db = await self.db_session.get(User, user_id) # User should exist if token was created for them
        if not user_db:
            # This case should be rare if token validation implies user existence.
            logger.error(f"User with ID '{user_id}' not found during password reset, though a valid token existed. Inconsistency detected.")
            # Mark token as used anyway to prevent reuse with a now-orphaned token
            token_db.is_used = True
            token_db.used_at = datetime.now(timezone.utc)
            self.db_session.add(token_db)
            await self.commit()
            return False # Or raise

        # Update user's password
        user_db.hashed_password = self.get_hashed_password(new_password)
        # Optionally, update a 'password_last_changed_at' field on the User model
        # user_db.password_last_changed_at = datetime.now(timezone.utc)

        # Mark the reset token as used
        token_db.is_used = True
        token_db.used_at = datetime.now(timezone.utc)

        self.db_session.add(user_db)
        self.db_session.add(token_db)

        try:
            await self.commit()
            logger.info(f"Password for user ID '{user_id}' successfully reset and token marked as used.")

            # Optional: After successful password reset, one might want to invalidate all active refresh tokens
            # for this user to log them out of other sessions. This would require TokenService.
            # from app.src.services.auth.token import TokenService # Local import to avoid circularity at module level
            # token_service = TokenService(self.db_session)
            # await token_service.revoke_all_refresh_tokens_for_user(user_id)
            # logger.info(f"All refresh tokens for user ID '{user_id}' revoked after password reset.")

            return True
        except Exception as e:
            await self.rollback()
            logger.error(f"Error during password reset commit for user ID '{user_id}': {e}", exc_info=True)
            # Do not mark token as used if commit fails, so user can retry with same token (if still valid)
            return False # Or re-raise

    async def change_password(self, user_id: UUID, old_password: str, new_password: str) -> bool:
        """
        Allows an authenticated user to change their current password.
        Requires provision of the old password for verification.
        """
        logger.info(f"User ID '{user_id}' attempting to change password.")
        user_db = await self.db_session.get(User, user_id)
        if not user_db:
            logger.warning(f"User ID '{user_id}' not found for password change.")
            return False # Or raise error

        if not self.verify_password(old_password, user_db.hashed_password):
            logger.warning(f"Old password verification failed for user ID '{user_id}'.")
            return False # Or raise error indicating incorrect old password

        if old_password == new_password:
            logger.warning(f"User ID '{user_id}': New password is the same as the old password. No change made.")
            # Depending on policy, this could be an error or a silent success.
            # For now, let's treat it as "no change needed", so effectively success.
            return True


        user_db.hashed_password = self.get_hashed_password(new_password)
        # user_db.password_last_changed_at = datetime.now(timezone.utc) # Update timestamp

        self.db_session.add(user_db)
        await self.commit()

        logger.info(f"Password successfully changed for user ID '{user_id}'.")
        # Optional: Invalidate refresh tokens for security
        # from app.src.services.auth.token import TokenService # Local import
        # token_service = TokenService(self.db_session)
        # await token_service.revoke_all_refresh_tokens_for_user(user_id)
        # logger.info(f"All refresh tokens for user ID '{user_id}' revoked after password change.")
        return True

logger.info("PasswordService class defined.")
