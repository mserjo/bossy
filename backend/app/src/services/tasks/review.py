# backend/app/src/services/tasks/review.py
# -*- coding: utf-8 -*-
from typing import List, Optional
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload, noload
from sqlalchemy.exc import IntegrityError

from backend.app.src.services.base import BaseService
from backend.app.src.models.tasks.review import TaskReview
from backend.app.src.repositories.tasks.review_repository import TaskReviewRepository # Імпорт репозиторію
from backend.app.src.models.tasks.task import Task
from backend.app.src.models.auth.user import User
from backend.app.src.models.tasks.completion import TaskCompletion

from backend.app.src.schemas.tasks.review import (
    TaskReviewCreate,
    TaskReviewUpdate,
    TaskReviewResponse
)
from backend.app.src.config import settings as global_settings
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)


class TaskReviewService(BaseService):
    """
    Сервіс для управління відгуками та оцінками користувачів щодо завдань (або подій).
    Обробляє створення, отримання, оновлення та видалення відгуків.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        self.review_repo = TaskReviewRepository() # Ініціалізація репозиторію
        logger.info("TaskReviewService ініціалізовано.")

    async def _get_orm_review_with_relations(self, review_id: int) -> Optional[TaskReview]:
        """Внутрішній метод для отримання ORM моделі TaskReview з усіма зв'язками."""
        # Залишаємо прямий запит для гнучкого selectinload
        stmt = select(TaskReview).options(
            selectinload(TaskReview.reviewer_user).options(selectinload(User.user_type)),
            selectinload(TaskReview.task).options(
                selectinload(Task.task_type), selectinload(Task.status), selectinload(Task.group)
            ),
            selectinload(TaskReview.completion).options(
                selectinload(TaskCompletion.user).options(selectinload(User.user_type))
            )
        ).where(TaskReview.id == review_id)
        return (await self.db_session.execute(stmt)).scalar_one_or_none()

    async def create_task_review(
            self,
            task_id: int,
            reviewer_user_id: int,
            review_data: TaskReviewCreate,
            completion_id: Optional[int] = None
    ) -> TaskReviewResponse:
        """
        Створює новий відгук для завдання.
        """
        logger.debug(f"Користувач ID '{reviewer_user_id}' намагається створити відгук для завдання ID '{task_id}'.")

        # Перевірки існування FK залишаються в сервісі
        if not await self.db_session.get(Task, task_id):
            raise ValueError(f"Завдання з ID '{task_id}' не знайдено.")
        if not await self.db_session.get(User, reviewer_user_id):
            raise ValueError(f"Рецензента з ID '{reviewer_user_id}' не знайдено.")

        if completion_id:
            completion = await self.db_session.get(TaskCompletion, completion_id)
            if not completion:
                raise ValueError(f"Виконання завдання з ID '{completion_id}' не знайдено.")
            if completion.task_id != task_id:
                raise ValueError(f"Виконання ID '{completion_id}' не належить завданню ID '{task_id}'.")

        # Перевірка "один відгук на користувача" через репозиторій
        # (Припускаючи, що UniqueConstraint в моделі (task_id, user_id) або (task_id, user_id, completion_id))
        # Якщо constraint (task_id, reviewer_user_id), то:
        existing_review = await self.review_repo.get_by_task_and_user(
             session=self.db_session, task_id=task_id, user_id=reviewer_user_id
        )
        # TODO: Розширити логіку, якщо відгук унікальний по (task_id, reviewer_user_id, completion_id)
        if existing_review and (completion_id is None or existing_review.completion_id == completion_id) :
             context_msg = f"виконання ID '{completion_id}'" if completion_id else f"завдання ID '{task_id}'"
             raise ValueError(f"Користувач ID '{reviewer_user_id}' вже залишив відгук для {context_msg}.")

        # Створення через репозиторій
        # TaskReviewCreateSchema має включати task_id, reviewer_user_id, completion_id
        # Поточна review_data (TaskReviewCreate) їх не має, вони передаються окремо.
        # Потрібно або додати їх в TaskReviewCreate, або створити TaskReviewCreateSchema тут.

        create_schema_data = review_data.model_dump()
        create_schema_data['task_id'] = task_id
        create_schema_data['reviewer_user_id'] = reviewer_user_id
        create_schema_data['completion_id'] = completion_id

        # Припускаємо, що TaskReviewCreateSchema = TaskReviewCreate (або сумісні)
        # Якщо TaskReviewCreate не має цих полів, а TaskReviewCreateSchema (для репо) має, то:
        from backend.app.src.schemas.tasks.review import TaskReviewCreateSchema as RepoCreateSchema
        final_create_data = RepoCreateSchema(**create_schema_data)


        try:
            new_review_db = await self.review_repo.create(session=self.db_session, obj_in=final_create_data)
            await self.commit()
            refreshed_review = await self._get_orm_review_with_relations(new_review_db.id) # Для завантаження зв'язків
            if not refreshed_review: raise RuntimeError("Не вдалося отримати створений відгук.")
        except IntegrityError as e: # Може бути через UniqueConstraint в моделі
            await self.rollback()
            logger.error(f"Помилка цілісності при створенні відгуку для завдання ID '{task_id}': {e}",
                         exc_info=global_settings.DEBUG)
            raise ValueError(f"Не вдалося створити відгук через конфлікт даних: {e}")

        logger.info(
            f"Відгук ID: {refreshed_review.id} успішно створено для завдання ID '{task_id}' користувачем ID '{reviewer_user_id}'.")
        return TaskReviewResponse.model_validate(refreshed_review)

    async def get_review_by_id(self, review_id: int) -> Optional[TaskReviewResponse]:
        """Отримує відгук за його ID."""
        logger.debug(f"Спроба отримання відгуку на завдання за ID: {review_id}")
        # Використовуємо _get_orm_review_with_relations для завантаження зв'язків
        review_db = await self._get_orm_review_with_relations(review_id)
        if review_db:
            logger.info(f"Відгук на завдання з ID '{review_id}' знайдено.")
            return TaskReviewResponse.model_validate(review_db)
        logger.info(f"Відгук на завдання з ID '{review_id}' не знайдено.")
        return None

    async def update_task_review(
            self, review_id: int, review_update_data: TaskReviewUpdate, current_user_id: int
    ) -> Optional[TaskReviewResponse]:
        """
        Оновлює існуючий відгук на завдання.
        Дозволяє оновлювати тільки власні відгуки (якщо не адмін/суперюзер).
        """
        logger.debug(f"Користувач ID '{current_user_id}' намагається оновити відгук ID: {review_id}")

        review_db = await self.review_repo.get(session=self.db_session, id=review_id) # Використання репозиторію
        if not review_db:
            logger.warning(f"Відгук ID '{review_id}' не знайдено для оновлення.")
            return None

        if review_db.reviewer_user_id != current_user_id: # Перевірка власності залишається в сервісі
            logger.error(
                f"Користувач ID '{current_user_id}' не авторизований для оновлення відгуку ID '{review_id}' (власник: {review_db.reviewer_user_id}).")
            raise PermissionError("Ви не маєте дозволу на оновлення цього відгуку.")

        # updated_at оновлюється автоматично через TimestampedMixin в BaseRepository.update
        updated_review_db = await self.review_repo.update(
            session=self.db_session, db_obj=review_db, obj_in=review_update_data
        )
        if not updated_review_db: # Малоймовірно, якщо update не кинув виняток
             logger.error(f"Не вдалося оновити відгук ID {review_id} через репозиторій.")
             raise RuntimeError("Помилка оновлення відгуку.")

        await self.commit()

        updated_review_response = await self._get_orm_review_with_relations(updated_review_db.id) # Перезавантажуємо зі зв'язками
        if not updated_review_response: raise RuntimeError("Не вдалося отримати оновлений відгук зі зв'язками.")

        logger.info(f"Відгук ID '{review_id}' успішно оновлено користувачем ID '{current_user_id}'.")
        return TaskReviewResponse.model_validate(updated_review_response)

    async def delete_task_review(self, review_id: int, current_user_id: int) -> bool:
        """
        Видаляє відгук на завдання.
        Дозволяє видаляти тільки власні відгуки (якщо не адмін/суперюзер).
        """
        logger.debug(f"Користувач ID '{current_user_id}' намагається видалити відгук ID: {review_id}")

        review_db = await self.review_repo.get(session=self.db_session, id=review_id) # Використання репозиторію
        if not review_db:
            logger.warning(f"Відгук ID '{review_id}' не знайдено для видалення.")
            return False

        if review_db.reviewer_user_id != current_user_id: # Перевірка власності залишається в сервісі
            logger.warning(
                f"Користувач ID '{current_user_id}' не є власником відгуку ID '{review_id}'. Видалення заборонено.")
            raise PermissionError("Ви можете видаляти тільки власні відгуки.")

        deleted = await self.review_repo.remove(session=self.db_session, id=review_id) # Використання репозиторію
        if deleted:
            await self.commit()
            logger.info(f"Відгук ID '{review_id}' успішно видалено користувачем ID '{current_user_id}'.")
            return True
        logger.error(f"Не вдалося видалити відгук ID {review_id} через репозиторій.")
        return False # Якщо remove повернув None

    async def list_reviews_for_task(self, task_id: int, skip: int = 0, limit: int = 100) -> List[TaskReviewResponse]: # Змінено UUID на int
        """Перелічує всі відгуки для конкретного завдання."""
        logger.debug(f"Перелік відгуків для завдання ID: {task_id}, пропустити={skip}, ліміт={limit}")

        reviews_db_list, _ = await self.review_repo.get_reviews_for_task(
            session=self.db_session, task_id=task_id, skip=skip, limit=limit
        )
        # Потрібно завантажити зв'язки для кожного відгуку
        response_list = []
        for review_base in reviews_db_list:
            detailed_review = await self._get_orm_review_with_relations(review_base.id)
            if detailed_review:
                response_list.append(TaskReviewResponse.model_validate(detailed_review))

        logger.info(f"Отримано {len(response_list)} відгуків для завдання ID '{task_id}'.")
        return response_list

    async def list_reviews_by_user(self, reviewer_user_id: int, skip: int = 0, limit: int = 100) -> List[ # Змінено UUID на int
        TaskReviewResponse]:
        """Перелічує всі відгуки, залишені конкретним користувачем."""
        logger.debug(f"Перелік відгуків користувачем ID: {reviewer_user_id}, пропустити={skip}, ліміт={limit}")

        reviews_db_list, _ = await self.review_repo.list_by_reviewer(
            session=self.db_session, reviewer_user_id=reviewer_user_id, skip=skip, limit=limit
        )

        response_list = []
        for review_base in reviews_db_list:
            detailed_review = await self._get_orm_review_with_relations(review_base.id)
            if detailed_review:
                response_list.append(TaskReviewResponse.model_validate(detailed_review))

        logger.info(f"Отримано {len(response_list)} відгуків користувачем ID '{reviewer_user_id}'.")
        return response_list


logger.debug(f"{TaskReviewService.__name__} (сервіс відгуків на завдання) успішно визначено.")
