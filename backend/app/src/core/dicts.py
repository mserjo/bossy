# backend/app/src/core/dicts.py
# -*- coding: utf-8 -*-
"""
Цей модуль призначений для визначення системних довідників, які не зберігаються
в базі даних, а є частиною коду, наприклад, у вигляді Enum-класів.
Це можуть бути типи, які рідко змінюються або жорстко пов'язані з логікою коду.

Однак, згідно з `technical-task.md`, більшість довідників (статуси, ролі, типи груп,
типи завдань, типи бонусів, типи інтеграцій, типи користувачів)
мають бути моделями в базі даних та налаштовуватися супер-адміністратором.
Тому цей файл може містити лише ті Enum'и, які дійсно не потребують
зберігання в БД або використовуються для внутрішньої логіки до того,
як довідники з БД будуть завантажені.

Наприклад, тут могли б бути Enum'и для:
- Категорій інтеграцій (`IntegrationModel.category`)
- Каналів сповіщень (`NotificationChannel`)
- Типів транзакцій (`TransactionType`)
- Типів умов для бейджів (`BadgeConditionType`)
- Типів рейтингів (`RatingType`)
- Кодів звітів (`ReportCode`)
- Рівнів логування (хоча вони зазвичай стандартні: DEBUG, INFO, WARNING, ERROR, CRITICAL)

Якщо ці значення також будуть зберігатися в довідниках БД (для гнучкості),
то цей файл може бути менш задіяним або містити лише ті Enum'и,
що використовуються на ранніх етапах ініціалізації або в тестах.
"""

from enum import Enum

# --- Приклад Enum для типів користувачів (якщо не з довідника БД) ---
# Згідно ТЗ: "(довідник чи enum) типи користувачів"
# Якщо це буде Enum, то він може бути тут.
# Але також є константи в `core.constants.py` (USER_TYPE_SUPERADMIN тощо),
# які посилаються на коди з довідника БД.
# Якщо довідник в БД є першоджерелом, то цей Enum може бути зайвим або
# використовуватися для валідації значень, отриманих з БД.
#
# class UserTypeEnum(str, Enum):
#     """Типи користувачів системи."""
#     SUPERADMIN = "superadmin"
#     ADMIN = "admin" # Загальний адмін системи (якщо є)
#     USER = "user"   # Звичайний користувач
#     BOT = "bot"     # Системний бот
#     # GROUP_ADMIN та GROUP_USER - це ролі в контексті групи, а не глобальні типи користувачів.
#     # Хоча `UserModel.user_type_code` може мати значення "admin" для адміна групи,
#     # а "user" для звичайного користувача.
#     # Це потребує узгодження з `UserRoleModel` та логікою.
#     # Поки що константи в `constants.py` виглядають кращим рішенням,
#     # якщо типи користувачів - це довідник.

# --- Enum для каналів сповіщень ---
# Ці коди використовуються в NotificationTemplateModel та NotificationDeliveryModel.
# Мають відповідати константам з `core.constants.py`.
class NotificationChannelEnum(str, Enum):
    """Канали доставки сповіщень."""
    IN_APP = "IN_APP"             # Внутрішнє сповіщення в додатку
    EMAIL = "EMAIL"               # Електронна пошта (може бути розбито на SUBJECT/BODY)
    SMS = "SMS"                   # SMS повідомлення
    PUSH_FCM = "PUSH_FCM"         # Push через Firebase Cloud Messaging
    PUSH_APNS = "PUSH_APNS"       # Push через Apple Push Notification Service
    TELEGRAM_BOT = "TELEGRAM_BOT" # Через Telegram бота
    SLACK = "SLACK"               # Через Slack
    # ... інші можливі канали ...

    @classmethod
    def get_email_channels(cls) -> List['NotificationChannelEnum']:
        """Повертає канали, пов'язані з email (наприклад, для тіла, теми)."""
        # Якщо будуть окремі канали для EMAIL_SUBJECT, EMAIL_BODY_HTML, EMAIL_BODY_TEXT
        return [cls.EMAIL] # Поки що один загальний EMAIL


# --- Enum для типів транзакцій ---
# Ці коди використовуються в `TransactionModel.transaction_type_code`.
# Мають відповідати константам з `core.constants.py`.
class TransactionTypeEnum(str, Enum):
    """Типи фінансових транзакцій по бонусних рахунках."""
    TASK_REWARD = "TASK_REWARD"                 # Нарахування за виконання завдання
    TASK_PENALTY = "TASK_PENALTY"               # Штраф за завдання
    REWARD_PURCHASE = "REWARD_PURCHASE"         # Списання за купівлю нагороди
    MANUAL_CREDIT = "MANUAL_CREDIT"             # Ручне нарахування адміністратором
    MANUAL_DEBIT = "MANUAL_DEBIT"               # Ручне списання адміністратором
    THANK_YOU_SENT = "THANK_YOU_SENT"           # Відправка "подяки" іншому користувачеві (списання)
    THANK_YOU_RECEIVED = "THANK_YOU_RECEIVED"   # Отримання "подяки" (нарахування)
    INITIAL_BALANCE = "INITIAL_BALANCE"         # Встановлення початкового балансу (якщо потрібно)
    PROPOSAL_BONUS = "PROPOSAL_BONUS"           # Бонус за вдалу пропозицію завдання
    STREAK_BONUS = "STREAK_BONUS"               # Бонус за серію виконаних завдань
    SYSTEM_ADJUSTMENT_CREDIT = "SYSTEM_ADJUSTMENT_CREDIT" # Системне нарахування
    SYSTEM_ADJUSTMENT_DEBIT = "SYSTEM_ADJUSTMENT_DEBIT"   # Системне списання
    # ... інші типи ...


