# backend/app/src/models/auth/user.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає модель SQLAlchemy `UserModel` для представлення користувачів системи.
Користувач є центральною сутністю для автентифікації, авторизації та взаємодії з системою.
Модель включає поля для ідентифікації, автентифікаційних даних, особистої інформації та зв'язків з іншими сутностями.
"""
from datetime import datetime # Додано імпорт datetime
from typing import List, TYPE_CHECKING, Optional

from sqlalchemy import String, Text, DateTime, Boolean, ForeignKey, Integer, Index  # type: ignore  # Removed LargeBinary as it's not used, Column
from sqlalchemy.dialects.postgresql import UUID # type: ignore
from sqlalchemy.orm import relationship, Mapped, mapped_column  # type: ignore # Додано mapped_column
import uuid # Для роботи з UUID

from backend.app.src.models.base import BaseMainModel # Успадковуємо від BaseMainModel для отримання name, description, state_id тощо.
# Хоча `name` для користувача може бути його повним ім'ям або нікнеймом.
# `description` може бути біографією.
# `state_id` може вказувати на статус користувача (активний, заблокований, непідтверджений).
# `group_id` тут нерелевантний, оскільки користувач глобальний, а його приналежність до груп визначається через GroupMembershipModel.

# TODO: Імпортувати Enum UserTypeEnum, коли він буде створений (в `backend/app/src/core/dicts.py` або схожому місці)
# from backend.app.src.core.dicts import UserTypeEnum (приклад)

if TYPE_CHECKING:
    from backend.app.src.models.auth.token import RefreshTokenModel
    from backend.app.src.models.auth.session import SessionModel
    from backend.app.src.models.files.avatar import AvatarModel
    from backend.app.src.models.groups.membership import GroupMembershipModel
    from backend.app.src.models.bonuses.account import AccountModel
    from backend.app.src.models.notifications.notification import NotificationModel
    from backend.app.src.models.tasks.task import TaskModel
    from backend.app.src.models.tasks.assignment import TaskAssignmentModel
    from backend.app.src.models.tasks.completion import TaskCompletionModel
    from backend.app.src.models.tasks.proposal import TaskProposalModel
    from backend.app.src.models.tasks.review import TaskReviewModel
    from backend.app.src.models.groups.poll_vote import PollVoteModel
    from backend.app.src.models.system.monitoring import SystemEventLogModel # Припускаючи, що це модель для логів
    from backend.app.src.models.groups.template import GroupTemplateModel
    from backend.app.src.models.groups.poll import PollModel
    from backend.app.src.models.teams.team import TeamModel
    from backend.app.src.models.teams.membership import TeamMembershipModel
    from backend.app.src.models.bonuses.bonus import BonusAdjustmentModel # Припускаючи, що це модель для BonusAdjustment
    from backend.app.src.models.reports.report import ReportModel
    from backend.app.src.models.gamification.user_level import UserLevelModel
    from backend.app.src.models.gamification.achievement import AchievementModel
    from backend.app.src.models.gamification.rating import RatingModel
    from backend.app.src.models.files.file import FileModel
    from backend.app.src.models.dictionaries.user_type import UserTypeModel
    from backend.app.src.models.bonuses.transaction import TransactionModel # Додано


class UserModel(BaseMainModel):
    """
    Модель для представлення користувачів системи.

    Атрибути:
        id (uuid.UUID): Унікальний ідентифікатор користувача (успадковано).
        name (str): Повне ім'я користувача або нікнейм (успадковано).
        description (str | None): Біографія або додаткова інформація про користувача (успадковано).
        state_id (uuid.UUID | None): Статус користувача (наприклад, "активний", "заблокований", "очікує підтвердження").
                                     Посилається на StatusModel. (успадковано)
        group_id (uuid.UUID | None): Це поле з BaseMainModel тут не використовується для основного профілю користувача
                                     і буде NULL. Приналежність до груп реалізується через GroupMembershipModel. (успадковано)

        email (str): Електронна пошта користувача, використовується для входу та комунікації. Має бути унікальною.
        phone_number (str | None): Номер телефону користувача. Може бути унікальним, якщо використовується для входу.
        hashed_password (str): Захешований пароль користувача.

        first_name (str | None): Ім'я користувача.
        last_name (str | None): Прізвище користувача.
        patronymic (str | None): По батькові користувача (якщо застосовно).

        birth_date (DateTime | None): Дата народження користувача.

        user_type (str): Тип користувача (наприклад, 'superadmin', 'admin', 'user', 'bot').
                         Зберігається як рядок, може посилатися на довідник або Enum.
                         Згідно ТЗ: (довідник чи enum) типи користувачів.
                         Якщо це enum, то тип поля може бути `EnumType(UserTypeEnum)`. Поки що `String`.

        is_email_verified (bool): Прапорець, чи підтверджена електронна пошта.
        is_phone_verified (bool): Прапорець, чи підтверджений номер телефону.

        last_login_at (DateTime | None): Час останнього входу користувача в систему.
        failed_login_attempts (int): Кількість невдалих спроб входу поспіль.
        locked_until (DateTime | None): Час, до якого акаунт заблокований через невдалі спроби входу.

        # Поля для двофакторної автентифікації (2FA)
        is_2fa_enabled (bool): Чи ввімкнена двофакторна автентифікація.
        otp_secret (str | None): Секретний ключ для генерації одноразових паролів (TOTP).
        otp_backup_codes_hashed (Text | None): Захешовані резервні коди для 2FA.

        created_at (datetime): Дата та час створення запису (успадковано).
        updated_at (datetime): Дата та час останнього оновлення запису (успадковано).
        deleted_at (datetime | None): Дата та час "м'якого" видалення (успадковано).
        is_deleted (bool): Прапорець "м'якого" видалення (успадковано).
        notes (str | None): Додаткові нотатки (успадковано).

    Зв'язки:
        Більшість необхідних зв'язків вже визначено нижче.
        Потрібно переконатися в коректності `back_populates` при роботі з відповідними моделями.
        # TODO: Розглянути необхідність зв'язку для `created_system_settings`, якщо `created_by_user_id`
        #       в `BaseModel` буде активно використовуватися для відстеження змін системних налаштувань.
        # TODO: (Функціонал майбутнього) Реалізувати налаштування приватності профілю та активності.
        #       Це може потребувати окремої моделі `UserPrivacySettingsModel` або додаткових полів тут.
    """
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    phone_number: Mapped[Optional[str]] = mapped_column(String(30), unique=True, index=True, nullable=True) # Може бути унікальним
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False) # Зберігає результат хешування

    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    patronymic: Mapped[Optional[str]] = mapped_column(String(100), nullable=True) # По батькові

    birth_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Тип користувача: 'superadmin', 'admin' (загальний адмін, якщо є), 'user', 'bot'.
    # 'group_admin' - це роль в контексті групи, а не тип користувача.
    # TODO: Узгодити з довідником UserRoleModel та можливим Enum UserType.
    # Тип користувача визначається через ForeignKey до таблиці user_types.
    user_type_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("user_types.id", name="fk_users_user_type_id"), nullable=True, index=True) # Зроблено nullable=True, щоб можна було створити юзера, а потім тип

    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_phone_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True) # Час, до якого акаунт заблокований

    # --- Поля для 2FA ---
    is_2fa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Секрет для TOTP, зазвичай шифрується перед збереженням або зберігається в захищеному сховищі.
    # Тут для простоти - рядок, але в реальній системі потребує уваги до безпеки.
    otp_secret_encrypted: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) # Зашифрований OTP секрет
    # Резервні коди, зазвичай надаються користувачу один раз. Зберігати їх хеші.
    otp_backup_codes_hashed: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # Список хешів резервних кодів

    # --- Зв'язки (Relationships) ---
    # Зв'язок з токенами оновлення
    refresh_tokens: Mapped[List["RefreshTokenModel"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    # Зв'язок з сесіями користувача
    sessions: Mapped[List["SessionModel"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    # Зв'язок з аватарами користувача (один користувач може мати багато записів AvatarModel для історії)
    avatars: Mapped[List["AvatarModel"]] = relationship(back_populates="user", cascade="all, delete-orphan", foreign_keys="[AvatarModel.user_id]")
    # Поточний аватар можна буде отримати через фільтр is_current=True або окремим полем/методом.

    # Зв'язок з членством у групах (таблиця GroupMembershipModel)
    group_memberships: Mapped[List["GroupMembershipModel"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    # Зв'язок з рахунками користувача (таблиця AccountModel)
    accounts: Mapped[List["AccountModel"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    # Зв'язок з отриманими сповіщеннями (таблиця NotificationModel)
    notifications_received: Mapped[List["NotificationModel"]] = relationship(
        back_populates="recipient", # Узгоджено з NotificationModel
        foreign_keys="[NotificationModel.recipient_user_id]",
        cascade="all, delete-orphan"
    )

    # Зв'язок з створеними завданнями/подіями
    created_tasks: Mapped[List["TaskModel"]] = relationship(
        back_populates="creator",
        foreign_keys="[TaskModel.created_by_user_id]",
        cascade="all, delete-orphan" # Або SET NULL, якщо завдання можуть існувати без автора
    )

    # Зв'язок з призначеннями завдань (де цей користувач є виконавцем)
    task_assignments: Mapped[List["TaskAssignmentModel"]] = relationship(
        back_populates="user", # Виконавець
        foreign_keys="[TaskAssignmentModel.user_id]",
        cascade="all, delete-orphan"
    )
    # Зв'язок з призначеннями завдань (де цей користувач є тим, хто призначив)
    made_task_assignments: Mapped[List["TaskAssignmentModel"]] = relationship(
        back_populates="assigner",
        foreign_keys="[TaskAssignmentModel.assigned_by_user_id]",
        cascade="all, delete-orphan" # Або SET NULL
    )

    # Зв'язок з виконаннями завдань
    task_completions: Mapped[List["TaskCompletionModel"]] = relationship(
        back_populates="user", # Виконавець
        foreign_keys="[TaskCompletionModel.user_id]",
        cascade="all, delete-orphan"
    )
    # Зв'язок з перевірками завдань (де цей користувач є тим, хто перевірив)
    reviewed_task_completions: Mapped[List["TaskCompletionModel"]] = relationship(
        back_populates="reviewer",
        foreign_keys="[TaskCompletionModel.reviewed_by_user_id]",
        cascade="all, delete-orphan" # Або SET NULL
    )

    # Зв'язок з пропозиціями завдань (де цей користувач є автором пропозиції)
    task_proposals_made: Mapped[List["TaskProposalModel"]] = relationship(
        back_populates="proposer",
        foreign_keys="[TaskProposalModel.proposed_by_user_id]",
        cascade="all, delete-orphan"
    )
    # Зв'язок з пропозиціями завдань (де цей користувач є тим, хто розглянув)
    task_proposals_reviewed: Mapped[List["TaskProposalModel"]] = relationship(
        back_populates="reviewer",
        foreign_keys="[TaskProposalModel.reviewed_by_user_id]",
        cascade="all, delete-orphan" # Або SET NULL
    )

    # Зв'язок з відгуками на завдання, залишеними цим користувачем
    task_reviews_left: Mapped[List["TaskReviewModel"]] = relationship(
        back_populates="user",
        foreign_keys="[TaskReviewModel.user_id]",
        cascade="all, delete-orphan"
    )

    # Зв'язок з голосами в опитуваннях
    poll_votes_made: Mapped[List["PollVoteModel"]] = relationship(
        back_populates="user",
        foreign_keys="[PollVoteModel.user_id]",
        cascade="all, delete-orphan" # Або SET NULL, якщо голоси анонімізуються при видаленні юзера
    )

    # Зв'язок з системними логами, пов'язаними з цим користувачем
    system_event_logs: Mapped[List["SystemEventLogModel"]] = relationship(
        back_populates="user", # Потрібно додати "user" в SystemEventLogModel
        foreign_keys="[SystemEventLogModel.user_id]"
        # ondelete='SET NULL' має бути на ForeignKey в SystemEventLogModel.user_id
        # cascade тут не потрібен для SET NULL
    )

    # Зв'язок з створеними шаблонами груп (якщо created_by_user_id в GroupTemplateModel)
    created_group_templates: Mapped[List["GroupTemplateModel"]] = relationship(
        back_populates="creator",
        foreign_keys="[GroupTemplateModel.created_by_user_id]"
        # ondelete='SET NULL' має бути на ForeignKey в GroupTemplateModel.created_by_user_id
    )

    # Зв'язок з створеними опитуваннями (якщо created_by_user_id в PollModel)
    created_polls: Mapped[List["PollModel"]] = relationship(
        back_populates="creator",
        foreign_keys="[PollModel.created_by_user_id]"
        # ondelete='SET NULL' або 'CASCADE' має бути на ForeignKey в PollModel.created_by_user_id
    )

    # Зв'язок з командами, де користувач є лідером
    led_teams: Mapped[List["TeamModel"]] = relationship(
        back_populates="leader",
        foreign_keys="[TeamModel.leader_user_id]"
        # ondelete='SET NULL' має бути на ForeignKey в TeamModel.leader_user_id
    )

    # Зв'язок з членством в командах
    team_memberships: Mapped[List["TeamMembershipModel"]] = relationship(
        back_populates="user",
        foreign_keys="[TeamMembershipModel.user_id]",
        cascade="all, delete-orphan"
    )

    # Зв'язок з ручними коригуваннями бонусів, зробленими цим адміном
    made_bonus_adjustments: Mapped[List["BonusAdjustmentModel"]] = relationship(
        back_populates="admin",
        foreign_keys="[BonusAdjustmentModel.adjusted_by_user_id]"
        # ondelete='SET NULL' має бути на ForeignKey в BonusAdjustmentModel.adjusted_by_user_id
    )

    # Зв'язок з запитами на звіти, зробленими цим користувачем
    requested_reports: Mapped[List["ReportModel"]] = relationship(
        back_populates="requester",
        foreign_keys="[ReportModel.requested_by_user_id]"
        # ondelete='SET NULL' має бути на ForeignKey в ReportModel.requested_by_user_id
    )

    # Зв'язок з досягненнями (отриманими бейджами та рівнями)
    achieved_user_levels: Mapped[List["UserLevelModel"]] = relationship(back_populates="user", foreign_keys="[UserLevelModel.user_id]", cascade="all, delete-orphan")
    achievements_earned: Mapped[List["AchievementModel"]] = relationship(back_populates="user", foreign_keys="[AchievementModel.user_id]", cascade="all, delete-orphan")
    # Зв'язок з досягненнями, які цей користувач (адмін) вручну присудив
    awarded_achievements_by_admin: Mapped[List["AchievementModel"]] = relationship(
        back_populates="awarder",
        foreign_keys="[AchievementModel.awarded_by_user_id]"
        # ondelete='SET NULL' має бути на ForeignKey в AchievementModel.awarded_by_user_id
    )

    # Зв'язок з рейтингами цього користувача
    ratings_history: Mapped[List["RatingModel"]] = relationship(back_populates="user", foreign_keys="[RatingModel.user_id]", cascade="all, delete-orphan")

    # Зв'язок з файлами, завантаженими цим користувачем
    uploaded_files: Mapped[List["FileModel"]] = relationship(
        back_populates="uploader",
        foreign_keys="[FileModel.uploaded_by_user_id]"
        # ondelete='SET NULL' має бути на ForeignKey в FileModel.uploaded_by_user_id
    )

    # Зв'язок зі статусом (успадковано з BaseMainModel)
    # state: Mapped[Optional["StatusModel"]] = relationship("StatusModel", foreign_keys="[UserModel.state_id]", back_populates="users_with_this_state")
    # Це вже визначено в BaseMainModel як:
    # state: Mapped[Optional["StatusModel"]] = relationship("StatusModel", foreign_keys=[state_id], lazy="selectin")
    # Потрібно в StatusModel додати `users_with_this_state: Mapped[List["UserModel"]] = relationship(back_populates="state")`

    # Зв'язок з типом користувача
    user_type: Mapped[Optional["UserTypeModel"]] = relationship("UserTypeModel", back_populates="users", foreign_keys=[user_type_id])

    # Зв'язок з транзакціями, де цей користувач є "пов'язаним" (наприклад, для подяки)
    related_transactions: Mapped[List["TransactionModel"]] = relationship(
        "TransactionModel", # Використовуємо рядкове посилання
        back_populates="related_user",
        foreign_keys="[TransactionModel.related_user_id]" # Вказуємо зовнішній ключ з TransactionModel
    )

    # Зв'язки created_by/updated_by з BaseModel
    # created_records: Mapped[List["SQLABaseModel"]] = relationship( # Потребує більш складної реалізації з primaryjoin
    #     foreign_keys="[SQLABaseModel.created_by_user_id]",
    #     backref="created_by_user"
    # )
    # updated_records: Mapped[List["SQLABaseModel"]] = relationship(
    #     foreign_keys="[SQLABaseModel.updated_by_user_id]",
    #     backref="updated_by_user"
    # )
    # Це складно реалізувати для базового класу, тому ці зворотні зв'язки зазвичай не визначаються.

    # Поле `group_id` з BaseMainModel для користувача завжди буде NULL.
    # Це поле не використовується для визначення приналежності до груп.

    # TODO: Додати інші зв'язки згідно з `technical-task.md` та `structure-claude-v3.md` (більшість вже є).
    # - SystemEventLogModel (логи, пов'язані з користувачем) - додано.

    __table_args__ = (
        # Додаткові індекси для полів, за якими може здійснюватися пошук або фільтрація
        Index('ix_users_first_name', 'first_name'),
        Index('ix_users_last_name', 'last_name'),
        # Index('ix_users_user_type_code', 'user_type_code'), # user_type_code вже має index=True
    )

    def __repr__(self) -> str:
        """
        Повертає рядкове представлення об'єкта моделі UserModel.
        """
        return f"<{self.__class__.__name__}(id='{self.id}', email='{self.email}', name='{self.name}')>"

# TODO: Перевірити відповідність `technical-task.md`:
# - "створення/редагування/видалення/блокування/підтвердження користувача" - керується через поля та стан.
# - "авторизація, реєстрація за поштою/телефоном" - поля email, phone_number, hashed_password.
# - "налаштування свого профіля - детальна інформація, фото, аватарка" - first_name, last_name, description, зв'язок з AvatarModel.
# - "налаштування свого профіля - сповіщення, повідомлення, інтеграції" - потребуватиме окремих таблиць налаштувань.
# - "користувачам (за бажанням) може робити частину свого профілю та активності видимою" - потребує полів налаштувань приватності.

# TODO: Подумати про індекси для полів, за якими часто буде пошук (наприклад, first_name, last_name, user_type_code).
# `email` та `phone_number` вже мають індекси та унікальність.

# TODO: Узгодити поле `name` з `BaseMainModel` та `first_name`, `last_name`.
# Можливо, `name` буде автоматично генеруватися як `first_name + ' ' + last_name` або буде нікнеймом.
# За ТЗ, користувач створюється адміном групи, тому адмін може заповнити ці поля.
# При самостійній реєстрації користувач також їх вказує.
# Поки що `name` - це окреме поле, яке може бути нікнеймом або повним ім'ям.
# Якщо `name` - це нікнейм, то він теж може бути `unique=True, nullable=False`.
# Якщо `name` - це ПІБ, то `nullable=False`.
# Залишаю `name` як `nullable=False` з `BaseMainModel`.
# Поля `first_name`, `last_name` можуть бути `nullable=True`.
# Або ж зробити `name` `nullable=True` і формувати його з `first_name` та `last_name`.
# Поки залишаю як є, `name` буде обов'язковим.
# Згідно code-style.md, BaseMainModel має name, description.

# TODO: Розглянути необхідність поля `username` (логін), якщо він відрізняється від email/phone.
# Поки що припускаємо, що вхід відбувається за email або телефоном.
# Якщо `name` використовується як нікнейм, то він може бути логіном.
# Але тоді він має бути унікальним. Поки що `name` не унікальний.
# Якщо `name` це ПІБ, то він точно не унікальний.
# Вирішено: `name` з `BaseMainModel` буде використовуватися як відображуване ім'я / нікнейм.
# Воно не обов'язково унікальне.
# `email` та `phone_number` - для входу та унікальної ідентифікації.
# `first_name`, `last_name` - для персоналізації.
# `user_type_code` - посилання на код типу користувача з відповідного довідника.
# Поле `state_id` з `BaseMainModel` використовується для статусу (активний, заблокований).
# Поле `group_id` з `BaseMainModel` для `UserModel` буде завжди `NULL`.
# Приналежність до груп визначається через `GroupMembershipModel`.
# `deleted_at` та `is_deleted` з `BaseMainModel` для м'якого видалення.
# `notes` з `BaseMainModel` для додаткових нотаток.
# `description` з `BaseMainModel` для біографії.
# Все виглядає узгоджено.
