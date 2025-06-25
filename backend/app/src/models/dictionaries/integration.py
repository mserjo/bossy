# backend/app/src/models/dictionaries/integration.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає модель SQLAlchemy `IntegrationModel` для довідника "Типи зовнішніх інтеграцій".
Цей довідник містить перелік зовнішніх сервісів, з якими система може інтегруватися,
наприклад, месенджери (Telegram, Viber), календарі (Google Calendar, Outlook), таск-трекери (Jira, Trello).

Модель `IntegrationModel` успадковує `BaseDictModel`, що надає їй стандартний набір полів
(id, name, description, code, state_id, group_id, created_at, updated_at, deleted_at, is_deleted, notes)
та функціональність.
"""

from sqlalchemy import UniqueConstraint, Column, String # type: ignore
# from sqlalchemy.orm import relationship # type: ignore # Для визначення зв'язків

from backend.app.src.models.dictionaries.base import BaseDictModel # Імпорт базової моделі для довідників

# TODO: Визначити, чи потрібні специфічні поля для моделі IntegrationModel.
# Наприклад, категорія інтеграції (месенджер, календар, таск-трекер),
# URL для документації API, необхідні поля для налаштування (API ключ, токен тощо).

class IntegrationModel(BaseDictModel):
    """
    Модель для довідника "Типи зовнішніх інтеграцій".

    Атрибути:
        id (uuid.UUID): Унікальний ідентифікатор типу інтеграції (успадковано).
        name (str): Назва типу інтеграції (наприклад, "Telegram Bot", "Google Calendar API") (успадковано).
        description (str | None): Детальний опис типу інтеграції (успадковано).
        code (str): Унікальний символьний код типу інтеграції (наприклад, "telegram", "google_calendar") (успадковано).
        state_id (uuid.UUID | None): Ідентифікатор стану запису типу інтеграції (успадковано, використання під питанням).
        group_id (uuid.UUID | None): Для довідника типів інтеграцій це поле, ймовірно, завжди буде NULL,
                                     оскільки типи інтеграцій є глобальними (успадковано).
        created_at (datetime): Дата та час створення запису (успадковано).
        updated_at (datetime): Дата та час останнього оновлення запису (успадковано).
        deleted_at (datetime | None): Дата та час "м'якого" видалення запису (успадковано).
        is_deleted (bool): Прапорець, що вказує, чи запис "м'яко" видалено (успадковано).
        notes (str | None): Додаткові нотатки (успадковано).

    Додаткові поля:
        category (str | None): Категорія інтеграції (наприклад, 'messenger', 'calendar', 'task_tracker').
                               Може бути корисним для групування та фільтрації.

    Ім'я таблиці в базі даних: `integrations`.
    """
    __tablename__ = "integrations"

    # Обмеження унікальності для поля `code`.
    # Гарантує, що кожен символьний код типу інтеграції є унікальним.
    __table_args__ = (
        UniqueConstraint('code', name='uq_integrations_code'),
    )

    # Категорія інтеграції, наприклад, 'messenger', 'calendar', 'task_tracker', 'payment_system'.
    # Допомагає класифікувати типи інтеграцій.
    category: Column[str | None] = Column(String(100), nullable=True, index=True)

    # TODO: Розглянути можливість зберігання URL документації або базового URL API для інтеграції.
    # api_docs_url: Column[str | None] = Column(String(512), nullable=True)
    # base_api_url: Column[str | None] = Column(String(255), nullable=True)

    # TODO: Подумати про зберігання шаблону налаштувань, необхідних для цієї інтеграції (наприклад, у форматі JSON).
    # Це може допомогти динамічно генерувати форми для налаштування інтеграції користувачем.
    # required_settings_schema: Column[JSON] = Column(JSON, nullable=True)

    # TODO: Визначити зв'язки з іншими моделями, наприклад, з таблицею,
    # де зберігаються конкретні налаштування інтеграції для користувача або групи.
    # user_integrations = relationship("UserIntegrationSettingsModel", back_populates="integration_type")
    # group_integrations = relationship("GroupIntegrationSettingsModel", back_populates="integration_type")

    def __repr__(self) -> str:
        """
        Повертає рядкове представлення об'єкта моделі IntegrationModel.
        Наприклад: <IntegrationModel(id='...', name='Telegram Bot', code='telegram')>
        """
        return f"<{self.__class__.__name__}(id='{self.id}', name='{self.name}', code='{self.code}')>"

# Приклади початкових даних для довідника типів інтеграцій (згідно technical-task.md):
# Месенджери:
# - Telegram (code: 'telegram', name: 'Telegram', category: 'messenger')
# - Viber (code: 'viber', name: 'Viber', category: 'messenger')
# - Slack (code: 'slack', name: 'Slack', category: 'messenger')
# - Microsoft Teams (code: 'msteams', name: 'Microsoft Teams', category: 'messenger')
# - WhatsApp (code: 'whatsapp', name: 'WhatsApp', category: 'messenger') - може бути складним через API
# Календарі:
# - Google Calendar (code: 'google_calendar', name: 'Google Calendar', category: 'calendar')
# - Outlook Calendar (code: 'outlook_calendar', name: 'Outlook Calendar', category: 'calendar')
# Таск-трекери:
# - Jira (code: 'jira', name: 'Jira', category: 'task_tracker')
# - Trello (code: 'trello', name: 'Trello', category: 'task_tracker')
# Інші (потенційно):
# - Firebase Cloud Messaging (code: 'fcm', name: 'Firebase Cloud Messaging', category: 'push_notification')
# - Elasticsearch (code: 'elasticsearch', name: 'Elasticsearch', category: 'search_engine')

# TODO: Перевірити відповідність `technical-task.md` та `structure-claude-v3.md`.
# `BaseDictModel` надає більшість полів. `group_id` для цієї моделі буде `None`.
# Додано поле `category`.
# Назва таблиці `integrations` (а не `integration_types`, як у структурі для schemas/repositories)
# для узгодження з іншими довідниками (statuses, user_roles).
# TODO: Узгодити назву таблиці: `integrations` чи `integration_types`.
# В `structure-claude-v3.md` для моделей вказано `integration.py`, що передбачає `integrations`.
# Для схем/репозиторіїв вказано `integration_type.py`.
# Залишаю `integrations` для таблиці моделі.
# Унікальність `code` встановлена.
# Поле `category` додано для кращої класифікації.
# Подальші поля, такі як `api_docs_url` або `required_settings_schema`, можуть бути корисними.
