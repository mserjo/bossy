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
import enum
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)


class BaseEnum(str, enum.Enum):
    """Базовий клас для всіх Enum у проекті для забезпечення строкової типізації."""
    @classmethod
    def has_value(cls, value: str) -> bool:
        """Перевіряє, чи існує таке значення в Enum."""
        return value in cls._value2member_map_ # type: ignore

    def __str__(self) -> str:
        """Повертає рядкове представлення значення Enum."""
        return self.value

    # Для порівняння з рядками напряму, наприклад MyEnum.VALUE == "value_string"
    # Це вже забезпечується успадкуванням від str.


class SortOrder(BaseEnum):
    """Визначає порядок сортування для результатів запитів та списків."""
    ASC = "asc"         # Сортування за зростанням (A-Z, 0-9).
    DESC = "desc"       # Сортування за спаданням (Z-A, 9-0).

class UserState(BaseEnum):
    """Представляє можливі стани облікового запису користувача в системі."""
    PENDING_VERIFICATION = "pending_verification" # Обліковий запис створено, але очікує на підтвердження (наприклад, email).
    ACTIVE = "active"                             # Обліковий запис активний і може використовуватися.
    INACTIVE = "inactive"                         # Обліковий запис деактивовано користувачем або за тривалою неактивністю.
    SUSPENDED = "suspended"                       # Обліковий запис тимчасово призупинено адміністратором системи.
    BANNED = "banned"                             # Обліковий запис остаточно заблоковано адміністратором системи.
    DELETED = "deleted"                           # Обліковий запис позначено для видалення (м'яке видалення).

class SystemUserRole(BaseEnum):
    """Визначає системні ролі користувачів, що впливають на доступ до всієї системи."""
    SUPERUSER = "superuser" # Суперкористувач, має повний доступ до всієї системи.
    USER = "user"           # Звичайний користувач системи.
    BOT = "bot"             # Системний бот для виконання автоматизованих завдань.

class UserType(BaseEnum):
    """Визначає типи користувачів на основі їх реєстрації або системного призначення."""
    SUPERUSER = "superuser"     # Тип для суперкористувачів.
    ADMIN_USER = "admin_user"   # Тип користувача, який може бути адміністратором групи.
    REGULAR_USER = "regular_user" # Тип для звичайних користувачів.
    BOT_USER = "bot_user"         # Тип для системних ботів.

class GroupRole(BaseEnum):
    """Визначає ролі користувачів всередині конкретної групи."""
    OWNER = "owner"       # Власник групи (можливо, той хто створив, з особливими правами).
    ADMIN = "admin"       # Адміністратор групи, може керувати учасниками та завданнями.
    MEMBER = "member"     # Звичайний учасник групи.
    GUEST = "guest"       # Опціонально: гостьова роль з обмеженими правами перегляду.

class GroupType(BaseEnum):
    """Визначає типи груп, відповідно до технічного завдання."""
    FAMILY = "family"           # Тип групи "Сім'я".
    DEPARTMENT = "department"   # Тип групи "Відділ".
    ORGANIZATION = "organization" # Тип групи "Організація".
    COMMUNITY = "community"       # Спільнота за інтересами
    OTHER = "other"               # Інший тип групи


class TaskStatus(BaseEnum):
    """Представляє можливі статуси життєвого циклу завдання або події."""
    NEW = "new"                             # Нове завдання, ще не в роботі
    PENDING_ASSIGNMENT = "pending_assignment" # Очікує на призначення виконавця
    ASSIGNED = "assigned"                   # Призначено виконавцю
    OPEN = "open"                             # Завдання відкрите та доступне для взяття в роботу.
    IN_PROGRESS = "in_progress"               # Завдання взято в роботу та виконується.
    PENDING_REVIEW = "pending_review"         # Виконання завдання завершено користувачем та очікує на перевірку/затвердження.
    COMPLETED = "completed"                   # Завдання успішно виконано та затверджено.
    REJECTED = "rejected"                     # Виконання завдання було відхилено після перевірки.
    CANCELLED = "cancelled"                   # Завдання було скасовано до його завершення.
    ON_HOLD = "on_hold"                       # Виконання завдання тимчасово призупинено.
    ARCHIVED = "archived"                     # Архівовано (неактивне)
    EXPIRED = "expired"                       # Термін виконання завдання минув до його завершення.


class TaskPriority(BaseEnum):
    """Пріоритети завдань."""
    LOW = "low"       # Низький пріоритет
    MEDIUM = "medium" # Середній пріоритет
    HIGH = "high"     # Високий пріоритет
    CRITICAL = "critical" # Критичний пріоритет


class TaskType(BaseEnum):
    """Визначає типи завдань, відповідно до технічного завдання."""
    REGULAR_TASK = "regular_task"   # "Звичайне завдання"
    COMPLEX_TASK = "complex_task"   # "Складне завдання"
    EVENT = "event"                 # "Подія" (як тип завдання)
    FINE = "fine"                   # "Штраф" (завдання, що призводить до штрафу)

