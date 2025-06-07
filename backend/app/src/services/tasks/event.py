# backend/app/src/services/tasks/event.py
import logging
from typing import List, Optional, Any
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.exc import IntegrityError

from app.src.services.base import BaseService
from app.src.models.tasks.event import Event # SQLAlchemy Event model
from app.src.models.auth.user import User
from app.src.models.groups.group import Group
from app.src.models.dictionaries.task_types import TaskType # Events might still use task types, or have event types
from app.src.models.dictionaries.statuses import Status # For event status
# Assuming these models exist for relationships if used by Event model
from app.src.models.tasks.assignment import TaskAssignment # If events can be "assigned"
# from app.src.models.tasks.rsvp import EventRSVP # If events have RSVP functionality


from app.src.schemas.tasks.event import ( # Pydantic Event schemas
    EventCreate,
    EventUpdate,
    EventResponse,
    EventDetailedResponse # Assuming a more detailed response schema
)

# Initialize logger for this module
logger = logging.getLogger(__name__)

class EventService(BaseService):
    """
    Service for managing events. Events are similar to tasks but may represent
    scheduled occurrences, activities, or milestones.
    This service provides CRUD operations and specific event logic.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        logger.info("EventService initialized.")

    async def get_event_by_id(self, event_id: UUID, include_details: bool = False) -> Optional[EventResponse]: # Or EventDetailedResponse
        """
        Retrieves an event by its ID.
        Can optionally include more details like assignees, type, status, etc.
        """
        logger.debug(f"Attempting to retrieve event by ID: {event_id}, include_details: {include_details}")

        query = select(Event).where(Event.id == event_id)
        if include_details:
            # Adjust eager loading based on Event model's relationships
            query = query.options(
                selectinload(Event.event_type),
                selectinload(Event.status),
                selectinload(Event.group),
                selectinload(Event.created_by_user).options(selectinload(User.user_type)),
                selectinload(Event.updated_by_user).options(selectinload(User.user_type)) if hasattr(Event, 'updated_by_user') else None,
                selectinload(Event.assignments).joinedload(TaskAssignment.user).options(selectinload(User.user_type)) if hasattr(Event, 'assignments') else None,
                # selectinload(Event.rsvps).joinedload(EventRSVP.user).options(selectinload(User.user_type)) if hasattr(Event, 'rsvps') else None,
            )
            query = query.options(*(opt for opt in query.get_options() if opt is not None))


        result = await self.db_session.execute(query)
        event_db = result.scalar_one_or_none()

        if event_db:
            logger.info(f"Event with ID '{event_id}' found.")
            if include_details:
                # return EventDetailedResponse.model_validate(event_db) # Pydantic v2
                return EventDetailedResponse.from_orm(event_db) # Pydantic v1
            # return EventResponse.model_validate(event_db) # Pydantic v2
            return EventResponse.from_orm(event_db) # Pydantic v1

        logger.info(f"Event with ID '{event_id}' not found.")
        return None

    async def create_event(self, event_create_data: EventCreate, creator_user_id: UUID) -> Optional[EventDetailedResponse]: # Return Optional
        """
        Creates a new event.
        """
        logger.debug(f"Attempting to create new event '{event_create_data.title}' by user ID: {creator_user_id}")

        group = await self.db_session.get(Group, event_create_data.group_id)
        if not group: raise ValueError(f"Group with ID '{event_create_data.group_id}' not found.")

        event_type_id_to_check = getattr(event_create_data, 'event_type_id', None) # Event model should have event_type_id
        if not event_type_id_to_check: raise ValueError("Event type ID (event_type_id) must be provided.")

        event_type_model = TaskType # Or a dedicated EventType model if it exists
        event_type = await self.db_session.get(event_type_model, event_type_id_to_check)
        if not event_type: raise ValueError(f"EventType/TaskType with ID '{event_type_id_to_check}' not found.")

        status_id_to_set = event_create_data.status_id
        if not status_id_to_set:
            default_status_stmt = select(Status.id).where(Status.code == "SCHEDULED")
            default_status_id = (await self.db_session.execute(default_status_stmt)).scalar_one_or_none()
            if not default_status_id:
                if not hasattr(Event, 'status_id') or Event.status_id.nullable is False:
                     raise ValueError("Event status is required and default 'SCHEDULED' status not found.")
                status_id_to_set = None
            else:
                status_id_to_set = default_status_id
            logger.info(f"No status_id provided for new event, using default status ID: {status_id_to_set or 'None (if nullable)'}")
        else:
            status = await self.db_session.get(Status, status_id_to_set)
            if not status: raise ValueError(f"Status with ID '{status_id_to_set}' not found.")

        event_db_data = event_create_data.dict()
        event_db_data['status_id'] = status_id_to_set
        # Ensure the field name for type ID matches the Event model (e.g., event_type_id)
        if 'task_type_id' in event_db_data and 'event_type_id' not in event_db_data and hasattr(Event, 'event_type_id'):
            event_db_data['event_type_id'] = event_db_data.pop('task_type_id')
        elif 'event_type_id' not in event_db_data and 'task_type_id' in event_db_data and not hasattr(Event, 'event_type_id') and hasattr(Event, 'task_type_id'):
             pass # Use task_type_id as is
        elif 'event_type_id' not in event_db_data and 'task_type_id' not in event_db_data:
             raise ValueError("Missing event_type_id or task_type_id in data for Event model.")


        new_event_db = Event(**event_db_data, created_by_user_id=creator_user_id)

        self.db_session.add(new_event_db)
        try:
            await self.commit()
            created_event_detailed = await self.get_event_by_id(new_event_db.id, include_details=True)
            if created_event_detailed:
                logger.info(f"Event '{new_event_db.title}' (ID: {new_event_db.id}) created by user ID '{creator_user_id}'.")
                return created_event_detailed
            else:
                logger.error(f"Failed to retrieve newly created event ID {new_event_db.id} after commit.")
                return None
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Integrity error creating event '{event_create_data.title}': {e}", exc_info=True)
            raise ValueError(f"Could not create event due to a data conflict: {e}")
        except Exception as e:
            await self.rollback()
            logger.error(f"Unexpected error creating event '{event_create_data.title}': {e}", exc_info=True)
            raise

    async def update_event(self, event_id: UUID, event_update_data: EventUpdate, current_user_id: UUID) -> Optional[EventDetailedResponse]:
        logger.debug(f"Attempting to update event ID: {event_id} by user ID: {current_user_id}")

        event_db = await self.db_session.get(Event, event_id)

        if not event_db:
            logger.warning(f"Event ID '{event_id}' not found for update.")
            return None

        update_data = event_update_data.dict(exclude_unset=True)

        event_type_id_to_check = update_data.get('event_type_id', update_data.get('task_type_id'))
        current_event_type_id = getattr(event_db, 'event_type_id', getattr(event_db, 'task_type_id', None))

        if event_type_id_to_check and current_event_type_id != event_type_id_to_check :
            if not await self.db_session.get(TaskType, event_type_id_to_check): # Or EventType model
                raise ValueError(f"New EventType/TaskType ID '{event_type_id_to_check}' not found.")

        if 'status_id' in update_data and event_db.status_id != update_data['status_id']:
            if not await self.db_session.get(Status, update_data['status_id']):
                raise ValueError(f"New Status ID '{update_data['status_id']}' not found.")

        for field, value in update_data.items():
            model_field_name = field
            if field == 'task_type_id' and hasattr(Event, 'event_type_id') and not hasattr(Event, 'task_type_id'):
                model_field_name = 'event_type_id'

            if hasattr(event_db, model_field_name):
                setattr(event_db, model_field_name, value)
            else:
                logger.warning(f"Field '{model_field_name}' (from '{field}') not found on Event model for update of event ID '{event_id}'.")

        if hasattr(event_db, 'updated_by_user_id'):
            event_db.updated_by_user_id = current_user_id
        if hasattr(event_db, 'updated_at'):
            event_db.updated_at = datetime.now(timezone.utc)

        self.db_session.add(event_db)
        try:
            await self.commit()
            logger.info(f"Event ID '{event_id}' updated successfully by user ID '{current_user_id}'.")
            return await self.get_event_by_id(event_id, include_details=True)
        except Exception as e:
            await self.rollback()
            logger.error(f"Error during event update commit for event ID '{event_id}': {e}", exc_info=True)
            raise


    async def delete_event(self, event_id: UUID, current_user_id: UUID) -> bool:
        logger.debug(f"Attempting to delete event ID: {event_id} by user ID: {current_user_id}")

        event_db = await self.db_session.get(Event, event_id)
        if not event_db:
            logger.warning(f"Event ID '{event_id}' not found for deletion.")
            return False

        await self.db_session.delete(event_db)
        await self.commit()
        logger.info(f"Event ID '{event_id}' deleted successfully by user ID '{current_user_id}'.")
        return True

    async def list_events_for_group(
        self, group_id: UUID, skip: int = 0, limit: int = 100,
        status_code: Optional[str] = None, event_type_code: Optional[str] = None,
        include_details: bool = False,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[EventResponse]:
        logger.debug(f"Listing events for group ID: {group_id}, status: {status_code}, type: {event_type_code}, details: {include_details}, start: {start_date}, end: {end_date}")

        query = select(Event).where(Event.group_id == group_id)
        event_type_field_name = 'event_type_id' if hasattr(Event, 'event_type_id') else 'task_type_id'


        if include_details:
            query = query.options(
                selectinload(getattr(Event, 'event_type', getattr(Event, 'task_type', None))), # Adapt based on actual field name
                selectinload(Event.status),
                selectinload(Event.created_by_user).options(selectinload(User.user_type)),
                selectinload(Event.assignments).joinedload(TaskAssignment.user).options(selectinload(User.user_type)) if hasattr(Event, 'assignments') else None,
            )
            query = query.options(*(opt for opt in query.get_options() if opt is not None))
        else:
             query = query.options(selectinload(getattr(Event, 'event_type', getattr(Event, 'task_type', None))), selectinload(Event.status))


        if status_code:
            query = query.join(Status, Event.status_id == Status.id).where(Status.code == status_code)

        if event_type_code: # Join with TaskType or EventType model
            query = query.join(TaskType, getattr(Event, event_type_field_name) == TaskType.id).where(TaskType.code == event_type_code)

        # Assume Event model has 'start_time' and 'end_time' for date filtering.
        # If it only has 'start_time', adjust end_date filter accordingly.
        if start_date and hasattr(Event, 'start_time'):
            query = query.where(Event.start_time >= start_date)
        if end_date:
            if hasattr(Event, 'end_time') and Event.end_time is not None : # If events have a specific end_time
                 query = query.where(Event.end_time <= end_date)
            elif hasattr(Event, 'start_time'): # If only start_time, filter events starting before or on end_date
                 query = query.where(Event.start_time <= end_date)

        order_by_attr = getattr(Event, 'start_time', Event.created_at) # Order by start_time if available
        query = query.order_by(order_by_attr.desc() if order_by_attr is not None else Event.created_at.desc()).offset(skip).limit(limit) # type: ignore

        result = await self.db_session.execute(query)
        events_db = result.scalars().unique().all()

        response_model = EventDetailedResponse if include_details else EventResponse
        # response_list = [response_model.model_validate(e) for e in events_db] # Pydantic v2
        response_list = [response_model.from_orm(e) for e in events_db] # Pydantic v1

        logger.info(f"Retrieved {len(response_list)} events for group ID '{group_id}'.")
        return response_list

logger.info("EventService class defined.")
