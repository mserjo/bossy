# backend/app/src/services/tasks/scheduler.py
import logging
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.src.services.base import BaseService
from app.src.models.tasks.task import Task # SQLAlchemy Task model
from app.src.models.tasks.assignment import TaskAssignment # For task assignments
# from app.src.models.tasks.event import Event # If events can also be recurring
# from app.src.services.tasks.task import TaskService # To create new task instances
# from app.src.services.tasks.assignment import TaskAssignmentService # To assign recurring tasks
# from app.src.services.notifications.notification import InternalNotificationService # For reminders

# Initialize logger for this module
logger = logging.getLogger(__name__)

# Define recurrence intervals (could be an Enum or from a dictionary model)
RECURRENCE_DAILY = "DAILY"
RECURRENCE_WEEKLY = "WEEKLY"
RECURRENCE_MONTHLY = "MONTHLY"
RECURRENCE_YEARLY = "YEARLY"
# etc.

class TaskSchedulingService(BaseService):
    """
    Service for handling scheduled and recurring tasks/events.
    This includes logic for creating instances of recurring tasks,
    sending reminders for upcoming deadlines, and potentially auto-assigning tasks.

    Note: Actual execution of these methods would typically be triggered by a
    scheduled job runner (e.g., Celery Beat, APScheduler, cron) that calls
    these service methods at appropriate intervals.
    """

    def __init__(self, db_session: AsyncSession): #, task_service: TaskService, notification_service: InternalNotificationService, etc.
        super().__init__(db_session)
        # To avoid circular dependencies at module level, dependent services can be
        # instantiated locally within methods or passed during initialization if managed by DI.
        # For now, some service calls will be conceptual placeholders.
        logger.info("TaskSchedulingService initialized.")

    async def process_recurring_tasks(self) -> List[UUID]:
        """
        Identifies recurring task templates that are due for new instance creation
        and creates those new instances.

        This method would be called periodically (e.g., daily).

        Returns:
            List[UUID]: A list of newly created task instance IDs.
        """
        logger.info("Processing recurring tasks...")
        now = datetime.now(timezone.utc)
        newly_created_task_ids: List[UUID] = []

        # This query assumes Task model has: is_recurring_template, is_active, recurrence_end_date
        stmt = select(Task).where(
            Task.is_recurring_template == True,
            Task.is_active == True,
            ((Task.recurrence_end_date == None) | (Task.recurrence_end_date > now)) # Check recurrence_end_date
        ).options(
            selectinload(Task.group),
            selectinload(Task.task_type),
            selectinload(Task.status), # To get default status_id for new instance
            selectinload(Task.created_by_user) # To get original creator
        )

        recurring_templates_db = (await self.db_session.execute(stmt)).scalars().all()

        # Import TaskService locally to avoid circular import at module level
        # from app.src.services.tasks.task import TaskService # This would still be circular if TaskService imports this.
        # task_service = TaskService(self.db_session) # For robust creation, better to use TaskService.
                                                    # For now, direct model instantiation.

        for template in recurring_templates_db:
            if await self._should_create_new_instance(template, now):
                try:
                    logger.info(f"Creating new instance for recurring task template ID: {template.id} ('{template.title}')")

                    new_due_date = self._calculate_next_due_date(template, now)

                    from app.src.models.dictionaries.statuses import Status # For default status
                    # Use template's status if available and valid, else default to OPEN
                    status_id_to_set = template.status_id
                    if not status_id_to_set:
                        open_status = (await self.db_session.execute(select(Status).where(Status.code == "OPEN"))).scalar_one_or_none()
                        if not open_status:
                            logger.error(f"Default 'OPEN' status not found, cannot create instance for task template {template.id}")
                            continue
                        status_id_to_set = open_status.id

                    new_instance_model = Task(
                        title=template.title,
                        description=template.description,
                        group_id=template.group_id,
                        task_type_id=template.task_type_id,
                        status_id=status_id_to_set,
                        due_date=new_due_date,
                        points_value=getattr(template, 'points_value', None),
                        is_recurring_template=False, # This is an instance
                        parent_task_id=template.id,  # Link to the template task
                        created_by_user_id=template.created_by_user_id, # Or a dedicated system user ID
                        is_active=True # New instances are active by default
                        # Copy other relevant fields from template as needed
                    )
                    self.db_session.add(new_instance_model)
                    await self.db_session.flush() # Get ID for logging and potential assignments
                    newly_created_task_ids.append(new_instance_model.id)
                    logger.info(f"Created new task instance ID: {new_instance_model.id} for template ID: {template.id}")

                    # Update the template's last_instance_created_at
                    if hasattr(template, 'last_instance_created_at'):
                        template.last_instance_created_at = now
                        self.db_session.add(template)
                    else:
                        logger.warning(f"Task template ID {template.id} missing 'last_instance_created_at' field.")


                    # TODO: If template had default assignees, assign the new instance too
                    # from app.src.services.tasks.assignment import TaskAssignmentService # Local import
                    # assignment_service = TaskAssignmentService(self.db_session)
                    # template_assignments = await assignment_service.list_assignments_for_task(template.id, is_active=True)
                    # for t_assignment in template_assignments:
                    #     await assignment_service.assign_task_to_user(new_instance_model.id, t_assignment.user_id, template.created_by_user_id)


                except Exception as e:
                    logger.error(f"Error processing recurring task template ID {template.id}: {e}", exc_info=True)
                    await self.db_session.rollback() # Rollback changes for this specific template processing
                    # Continue to next template

        if newly_created_task_ids: # Only commit if there were successful creations flushed
            try:
                await self.commit()
                logger.info(f"Successfully processed recurring tasks. Created {len(newly_created_task_ids)} new instances.")
            except Exception as e:
                logger.error(f"Error committing recurring task instances: {e}", exc_info=True)
                await self.rollback()
                newly_created_task_ids.clear() # Clear list as commit failed

        return newly_created_task_ids

    async def _should_create_new_instance(self, template_task: Task, current_time: datetime) -> bool:
        if not getattr(template_task, 'is_recurring_template', False): return False

        interval = getattr(template_task, 'recurrence_interval', None)
        last_created = getattr(template_task, 'last_instance_created_at', None)

        if not interval: return False

        if getattr(template_task, 'recurrence_end_date', None) and template_task.recurrence_end_date < current_time:
            logger.info(f"Recurring task template ID {template_task.id} has ended. No new instance.")
            return False

        if not last_created:
            template_start_date = getattr(template_task, 'recurrence_start_date', template_task.created_at)
            return current_time >= template_start_date

        if interval == RECURRENCE_DAILY:
            return last_created.date() < current_time.date()
        elif interval == RECURRENCE_WEEKLY: # Create if it's been a week since last_created (based on date part)
            return last_created.date() <= current_time.date() - timedelta(days=7)
        elif interval == RECURRENCE_MONTHLY:
            # Simplified: create if current_day >= last_created_day and it's a new month, or significantly into the month.
            # This is a known hard problem. Using dateutil.relativedelta is better.
            if current_time.year > last_created.year or current_time.month > last_created.month:
                return current_time.day >= last_created.day
            return False # Same month, already created.
        logger.warning(f"Unknown or unhandled recurrence interval '{interval}' for template ID {template_task.id}")
        return False

    def _calculate_next_due_date(self, template_task: Task, current_time: datetime) -> Optional[datetime]:
        # This is a placeholder. Real logic needs to be much more robust.
        # Example: Due in N days from instance creation (current_time for scheduler)
        instance_duration_days = getattr(template_task, 'instance_duration_days', 1) # Assume tasks are due in 1 day

        # Set due time based on template's due_date time component if available, else default (e.g. EOD)
        due_time = getattr(template_task, 'due_date', None)
        due_time_component = due_time.time() if due_time else datetime.max.time().replace(hour=23, minute=59, second=59, microsecond=0)

        # New due date is based on current_time (when instance is conceptually for) + duration, with specific time
        new_due_date_val = current_time.replace(hour=due_time_component.hour, minute=due_time_component.minute, second=due_time_component.second, microsecond=due_time_component.microsecond) + timedelta(days=instance_duration_days -1) # if instance_duration_days includes "today"

        # If template had a due_date, it might imply a specific time of day.
        # Or, if the template's due_date was relative (e.g. task.due_date = created_at + timedelta(days=N)),
        # then new_due_date = current_time + (template.due_date - template.created_at)
        # This is complex and depends on how template due_dates are defined.

        # Fallback if time_to_complete_hours exists
        if hasattr(template_task, 'time_to_complete_hours') and template_task.time_to_complete_hours is not None:
            return current_time + timedelta(hours=template_task.time_to_complete_hours)

        return new_due_date_val


    async def send_task_reminders(self) -> int:
        logger.info("Sending task reminders...")
        now = datetime.now(timezone.utc)
        reminders_sent_count = 0

        reminder_window_start = now
        reminder_window_end = now + timedelta(days=1)

        # This query assumes Task model has: due_date, is_active, last_reminder_sent_at
        # And Status model has 'code' (and Task.status relationship)
        stmt = select(Task).join(Status, Task.status_id == Status.id).where(
            Task.due_date >= reminder_window_start,
            Task.due_date <= reminder_window_end,
            Task.is_active == True,
            Status.code != "COMPLETED", # Filter out completed tasks
            Status.code != "CANCELLED", # Filter out cancelled tasks
            # Check last_reminder_sent_at to avoid spamming
            ((Task.last_reminder_sent_at == None) | (Task.last_reminder_sent_at < (now - timedelta(hours=23))))
        ).options(
            selectinload(Task.assignments).joinedload(TaskAssignment.user).options(selectinload(User.user_type)), # Load user for notification
            selectinload(Task.group) # Load group for context in notification
        )

        tasks_to_remind_db = (await self.db_session.execute(stmt)).scalars().unique().all()

        # from app.src.services.notifications.notification import InternalNotificationService # Conceptual
        # notification_service = InternalNotificationService(self.db_session)

        for task in tasks_to_remind_db:
            if not task.assignments:
                logger.debug(f"Task ID {task.id} ('{task.title}') has no assignees. Skipping reminder.")
                continue

            for assignment in task.assignments:
                if assignment.is_active and assignment.user:
                    try:
                        logger.info(f"Sending reminder for task ID {task.id} ('{task.title}') to user ID {assignment.user_id}.")
                        # await notification_service.send_task_deadline_reminder(user=assignment.user, task=task)
                        logger.info(f"SIMULATED REMINDER (to user {assignment.user.username}): Task '{task.title}' in group '{task.group.name}' is due at {task.due_date}.")

                        reminders_sent_count += 1

                        if hasattr(task, 'last_reminder_sent_at'):
                            task.last_reminder_sent_at = now
                            self.db_session.add(task)
                        else:
                            logger.warning(f"Task ID {task.id} missing 'last_reminder_sent_at' field.")

                    except Exception as e:
                        logger.error(f"Error sending reminder for task ID {task.id} to user ID {assignment.user_id}: {e}", exc_info=True)
                        # Do not rollback all reminders if one fails

        if reminders_sent_count > 0 and any(hasattr(t, 'last_reminder_sent_at') for t in tasks_to_remind_db):
            try:
                await self.commit()
                logger.info(f"Successfully sent {reminders_sent_count} task reminders and updated timestamps.")
            except Exception as e:
                logger.error(f"Error committing task reminder updates: {e}", exc_info=True)
                await self.rollback()
        elif reminders_sent_count > 0:
             logger.info(f"Successfully sent {reminders_sent_count} task reminders (no timestamps updated as field missing).")
        else:
            logger.info("No task reminders to send at this time.")

        return reminders_sent_count

logger.info("TaskSchedulingService class defined.")
