# backend/app/src/schemas/groups/__init__.py
# -*- coding: utf-8 -*-
"""
Ініціалізаційний файл для пакету схем, пов'язаних з групами (`groups`).

Цей файл робить доступними основні схеми груп для імпорту з пакету
`backend.app.src.schemas.groups`.

Приклад імпорту:
from backend.app.src.schemas.groups import GroupSchema, GroupCreateSchema

Також цей файл може використовуватися для визначення змінної `__all__`,
яка контролює, що саме експортується при використанні `from . import *`.
"""

# Імпорт конкретних схем, пов'язаних з групами
from backend.app.src.schemas.groups.group import (
    GroupSchema,
    GroupSimpleSchema,
    GroupCreateSchema,
    GroupUpdateSchema,
)
from backend.app.src.schemas.groups.settings import (
    GroupSettingsSchema,
    GroupSettingsCreateSchema,
    GroupSettingsUpdateSchema,
)
from backend.app.src.schemas.groups.membership import (
    GroupMembershipSchema,
    GroupMembershipCreateSchema,
    GroupMembershipUpdateSchema,
)
from backend.app.src.schemas.groups.invitation import (
    GroupInvitationSchema,
    GroupInvitationCreateSchema,
    GroupInvitationUpdateSchema,
)
from backend.app.src.schemas.groups.template import (
    GroupTemplateSchema,
    GroupTemplateCreateSchema,
    GroupTemplateUpdateSchema,
)
from backend.app.src.schemas.groups.poll import (
    PollSchema,
    PollCreateSchema,
    PollUpdateSchema,
    PollOptionSchema,
    PollOptionCreateSchema,
    PollOptionUpdateSchema,
    PollVoteSchema,
    PollVoteCreateSchema,
)

# Визначення змінної `__all__` для контролю публічного API пакету.
__all__ = [
    # Group Schemas
    "GroupSchema",
    "GroupSimpleSchema",
    "GroupCreateSchema",
    "GroupUpdateSchema",

    # Group Settings Schemas
    "GroupSettingsSchema",
    "GroupSettingsCreateSchema",
    "GroupSettingsUpdateSchema",

    # Group Membership Schemas
    "GroupMembershipSchema",
    "GroupMembershipCreateSchema",
    "GroupMembershipUpdateSchema",

    # Group Invitation Schemas
    "GroupInvitationSchema",
    "GroupInvitationCreateSchema",
    "GroupInvitationUpdateSchema",

    # Group Template Schemas
    "GroupTemplateSchema",
    "GroupTemplateCreateSchema",
    "GroupTemplateUpdateSchema",

    # Poll Schemas
    "PollSchema",
    "PollCreateSchema",
    "PollUpdateSchema",
    "PollOptionSchema",
    "PollOptionCreateSchema",
    "PollOptionUpdateSchema",
    "PollVoteSchema",
    "PollVoteCreateSchema",
]

# Виклик model_rebuild для схем, що використовують ForwardRef,
# щоб Pydantic міг коректно розпізнати типи.
# Це потрібно робити після того, як всі залежні схеми визначені та імпортовані.
# Pydantic v2 може обробляти це автоматично в багатьох випадках.
# Якщо виникають помилки `NameError` через ForwardRef, розкоментуйте відповідні model_rebuild().

# Приклад:
# GroupSchema.model_rebuild(force=True)
# GroupSettingsSchema.model_rebuild(force=True)
# GroupMembershipSchema.model_rebuild(force=True)
# PollSchema.model_rebuild(force=True)
# PollOptionSchema.model_rebuild(force=True) # Якщо PollOptionSchema має ForwardRef на PollSchema
# PollVoteSchema.model_rebuild(force=True)

# TODO: Перевірити, чи потрібен явний виклик model_rebuild для Pydantic v2.
# Зазвичай, якщо всі файли імпортуються в `__init__.py`, Pydantic v2
# має впоратися з розв'язанням ForwardRef автоматично під час першого використання схеми.
# Якщо ні, то тут місце для `model_rebuild()`.
# Наприклад, `GroupSchema` використовує `ForwardRef` для `GroupSettingsSchema` та `GroupMembershipSchema`.
# `GroupMembershipSchema` використовує `ForwardRef` для `UserPublicSchema`, `GroupSimpleSchema`, `UserRoleSchema`, `StatusSchema`.
# І так далі.
# Оскільки всі вони імпортуються тут, Pydantic має мати всю інформацію.
# Залишаю закоментованим, оскільки Pydantic v2 зазвичай справляється.
# Якщо будуть помилки, їх потрібно буде розкоментувати та правильно вказати залежності.
# Наприклад, якщо А залежить від Б, а Б від А, то `A.model_rebuild()` та `B.model_rebuild()`.
# Або ж, якщо А залежить від Б, то `A.model_rebuild()` після визначення Б.
#
# Порядок імпорту в цьому файлі може мати значення, якщо не покладатися повністю на автоматичне
# розв'язання ForwardRef. Але з `ForwardRef` це менш критично.
#
# Важливо, щоб всі схеми, на які є `ForwardRef`, були імпортовані до моменту,
# коли Pydantic намагається їх розв'язати (зазвичай при першому використанні схеми з `ForwardRef`).
# Оскільки цей `__init__.py` імпортує все, це має допомогти.
# Якщо `model_rebuild` потрібен, його краще викликати для кожної схеми, що містить `ForwardRef`,
# ПІСЛЯ того, як всі схеми, на які вона посилається, були визначені та імпортовані.
# Це може означати, що `model_rebuild` викликається в кінці цього файлу
# або в головному `schemas/__init__.py`.
# Поки що залишаю без явних викликів `model_rebuild`.
