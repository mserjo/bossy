# backend/app/src/models/auth/token.py

"""
SQLAlchemy model for storing Refresh Tokens.
Refresh tokens are typically long-lived tokens used to obtain new access tokens.
"""

import logging
from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone, timedelta # Added timezone, timedelta for __main__

from sqlalchemy import String, DateTime, Boolean, ForeignKey, Integer # Added Integer for FK
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.src.models.base import BaseModel

# Configure logger for this module
logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from backend.app.src.models.auth.user import User

class RefreshToken(BaseModel):
    """
    Represents a refresh token issued to a user.
    Allows users to obtain new access tokens without re-authenticating.
    It's crucial to manage these tokens securely.

    Attributes:
        user_id (int): Foreign key to the user this token belongs to.
        token_jti (str): The JWT ID (jti claim) of the refresh token, used for precise revocation.
        expires_at (datetime): Timestamp when this refresh token expires (UTC).
        is_revoked (bool): Whether this token has been revoked before its expiry.
        ip_address (Optional[str]): IP address from which the token was issued/used.
        user_agent (Optional[str]): User agent of the client that requested/used the token.
        # `id`, `created_at`, `updated_at` are inherited from BaseModel.
    """
    __tablename__ = "refresh_tokens"

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="The user this token belongs to")
    token_jti: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False, comment="JWT ID (jti claim) of the refresh token, for unique identification and revocation")

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True, comment="Timestamp when this refresh token expires (UTC)")
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True, comment="True if this token has been revoked before its natural expiry")

    ip_address: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="IP address from which the token was issued/last used")
    user_agent: Mapped[Optional[str]] = mapped_column(String(512), nullable=True, comment="User agent of the client that requested/used the token")

    # --- Relationship ---
    user: Mapped["User"] = relationship(back_populates="refresh_tokens")

    def __repr__(self) -> str:
        id_val = getattr(self, 'id', 'N/A')
        return f"<RefreshToken(id={id_val}, user_id={self.user_id}, jti='{self.token_jti[:10]}...', expires_at='{self.expires_at.isoformat() if self.expires_at else 'N/A'}', revoked={self.is_revoked})>"

if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- RefreshToken Model --- Demonstration")

    # Assume User model is available for demonstration if this were run in context
    # from backend.app.src.models.auth.user import User
    # demo_user = User(id=1, email="test@example.com", name="Test User", hashed_password="xyz")

    # Example RefreshToken instance
    refresh_token_instance = RefreshToken(
        user_id=1, # Assuming user with id=1 exists
        token_jti="unique_jwt_identifier_for_token_revocation_12345",
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        is_revoked=False,
        ip_address="192.168.1.101",
        user_agent="DemoClient/1.0"
    )
    refresh_token_instance.id = 1 # Simulate ORM-set ID
    refresh_token_instance.created_at = datetime.now(timezone.utc)
    refresh_token_instance.updated_at = datetime.now(timezone.utc)

    logger.info(f"Example RefreshToken: {refresh_token_instance!r}")
    logger.info(f"  User ID: {refresh_token_instance.user_id}")
    logger.info(f"  JTI: {refresh_token_instance.token_jti}")
    logger.info(f"  Expires At: {refresh_token_instance.expires_at.isoformat() if refresh_token_instance.expires_at else 'N/A'}")
    logger.info(f"  Is Revoked: {refresh_token_instance.is_revoked}")
    logger.info(f"  Created At: {refresh_token_instance.created_at.isoformat() if refresh_token_instance.created_at else 'N/A'}")


    revoked_token_instance = RefreshToken(
        user_id=2,
        token_jti="another_jti_67890",
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        is_revoked=True,
    )
    revoked_token_instance.id = 2
    logger.info(f"Example Revoked RefreshToken: {revoked_token_instance!r}")

    # The following line would error if run directly without SQLAlchemy engine and metadata setup for all related tables.
    # logger.info(f"RefreshToken attributes (conceptual table columns): {[c.name for c in RefreshToken.__table__.columns if not c.name.startswith('_')]}")
    logger.info("To see actual table columns, SQLAlchemy metadata needs to be initialized with an engine (e.g., Base.metadata.create_all(engine)).")
