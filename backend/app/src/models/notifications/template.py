# backend/app/src/models/notifications/template.py
"""
Модель SQLAlchemy для сутності "Шаблон Сповіщення" (NotificationTemplate).

Цей модуль визначає модель `NotificationTemplate`, яка зберігає шаблони
для різних типів сповіщень (наприклад, email, SMS, внутрішні сповіщення).
Шаблони містять тему та тіло, які можуть включати плейсхолдери для динамічних даних.
"""
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column  # relationship тут не потрібен, якщо немає зворотніх зв'язків

# Абсолютний імпорт базової моделі для довідників
from backend.app.src.models.dictionaries.base_dict import BaseDictionary
from backend.app.src.config.logging import get_logger
from backend.app.src.core.dicts import NotificationChannelType # Імпорт Enum
from sqlalchemy import Enum as SQLEnum # Імпорт SQLEnum
logger = get_logger(__name__)

class NotificationTemplate(BaseDictionary):
    """
    Модель Шаблону Сповіщення.

    Успадковує `BaseDictionary` (id, code, name, description, state, etc.).
    Поле `code` - унікальний код шаблону (наприклад, "new_task_assigned_email").
    Поле `name` - людиночитана назва шаблону (наприклад, "Email: Нове завдання призначено").
    Поле `description` - детальний опис призначення шаблону.
    Поле `state` - чи активний шаблон для використання.

    Атрибути:
        subject_template (Mapped[str]): Шаблон теми сповіщення (може містити плейсхолдери).
        body_template (Mapped[str]): Шаблон тіла сповіщення (HTML для email, текст для SMS/push, Markdown/JSON для in-app).
        template_type (Mapped[NotificationChannelType]): Тип/канал сповіщення (використовує Enum `NotificationChannelType`).
    """
    __tablename__ = "notification_templates"

    # --- Специфічні поля для Шаблону Сповіщення ---
    subject_template: Mapped[str] = mapped_column(
        String(500), nullable=False, comment="Шаблон теми сповіщення (з плейсхолдерами)"
    )
    body_template: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Шаблон тіла сповіщення (з плейсхолдерами, може бути HTML/Markdown/Text)"
    )

    template_type: Mapped[NotificationChannelType] = mapped_column(
        SQLEnum(NotificationChannelType), nullable=False, index=True, comment="Тип/канал шаблону (наприклад, email, sms, in_app)"
    )

    # _repr_fields успадковуються та збираються з BaseDictionary (id, name, code, state_id тощо).
    # Додаємо специфічні для NotificationTemplate поля.
    _repr_fields = ("template_type",)


if __name__ == "__main__":
    # Демонстраційний блок для моделі NotificationTemplate.
    logger.info("--- Модель Шаблону Сповіщення (NotificationTemplate) ---")
    logger.info(f"Назва таблиці: {NotificationTemplate.__tablename__}")

    logger.info("\nОчікувані поля (успадковані та власні):")
    expected_fields = [
        'id', 'code', 'name', 'description', 'state', 'group_id', 'notes',
        'created_at', 'updated_at', 'deleted_at',
        'subject_template', 'body_template', 'template_type'
    ]
    for field in expected_fields:
        logger.info(f"  - {field}")

    # Приклад створення екземпляра (без взаємодії з БД)
    from datetime import datetime, timezone

    example_template = NotificationTemplate(
        id=1,
        code="WELCOME_EMAIL",
        name="Вітальне Email Сповіщення",  # TODO i18n
        description="Шаблон для вітального листа, що надсилається новому користувачеві.",  # TODO i18n
        subject_template="Ласкаво просимо до {project_name}, {{user_name}}!",  # TODO i18n (плейсхолдери окремо)
        body_template="<p>Привіт, {{user_name}}!</p><p>Дякуємо за реєстрацію в {project_name}.</p>",
        # TODO i18n (плейсхолдери окремо)
        template_type=NotificationChannelType.EMAIL,  # Використання Enum
        state="active"
    )
    example_template.created_at = datetime.now(tz=timezone.utc)

    logger.info(f"\nПриклад екземпляра NotificationTemplate (без сесії):\n  {example_template}")
    # Очікуваний __repr__ (порядок може відрізнятися):
    # <NotificationTemplate(id=1, name='Вітальне Email Сповіщення', code='WELCOME_EMAIL', state='active', template_type=<NotificationChannelType.EMAIL: 'email'>, created_at=...)>

    logger.info("\nПримітка: Для повноцінної роботи з моделлю потрібна сесія SQLAlchemy та підключення до БД.")
