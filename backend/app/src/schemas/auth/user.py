# backend/app/src/schemas/auth/user.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає Pydantic схеми для моделі `UserModel`.
Схеми використовуються для валідації даних при створенні, оновленні,
відображенні користувачів, а також для даних профілю.
"""

from pydantic import Field, EmailStr, field_validator, model_validator
from typing import Optional, List, Any
import uuid
from datetime import datetime

from backend.app.src.schemas.base import BaseMainSchema, BaseSchema, AuditDatesSchema
# Потрібно буде імпортувати схеми для зв'язків, коли вони будуть готові, наприклад:
# from backend.app.src.schemas.groups.membership import GroupMembershipSchema
# from backend.app.src.schemas.bonuses.account import AccountSchema
from backend.app.src.schemas.files.avatar import AvatarSchema
from backend.app.src.schemas.dictionaries.status import StatusSchema
from backend.app.src.schemas.groups.membership import GroupMembershipSchema
from backend.app.src.schemas.bonuses.account import AccountSchema
from backend.app.src.schemas.tasks.task import TaskSimpleSchema # Для created_tasks
from backend.app.src.schemas.gamification.achievement import AchievementSchema # Для achievements_earned
from backend.app.src.schemas.gamification.user_level import UserLevelSchema # Для achieved_user_levels


# --- Схема для відображення повної інформації про користувача (для адмінів або власного профілю) ---
class UserSchema(BaseMainSchema):
    """
    Повна схема для представлення користувача.
    Успадковує `id, name, description, state_id, group_id (тут NULL), created_at, updated_at, deleted_at, is_deleted, notes`
    від `BaseMainSchema`.
    """
    email: EmailStr = Field(..., description="Електронна пошта користувача")
    phone_number: Optional[str] = Field(None, description="Номер телефону користувача")

    first_name: Optional[str] = Field(None, max_length=100, description="Ім'я користувача")
    last_name: Optional[str] = Field(None, max_length=100, description="Прізвище користувача")
    patronymic: Optional[str] = Field(None, max_length=100, description="По батькові користувача")

    birth_date: Optional[datetime] = Field(None, description="Дата народження користувача")

    user_type_code: str = Field(..., description="Код типу користувача (наприклад, 'superadmin', 'user', 'bot')")
    # TODO: Додати поле `user_type: Optional[UserTypeSchema]` для розгорнутого об'єкта типу користувача,
    # коли буде створена схема для довідника типів користувачів (якщо такий довідник буде).

    is_email_verified: bool = Field(..., description="Прапорець, чи підтверджена електронна пошта")
    is_phone_verified: bool = Field(..., description="Прапорець, чи підтверджений номер телефону")

    last_login_at: Optional[datetime] = Field(None, description="Час останнього входу користувача в систему")
    failed_login_attempts: int = Field(..., ge=0, description="Кількість невдалих спроб входу поспіль")
    locked_until: Optional[datetime] = Field(None, description="Час, до якого акаунт заблокований")

    is_2fa_enabled: bool = Field(..., description="Чи ввімкнена двофакторна автентифікація")
    # otp_secret_encrypted та otp_backup_codes_hashed не повинні віддаватися через API.

    # --- Розгорнуті зв'язки ---
    state: Optional[StatusSchema] = Field(None, description="Статус користувача (розгорнутий)")
    # Для аватара: UserModel має зв'язок `avatars: Mapped[List["AvatarModel"]]`.
    # Потрібно вибрати поточний аватар. Це краще робити на сервісному рівні
    # і додавати поле `current_avatar: Optional[AvatarSchema]` або `avatar_url: Optional[HttpUrl]`.
    # Поки що додаю список всіх аватарів (історія), або можна зробити поле для поточного.
    current_avatar: Optional[AvatarSchema] = Field(None, description="Поточний аватар користувача")
    # avatars_history: List[AvatarSchema] = Field(default_factory=list, description="Історія аватарів користувача")


    group_memberships: List[GroupMembershipSchema] = Field(default_factory=list, description="Членство користувача в групах")
    accounts: List[AccountSchema] = Field(default_factory=list, description="Рахунки користувача в групах")

    # Приклади інших зв'язків (можуть бути не всі потрібні для кожної відповіді)
    # created_tasks: List[TaskSimpleSchema] = Field(default_factory=list, description="Завдання, створені користувачем")
    # achievements_earned: List[AchievementSchema] = Field(default_factory=list, description="Отримані бейджі/досягнення")
    # achieved_user_levels: List[UserLevelSchema] = Field(default_factory=list, description="Досягнуті рівні")

    # `group_id` з `BaseMainSchema` для `UserModel` завжди буде `None`.
    # Це поле не використовується для визначення приналежності до груп.
    # Приналежність до груп визначається через `group_memberships`.

# --- Схема для відображення публічної інформації про користувача ---
class UserPublicSchema(IdentifiedSchema): # Тільки id + публічні поля
    """
    Схема для публічного представлення користувача (обмежений набір полів).
    """
    name: str = Field(..., description="Відображуване ім'я або нікнейм користувача")
    # email: Optional[EmailStr] = Field(None, description="Електронна пошта (якщо дозволено показувати)")
    # first_name: Optional[str] = Field(None)
    # last_name: Optional[str] = Field(None)
    # avatar_url: Optional[str] = Field(None, description="URL аватара користувача")
    # user_type_code: str = Field(..., description="Код типу користувача") # Можливо, не потрібне публічно

    # `name` з `BaseMainModel` (успадковано через `BaseSchema` -> `IdentifiedSchema` -> `BaseMainSchema`) використовується як основне відображуване ім'я.
    first_name: Optional[str] = Field(None, description="Ім'я користувача (публічне, якщо заповнене та дозволено налаштуваннями приватності)")
    last_name: Optional[str] = Field(None, description="Прізвище користувача (публічне, якщо заповнене та дозволено налаштуваннями приватності)")
    description: Optional[str] = Field(None, description="Опис/біографія користувача (публічне, якщо заповнене та дозволено)")
    current_avatar_url: Optional[str] = Field(None, description="URL поточного аватара користувача (публічний, якщо є та дозволено)")
    # TODO: Сервісний шар повинен заповнювати ці поля з урахуванням налаштувань приватності.

# --- Схема для створення нового користувача (наприклад, адміном або при реєстрації) ---
class UserCreateSchema(BaseSchema):
    """
    Схема для створення нового користувача.
    """
    email: EmailStr = Field(..., description="Електронна пошта користувача")
    password: str = Field(..., min_length=8, description="Пароль користувача (буде захешовано)")

    name: str = Field(..., min_length=1, max_length=255, description="Відображуване ім'я або нікнейм")
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    patronymic: Optional[str] = Field(None, max_length=100)

    phone_number: Optional[str] = Field(None, description="Номер телефону")

    user_type_code: str = Field(default="user", description="Код типу користувача (за замовчуванням 'user')")
    # state_id: Optional[uuid.UUID] = Field(None, description="Початковий статус користувача (якщо встановлюється при створенні)")
    # Зазвичай, при створенні користувач може бути "неактивний" або "очікує підтвердження пошти".
    # Це керується логікою сервісу.

    confirm_password: str = Field(..., description="Підтвердження пароля")

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        from backend.app.src.core.validators import is_strong_password
        is_strong_password(value) # Валідатор кине ValueError, якщо пароль не надійний
        return value

    @field_validator('phone_number')
    @classmethod
    def validate_phone_number_format(cls, value: Optional[str]) -> Optional[str]:
        from backend.app.src.core.validators import is_valid_phone_number
        is_valid_phone_number(value) # Валідатор кине ValueError, якщо номер не валідний
        return value

    @model_validator(mode='after')
    def check_passwords_match(cls, data: 'UserCreateSchema') -> 'UserCreateSchema':
        if data.password != data.confirm_password:
            raise ValueError("Паролі не співпадають.")
        return data

# --- Схема для оновлення інформації про користувача (власний профіль) ---
class UserUpdateSchema(BaseSchema):
    """
    Схема для оновлення інформації користувача (наприклад, власний профіль).
    """
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    patronymic: Optional[str] = Field(None, max_length=100)

    phone_number: Optional[str] = Field(None)
    birth_date: Optional[datetime] = Field(None)
    description: Optional[str] = Field(None) # Біографія
    notes: Optional[str] = Field(None) # Нотатки (якщо користувач може їх редагувати)

    @field_validator('phone_number')
    @classmethod
    def validate_phone_number_format(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            cleaned_phone = value.lstrip('+')
            if not cleaned_phone.isdigit():
                raise ValueError("Номер телефону повинен містити лише цифри та опціональний '+' на початку.")
            if not (7 <= len(cleaned_phone) <= 15):
                raise ValueError("Некоректна довжина номера телефону.")
        return value

    # email: Optional[EmailStr] = Field(None, description="Нова електронна пошта (потребуватиме підтвердження)")
    # Зміна email - це окремий процес, зазвичай.

    # Поля, які користувач може змінювати в своєму профілі.
    # Пароль, 2FA, email змінюються через окремі ендпоінти.

# --- Схема для оновлення пароля ---
class UserPasswordUpdateSchema(BaseSchema):
    current_password: str = Field(..., description="Поточний пароль")
    new_password: str = Field(..., min_length=8, description="Новий пароль")
    confirm_new_password: str = Field(..., description="Підтвердження нового пароля")

    @model_validator(mode='after')
    def check_passwords_match_and_strength(cls, data: 'UserPasswordUpdateSchema') -> 'UserPasswordUpdateSchema':
        if data.new_password != data.confirm_new_password:
            raise ValueError("Новий пароль та його підтвердження не співпадають.")

        from backend.app.src.core.validators import is_strong_password
        is_strong_password(data.new_password) # Валідація надійності нового пароля

        if data.new_password == data.current_password:
            raise ValueError("Новий пароль не може бути таким же, як поточний.")
        return data

# --- Схема для адміністративного оновлення користувача ---
class UserAdminUpdateSchema(UserUpdateSchema):
    """
    Схема для оновлення користувача адміністратором. Може включати зміну полів,
    недоступних для редагування самому користувачеві.
    """
    email: Optional[EmailStr] = Field(None)
    user_type_code: Optional[str] = Field(None)
    state_id: Optional[uuid.UUID] = Field(None) # Зміна статусу (активний, заблокований)
    is_email_verified: Optional[bool] = Field(None)
    is_phone_verified: Optional[bool] = Field(None)
    is_2fa_enabled: Optional[bool] = Field(None) # Адмін може скинути/ввімкнути 2FA
    locked_until: Optional[datetime] = Field(None) # Адмін може розблокувати
    failed_login_attempts: Optional[int] = Field(None, ge=0) # Адмін може скинути лічильник
    is_deleted: Optional[bool] = Field(None) # "М'яке" видалення/відновлення

    # Адмін не повинен змінювати пароль користувача напряму через цю схему.
    # Для скидання пароля має бути окремий механізм.


# TODO: Переконатися, що схеми відповідають моделі `UserModel`.
# `UserModel` успадковує від `BaseMainModel`.
# `UserSchema` успадковує від `BaseMainSchema` і додає специфічні поля користувача.
# Поля, які не повинні віддаватися через API (hashed_password, otp_secret_encrypted, otp_backup_codes_hashed),
# відсутні в `UserSchema`.
# `UserPublicSchema` для обмеженого представлення.
# `UserCreateSchema` для реєстрації/створення.
# `UserUpdateSchema` для оновлення профілю користувачем.
# `UserPasswordUpdateSchema` для зміни пароля.
# `UserAdminUpdateSchema` для адміністрування користувачів.
#
# Зв'язки (state, avatar_url, group_memberships, accounts) потребуватимуть відповідних схем
# та їх імпорту (з використанням `model_rebuild()` або `ForwardRef` для уникнення циклічних залежностей,
# якщо вони визначаються в цьому ж файлі або імпортуються до того, як ці схеми будуть повністю визначені).
# Наприклад, для `state: Optional[StatusSchema] = None;`
# потрібно буде додати `StatusSchema.model_rebuild()` або `UserSchema.model_rebuild()`
# після визначення всіх схем. Pydantic v2 автоматично обробляє ForwardRefs краще.
# Поки що залишаю їх закоментованими або з `Any`.
#
# Валідатори для `password` та `key` (в `SystemSettingCreateSchema`) є прикладами.
# Валідація формату `phone_number` також може бути додана.
# `user_type_code` - посилання на код типу користувача.
# `group_id` з `BaseMainSchema` для `UserSchema` завжди буде `None`, що коректно.
# Все виглядає узгоджено.
# Схема `UserSchema` (для відповіді) не містить `hashed_password` та секретів 2FA, що правильно.
# `UserCreateSchema` приймає `password`, який потім хешується сервісом.
# `UserPasswordUpdateSchema` також приймає паролі у відкритому вигляді для обробки сервісом.
# Це стандартні підходи.
# `EmailStr` забезпечує валідацію формату email.
# `ge=0` для `failed_login_attempts`.
# `min_length` для пароля.
# Все виглядає добре.

UserSchema.model_rebuild()
UserPublicSchema.model_rebuild()
UserCreateSchema.model_rebuild()
UserUpdateSchema.model_rebuild()
UserPasswordUpdateSchema.model_rebuild()
UserAdminUpdateSchema.model_rebuild()
