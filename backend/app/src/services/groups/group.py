# backend/app/src/services/groups/group.py
import logging
from typing import List, Optional, Any, Dict # Added Dict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.exc import IntegrityError

from app.src.services.base import BaseService
from app.src.models.groups.group import Group # SQLAlchemy Group model
from app.src.models.auth.user import User # For creator and members
from app.src.models.dictionaries.group_types import GroupType
from app.src.models.groups.membership import GroupMembership # For adding creator as admin
from app.src.models.dictionaries.user_roles import UserRole # For default admin role

from app.src.schemas.groups.group import ( # Pydantic Group schemas
    GroupCreate,
    GroupUpdate,
    GroupResponse,
    GroupDetailedResponse # Assuming a more detailed response schema
)
# from app.src.services.groups.membership import GroupMembershipService # Potentially for adding creator, but avoid circularity for now
# from app.src.services.auth.user import UserService # For fetching user details

# Initialize logger for this module
logger = logging.getLogger(__name__)

class GroupService(BaseService):
    """
    Service for managing core group operations including creation, updates,
    retrieval, and deletion of groups.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        logger.info("GroupService initialized.")

    async def get_group_by_id(self, group_id: UUID, include_details: bool = False) -> Optional[GroupResponse]: # Or GroupDetailedResponse
        """
        Retrieves a group by its ID.
        Can optionally include more details like members, settings, etc.
        """
        logger.debug(f"Attempting to retrieve group by ID: {group_id}, include_details: {include_details}")

        query = select(Group).where(Group.id == group_id)
        if include_details:
            # Eager load relationships needed for GroupDetailedResponse
            query = query.options(
                selectinload(Group.members).joinedload(GroupMembership.user).options(selectinload(User.roles), selectinload(User.user_type)), # Load members and their user details + roles + type
                selectinload(Group.group_type), # Load group type
                selectinload(Group.created_by_user).options(selectinload(User.user_type)), # Load creator and their type
                selectinload(Group.updated_by_user).options(selectinload(User.user_type)) if hasattr(Group, 'updated_by_user') else None, # If updated_by_user exists
                # selectinload(Group.settings), # If Group has a direct relationship to GroupSetting model
                # selectinload(Group.tasks), # Example if tasks are directly linked
            )
            # Filter out None options from query.options if they occur
            query = query.options(*(opt for opt in query.get_options() if opt is not None))


        result = await self.db_session.execute(query)
        group_db = result.scalar_one_or_none()

        if group_db:
            logger.info(f"Group with ID '{group_id}' found.")
            if include_details:
                # Ensure GroupDetailedResponse can handle the loaded relationships
                # return GroupDetailedResponse.model_validate(group_db) # Pydantic v2
                return GroupDetailedResponse.from_orm(group_db) # Pydantic v1
            # return GroupResponse.model_validate(group_db) # Pydantic v2
            return GroupResponse.from_orm(group_db) # Pydantic v1

        logger.info(f"Group with ID '{group_id}' not found.")
        return None

    async def create_group(self, group_create_data: GroupCreate, creator_id: UUID) -> Optional[GroupDetailedResponse]: # Return Optional for consistency
        """
        Creates a new group and sets the creator as the initial admin.

        Args:
            group_create_data (GroupCreate): Data for the new group.
            creator_id (UUID): The ID of the user creating the group.

        Returns:
            Optional[GroupDetailedResponse]: The created group with details, or None if creation failed before commit.

        Raises:
            ValueError: If creator user, group type, or default admin role is not found,
                        or if group name conflicts within a certain scope (if applicable).
        """
        logger.debug(f"Attempting to create new group '{group_create_data.name}' by user ID: {creator_id}")

        # Validate creator user
        creator_user_db = await self.db_session.get(User, creator_id)
        if not creator_user_db:
            logger.error(f"Creator user with ID '{creator_id}' not found. Cannot create group.")
            raise ValueError(f"Creator user with ID '{creator_id}' not found.")

        # Validate group type if group_type_id is provided
        if group_create_data.group_type_id:
            group_type_db = await self.db_session.get(GroupType, group_create_data.group_type_id)
            if not group_type_db:
                logger.error(f"GroupType with ID '{group_create_data.group_type_id}' not found.")
                raise ValueError(f"GroupType with ID '{group_create_data.group_type_id}' not found.")

        # Optional: Check for group name uniqueness if required by business logic
        # stmt_name = select(Group).where(Group.name == group_create_data.name)
        # if (await self.db_session.execute(stmt_name)).scalar_one_or_none():
        #     logger.warning(f"Group with name '{group_create_data.name}' already exists.")
        #     raise ValueError(f"Group with name '{group_create_data.name}' already exists.")

        # group_db_data = group_create_data.model_dump() # Pydantic v2
        group_db_data = group_create_data.dict() # Pydantic v1

        new_group_db = Group(**group_db_data, created_by_user_id=creator_id)
        self.db_session.add(new_group_db)

        # Add creator as admin
        admin_role_stmt = select(UserRole).where(UserRole.code == "ADMIN")
        admin_role_db = (await self.db_session.execute(admin_role_stmt)).scalar_one_or_none()
        if not admin_role_db:
            # Not calling self.rollback() here as nothing critical committed yet, error will prevent commit.
            logger.error("Default 'ADMIN' role not found in database. Cannot assign creator as admin.")
            raise ValueError("Default 'ADMIN' role not found. Group setup failed.")

        await self.db_session.flush() # Ensure new_group_db.id is populated

        initial_membership = GroupMembership(
            user_id=creator_id,
            group_id=new_group_db.id,
            user_role_id=admin_role_db.id,
            is_active=True,
        )
        self.db_session.add(initial_membership)

        try:
            await self.commit()
            # After commit, group_db.id is definitely available.
            # Fetch the group again with all necessary details for the response.
            # This ensures that all relationships set up by SQLAlchemy event listeners or defaults are loaded.
            created_group_detailed = await self.get_group_by_id(new_group_db.id, include_details=True)
            if created_group_detailed:
                 logger.info(f"Group '{new_group_db.name}' (ID: {new_group_db.id}) created successfully by user ID '{creator_id}'.")
                 return created_group_detailed # Should be GroupDetailedResponse due to include_details=True
            else: # Should not happen if commit was successful and ID is valid
                logger.error(f"Failed to retrieve newly created group ID {new_group_db.id} after commit.")
                return None # Or raise an internal server error

        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Integrity error creating group '{group_create_data.name}': {e}", exc_info=True)
            raise ValueError(f"Could not create group due to a data conflict: {e}")
        except Exception as e: # Catch any other errors during commit or re-fetch
            await self.rollback()
            logger.error(f"Unexpected error creating group '{group_create_data.name}': {e}", exc_info=True)
            raise

    async def update_group(self, group_id: UUID, group_update_data: GroupUpdate, current_user_id: UUID) -> Optional[GroupDetailedResponse]:
        """
        Updates a group's details.
        Requires permission check (e.g., user is admin of the group or superuser),
        which should be handled by the API layer or a permission dependency.
        This service method assumes permissions are already checked.
        """
        logger.debug(f"Attempting to update group ID: {group_id} by user ID: {current_user_id}")

        # Fetch the group with details to ensure all fields are loaded for response
        # Using get_group_by_id ensures consistent data loading logic
        group_to_update = await self.db_session.get(Group, group_id)

        if not group_to_update:
            logger.warning(f"Group ID '{group_id}' not found for update.")
            return None

        # update_data = group_update_data.model_dump(exclude_unset=True) # Pydantic v2
        update_data = group_update_data.dict(exclude_unset=True) # Pydantic v1

        if 'group_type_id' in update_data and update_data['group_type_id'] is not None:
            if group_to_update.group_type_id != update_data['group_type_id']:
                new_group_type_db = await self.db_session.get(GroupType, update_data['group_type_id'])
                if not new_group_type_db:
                    logger.error(f"New GroupType ID '{update_data['group_type_id']}' not found for update of group ID '{group_id}'.")
                    raise ValueError(f"Invalid GroupType ID: {update_data['group_type_id']}.")

        for field, value in update_data.items():
            if hasattr(group_to_update, field):
                setattr(group_to_update, field, value)
            else:
                logger.warning(f"Field '{field}' not found on Group model for update of group ID '{group_id}'. Skipping.")

        if hasattr(group_to_update, 'updated_by_user_id'): # Check if model has this field
            group_to_update.updated_by_user_id = current_user_id

        self.db_session.add(group_to_update)

        try:
            await self.commit()
            # Fetch again with all details for response consistency
            updated_group_detailed = await self.get_group_by_id(group_id, include_details=True)
            if updated_group_detailed:
                logger.info(f"Group ID '{group_id}' updated successfully by user ID '{current_user_id}'.")
                return updated_group_detailed
            else: # Should ideally not happen
                logger.error(f"Failed to retrieve updated group ID {group_id} after commit.")
                return None
        except Exception as e:
            await self.rollback()
            logger.error(f"Error during group update commit for group ID '{group_id}': {e}", exc_info=True)
            raise


    async def delete_group(self, group_id: UUID, current_user_id: UUID) -> bool:
        """
        Deletes a group.
        Requires permission checks (admin/superuser).
        Business logic might prevent deletion if group has active members or tasks, etc.
        For now, a simple deletion. Consider soft delete via 'deleted_at' or 'is_active' fields.
        """
        logger.debug(f"Attempting to delete group ID: {group_id} by user ID: {current_user_id}")

        group_db = await self.db_session.get(Group, group_id)
        if not group_db:
            logger.warning(f"Group ID '{group_id}' not found for deletion.")
            return False

        # Placeholder for business logic: e.g., check if group is empty
        # from sqlalchemy import func
        # member_count_stmt = select(func.count(GroupMembership.id)).where(GroupMembership.group_id == group_id)
        # member_count = (await self.db_session.execute(member_count_stmt)).scalar_one()
        # if member_count > 0:
        #     logger.warning(f"Group ID '{group_id}' has {member_count} members. Deletion aborted.")
        #     raise ValueError(f"Cannot delete group with active members.")

        await self.db_session.delete(group_db)
        await self.commit()
        logger.info(f"Group ID '{group_id}' deleted successfully by user ID '{current_user_id}'.")
        return True

    async def list_user_groups(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[GroupResponse]:
        """Lists all groups a user is an active member of."""
        logger.debug(f"Listing groups for user ID: {user_id}, skip={skip}, limit={limit}")

        stmt = select(Group).            join(GroupMembership, Group.id == GroupMembership.group_id).            where(GroupMembership.user_id == user_id, GroupMembership.is_active == True).            options(selectinload(Group.group_type)).            order_by(Group.name).            offset(skip).            limit(limit)

        result = await self.db_session.execute(stmt)
        groups_db = result.scalars().unique().all()

        # response_list = [GroupResponse.model_validate(g) for g in groups_db] # Pydantic v2
        response_list = [GroupResponse.from_orm(g) for g in groups_db] # Pydantic v1
        logger.info(f"Retrieved {len(response_list)} groups for user ID '{user_id}'.")
        return response_list

    async def get_group_activity_report(self, group_id: UUID) -> Dict[str, Any]:
        logger.info(f"Generating activity report for group ID: {group_id} (Placeholder)")
        return {"group_id": group_id, "status": "Report generation not yet implemented."}


logger.info("GroupService class defined.")
