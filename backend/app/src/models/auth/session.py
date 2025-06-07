# backend/app/src/models/auth/session.py

"""
SQLAlchemy model for storing User Session information.
This can be used for tracking active user sessions, especially for web applications
or if you need server-side session management beyond stateless JWTs.
"""

import logging
from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone, timedelta # Added timezone, timedelta for __main__

from sqlalchemy import String, DateTime, ForeignKey, Text, Integer # Added Integer for FK
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.src.models.base import BaseModel

# Configure logger for this module
logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from backend.app.src.models.auth.user import User

class UserSession(BaseModel):
    """
    Represents an active user session.
    This can be used to track user activity, manage server-side sessions,
    or provide features like 'log out from other devices'.

    Attributes:
        user_id (int): Foreign key to the user this session belongs to.
        session_id_hash (str): A securely hashed version of the session ID.
                               The actual session ID might be stored in a client-side cookie.
        ip_address (Optional[str]): IP address where the session originated.
        user_agent (Optional[str]): User agent string of the client.
        last_activity_at (datetime): Timestamp of the last known activity for this session (UTC).
        expires_at (datetime): Timestamp when this session is set to expire (UTC).
        # `id`, `created_at`, `updated_at` are inherited from BaseModel.
    """
    __tablename__ = "user_sessions"

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True, comment="The user this session belongs to")

    # Store a hash of the session ID, not the session ID itself, if the actual ID is client-side (e.g., in a secure cookie)
    # If this table IS the session store, then session_id_hash could just be session_id and be the primary lookup key.
    session_id_hash: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False, comment="Hashed identifier of the session (e.g., hash of a cookie value)")

    ip_address: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="IP address from which the session originated")
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="User agent string of the client for this session") # Text for potentially long UA strings

    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True, comment="Timestamp of the last recorded activity for this session (UTC)")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True, comment="Timestamp when this session will/did expire (UTC)")

    # --- Relationship ---
    user: Mapped["User"] = relationship(back_populates="sessions")

    def __repr__(self) -> str:
        id_val = getattr(self, 'id', 'N/A')
        return f"<UserSession(id={id_val}, user_id={self.user_id}, session_id_hash='{self.session_id_hash[:10]}...', expires_at='{self.expires_at.isoformat() if self.expires_at else 'N/A'}')>"

if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- UserSession Model --- Demonstration")

    # from backend.app.src.models.auth.user import User # If needed for demo
    # demo_user = User(id=1, email="session_user@example.com", name="Session User", hashed_password="xyz")

    # Example UserSession instance
    session_instance = UserSession(
        user_id=1, # Assuming user with id=1 exists
        session_id_hash="hashed_session_id_placeholder_abcdef123456",
        ip_address="203.0.113.45",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
        last_activity_at=datetime.now(timezone.utc) - timedelta(minutes=5),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=8)
    )
    session_instance.id = 1 # Simulate ORM-set ID
    session_instance.created_at = datetime.now(timezone.utc) - timedelta(minutes=30)
    session_instance.updated_at = datetime.now(timezone.utc) - timedelta(minutes=5)

    logger.info(f"Example UserSession: {session_instance!r}")
    logger.info(f"  User ID: {session_instance.user_id}")
    logger.info(f"  IP Address: {session_instance.ip_address}")
    logger.info(f"  Expires At: {session_instance.expires_at.isoformat() if session_instance.expires_at else 'N/A'}")
    logger.info(f"  Last Activity: {session_instance.last_activity_at.isoformat() if session_instance.last_activity_at else 'N/A'}")
    logger.info(f"  Created At: {session_instance.created_at.isoformat() if session_instance.created_at else 'N/A'}")


    expired_session = UserSession(
        user_id=2,
        session_id_hash="another_hashed_session_id_7890ghijk",
        last_activity_at=datetime.now(timezone.utc) - timedelta(days=2, hours=1),
        expires_at=datetime.now(timezone.utc) - timedelta(days=2) # Expired
    )
    expired_session.id = 2
    logger.info(f"Example Expired UserSession: {expired_session!r}")

    # The following line would error if run directly without SQLAlchemy engine and metadata setup for all related tables.
    # logger.info(f"UserSession attributes (conceptual table columns): {[c.name for c in UserSession.__table__.columns if not c.name.startswith('_')]}")
    logger.info("To see actual table columns, SQLAlchemy metadata needs to be initialized with an engine (e.g., Base.metadata.create_all(engine)).")
