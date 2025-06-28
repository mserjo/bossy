# backend/app/src/core/constants.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає глобальні константи, що використовуються в усьому додатку.
Це можуть бути рядкові константи, числові значення, коди помилок,
назви ролей, статусів, типи сутностей тощо, які є фіксованими
або використовуються для початкової ініціалізації даних.
"""

# --- Константи для назв ролей (коди) ---
# Ці коди повинні відповідати значенням `code` в `UserRoleModel`
# після початкової ініціалізації довідника ролей.
# Використання констант допомагає уникнути помилок при написанні рядків вручну.
ROLE_SUPERADMIN_CODE: str = "superadmin"
ROLE_ADMIN_CODE: str = "group_admin"  # Адміністратор групи
ROLE_USER_CODE: str = "group_user"    # Звичайний користувач групи
# ROLE_BOT_CODE: str = "bot" # Якщо буде окрема роль для ботів

# --- Константи для типів користувачів (коди) ---
# Ці коди повинні відповідати значенням `code` в довіднику типів користувачів (якщо він буде)
# або використовуватися для поля `UserModel.user_type_code`.
USER_TYPE_SUPERADMIN: str = "superadmin" # Головний адміністратор системи
USER_TYPE_ADMIN: str = "admin" # Можливо, загальний адмін (якщо відрізняється від group_admin) - уточнити
USER_TYPE_USER: str = "user"   # Звичайний зареєстрований користувач
USER_TYPE_BOT: str = "bot"     # Системний бот (наприклад, "shadow" для cron задач)

# Імена системних користувачів
SYSTEM_USER_ODIN_USERNAME: str = "odin" # Superadmin
SYSTEM_USER_SHADOW_USERNAME: str = "shadow" # Системний бот

# --- Константи для статусів (коди) ---
# Ці коди повинні відповідати значенням `code` в `StatusModel`.
# Загальні статуси:
STATUS_CREATED_CODE: str = "created"
STATUS_ACTIVE_CODE: str = "active"     # Загальний активний статус
STATUS_INACTIVE_CODE: str = "inactive"   # Загальний неактивний статус
STATUS_PENDING_EMAIL_VERIFICATION_CODE: str = "pending_email_verification" # Очікує підтвердження email
STATUS_DELETED_CODE: str = "deleted"   # Для позначки "м'яко" видалених записів (якщо використовується окремий статус)
STATUS_ARCHIVED_CODE: str = "archived"  # Для архівованих сутностей
STATUS_PENDING_CODE: str = "pending"   # В очікуванні (наприклад, підтвердження)
STATUS_BLOCKED_CODE: str = "blocked"   # Заблоковано
STATUS_REJECTED_CODE: str = "rejected"  # Відхилено
STATUS_APPROVED_CODE: str = "approved"  # Затверджено / Підтверджено
STATUS_CANCELLED_CODE: str = "cancelled" # Скасовано

# Статуси для завдань (`TaskModel.state_id` або `TaskCompletionModel.status_id`):
TASK_STATUS_NEW_CODE: str = "task_new" # Нове завдання (ще не взято в роботу)
TASK_STATUS_IN_PROGRESS_CODE: str = "task_in_progress" # В роботі
TASK_STATUS_PENDING_REVIEW_CODE: str = "task_pending_review" # Виконано, очікує перевірки
TASK_STATUS_COMPLETED_CODE: str = "task_completed" # Виконано та підтверджено
TASK_STATUS_VERIFIED_CODE: str = "task_verified" # Синонім до COMPLETED або окремий крок
TASK_STATUS_REJECTED_CODE: str = "task_rejected" # Відхилено після перевірки
TASK_STATUS_CANCELLED_CODE: str = "task_cancelled" # Скасовано користувачем або системою
TASK_STATUS_BLOCKED_CODE: str = "task_blocked" # Заблоковано (наприклад, адміном)
# Згідно ТЗ: "створено, в роботі, перевірка, підтверджено, відхилено, заблоковано, скасовано, видалено"
# Потрібно узгодити коди з тими, що будуть в довіднику.
# Наприклад, для "підтверджено" може бути TASK_STATUS_CONFIRMED_CODE (поточний TASK_STATUS_COMPLETED_CODE).
# TASK_STATUS_VERIFIED_CODE є синонімом або окремим кроком.
# STATUS_DELETED_CODE є загальним для "м'якого" видалення.

# Статуси для запрошень (`GroupInvitationModel.status_id`):
INVITATION_STATUS_PENDING_CODE: str = "invite_pending"  # Надіслано, очікує відповіді
INVITATION_STATUS_ACCEPTED_CODE: str = "invite_accepted" # Прийнято
INVITATION_STATUS_REJECTED_CODE: str = "invite_rejected" # Відхилено користувачем
INVITATION_STATUS_EXPIRED_CODE: str = "invite_expired"  # Термін дії вийшов
INVITATION_STATUS_CANCELLED_CODE: str = "invite_cancelled" # Скасовано адміністратором

# --- Константи для типів груп (коди) ---
# Відповідають `GroupTypeModel.code`.
GROUP_TYPE_FAMILY_CODE: str = "family"          # Тип групи "Сім'я"
GROUP_TYPE_DEPARTMENT_CODE: str = "department"    # Тип групи "Відділ"
GROUP_TYPE_ORGANIZATION_CODE: str = "organization"  # Тип групи "Організація"
GROUP_TYPE_GENERIC_CODE: str = "generic_group"    # Загальний тип групи

# --- Константи для типів завдань/подій (коди) ---
# Відповідають `TaskTypeModel.code`.
TASK_TYPE_TASK_CODE: str = "task"                # Звичайне завдання
TASK_TYPE_SUBTASK_CODE: str = "subtask"              # Підзавдання
TASK_TYPE_COMPLEX_TASK_CODE: str = "complex_task"    # Складне завдання (можливо, з підзадачами)
TASK_TYPE_TEAM_TASK_CODE: str = "team_task"          # Командне завдання
TASK_TYPE_EVENT_CODE: str = "event"                # Подія (не потребує активного виконання)
TASK_TYPE_PENALTY_CODE: str = "penalty"              # Штраф (як тип завдання/події)

# --- Константи для типів бонусів (коди) ---
# Відповідають `BonusTypeModel.code`.
BONUS_TYPE_POINTS_CODE: str = "points"      # Бонуси у вигляді балів/очок
BONUS_TYPE_STARS_CODE: str = "stars"       # Бонуси у вигляді зірочок
BONUS_TYPE_BONUSES_CODE: str = "bonuses"     # Загальний тип "бонуси"
# ... інші типи бонусів можуть бути додані в довідник `BonusTypeModel` ...

# --- Константи для типів інтеграцій (коди) ---
# Відповідають `IntegrationModel.code`.
INTEGRATION_TYPE_TELEGRAM_CODE: str = "telegram"            # Інтеграція з Telegram
INTEGRATION_TYPE_GOOGLE_CALENDAR_CODE: str = "google_calendar"  # Інтеграція з Google Calendar
INTEGRATION_TYPE_SLACK_CODE: str = "slack"                # Інтеграція зі Slack
# ... інші типи інтеграцій можуть бути додані в довідник `IntegrationModel` ...

# --- Константи для типів транзакцій (коди) ---
# Використовуються в `TransactionModel.transaction_type_code`.
# Також використовуються в `TransactionTypeEnum` в `dicts.py`.
TRANSACTION_TYPE_TASK_REWARD: str = "TASK_REWARD"          # Нагорода за виконання завдання
TRANSACTION_TYPE_TASK_PENALTY: str = "TASK_PENALTY"         # Штраф за завдання
TRANSACTION_TYPE_REWARD_PURCHASE: str = "REWARD_PURCHASE"      # Покупка нагороди за бонуси
TRANSACTION_TYPE_MANUAL_CREDIT: str = "MANUAL_CREDIT"        # Ручне нарахування бонусів адміном
TRANSACTION_TYPE_MANUAL_DEBIT: str = "MANUAL_DEBIT"         # Ручне списання бонусів адміном
TRANSACTION_TYPE_THANK_YOU_SENT: str = "THANK_YOU_SENT"       # Відправка "подяки" іншому користувачу
TRANSACTION_TYPE_THANK_YOU_RECEIVED: str = "THANK_YOU_RECEIVED"   # Отримання "подяки" від іншого користувача
TRANSACTION_TYPE_INITIAL_BALANCE: str = "INITIAL_BALANCE"      # Встановлення початкового балансу
TRANSACTION_TYPE_PROPOSAL_BONUS: str = "PROPOSAL_BONUS"       # Бонус за вдалу пропозицію завдання
TRANSACTION_TYPE_STREAK_BONUS: str = "STREAK_BONUS"         # Бонус за серію виконаних завдань
TRANSACTION_TYPE_SYSTEM_ADJUSTMENT_CREDIT: str = "SYSTEM_ADJUSTMENT_CREDIT" # Системне коригування (нарахування)
TRANSACTION_TYPE_SYSTEM_ADJUSTMENT_DEBIT: str = "SYSTEM_ADJUSTMENT_DEBIT"   # Системне коригування (списання)

# --- Константи для каналів сповіщень (коди) ---
# Використовуються в `NotificationTemplateModel.channel_code`, `NotificationDeliveryModel.channel_code`
# та `NotificationChannelEnum` в `dicts.py`.
NOTIFICATION_CHANNEL_IN_APP: str = "IN_APP"                # Внутрішньо-додаткове сповіщення
NOTIFICATION_CHANNEL_EMAIL: str = "EMAIL"                  # Сповіщення електронною поштою
NOTIFICATION_CHANNEL_SMS: str = "SMS"                    # SMS сповіщення
NOTIFICATION_CHANNEL_PUSH_FCM: str = "PUSH_FCM"              # Push-сповіщення через Firebase Cloud Messaging
NOTIFICATION_CHANNEL_PUSH_APNS: str = "PUSH_APNS"             # Push-сповіщення через Apple Push Notification Service
NOTIFICATION_CHANNEL_TELEGRAM: str = "TELEGRAM_BOT"           # Сповіщення через Telegram бота
NOTIFICATION_CHANNEL_SLACK: str = "SLACK"                  # Сповіщення через Slack
# ... інші канали можуть бути додані ...

# --- Константи для типів сповіщень (коди) ---
# Використовуються в `NotificationModel.notification_type_code`, `NotificationTemplateModel.notification_type_code`
# та `NotificationTypeEnum` в `dicts.py`.
NOTIFICATION_TYPE_TASK_COMPLETED: str = "TASK_COMPLETED_BY_USER" # Завдання виконано користувачем (сповіщення для адміна)
NOTIFICATION_TYPE_TASK_STATUS_CHANGED: str = "TASK_STATUS_CHANGED_FOR_USER" # Статус завдання змінено адміном (сповіщення для користувача)
NOTIFICATION_TYPE_ACCOUNT_TRANSACTION: str = "ACCOUNT_TRANSACTION" # Відбулася транзакція по бонусному рахунку
NOTIFICATION_TYPE_TASK_DEADLINE_REMINDER: str = "TASK_DEADLINE_REMINDER" # Нагадування про термін виконання завдання
NOTIFICATION_TYPE_NEW_GROUP_INVITATION: str = "NEW_GROUP_INVITATION" # Нове запрошення до групи
NOTIFICATION_TYPE_NEW_TASK_ASSIGNED: str = "NEW_TASK_ASSIGNED"    # Користувачу призначено нове завдання
NOTIFICATION_TYPE_NEW_POLL_IN_GROUP: str = "NEW_POLL_IN_GROUP"    # У групі створено нове опитування
NOTIFICATION_TYPE_BIRTHDAY_GREETING: str = "BIRTHDAY_GREETING"    # Автоматичне привітання з днем народження
# ... інші типи сповіщень можуть бути додані ...

# --- Константи для категорій файлів (коди) ---
# Використовуються в `FileModel.file_category_code` та `FileCategoryEnum` в `dicts.py`.
FILE_CATEGORY_USER_AVATAR: str = "USER_AVATAR"          # Аватар користувача
FILE_CATEGORY_GROUP_ICON: str = "GROUP_ICON"           # Іконка групи
FILE_CATEGORY_REWARD_ICON: str = "REWARD_ICON"          # Іконка нагороди
FILE_CATEGORY_BADGE_ICON: str = "BADGE_ICON"           # Іконка бейджа
FILE_CATEGORY_LEVEL_ICON: str = "LEVEL_ICON"           # Іконка рівня
FILE_CATEGORY_TASK_ATTACHMENT: str = "TASK_ATTACHMENT"    # Вкладення до завдання
FILE_CATEGORY_REPORT_FILE: str = "REPORT_FILE"          # Згенерований файл звіту
# ... інші категорії файлів можуть бути додані ...

# --- Константи для типів умов отримання бейджів (коди) ---
# Використовуються в `BadgeConditionTypeEnum` в `dicts.py`.
BADGE_CONDITION_TASK_COUNT_TOTAL: str = "TASK_COUNT_TOTAL"     # Загальна кількість виконаних завдань
BADGE_CONDITION_TASK_COUNT_TYPE: str = "TASK_COUNT_TYPE"      # Кількість виконаних завдань певного типу
BADGE_CONDITION_TASK_STREAK: str = "TASK_STREAK"            # Серія послідовно виконаних завдань
BADGE_CONDITION_FIRST_TO_COMPLETE_TASK: str = "FIRST_TO_COMPLETE_TASK" # Перший, хто виконав певне завдання
BADGE_CONDITION_SPECIFIC_TASK_COMPLETED: str = "SPECIFIC_TASK_COMPLETED" # Виконання конкретного завдання
BADGE_CONDITION_MANUAL_AWARD: str = "MANUAL_AWARD"           # Ручне нагородження бейджем
BADGE_CONDITION_CUSTOM_EVENT: str = "CUSTOM_EVENT"          # Спеціальна подія або умова
BADGE_CONDITION_BONUS_POINTS_EARNED: str = "BONUS_POINTS_EARNED" # Зароблена певна кількість бонусних балів

# --- Константи для типів рейтингів користувачів (коди) ---
# Використовуються в `RatingTypeEnum` в `dicts.py`.
RATING_TYPE_BY_TASKS_COMPLETED_OVERALL: str = "TASKS_COMPLETED_OVERALL" # Рейтинг за загальною кількістю виконаних завдань
RATING_TYPE_BY_BONUS_POINTS_EARNED_OVERALL: str = "BONUS_POINTS_EARNED_OVERALL" # Рейтинг за загальною кількістю зароблених балів
RATING_TYPE_BY_CURRENT_BALANCE: str = "CURRENT_BALANCE"             # Рейтинг за поточним балансом бонусів
RATING_TYPE_BY_TASKS_COMPLETED_PERIOD: str = "TASKS_COMPLETED_PERIOD"   # Рейтинг за кількістю завдань за період
RATING_TYPE_BY_BONUS_POINTS_EARNED_PERIOD: str = "BONUS_POINTS_EARNED_PERIOD" # Рейтинг за кількістю балів за період

# --- Константи для кодів (типів) звітів (коди) ---
# Використовуються в `ReportCodeEnum` в `dicts.py`.
REPORT_CODE_USER_ACTIVITY: str = "USER_ACTIVITY"              # Звіт по активності користувачів
REPORT_CODE_TASK_POPULARITY: str = "TASK_POPULARITY"            # Звіт по популярності завдань
REPORT_CODE_REWARD_POPULARITY: str = "REWARD_POPULARITY"          # Звіт по популярності нагород
REPORT_CODE_BONUS_DYNAMICS: str = "BONUS_DYNAMICS"             # Звіт по динаміці накопичення бонусів
REPORT_CODE_INACTIVE_USERS: str = "INACTIVE_USERS"             # Звіт по неактивних користувачах
REPORT_CODE_LAGGING_USERS: str = "LAGGING_USERS"              # Звіт по "відстаючих" користувачах
REPORT_CODE_GROUP_OVERVIEW: str = "GROUP_OVERVIEW"             # Загальний звіт по групі
REPORT_CODE_USER_PERSONAL_PROGRESS: str = "USER_PERSONAL_PROGRESS"   # Персональний звіт користувача по прогресу
REPORT_CODE_ABANDONED_GROUPS: str = "ABANDONED_GROUPS"           # Звіт по покинутих групах (без користувачів)
REPORT_CODE_INACTIVE_GROUPS_REPORT: str = "INACTIVE_GROUPS_REPORT" # Звіт по неактивних групах

# --- Загальні константи ---
DEFAULT_PAGE_SIZE: int = 20 # Кількість елементів на сторінці за замовчуванням для пагінації
MAX_PAGE_SIZE: int = 100    # Максимальна кількість елементів на сторінці

# Формати дати та часу
DATETIME_FORMAT_TECHNICAL: str = "%Y-%m-%dT%H:%M:%S.%fZ" # ISO 8601 з мілісекундами та Z (UTC)
DATETIME_FORMAT_USER_FRIENDLY: str = "%d.%m.%Y %H:%M:%S" # Приклад для відображення користувачу
DATE_FORMAT_USER_FRIENDLY: str = "%d.%m.%Y"

# Ключі для кешування Redis (приклади)
CACHE_KEY_USER_PROFILE_PREFIX: str = "user_profile:" # user_profile:{user_id}
CACHE_KEY_GROUP_DETAILS_PREFIX: str = "group_details:" # group_details:{group_id}
CACHE_KEY_ALL_STATUSES: str = "all_statuses_dict"
DEFAULT_CACHE_TTL_SECONDS: int = 300 # 5 хвилин

# Назви черг Celery (приклади)
CELERY_QUEUE_DEFAULT: str = "default_celery_queue"
CELERY_QUEUE_NOTIFICATIONS: str = "notifications_celery_queue"
CELERY_QUEUE_REPORTS: str = "reports_celery_queue"

# Інші загальні ліміти або налаштування
MAX_USERNAME_LENGTH: int = 150
MAX_EMAIL_LENGTH: int = 255
MAX_PASSWORD_LENGTH: int = 128 # Максимальна довжина паролю до хешування
MIN_PASSWORD_LENGTH: int = 8

# TODO: Додати інші загальні константи, якщо вони будуть потрібні.
# Наприклад, максимальна довжина інших полів, специфічні формати.

# --- Константи для статусів пропозицій завдань (коди) ---
TASK_PROPOSAL_STATUS_PENDING_CODE: str = "proposal_pending_review" # На розгляді
TASK_PROPOSAL_STATUS_APPROVED_CODE: str = "proposal_approved"     # Прийнято (можливо, створено завдання)
TASK_PROPOSAL_STATUS_REJECTED_CODE: str = "proposal_rejected"     # Відхилено
TASK_PROPOSAL_STATUS_IMPLEMENTED_CODE: str = "proposal_implemented" # Реалізовано (завдання створено і завершено) - опціонально

# --- Константи для статусів доставки сповіщень (коди) ---
# Використовуються в `NotificationDeliveryModel.status_code` та `NotificationDeliveryStatusEnum` в `dicts.py`.
DELIVERY_STATUS_PENDING: str = "PENDING"        # В очікуванні відправки
DELIVERY_STATUS_PROCESSING: str = "PROCESSING"    # Обробляється системою перед відправкою
DELIVERY_STATUS_SENT: str = "SENT"            # Надіслано провайдеру доставки
DELIVERY_STATUS_DELIVERED: str = "DELIVERED"      # Доставлено отримувачу (підтверджено провайдером)
DELIVERY_STATUS_FAILED: str = "FAILED"          # Не вдалося доставити
DELIVERY_STATUS_RETRYING: str = "RETRYING"       # Запланована повторна спроба
DELIVERY_STATUS_OPENED: str = "OPENED"          # Відкрито (наприклад, email або push)
DELIVERY_STATUS_CLICKED: str = "CLICKED"         # Клікнуто посилання в сповіщенні
DELIVERY_STATUS_UNSUBSCRIBED: str = "UNSUBSCRIBED" # Користувач відписався від цього типу сповіщень/каналу

# --- Константи для статусів генерації звітів (коди) ---
REPORT_STATUS_QUEUED: str = "report_queued"          # В черзі на генерацію
REPORT_STATUS_PROCESSING: str = "report_processing"    # В процесі генерації
REPORT_STATUS_COMPLETED: str = "report_completed"     # Генерацію успішно завершено
REPORT_STATUS_FAILED: str = "report_failed"          # Помилка під час генерації
REPORT_STATUS_CANCELLED: str = "report_cancelled"     # Запит на генерацію скасовано (опціонально)
# Дублюючий блок DELIVERY_STATUS_ нижче видалено

# Важливо, щоб значення кодів (наприклад, ROLE_SUPERADMIN_CODE)
# збігалися з тими, що будуть ініціалізовані в довідниках у базі даних.
# Ці константи допомагають уникнути "магічних рядків" у коді.
#
# Цей файл буде поступово наповнюватися константами в міру розробки системи.
# На даному етапі визначено основні групи констант, що можуть знадобитися
# для початкової ініціалізації даних та базової логіки.
#
# Все виглядає добре як початковий набір.
# Потрібно буде переконатися, що ці коди відповідають тим, що будуть
# використовуватися при початковому заповненні довідників (seeding).
#
# Назви констант у форматі UPPER_SNAKE_CASE є стандартною практикою.
# Типізація (`: str`, `: int`) покращує читабельність та допомагає статичним аналізаторам.
#
# Все готово.
