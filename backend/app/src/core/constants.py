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
# TASK_STATUS_BLOCKED_CODE: str = "task_blocked" # Заблоковано (якщо є такий стан для завдань)
# Згідно ТЗ: "створено, в роботі, перевірка, підтверджено, відхилено, заблоковано, скасовано, видалено"
# Потрібно узгодити коди з тими, що будуть в довіднику.
# Наприклад, для "підтверджено" може бути TASK_STATUS_CONFIRMED_CODE.
# Поки що використовую більш описові назви.

# Статуси для запрошень (`GroupInvitationModel.status_id`):
INVITATION_STATUS_PENDING_CODE: str = "invite_pending"  # Надіслано, очікує відповіді
INVITATION_STATUS_ACCEPTED_CODE: str = "invite_accepted" # Прийнято
INVITATION_STATUS_REJECTED_CODE: str = "invite_rejected" # Відхилено користувачем
INVITATION_STATUS_EXPIRED_CODE: str = "invite_expired"  # Термін дії вийшов
INVITATION_STATUS_CANCELLED_CODE: str = "invite_cancelled" # Скасовано адміністратором

# --- Константи для типів груп (коди) ---
# Відповідають `GroupTypeModel.code`.
GROUP_TYPE_FAMILY_CODE: str = "family"
GROUP_TYPE_DEPARTMENT_CODE: str = "department"
GROUP_TYPE_ORGANIZATION_CODE: str = "organization"
GROUP_TYPE_GENERIC_CODE: str = "generic_group" # Загальний тип групи

# --- Константи для типів завдань/подій (коди) ---
# Відповідають `TaskTypeModel.code`.
TASK_TYPE_TASK_CODE: str = "task"
TASK_TYPE_SUBTASK_CODE: str = "subtask"
TASK_TYPE_COMPLEX_TASK_CODE: str = "complex_task"
TASK_TYPE_TEAM_TASK_CODE: str = "team_task"
TASK_TYPE_EVENT_CODE: str = "event"
TASK_TYPE_PENALTY_CODE: str = "penalty" # Штраф як тип завдання/події

# --- Константи для типів бонусів (коди) ---
# Відповідають `BonusTypeModel.code`.
BONUS_TYPE_POINTS_CODE: str = "points"
BONUS_TYPE_STARS_CODE: str = "stars"
BONUS_TYPE_BONUSES_CODE: str = "bonuses" # Загальний
# ... інші з довідника ...

# --- Константи для типів інтеграцій (коди) ---
# Відповідають `IntegrationModel.code`.
INTEGRATION_TYPE_TELEGRAM_CODE: str = "telegram"
INTEGRATION_TYPE_GOOGLE_CALENDAR_CODE: str = "google_calendar"
# ... інші ...

# --- Константи для типів транзакцій (коди) ---
# Використовуються в `TransactionModel.transaction_type_code`.
# TODO: Створити Enum або довідник для цих типів.
TRANSACTION_TYPE_TASK_REWARD: str = "TASK_REWARD"
TRANSACTION_TYPE_TASK_PENALTY: str = "TASK_PENALTY"
TRANSACTION_TYPE_REWARD_PURCHASE: str = "REWARD_PURCHASE"
TRANSACTION_TYPE_MANUAL_CREDIT: str = "MANUAL_CREDIT" # Ручне нарахування
TRANSACTION_TYPE_MANUAL_DEBIT: str = "MANUAL_DEBIT"   # Ручне списання
TRANSACTION_TYPE_THANK_YOU_SENT: str = "THANK_YOU_SENT"
TRANSACTION_TYPE_THANK_YOU_RECEIVED: str = "THANK_YOU_RECEIVED"
TRANSACTION_TYPE_INITIAL_BALANCE: str = "INITIAL_BALANCE" # Початкове встановлення балансу
TRANSACTION_TYPE_PROPOSAL_BONUS: str = "PROPOSAL_BONUS" # Бонус за вдалу пропозицію завдання

# --- Константи для каналів сповіщень (коди) ---
# Використовуються в `NotificationTemplateModel.channel_code` та `NotificationDeliveryModel.channel_code`.
# TODO: Створити Enum або довідник.
NOTIFICATION_CHANNEL_IN_APP: str = "IN_APP"
NOTIFICATION_CHANNEL_EMAIL: str = "EMAIL" # Може бути розбито на EMAIL_SUBJECT, EMAIL_BODY
NOTIFICATION_CHANNEL_SMS: str = "SMS"
NOTIFICATION_CHANNEL_PUSH_FCM: str = "PUSH_FCM" # Firebase Cloud Messaging
NOTIFICATION_CHANNEL_PUSH_APNS: str = "PUSH_APNS" # Apple Push Notification Service
NOTIFICATION_CHANNEL_TELEGRAM: str = "TELEGRAM_BOT"
# ... інші ...

# --- Константи для типів сповіщень (коди) ---
# Використовуються в `NotificationModel.notification_type_code` та `NotificationTemplateModel.notification_type_code`.
# TODO: Створити Enum або довідник.
NOTIFICATION_TYPE_TASK_COMPLETED: str = "TASK_COMPLETED_BY_USER" # Користувач виконав, адміну
NOTIFICATION_TYPE_TASK_STATUS_CHANGED: str = "TASK_STATUS_CHANGED_FOR_USER" # Адмін змінив статус, користувачу
NOTIFICATION_TYPE_ACCOUNT_TRANSACTION: str = "ACCOUNT_TRANSACTION" # Рух по рахунку
NOTIFICATION_TYPE_TASK_DEADLINE_REMINDER: str = "TASK_DEADLINE_REMINDER"
NOTIFICATION_TYPE_NEW_GROUP_INVITATION: str = "NEW_GROUP_INVITATION"
NOTIFICATION_TYPE_NEW_TASK_ASSIGNED: str = "NEW_TASK_ASSIGNED"
NOTIFICATION_TYPE_NEW_POLL_IN_GROUP: str = "NEW_POLL_IN_GROUP"
NOTIFICATION_TYPE_BIRTHDAY_GREETING: str = "BIRTHDAY_GREETING" # Привітання з днем народження
# ... інші ...

# --- Константи для категорій файлів (коди) ---
# Використовуються в `FileModel.file_category_code`.
# TODO: Створити Enum або довідник.
FILE_CATEGORY_USER_AVATAR: str = "USER_AVATAR"
FILE_CATEGORY_GROUP_ICON: str = "GROUP_ICON"
FILE_CATEGORY_REWARD_ICON: str = "REWARD_ICON"
FILE_CATEGORY_BADGE_ICON: str = "BADGE_ICON"
FILE_CATEGORY_LEVEL_ICON: str = "LEVEL_ICON"
FILE_CATEGORY_TASK_ATTACHMENT: str = "TASK_ATTACHMENT"
FILE_CATEGORY_REPORT_FILE: str = "REPORT_FILE"
# ... інші ...


# --- Загальні константи ---
DEFAULT_PAGE_SIZE: int = 20 # Кількість елементів на сторінці за замовчуванням для пагінації
MAX_PAGE_SIZE: int = 100    # Максимальна кількість елементів на сторінці

# TODO: Додати інші константи, якщо вони будуть потрібні.
# Наприклад, максимальна довжина певних полів, формати дат,
# ключі для кешування Redis, назви черг Celery тощо.

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
