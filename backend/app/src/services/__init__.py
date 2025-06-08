# backend/app/src/services/__init__.py
import logging

# Initialize logger for this module
logger = logging.getLogger(__name__)

logger.info("Services package initialized.")

# Import BaseService
try:
    from .base import BaseService
    logger.info("Successfully imported BaseService from .base")
except ImportError:
    logger.warning("BaseService could not be imported from .base. It might not be defined yet.")
    BaseService = None

# --- System Services ---
# Define expected system services and attempt to import them.
# This makes it clear what services are part of this domain.
HEALTH_CHECK_SERVICE = "HealthCheckService"
INITIAL_DATA_SERVICE = "InitialDataService"
SYSTEM_MONITORING_SERVICE = "SystemMonitoringService"
SYSTEM_SETTING_SERVICE = "SystemSettingService"

_system_service_names = [
    HEALTH_CHECK_SERVICE, INITIAL_DATA_SERVICE,
    SYSTEM_MONITORING_SERVICE, SYSTEM_SETTING_SERVICE
]
_imported_system_services = {}

try:
    from .system import (
        HealthCheckService, InitialDataService,
        SystemMonitoringService, SystemSettingService
    )
    _imported_system_services[HEALTH_CHECK_SERVICE] = HealthCheckService
    _imported_system_services[INITIAL_DATA_SERVICE] = InitialDataService
    _imported_system_services[SYSTEM_MONITORING_SERVICE] = SystemMonitoringService
    _imported_system_services[SYSTEM_SETTING_SERVICE] = SystemSettingService
    logger.info("Successfully imported all specified system services.")
except ImportError as e:
    logger.warning(f"Could not import one or more system services from .system: {e}. Attempting individual imports.")
    # Fallback to individual imports if collective import fails (e.g., one service is broken)
    for service_name_const in _system_service_names:
        try:
            module = __import__("app.src.services.system", globals(), locals(), [service_name_const], 0)
            _imported_system_services[service_name_const] = getattr(module, service_name_const)
            logger.info(f"Successfully imported {service_name_const} individually.")
        except (ImportError, AttributeError) as ie:
            logger.warning(f"Could not import {service_name_const} from .system: {ie}")
            _imported_system_services[service_name_const] = None


# --- Dictionary Services ---
# Define expected dictionary services.
BASE_DICT_SERVICE = "BaseDictionaryService"
STATUS_SERVICE = "StatusService"
USER_ROLE_SERVICE = "UserRoleService"
USER_TYPE_SERVICE = "UserTypeService"
GROUP_TYPE_SERVICE = "GroupTypeService"
TASK_TYPE_SERVICE = "TaskTypeService"
BONUS_TYPE_SERVICE = "BonusTypeService"
CALENDAR_PROVIDER_SERVICE = "CalendarProviderService"
MESSENGER_PLATFORM_SERVICE = "MessengerPlatformService"

_dictionary_service_names = [
    BASE_DICT_SERVICE, STATUS_SERVICE, USER_ROLE_SERVICE, USER_TYPE_SERVICE,
    GROUP_TYPE_SERVICE, TASK_TYPE_SERVICE, BONUS_TYPE_SERVICE,
    CALENDAR_PROVIDER_SERVICE, MESSENGER_PLATFORM_SERVICE
]
_imported_dictionary_services = {}

try:
    from .dictionaries import (
        BaseDictionaryService, StatusService, UserRoleService, UserTypeService,
        GroupTypeService, TaskTypeService, BonusTypeService,
        CalendarProviderService, MessengerPlatformService
    )
    _imported_dictionary_services[BASE_DICT_SERVICE] = BaseDictionaryService
    _imported_dictionary_services[STATUS_SERVICE] = StatusService
    _imported_dictionary_services[USER_ROLE_SERVICE] = UserRoleService
    _imported_dictionary_services[USER_TYPE_SERVICE] = UserTypeService
    _imported_dictionary_services[GROUP_TYPE_SERVICE] = GroupTypeService
    _imported_dictionary_services[TASK_TYPE_SERVICE] = TaskTypeService
    _imported_dictionary_services[BONUS_TYPE_SERVICE] = BonusTypeService
    _imported_dictionary_services[CALENDAR_PROVIDER_SERVICE] = CalendarProviderService
    _imported_dictionary_services[MESSENGER_PLATFORM_SERVICE] = MessengerPlatformService
    logger.info("Successfully imported all specified dictionary services.")
