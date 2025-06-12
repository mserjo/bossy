# backend/app/src/core/dicts.py
# -*- coding: utf-8 -*-
"""
Системні переліки (Enums) для програми Kudos.

Цей модуль визначає фіксовані набори значень (переліки), які використовуються
для представлення стандартизованих станів, типів, ролей та інших категорій
в межах бізнес-логіки програми. Використання Enum допомагає забезпечити
узгодженість даних, покращує читабельність коду та зменшує ймовірність помилок,
пов'язаних із використанням довільних рядкових значень.

Ці переліки є частиною ядра програми і не призначені для динамічного
керування через адміністративний інтерфейс (на відміну від моделей-довідників,
які зберігаються в базі даних).
"""

from enum import Enum
from backend.app.src.config.logging import get_logger

# Отримання логера для цього модуля
logger = get_logger(__name__)


class SortOrder(str, Enum):
    """Визначає порядок сортування для результатів запитів та списків."""
    ASC = "asc"         # Сортування за зростанням (A-Z, 0-9).
    DESC = "desc"       # Сортування за спаданням (Z-A, 9-0).

class UserState(str, Enum):
    """Представляє можливі стани облікового запису користувача в системі."""
    PENDING_VERIFICATION = "pending_verification" # Обліковий запис створено, але очікує на підтвердження (наприклад, email).
    ACTIVE = "active"                             # Обліковий запис активний і може використовуватися.
    INACTIVE = "inactive"                         # Обліковий запис деактивовано користувачем або за тривалою неактивністю.
    SUSPENDED = "suspended"                       # Обліковий запис тимчасово призупинено адміністратором системи.
    BANNED = "banned"                             # Обліковий запис остаточно заблоковано адміністратором системи.
    DELETED = "deleted"                           # Обліковий запис позначено для видалення (м'яке видалення).

class SystemUserRole(str, Enum):
    """Визначає системні ролі користувачів, що впливають на доступ до всієї системи."""
    SUPERUSER = "superuser" # Суперкористувач, має повний доступ до всієї системи.
    USER = "user"           # Звичайний користувач системи.
    BOT = "bot"             # Системний бот для виконання автоматизованих завдань.
    # Примітка: Роль "адмін групи" визначається через GroupRole та членство в групі.

class UserType(str, Enum):
    """Визначає типи користувачів на основі їх реєстрації або системного призначення."""
    # Відповідно до "тип користувача - суперюзер, адмін, користувач, бот" з тех. завдання.
    # "Адмін" тут може означати користувача, який має потенціал бути адміном групи,
    # але його конкретні права визначаються через GroupRole.
    SUPERUSER = "superuser"     # Тип для суперкористувачів.
    ADMIN_USER = "admin_user"   # Тип користувача, який може бути адміністратором групи.
    REGULAR_USER = "regular_user" # Тип для звичайних користувачів.
    BOT_USER = "bot_user"         # Тип для системних ботів.

class GroupRole(str, Enum):
    """Визначає ролі користувачів всередині конкретної групи."""
    OWNER = "owner"       # Власник групи (можливо, той хто створив, з особливими правами).
    ADMIN = "admin"       # Адміністратор групи, може керувати учасниками та завданнями.
    MEMBER = "member"     # Звичайний учасник групи.
    # GUEST = "guest"     # Опціонально: гостьова роль з обмеженими правами перегляду.

class GroupType(str, Enum):
    """Визначає типи груп, відповідно до технічного завдання."""
    FAMILY = "family"           # Тип групи "Сім'я".
    DEPARTMENT = "department"   # Тип групи "Відділ".
    ORGANIZATION = "organization" # Тип групи "Організація".

class TaskStatus(str, Enum):
    """Представляє можливі статуси життєвого циклу завдання або події."""
    OPEN = "open"                             # Завдання відкрите та доступне для взяття в роботу.
    IN_PROGRESS = "in_progress"               # Завдання взято в роботу та виконується.
    PENDING_REVIEW = "pending_review"         # Виконання завдання завершено користувачем та очікує на перевірку/затвердження.
    COMPLETED = "completed"                   # Завдання успішно виконано та затверджено.
    REJECTED = "rejected"                     # Виконання завдання було відхилено після перевірки.
    CANCELLED = "cancelled"                   # Завдання було скасовано до його завершення.
    ON_HOLD = "on_hold"                       # Виконання завдання тимчасово призупинено.
    EXPIRED = "expired"                       # Термін виконання завдання минув до його завершення.

class TaskType(str, Enum):
    """Визначає типи завдань, відповідно до технічного завдання."""
    REGULAR_TASK = "regular_task"   # "Звичайне завдання"
    COMPLEX_TASK = "complex_task"   # "Складне завдання"
    EVENT = "event"                 # "Подія" (як тип завдання)
    FINE = "fine"                   # "Штраф" (завдання, що призводить до штрафу)

class EventFrequency(str, Enum):
    """Визначає частоту повторення для завдань або подій."""
    ONCE = "once"           # Одноразова подія/завдання.
    DAILY = "daily"         # Щоденно.
    WEEKLY = "weekly"       # Щотижня.
    MONTHLY = "monthly"     # Щомісяця.
    YEARLY = "yearly"       # Щорічно.
    # CUSTOM = "custom"     # Для більш складних шаблонів повторення (потребуватиме дод. полів).

class BonusType(str, Enum):
    """Визначає типи бонусів, відповідно до технічного завдання."""
    REWARD = "reward"   # Нарахування бонусів (позитивне).
    PENALTY = "penalty" # Списання бонусів/штраф (негативне).

