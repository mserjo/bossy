# backend/app/src/schemas/tasks/review.py
"""
Pydantic схеми для сутності "Відгук на Завдання" (TaskReview).

Цей модуль визначає схеми для:
- Базового представлення відгуку на завдання (`TaskReviewBaseSchema`).
- Створення нового відгуку (`TaskReviewCreateSchema`).
- Оновлення існуючого відгуку (`TaskReviewUpdateSchema`).
- Представлення даних про відгук у відповідях API (`TaskReviewSchema`).
"""
from datetime import datetime
from typing import Optional

from pydantic import Field

# Абсолютний імпорт базових схем та міксинів
from backend.app.src.schemas.base import BaseSchema, IDSchemaMixin, TimestampedSchemaMixin
from backend.app.src.schemas.auth.user import UserPublicProfileSchema  # Для представлення користувача
from datetime import timedelta
from backend.app.src.config.logging import get_logger
from backend.app.src.core.i18n import _ # Added import
logger = get_logger(__name__)


class TaskReviewBaseSchema(BaseSchema):
    """
    Базова схема для полів відгуку на завдання.
    `task_id` та `user_id` зазвичай визначаються з контексту.
    """
    # task_id: int = Field(description="Ідентифікатор завдання, до якого залишено відгук.") # Зазвичай з URL
    # user_id: int = Field(description="Ідентифікатор користувача, який залишив відгук.") # Зазвичай поточний користувач

    rating: Optional[int] = Field(
        None,
        ge=1,
        le=5,
        description=_("task_review.fields.rating.description")
    )
    comment: Optional[str] = Field(
        None,
        description=_("task_review.fields.comment.description")
    )

    # model_config успадковується з BaseSchema (from_attributes=True)


class TaskReviewCreateSchema(TaskReviewBaseSchema):
    """
    Схема для створення нового відгуку на завдання.
    `task_id` зазвичай з параметра шляху, `user_id` - поточний користувач.
    """
    # Успадковує rating та comment.
    # Валідація, що хоча б одне з полів (rating або comment) має бути надане,
    # може бути додана за допомогою model_validator.
    pass


class TaskReviewUpdateSchema(
    BaseSchema):  # Не успадковує TaskReviewBaseSchema, щоб уникнути успадкування полів, які не можна змінювати
    """
    Схема для оновлення існуючого відгуку на завдання.
    Дозволяє оновлювати рейтинг та/або коментар.
    """
    rating: Optional[int] = Field(
        None,
        ge=1,
        le=5,
        description=_("task_review.fields.rating.description") # Reuse from base
    )
    comment: Optional[str] = Field(
        None,
        description=_("task_review.fields.comment.description") # Reuse from base
    )
    # Валідація, що хоча б одне поле надано для оновлення,
    # може бути додана за допомогою model_validator.


class TaskReviewSchema(TaskReviewBaseSchema, IDSchemaMixin, TimestampedSchemaMixin):
    """
    Схема для представлення даних про відгук на завдання у відповідях API.
    """
    # id, created_at, updated_at успадковані.
    # rating, comment успадковані.
    # task_id та user_id потрібно додати явно, оскільки вони не в TaskReviewBaseSchema.
    task_id: int = Field(description=_("task_review.response.fields.task_id.description"))
    user_id: int = Field(description=_("task_review.response.fields.user_id.description"))

    user: Optional[UserPublicProfileSchema] = Field(None,
                                                    description=_("task_review.response.fields.user.description"))
    # Можна додати поле `task: Optional[TaskBriefSchema] = None`, якщо потрібно.


if __name__ == "__main__":
    # Демонстраційний блок для схем відгуків на завдання.
    logger.info("--- Pydantic Схеми для Відгуків на Завдання (TaskReview) ---")

    logger.info("\nTaskReviewCreateSchema (приклад для створення):")
    create_review_data = {
        "rating": 5,
        "comment": "Дуже корисне завдання, дякую!"  # TODO i18n
    }
    create_review_instance = TaskReviewCreateSchema(**create_review_data)
    logger.info(create_review_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nTaskReviewUpdateSchema (приклад для оновлення):")
    update_review_data = {
        "comment": "Оновлений коментар: завдання було справді корисним для команди."  # TODO i18n
    }
    update_review_instance = TaskReviewUpdateSchema(**update_review_data)
    logger.info(update_review_instance.model_dump_json(indent=2, exclude_none=True))
    try:
        TaskReviewUpdateSchema(rating=7)  # Невалідний рейтинг
    except Exception as e:
        logger.info(f"Помилка валідації TaskReviewUpdateSchema (очікувано): {e}")

    logger.info("\nTaskReviewSchema (приклад відповіді API):")
    review_response_data = {
        "id": 1,
        "task_id": 10,
        "user_id": 101,
        "rating": 4,
        "comment": "Гарне завдання, але можна було б чіткіше сформулювати умови.",  # TODO i18n
        "created_at": datetime.now() - timedelta(days=1),
        "updated_at": datetime.now(),
        "user": {"id": 101, "name": "Рецензент Користувач"}  # TODO i18n
    }
    review_response_instance = TaskReviewSchema(**review_response_data)
    logger.info(review_response_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nПримітка: Ці схеми використовуються для валідації та серіалізації даних відгуків на завдання.")

# Потрібно для timedelta в __main__ - вже переміщено нагору
# from datetime import timedelta
