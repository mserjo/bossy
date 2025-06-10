# backend/app/src/schemas/gamification/badge.py
"""
Pydantic схеми для сутності "Бейдж" (Badge) в системі гейміфікації.

Цей модуль визначає схеми для:
- Створення нового бейджа (`BadgeCreateSchema`).
- Оновлення існуючого бейджа (`BadgeUpdateSchema`).
- Представлення даних про бейдж у відповідях API (`BadgeSchema`).
"""
from datetime import datetime  # Потрібен для TimestampedSchemaMixin через BaseMainSchema
from typing import Optional, Any  # Any для тимчасових полів

from pydantic import Field, AnyHttpUrl

# Абсолютний імпорт базових схем
from backend.app.src.schemas.base import BaseSchema, \
    BaseMainSchema  # IDSchemaMixin, TimestampedSchemaMixin вже в BaseMainSchema

# TODO: Замінити Any на конкретну схему GroupSchema (коротка версія), коли вона буде готова.
# from backend.app.src.schemas.groups.group import GroupBriefSchema
GroupBriefSchema = Any  # Тимчасовий заповнювач

BADGE_NAME_MAX_LENGTH = 255
BADGE_ICON_URL_MAX_LENGTH = 512  # Збігається з моделлю


class BadgeBaseSchema(
    BaseSchema):  # Не успадковує BaseMainSchema, оскільки ID/timestamps не потрібні для Create/Update базових полів
    """
    Базова схема для полів бейджа, спільних для створення та оновлення.
    """
    name: str = Field(
        ...,
        max_length=BADGE_NAME_MAX_LENGTH,
        description="Назва бейджа гейміфікації.",
        examples=["Першопроходець", "Командний Гравець"]
    )
    description: Optional[str] = Field(
        None,
        description="Опис умов отримання або значення цього бейджа."
    )
    icon_url: Optional[AnyHttpUrl] = Field(
        None,
        description="URL або шлях до іконки, що представляє бейдж."
    )
    group_id: Optional[int] = Field(
        None,
        description="ID групи, до якої належить цей бейдж. NULL, якщо бейдж глобальний/системний."
    )
    state: Optional[str] = Field(
        None,  # Або default="active"
        max_length=50,
        description="Стан бейджа (наприклад, 'active', 'archived').",
        examples=["active"]
    )
    notes: Optional[str] = Field(  # Додаємо notes, оскільки Badge модель успадковує NotesMixin через BaseMainModel
        None,
        description="Додаткові нотатки щодо бейджа."
    )


class BadgeCreateSchema(BadgeBaseSchema):
    """
    Схема для створення нового бейджа гейміфікації.
    Успадковує всі поля від `BadgeBaseSchema`.
    """
    pass


class BadgeUpdateSchema(BadgeBaseSchema):
    """
    Схема для оновлення існуючого бейджа гейміфікації.
    Всі поля, успадковані з `BadgeBaseSchema`, стають опціональними.
    """
    name: Optional[str] = Field(None, max_length=BADGE_NAME_MAX_LENGTH)
    description: Optional[str] = None
    icon_url: Optional[AnyHttpUrl] = None
    group_id: Optional[int] = Field(None,
                                    description="Зміна групи для бейджа (зазвичай не дозволяється або обробляється окремо).")
    state: Optional[str] = Field(None, max_length=50)
    notes: Optional[str] = None


class BadgeSchema(BaseMainSchema):  # Успадковує id, name, description, state, notes, group_id, timestamps
    """
    Схема для представлення даних про бейдж гейміфікації у відповідях API.
    Успадковує стандартні поля з `BaseMainSchema`.
    """
    # id, name, description, state, notes, group_id, created_at, updated_at, deleted_at - успадковані

    # Специфічні поля моделі Badge
    icon_url: Optional[AnyHttpUrl] = Field(None, description="URL іконки бейджа.")

    # Пов'язані об'єкти
    # TODO: Замінити Any на GroupBriefSchema, коли вона буде імпортована.
    group: Optional[GroupBriefSchema] = Field(None,
                                              description="Коротка інформація про групу, до якої належить бейдж (якщо є).")

    # model_config успадковується з BaseMainSchema -> BaseSchema (from_attributes=True)


if __name__ == "__main__":
    # Демонстраційний блок для схем бейджів.
    print("--- Pydantic Схеми для Бейджів Гейміфікації (Badge) ---")

    print("\nBadgeCreateSchema (приклад для створення):")
    create_badge_data = {
        "name": "Зірка Спільноти",  # TODO i18n
        "description": "Надається за активну допомогу іншим учасникам.",  # TODO i18n
        "icon_url": "https://example.com/icons/community_star.png",
        "state": "active"
        # group_id може бути None для глобального бейджа
    }
    create_badge_instance = BadgeCreateSchema(**create_badge_data)
    print(create_badge_instance.model_dump_json(indent=2, exclude_none=True))

    print("\nBadgeUpdateSchema (приклад для оновлення):")
    update_badge_data = {
        "description": "Оновлений опис для Зірки Спільноти: надається за 100 корисних відповідей.",  # TODO i18n
        "icon_url": "https://example.com/icons/community_star_v2.png"
    }
    update_badge_instance = BadgeUpdateSchema(**update_badge_data)
    print(update_badge_instance.model_dump_json(indent=2, exclude_none=True))

    print("\nBadgeSchema (приклад відповіді API):")
    badge_response_data = {
        "id": 1,
        "name": "Ранній Птах",  # TODO i18n
        "description": "Надається за реєстрацію в перший тиждень роботи системи.",  # TODO i18n
        "state": "active",
        "group_id": None,  # Глобальний бейдж
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "icon_url": "https://example.com/icons/early_bird.png",
    }
    badge_response_instance = BadgeSchema(**badge_response_data)
    print(badge_response_instance.model_dump_json(indent=2, exclude_none=True))

    print("\nПримітка: Схема для `group` наразі є заповнювачем (Any).")
    print("Її потрібно буде замінити на `GroupBriefSchema` після її визначення.")
