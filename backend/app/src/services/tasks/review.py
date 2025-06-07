# backend/app/src/services/tasks/review.py
import logging
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from app.src.services.base import BaseService
from app.src.models.tasks.review import TaskReview # SQLAlchemy TaskReview model
from app.src.models.tasks.task import Task # For task context
# from app.src.models.tasks.event import Event # If reviews can be for events too
from app.src.models.auth.user import User # For user context (reviewer)
from app.src.models.tasks.completion import TaskCompletion # Reviews might be linked to a specific completion

from app.src.schemas.tasks.review import ( # Pydantic Schemas
    TaskReviewCreate,
    TaskReviewUpdate,
    TaskReviewResponse
)

# Initialize logger for this module
logger = logging.getLogger(__name__)

class TaskReviewService(BaseService):
    """
    Service for managing user reviews and ratings on tasks (or events).
    Handles creation, retrieval, update, and deletion of reviews.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        logger.info("TaskReviewService initialized.")

    async def create_task_review(
        self,
        task_id: UUID,
        reviewer_user_id: UUID,
        review_data: TaskReviewCreate,
        completion_id: Optional[UUID] = None
    ) -> TaskReviewResponse:
        logger.debug(f"User ID '{reviewer_user_id}' attempting to create review for task ID '{task_id}'.")

        task = await self.db_session.get(Task, task_id)
        if not task: raise ValueError(f"Task with ID '{task_id}' not found.")

        reviewer = await self.db_session.get(User, reviewer_user_id)
        if not reviewer: raise ValueError(f"Reviewer user with ID '{reviewer_user_id}' not found.")

        if completion_id:
            completion = await self.db_session.get(TaskCompletion, completion_id)
            if not completion: raise ValueError(f"TaskCompletion with ID '{completion_id}' not found.")
            # Ensure completion matches task and potentially reviewer, depending on rules
            if completion.task_id != task_id:
                 raise ValueError(f"Completion ID '{completion_id}' does not belong to task ID '{task_id}'.")
            # Example rule: if review is for a completion, only the completer can "self-review" or it's a peer review.
            # if completion.user_id != reviewer_user_id: # This rule depends on the system's design for reviews.
            #     logger.warning(f"Reviewer {reviewer_user_id} is not the completer {completion.user_id} for this completion-linked review.")
            #     # This might be allowed or disallowed based on business logic. For now, allowing.

        # Business Logic: Check if user has already reviewed this task/completion (if one review per user)
        # existing_review_stmt = select(TaskReview.id).where( # Select only ID for existence check
        #     TaskReview.task_id == task_id,
        #     TaskReview.reviewer_user_id == reviewer_user_id
        # )
        # if completion_id: # If review is per completion
        #     existing_review_stmt = existing_review_stmt.where(TaskReview.completion_id == completion_id)

        # if (await self.db_session.execute(existing_review_stmt)).scalar_one_or_none():
        #     # Customize error based on whether it's per task or per completion
        #     context_msg = f"completion ID '{completion_id}'" if completion_id else f"task ID '{task_id}'"
        #     raise ValueError(f"User ID '{reviewer_user_id}' has already reviewed {context_msg}.")


        review_db_data = review_data.dict()

        new_review_db = TaskReview(
            task_id=task_id,
            reviewer_user_id=reviewer_user_id,
            completion_id=completion_id,
            **review_db_data
        )

        self.db_session.add(new_review_db)
        try:
            await self.commit()
            await self.db_session.refresh(new_review_db, attribute_names=['reviewer', 'task', 'completion'])
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Integrity error creating review for task ID '{task_id}': {e}", exc_info=True)
            raise ValueError(f"Could not create review due to a data conflict: {e}")

        logger.info(f"Review created successfully (ID: {new_review_db.id}) for task ID '{task_id}' by user ID '{reviewer_user_id}'.")
        # return TaskReviewResponse.model_validate(new_review_db) # Pydantic v2
        return TaskReviewResponse.from_orm(new_review_db) # Pydantic v1

    async def get_review_by_id(self, review_id: UUID) -> Optional[TaskReviewResponse]:
        logger.debug(f"Attempting to retrieve task review by ID: {review_id}")

        stmt = select(TaskReview).options(
            selectinload(TaskReview.reviewer).options(selectinload(User.user_type)),
            selectinload(TaskReview.task),
            selectinload(TaskReview.completion)
        ).where(TaskReview.id == review_id)

        review_db = (await self.db_session.execute(stmt)).scalar_one_or_none()

        if review_db:
            logger.info(f"Task review with ID '{review_id}' found.")
            # return TaskReviewResponse.model_validate(review_db) # Pydantic v2
            return TaskReviewResponse.from_orm(review_db) # Pydantic v1

        logger.info(f"Task review with ID '{review_id}' not found.")
        return None

    async def update_task_review(
        self,
        review_id: UUID,
        review_update_data: TaskReviewUpdate,
        current_user_id: UUID
    ) -> Optional[TaskReviewResponse]:
        logger.debug(f"User ID '{current_user_id}' attempting to update task review ID: {review_id}")

        # Load reviewer relationship for permission check
        review_db = await self.db_session.get(TaskReview, review_id, options=[selectinload(TaskReview.reviewer)])


        if not review_db:
            logger.warning(f"Task review ID '{review_id}' not found for update.")
            return None

        if review_db.reviewer_user_id != current_user_id:
            logger.error(f"User ID '{current_user_id}' is not authorized to update review ID '{review_id}' (owner: {review_db.reviewer_user_id}).")
            raise ValueError("You are not authorized to update this review.")

        update_data = review_update_data.dict(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(review_db, field):
                setattr(review_db, field, value)
            else:
                logger.warning(f"Field '{field}' not found on TaskReview model for update of review ID '{review_id}'.")

        if hasattr(review_db, 'updated_at'): # Check if model has updated_at
             review_db.updated_at = datetime.now(timezone.utc)

        self.db_session.add(review_db)
        await self.commit()
        # Refresh all relevant fields for the response
        await self.db_session.refresh(review_db, attribute_names=['reviewer', 'task', 'completion'])

        logger.info(f"Task review ID '{review_id}' updated successfully by user ID '{current_user_id}'.")
        # return TaskReviewResponse.model_validate(review_db) # Pydantic v2
        return TaskReviewResponse.from_orm(review_db) # Pydantic v1

    async def delete_task_review(self, review_id: UUID, current_user_id: UUID) -> bool:
        logger.debug(f"User ID '{current_user_id}' attempting to delete task review ID: {review_id}")

        review_db = await self.db_session.get(TaskReview, review_id)
        if not review_db:
            logger.warning(f"Task review ID '{review_id}' not found for deletion.")
            return False

        # Simplified permission: only owner can delete. Admin/moderator logic would be more complex.
        if review_db.reviewer_user_id != current_user_id:
             logger.warning(f"User ID '{current_user_id}' is not the owner of review ID '{review_id}'. Deletion denied.")
             raise ValueError("You can only delete your own reviews.")

        await self.db_session.delete(review_db)
        await self.commit()
        logger.info(f"Task review ID '{review_id}' deleted successfully by user ID '{current_user_id}'.")
        return True

    async def list_reviews_for_task(self, task_id: UUID, skip: int = 0, limit: int = 100) -> List[TaskReviewResponse]:
        logger.debug(f"Listing reviews for task ID: {task_id}, skip={skip}, limit={limit}")

        stmt = select(TaskReview).options(
            selectinload(TaskReview.reviewer).options(selectinload(User.user_type)),
            selectinload(TaskReview.task),
            selectinload(TaskReview.completion)
        ).where(TaskReview.task_id == task_id).order_by(TaskReview.created_at.desc()).offset(skip).limit(limit)

        reviews_db = (await self.db_session.execute(stmt)).scalars().unique().all()

        # response_list = [TaskReviewResponse.model_validate(r) for r in reviews_db] # Pydantic v2
        response_list = [TaskReviewResponse.from_orm(r) for r in reviews_db] # Pydantic v1
        logger.info(f"Retrieved {len(response_list)} reviews for task ID '{task_id}'.")
        return response_list

    async def list_reviews_by_user(self, reviewer_user_id: UUID, skip: int = 0, limit: int = 100) -> List[TaskReviewResponse]:
        logger.debug(f"Listing reviews by user ID: {reviewer_user_id}, skip={skip}, limit={limit}")

        stmt = select(TaskReview).options(
            selectinload(TaskReview.reviewer).options(selectinload(User.user_type)),
            selectinload(TaskReview.task).options(selectinload(Task.task_type)),
            selectinload(TaskReview.completion)
        ).where(TaskReview.reviewer_user_id == reviewer_user_id).order_by(TaskReview.created_at.desc()).offset(skip).limit(limit)

        reviews_db = (await self.db_session.execute(stmt)).scalars().unique().all()

        # response_list = [TaskReviewResponse.model_validate(r) for r in reviews_db] # Pydantic v2
        response_list = [TaskReviewResponse.from_orm(r) for r in reviews_db] # Pydantic v1
        logger.info(f"Retrieved {len(response_list)} reviews by user ID '{reviewer_user_id}'.")
        return response_list

logger.info("TaskReviewService class defined.")
