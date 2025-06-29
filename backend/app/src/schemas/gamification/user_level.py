# backend/app/src/schemas/gamification/user_level.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає Pydantic схеми для моделі `UserLevelModel`.
Схеми використовуються для відображення інформації про рівні, досягнуті користувачами.
Записи `UserLevelModel` зазвичай створюються та оновлюються автоматично системою
на основі досягнень користувачів, а не через прямі API запити на створення/оновлення.
"""

from pydantic import Field
from typing import Optional, List, ForwardRef
import uuid
from datetime import datetime

from backend.app.src.schemas.base import BaseSchema, AuditDatesSchema
# Потрібно буде імпортувати схеми для зв'язків:
# from backend.app.src.schemas.auth.user import UserPublicSchema
# from backend.app.src.schemas.groups.group import GroupSimpleSchema
# from backend.app.src.schemas.gamification.level import LevelSchema

from typing import TYPE_CHECKING # Додано TYPE_CHECKING

if TYPE_CHECKING:
    from backend.app.src.schemas.auth.user import UserPublicSchema
    from backend.app.src.schemas.groups.group import GroupSimpleSchema
    from backend.app.src.schemas.gamification.level import LevelSchema

# UserPublicSchema = ForwardRef('backend.app.src.schemas.auth.user.UserPublicSchema') # Перенесено
# GroupSimpleSchema = ForwardRef('backend.app.src.schemas.groups.group.GroupSimpleSchema') # Перенесено
# LevelSchema = ForwardRef('backend.app.src.schemas.gamification.level.LevelSchema') # Перенесено

# --- Схема для відображення інформації про досягнутий рівень користувачем (для читання) ---
class UserLevelSchema(AuditDatesSchema): # Успадковує id, created_at, updated_at
    """
    Схема для представлення запису про досягнення рівня користувачем в групі.
    `created_at` використовується як `achieved_at`.
    """
    user_id: uuid.UUID = Field(..., description="ID користувача")
    group_id: uuid.UUID = Field(..., description="ID групи, в якій досягнуто рівень")
    level_id: uuid.UUID = Field(..., description="ID досягнутого рівня")

    # Поле `is_current` було в моделі, але обговорювалося його видалення
    # або зміна логіки. Якщо воно є в моделі і потрібне в схемі:
    is_current: Optional[bool] = Field(None, description="Прапорець, чи є цей рівень поточним для користувача в групі (якщо модель підтримує це)")
    # Якщо `is_current` немає в моделі, то це поле не потрібне тут.
    # Поточна модель `UserLevelModel` (після обговорень) МАЄ `is_current`.

    # --- Розгорнуті зв'язки (приклад) ---
    user: Optional['UserPublicSchema'] = Field(None, description="Користувач, який досяг рівня") # Рядкове посилання
    group: Optional['GroupSimpleSchema'] = Field(None, description="Група, в якій досягнуто рівень") # Рядкове посилання
    level: Optional['LevelSchema'] = Field(None, description="Досягнутий рівень") # Рядкове посилання


# --- Схема для створення запису про досягнення рівня (зазвичай внутрішнє використання) ---
class UserLevelCreateSchema(BaseSchema):
    """
    Схема для створення запису про досягнення рівня користувачем.
    Зазвичай використовується внутрішньою логікою системи, а не через прямий API.
    """
    user_id: uuid.UUID = Field(..., description="ID користувача")
    group_id: uuid.UUID = Field(..., description="ID групи") # Потрібно для контексту і можливих UniqueConstraint
    level_id: uuid.UUID = Field(..., description="ID досягнутого рівня")
    # achieved_at: datetime # Встановлюється автоматично як created_at
    is_current: bool = Field(default=True, description="Чи є цей рівень поточним (сервіс має оновити попередні)")


# --- Схема для оновлення запису про досягнення рівня (дуже рідко використовується) ---
# Зазвичай, якщо користувач досягає нового рівня, створюється новий запис UserLevel,
# а старий (якщо is_current використовується) позначається is_current=False.
# Пряме оновлення існуючого запису UserLevel (наприклад, зміна level_id) нетипове.
# class UserLevelUpdateSchema(BaseSchema):
#     """
#     Схема для оновлення запису про досягнення рівня (використовується рідко).
#     """
#     is_current: Optional[bool] = Field(None, description="Оновлення статусу 'поточний'")
#     # Інші поля (user_id, group_id, level_id) зазвичай не змінюються.


# UserLevelSchema.model_rebuild() # Для ForwardRef

# TODO: Переконатися, що схеми відповідають моделі `UserLevelModel`.
# `UserLevelModel` успадковує від `BaseModel` і має `user_id, group_id, level_id, is_current`.
# `UserLevelSchema` успадковує від `AuditDatesSchema` і відображає ці поля.
# Розгорнуті зв'язки `user`, `group`, `level` додані з `ForwardRef`.
#
# `UserLevelCreateSchema` містить поля для створення запису.
# `is_current` за замовчуванням `True`, оскільки новий досягнутий рівень стає поточним.
# Сервіс, що створює цей запис, відповідає за оновлення `is_current=False` для попереднього
# поточного рівня цього користувача в цій групі.
#
# `UserLevelUpdateSchema` закоментована, оскільки оновлення таких записів не є типовою операцією.
#
# Поле `group_id` в `UserLevelSchema` та `UserLevelCreateSchema` важливе, оскільки
# рівні визначаються в контексті групи, і користувач може мати різні рівні в різних групах.
# `UniqueConstraint('user_id', 'level_id')` в моделі гарантує, що користувач досягає
# конкретного рівня (який вже прив'язаний до групи) лише один раз.
# Додаткове `UniqueConstraint('user_id', 'group_id', name='uq_user_group_is_current_true', postgresql_where=(UserLevelModel.is_current == True))`
# (якщо було б додано до моделі) гарантувало б один поточний рівень на користувача в групі.
# Поточна модель `UserLevelModel` (згідно з її файлом) має `UniqueConstraint('user_id', 'level_id')`
# та поле `is_current`. Логіка підтримки `is_current` - на сервісному рівні.
#
# Все виглядає узгоджено.
# `AuditDatesSchema` надає `id, created_at, updated_at`.
# `created_at` використовується як час досягнення рівня.
# `updated_at` - якщо поле `is_current` змінюється.
#
# Все виглядає добре.

UserLevelSchema.model_rebuild()
UserLevelCreateSchema.model_rebuild()
