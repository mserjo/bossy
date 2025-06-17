# backend/app/src/schemas/gamification/rating.py
"""
Pydantic схеми для сутності "Рейтинг Користувача в Групі" (UserGroupRating).

Цей модуль визначає схеми для:
- Базового представлення запису про рейтинг (`UserGroupRatingBaseSchema`).
- Створення нового запису про рейтинг (зазвичай виконується сервісом) (`UserGroupRatingCreateSchema`).
- Оновлення існуючого запису про рейтинг (`UserGroupRatingUpdateSchema`).
- Представлення даних про рейтинг користувача у відповідях API (`UserGroupRatingSchema`).
"""
from datetime import datetime, date  # date для period_start_date, period_end_date
from typing import Optional, Any  # Any для тимчасових полів

from pydantic import Field

# Абсолютний імпорт базових схем та міксинів
from backend.app.src.schemas.base import BaseSchema, IDSchemaMixin, TimestampedSchemaMixin
from backend.app.src.config.logging import get_logger 
from backend.app.src.core.dicts import RatingType # Імпортовано RatingType Enum
logger = get_logger(__name__)

from datetime import timedelta # Moved import to top

# RatingType Enum імпортовано вище.

# Імпорти для конкретних схем
from backend.app.src.schemas.auth.user import UserPublicProfileSchema
from backend.app.src.schemas.groups.group import GroupSchema


# Placeholder assignments removed
# UserPublicProfileSchema = Any
# GroupBriefSchema = Any


class UserGroupRatingBaseSchema(BaseSchema):
    """
    Базова схема для полів запису про рейтинг користувача в групі.
    """
    user_id: int = Field(description="Ідентифікатор користувача.")
    group_id: int = Field(description="Ідентифікатор групи, в якій розраховано рейтинг.")
    rating_score: int = Field(default=0, description="Розрахований рейтинг або кількість балів користувача.")
    period_start_date: Optional[date] = Field(None,
                                              description="Дата початку періоду, за який розраховано рейтинг (якщо застосовно).")
    period_end_date: Optional[date] = Field(None,
                                            description="Дата кінця періоду, за який розраховано рейтинг (якщо застосовно).")
    rating_type: Optional[RatingType] = Field( # Використовує імпортований RatingType Enum
        None,
        # max_length=50, # Не потрібно для Enum
        description="Тип рейтингу (наприклад, 'monthly', 'overall', 'weekly').",
        examples=["monthly", "overall"]
    )
    # model_config успадковується з BaseSchema (from_attributes=True)


class UserGroupRatingCreateSchema(UserGroupRatingBaseSchema):
    """
    Схема для створення нового запису про рейтинг користувача.
    Зазвичай цей запис створюється або оновлюється автоматично сервісом гейміфікації.
    """
    # Успадковує всі поля від UserGroupRatingBaseSchema.
    # `updated_at` (як час останнього розрахунку) буде встановлено автоматично.
    pass


class UserGroupRatingUpdateSchema(
    BaseSchema):  # Не успадковує UserGroupRatingBaseSchema, щоб дозволити часткове оновлення
    """
    Схема для оновлення рейтингу користувача (наприклад, лише `rating_score`).
    """
    rating_score: Optional[int] = Field(None, description="Нове значення рейтингу/балів.")
    # Інші поля, такі як period_start_date, period_end_date, rating_type зазвичай не оновлюються
    # для існуючого запису рейтингу; замість цього створюється новий запис для нового періоду/типу.


class UserGroupRatingSchema(UserGroupRatingBaseSchema, IDSchemaMixin, TimestampedSchemaMixin):
    """
    Схема для представлення даних про рейтинг користувача в групі у відповідях API.
    Поле `updated_at` (з `TimestampedSchemaMixin`) позначає час останнього розрахунку рейтингу.
    """
    # id, created_at, updated_at успадковані.
    # user_id, group_id, rating_score, period_start_date, period_end_date, rating_type успадковані.

    user: Optional[UserPublicProfileSchema] = Field(None, description="Публічний профіль користувача.")
    group: Optional[GroupSchema] = Field(None, description="Коротка інформація про групу.") # Changed from GroupBriefSchema


if __name__ == "__main__":
    # Демонстраційний блок для схем рейтингів користувачів у групах.
    logger.info("--- Pydantic Схеми для Рейтингів Користувачів в Групах (UserGroupRating) ---")

    # Приклад використання RatingType (потребує, щоб RatingType був визначений та імпортований)
    # Для демонстрації, якщо RatingType ще не існує, можна тимчасово закоментувати
    # або створити фіктивний Enum RatingType тут.
    # class RatingType(str, Enum): OVERALL = "overall"; MONTHLY = "monthly"

    logger.info("\nUserGroupRatingCreateSchema (приклад для створення сервісом):")
    create_rating_data = {
        "user_id": 101,
        "group_id": 1,
        "rating_score": 1500,
        "rating_type": RatingType.OVERALL # Використання імпортованого Enum
    }
    create_rating_instance = UserGroupRatingCreateSchema(**create_rating_data)
    logger.info(create_rating_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nUserGroupRatingUpdateSchema (приклад для оновлення):")
    update_rating_data = {"rating_score": 1550}
    update_rating_instance = UserGroupRatingUpdateSchema(**update_rating_data)
    logger.info(update_rating_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nUserGroupRatingSchema (приклад відповіді API):")
    rating_response_data = {
        "id": 1,
        "user_id": 101,
        "group_id": 1,
        "rating_score": 1550,
        "rating_type": RatingType.OVERALL, # Використання імпортованого Enum
        "period_start_date": None,
        "period_end_date": None,
        "created_at": datetime.now() - timedelta(days=30),  # Коли запис було вперше створено
        "updated_at": datetime.now(),  # Коли рейтинг було востаннє оновлено/перераховано
        # Приклади для пов'язаних об'єктів (закоментовано, бо потребують повних даних схем)
        # "user": {"id": 101, "username": "top_player", "name": "Лідер Рейтингу"},
        # "group": {"id": 1, "name": "Головна Ліга", "group_type_code": "LEAGUE",
        #           "created_at": str(datetime.now()), "updated_at": str(datetime.now())}
    }
    rating_response_instance = UserGroupRatingSchema(**rating_response_data)
    logger.info(rating_response_instance.model_dump_json(indent=2, exclude_none=True))

    logger.info("\nПримітка: Схеми для пов'язаних об'єктів тепер імпортовані.")
    logger.info("Приклади даних для цих полів у `rating_response_data` закоментовані,")
    logger.info("оскільки потребують повної структури відповідних схем.")
    # Коментар про TODO щодо RatingType тепер неактуальний, оскільки Enum імпортовано.