class EventFrequency(BaseEnum):
    """Визначає частоту повторення для завдань або подій."""
    ONCE = "once"           # Одноразова подія/завдання.
    DAILY = "daily"         # Щоденно.
    WEEKLY = "weekly"       # Щотижня.
    MONTHLY = "monthly"     # Щомісяця.
    YEARLY = "yearly"       # Щорічно.

class BonusTypeDict(BaseEnum): # У моєму плані було BonusType, але існуючий BonusType перейменовано на BonusTypeDict
    """Типи бонусів (з довідника dict_bonus_types)."""
    REWARD = "reward"  # Нагорода за позитивні дії
    PENALTY = "penalty" # Штраф за негативні дії
    MANUAL = "manual"   # Ручне нарахування/списання адміністратором


class TransactionType(BaseEnum):
    """Визначає типи фінансових транзакцій по рахунку користувача."""
    CREDIT = "credit"   # Нарахування коштів/бонусів на рахунок.
    DEBIT = "debit"     # Списання коштів/бонусів з рахунку.
    REFUND = "refund"   # Повернення коштів/бонусів.
    ADJUSTMENT_INCREASE = "adjustment_increase" # Ручне коригування (збільшення).
    ADJUSTMENT_DECREASE = "adjustment_decrease" # Ручне коригування (зменшення).

class NotificationType(BaseEnum): # Існуючий Enum, розширений
    """Визначає різні типи системних сповіщень."""
    GENERIC = "generic"                     # Загальне сповіщення (з мого плану)
    TASK_ASSIGNED = "task_assigned"                 # Призначено нове завдання.
    TASK_COMPLETED = "task_completed"       # Завдання виконано (з мого плану, відрізняється від TASK_COMPLETED_BY_USER)
    TASK_COMPLETED_BY_USER = "task_completed_by_user" # Користувач позначив завдання як виконане.
    TASK_VERIFIED_BY_ADMIN = "task_verified_by_admin" # Адміністратор затвердив/відхилив виконання завдання.
    TASK_STATUS_CHANGED = "task_status_changed" # Змінено статус завдання (з мого плану)
    TASK_REMINDER = "task_reminder"                 # Нагадування про термін виконання завдання.
    BONUS_AWARDED = "bonus_awarded"                 # Нараховано бонуси.
    PENALTY_APPLIED = "penalty_applied"             # Застосовано штраф.
    REWARD_REDEEMED = "reward_redeemed"             # Користувач отримав нагороду.
    NEW_REWARD_AVAILABLE = "new_reward_available" # Доступна нова нагорода (з мого плану)
    GROUP_INVITATION = "group_invitation"           # Запрошення до групи.
    GROUP_JOIN_REQUEST = "group_join_request" # Запит на приєднання до групи (з мого плану)
    NEW_MEMBER_JOINED_GROUP = "new_member_joined_group" # Новий учасник приєднався до групи.
    NEW_MESSAGE = "new_message"               # Нове повідомлення (з мого плану, якщо є чат)
    ACCOUNT_BALANCE_UPDATE = "account_balance_update" # Оновлення балансу рахунку.
    SYSTEM_ANNOUNCEMENT = "system_announcement"       # Загальносистемне оголошення.
    # GENERAL_INFO було в існуючому, замінено на GENERIC для уникнення конфлікту з LogLevel.INFO

class FileType(BaseEnum): # Існуючий Enum, розширений
    """Категоризує типи файлів, що завантажуються в систему."""
    AVATAR = "avatar"                 # Аватар користувача.
    TASK_ATTACHMENT = "task_attachment" # Вкладення до завдання.
    GROUP_ICON = "group_icon"         # Іконка групи.
    REWARD_ICON = "reward_icon"       # Іконка нагороди. (Існуючий)
    REWARD_IMAGE = "reward_image"         # Зображення для нагороди (з мого плану, схоже на REWARD_ICON)
    BADGE_ICON = "badge_icon"         # Іконка бейджа/досягнення.
    GENERAL_DOCUMENT = "general_document" # Загальний документ.
    IMAGE = "image"                   # Зображення (загального призначення).
    VIDEO = "video"                   # Відеофайл.
    AUDIO = "audio"                   # Аудіофайл.
    OTHER = "other"                   # Інший тип файлу.

class TimePeriod(BaseEnum):
    """Представляє загальні періоди часу для використання у звітах або фільтрації даних."""
    TODAY = "today"                 # Сьогодні.
    YESTERDAY = "yesterday"         # Вчора.
    LAST_7_DAYS = "last_7_days"     # Останні 7 днів.
    LAST_30_DAYS = "last_30_days"   # Останні 30 днів.
    CURRENT_MONTH = "current_month" # Поточний місяць.
    PREVIOUS_MONTH = "previous_month" # Попередній місяць.
    CURRENT_YEAR = "current_year"   # Поточний рік.
    ALL_TIME = "all_time"           # За весь час.

# --- Нові Enum, що додаються ---

class RelatedEntityType(BaseEnum):
    """Типи сутностей, на які може посилатися сповіщення."""
    TASK = "task"                         # Завдання
    GROUP = "group"                       # Група
    USER = "user"                         # Користувач
    BONUS_TRANSACTION = "bonus_transaction" # Бонусна транзакція
    REWARD = "reward"                     # Нагорода
    EVENT = "event"                       # Подія
    # Додайте інші типи сутностей за потребою

