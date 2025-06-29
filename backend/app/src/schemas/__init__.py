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

# Схеми, які точно використовують рядкові посилання і потребують rebuild:

# 0. UserPublicSchema - від неї можуть залежати багато інших схем, включаючи FileSchema, AvatarSchema.
# Важливо, щоб вона була оброблена однією з перших серед тих, хто має залежності.
if hasattr(auth, 'user') and hasattr(auth.user, 'UserPublicSchema'):
    auth.user.UserPublicSchema.model_rebuild()

# 1. Схеми з модуля 'files', оскільки AvatarSchema залежить від FileSchema.
if hasattr(files, 'file') and hasattr(files.file, 'FileSchema'):
    files.file.FileSchema.model_rebuild() # FileSchema може залежати від UserPublicSchema
if hasattr(files, 'avatar') and hasattr(files.avatar, 'AvatarSchema'):
    files.avatar.AvatarSchema.model_rebuild() # AvatarSchema залежить від FileSchema та UserPublicSchema

# 2. Тепер схеми з модуля 'auth', зокрема UserSchema, яка залежить від AvatarSchema.
if hasattr(auth, 'user') and hasattr(auth.user, 'UserSchema'):
    auth.user.UserSchema.model_rebuild()
# Інші схеми з auth.user, якщо вони теж використовують ForwardRef
if hasattr(auth, 'user') and hasattr(auth.user, 'UserCreateSchema'):
    auth.user.UserCreateSchema.model_rebuild()
if hasattr(auth, 'user') and hasattr(auth.user, 'UserUpdateSchema'):
    auth.user.UserUpdateSchema.model_rebuild()
if hasattr(auth, 'user') and hasattr(auth.user, 'UserPasswordUpdateSchema'):
    auth.user.UserPasswordUpdateSchema.model_rebuild()
if hasattr(auth, 'user') and hasattr(auth.user, 'UserAdminUpdateSchema'):
    auth.user.UserAdminUpdateSchema.model_rebuild()

# 3. Схеми з модуля 'bonuses'
if hasattr(bonuses, 'account') and hasattr(bonuses.account, 'AccountSchema'):
    bonuses.account.AccountSchema.model_rebuild() # AccountSchema залежить від UserPublicSchema, TransactionSchema
if hasattr(bonuses, 'transaction') and hasattr(bonuses.transaction, 'TransactionSchema'):
    bonuses.transaction.TransactionSchema.model_rebuild() # TransactionSchema залежить від AccountSchema, UserPublicSchema
# Порядок AccountSchema та TransactionSchema може бути важливим, якщо вони посилаються одна на одну.
# Якщо TransactionSchema в AccountSchema, то TransactionSchema.model_rebuild() має бути першим.
# Якщо AccountSchema в TransactionSchema, то AccountSchema.model_rebuild() має бути першим.
# Поточний код: AccountSchema -> TransactionSchema; TransactionSchema -> AccountSchema. Цикл.
# Pydantic v2 має краще справлятися з цим, якщо обидві вже імпортовані.
# Залишимо поточний порядок, але маємо на увазі.
# Якщо AccountSchema містить List[TransactionSchema], а TransactionSchema містить Optional[AccountSchema],
# то, можливо, TransactionSchema.model_rebuild() перед AccountSchema.model_rebuild() буде краще.
# Давайте спробуємо так:
# if hasattr(bonuses, 'transaction') and hasattr(bonuses.transaction, 'TransactionSchema'):
#     bonuses.transaction.TransactionSchema.model_rebuild()
# if hasattr(bonuses, 'account') and hasattr(bonuses.account, 'AccountSchema'):
#     bonuses.account.AccountSchema.model_rebuild()
# Поки що залишу як є, Pydantic v2 має впоратися після того, як всі модулі завантажені.

if hasattr(bonuses, 'account') and hasattr(bonuses.account, 'AccountCreateSchema'): # Зазвичай не мають ForwardRef
    bonuses.account.AccountCreateSchema.model_rebuild()
if hasattr(bonuses, 'account') and hasattr(bonuses.account, 'AccountUpdateSchema'):
    bonuses.account.AccountUpdateSchema.model_rebuild()


# 4. Інші модулі по порядку
if hasattr(groups, 'group') and hasattr(groups.group, 'GroupSchema'):
    groups.group.GroupSchema.model_rebuild()
if hasattr(groups, 'membership') and hasattr(groups.membership, 'GroupMembershipSchema'):
    groups.membership.GroupMembershipSchema.model_rebuild() # Може залежати від UserSchema, GroupSchema

if hasattr(tasks, 'task') and hasattr(tasks.task, 'TaskSchema'):
    tasks.task.TaskSchema.model_rebuild() # Може залежати від UserPublicSchema, TaskTypeSchema
if hasattr(tasks, 'assignment') and hasattr(tasks.assignment, 'TaskAssignmentSchema'):
    tasks.assignment.TaskAssignmentSchema.model_rebuild()
if hasattr(tasks, 'completion') and hasattr(tasks.completion, 'TaskCompletionSchema'):
    tasks.completion.TaskCompletionSchema.model_rebuild()

if hasattr(notifications, 'notification') and hasattr(notifications.notification, 'NotificationSchema'):
    notifications.notification.NotificationSchema.model_rebuild()


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
