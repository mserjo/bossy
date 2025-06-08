# backend/app/src/repositories/system/__init__.py

"""
This package contains repository classes for system-related entities.

Each module within this package should define repository classes that interact
with system-level data models (e.g., settings, logs, health checks).
"""

# Import and re-export repository classes here as they are created.
# This allows for cleaner imports from other parts of the application,
# e.g., `from app.src.repositories.system import SystemSettingRepository`.

from .settings_repository import SystemSettingRepository
from .monitoring_repository import SystemLogRepository, PerformanceMetricRepository
from .health_repository import ServiceHealthRepository


# Define __all__ to specify which names are exported when `from .system import *` is used.
# This also helps linters and IDEs understand the public API of this package.
__all__ = [
    "SystemSettingRepository",
    "SystemLogRepository",
    "PerformanceMetricRepository",
    "ServiceHealthRepository",
]

# Detailed comments:
# This __init__.py file initializes the 'system' sub-package within the 'repositories'
# package. Its primary roles are:
#
# 1. Package Recognition:
#    It makes Python treat the 'repositories/system' directory as a sub-package,
#    enabling structured imports and organization of system-specific repositories.
#
# 2. Namespace Management:
#    It serves as a central point for importing and re-exporting the repository
#    classes defined in other modules within this sub-package (like
#    `settings_repository.py`, `monitoring_repository.py`, etc.). This simplifies
#    access for other application layers. For instance, instead of:
#    `from app.src.repositories.system.settings_repository import SystemSettingRepository`
#    you can use:
#    `from app.src.repositories.system import SystemSettingRepository`
#    (once SystemSettingRepository is defined and uncommented above).
#
# 3. Public API Definition (`__all__`):
#    The `__all__` list explicitly declares which symbols are part of the public
#    interface of this sub-package. This is good practice for package maintainability
#    and clarity. When new repositories are added to this sub-package, they should
#    be imported here and their names added to the `__all__` list.
#
# Example of adding a new repository (e.g., SystemSettingRepository):
#
# 1. Create `settings_repository.py` in `backend/app/src/repositories/system/`.
# 2. Define `SystemSettingRepository` in that file.
# 3. In this `__init__.py` file:
#    - Uncomment or add: `from .settings_repository import SystemSettingRepository`
#    - Uncomment or add: `"SystemSettingRepository"` to the `__all__` list.
#
# This approach ensures that the system repositories are well-organized and
# easily accessible throughout the application while maintaining a clear structure.
