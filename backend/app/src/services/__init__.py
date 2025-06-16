# backend/app/src/services/__init__.py
# backend/app/src/services/__init__.py
# Центральний файл для експорту сервісів.
# Дозволяє імпортувати сервіси через `from backend.app.src.services import SomeService`
# замість вказання повного шляху до модуля сервісу.

from backend.app.src.config.logging import get_logger # Змінено на get_logger
logger = get_logger(__name__) # Ініціалізація логера через get_logger

logger.info("Ініціалізація пакету сервісів...")

# --- Базовий сервіс ---
try:
    from .base import BaseService
    logger.debug("BaseService успішно імпортовано.")
except ImportError as e:
    logger.warning(f"Не вдалося імпортувати BaseService: {e}")
    BaseService = None # type: ignore

# --- Сервіси автентифікації та користувачів (auth) ---
try:
    from .auth.user import UserService
    from .auth.token import TokenService
    from .auth.password import PasswordService
    from .auth.session import UserSessionService
    logger.debug("Сервіси Auth (User, Token, Password, UserSession) успішно імпортовано.")
except ImportError as e:
    logger.warning(f"Не вдалося імпортувати один або більше сервісів Auth: {e}")
    UserService, TokenService, PasswordService, UserSessionService = None, None, None, None # type: ignore

# --- Сервіси довідників (dictionaries) ---
try:
    from .dictionaries.base_dict import BaseDictionaryService
    from .dictionaries.status import StatusService
    from .dictionaries.user_roles import UserRoleService
    from .dictionaries.user_types import UserTypeService
    from .dictionaries.group_types import GroupTypeService
    from .dictionaries.task_types import TaskTypeService
    from .dictionaries.bonus_types import BonusTypeService
    from .dictionaries.calendars import CalendarProviderService
    from .dictionaries.messengers import MessengerPlatformService
    logger.debug("Сервіси Dictionaries успішно імпортовано.")
except ImportError as e:
    logger.warning(f"Не вдалося імпортувати один або більше сервісів Dictionaries: {e}")
    BaseDictionaryService, StatusService, UserRoleService, UserTypeService = None, None, None, None # type: ignore
    GroupTypeService, TaskTypeService, BonusTypeService = None, None, None # type: ignore
    CalendarProviderService, MessengerPlatformService = None, None # type: ignore

# --- Сервіси груп (groups) ---
try:
    from .groups.group import GroupService
    from .groups.settings import GroupSettingService
    from .groups.membership import GroupMembershipService
    from .groups.invitation import GroupInvitationService
    logger.debug("Сервіси Groups успішно імпортовано.")
except ImportError as e:
    logger.warning(f"Не вдалося імпортувати один або більше сервісів Groups: {e}")
    GroupService, GroupSettingService, GroupMembershipService, GroupInvitationService = None, None, None, None # type: ignore

# --- Сервіси завдань та подій (tasks) ---
try:
    from .tasks.task import TaskService
    from .tasks.event import EventService
    from .tasks.assignment import TaskAssignmentService
    from .tasks.completion import TaskCompletionService
    from .tasks.review import TaskReviewService
    from .tasks.scheduler import TaskSchedulingService
    logger.debug("Сервіси Tasks успішно імпортовано.")
except ImportError as e:
    logger.warning(f"Не вдалося імпортувати один або більше сервісів Tasks: {e}")
    TaskService, EventService, TaskAssignmentService = None, None, None # type: ignore
    TaskCompletionService, TaskReviewService, TaskSchedulingService = None, None, None # type: ignore

# --- Сервіси бонусів (bonuses) ---
try:
    from .bonuses.bonus_rule import BonusRuleService
    from .bonuses.account import UserAccountService
    from .bonuses.transaction import AccountTransactionService
    from .bonuses.reward import RewardService
    from .bonuses.calculation import BonusCalculationService
    logger.debug("Сервіси Bonuses успішно імпортовано.")
except ImportError as e:
    logger.warning(f"Не вдалося імпортувати один або більше сервісів Bonuses: {e}")
    BonusRuleService, UserAccountService, AccountTransactionService = None, None, None # type: ignore
    RewardService, BonusCalculationService = None, None # type: ignore

# --- Сервіси гейміфікації (gamification) ---
try:
    from .gamification.level import LevelService
    from .gamification.user_level import UserLevelService
    from .gamification.badge import BadgeService
    from .gamification.achievement import UserAchievementService
    from .gamification.rating import UserRatingService
    logger.debug("Сервіси Gamification успішно імпортовано.")
except ImportError as e:
    logger.warning(f"Не вдалося імпортувати один або більше сервісів Gamification: {e}")
    LevelService, UserLevelService, BadgeService = None, None, None # type: ignore
    UserAchievementService, UserRatingService = None, None # type: ignore

# --- Сервіси сповіщень (notifications) ---
try:
    from .notifications.template import NotificationTemplateService
    from .notifications.notification import NotificationService
    from .notifications.delivery import NotificationDeliveryService
    from .notifications.delivery_channels import EmailNotificationService, SmsNotificationService, PushNotificationService # Channel senders
    logger.debug("Сервіси Notifications успішно імпортовано.")