# --- Enum для типів умов отримання бейджів ---
# Використовується в `BadgeModel.condition_type_code`.
class BadgeConditionTypeEnum(str, Enum):
    """Типи умов для отримання бейджів."""
    TASK_COUNT_TOTAL = "TASK_COUNT_TOTAL" # Загальна кількість виконаних завдань
    TASK_COUNT_TYPE = "TASK_COUNT_TYPE"   # Кількість завдань певного типу
    TASK_STREAK = "TASK_STREAK"           # Послідовне виконання завдань
    FIRST_TO_COMPLETE_TASK = "FIRST_TO_COMPLETE_TASK" # Перший, хто виконав конкретне завдання
    SPECIFIC_TASK_COMPLETED = "SPECIFIC_TASK_COMPLETED" # Виконання конкретного завдання (не обов'язково перший)
    MANUAL_AWARD = "MANUAL_AWARD"         # Ручне присудження адміністратором
    CUSTOM_EVENT = "CUSTOM_EVENT"         # Спрацювання кастомної події
    BONUS_POINTS_EARNED = "BONUS_POINTS_EARNED" # Накопичення певної кількості бонусів
    # ... інші типи ...


# --- Enum для типів рейтингів ---
# Використовується в `RatingModel.rating_type_code`.
class RatingTypeEnum(str, Enum):
    """Типи рейтингів користувачів."""
    BY_TASKS_COMPLETED_OVERALL = "TASKS_COMPLETED_OVERALL" # За кількістю виконаних завдань (за весь час)
    BY_BONUS_POINTS_EARNED_OVERALL = "BONUS_POINTS_EARNED_OVERALL" # За заробленими бонусами (за весь час)
    BY_CURRENT_BALANCE = "CURRENT_BALANCE" # За поточним балансом бонусів

    BY_TASKS_COMPLETED_PERIOD = "TASKS_COMPLETED_PERIOD" # За завданнями за період (тиждень, місяць)
    BY_BONUS_POINTS_EARNED_PERIOD = "BONUS_POINTS_EARNED_PERIOD" # За бонусами за період
    # ... інші типи ...


# --- Enum для кодів звітів ---
# Використовується в `ReportModel.report_code`.
class ReportCodeEnum(str, Enum):
    """Коди (типи) звітів, що генеруються системою."""
    USER_ACTIVITY = "USER_ACTIVITY"                 # Активність користувачів
    TASK_POPULARITY = "TASK_POPULARITY"             # Популярність завдань
    REWARD_POPULARITY = "REWARD_POPULARITY"           # Популярність нагород
    BONUS_DYNAMICS = "BONUS_DYNAMICS"               # Динаміка накопичення/витрат бонусів
    INACTIVE_USERS = "INACTIVE_USERS"               # Неактивні користувачі
    LAGGING_USERS = "LAGGING_USERS"                 # "Відстаючі" користувачі
    GROUP_OVERVIEW = "GROUP_OVERVIEW"               # Загальний огляд по групі
    USER_PERSONAL_PROGRESS = "USER_PERSONAL_PROGRESS" # Персональний звіт для користувача
    # Для суперадміна:
    ABANDONED_GROUPS = "ABANDONED_GROUPS"           # Групи без користувачів
    INACTIVE_GROUPS_REPORT = "INACTIVE_GROUPS_REPORT" # Неактивні групи (за певний період)
    # ... інші типи звітів ...


# TODO: Переглянути, які з цих Enum дійсно потрібні як Enum в коді,
# а які краще залишити як рядкові константи в `constants.py`,
# особливо якщо їх значення будуть завантажуватися з довідників БД.
#
# Якщо значення Enum використовуються для валідації в Pydantic схемах,
# то їх визначення тут є доречним.
# Наприклад, в схемі: `channel: NotificationChannelEnum`
#
# Для тих кодів, що зберігаються в довідниках БД (статуси, ролі, типи груп тощо),
# використання Enum тут може бути для зручності розробника, але першоджерелом
# є БД. Константи в `constants.py` для кодів з БД також є хорошим підходом.
#
# Поки що визначено декілька Enum'ів, які можуть бути корисними для валідації
# та типізації в коді, навіть якщо деякі з них мають аналоги в довідниках БД.
# Це допомагає уникнути "магічних рядків".
#
# `UserTypeEnum` закоментований, оскільки типи користувачів (superadmin, admin, user, bot)
# краще визначати через довідник `UserRoleModel` або `UserModel.user_type_code`
# з відповідними константами в `constants.py`.
#
# Все готово для цього файлу.
# Він містить Enum'и, які можуть бути використані для типізації та валідації
# кодів, що передаються в API або використовуються в логіці.
# Це доповнює константи, визначені в `constants.py`.
#
# Все готово.
