# backend/app/src/services/tasks/review.py
# import logging # Замінено на централізований логер
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, noload
from sqlalchemy.exc import IntegrityError

# Повні шляхи імпорту
from backend.app.src.services.base import BaseService
from backend.app.src.models.tasks.review import TaskReview  # Модель SQLAlchemy TaskReview
from backend.app.src.models.tasks.task import Task  # Для контексту завдання
# from backend.app.src.models.tasks.event import Event # Якщо відгуки можуть бути і для подій
from backend.app.src.models.auth.user import User  # Для контексту користувача (рецензента)
from backend.app.src.models.tasks.completion import \
    TaskCompletion  # Відгуки можуть бути пов'язані з конкретним виконанням

from backend.app.src.schemas.tasks.review import (  # Схеми Pydantic
    TaskReviewCreate,
    TaskReviewUpdate,
    TaskReviewResponse
)
from backend.app.src.config.logging import logger  # Централізований логер
from backend.app.src.config import settings as global_settings  # Для доступу до конфігурацій (наприклад, DEBUG)


class TaskReviewService(BaseService):
    """
    Сервіс для управління відгуками та оцінками користувачів щодо завдань (або подій).
    Обробляє створення, отримання, оновлення та видалення відгуків.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        logger.info("TaskReviewService ініціалізовано.")

    async def _get_orm_review_with_relations(self, review_id: UUID) -> Optional[TaskReview]:
        """Внутрішній метод для отримання ORM моделі TaskReview з усіма зв'язками."""
        stmt = select(TaskReview).options(
            selectinload(TaskReview.reviewer_user).options(selectinload(User.user_type)),
            selectinload(TaskReview.task).options(
                selectinload(Task.task_type), selectinload(Task.status), selectinload(Task.group)
            ),
            selectinload(TaskReview.completion).options(  # Якщо відгук пов'язаний з виконанням
                selectinload(TaskCompletion.user).options(selectinload(User.user_type))  # Користувач, що виконав
            )
        ).where(TaskReview.id == review_id)
        return (await self.db_session.execute(stmt)).scalar_one_or_none()

    async def create_task_review(
            self,
            task_id: UUID,
            reviewer_user_id: UUID,
            review_data: TaskReviewCreate,
            completion_id: Optional[UUID] = None  # Опціонально, якщо відгук стосується конкретного виконання
    ) -> TaskReviewResponse:
        """
        Створює новий відгук для завдання.

        :param task_id: ID завдання, для якого створюється відгук.
        :param reviewer_user_id: ID користувача, який залишає відгук.
        :param review_data: Дані для створення відгуку (оцінка, коментар).
        :param completion_id: Опціональний ID виконання завдання, до якого відноситься відгук.
        :return: Pydantic схема TaskReviewResponse створеного відгуку.
        :raises ValueError: Якщо завдання, рецензента або виконання не знайдено, або якщо користувач вже залишив відгук (якщо це заборонено). # i18n
        """
        logger.debug(f"Користувач ID '{reviewer_user_id}' намагається створити відгук для завдання ID '{task_id}'.")

        if not await self.db_session.get(Task, task_id):
            raise ValueError(f"Завдання з ID '{task_id}' не знайдено.")  # i18n
        if not await self.db_session.get(User, reviewer_user_id):
            raise ValueError(f"Рецензента з ID '{reviewer_user_id}' не знайдено.")  # i18n

        if completion_id:
            completion = await self.db_session.get(TaskCompletion, completion_id)
            if not completion:
                raise ValueError(f"Виконання завдання з ID '{completion_id}' не знайдено.")  # i18n
            if completion.task_id != task_id:
                # i18n
                raise ValueError(f"Виконання ID '{completion_id}' не належить завданню ID '{task_id}'.")
            # TODO: Уточнити бізнес-правила: чи може користувач залишати відгук на власне виконання?
            #  Чи може залишати відгук тільки той, хто перевіряв (reviewed_by_user_id з TaskCompletion)?
            #  Поточна логіка дозволяє будь-кому (reviewer_user_id) залишити відгук на будь-яке completion_id.

        # TODO: Реалізувати політику "один відгук на користувача" (на завдання або на виконання).
        #  Якщо відгук один на завдання від користувача:
        # existing_review_stmt = select(TaskReview.id).where(
        #     TaskReview.task_id == task_id,
        #     TaskReview.reviewer_user_id == reviewer_user_id
        # )
        #  Якщо відгук один на конкретне виконання від користувача:
        # if completion_id:
        #     existing_review_stmt = existing_review_stmt.where(TaskReview.completion_id == completion_id)
        # else: # Якщо відгук на завдання в цілому, а не на виконання, і completion_id не надано
        #     existing_review_stmt = existing_review_stmt.where(TaskReview.completion_id.is_(None))

        # if (await self.db_session.execute(existing_review_stmt)).scalar_one_or_none():
        #     context_msg = f"виконання ID '{completion_id}'" if completion_id else f"завдання ID '{task_id}'" # i18n
        #     raise ValueError(f"Користувач ID '{reviewer_user_id}' вже залишив відгук для {context_msg}.") # i18n

        new_review_db = TaskReview(
            **review_data.model_dump(),  # Pydantic v2
            task_id=task_id,
            reviewer_user_id=reviewer_user_id,
            completion_id=completion_id
            # `created_at`, `updated_at` встановлюються автоматично моделлю
        )
        self.db_session.add(new_review_db)
        try:
            await self.commit()
            refreshed_review = await self._get_orm_review_with_relations(new_review_db.id)
            if not refreshed_review: raise RuntimeError("Не вдалося отримати створений відгук.")  # i18n
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Помилка цілісності при створенні відгуку для завдання ID '{task_id}': {e}",
                         exc_info=global_settings.DEBUG)
            # i18n
            raise ValueError(f"Не вдалося створити відгук через конфлікт даних: {e}")

        logger.info(
            f"Відгук ID: {refreshed_review.id} успішно створено для завдання ID '{task_id}' користувачем ID '{reviewer_user_id}'.")
        return TaskReviewResponse.model_validate(refreshed_review)  # Pydantic v2

    async def get_review_by_id(self, review_id: UUID) -> Optional[TaskReviewResponse]:
        """Отримує відгук за його ID."""
        logger.debug(f"Спроба отримання відгуку на завдання за ID: {review_id}")
        review_db = await self._get_orm_review_with_relations(review_id)
        if review_db:
            logger.info(f"Відгук на завдання з ID '{review_id}' знайдено.")
            return TaskReviewResponse.model_validate(review_db)  # Pydantic v2
        logger.info(f"Відгук на завдання з ID '{review_id}' не знайдено.")
        return None

    async def update_task_review(
            self, review_id: UUID, review_update_data: TaskReviewUpdate, current_user_id: UUID
    ) -> Optional[TaskReviewResponse]:
        """
        Оновлює існуючий відгук на завдання.
        Дозволяє оновлювати тільки власні відгуки (якщо не адмін/суперюзер).
        """
        logger.debug(f"Користувач ID '{current_user_id}' намагається оновити відгук ID: {review_id}")

        review_db = await self.db_session.get(TaskReview,
                                              review_id)  # Не завантажуємо зв'язки для простої перевірки власника
        if not review_db:
            logger.warning(f"Відгук ID '{review_id}' не знайдено для оновлення.")
            return None

        # TODO: Додати перевірку прав адміністратора/суперкористувача для оновлення чужих відгуків.
        if review_db.reviewer_user_id != current_user_id:
            logger.error(
                f"Користувач ID '{current_user_id}' не авторизований для оновлення відгуку ID '{review_id}' (власник: {review_db.reviewer_user_id}).")
            # i18n
            raise PermissionError("Ви не маєте дозволу на оновлення цього відгуку.")

        update_data = review_update_data.model_dump(exclude_unset=True)  # Pydantic v2
        for field, value in update_data.items():
            setattr(review_db, field, value)

        review_db.updated_at = datetime.now(timezone.utc)  # Явне оновлення

        self.db_session.add(review_db)
        await self.commit()

        # Отримуємо оновлений запис з усіма зв'язками для відповіді
        updated_review = await self._get_orm_review_with_relations(review_id)
        if not updated_review: raise RuntimeError("Не вдалося отримати оновлений відгук.")  # i18n

        logger.info(f"Відгук ID '{review_id}' успішно оновлено користувачем ID '{current_user_id}'.")
        return TaskReviewResponse.model_validate(updated_review)  # Pydantic v2

    async def delete_task_review(self, review_id: UUID, current_user_id: UUID) -> bool:
        """
        Видаляє відгук на завдання.
        Дозволяє видаляти тільки власні відгуки (якщо не адмін/суперюзер).
        """
        logger.debug(f"Користувач ID '{current_user_id}' намагається видалити відгук ID: {review_id}")

        review_db = await self.db_session.get(TaskReview, review_id)
        if not review_db:
            logger.warning(f"Відгук ID '{review_id}' не знайдено для видалення.")
            return False

        # TODO: Додати перевірку прав адміністратора/суперкористувача для видалення чужих відгуків.
        if review_db.reviewer_user_id != current_user_id:
            logger.warning(
                f"Користувач ID '{current_user_id}' не є власником відгуку ID '{review_id}'. Видалення заборонено.")
            # i18n
            raise PermissionError("Ви можете видаляти тільки власні відгуки.")

        await self.db_session.delete(review_db)
        await self.commit()
        logger.info(f"Відгук ID '{review_id}' успішно видалено користувачем ID '{current_user_id}'.")
        return True

    async def list_reviews_for_task(self, task_id: UUID, skip: int = 0, limit: int = 100) -> List[TaskReviewResponse]:
        """Перелічує всі відгуки для конкретного завдання."""
        logger.debug(f"Перелік відгуків для завдання ID: {task_id}, пропустити={skip}, ліміт={limit}")

        stmt = select(TaskReview).options(
            selectinload(TaskReview.reviewer_user).options(selectinload(User.user_type)),
            selectinload(TaskReview.task).options(noload("*")),  # Завдання вже відоме
            selectinload(TaskReview.completion)  # Опціонально, може бути None
        ).where(TaskReview.task_id == task_id).order_by(TaskReview.created_at.desc()).offset(skip).limit(limit)

        reviews_db = (await self.db_session.execute(stmt)).scalars().unique().all()

        response_list = [TaskReviewResponse.model_validate(r) for r in reviews_db]  # Pydantic v2
        logger.info(f"Отримано {len(response_list)} відгуків для завдання ID '{task_id}'.")
        return response_list

    async def list_reviews_by_user(self, reviewer_user_id: UUID, skip: int = 0, limit: int = 100) -> List[
        TaskReviewResponse]:
        """Перелічує всі відгуки, залишені конкретним користувачем."""
        logger.debug(f"Перелік відгуків користувачем ID: {reviewer_user_id}, пропустити={skip}, ліміт={limit}")

        stmt = select(TaskReview).options(
            selectinload(TaskReview.reviewer_user).options(noload("*")),  # Рецензент вже відомий
            selectinload(TaskReview.task).options(selectinload(Task.task_type), selectinload(Task.group)),
            selectinload(TaskReview.completion)
        ).where(TaskReview.reviewer_user_id == reviewer_user_id).order_by(TaskReview.created_at.desc()).offset(
            skip).limit(limit)

        reviews_db = (await self.db_session.execute(stmt)).scalars().unique().all()
        response_list = [TaskReviewResponse.model_validate(r) for r in reviews_db]  # Pydantic v2
        logger.info(f"Отримано {len(response_list)} відгуків користувачем ID '{reviewer_user_id}'.")
        return response_list


logger.debug(f"{TaskReviewService.__name__} (сервіс відгуків на завдання) успішно визначено.")