except ImportError as e:
    logger.warning(f"Could not import one or more dictionary services from .dictionaries: {e}. Attempting individual imports.")
    for service_name_const in _dictionary_service_names:
        try:
            module = __import__("app.src.services.dictionaries", globals(), locals(), [service_name_const], 0)
            _imported_dictionary_services[service_name_const] = getattr(module, service_name_const)
            logger.info(f"Successfully imported {service_name_const} individually.")
        except (ImportError, AttributeError) as ie:
            logger.warning(f"Could not import {service_name_const} from .dictionaries: {ie}")
            _imported_dictionary_services[service_name_const] = None


# Update globals() with successfully imported services to make them available for export
# and direct import from this package.
if BaseService: globals()["BaseService"] = BaseService

for name, service in _imported_system_services.items():
    if service: globals()[name] = service
    else: globals()[name] = None # Ensure name exists as None if not imported

for name, service in _imported_dictionary_services.items():
    if service: globals()[name] = service
    else: globals()[name] = None # Ensure name exists as None if not imported


# --- Auth Services ---
USER_SERVICE = "UserService"
TOKEN_SERVICE = "TokenService"
PASSWORD_SERVICE = "PasswordService"
USER_SESSION_SERVICE = "UserSessionService"

_auth_service_names = [
    USER_SERVICE, TOKEN_SERVICE, PASSWORD_SERVICE, USER_SESSION_SERVICE
]
_imported_auth_services = {}

try:
    from .auth import (
        UserService, TokenService, PasswordService, UserSessionService
    )
    _imported_auth_services[USER_SERVICE] = UserService
    _imported_auth_services[TOKEN_SERVICE] = TokenService
    _imported_auth_services[PASSWORD_SERVICE] = PasswordService
    _imported_auth_services[USER_SESSION_SERVICE] = UserSessionService
    logger.info("Successfully imported all specified authentication services.")
except ImportError as e:
    logger.warning(f"Could not import one or more authentication services from .auth: {e}. Attempting individual imports.")
    for service_name_const in _auth_service_names:
        try:
            module = __import__("app.src.services.auth", globals(), locals(), [service_name_const], 0)
            _imported_auth_services[service_name_const] = getattr(module, service_name_const)
            logger.info(f"Successfully imported {service_name_const} individually.")
        except (ImportError, AttributeError) as ie:
            logger.warning(f"Could not import {service_name_const} from .auth: {ie}")
            _imported_auth_services[service_name_const] = None

for name, service in _imported_auth_services.items():
    if service: globals()[name] = service
    else: globals()[name] = None # Ensure name exists as None if not imported


# --- Group Services ---
GROUP_SERVICE = "GroupService"
GROUP_SETTING_SERVICE = "GroupSettingService"
GROUP_MEMBERSHIP_SERVICE = "GroupMembershipService"
GROUP_INVITATION_SERVICE = "GroupInvitationService"

_group_service_names = [
    GROUP_SERVICE, GROUP_SETTING_SERVICE,
    GROUP_MEMBERSHIP_SERVICE, GROUP_INVITATION_SERVICE
]
_imported_group_services = {}

try:
    from .groups import (
        GroupService, GroupSettingService,
        GroupMembershipService, GroupInvitationService
    )
    _imported_group_services[GROUP_SERVICE] = GroupService
    _imported_group_services[GROUP_SETTING_SERVICE] = GroupSettingService
    _imported_group_services[GROUP_MEMBERSHIP_SERVICE] = GroupMembershipService
    _imported_group_services[GROUP_INVITATION_SERVICE] = GroupInvitationService
    logger.info("Successfully imported all specified group services.")
except ImportError as e:
    logger.warning(f"Could not import one or more group services from .groups: {e}. Attempting individual imports.")
    for service_name_const in _group_service_names:
        try:
            module = __import__("app.src.services.groups", globals(), locals(), [service_name_const], 0)
            _imported_group_services[service_name_const] = getattr(module, service_name_const)
            logger.info(f"Successfully imported {service_name_const} individually.")
        except (ImportError, AttributeError) as ie:
            logger.warning(f"Could not import {service_name_const} from .groups: {ie}")
            _imported_group_services[service_name_const] = None

for name, service in _imported_group_services.items():
    if service: globals()[name] = service
    else: globals()[name] = None # Ensure name exists as None if not imported


