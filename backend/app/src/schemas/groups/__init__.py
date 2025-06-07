# backend/app/src/schemas/groups/__init__.py

"""
This package contains Pydantic schemas related to groups, group settings,
memberships, and invitations.
"""

import logging

logger = logging.getLogger(__name__)
logger.debug("Group schemas package initialized.")

# Example of re-exporting for easier access:
# from .group import GroupResponse, GroupCreate, GroupUpdate
# from .membership import GroupMembershipResponse, GroupMembershipCreate
# from .settings import GroupSettingResponse
# from .invitation import GroupInvitationResponse

# __all__ = [
#     "GroupResponse",
#     "GroupCreate",
#     "GroupUpdate",
#     # ... other group schemas
# ]
