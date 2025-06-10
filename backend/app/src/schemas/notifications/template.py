# backend/app/src/schemas/notifications/template.py
import logging
from typing import Optional, Dict, Any, List, Literal

from pydantic import BaseModel, Field, field_validator

from app.src.schemas.base import BaseDBRead # Common DB fields

# Initialize logger for this module
logger = logging.getLogger(__name__)

# --- Notification Template Type Enum (Example) ---
TemplateTypeLiterals = Literal["email", "in_app", "sms", "push_notification", "messenger_bot"]

# --- NotificationTemplate Schemas ---

class NotificationTemplateBase(BaseModel):
    """
    Base schema for notification templates.
    """
    name: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Unique name/identifier for the template (e.g., 'user_registration_welcome', 'task_completion_alert')."
    )
    description: Optional[str] = Field(
        None,
        max_length=255,
        description="Brief description of the template's purpose."
    )
    template_type: TemplateTypeLiterals = Field(
        ...,
        description="The type of template (e.g., 'email', 'in_app', 'sms'). Determines which fields (subject/body) are relevant."
    )
    subject_template: Optional[str] = Field(
        None,
        max_length=255,
        description="Template for the notification subject (e.g., for emails). Uses Jinja2-like syntax for variables: 'Welcome, {{ username }}!'."
    )
    body_template: str = Field(
        ...,
        description="Template for the notification body/content. Uses Jinja2-like syntax: 'Your task {{ task_name }} is due on {{ due_date }}'."
    )
    default_vars: Optional[Dict[str, Any]] = Field(
        None,
        description="Default variables and their values for this template. Can be overridden at notification generation time."
    )
    required_vars: Optional[List[str]] = Field(
        None,
        description="List of variable names that MUST be provided when using this template to generate a notification."
    )
    # language_code: Optional[str] = Field("en", max_length=10, description="Language code for this template (e.g., 'en', 'uk'). Allows for localized templates.")


    @field_validator('subject_template', mode='before')
    @classmethod
    def check_subject_for_email(cls, v, values):
        # For Pydantic V2, `values` is a `ValidationInfo` object, access data via `values.data`
        # For Pydantic V1, `values` is a dict
        data = values.data if hasattr(values, 'data') else values
        if data.get('template_type') == 'email' and not v:
            logger.warning(f"Subject template is recommended for email templates. Name: {data.get('name')}")
            # raise ValueError('subject_template is required for email templates') # Or just log a warning
        return v

    class Config:
        orm_mode = True
        # from_attributes = True # For Pydantic V2
        anystr_strip_whitespace = True
        title = "NotificationTemplateBase"
        json_schema_extra = {
            "example": {
                "name": "task_reminder_email",
                "description": "Email reminder for an upcoming task deadline.",
                "template_type": "email",
                "subject_template": "Reminder: Task '{{ task_name }}' is due soon!",
                "body_template": "Hello {{ user_name }},\n\nThis is a reminder that your task '{{ task_name }}' is due on {{ due_date }}.\n\nDetails: {{ task_details }}\n\nThank you,\nKudos System",
                "default_vars": {"system_name": "Kudos Platform"},
                "required_vars": ["user_name", "task_name", "due_date", "task_details"]
            }
        }

    def __init__(self, **data):
        super().__init__(**data)
        logger.debug(f"NotificationTemplateBase instance created with data: {data}")


class NotificationTemplateCreate(NotificationTemplateBase):
    """
    Schema for creating a new notification template.
    """
    pass

    def __init__(self, **data):
        super().__init__(**data)
        logger.info(f"NotificationTemplateCreate instance created for template '{self.name}'.")


class NotificationTemplateUpdate(BaseModel):
    """
    Schema for updating an existing notification template. All fields are optional.
    """
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    template_type: Optional[TemplateTypeLiterals] = None
    subject_template: Optional[str] = Field(None, max_length=255)
    body_template: Optional[str] = None
    default_vars: Optional[Dict[str, Any]] = None
    required_vars: Optional[List[str]] = None
    # language_code: Optional[str] = Field(None, max_length=10)

    class Config:
        orm_mode = True
        # from_attributes = True # For Pydantic V2
        anystr_strip_whitespace = True
        title = "NotificationTemplateUpdate"
        json_schema_extra = {
            "example": {
                "description": "Updated email reminder for task deadlines with more details.",
                "body_template": "Hi {{ user_name }},\n\nJust a friendly reminder that your task '{{ task_name }}' is approaching its deadline on {{ due_date }}.\n\nPlease ensure it's completed on time.\n\nTask Details: {{ task_details }}\n\nBest regards,\nKudos System Team"
            }
        }

    def __init__(self, **data):
        super().__init__(**data)
        logger.info(f"NotificationTemplateUpdate instance created with update data: {data}")


class NotificationTemplateResponse(NotificationTemplateBase, BaseDBRead):
    """
    Schema for representing a notification template in API responses.
    """
    # id: UUID # From BaseDBRead
    # created_at: datetime # From BaseDBRead
    # updated_at: datetime # From BaseDBRead

    class Config(NotificationTemplateBase.Config):
        title = "NotificationTemplateResponse"
        json_schema_extra = { # Override or extend example
            "example": {
                "id": "c1d2e3f4-a5b6-c7d8-e9f0-a1b2c3d4e5f6",
                "name": "task_reminder_email",
                "description": "Email reminder for an upcoming task deadline.",
                "template_type": "email",
                "subject_template": "Reminder: Task '{{ task_name }}' is due soon!",
                "body_template": "Hello {{ user_name }},\n\nThis is a reminder that your task '{{ task_name }}' is due on {{ due_date }}.\n\nDetails: {{ task_details }}\n\nThank you,\nKudos System",
                "default_vars": {"system_name": "Kudos Platform"},
                "required_vars": ["user_name", "task_name", "due_date", "task_details"],
                # "language_code": "en",
                "created_at": "2023-06-01T14:00:00Z",
                "updated_at": "2023-06-05T11:30:00Z"
            }
        }

    def __init__(self, **data):
        super().__init__(**data)
        logger.debug(f"NotificationTemplateResponse instance created for template ID '{self.id}'.")

logger.info("NotificationTemplate schemas (NotificationTemplateBase, NotificationTemplateCreate, NotificationTemplateUpdate, NotificationTemplateResponse) defined successfully.")
