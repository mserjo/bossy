# backend/app/src/models/groups/__init__.py

"""
This package contains SQLAlchemy models related to groups, group membership,
settings, and invitations.
"""

import logging

logger = logging.getLogger(__name__)
logger.debug("Group models package initialized.")

# Example of re-exporting for easier access:
# from .group import Group
# from .membership import GroupMembership
# from .settings import GroupSetting
# from .invitation import GroupInvitation

# __all__ = [
#     "Group",
#     "GroupMembership",
#     "GroupSetting",
#     "GroupInvitation",
# ]
