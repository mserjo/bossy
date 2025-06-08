# backend/app/src/repositories/notifications/notification_template_repository.py

"""
Repository for NotificationTemplate entities.
Provides CRUD operations and specific methods for managing notification templates.
"""

import logging
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from backend.app.src.models.notifications.template import NotificationTemplate, NotificationChannelEnum
from backend.app.src.schemas.notifications.template import NotificationTemplateCreate, NotificationTemplateUpdate
from backend.app.src.repositories.base import BaseRepository

logger = logging.getLogger(__name__)

class NotificationTemplateRepository(BaseRepository[NotificationTemplate, NotificationTemplateCreate, NotificationTemplateUpdate]):
    """
    Repository for managing NotificationTemplate records.
    Templates are unique by (template_type_code, channel, language_code).
    """

    def __init__(self):
        super().__init__(NotificationTemplate)

    async def get_template_by_code_channel_lang(
        self,
        db: AsyncSession,
        *,
        template_type_code: str,
        channel: NotificationChannelEnum,
        language_code: str = "en"
    ) -> Optional[NotificationTemplate]:
        """
        Retrieves a notification template by its type code, channel, and language.
        Filters for active, non-deleted templates by default.

        Args:
            db: The SQLAlchemy asynchronous database session.
            template_type_code: The unique code for the template's purpose.
            channel: The NotificationChannelEnum member.
            language_code: The language code (e.g., 'en', 'uk').

        Returns:
            The NotificationTemplate object if found, otherwise None.
        """
        conditions = [
            self.model.template_type_code == template_type_code, # type: ignore[attr-defined]
            self.model.channel == channel, # type: ignore[attr-defined]
            self.model.language_code == language_code # type: ignore[attr-defined]
        ]
        if hasattr(self.model, "state"):
             conditions.append(self.model.state == "active") # type: ignore[attr-defined]

        if hasattr(self.model, "deleted_at"):
            conditions.append(self.model.deleted_at.is_(None)) # type: ignore[attr-defined]

        statement = select(self.model).where(*conditions)
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_templates_by_code(
        self,
        db: AsyncSession,
        *,
        template_type_code: str,
        channel: Optional[NotificationChannelEnum] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[NotificationTemplate]:
        """
        Retrieves all language versions of a template for a specific type code,
        optionally filtered by channel. Fetches active, non-deleted templates by default.

        Args:
            db: The SQLAlchemy asynchronous database session.
            template_type_code: The unique code for the template's purpose.
            channel: Optional. Filter by a specific NotificationChannelEnum member.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            A list of NotificationTemplate objects.
        """
        conditions = [self.model.template_type_code == template_type_code] # type: ignore[attr-defined]
        if channel:
            conditions.append(self.model.channel == channel) # type: ignore[attr-defined]

        if hasattr(self.model, "state"):
             conditions.append(self.model.state == "active") # type: ignore[attr-defined]
        if hasattr(self.model, "deleted_at"):
            conditions.append(self.model.deleted_at.is_(None)) # type: ignore[attr-defined]

        statement = (
            select(self.model)
            .where(*conditions)
            .order_by(self.model.language_code) # type: ignore[attr-defined]
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(statement)
        return list(result.scalars().all())

    # BaseRepository methods create, get, update, remove are inherited.
