# backend/app/src/services/tasks/task_review_service.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає сервіс `TaskReviewService` для управління відгуками та рейтингами на завдання.
"""
from typing import List, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore

from backend.app.src.models.tasks.review import TaskReviewModel
from backend.app.src.models.auth.user import UserModel
from backend.app.src.schemas.tasks.review import TaskReviewCreateSchema, TaskReviewUpdateSchema, TaskReviewSchema
from backend.app.src.repositories.tasks.review import TaskReviewRepository, task_review_repository
from backend.app.src.repositories.tasks.task import task_repository # Для перевірки існування завдання
# from backend.app.src.repositories.groups.group_settings import group_settings_repository # Для перевірки, чи ввімкнено відгуки
# from backend.app.src.services.groups.group_membership_service import group_membership_service # Для перевірки членства в групі
from backend.app.src.services.base import BaseService
from backend.app.src.core.exceptions import NotFoundException, ForbiddenException, BadRequestException
from backend.app.src.core.constants import USER_TYPE_SUPERADMIN


class TaskReviewService(BaseService[TaskReviewRepository]):
    """
    Сервіс для управління відгуками та рейтингами на завдання.
    """

    async def get_review_by_id(self, db: AsyncSession, review_id: uuid.UUID) -> TaskReviewModel:
        review = await self.repository.get(db, id=review_id)
        if not review:
            raise NotFoundException(f"Відгук з ID {review_id} не знайдено.")
        return review

    async def leave_review(
        self, db: AsyncSession, *, task_id: uuid.UUID, obj_in: TaskReviewCreateSchema, current_user: UserModel
    ) -> TaskReviewModel:
        """
        Дозволяє користувачеві залишити відгук/рейтинг на завдання.
        """
        task = await task_repository.get(db, id=task_id)
        if not task:
            raise NotFoundException(f"Завдання з ID {task_id} не знайдено.")

        # Перевірка, чи користувач є членом групи завдання
        from backend.app.src.services.groups.group_membership_service import group_membership_service # Відкладений імпорт
        membership = await group_membership_service.get_membership_by_user_and_group(db, user_id=current_user.id, group_id=task.group_id)
        if not membership:
            raise ForbiddenException("Лише члени групи можуть залишати відгуки на завдання цієї групи.")

        # TODO: Перевірити, чи ввімкнено відгуки в налаштуваннях групи
        # group_settings = await group_settings_repository.get_by_group_id(db, group_id=task.group_id)
        # if not group_settings or not group_settings.task_reviews_enabled:
        #     raise ForbiddenException("Відгуки для завдань у цій групі вимкнені.")

        # Перевірка, чи користувач вже не залишав відгук (якщо дозволено лише один)
        # Модель TaskReviewModel має UniqueConstraint('task_id', 'user_id')
        existing_review = await self.repository.get_review_by_task_and_user(db, task_id=task_id, user_id=current_user.id)
        if existing_review:
            raise BadRequestException("Ви вже залишили відгук на це завдання.")

        # Валідатор в TaskReviewCreateSchema перевіряє, що rating або comment є.

        # Використовуємо кастомний метод репозиторію
        return await self.repository.create_review(
            db, obj_in=obj_in, task_id=task_id, user_id=current_user.id
        )

    async def update_review(
        self, db: AsyncSession, *, review_id: uuid.UUID, obj_in: TaskReviewUpdateSchema, current_user: UserModel
    ) -> TaskReviewModel:
        """
        Оновлює існуючий відгук/рейтинг.
        Дозволено лише автору відгуку або адміністратору.
        """
        db_review = await self.get_review_by_id(db, review_id=review_id)

        # Перевірка прав
        can_update = False
        if db_review.user_id == current_user.id:
            can_update = True
        else:
            task = await task_repository.get(db, id=db_review.task_id) # Потрібна група завдання
            if task:
                from backend.app.src.services.groups.group_membership_service import group_membership_service
                if await group_membership_service.is_user_group_admin(db, user_id=current_user.id, group_id=task.group_id) or \
                   current_user.user_type_code == USER_TYPE_SUPERADMIN:
                    can_update = True

        if not can_update:
            raise ForbiddenException("Ви не маєте прав оновлювати цей відгук.")

        # Валідатор в TaskReviewUpdateSchema перевіряє, що хоча б одне поле передано.
        # І що не можна зробити так, щоб і rating, і comment були порожніми (це краще на сервісі).
        if obj_in.rating is None and (obj_in.comment is None or not obj_in.comment.strip()):
            # Якщо оновлення призведе до порожнього відгуку, перевіряємо поточний стан
            if (obj_in.rating is None and db_review.rating is not None and (obj_in.comment is None and db_review.comment is None)) or \
               (obj_in.comment is None and db_review.comment is not None and (obj_in.rating is None and db_review.rating is None)):
                 # Намагаються видалити останнє значуще поле
                 pass # Дозволяємо, якщо хоча б щось залишається або щось нове додається.
                      # Складніша логіка: якщо обидва стають None, то помилка.
            elif obj_in.rating is None and obj_in.comment is not None and not obj_in.comment.strip() and db_review.rating is None:
                 raise BadRequestException("Відгук не може бути повністю порожнім (ані рейтинг, ані коментар).")


        return await self.repository.update(db, db_obj=db_review, obj_in=obj_in)

    async def delete_review(
        self, db: AsyncSession, *, review_id: uuid.UUID, current_user: UserModel
    ) -> Optional[TaskReviewModel]:
        """Видаляє відгук."""
        db_review = await self.get_review_by_id(db, review_id=review_id)

        # Перевірка прав (автор, адмін групи, superuser)
        can_delete = False
        if db_review.user_id == current_user.id:
            can_delete = True
        else:
            task = await task_repository.get(db, id=db_review.task_id)
            if task:
                from backend.app.src.services.groups.group_membership_service import group_membership_service
                if await group_membership_service.is_user_group_admin(db, user_id=current_user.id, group_id=task.group_id) or \
                   current_user.user_type_code == USER_TYPE_SUPERADMIN:
                    can_delete = True

        if not can_delete:
            raise ForbiddenException("Ви не маєте прав видаляти цей відгук.")

        return await self.repository.delete(db, id=review_id)

task_review_service = TaskReviewService(task_review_repository)

# TODO: Реалізувати перевірку налаштування `task_reviews_enabled` в `GroupSettingsModel`.
# TODO: Додати логіку модерації відгуків, якщо `status_id` буде додано до `TaskReviewModel`.
# TODO: Покращити валідацію в `update_review`, щоб не дозволити зробити відгук повністю порожнім.
#
# Все виглядає як хороший початок для сервісу відгуків.
# Основні операції (створення, оновлення, видалення) з перевіркою прав.
# Використання `group_membership_service` для перевірки членства та адмінських прав.
