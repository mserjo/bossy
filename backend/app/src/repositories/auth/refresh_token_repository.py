# backend/app/src/repositories/auth/refresh_token_repository.py

"""
Repository for RefreshToken entities.
Provides CRUD operations and specific methods for managing refresh tokens.
"""

import logging
from typing import Optional, List, Any # Added Any for update schema if not specific
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from backend.app.src.models.auth.token import RefreshToken
from backend.app.src.schemas.auth.token import TokenPayload # Assuming RefreshTokenCreate schema might be similar to parts of TokenPayload or a new specific schema
# For creating a refresh token, we'd typically need user_id, jti, expires_at.
# Let's define a placeholder Create schema or use Dict for obj_in for now.
# A proper RefreshTokenCreate schema would be defined in schemas/auth/token.py.
from pydantic import BaseModel as PydanticBaseModel # For a placeholder schema

from backend.app.src.repositories.base import BaseRepository

logger = logging.getLogger(__name__)

# Placeholder Create/Update schemas for RefreshToken if not explicitly defined in schemas/auth/token.py
# Ideally, these would be defined in schemas.auth.token:
class RefreshTokenCreateSchema(PydanticBaseModel):
    user_id: int
    token_jti: str
    expires_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class RefreshTokenUpdateSchema(PydanticBaseModel):
    is_revoked: Optional[bool] = None
    # Potentially other fields if they are updatable, though usually only revocation status changes.


class RefreshTokenRepository(BaseRepository[RefreshToken, RefreshTokenCreateSchema, RefreshTokenUpdateSchema]):
    """
    Repository for managing RefreshToken records.
    """

    def __init__(self):
        super().__init__(RefreshToken)

    async def get_by_jti(self, db: AsyncSession, *, jti: str) -> Optional[RefreshToken]:
        """
        Retrieves a refresh token by its JTI (JWT ID).

        Args:
            db: The SQLAlchemy asynchronous database session.
            jti: The JTI of the refresh token.

        Returns:
            The RefreshToken object if found, otherwise None.
        """
        statement = select(self.model).where(self.model.token_jti == jti) # type: ignore[attr-defined]
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_all_by_user_id(self, db: AsyncSession, *, user_id: int, include_revoked: bool = False) -> List[RefreshToken]:
        """
        Retrieves all refresh tokens for a specific user.

        Args:
            db: The SQLAlchemy asynchronous database session.
            user_id: The ID of the user.
            include_revoked: Whether to include tokens that are already revoked.

        Returns:
            A list of RefreshToken objects.
        """
        conditions = [self.model.user_id == user_id] # type: ignore[attr-defined]
        if not include_revoked:
            conditions.append(self.model.is_revoked == False) # type: ignore[attr-defined]

        statement = select(self.model).where(*conditions).order_by(self.model.created_at.desc()) # type: ignore[attr-defined]
        result = await db.execute(statement)
        return list(result.scalars().all())

    async def revoke_token(self, db: AsyncSession, *, token_jti: str) -> Optional[RefreshToken]:
        """
        Marks a specific refresh token as revoked by its JTI.

        Args:
            db: The SQLAlchemy asynchronous database session.
            token_jti: The JTI of the token to revoke.

        Returns:
            The revoked RefreshToken object if found and updated, otherwise None.
        """
        db_obj = await self.get_by_jti(db, jti=token_jti)
        if db_obj and not db_obj.is_revoked: # type: ignore[union-attr]
            db_obj.is_revoked = True # type: ignore[union-attr]
            db_obj.updated_at = datetime.now(timezone.utc) # type: ignore[union-attr] # Manually update timestamp as super().update is not called directly for this field change
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        return None # Or return db_obj if already revoked

    async def revoke_all_for_user(self, db: AsyncSession, *, user_id: int) -> int:
        """
        Marks all active refresh tokens for a specific user as revoked.

        Args:
            db: The SQLAlchemy asynchronous database session.
            user_id: The ID of the user whose tokens are to be revoked.

        Returns:
            The number of tokens successfully revoked.
        """
        statement = (
            update(self.model)
            .where(self.model.user_id == user_id, self.model.is_revoked == False) # type: ignore[attr-defined]
            .values(is_revoked=True, updated_at=datetime.now(timezone.utc))
            .execution_options(synchronize_session=False) # Important for bulk updates
        )
        result = await db.execute(statement)
        await db.commit()
        return result.rowcount # type: ignore[no-any-return]

    async def delete_expired_tokens(self, db: AsyncSession) -> int:
        """
        Deletes refresh tokens that are expired (expires_at < now) or already revoked.

        Args:
            db: The SQLAlchemy asynchronous database session.

        Returns:
            The number of tokens successfully deleted.
        """
        now = datetime.now(timezone.utc)
        statement = delete(self.model).where(
            (self.model.expires_at < now) | (self.model.is_revoked == True) # type: ignore[attr-defined]
        )
        result = await db.execute(statement)
        await db.commit()
        return result.rowcount # type: ignore[no-any-return]

    # The base `create` method will use RefreshTokenCreateSchema.
    # The base `update` method (if ever used directly, e.g. by an admin) would use RefreshTokenUpdateSchema.
    # Most updates are handled by specific methods like `revoke_token`.