# --- Task and Event Services ---
TASK_SERVICE = "TaskService"
EVENT_SERVICE = "EventService"
TASK_ASSIGNMENT_SERVICE = "TaskAssignmentService"
TASK_COMPLETION_SERVICE = "TaskCompletionService"
TASK_REVIEW_SERVICE = "TaskReviewService"
TASK_SCHEDULING_SERVICE = "TaskSchedulingService"

_task_event_service_names = [
    TASK_SERVICE, EVENT_SERVICE, TASK_ASSIGNMENT_SERVICE,
    TASK_COMPLETION_SERVICE, TASK_REVIEW_SERVICE, TASK_SCHEDULING_SERVICE
]
_imported_task_event_services = {}

try:
    from .tasks import (
        TaskService, EventService, TaskAssignmentService,
        TaskCompletionService, TaskReviewService, TaskSchedulingService
    )
    _imported_task_event_services[TASK_SERVICE] = TaskService
    _imported_task_event_services[EVENT_SERVICE] = EventService
    _imported_task_event_services[TASK_ASSIGNMENT_SERVICE] = TaskAssignmentService
    _imported_task_event_services[TASK_COMPLETION_SERVICE] = TaskCompletionService
    _imported_task_event_services[TASK_REVIEW_SERVICE] = TaskReviewService
    _imported_task_event_services[TASK_SCHEDULING_SERVICE] = TaskSchedulingService
    logger.info("Successfully imported all specified task and event services.")
except ImportError as e:
    logger.warning(f"Could not import one or more task/event services from .tasks: {e}. Attempting individual imports.")
    for service_name_const in _task_event_service_names:
        try:
            module = __import__("app.src.services.tasks", globals(), locals(), [service_name_const], 0)
            _imported_task_event_services[service_name_const] = getattr(module, service_name_const)
            logger.info(f"Successfully imported {service_name_const} individually.")
        except (ImportError, AttributeError) as ie:
            logger.warning(f"Could not import {service_name_const} from .tasks: {ie}")
            _imported_task_event_services[service_name_const] = None

for name, service in _imported_task_event_services.items():
    if service: globals()[name] = service
    else: globals()[name] = None # Ensure name exists as None if not imported


# --- Bonus Services ---
BONUS_RULE_SERVICE = "BonusRuleService"
USER_ACCOUNT_SERVICE = "UserAccountService"
ACCOUNT_TRANSACTION_SERVICE = "AccountTransactionService"
REWARD_SERVICE = "RewardService"
BONUS_CALCULATION_SERVICE = "BonusCalculationService"

_bonus_service_names = [
    BONUS_RULE_SERVICE, USER_ACCOUNT_SERVICE, ACCOUNT_TRANSACTION_SERVICE,
    REWARD_SERVICE, BONUS_CALCULATION_SERVICE
]
_imported_bonus_services = {}

try:
    from .bonuses import (
        BonusRuleService, UserAccountService, AccountTransactionService,
        RewardService, BonusCalculationService
    )
    _imported_bonus_services[BONUS_RULE_SERVICE] = BonusRuleService
    _imported_bonus_services[USER_ACCOUNT_SERVICE] = UserAccountService
    _imported_bonus_services[ACCOUNT_TRANSACTION_SERVICE] = AccountTransactionService
    _imported_bonus_services[REWARD_SERVICE] = RewardService
    _imported_bonus_services[BONUS_CALCULATION_SERVICE] = BonusCalculationService
    logger.info("Successfully imported all specified bonus services.")
except ImportError as e:
    logger.warning(f"Could not import one or more bonus services from .bonuses: {e}. Attempting individual imports.")
    for service_name_const in _bonus_service_names:
        try:
            module = __import__("app.src.services.bonuses", globals(), locals(), [service_name_const], 0)
            _imported_bonus_services[service_name_const] = getattr(module, service_name_const)
            logger.info(f"Successfully imported {service_name_const} individually.")
        except (ImportError, AttributeError) as ie:
            logger.warning(f"Could not import {service_name_const} from .bonuses: {ie}")
            _imported_bonus_services[service_name_const] = None

for name, service in _imported_bonus_services.items():
    if service: globals()[name] = service
    else: globals()[name] = None # Ensure name exists as None if not imported


# --- Gamification Services ---
LEVEL_SERVICE = "LevelService"
USER_LEVEL_SERVICE = "UserLevelService"
BADGE_SERVICE = "BadgeService"
USER_ACHIEVEMENT_SERVICE = "UserAchievementService"
USER_RATING_SERVICE = "UserRatingService"

