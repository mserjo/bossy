# backend/app/src/core/dicts.py

"""
Цей модуль визначає переліки (Enums) системного рівня, які представляють
фіксовані набори варіантів, що використовуються в бізнес-логіці програми.
Вони відрізняються від моделей-довідників, які можуть зберігатися в базі даних
та керуватися динамічно.
"""

from enum import Enum

class SortOrder(str, Enum):
    """Визначає порядок сортування для результатів запитів."""
    ASC = "asc"         # За зростанням
    DESC = "desc"       # За спаданням

class UserState(str, Enum):
    """Представляє можливі стани облікового запису користувача."""
    PENDING_VERIFICATION = "pending_verification" # Користувач зареєстрований, email/телефон ще не підтверджено
    ACTIVE = "active"                     # Обліковий запис користувача активний і може використовуватися
    INACTIVE = "inactive"                   # Обліковий запис користувача деактивовано адміністратором або користувачем
    SUSPENDED = "suspended"                 # Обліковий запис користувача тимчасово призупинено адміністратором
    BANNED = "banned"                     # Обліковий запис користувача остаточно заблоковано
    DELETED = "deleted"                   # Обліковий запис користувача позначено для видалення (м'яке видалення)

class GroupRole(str, Enum):
    """Визначає ролі всередині групи."""
    ADMIN = "admin"       # Адміністратор групи
    MEMBER = "member"     # Звичайний учасник групи
    # GUEST = "guest"     # Опціонально: гостьова роль з обмеженими правами

class TaskStatus(str, Enum):
    """
    Представляє статус життєвого циклу завдання.
    Це загальні статуси; конкретні програми можуть розширювати або спеціалізувати їх.
    """
    OPEN = "open"                          # Завдання доступне для виконання
    IN_PROGRESS = "in_progress"            # Завдання зараз виконується користувачем
    PENDING_REVIEW = "pending_review"      # Виконання завдання надіслано та очікує на затвердження адміністратором
    COMPLETED = "completed"                # Завдання успішно виконано та перевірено
    REJECTED = "rejected"                  # Виконання завдання було переглянуто та відхилено
    CANCELLED = "cancelled"                # Завдання було скасовано до завершення
    ON_HOLD = "on_hold"                    # Завдання тимчасово призупинено
    EXPIRED = "expired"                    # Завдання не було виконано до встановленого терміну

class EventFrequency(str, Enum):
    """Визначає, як часто відбувається повторюване завдання або подія."""
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    # CUSTOM = "custom" # Для складніших шаблонів повторення, зазвичай потребує більше полів

class NotificationType(str, Enum):
    """Визначає різні типи сповіщень у системі."""
    GENERAL_INFO = "general_info"
    TASK_ASSIGNED = "task_assigned"
    TASK_COMPLETED_USER = "task_completed_by_user" # Користувач позначив завдання як виконане
    TASK_VERIFIED_ADMIN = "task_verified_by_admin" # Адміністратор затвердив/відхилив виконання
    TASK_REMINDER = "task_reminder"
    BONUS_AWARDED = "bonus_awarded"
    REWARD_REDEEMED = "reward_redeemed"
    GROUP_INVITATION = "group_invitation"
    NEW_MEMBER_JOINED_GROUP = "new_member_joined_group"
    ACCOUNT_BALANCE_UPDATE = "account_balance_update"
    SYSTEM_ANNOUNCEMENT = "system_announcement"

class FileType(str, Enum):
    """Категоризує завантажені файли."""
    AVATAR = "avatar"
    GROUP_ICON = "group_icon"
    REWARD_ICON = "reward_icon"
    BADGE_ICON = "badge_icon"
    TASK_ATTACHMENT = "task_attachment"
    GENERAL_DOCUMENT = "general_document"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    OTHER = "other"

class TimePeriod(str, Enum):
    """Представляє загальні періоди часу для звітності або фільтрації."""
    TODAY = "today"
    YESTERDAY = "yesterday"
    LAST_7_DAYS = "last_7_days"
    LAST_30_DAYS = "last_30_days"
    CURRENT_MONTH = "current_month"
    PREVIOUS_MONTH = "previous_month"
    CURRENT_YEAR = "current_year"
    ALL_TIME = "all_time"

# Додавайте більше Enum за потребою для основної логіки вашої програми.
# Приклади:
# class TransactionType(str, Enum):
#     CREDIT = "credit"
#     DEBIT = "debit"
#     REFUND = "refund"

# class LogLevel(str, Enum):
#     DEBUG = "debug"
#     INFO = "info"
#     WARNING = "warning"
#     ERROR = "error"
#     CRITICAL = "critical"

if __name__ == "__main__":
    print("--- Основні переліки (Довідники) ---")

    print("\nСтани користувача:")
    for state in UserState:
        print(f"- {state.name}: {state.value}")

    print("\nРолі в групі:")
    for role in GroupRole:
        print(f"- {role.name}: {role.value}")

    print("\nСтатуси завдань:")
    for status in TaskStatus:
        print(f"- {status.name}: {status.value}")

    print("\nПорядки сортування:")
    for order in SortOrder:
        print(f"- {order.name}: {order.value}")

    print("\nТипи сповіщень:")
    for n_type in NotificationType:
        print(f"- {n_type.name}: {n_type.value}")

    print(f"\nДоступ до конкретного значення enum: UserState.ACTIVE це '{UserState.ACTIVE.value}'")
