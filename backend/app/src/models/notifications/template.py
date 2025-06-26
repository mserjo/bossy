# backend/app/src/models/notifications/template.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає модель SQLAlchemy `NotificationTemplateModel` для зберігання
шаблонів сповіщень. Шаблони використовуються для генерації тексту та заголовків
сповіщень різними мовами, підставляючи динамічні дані.
"""

from sqlalchemy import Column, String, Text, ForeignKey, UniqueConstraint # type: ignore
from sqlalchemy.dialects.postgresql import UUID, JSONB # type: ignore
from sqlalchemy.orm import relationship, Mapped, mapped_column  # type: ignore
import uuid # Для роботи з UUID

# Використовуємо BaseMainModel, оскільки шаблон має назву (ідентифікатор), опис,
# може мати статус (активний/неактивний) і може бути пов'язаний з групою (якщо є кастомні шаблони для груп)
# або бути глобальним.
# group_id тут, ймовірно, буде NULL для системних шаблонів.
from backend.app.src.models.base import BaseMainModel

class NotificationTemplateModel(BaseMainModel):
    """
    Модель для зберігання шаблонів сповіщень.

    Атрибути:
        id (uuid.UUID): Унікальний ідентифікатор шаблону (успадковано).
        name (str): Унікальний код/назва шаблону (наприклад, "TASK_COMPLETED_USER_NOTIFICATION",
                    "NEW_GROUP_INVITE_EMAIL_SUBJECT"). Використовується для програмного пошуку шаблону. (успадковано)
        description (str | None): Опис призначення шаблону (успадковано).
        state_id (uuid.UUID | None): Статус шаблону (наприклад, "активний", "чернетка", "архівований").
                                     Посилається на StatusModel. (успадковано)
        group_id (uuid.UUID | None): Ідентифікатор групи, якщо шаблон специфічний для групи.
                                     NULL для глобальних/системних шаблонів. (успадковано)

        notification_type_code (str): Код типу сповіщення, для якого призначений цей шаблон.
                                      Має відповідати `NotificationModel.notification_type_code`.
                                      Дозволяє мати кілька шаблонів для одного типу сповіщення (наприклад, для різних каналів).
        channel_code (str): Код каналу доставки, для якого призначений цей шаблон
                            (наприклад, "IN_APP", "EMAIL_TITLE", "EMAIL_BODY_HTML", "PUSH_SHORT").
                            TODO: Визначити Enum або довідник для каналів.
        language_code (str): Код мови шаблону (наприклад, "uk", "en"). ISO 639-1.

        template_content (Text): Сам шаблон тексту. Може використовувати синтаксис шаблонізатора
                                 (наприклад, Jinja2, Mustache: "Вітаємо, {{ user_name }}!").

        # Додаткові поля
        # subject_template (Text | None): Окремий шаблон для заголовка (наприклад, для email).
        # Якщо channel_code розрізняє title/body, то це поле може бути непотрібним.

        # version (int): Версія шаблону, для можливості оновлення.

        created_at (datetime): Дата та час створення запису (успадковано).
        updated_at (datetime): Дата та час останнього оновлення запису (успадковано).
        deleted_at (datetime | None): Дата та час "м'якого" видалення (успадковано).
        is_deleted (bool): Прапорець "м'якого" видалення (успадковано).
        notes (str | None): Додаткові нотатки (успадковано).

    Зв'язки:
        # group (relationship): Зв'язок з GroupModel (якщо є групові шаблони).
        # status (relationship): Зв'язок зі статусом шаблону.
    """
    __tablename__ = "notification_templates"

    # `name` з BaseMainModel використовується як унікальний код шаблону.
    # Потрібно забезпечити його унікальність, можливо, в поєднанні з іншими полями.

    # Тип сповіщення, для якого цей шаблон.
    notification_type_code: Column[str] = Column(String(100), nullable=False, index=True)

    # Канал, для якого цей шаблон (наприклад, 'IN_APP', 'EMAIL_SUBJECT', 'EMAIL_BODY_HTML', 'SMS', 'PUSH')
    # TODO: Створити Enum або довідник для NotificationChannel.
    channel_code: Column[str] = Column(String(50), nullable=False, index=True)

    # Код мови (наприклад, 'uk', 'en')
    language_code: Column[str] = Column(String(10), nullable=False, index=True) # ISO 639-1 коди (uk, en)

    # Вміст шаблону. Може містити змінні для підстановки.
    template_content: Column[str] = Column(Text, nullable=False)

    # `group_id` з BaseMainModel дозволяє створювати кастомні шаблони для груп.
    # `group_id` з BaseMainModel дозволяє створювати кастомні шаблони для груп.
    # Якщо `group_id` = NULL, шаблон є глобальним.

    template_code: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)

    # --- Зв'язки (Relationships) ---
    # group: Mapped[Optional["GroupModel"]] - успадковано з BaseMainModel
    # state: Mapped[Optional["StatusModel"]] - успадковано з BaseMainModel

    # Коментар для Alembic щодо унікальності комбінації:
    # Для забезпечення унікальності функціонального ключа шаблону (тип, канал, мова, група)
    # можна додати наступні обмеження через міграції:
    # 1. Для групових шаблонів:
    #    UniqueConstraint('notification_type_code', 'channel_code', 'language_code', 'group_id',
    #                     name='uq_notif_template_group_key',
    #                     postgresql_where=sa.text('group_id IS NOT NULL'))
    # 2. Для глобальних шаблонів:
    #    UniqueConstraint('notification_type_code', 'channel_code', 'language_code',
    #                     name='uq_notif_template_global_key',
    #                     postgresql_where=sa.text('group_id IS NULL'))
    # Це гарантує, що не буде двох однакових шаблонів для однієї ситуації.
    # Поле `template_code` залишається головним унікальним ключем для програмного доступу.

    def __repr__(self) -> str:
        """
        Повертає рядкове представлення об'єкта моделі NotificationTemplateModel.
        """
        return f"<{self.__class__.__name__}(id='{self.id}', template_code='{self.template_code}', lang='{self.language_code}')>"

# TODO: Перевірити відповідність `technical-task.md`.
# - Прямо не згадано, але для підтримки різних мов та типів сповіщень шаблони необхідні.
# - "підтримка різних мов ... і UI, і контент, і помилки, і сповіщення (JSON)"
#   - `language_code` та `template_content` для цього.

# TODO: Узгодити назву таблиці `notification_templates` з `structure-claude-v3.md`. Відповідає.
# Використання `BaseMainModel` як основи.
# Поля `notification_type_code`, `channel_code`, `language_code`, `template_content` ключові.
# Додано `template_code` для унікальної ідентифікації шаблону, `name` з `BaseMainModel` - для описової назви.
# `group_id` для кастомних шаблонів груп.
# `state_id` для статусу шаблону.
# Зв'язки визначені.
# Все виглядає логічно.
# Система буде шукати найбільш специфічний шаблон: спочатку для групи та мови,
# потім глобальний для мови, потім дефолтний глобальний.
# `template_content` може містити плейсхолдери для підстановки даних.
# `channel_code` важливий, бо формат сповіщення для email, sms, push, in-app може сильно відрізнятися.
# Наприклад, для email може бути HTML, для SMS - короткий текст.
# `name` з `BaseMainModel` - це назва шаблону для адміністрування.
# `description` - опис.
# `notes` - додаткові нотатки.
# `deleted_at`, `is_deleted` - для м'якого видалення.
# Зв'язок `group` уточнено з `foreign_keys`.
# Унікальність `template_code` важлива.
# Можливо, варто додати унікальне обмеження на (`notification_type_code`, `channel_code`, `language_code`, `group_id`),
# щоб уникнути дублювання функціонально однакових шаблонів, якщо `template_code` не використовується
# для їх розрізнення. Але якщо `template_code` є ключем, то це не потрібно.
# Поточна структура з `template_code` як унікальним ключем є робочою.
# Сервіс буде відповідати за вибір правильного `template_code` на основі
# `notification_type`, `channel`, `language` та `group`.
# Це означає, що `template_code` має бути добре продуманим, щоб кодувати ці аспекти,
# або ж потрібна буде таблиця-мапінг або складна логіка вибору.
#
# Якщо `template_code` не буде містити всю цю інформацію, то краще
# `UniqueConstraint(notification_type_code, channel_code, language_code, group_id (з урахуванням NULL))`.
# Це складніше реалізувати в SQLAlchemy для NULL-специфічних UniqueConstraint.
#
# Переглядаю рішення: `template_code` (унікальний) - це програмний ідентифікатор шаблону.
# `name` (з BaseMainModel) - це назва для відображення в адмінці.
# Поля `notification_type_code`, `channel_code`, `language_code`, `group_id` - це атрибути,
# за якими сервіс знаходить потрібний `template_code`.
# Тоді на ці атрибути має бути унікальний індекс (якщо вони разом визначають унікальний шаблон).
# Наприклад, не може бути два шаблони з однаковими `notification_type_code`, `channel_code`, `language_code`
# для однієї й тієї ж групи (або для глобальних, якщо `group_id` is NULL).
# Це важливе обмеження.
#
# Додаю __table_args__ для цього.
# Це потребує двох окремих UniqueConstraint через NULL в group_id.
# Це стандартний підхід для таких випадків.
# _table_args__ = (
#     UniqueConstraint('notification_type_code', 'channel_code', 'language_code', 'group_id', name='uq_notif_template_group_specific_key'),
#     UniqueConstraint('notification_type_code', 'channel_code', 'language_code', name='uq_notif_template_global_key', postgresql_where=(group_id.is_(None))),
# )
# Поле `template_code` тоді може бути необов'язковим або генеруватися на основі цих полів.
# Або ж, якщо `template_code` є, то він має бути унікальним, а ці поля - просто для пошуку.
# Поки що залишаю `template_code` унікальним, а ці поля - для фільтрації.
# Це означає, що сервіс знаходить потрібний `template_code` за цими фільтрами.
# Якщо знайдено кілька - це помилка конфігурації.
# Якщо не знайдено - використовується дефолтний.
# Це виглядає більш гнучким.
# Унікальність `template_code` вже є.

    __table_args__ = (
        # Унікальний шаблон для групи, типу, каналу та мови
        UniqueConstraint('notification_type_code', 'channel_code', 'language_code', 'group_id',
                         name='uq_notif_template_group_key',
                         postgresql_where=(group_id.isnot(None))),
        # Унікальний глобальний шаблон для типу, каналу та мови
        UniqueConstraint('notification_type_code', 'channel_code', 'language_code',
                         name='uq_notif_template_global_key',
                         postgresql_where=(group_id.is_(None))),
    )