class TransactionType(str, Enum):
    """Визначає типи фінансових транзакцій по рахунку користувача."""
    CREDIT = "credit"   # Нарахування коштів/бонусів на рахунок.
    DEBIT = "debit"     # Списання коштів/бонусів з рахунку.
    REFUND = "refund"   # Повернення коштів/бонусів.
    ADJUSTMENT_INCREASE = "adjustment_increase" # Ручне коригування (збільшення).
    ADJUSTMENT_DECREASE = "adjustment_decrease" # Ручне коригування (зменшення).

class NotificationType(str, Enum):
    """Визначає різні типи системних сповіщень."""
    GENERAL_INFO = "general_info"                   # Загальна інформація.
    TASK_ASSIGNED = "task_assigned"                 # Призначено нове завдання.
    TASK_COMPLETED_BY_USER = "task_completed_by_user" # Користувач позначив завдання як виконане.
    TASK_VERIFIED_BY_ADMIN = "task_verified_by_admin" # Адміністратор затвердив/відхилив виконання завдання.
    TASK_REMINDER = "task_reminder"                 # Нагадування про термін виконання завдання.
    BONUS_AWARDED = "bonus_awarded"                 # Нараховано бонуси.
    PENALTY_APPLIED = "penalty_applied"             # Застосовано штраф.
    REWARD_REDEEMED = "reward_redeemed"             # Користувач отримав нагороду.
    GROUP_INVITATION = "group_invitation"           # Запрошення до групи.
    NEW_MEMBER_JOINED_GROUP = "new_member_joined_group" # Новий учасник приєднався до групи.
    ACCOUNT_BALANCE_UPDATE = "account_balance_update" # Оновлення балансу рахунку.
    SYSTEM_ANNOUNCEMENT = "system_announcement"       # Загальносистемне оголошення.

class FileType(str, Enum):
    """Категоризує типи файлів, що завантажуються в систему."""
    AVATAR = "avatar"                 # Аватар користувача.
    GROUP_ICON = "group_icon"         # Іконка групи.
    REWARD_ICON = "reward_icon"       # Іконка нагороди.
    BADGE_ICON = "badge_icon"         # Іконка бейджа/досягнення.
    TASK_ATTACHMENT = "task_attachment" # Вкладення до завдання.
    GENERAL_DOCUMENT = "general_document" # Загальний документ.
    IMAGE = "image"                   # Зображення (загального призначення).
    VIDEO = "video"                   # Відеофайл.
    AUDIO = "audio"                   # Аудіофайл.
    OTHER = "other"                   # Інший тип файлу.

class TimePeriod(str, Enum):
    """Представляє загальні періоди часу для використання у звітах або фільтрації даних."""
    TODAY = "today"                 # Сьогодні.
    YESTERDAY = "yesterday"         # Вчора.
    LAST_7_DAYS = "last_7_days"     # Останні 7 днів.
    LAST_30_DAYS = "last_30_days"   # Останні 30 днів.
    CURRENT_MONTH = "current_month" # Поточний місяць.
    PREVIOUS_MONTH = "previous_month" # Попередній місяць.
    CURRENT_YEAR = "current_year"   # Поточний рік.
    ALL_TIME = "all_time"           # За весь час.


if __name__ == "__main__":
    # Демонстраційний блок для перегляду визначених переліків.
    logger.info("--- Системні Переліки (Довідники) ---")

    logger.info("\nПорядок сортування (SortOrder):")
    for item in SortOrder: logger.info(f"- {item.name}: {item.value}")

    logger.info("\nСтани користувача (UserState):")
    for item in UserState: logger.info(f"- {item.name}: {item.value}")

    logger.info("\nСистемні ролі користувачів (SystemUserRole):")
    for item in SystemUserRole: logger.info(f"- {item.name}: {item.value}")

    logger.info("\nТипи користувачів (UserType):")
    for item in UserType: logger.info(f"- {item.name}: {item.value}")

    logger.info("\nРолі в групі (GroupRole):")
    for item in GroupRole: logger.info(f"- {item.name}: {item.value}")

    logger.info("\nТипи груп (GroupType):")
    for item in GroupType: logger.info(f"- {item.name}: {item.value}")

    logger.info("\nСтатуси завдань (TaskStatus):")
    for item in TaskStatus: logger.info(f"- {item.name}: {item.value}")

    logger.info("\nТипи завдань (TaskType):")
    for item in TaskType: logger.info(f"- {item.name}: {item.value}")

    logger.info("\nЧастота подій (EventFrequency):")
    for item in EventFrequency: logger.info(f"- {item.name}: {item.value}")

    logger.info("\nТипи бонусів (BonusType):")
    for item in BonusType: logger.info(f"- {item.name}: {item.value}")

    logger.info("\nТипи транзакцій (TransactionType):")
    for item in TransactionType: logger.info(f"- {item.name}: {item.value}")

    logger.info("\nТипи сповіщень (NotificationType):")
    for item in NotificationType: logger.info(f"- {item.name}: {item.value}")

    logger.info("\nТипи файлів (FileType):")
    for item in FileType: logger.info(f"- {item.name}: {item.value}")

    logger.info("\nПеріоди часу (TimePeriod):")
    for item in TimePeriod: logger.info(f"- {item.name}: {item.value}")

    logger.info(f"\nПриклад доступу до значення: UserState.ACTIVE = '{UserState.ACTIVE.value}'")
