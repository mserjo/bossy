# backend/app/src/models/groups/template.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає модель SQLAlchemy `GroupTemplateModel` для зберігання шаблонів груп.
Шаблони груп дозволяють супер-адміністраторам створювати передвизначені конфігурації груп
(з налаштуваннями, типами завдань, нагородами тощо) для швидкого розгортання нових схожих груп.
"""

from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey, JSON # type: ignore
from sqlalchemy.dialects.postgresql import UUID, JSONB # type: ignore
from sqlalchemy.orm import relationship # type: ignore
import uuid # Для роботи з UUID

# Використовуємо BaseMainModel, оскільки шаблон має назву, опис, і потенційно статус (активний/неактивний шаблон).
# group_id для шаблона буде NULL.
from backend.app.src.models.base import BaseMainModel

class GroupTemplateModel(BaseMainModel):
    """
    Модель для зберігання шаблонів груп.

    Атрибути:
        id (uuid.UUID): Унікальний ідентифікатор шаблону групи (успадковано).
        name (str): Назва шаблону групи (наприклад, "Шаблон для ІТ-відділу", "Сімейний шаблон") (успадковано).
        description (str | None): Опис шаблону, для чого він призначений (успадковано).
        state_id (uuid.UUID | None): Статус шаблону (наприклад, "активний", "чернетка", "архівований").
                                     Посилається на StatusModel. (успадковано)
        group_id (uuid.UUID | None): Для шаблонів груп це поле буде NULL. (успадковано)

        template_data (JSONB): JSON-об'єкт, що зберігає конфігурацію шаблону.
                               Це може включати:
                               - Налаштування групи (аналогічно GroupSettingsModel).
                               - Список стандартних типів завдань для групи.
                               - Список стандартних нагород.
                               - Можливо, початковий набір ролей (окрім стандартних адмін/користувач).
                               - Інші передвизначені параметри.
        version (int): Версія шаблону, для можливості оновлення шаблонів.

        created_by_user_id (uuid.UUID | None): Ідентифікатор супер-адміністратора, який створив шаблон.
        # updated_by_user_id успадковується з BaseModel, якщо там розкоментовано.

        created_at (datetime): Дата та час створення запису (успадковано).
        updated_at (datetime): Дата та час останнього оновлення запису (успадковано).
        deleted_at (datetime | None): Дата та час "м'якого" видалення (успадковано).
        is_deleted (bool): Прапорець "м'якого" видалення (успадковано).
        notes (str | None): Додаткові нотатки (успадковано).

    Зв'язки:
        # TODO: Додати зв'язки, якщо потрібно:
        # - creator (UserModel): Зв'язок з користувачем, який створив шаблон.
        # - status (StatusModel): Зв'язок зі статусом шаблону (вже є через state_id з BaseMainModel).
        # - groups_created_from_template (GroupModel): Список груп, створених на основі цього шаблону (необов'язково, для статистики).
    """
    __tablename__ = "group_templates"

    # JSONB поле для зберігання всіх даних шаблону.
    # JSONB є кращим за JSON в PostgreSQL для індексації та продуктивності.
    template_data: Column[JSONB] = Column(JSONB, nullable=False, default=lambda: {})

    # Версія шаблону. Дозволяє оновлювати шаблони, зберігаючи старі версії або контролюючи зміни.
    version: Column[int] = Column(Integer, default=1, nullable=False)

    # Ідентифікатор користувача (супер-адміна), який створив цей шаблон.
    # TODO: Замінити "users.id" на константу або імпорт моделі UserModel.
    created_by_user_id: Column[uuid.UUID | None] = Column(UUID(as_uuid=True), ForeignKey("users.id", name="fk_group_templates_creator_id"), nullable=True) # Може бути NULL, якщо є системні шаблони

    # --- Зв'язки (Relationships) ---
    creator = relationship("UserModel", foreign_keys=[created_by_user_id]) # back_populates="created_group_templates" буде в UserModel

    # Зв'язок зі статусом (успадкований з BaseMainModel, якщо там визначено relationship `state`)
    # state = relationship("StatusModel", foreign_keys=[state_id])

    # `group_id` з BaseMainModel тут завжди буде NULL.

    def __repr__(self) -> str:
        """
        Повертає рядкове представлення об'єкта моделі GroupTemplateModel.
        """
        return f"<{self.__class__.__name__}(id='{self.id}', name='{self.name}', version='{self.version}')>"

# Приклад структури `template_data`:
# {
#   "group_settings": {
#     "currency_name": "Бали активності",
#     "allow_decimal_bonuses": True,
#     "max_debt_allowed": 100.00,
#     "task_proposals_enabled": True,
#     // ... інші поля з GroupSettingsModel
#   },
#   "default_task_types": [ # Список кодів або ID типів завдань
#     "general_task", "bug_report", "meeting_participation"
#   ],
#   "default_rewards": [ # Список описів нагород або їх шаблонів
#     {"name": "Чашка кави", "cost": 50, "description": "Безкоштовна чашка кави в офісі"},
#     {"name": "Додатковий вихідний", "cost": 500, "description": "Один додатковий оплачуваний вихідний"}
#   ],
#   "default_roles_config": { # Можливо, специфічні налаштування для ролей у групах цього типу
#       "custom_role_code": {"permissions": ["view_reports"]}
#   },
#   "welcome_message_template": "Вітаємо в нашій команді {{group_name}}!"
# }

# TODO: Перевірити відповідність `technical-task.md`:
# - "(superadmin) створення/налаштування шаблонів груп (групи з передвизначеними налаштуваннями,
#   типами завдань та нагородами для швидкого розгортання нових схожих груп)" - ця модель для цього.
# - "при створенні групи, адмін обирає серед існуючих шаблонів груп" - означає, що GroupModel
#   може мати посилання `created_from_template_id` на `GroupTemplateModel.id`.

# TODO: Узгодити назву таблиці `group_templates` з `structure-claude-v3.md`. Відповідає.
# Використання `BaseMainModel` як основи є доречним (назва, опис, статус шаблону).
# `template_data` у форматі JSONB для зберігання конфігурації.
# `version` для версіонування шаблонів.
# `created_by_user_id` для відстеження автора шаблону.
# `group_id` з `BaseMainModel` буде `NULL`.
# Зв'язки визначені.
# Все виглядає логічно.
# Супер-адміністратор керує цими шаблонами. Адміністратори груп використовують їх при створенні нових груп.
# Логіка застосування шаблону (копіювання налаштувань, створення стандартних завдань/нагород)
# буде реалізована на сервісному рівні.
