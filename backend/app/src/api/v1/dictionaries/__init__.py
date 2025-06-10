# backend/app/src/api/v1/dictionaries/__init__.py
from fastapi import APIRouter

from . import statuses
from . import user_roles
from . import user_types
from . import group_types
from . import task_types
from . import bonus_types
from . import calendars
from . import messengers

router = APIRouter()

# Включити всі роутери словників
router.include_router(statuses.router, prefix="/statuses", tags=["Dictionary - Statuses"])
router.include_router(user_roles.router, prefix="/user-roles", tags=["Dictionary - User Roles"])
router.include_router(user_types.router, prefix="/user-types", tags=["Dictionary - User Types"])
router.include_router(group_types.router, prefix="/group-types", tags=["Dictionary - Group Types"])
router.include_router(task_types.router, prefix="/task-types", tags=["Dictionary - Task Types"])
router.include_router(bonus_types.router, prefix="/bonus-types", tags=["Dictionary - Bonus Types"])
router.include_router(calendars.router, prefix="/calendar-providers", tags=["Dictionary - Calendar Providers"])
router.include_router(messengers.router, prefix="/messenger-platforms", tags=["Dictionary - Messenger Platforms"])

__all__ = ["router"] # Експортувати головний роутер словників
