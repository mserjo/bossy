# backend/app/src/schemas/__init__.py
# -*- coding: utf-8 -*-
"""
Ініціалізаційний файл для пакету схем Pydantic.

Цей файл відповідає за імпорт ключових схем або модулів схем,
а також за централізований виклик `model_rebuild()` для тих схем,
які використовують рядкові анотації типів (ForwardRef) для розв'язання
циклічних залежностей.
"""

# Імпортуємо модулі, що містять схеми, які можуть потребувати `model_rebuild`
# або містять схеми, на які є посилання з інших модулів.
from . import base
from . import auth
from . import bonuses
from . import dictionaries
from . import files
from . import gamification
from . import groups
from . import notifications
from . import system # Хоча тут може не бути ForwardRefs, для повноти
from . import tasks # Може містити ForwardRefs

# Тепер викликаємо model_rebuild() для конкретних схем,
# які використовують рядкові анотації (ForwardRef).
# Порядок тут може бути важливим, якщо схеми залежать одна від одної
# навіть після використання рядкових анотацій, але зазвичай Pydantic v2
# справляється з цим досить добре, якщо всі модулі вже імпортовані.

# Схеми, які точно використовують рядкові посилання і потребують rebuild.
# Порядок викликів model_rebuild важливий: спочатку ті, від яких залежать інші.

# --- Dictionaries (словники) ---
# Зазвичай схеми довідників прості і не мають складних ForwardRef,
# але якщо StatusSchema або BonusTypeSchema мали б їх, їх model_rebuild() був би тут.
# Наприклад:
# if hasattr(dictionaries, 'status') and hasattr(dictionaries.status, 'StatusSchema'):
#     dictionaries.status.StatusSchema.model_rebuild()
# if hasattr(dictionaries, 'bonus_type') and hasattr(dictionaries.bonus_type, 'BonusTypeSchema'):
#     dictionaries.bonus_type.BonusTypeSchema.model_rebuild()

# --- Auth & Users (користувачі та автентифікація) ---
# UserPublicSchema часто використовується іншими.
if hasattr(auth, 'user') and hasattr(auth.user, 'UserPublicSchema'):
    auth.user.UserPublicSchema.model_rebuild()

# FileSchema та AvatarSchema (якщо вони залежать від UserPublicSchema або одна від одної)
if hasattr(files, 'file') and hasattr(files.file, 'FileSchema'):
    files.file.FileSchema.model_rebuild()
if hasattr(files, 'avatar') and hasattr(files.avatar, 'AvatarSchema'):
    files.avatar.AvatarSchema.model_rebuild() # Залежить від FileSchema, UserPublicSchema

# Повна UserSchema (може залежати від AvatarSchema)
if hasattr(auth, 'user') and hasattr(auth.user, 'UserSchema'):
    auth.user.UserSchema.model_rebuild()

# RefreshTokenSchema (може залежати від UserPublicSchema)
if hasattr(auth, 'token') and hasattr(auth.token, 'RefreshTokenSchema'):
    auth.token.RefreshTokenSchema.model_rebuild()

# --- Bonuses (бонуси, рахунки, транзакції, нагороди) ---
# TransactionSchema та AccountSchema мають взаємні посилання.
# Pydantic v2 має обробити це, якщо обидва типи відомі.
# Спробуємо такий порядок:
if hasattr(bonuses, 'transaction') and hasattr(bonuses.transaction, 'TransactionSchema'):
    bonuses.transaction.TransactionSchema.model_rebuild()
if hasattr(bonuses, 'account') and hasattr(bonuses.account, 'AccountSchema'):
    bonuses.account.AccountSchema.model_rebuild()

# RewardSchema залежить від StatusSchema (з dictionaries) та BonusTypeSchema (з dictionaries)
# Також може залежати від FileSchema.
if hasattr(bonuses, 'reward') and hasattr(bonuses.reward, 'RewardSchema'):
    bonuses.reward.RewardSchema.model_rebuild()

