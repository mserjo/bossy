# backend/app/src/models/notifications/template.py

"""
SQLAlchemy model for Notification Templates.
Templates are used to generate consistent notification messages for various channels.
"""

import logging
from typing import Optional, TYPE_CHECKING, Dict, Any # For Mapped type hints
from datetime import datetime, timezone # Added for __main__
from enum import Enum as PythonEnum # For NotificationChannelEnum

from sqlalchemy import String, Text, Enum as SQLAlchemyEnum, UniqueConstraint, JSON # Added JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.src.models.base import BaseMainModel # Templates are managed entities

# Configure logger for this module
logger = logging.getLogger(__name__)

class NotificationChannelEnum(PythonEnum): # Changed to inherit from PythonEnum
    """ Defines the channels through which a notification can be sent. """
    IN_APP = "in_app"       # In-application notification system
    EMAIL = "email"         # Email notification
    SMS = "sms"             # SMS text message
    PUSH = "push"           # Mobile or web push notification
    # SLACK = "slack"       # Example: Slack message
    # TELEGRAM = "telegram" # Example: Telegram message

if TYPE_CHECKING:
    # No direct relationships from template to other main tables typically, but could link to a category or similar dict table.
    pass

class NotificationTemplate(BaseMainModel): # Inherits id, name, description, state, notes, created_at, updated_at, deleted_at
    """
    Represents a template for generating notification messages.
    This allows for consistent messaging and easier management of notification content.
    The 'name' field from BaseMainModel can be used as a human-readable template name.
    The 'description' can explain the purpose or context of the template.
    """
    __tablename__ = "notification_templates"

    # 'name' (e.g., "Welcome Email Template", "Task Assigned In-App Notification") inherited.
    # 'description' (e.g., "Template used when a new user registers and verifies their email.") inherited.
    # 'state' can be 'active', 'draft', 'archived'.

    template_type_code: Mapped[str] = mapped_column(String(100), nullable=False, index=True, comment="Unique code identifying the template's purpose (e.g., 'USER_REGISTRATION_WELCOME', 'TASK_ASSIGNED_ALERT')")
    # This is not globally unique, but unique per channel+language. See UniqueConstraint.

    channel: Mapped[NotificationChannelEnum] = mapped_column(
        SQLAlchemyEnum(NotificationChannelEnum, name="notificationchannelenum", create_constraint=True, native_enum=False), # native_enum=False for string storage
        nullable=False,
        index=True,
        comment="The communication channel this template is designed for (e.g., email, sms, in_app)"
    )

    language_code: Mapped[str] = mapped_column(String(10), default="en", nullable=False, index=True, comment="Language code for this template version (e.g., 'en', 'uk', 'es')")
    # This allows for multiple language versions of the same template_type_code and channel.

    subject_template: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="Template for the notification subject (e.g., for emails). Uses templating engine syntax (e.g., Jinja2 vars like {{ user_name }})")
    body_template: Mapped[str] = mapped_column(Text, nullable=False, comment="Template for the notification body/content. Uses templating engine syntax.")

    # Example of storing rendering hints or required variables as JSON
    template_variables_schema: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True, comment="JSON schema or list of expected variables for this template (e.g., ['user_name', 'task_title'])")

    # --- Relationships ---
    # No direct ORM relationships defined from here in this basic setup.
    # Could potentially link to a dictionary table for categories if templates are numerous.

    # --- Table Arguments ---
    # A template should be unique for its type, channel, and language.
    __table_args__ = (
        UniqueConstraint('template_type_code', 'channel', 'language_code', name='uq_notification_template_type_channel_lang'),
    )

    def __repr__(self) -> str:
        id_val = getattr(self, 'id', 'N/A')
        return f"<NotificationTemplate(id={id_val}, type_code='{self.template_type_code}', channel='{self.channel.value}', lang='{self.language_code}')>"

if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- NotificationTemplate Model --- Demonstration")

    # Example NotificationTemplate instances
    welcome_email_en = NotificationTemplate(
        name="Welcome Email (English)",
        description="Standard welcome email sent to new users upon successful registration.",
        template_type_code="USER_WELCOME",
        channel=NotificationChannelEnum.EMAIL,
        language_code="en",
        subject_template="Welcome to {{ project_name }}, {{ user_name }}!",
        body_template="Hello {{ user_name }},\n\nWelcome aboard! We're excited to have you at {{ project_name }}.\n\nTo get started, please verify your email by clicking here: {{ verification_link }}\n\nThanks,\nThe {{ project_name }} Team",
        state="active", # from BaseMainModel
        template_variables_schema={"project_name": "string", "user_name": "string", "verification_link": "url"}
    )
    welcome_email_en.id = 1 # Simulate ORM-set ID
    welcome_email_en.created_at = datetime.now(timezone.utc) # Simulate timestamp
    welcome_email_en.updated_at = datetime.now(timezone.utc) # Simulate timestamp

    logger.info(f"Example Email Template (EN): {welcome_email_en!r}")
    logger.info(f"  Subject: {welcome_email_en.subject_template}")
    logger.info(f"  Variables Schema: {welcome_email_en.template_variables_schema}")
    logger.info(f"  Created At: {welcome_email_en.created_at.isoformat() if welcome_email_en.created_at else 'N/A'}")


    task_assigned_in_app_uk = NotificationTemplate(
        name="Task Assigned In-App (Ukrainian)",
        description="In-app notification when a task is assigned to a user.",
        template_type_code="TASK_ASSIGNED",
        channel=NotificationChannelEnum.IN_APP,
        language_code="uk",
        subject_template="Нове завдання: {{ task_title }}",
        body_template="Вам призначено нове завдання: '{{ task_title }}' у групі '{{ group_name }}'. Дедлайн: {{ due_date }}.",
        state="active"
    )
    task_assigned_in_app_uk.id = 2
    logger.info(f"Example In-App Template (UK): {task_assigned_in_app_uk!r}")
    logger.info(f"  Body: {task_assigned_in_app_uk.body_template}")

    # The following line would error if run directly without SQLAlchemy engine and metadata setup for all related tables.
    # logger.info(f"NotificationTemplate attributes (conceptual table columns): {[c.name for c in NotificationTemplate.__table__.columns if not c.name.startswith('_')]}")
    logger.info("To see actual table columns, SQLAlchemy metadata needs to be initialized with an engine (e.g., Base.metadata.create_all(engine)).")
