# backend/app/src/services/groups/membership.py
import logging
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.exc import IntegrityError

from app.src.services.base import BaseService
from app.src.models.groups.membership import GroupMembership # SQLAlchemy GroupMembership model
from app.src.models.groups.group import Group # For group context
from app.src.models.auth.user import User # For user context
from app.src.models.dictionaries.user_roles import UserRole # For roles within group

from app.src.schemas.groups.membership import ( # Pydantic Schemas
    GroupMembershipCreate, # For adding a user to a group with a role
    GroupMembershipUpdate, # For changing a user's role or status in a group
    GroupMembershipResponse,
    GroupMemberResponse # A schema that might include more user details
)
# from app.src.services.auth.user import UserService # For fetching user details if needed for validation
# from app.src.services.groups.group import GroupService # For fetching group details if needed

# Initialize logger for this module
logger = logging.getLogger(__name__)

class GroupMembershipService(BaseService):
    """
    Service for managing user memberships within groups, including their roles and status.
    Handles adding users to groups, removing them, updating roles, and listing members.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        logger.info("GroupMembershipService initialized.")

    async def add_member_to_group(
        self,
        group_id: UUID,
        user_id: UUID,
        role_code: str, # e.g., "USER", "ADMIN"
        added_by_user_id: Optional[UUID] = None # For audit trail
    ) -> GroupMembershipResponse:
        """
        Adds a user to a group with a specified role.
        Prevents adding if the user is already an active member.
        Reactivates and updates role if user is an inactive member.

        Args:
            group_id (UUID): The ID of the group.
            user_id (UUID): The ID of the user to add.
            role_code (str): The code of the role to assign to the user in this group.
            added_by_user_id (Optional[UUID]): ID of the user performing the action.

        Returns:
            GroupMembershipResponse: The created or updated membership details.

        Raises:
            ValueError: If group, user, or role is not found, or if user is already an active member with the same role.
        """
        logger.debug(f"Attempting to add user ID '{user_id}' to group ID '{group_id}' with role code '{role_code}'.")

        # Validate group, user, and role
        group = await self.db_session.get(Group, group_id)
        if not group: raise ValueError(f"Group with ID '{group_id}' not found.")

        user = await self.db_session.get(User, user_id)
        if not user: raise ValueError(f"User with ID '{user_id}' not found.")

        role_stmt = select(UserRole).where(UserRole.code == role_code)
        role = (await self.db_session.execute(role_stmt)).scalar_one_or_none()
        if not role: raise ValueError(f"UserRole with code '{role_code}' not found.")

        # Check for existing active membership
        existing_active_membership_stmt = select(GroupMembership).options(
            selectinload(GroupMembership.role) # Load role for comparison
        ).where(
            GroupMembership.group_id == group_id,
            GroupMembership.user_id == user_id,
            GroupMembership.is_active == True
        )
        existing_active_membership = (await self.db_session.execute(existing_active_membership_stmt)).scalar_one_or_none()

        if existing_active_membership:
            if existing_active_membership.user_role_id == role.id:
                logger.info(f"User ID '{user_id}' is already an active member of group ID '{group_id}' with the role '{role_code}'. Returning existing membership.")
                # return GroupMembershipResponse.model_validate(existing_active_membership) # Pydantic v2
                return GroupMembershipResponse.from_orm(existing_active_membership) # Pydantic v1
            else:
                # User is active but role is different, proceed to update role via update_member_role logic
                logger.info(f"User ID '{user_id}' is active in group ID '{group_id}' but with a different role. Proceeding to update role to '{role_code}'.")
                # This effectively becomes an update operation.
                # For clarity, one might redirect to update_member_role or raise an error asking to use update endpoint.
                # Here, we'll let it be handled by the inactive check logic path if it were an update.
                # However, since it's active, this path is an explicit update.
                # For simplicity of this method's contract (add member), we can raise or update. Let's update.
                return await self.update_member_role(group_id, user_id, role_code, added_by_user_id)


        # Check for existing inactive membership - reactivate and update role
        existing_inactive_membership_stmt = select(GroupMembership).where(
            GroupMembership.group_id == group_id,
            GroupMembership.user_id == user_id,
            GroupMembership.is_active == False
        )
        membership_db = (await self.db_session.execute(existing_inactive_membership_stmt)).scalar_one_or_none()

        if membership_db: # Was inactive member
            logger.info(f"Reactivating and updating role for inactive member user ID '{user_id}' in group ID '{group_id}'.")
            membership_db.is_active = True
            membership_db.user_role_id = role.id
            membership_db.joined_at = datetime.now(timezone.utc)
            if hasattr(membership_db, 'added_by_user_id') and added_by_user_id:
                 membership_db.added_by_user_id = added_by_user_id
        else: # New member
            create_data = {
                "group_id": group_id,
                "user_id": user_id,
                "user_role_id": role.id,
                "is_active": True,
            }
            if hasattr(GroupMembership, 'added_by_user_id') and added_by_user_id:
                create_data['added_by_user_id'] = added_by_user_id

            membership_db = GroupMembership(**create_data)
            self.db_session.add(membership_db)

        try:
            await self.commit()
            await self.db_session.refresh(membership_db, attribute_names=['user', 'group', 'role'])
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Integrity error adding user ID '{user_id}' to group ID '{group_id}': {e}", exc_info=True)
            raise ValueError(f"Could not add user to group due to a data conflict: {e}")

        logger.info(f"User ID '{user_id}' successfully added/reactivated in group ID '{group_id}' with role '{role.name}'.")
        # return GroupMembershipResponse.model_validate(membership_db) # Pydantic v2
        return GroupMembershipResponse.from_orm(membership_db) # Pydantic v1


    async def remove_member_from_group(self, group_id: UUID, user_id: UUID, removed_by_user_id: Optional[UUID] = None) -> bool:
        """
        Removes a user from a group by deactivating their membership.
        Handles logic like "admin cannot leave if they are the only admin".

        Args:
            group_id (UUID): The ID of the group.
            user_id (UUID): The ID of the user to remove.
            removed_by_user_id (Optional[UUID]): ID of user performing action.

        Returns:
            bool: True if removal was successful, False otherwise.

        Raises:
            ValueError: If the user is the last admin in the group.
        """
        logger.debug(f"Attempting to remove user ID '{user_id}' from group ID '{group_id}'.")

        membership_stmt = select(GroupMembership).options(
            selectinload(GroupMembership.role),
        ).where(
            GroupMembership.group_id == group_id,
            GroupMembership.user_id == user_id,
            GroupMembership.is_active == True
        )
        membership_db = (await self.db_session.execute(membership_stmt)).scalar_one_or_none()

        if not membership_db:
            logger.warning(f"Active membership for user ID '{user_id}' in group ID '{group_id}' not found. Cannot remove.")
            return False

        if membership_db.role.code == "ADMIN":
            active_admins_stmt = select(func.count(GroupMembership.id)).select_from(GroupMembership).join(UserRole).where( # Import func from sqlalchemy
                GroupMembership.group_id == group_id,
                GroupMembership.is_active == True,
                UserRole.code == "ADMIN",
                GroupMembership.user_id != user_id
            )
            other_active_admins_count = (await self.db_session.execute(active_admins_stmt)).scalar_one()
            if other_active_admins_count == 0:
                logger.warning(f"User ID '{user_id}' is the last admin in group ID '{group_id}'. Cannot remove.")
                raise ValueError("Cannot remove the last admin from the group. Assign another admin first.")

        membership_db.is_active = False
        if hasattr(membership_db, 'removed_at'):
            membership_db.removed_at = datetime.now(timezone.utc)
        if hasattr(membership_db, 'removed_by_user_id') and removed_by_user_id:
            membership_db.removed_by_user_id = removed_by_user_id

        self.db_session.add(membership_db)
        await self.commit()

        logger.info(f"User ID '{user_id}' successfully removed (deactivated) from group ID '{group_id}'.")
        return True

    async def update_member_role(
        self,
        group_id: UUID,
        user_id: UUID,
        new_role_code: str,
        updated_by_user_id: Optional[UUID] = None
    ) -> Optional[GroupMembershipResponse]:
        """
        Updates a user's role within a group.
        Handles logic if demoting the last admin.
        """
        logger.debug(f"Attempting to update role for user ID '{user_id}' in group ID '{group_id}' to role code '{new_role_code}'.")

        membership_stmt = select(GroupMembership).options(selectinload(GroupMembership.role)).where(
            GroupMembership.group_id == group_id,
            GroupMembership.user_id == user_id,
            GroupMembership.is_active == True
        )
        membership_db = (await self.db_session.execute(membership_stmt)).scalar_one_or_none()

        if not membership_db:
            logger.warning(f"Active membership for user ID '{user_id}' in group ID '{group_id}' not found. Cannot update role.")
            return None

        new_role_stmt = select(UserRole).where(UserRole.code == new_role_code)
        new_role_db = (await self.db_session.execute(new_role_stmt)).scalar_one_or_none()
        if not new_role_db:
            raise ValueError(f"UserRole with code '{new_role_code}' not found.")

        if membership_db.user_role_id == new_role_db.id:
            logger.info(f"User ID '{user_id}' in group ID '{group_id}' already has role '{new_role_code}'. No update needed.")
            # return GroupMembershipResponse.model_validate(membership_db) # Pydantic v2
            return GroupMembershipResponse.from_orm(membership_db) # Pydantic v1

        if membership_db.role.code == "ADMIN" and new_role_db.code != "ADMIN":
            from sqlalchemy import func # Local import for func
            active_admins_stmt = select(func.count(GroupMembership.id)).select_from(GroupMembership).join(UserRole).where(
                GroupMembership.group_id == group_id,
                GroupMembership.is_active == True,
                UserRole.code == "ADMIN",
                GroupMembership.user_id != user_id
            )
            other_active_admins_count = (await self.db_session.execute(active_admins_stmt)).scalar_one()
            if other_active_admins_count == 0:
                logger.warning(f"User ID '{user_id}' is the last admin in group ID '{group_id}'. Cannot change role from ADMIN.")
                raise ValueError("Cannot change the role of the last admin. Assign another admin first.")

        membership_db.user_role_id = new_role_db.id
        if hasattr(membership_db, 'updated_by_user_id') and updated_by_user_id:
             membership_db.updated_by_user_id = updated_by_user_id
        if hasattr(membership_db, 'role_updated_at'):
            membership_db.role_updated_at = datetime.now(timezone.utc)

        self.db_session.add(membership_db)
        await self.commit()
        await self.db_session.refresh(membership_db, attribute_names=['user', 'group', 'role'])

        logger.info(f"Role for user ID '{user_id}' in group ID '{group_id}' updated to '{new_role_db.name}'.")
        # return GroupMembershipResponse.model_validate(membership_db) # Pydantic v2
        return GroupMembershipResponse.from_orm(membership_db) # Pydantic v1

    async def list_group_members(
        self,
        group_id: UUID,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = True
    ) -> List[GroupMemberResponse]:
        logger.debug(f"Listing members for group ID: {group_id}, is_active: {is_active}, skip={skip}, limit={limit}")

        stmt = select(GroupMembership).options(
            selectinload(GroupMembership.user).options(
                selectinload(User.user_type),
            ),
            selectinload(GroupMembership.role)
        ).where(GroupMembership.group_id == group_id)

        if is_active is not None:
            stmt = stmt.where(GroupMembership.is_active == is_active)

        stmt = stmt.join(User, GroupMembership.user_id == User.id).               order_by(User.username).               offset(skip).               limit(limit)

        result = await self.db_session.execute(stmt)
        memberships_db = result.scalars().unique().all()

        # response_list = [GroupMemberResponse.model_validate(m) for m in memberships_db] # Pydantic v2
        response_list = [GroupMemberResponse.from_orm(m) for m in memberships_db] # Pydantic v1
        logger.info(f"Retrieved {len(response_list)} members for group ID '{group_id}'.")
        return response_list

    async def get_membership_details(self, group_id: UUID, user_id: UUID) -> Optional[GroupMembershipResponse]:
        logger.debug(f"Getting membership details for user ID {user_id} in group ID {group_id}")
        stmt = select(GroupMembership).options(
            selectinload(GroupMembership.user).options(selectinload(User.user_type)), # Eager load user and its type
            selectinload(GroupMembership.group).options(selectinload(Group.group_type)), # Eager load group and its type
            selectinload(GroupMembership.role) # Eager load role
        ).where(GroupMembership.group_id == group_id, GroupMembership.user_id == user_id)

        membership_db = (await self.db_session.execute(stmt)).scalar_one_or_none()
        if not membership_db:
            logger.info(f"No membership found for user ID {user_id} in group ID {group_id}")
            return None

        # return GroupMembershipResponse.model_validate(membership_db) # Pydantic v2
        return GroupMembershipResponse.from_orm(membership_db) # Pydantic v1


logger.info("GroupMembershipService class defined.")