class NotificationChannelType(BaseEnum):
    """Канали доставки сповіщень."""
    EMAIL = "email"                         # Електронна пошта
    SMS = "sms"                             # SMS повідомлення
    IN_APP = "in_app"                       # Внутрішнє сповіщення в додатку
    PUSH_NOTIFICATION = "push_notification" # Мобільний пуш-сповіщення
    WEBHOOK = "webhook"                     # Виклик зовнішнього вебхука
    MESSENGER = "messenger"                 # Через платформу месенджера (Telegram, Viber etc.)

class DeliveryStatusType(BaseEnum):
    """Статуси спроби доставки сповіщення."""
    PENDING = "pending"     # Очікує на відправку
    SENT = "sent"           # Успішно надіслано провайдеру/сервісу
    FAILED = "failed"       # Не вдалося надіслати (помилка на нашому боці або у провайдера)
    DELIVERED = "delivered"   # Підтверджено доставку (якщо провайдер це підтримує)
    READ = "read"           # Прочитано (для деяких каналів, як email, якщо є трекінг)
    ERROR = "error"         # Загальна помилка під час спроби

class HealthStatusType(BaseEnum):
    """Статуси здоров'я сервісів."""
    HEALTHY = "healthy"     # Сервіс працює нормально
    UNHEALTHY = "unhealthy"   # Сервіс не працює або не відповідає
    DEGRADED = "degraded"    # Сервіс працює, але з проблемами (повільно, частково)
    UNKNOWN = "unknown"     # Стан сервісу невідомий

class LogLevel(BaseEnum):
    """Рівні системного логування (схожі на стандартні рівні logging)."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class SettingValueType(BaseEnum):
    """Типи значень для системних налаштувань."""
    STRING = "string"       # Рядок
    INTEGER = "integer"     # Ціле число
    FLOAT = "float"         # Число з плаваючою комою
    BOOLEAN = "boolean"     # Булеве значення
    JSON = "json"           # JSON об'єкт або масив
    LIST_STR = "list_str"   # Список рядків (зберігається як JSON або розділений рядок)

class TaskAssignmentStatus(BaseEnum):
    """Статуси призначення завдання користувачеві."""
    ASSIGNED = "assigned"    # Завдання призначено, очікує на прийняття (якщо потрібно)
    ACCEPTED = "accepted"    # Користувач прийняв завдання до виконання
    DECLINED = "declined"    # Користувач відхилив завдання (якщо завдання не обов'язкове)
    IN_PROGRESS = "in_progress" # Користувач активно працює (якщо відрізняється від Task.state)

class InvitationStatus(BaseEnum):
    """Статуси запрошень до групи."""
    PENDING = "pending"     # Запрошення надіслано, очікує на відповідь
    ACCEPTED = "accepted"   # Запрошення прийнято
    DECLINED = "declined"   # Запрошення відхилено
    EXPIRED = "expired"     # Термін дії запрошення закінчився
    CANCELLED = "cancelled" # Запрошення скасовано відправником

class RatingType(BaseEnum):
    """Типи рейтингів користувачів у групі."""
    OVERALL = "overall"       # Загальний рейтинг за весь час
    MONTHLY = "monthly"       # Місячний рейтинг
    WEEKLY = "weekly"         # Тижневий рейтинг
    DAILY = "daily"           # Денний рейтинг
    CUSTOM_PERIOD = "custom_period" # Рейтинг за визначений період


if __name__ == "__main__":
    # Демонстраційний блок для перегляду визначених переліків.
    logger.info("--- Системні Переліки (Довідники) ---")

    all_enums = [
        SortOrder, UserState, SystemUserRole, UserType, GroupRole, GroupType,
        TaskStatus, TaskPriority, TaskType, EventFrequency, BonusTypeDict, TransactionType,
        NotificationType, FileType, TimePeriod, RelatedEntityType, NotificationChannelType,
        DeliveryStatusType, HealthStatusType, LogLevel, SettingValueType,
        TaskAssignmentStatus, InvitationStatus, RatingType
    ]

    for enum_cls in all_enums:
        logger.info(f"\n{enum_cls.__name__}:")
        for item in enum_cls: # type: ignore
            logger.info(f"- {item.name}: {item.value}") # type: ignore

    logger.info(f"\nПриклад доступу до значення: UserState.ACTIVE = '{UserState.ACTIVE.value}'")
    logger.info(f"Перевірка BaseEnum: UserState.ACTIVE == 'active' -> {UserState.ACTIVE == 'active'}")
    logger.info(f"Перевірка BaseEnum: str(UserState.ACTIVE) == 'active' -> {str(UserState.ACTIVE) == 'active'}")
    logger.info(f"Перевірка BaseEnum: GroupRole.has_value('admin') -> {GroupRole.has_value('admin')}")
    logger.info(f"Перевірка BaseEnum: GroupRole.has_value('non_existent') -> {GroupRole.has_value('non_existent')}")

logger.debug("Модуль core.dicts з Enum типами завантажено та оновлено.")
