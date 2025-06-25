# backend/app/src/models/__init__.py
# -*- coding: utf-8 -*-
"""
Головний ініціалізаційний файл для пакету моделей (`models`).

Цей файл агрегує та експортує основні моделі даних SQLAlchemy з усіх підпакетів
(auth, bonuses, core, dictionaries, files, gamification, groups, notifications, reports, system, tasks, teams).
Це дозволяє імпортувати моделі з одного централізованого місця, наприклад:

from backend.app.src.models import UserModel, GroupModel, TaskModel, Base

Також цей файл експортує `Base` з `backend.app.src.models.base`, який є
декларативною базою для всіх моделей SQLAlchemy і необхідний для Alembic.
"""

# Імпорт базового класу для моделей SQLAlchemy
from backend.app.src.models.base import Base, BaseModel, BaseMainModel

# Імпорт моделей з підпакетів
from backend.app.src.models.auth import (
    UserModel,
    RefreshTokenModel,
    SessionModel,
)
from backend.app.src.models.bonuses import (
    AccountModel,
    TransactionModel,
    RewardModel,
    BonusAdjustmentModel,
)
from backend.app.src.models.dictionaries import (
    BaseDictModel,
    StatusModel,
    UserRoleModel,
    GroupTypeModel,
    TaskTypeModel,
    BonusTypeModel,
    IntegrationModel,
)
from backend.app.src.models.files import (
    FileModel,
    AvatarModel,
)
from backend.app.src.models.gamification import (
    LevelModel,
    UserLevelModel,
    BadgeModel,
    AchievementModel,
    RatingModel,
)
from backend.app.src.models.groups import (
    GroupModel,
    GroupSettingsModel,
    GroupMembershipModel,
    GroupInvitationModel,
    GroupTemplateModel,
    PollModel,
    PollOptionModel,
    PollVoteModel,
)
from backend.app.src.models.notifications import (
    NotificationModel,
    NotificationTemplateModel,
    NotificationDeliveryModel,
)
from backend.app.src.models.reports import (
    ReportModel,
)
from backend.app.src.models.system import (
    SystemSettingModel,
    CronTaskModel,
    SystemEventLogModel,
    ServiceHealthStatusModel,
)
from backend.app.src.models.tasks import (
    TaskModel,
    TaskAssignmentModel,
    TaskCompletionModel,
    TaskDependencyModel,
    TaskProposalModel,
    TaskReviewModel,
)
from backend.app.src.models.teams import (
    TeamModel,
    TeamMembershipModel,
)

# Визначення змінної `__all__` для контролю публічного API пакету `models`.
# Це список всіх моделей, які будуть доступні при `from backend.app.src.models import *`.
# Рекомендується включати сюди всі основні моделі для зручності.
__all__ = [
    # Base models
    "Base",
    "BaseModel",
    "BaseMainModel",

    # Auth models
    "UserModel",
    "RefreshTokenModel",
    "SessionModel",

    # Bonuses models
    "AccountModel",
    "TransactionModel",
    "RewardModel",
    "BonusAdjustmentModel",

    # Dictionaries models
    "BaseDictModel",
    "StatusModel",
    "UserRoleModel",
    "GroupTypeModel",
    "TaskTypeModel",
    "BonusTypeModel",
    "IntegrationModel",

    # Files models
    "FileModel",
    "AvatarModel",

    # Gamification models
    "LevelModel",
    "UserLevelModel",
    "BadgeModel",
    "AchievementModel",
    "RatingModel",

    # Groups models
    "GroupModel",
    "GroupSettingsModel",
    "GroupMembershipModel",
    "GroupInvitationModel",
    "GroupTemplateModel",
    "PollModel",
    "PollOptionModel",
    "PollVoteModel",

    # Notifications models
    "NotificationModel",
    "NotificationTemplateModel",
    "NotificationDeliveryModel",

    # Reports models
    "ReportModel",

    # System models
    "SystemSettingModel",
    "CronTaskModel",
    "SystemEventLogModel",
    "ServiceHealthStatusModel",

    # Tasks models
    "TaskModel",
    "TaskAssignmentModel",
    "TaskCompletionModel",
    "TaskDependencyModel",
    "TaskProposalModel",
    "TaskReviewModel",

    # Teams models
    "TeamModel",
    "TeamMembershipModel",
]

# Цей файл є важливим для Alembic, оскільки він може використовуватися в `env.py`
# для імпорту `Base` та забезпечення того, що всі моделі зареєстровані
# в `Base.metadata` перед генерацією міграцій.
# Наприклад, в `env.py`:
# from backend.app.src.models import Base
# target_metadata = Base.metadata
#
# Також, імпорт всіх моделей тут гарантує, що SQLAlchemy знає про всі таблиці
# та їх зв'язки під час ініціалізації додатку.
# Це допомагає уникнути помилок, пов'язаних з тим, що SQLAlchemy не може знайти
# таблицю, на яку посилається ForeignKey або relationship, якщо відповідна модель
# не була імпортована.
# Однак, SQLAlchemy зазвичай вирішує це, якщо всі моделі успадковуються від одного `Base`.
# Головна мета цього файлу - зручність імпорту та чітке визначення публічного API пакету моделей.