_gamification_service_names = [
    LEVEL_SERVICE, USER_LEVEL_SERVICE, BADGE_SERVICE,
    USER_ACHIEVEMENT_SERVICE, USER_RATING_SERVICE
]
_imported_gamification_services = {}

try:
    from .gamification import (
        LevelService, UserLevelService, BadgeService,
        UserAchievementService, UserRatingService
    )
    _imported_gamification_services[LEVEL_SERVICE] = LevelService
    _imported_gamification_services[USER_LEVEL_SERVICE] = UserLevelService
    _imported_gamification_services[BADGE_SERVICE] = BadgeService
    _imported_gamification_services[USER_ACHIEVEMENT_SERVICE] = UserAchievementService
    _imported_gamification_services[USER_RATING_SERVICE] = UserRatingService
    logger.info("Successfully imported all specified gamification services.")
except ImportError as e:
    logger.warning(f"Could not import one or more gamification services from .gamification: {e}. Attempting individual imports.")
    for service_name_const in _gamification_service_names:
        try:
            module = __import__("app.src.services.gamification", globals(), locals(), [service_name_const], 0)
            _imported_gamification_services[service_name_const] = getattr(module, service_name_const)
            logger.info(f"Successfully imported {service_name_const} individually.")
        except (ImportError, AttributeError) as ie:
            logger.warning(f"Could not import {service_name_const} from .gamification: {ie}")
            _imported_gamification_services[service_name_const] = None

for name, service in _imported_gamification_services.items():
    if service: globals()[name] = service
    else: globals()[name] = None # Ensure name exists as None if not imported


# --- Notification Services ---
NOTIFICATION_TEMPLATE_SERVICE = "NotificationTemplateService"
NOTIFICATION_SERVICE = "NotificationService" # Or InternalNotificationService
NOTIFICATION_DELIVERY_SERVICE = "NotificationDeliveryService"
EMAIL_NOTIFICATION_SERVICE = "EmailNotificationService" # Channel sender
SMS_NOTIFICATION_SERVICE = "SmsNotificationService"     # Channel sender
PUSH_NOTIFICATION_SERVICE = "PushNotificationService"   # Channel sender

_notification_service_names = [
    NOTIFICATION_TEMPLATE_SERVICE, NOTIFICATION_SERVICE, NOTIFICATION_DELIVERY_SERVICE,
    EMAIL_NOTIFICATION_SERVICE, SMS_NOTIFICATION_SERVICE, PUSH_NOTIFICATION_SERVICE
]
_imported_notification_services = {}

try:
    from .notifications import (
        NotificationTemplateService, NotificationService, NotificationDeliveryService,
        EmailNotificationService, SmsNotificationService, PushNotificationService
    )
    _imported_notification_services[NOTIFICATION_TEMPLATE_SERVICE] = NotificationTemplateService
    _imported_notification_services[NOTIFICATION_SERVICE] = NotificationService
    _imported_notification_services[NOTIFICATION_DELIVERY_SERVICE] = NotificationDeliveryService
    _imported_notification_services[EMAIL_NOTIFICATION_SERVICE] = EmailNotificationService
    _imported_notification_services[SMS_NOTIFICATION_SERVICE] = SmsNotificationService
    _imported_notification_services[PUSH_NOTIFICATION_SERVICE] = PushNotificationService
    logger.info("Successfully imported all specified notification services.")
except ImportError as e:
    logger.warning(f"Could not import one or more notification services from .notifications: {e}. Attempting individual imports.")
    for service_name_const in _notification_service_names:
        try:
            module = __import__("app.src.services.notifications", globals(), locals(), [service_name_const], 0)
            _imported_notification_services[service_name_const] = getattr(module, service_name_const)
            logger.info(f"Successfully imported {service_name_const} individually.")
        except (ImportError, AttributeError) as ie:
            logger.warning(f"Could not import {service_name_const} from .notifications: {ie}")
            _imported_notification_services[service_name_const] = None

for name, service in _imported_notification_services.items():
    if service: globals()[name] = service
    else: globals()[name] = None # Ensure name exists as None if not imported


