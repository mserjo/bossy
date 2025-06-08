# backend/app/src/services/notifications/template.py
import logging
from typing import List, Optional, Dict, Any, Tuple # Added Dict, Any, Tuple for render_template example
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.src.services.dictionaries.base_dict import BaseDictionaryService
from app.src.models.notifications.template import NotificationTemplate # SQLAlchemy Model
from app.src.schemas.notifications.template import ( # Pydantic Schemas
    NotificationTemplateCreate,
    NotificationTemplateUpdate,
    NotificationTemplateResponse,
)

# Initialize logger for this module
logger = logging.getLogger(__name__)

class NotificationTemplateService(BaseDictionaryService[NotificationTemplate, NotificationTemplateCreate, NotificationTemplateUpdate, NotificationTemplateResponse]):
    """
    Service for managing Notification Template dictionary items.
    Templates define the structure and default content for various notification types (email, sms, in-app).
    Inherits generic CRUD operations from BaseDictionaryService.

    The 'name' field is expected to be the unique human-readable identifier for a template.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Initializes the NotificationTemplateService.

        Args:
            db_session (AsyncSession): The SQLAlchemy asynchronous database session.
        """
        super().__init__(db_session, model=NotificationTemplate, response_schema=NotificationTemplateResponse)
        logger.info("NotificationTemplateService initialized.")

    async def get_template_by_name(self, name: str) -> Optional[NotificationTemplateResponse]:
        """Retrieves a notification template by its unique name."""
        logger.debug(f"Attempting to retrieve NotificationTemplate by name: {name}")

        if not hasattr(self.model, 'name'): # Should exist based on typical model structure
            logger.error(f"Model {self._model_name} does not have a 'name' attribute. Cannot get_template_by_name.")
            return None

        stmt = select(self.model).where(self.model.name == name)
        result = await self.db_session.execute(stmt)
        item_db = result.scalar_one_or_none()

        if item_db:
            logger.info(f"{self._model_name} with name '{name}' found.")
            # return self.response_schema.model_validate(item_db) # Pydantic v2
            return self.response_schema.from_orm(item_db) # Pydantic v1
        logger.info(f"{self._model_name} with name '{name}' not found.")
        return None

    async def list_templates_by_type(
        self,
        template_type: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[NotificationTemplateResponse]:
        """
        Lists all notification templates of a specific type.
        Assumes NotificationTemplate model has a 'template_type' field.
        """
        logger.debug(f"Listing notification templates of type: '{template_type}'")
        if not hasattr(self.model, 'template_type'):
            logger.warning(f"NotificationTemplate model {self._model_name} does not have 'template_type' field. Cannot filter by type.")
            return []

        stmt = select(self.model).where(self.model.template_type == template_type) \
             .order_by(getattr(self.model, 'name', self.model.id)).offset(skip).limit(limit) # type: ignore

        templates_db = (await self.db_session.execute(stmt)).scalars().all()

        # response_list = [self.response_schema.model_validate(t) for t in templates_db] # Pydantic v2
        response_list = [self.response_schema.from_orm(t) for t in templates_db] # Pydantic v1
        logger.info(f"Retrieved {len(response_list)} notification templates of type '{template_type}'.")
        return response_list

    def render_template(self, template: NotificationTemplateResponse, context: Dict[str, Any]) -> Tuple[Optional[str], str]:
        """
        Renders subject and body of a template with provided context using Jinja2 or similar.
        This is a synchronous method as Jinja2 rendering is CPU-bound.
        If template strings are very large or context is huge, consider running in executor for async apps.

        Args:
            template (NotificationTemplateResponse): The Pydantic schema of the template.
            context (Dict[str, Any]): Dictionary of variables to use for rendering.

        Returns:
            Tuple[Optional[str], str]: Rendered subject (if applicable) and body.
        """
        logger.debug(f"Rendering template '{template.name}' with context keys: {list(context.keys())}")
        try:
            from jinja2 import Environment, select_autoescape, StrictUndefined
            # Using StrictUndefined helps catch missing variables in context during development
            env = Environment(
                autoescape=select_autoescape(['html', 'xml']), # Basic autoescaping
                undefined=StrictUndefined # Raise error for undefined variables
            )

            rendered_subject: Optional[str] = None
            if template.subject_template:
                jinja_subject_template = env.from_string(template.subject_template)
                rendered_subject = jinja_subject_template.render(context)

            jinja_body_template = env.from_string(template.body_template)
            rendered_body = jinja_body_template.render(context)

            logger.info(f"Template '{template.name}' rendered successfully.")
            return rendered_subject, rendered_body
        except Exception as e: # Catch Jinja errors (e.g., UndefinedError) or other issues
            logger.error(f"Error rendering template '{template.name}': {e}", exc_info=True)
            # Depending on policy, either raise or return a default/error message
            # For robustness in a notification system, might return a fallback message
            fallback_body = f"Error rendering notification '{template.name}'. Please contact support. Details: {str(e)}"
            fallback_subject = f"Notification Error: {template.name}" if template.subject_template else None
            return fallback_subject, fallback_body


logger.info("NotificationTemplateService class defined.")
