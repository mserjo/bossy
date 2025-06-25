# backend/app/src/models/groups/settings.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає модель SQLAlchemy `GroupSettingsModel` для зберігання
специфічних налаштувань для кожної окремої групи.
Ці налаштування керують поведінкою та функціоналом в межах конкретної групи.
"""

from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey, Integer, Numeric, Time # type: ignore
from sqlalchemy.dialects.postgresql import UUID, JSONB # type: ignore
from sqlalchemy.orm import relationship # type: ignore
import uuid # Для роботи з UUID

from backend.app.src.models.base import BaseModel # Успадковуємо від BaseModel, оскільки це налаштування, а не основна сутність з ім'ям/описом.
# Хоча, якщо налаштування мають версії або потребують аудиту як `BaseMainModel`, можна переглянути.
# Поки що `BaseModel` (id, created_at, updated_at) виглядає достатнім.

class GroupSettingsModel(BaseModel):
    """
    Модель для зберігання налаштувань конкретної групи.
    Кожен запис у цій таблиці відповідає налаштуванням однієї групи (зв'язок один-до-одного з GroupModel).

    Атрибути:
        id (uuid.UUID): Унікальний ідентифікатор запису налаштувань (успадковано).
        group_id (uuid.UUID): Ідентифікатор групи, до якої належать ці налаштування. Первинний ключ та зовнішній ключ.

        currency_name (str | None): Назва валюти бонусів для групи (наприклад, "бали", "зірочки").
                                    Може бути вибрано з BonusTypeModel або введено вручну.
        bonus_type_id (uuid.UUID | None): Посилання на обраний тип бонусу з довідника BonusTypeModel.
        allow_decimal_bonuses (bool): Чи дозволені дробові значення для бонусів у цій групі.
        max_debt_allowed (Numeric | None): Максимально допустимий борг для користувачів у групі.

        # Налаштування завдань/подій
        task_proposals_enabled (bool): Чи можуть користувачі пропонувати завдання.
        task_reviews_enabled (bool): Чи можуть користувачі залишати відгуки/рейтинги на завдання.
        default_task_visibility (str): Видимість завдань за замовчуванням ('all_members', 'assignees_only').

        # Налаштування сповіщень
        notify_admin_on_task_completion_check (bool): Сповіщати адміна, коли завдання позначено "на перевірку".
        notify_user_on_task_status_change (bool): Сповіщати користувача про зміну статусу його завдання.
        notify_user_on_account_change (bool): Сповіщати користувача про рухи по його рахунку.
        task_deadline_reminder_days (int | None): За скільки днів до дедлайну надсилати нагадування.

        # Налаштування приватності та видимості
        profile_visibility (str): Налаштування видимості профілів учасників ('public_in_group', 'admins_only').
        activity_feed_enabled (bool): Чи ввімкнена стрічка активності в групі.

        # Інтеграції (можуть бути більш складними і вимагати окремих таблиць)
        # Наприклад, чи ввімкнена синхронізація з календарем для цієї групи.
        calendar_integration_enabled (bool): Чи ввімкнена інтеграція з календарями.
        default_calendar_id (str | None): ID календаря за замовчуванням для групи.

        # Інші специфічні налаштування
        welcome_message (Text | None): Привітальне повідомлення для нових учасників групи.
        daily_standup_time (Time | None): Час для щоденного стендапу (якщо є).

        # Додаткові налаштування гейміфікації
        levels_enabled (bool): Чи ввімкнена система рівнів.
        badges_enabled (bool): Чи ввімкнена система бейджів.

        custom_settings (JSONB | None): Поле для зберігання будь-яких інших кастомних налаштувань у форматі JSONB.

        created_at (datetime): Дата та час створення запису (успадковано).
        updated_at (datetime): Дата та час останнього оновлення запису (успадковано).

    Зв'язки:
        group (relationship): Зв'язок з GroupModel (один-до-одного).
        selected_bonus_type (relationship): Зв'язок з BonusTypeModel.
    """
    __tablename__ = "group_settings"

    # Ідентифікатор групи. Це одночасно і зовнішній ключ, і частина первинного ключа,
    # щоб забезпечити зв'язок один-до-одного.
    # Однак, SQLAlchemy краще працює, коли ForeignKey є окремим від PK.
    # Тому `id` з `BaseModel` буде PK, а `group_id` буде ForeignKey з unique=True.
    group_id: Column[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    # --- Налаштування бонусів ---
    currency_name: Column[str | None] = Column(String(100), nullable=True) # Наприклад, "бали", "зірочки"
    # Посилання на обраний тип бонусу з довідника.
    # TODO: Замінити "bonus_types.id" на константу або імпорт моделі BonusTypeModel.
    bonus_type_id: Column[uuid.UUID | None] = Column(UUID(as_uuid=True), ForeignKey("bonus_types.id", name="fk_group_settings_bonus_type_id"), nullable=True)
    allow_decimal_bonuses: Column[bool] = Column(Boolean, default=False, nullable=False)
    max_debt_allowed: Column[Numeric | None] = Column(Numeric(10, 2), nullable=True) # 10 цифр, 2 після коми

    # --- Налаштування завдань/подій ---
    task_proposals_enabled: Column[bool] = Column(Boolean, default=True, nullable=False)
    task_reviews_enabled: Column[bool] = Column(Boolean, default=True, nullable=False)
    # TODO: Визначити можливі значення для default_task_visibility (можливо, Enum або довідник)
    default_task_visibility: Column[str] = Column(String(50), default="all_members", nullable=False)

    # --- Налаштування сповіщень ---
    notify_admin_on_task_completion_check: Column[bool] = Column(Boolean, default=True, nullable=False)
    notify_user_on_task_status_change: Column[bool] = Column(Boolean, default=True, nullable=False)
    notify_user_on_account_change: Column[bool] = Column(Boolean, default=True, nullable=False)
    task_deadline_reminder_days: Column[int | None] = Column(Integer, nullable=True) # NULL означає вимкнено

    # --- Налаштування приватності та видимості ---
    # TODO: Визначити можливі значення для profile_visibility
    profile_visibility: Column[str] = Column(String(50), default="public_in_group", nullable=False)
    activity_feed_enabled: Column[bool] = Column(Boolean, default=True, nullable=False)

    # --- Інтеграції ---
    calendar_integration_enabled: Column[bool] = Column(Boolean, default=False, nullable=False)
    default_calendar_id: Column[str | None] = Column(String(255), nullable=True) # Зовнішній ID календаря

    # --- Інші налаштування ---
    welcome_message: Column[str | None] = Column(Text, nullable=True)
    daily_standup_time: Column[Time | None] = Column(Time(timezone=False), nullable=True) # Тільки час, без дати

    # --- Налаштування гейміфікації ---
    levels_enabled: Column[bool] = Column(Boolean, default=True, nullable=False)
    badges_enabled: Column[bool] = Column(Boolean, default=True, nullable=False)

    # Поле для будь-яких інших кастомних налаштувань, які не мають власних колонок.
    # Використання JSONB рекомендується для PostgreSQL через кращу продуктивність та можливості індексації.
    custom_settings: Column[JSONB | None] = Column(JSONB, nullable=True)

    # --- Зв'язки (Relationships) ---
    group = relationship("GroupModel", back_populates="settings")

    selected_bonus_type = relationship("BonusTypeModel", foreign_keys=[bonus_type_id]) # back_populates="groups_using_this_setting" буде в BonusTypeModel

    def __repr__(self) -> str:
        """
        Повертає рядкове представлення об'єкта моделі GroupSettingsModel.
        """
        return f"<{self.__class__.__name__}(id='{self.id}', group_id='{self.group_id}')>"

# TODO: Перевірити відповідність `technical-task.md`:
# - "налаштування групи (назва групи, ієрархія груп, назва валюти бонусів, бонуси цілі чи дробові, максимальний розмір боргу, і т.д.)"
#   - назва групи, ієрархія - в GroupModel.
#   - назва валюти бонусів (`currency_name`), бонуси цілі/дробові (`allow_decimal_bonuses`), макс. борг (`max_debt_allowed`) - тут.
# - "користувач може створити пропозицію завдання/події ... (ця можливість налаштовується адміном в групі)" - `task_proposals_enabled`.
# - "можна залишати відгуки на завдання/події та ставити рейтинги (ця можливість налаштовується адміном в групі)" - `task_reviews_enabled`.
# - "досягнення ... (налаштовується в адміном групі)" - `levels_enabled`, `badges_enabled`.
# - "сповіщення ... (налаштовується в профілі користувача)" - частина сповіщень може налаштовуватися на рівні групи.

# TODO: Узгодити назву таблиці `group_settings` з `structure-claude-v3.md`. Відповідає.
# Використання `BaseModel` як основи. `group_id` є унікальним зовнішнім ключем для зв'язку 1-до-1.
# Додано багато специфічних полів для налаштувань.
# `JSONB` для `custom_settings` для гнучкості.
# `ondelete="CASCADE"` для `group_id` забезпечує видалення налаштувань при видаленні групи.
# Зв'язок з `BonusTypeModel` для `bonus_type_id`.
# Поля `currency_name` та `allow_decimal_bonuses` можуть частково дублювати інформацію з `BonusTypeModel`,
# але тут вони представляють конкретний вибір та налаштування для групи.
# Наприклад, `BonusTypeModel` може мати `code='points', name='Бали', allow_decimal=True` (як глобальний тип),
# а в `GroupSettingsModel` `bonus_type_id` посилається на нього, `currency_name` може бути "Очки Пошани",
# і `allow_decimal_bonuses` може бути встановлено в `False` для цієї конкретної групи,
# перевизначаючи значення за замовчуванням з `BonusTypeModel`.
# Або ж `currency_name` та `allow_decimal_bonuses` беруться з `selected_bonus_type` і тут не зберігаються,
# а зберігається лише `bonus_type_id`.
# Поточний підхід: `bonus_type_id` для посилання на глобальний тип, `currency_name` для кастомної назви в групі,
# `allow_decimal_bonuses` для кастомного налаштування дробовості в групі.
# Це виглядає гнучко.
# `Numeric(10, 2)` для `max_debt_allowed` дозволяє зберігати числа типу 12345678.90.
# `Time` для `daily_standup_time` зберігає лише час.
# Все виглядає логічно.