# BonusAdjustmentSchema (якщо має ForwardRefs)
if hasattr(bonuses, 'bonus_adjustment') and hasattr(bonuses.bonus_adjustment, 'BonusAdjustmentSchema'):
    bonuses.bonus_adjustment.BonusAdjustmentSchema.model_rebuild()


# --- Groups (групи та членство) ---
if hasattr(groups, 'group') and hasattr(groups.group, 'GroupSchema'):
    groups.group.GroupSchema.model_rebuild() # Може залежати від UserPublicSchema (для адмінів/творця)
if hasattr(groups, 'membership') and hasattr(groups.membership, 'GroupMembershipSchema'):
    groups.membership.GroupMembershipSchema.model_rebuild() # Залежить від UserSchema, GroupSchema, UserRoleSchema

# --- Tasks (завдання) ---
if hasattr(tasks, 'task') and hasattr(tasks.task, 'TaskSchema'):
    tasks.task.TaskSchema.model_rebuild() # Може залежати від UserPublicSchema, TaskTypeSchema, StatusSchema
if hasattr(tasks, 'assignment') and hasattr(tasks.assignment, 'TaskAssignmentSchema'):
    tasks.assignment.TaskAssignmentSchema.model_rebuild() # Залежить від TaskSchema, UserSchema
if hasattr(tasks, 'completion') and hasattr(tasks.completion, 'TaskCompletionSchema'):
    tasks.completion.TaskCompletionSchema.model_rebuild() # Залежить від TaskSchema, UserSchema

# --- Notifications (сповіщення) ---
if hasattr(notifications, 'notification') and hasattr(notifications.notification, 'NotificationSchema'):
    notifications.notification.NotificationSchema.model_rebuild() # Може залежати від UserSchema
if hasattr(notifications, 'template') and hasattr(notifications.template, 'NotificationTemplateSchema'):
    notifications.template.NotificationTemplateSchema.model_rebuild() # Може залежати від GroupSimpleSchema, StatusSchema
if hasattr(notifications, 'delivery') and hasattr(notifications.delivery, 'NotificationDeliverySchema'):
    notifications.delivery.NotificationDeliverySchema.model_rebuild() # Залежить від NotificationSchema

# --- Gamification (гейміфікація: рівні, бейджі) ---
# Схеми з gamification можуть залежати від UserSchema, GroupSchema, TaskSchema тощо.
if hasattr(gamification, 'level') and hasattr(gamification.level, 'LevelSchema'):
    gamification.level.LevelSchema.model_rebuild()
if hasattr(gamification, 'user_level') and hasattr(gamification.user_level, 'UserLevelSchema'): # Виправлено шлях
    gamification.user_level.UserLevelSchema.model_rebuild() # Залежить від UserSchema, LevelSchema
if hasattr(gamification, 'badge') and hasattr(gamification.badge, 'BadgeSchema'):
    gamification.badge.BadgeSchema.model_rebuild()
if hasattr(gamification, 'achievement') and hasattr(gamification.achievement, 'AchievementSchema'): # Припускаючи назву схеми
    gamification.achievement.AchievementSchema.model_rebuild() # Залежить від UserSchema, BadgeSchema

# Інші схеми Create/Update зазвичай не потребують model_rebuild, якщо вони не містять ForwardRef.
# Наприклад:
# if hasattr(auth, 'user') and hasattr(auth.user, 'UserCreateSchema'):
#     auth.user.UserCreateSchema.model_rebuild()
# ... і так далі для інших схем Create/Update, якщо вони складні.
# Зазвичай це не потрібно.


# Важливо: цей файл буде виконано, коли будь-який модуль з `backend.app.src.schemas`
# буде імпортовано вперше. Це забезпечить, що всі модулі схем завантажені
# перед тим, як викликається `model_rebuild()`.

# Логування для відладки (можна прибрати в продакшені)
try:
    from backend.app.src.config.logging import get_logger # type: ignore
    log = get_logger(__name__)
    log.info("Pydantic schemas __init__ executed and model_rebuild() calls attempted.")
except ImportError:
    # Може статися, якщо логер ще не налаштований або є проблеми з імпортом конфігурації
    import logging
    logging.info("Pydantic schemas __init__ executed (fallback logger).")