# --- Integration Services ---
BASE_CALENDAR_INTEGRATION_SERVICE = "BaseCalendarIntegrationService"
GOOGLE_CALENDAR_SERVICE = "GoogleCalendarService"
OUTLOOK_CALENDAR_SERVICE = "OutlookCalendarService"
BASE_MESSENGER_INTEGRATION_SERVICE = "BaseMessengerIntegrationService"
TELEGRAM_INTEGRATION_SERVICE = "TelegramIntegrationService"
VIBER_INTEGRATION_SERVICE = "ViberIntegrationService"
SLACK_INTEGRATION_SERVICE = "SlackIntegrationService"
TEAMS_INTEGRATION_SERVICE = "TeamsIntegrationService"

_integration_service_names = [
    BASE_CALENDAR_INTEGRATION_SERVICE, GOOGLE_CALENDAR_SERVICE, OUTLOOK_CALENDAR_SERVICE,
    BASE_MESSENGER_INTEGRATION_SERVICE, TELEGRAM_INTEGRATION_SERVICE, VIBER_INTEGRATION_SERVICE,
    SLACK_INTEGRATION_SERVICE, TEAMS_INTEGRATION_SERVICE
]
_imported_integration_services = {}

try:
    from .integrations import (
        BaseCalendarIntegrationService, GoogleCalendarService, OutlookCalendarService,
        BaseMessengerIntegrationService, TelegramIntegrationService, ViberIntegrationService,
        SlackIntegrationService, TeamsIntegrationService
    )
    _imported_integration_services[BASE_CALENDAR_INTEGRATION_SERVICE] = BaseCalendarIntegrationService
    _imported_integration_services[GOOGLE_CALENDAR_SERVICE] = GoogleCalendarService
    _imported_integration_services[OUTLOOK_CALENDAR_SERVICE] = OutlookCalendarService
    _imported_integration_services[BASE_MESSENGER_INTEGRATION_SERVICE] = BaseMessengerIntegrationService
    _imported_integration_services[TELEGRAM_INTEGRATION_SERVICE] = TelegramIntegrationService
    _imported_integration_services[VIBER_INTEGRATION_SERVICE] = ViberIntegrationService
    _imported_integration_services[SLACK_INTEGRATION_SERVICE] = SlackIntegrationService
    _imported_integration_services[TEAMS_INTEGRATION_SERVICE] = TeamsIntegrationService
    logger.info("Successfully imported all specified integration services.")
except ImportError as e:
    logger.warning(f"Could not import one or more integration services from .integrations: {e}. Attempting individual imports.")
    for service_name_const in _integration_service_names:
        try:
            module = __import__("app.src.services.integrations", globals(), locals(), [service_name_const], 0)
            _imported_integration_services[service_name_const] = getattr(module, service_name_const)
            logger.info(f"Successfully imported {service_name_const} individually.")
        except (ImportError, AttributeError) as ie:
            logger.warning(f"Could not import {service_name_const} from .integrations: {ie}")
            _imported_integration_services[service_name_const] = None

for name, service in _imported_integration_services.items():
    if service: globals()[name] = service
    else: globals()[name] = None # Ensure name exists as None if not imported


# Construct __all__ dynamically
__all__ = []
if BaseService:
    __all__.append("BaseService")

__all__.extend([name for name, service in _imported_system_services.items() if service is not None])
__all__.extend([name for name, service in _imported_dictionary_services.items() if service is not None])
__all__.extend([name for name, service in _imported_auth_services.items() if service is not None])
__all__.extend([name for name, service in _imported_group_services.items() if service is not None])
__all__.extend([name for name, service in _imported_task_event_services.items() if service is not None])
__all__.extend([name for name, service in _imported_bonus_services.items() if service is not None])
__all__.extend([name for name, service in _imported_gamification_services.items() if service is not None])
__all__.extend([name for name, service in _imported_notification_services.items() if service is not None])
__all__.extend([name for name, service in _imported_integration_services.items() if service is not None])

# Ensure __all__ has unique entries
# and sort for consistency.
__all__ = sorted(list(set(__all__)))


# Further imports for other service domains (auth, groups, tasks, etc.) can be added similarly
# by following the pattern above:
# 1. Define constants for service names.
# 2. Create a list of these names.
# 3. Create a dictionary to store imported services.
# 4. Attempt collective import, then individual fallbacks.
# 5. Update globals() with successfully imported services.
# 6. Extend __all__ with the names of successfully imported services.
# (The final sort and set operation on __all__ will handle uniqueness).

logger.info(f"Services package exports: {__all__}")
