# backend/app/src/models/dictionaries/status.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає модель SQLAlchemy `StatusModel` для довідника "Статуси".
Статуси використовуються для позначення стану різних об'єктів в системі,
наприклад, завдань (нове, в роботі, виконано, скасовано), користувачів (активний, заблокований) тощо.

Модель `StatusModel` успадковує `BaseDictModel`, що надає їй стандартний набір полів
(id, name, description, code, state_id, group_id, created_at, updated_at, deleted_at, is_deleted, notes)
та функціональність.
"""

from sqlalchemy import UniqueConstraint # type: ignore # Для визначення обмежень унікальності
# from sqlalchemy.orm import relationship # type: ignore # Для визначення зв'язків (якщо потрібно)

from backend.app.src.models.dictionaries.base import BaseDictModel # Імпорт базової моделі для довідників

# TODO: Визначити, чи потрібні специфічні поля для моделі StatusModel, окрім успадкованих.
# Наприклад, колір для візуального представлення статусу, або порядок сортування.

class StatusModel(BaseDictModel):
    """
    Модель для довідника "Статуси".

    Атрибути:
        id (uuid.UUID): Унікальний ідентифікатор статусу (успадковано).
        name (str): Назва статусу, що відображається користувачеві (наприклад, "Нове", "В роботі") (успадковано).
        description (str | None): Детальний опис статусу (успадковано).
        code (str): Унікальний символьний код статусу (наприклад, "new", "in_progress") (успадковано).
                    Використовується для програмної ідентифікації статусу.
        state_id (uuid.UUID | None): Ідентифікатор стану самого запису статусу (успадковано, використання під питанням для довідників).
        group_id (uuid.UUID | None): Ідентифікатор групи, якщо статус специфічний для групи (успадковано).
                                     Для глобальних статусів це поле буде NULL.
        created_at (datetime): Дата та час створення запису (успадковано).
        updated_at (datetime): Дата та час останнього оновлення запису (успадковано).
        deleted_at (datetime | None): Дата та час "м'якого" видалення запису (успадковано).
        is_deleted (bool): Прапорець, що вказує, чи запис "м'яко" видалено (успадковано).
        notes (str | None): Додаткові нотатки (успадковано).

    Ім'я таблиці в базі даних: `statuses`.
    """
    __tablename__ = "statuses"

    # Обмеження унікальності для поля `code`.
    # Це гарантує, що кожен символьний код статусу є унікальним в межах таблиці.
    # Якщо статуси можуть бути специфічними для груп (`group_id IS NOT NULL`),
    # то унікальність `code` може розглядатися в межах кожної групи.
    # В такому випадку, обмеження може бути `UniqueConstraint('group_id', 'code', name='uq_status_group_code')`.
    # Наразі припускаємо, що `code` має бути глобально унікальним, або унікальним серед тих, де `group_id IS NULL`.
    # TODO: Уточнити вимоги до унікальності кодів статусів (глобальна чи в межах групи).
    # Поки що робимо `code` унікальним глобально.
    __table_args__ = (
        UniqueConstraint('code', name='uq_statuses_code'),
    )

    # TODO: Якщо статуси використовуються багатьма іншими моделями (завдання, користувачі, тощо),
    # тут можна визначити зворотні зв'язки (relationships) для зручності доступу.
    # Наприклад, якщо модель TaskModel має поле state_id, що посилається на StatusModel:
    # tasks = relationship("TaskModel", back_populates="state")
    # Це дозволить отримати всі завдання з певним статусом: status_object.tasks

    # TODO: Розглянути додавання поля `order` (Integer) для можливості сортування статусів
    # у визначеному порядку (наприклад, для відображення у випадаючих списках).
    # order: Column[int] = Column(Integer, default=0, nullable=False)

    # TODO: Розглянути додавання поля `color` (String) для зберігання кольору статусу
    # (наприклад, для візуального виділення в інтерфейсі).
    # color: Column[str] = Column(String(7), nullable=True)  # Формат #RRGGBB

    def __repr__(self) -> str:
        """
        Повертає рядкове представлення об'єкта моделі StatusModel.
        Наприклад: <StatusModel(id='...', name='Нове', code='new')>
        """
        return f"<{self.__class__.__name__}(id='{self.id}', name='{self.name}', code='{self.code}')>"

# Приклади початкових даних для довідника статусів (згідно technical-task.md):
# - створено (code: 'created')
# - в роботі (code: 'in_progress')
# - перевірка (code: 'pending_review')
# - підтверджено (code: 'confirmed', 'approved')
# - відхилено (code: 'rejected', 'declined')
# - заблоковано (code: 'blocked', 'suspended')
# - скасовано (code: 'cancelled')
# - видалено (code: 'deleted') - цей статус може бути зайвим, якщо використовується is_deleted/deleted_at

# TODO: Переконатися, що назви полів та їх типи відповідають вимогам `technical-task.md` та `structure-claude-v3.md`.
# `BaseDictModel` вже включає `name`, `description`, `code`.
# `state_id` успадковано, але його доцільність для самих записів довідника обговорюється в `BaseDictModel`.
# `group_id` успадковано для можливості створення статусів, специфічних для груп.
# Якщо статуси завжди глобальні, `group_id` для них буде `None`.
# Поля аудиту `created_at`, `updated_at`, `deleted_at`, `is_deleted`, `notes` також успадковані.
# Унікальність `code` додана через `UniqueConstraint`.
# Назва таблиці `statuses` відповідає структурі.
# Подальші специфічні поля (як `order` чи `color`) можуть бути додані за потреби.