except ImportError as e:
    logger.warning(f"Не вдалося імпортувати один або більше сервісів Notifications: {e}")
    NotificationTemplateService, NotificationService, NotificationDeliveryService = None, None, None # type: ignore
    EmailNotificationService, SmsNotificationService, PushNotificationService = None, None, None # type: ignore

# --- Сервіси інтеграцій (integrations) ---
try:
    from .integrations.calendar_base import BaseCalendarIntegrationService, CalendarEventData, CalendarInfo
    from .integrations.google_calendar_service import GoogleCalendarService
    from .integrations.outlook_calendar_service import OutlookCalendarService
    from .integrations.messenger_base import BaseMessengerIntegrationService, MessengerUserProfile, MessengerMessage, MessageSendCommand, MessageSendResponse
    from .integrations.telegram_service import TelegramIntegrationService
    from .integrations.viber_service import ViberIntegrationService
    from .integrations.slack_service import SlackIntegrationService
    from .integrations.teams_service import TeamsIntegrationService
    logger.debug("Сервіси Integrations успішно імпортовано.")
except ImportError as e:
    logger.warning(f"Не вдалося імпортувати один або більше сервісів Integrations: {e}")
    BaseCalendarIntegrationService, GoogleCalendarService, OutlookCalendarService = None, None, None # type: ignore
    BaseMessengerIntegrationService, TelegramIntegrationService, ViberIntegrationService = None, None, None # type: ignore
    SlackIntegrationService, TeamsIntegrationService = None, None # type: ignore
    CalendarEventData, CalendarInfo = None, None # type: ignore
    MessengerUserProfile, MessengerMessage, MessageSendCommand, MessageSendResponse = None, None, None, None # type: ignore


# --- Сервіси файлів (files) ---
try:
    from .files.file_record_service import FileRecordService
    from .files.file_upload_service import FileUploadService
    from .files.user_avatar_service import UserAvatarService
    logger.debug("Сервіси Files успішно імпортовано.")
except ImportError as e:
    logger.warning(f"Не вдалося імпортувати один або більше сервісів Files: {e}")
    FileRecordService, FileUploadService, UserAvatarService = None, None, None # type: ignore

# --- Сервіси кешу (cache) ---
try:
    from .cache.base_cache import BaseCacheService
    from .cache.redis_service import RedisCacheService
    from .cache.memory_service import InMemoryCacheService
    logger.debug("Сервіси Cache успішно імпортовано.")
except ImportError as e:
    logger.warning(f"Не вдалося імпортувати один або більше сервісів Cache: {e}")
    BaseCacheService, RedisCacheService, InMemoryCacheService = None, None, None # type: ignore

# --- Системні сервіси (system) ---
try:
    from .system.health import HealthCheckService
    from .system.initialization import InitialDataService
    # from .system.monitoring import SystemMonitoringService # monitoring.py не було знайдено
    from .system.settings import SystemSettingService # Сервіс системних налаштувань
    logger.debug("Сервіси System успішно імпортовано.")
except ImportError as e:
    logger.warning(f"Не вдалося імпортувати один або більше сервісів System: {e}")
    HealthCheckService, InitialDataService, SystemSettingService = None, None, None # type: ignore
    # SystemMonitoringService = None


# Формування __all__ для експорту
_exported_services = [
    "BaseService",
    # Auth
    "UserService", "TokenService", "PasswordService", "UserSessionService",
    # Dictionaries
    "BaseDictionaryService", "StatusService", "UserRoleService", "UserTypeService",
    "GroupTypeService", "TaskTypeService", "BonusTypeService",
    "CalendarProviderService", "MessengerPlatformService",
    # Groups
    "GroupService", "GroupSettingService", "GroupMembershipService", "GroupInvitationService",
    # Tasks
    "TaskService", "EventService", "TaskAssignmentService", "TaskCompletionService",
    "TaskReviewService", "TaskSchedulingService",
    # Bonuses
    "BonusRuleService", "UserAccountService", "AccountTransactionService", "RewardService",
    "BonusCalculationService",
    # Gamification
    "LevelService", "UserLevelService", "BadgeService", "UserAchievementService", "UserRatingService",
    # Notifications
    "NotificationTemplateService", "NotificationService", "NotificationDeliveryService",
    "EmailNotificationService", "SmsNotificationService", "PushNotificationService",
    # Integrations (Base classes and concrete services)
    "BaseCalendarIntegrationService", "GoogleCalendarService", "OutlookCalendarService",
    "CalendarEventData", "CalendarInfo", # Pydantic models for integrations
    "BaseMessengerIntegrationService", "TelegramIntegrationService", "ViberIntegrationService",
    "SlackIntegrationService", "TeamsIntegrationService",
    "MessengerUserProfile", "MessengerMessage", "MessageSendCommand", "MessageSendResponse", # Pydantic models
    # Files
    "FileRecordService", "FileUploadService", "UserAvatarService",
    # Cache
    "BaseCacheService", "RedisCacheService", "InMemoryCacheService",
    # System
    "HealthCheckService", "InitialDataService", "SystemSettingService", # "SystemMonitoringService",
]

__all__ = [name for name in _exported_services if globals().get(name) is not None]

logger.info(f"Пакет сервісів ініціалізовано. Експортовано: {__all__}")
