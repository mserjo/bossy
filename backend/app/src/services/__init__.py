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


# Construct __all__ dynamically
__all__ = []
if BaseService:
    __all__.append("BaseService")

__all__.extend([name for name, service in _imported_system_services.items() if service is not None])
__all__.extend([name for name, service in _imported_dictionary_services.items() if service is not None])
__all__.extend([name for name, service in _imported_auth_services.items() if service is not None])
__all__.extend([name for name, service in _imported_group_services.items() if service is not None])

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
