# backend/app/src/schemas/files/avatar.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає Pydantic схеми для моделі `AvatarModel`.
Схеми використовуються для відображення інформації про аватари користувачів.
Записи `AvatarModel` зазвичай створюються та оновлюються системою
при завантаженні/зміні аватара користувачем.
"""

from pydantic import Field, HttpUrl
from typing import Optional, List, ForwardRef
import uuid
from datetime import datetime

from backend.app.src.schemas.base import BaseSchema, AuditDatesSchema
# Потрібно буде імпортувати схеми для зв'язків:
# from backend.app.src.schemas.auth.user import UserPublicSchema (для user)
# from backend.app.src.schemas.files.file import FileSchema (для file)

UserPublicSchema = ForwardRef('backend.app.src.schemas.auth.user.UserPublicSchema')
FileSchema = ForwardRef('backend.app.src.schemas.files.file.FileSchema')

# --- Схема для відображення інформації про аватар (для читання) ---
class AvatarSchema(AuditDatesSchema): # Успадковує id, created_at, updated_at
    """
    Схема для представлення запису про аватар користувача.
    `created_at` - час встановлення/завантаження цього аватара.
    """
    user_id: uuid.UUID = Field(..., description="ID користувача, якому належить аватар")
    file_id: uuid.UUID = Field(..., description="ID файлу (з FileModel), який є аватаром")
    is_current: bool = Field(..., description="Чи є цей аватар поточним (активним) для користувача")

    # --- Розгорнуті зв'язки (приклад) ---
    user: Optional[UserPublicSchema] = Field(None, description="Користувач, якому належить аватар") # Може бути корисним для адмінки
    file: Optional[FileSchema] = Field(None, description="Інформація про файл аватара (включаючи URL)")


# --- Схема для створення/встановлення аватара (зазвичай внутрішнє використання) ---
class AvatarCreateSchema(BaseSchema):
    """
    Схема для створення запису про аватар.
    Використовується сервісом після завантаження файлу аватара та створення запису FileModel.
    """
    user_id: uuid.UUID = Field(..., description="ID користувача")
    file_id: uuid.UUID = Field(..., description="ID файлу, що стає аватаром")
    # is_current: bool = Field(default=True) # Сервіс має встановити цей прапорець та оновити попередні
    # `id`, `created_at`, `updated_at` встановлюються автоматично.


# --- Схема для оновлення статусу аватара (наприклад, зміна is_current) ---
# Зазвичай, при встановленні нового аватара, створюється новий запис AvatarModel,
# а для попереднього `is_current` встановлюється в False.
# Пряме оновлення існуючого запису AvatarModel (окрім is_current) нетипове.
class AvatarUpdateSchema(BaseSchema):
    """
    Схема для оновлення статусу аватара (наприклад, зміна is_current).
    """
    is_current: bool = Field(..., description="Новий статус 'поточний'")


# AvatarSchema.model_rebuild() # Для ForwardRef

# TODO: Переконатися, що схеми відповідають моделі `AvatarModel`.
# `AvatarModel` успадковує від `BaseModel` і має `user_id, file_id, is_current`.
# `AvatarSchema` успадковує від `AuditDatesSchema` і відображає ці поля.
# Розгорнутий зв'язок `file` (з `FileSchema`) важливий, щоб отримати URL аватара.
# Зв'язок `user` закоментований, оскільки зазвичай аватар запитується в контексті користувача.
#
# `AvatarCreateSchema` містить `user_id` та `file_id`.
# `is_current` встановлюється сервісом (за замовчуванням `True` для нового аватара,
# при цьому сервіс має деактивувати попередній поточний аватар цього користувача).
#
# `AvatarUpdateSchema` дозволяє змінювати лише `is_current`.
#
# Все виглядає узгоджено.
# `AuditDatesSchema` надає `id, created_at, updated_at`.
# `created_at` - час встановлення аватара.
# `updated_at` - при зміні `is_current`.
#
# `FileSchema`, на яку посилається `AvatarSchema.file`, має містити поле `file_url`
# для прямого доступу до зображення.
# Це забезпечує відокремлення логіки аватарів від загальної логіки файлів.
#
# Все виглядає добре.
# Унікальне обмеження `UniqueConstraint('user_id', name='uq_user_current_avatar', postgresql_where=(is_current == True))`
# в моделі `AvatarModel` гарантує, що для кожного користувача може бути лише один активний аватар.
# Схеми це не відображають напряму, але логіка сервісу має це враховувати.
# `AvatarCreateSchema` не має `is_current`, бо сервіс це встановлює.
# `AvatarUpdateSchema` дозволяє змінити `is_current`, що може бути використано сервісом.
# Це виглядає коректно.

AvatarSchema.model_rebuild()
AvatarCreateSchema.model_rebuild()
AvatarUpdateSchema.model_rebuild()
