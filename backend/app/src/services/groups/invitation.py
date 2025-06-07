# backend/app/src/services/groups/invitation.py
import logging
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from app.src.services.base import BaseService
from app.src.models.groups.invitation import GroupInvitation # SQLAlchemy GroupInvitation model
from app.src.models.groups.group import Group # For group context
from app.src.models.auth.user import User # For invited user (if email specified) and inviter
from app.src.models.dictionaries.user_roles import UserRole # For role to be assigned on acceptance

from app.src.schemas.groups.invitation import ( # Pydantic Schemas
    GroupInvitationCreate,
    GroupInvitationResponse,
    GroupInvitationAccept # Schema for accepting an invitation (might just need the code)
)
from app.src.schemas.groups.membership import GroupMembershipResponse # For return type of accept_invitation

# GroupMembershipService might be needed to add user to group upon acceptance
# from app.src.services.groups.membership import GroupMembershipService

# Initialize logger for this module
logger = logging.getLogger(__name__)

# Default invitation expiry (e.g., 7 days)
DEFAULT_INVITATION_EXPIRE_DAYS = 7

class GroupInvitationService(BaseService):
    """
    Service for managing group invitations.
    Handles creation, acceptance, decline, revocation, and listing of invitations.
    """

    def __init__(self, db_session: AsyncSession): # Potentially pass other services like GroupMembershipService
        super().__init__(db_session)
        # self.membership_service = GroupMembershipService(db_session) # If auto-adding on accept
        logger.info("GroupInvitationService initialized.")

    async def create_invitation(
        self,
        group_id: UUID,
        inviter_user_id: UUID,
        role_to_assign_code: str, # Role code for the user upon joining
        invite_data: GroupInvitationCreate # Contains optional email, expiry override
    ) -> GroupInvitationResponse:
        """
        Creates a new invitation for a user to join a group.

        Args:
            group_id (UUID): The ID of the group to invite to.
            inviter_user_id (UUID): The ID of the user creating the invitation (must be admin/authorized).
            role_to_assign_code (str): The code of the role the invited user will get.
            invite_data (GroupInvitationCreate): Additional data like target email or custom expiry.

        Returns:
            GroupInvitationResponse: The created invitation details.

        Raises:
            ValueError: If group, inviter, or role_to_assign not found, or if user already member/invited.
        """
        logger.debug(f"Attempting to create invitation for group ID '{group_id}' by user ID '{inviter_user_id}'.")

        # Validate group, inviter, and role_to_assign
        group = await self.db_session.get(Group, group_id)
        if not group: raise ValueError(f"Group with ID '{group_id}' not found.")

        inviter = await self.db_session.get(User, inviter_user_id)
        if not inviter: raise ValueError(f"Inviter user with ID '{inviter_user_id}' not found.")

        role_stmt = select(UserRole).where(UserRole.code == role_to_assign_code)
        role_to_assign = (await self.db_session.execute(role_stmt)).scalar_one_or_none()
        if not role_to_assign: raise ValueError(f"Role with code '{role_to_assign_code}' not found.")

        # Check if target email user (if provided) is already a member or has a pending invite
        invited_user_id: Optional[UUID] = None
        if invite_data.email:
            normalized_email = invite_data.email.lower()
            invited_user_stmt = select(User).where(User.email == normalized_email)
            invited_user = (await self.db_session.execute(invited_user_stmt)).scalar_one_or_none()
            if invited_user:
                invited_user_id = invited_user.id
                # Check if this user is already an active member
                from app.src.models.groups.membership import GroupMembership # Local import for check
                active_member_stmt = select(GroupMembership.id).where( # Select only ID for existence check
                    GroupMembership.group_id == group_id,
                    GroupMembership.user_id == invited_user_id,
                    GroupMembership.is_active == True
                )
                if (await self.db_session.execute(active_member_stmt)).scalar_one_or_none():
                    raise ValueError(f"User with email '{normalized_email}' is already an active member of group '{group.name}'.")

            # Check for existing, non-expired, non-accepted invitation for this email/user to this group
            existing_invite_stmt = select(GroupInvitation.id).where( # Select only ID for existence check
                GroupInvitation.group_id == group_id,
                (GroupInvitation.email == normalized_email) | (GroupInvitation.invited_user_id == invited_user_id if invited_user_id else False),
                GroupInvitation.status == "pending",
                GroupInvitation.expires_at > datetime.now(timezone.utc)
            )
            if (await self.db_session.execute(existing_invite_stmt)).scalar_one_or_none():
                raise ValueError(f"An active pending invitation already exists for '{normalized_email or f'user ID {invited_user_id}'}' to group '{group.name}'.")


        invitation_code = str(uuid4())

        expires_at = datetime.now(timezone.utc) + timedelta(days=invite_data.custom_expire_days or DEFAULT_INVITATION_EXPIRE_DAYS)

        new_invitation_db = GroupInvitation(
            group_id=group_id,
            inviter_user_id=inviter_user_id,
            invited_user_id=invited_user_id,
            email=normalized_email if invite_data.email else None,
            role_id_to_assign=role_to_assign.id,
            invitation_code=invitation_code,
            status="pending",
            expires_at=expires_at
        )

        self.db_session.add(new_invitation_db)
        try:
            await self.commit()
            await self.db_session.refresh(new_invitation_db, attribute_names=['group', 'inviter', 'invited_user', 'role_to_assign'])
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Integrity error creating invitation for group ID '{group_id}': {e}", exc_info=True)
            raise ValueError(f"Could not create invitation due to a data conflict: {e}")

        logger.info(f"Invitation created successfully with code '{invitation_code}' for group ID '{group_id}'.")
        # return GroupInvitationResponse.model_validate(new_invitation_db) # Pydantic v2
        return GroupInvitationResponse.from_orm(new_invitation_db) # Pydantic v1

    async def get_invitation_by_code(self, invitation_code: str) -> Optional[GroupInvitationResponse]:
        """Retrieves an invitation by its unique code, if it's valid (pending and not expired)."""
        logger.debug(f"Attempting to retrieve invitation by code: {invitation_code}")

        stmt = select(GroupInvitation).options(
            selectinload(GroupInvitation.group),
            selectinload(GroupInvitation.inviter),
            selectinload(GroupInvitation.invited_user),
            selectinload(GroupInvitation.role_to_assign)
        ).where(
            GroupInvitation.invitation_code == invitation_code,
            GroupInvitation.status == "pending",
            GroupInvitation.expires_at > datetime.now(timezone.utc)
        )
        invitation_db = (await self.db_session.execute(stmt)).scalar_one_or_none()

        if invitation_db:
            logger.info(f"Valid pending invitation found for code '{invitation_code}'.")
            # return GroupInvitationResponse.model_validate(invitation_db) # Pydantic v2
            return GroupInvitationResponse.from_orm(invitation_db) # Pydantic v1

        logger.warning(f"No valid pending invitation found for code '{invitation_code}'. It might be invalid, expired, or already used.")
        return None

    async def accept_invitation(
        self,
        invitation_code: str,
        accepting_user_id: UUID
    ) -> GroupMembershipResponse:
        logger.info(f"User ID '{accepting_user_id}' attempting to accept invitation with code '{invitation_code}'.")

        # Fetch the full invitation ORM object to update its status
        stmt_get_orm = select(GroupInvitation).where(
            GroupInvitation.invitation_code == invitation_code,
            GroupInvitation.status == "pending",
            GroupInvitation.expires_at > datetime.now(timezone.utc)
        ).options(selectinload(GroupInvitation.role_to_assign)) # Load role for adding member

        invitation_db_record = (await self.db_session.execute(stmt_get_orm)).scalar_one_or_none()

        if not invitation_db_record:
            raise ValueError("Invitation is invalid, expired, or already used.")

        accepting_user = await self.db_session.get(User, accepting_user_id)
        if not accepting_user:
             raise ValueError("Accepting user not found.")

        if invitation_db_record.invited_user_id and invitation_db_record.invited_user_id != accepting_user_id:
            raise ValueError("This invitation is intended for another user.")

        if invitation_db_record.email and invitation_db_record.email.lower() != accepting_user.email.lower():
            raise ValueError("This invitation was sent to a different email address.")

        if not invitation_db_record.invited_user_id and accepting_user_id:
            invitation_db_record.invited_user_id = accepting_user_id

        invitation_db_record.status = "accepted"
        invitation_db_record.accepted_at = datetime.now(timezone.utc)
        invitation_db_record.responded_at = datetime.now(timezone.utc) # Also set responded_at
        self.db_session.add(invitation_db_record)

        from app.src.services.groups.membership import GroupMembershipService
        membership_service = GroupMembershipService(self.db_session)

        try:
            if not invitation_db_record.role_to_assign: # Should have been loaded or error earlier
                raise ValueError("Role to assign for invitation not found (internal error).")

            new_membership = await membership_service.add_member_to_group(
                group_id=invitation_db_record.group_id,
                user_id=accepting_user_id,
                role_code=invitation_db_record.role_to_assign.code,
                added_by_user_id=invitation_db_record.inviter_user_id
            )
            # The commit for invitation status change and new membership happens in membership_service's add_member_to_group,
            # or if it doesn't, it should be called here. Assuming add_member_to_group commits.
            # If add_member_to_group does not commit, we need: await self.commit()
            logger.info(f"Invitation code '{invitation_code}' accepted by user ID '{accepting_user_id}'. User added to group.")
            return new_membership

        except ValueError as ve:
            await self.rollback()
            logger.error(f"Error during membership creation while accepting invitation '{invitation_code}': {ve}", exc_info=True)
            raise ValueError(f"Failed to join group after accepting invitation: {ve}")
        except Exception as e:
            await self.rollback()
            logger.error(f"Unexpected error accepting invitation '{invitation_code}': {e}", exc_info=True)
            raise

    async def decline_invitation(self, invitation_code: str, declining_user_id: Optional[UUID] = None) -> bool:
        logger.info(f"User ID '{declining_user_id or 'Anonymous'}' attempting to decline invitation code '{invitation_code}'.")

        stmt = select(GroupInvitation).where(
            GroupInvitation.invitation_code == invitation_code,
            GroupInvitation.status == "pending",
            GroupInvitation.expires_at > datetime.now(timezone.utc)
        )
        invitation_db = (await self.db_session.execute(stmt)).scalar_one_or_none()

        if not invitation_db:
            logger.warning(f"No valid pending invitation found for code '{invitation_code}' to decline.")
            return False

        if declining_user_id and invitation_db.invited_user_id and invitation_db.invited_user_id != declining_user_id:
            logger.warning(f"User ID '{declining_user_id}' mismatch for declining invitation '{invitation_code}' intended for user ID '{invitation_db.invited_user_id}'.")
            return False

        invitation_db.status = "declined"
        invitation_db.responded_at = datetime.now(timezone.utc)
        self.db_session.add(invitation_db)
        await self.commit()
        logger.info(f"Invitation code '{invitation_code}' declined.")
        return True

    async def revoke_invitation(self, invitation_id: UUID, revoker_user_id: UUID) -> bool:
        logger.info(f"User ID '{revoker_user_id}' attempting to revoke invitation ID '{invitation_id}'.")

        invitation_db = await self.db_session.get(GroupInvitation, invitation_id, options=[selectinload(GroupInvitation.group)])
        if not invitation_db:
            logger.warning(f"Invitation ID '{invitation_id}' not found. Cannot revoke.")
            return False

        # Placeholder for permission check (e.g., inviter or group admin)
        # if not (invitation_db.inviter_user_id == revoker_user_id or await self._is_user_group_admin(revoker_user_id, invitation_db.group_id)):
        #     raise PermissionError("User not authorized to revoke this invitation.")


        if invitation_db.status != "pending":
            logger.warning(f"Invitation ID '{invitation_id}' is not pending (status: {invitation_db.status}). Cannot revoke.")
            return False

        if invitation_db.expires_at < datetime.now(timezone.utc): # Should be caught by status check if cleanup runs
            logger.warning(f"Invitation ID '{invitation_id}' has already expired. Marking as expired if not already.")
            if invitation_db.status != "expired":
                invitation_db.status = "expired"
                self.db_session.add(invitation_db)
                await self.commit()
            return False

        invitation_db.status = "revoked"
        invitation_db.responded_at = datetime.now(timezone.utc)
        self.db_session.add(invitation_db)
        await self.commit()
        logger.info(f"Invitation ID '{invitation_id}' successfully revoked by user ID '{revoker_user_id}'.")
        return True


    async def list_pending_invitations_for_group(self, group_id: UUID, skip: int = 0, limit: int = 100) -> List[GroupInvitationResponse]:
        logger.debug(f"Listing pending invitations for group ID: {group_id}, skip={skip}, limit={limit}")

        stmt = select(GroupInvitation).options(
            selectinload(GroupInvitation.inviter).options(selectinload(User.user_type)), # Load inviter and their type
            selectinload(GroupInvitation.invited_user).options(selectinload(User.user_type)), # Load invited user (if exists) and their type
            selectinload(GroupInvitation.role_to_assign)
        ).where(
            GroupInvitation.group_id == group_id,
            GroupInvitation.status == "pending",
            GroupInvitation.expires_at > datetime.now(timezone.utc)
        ).order_by(GroupInvitation.created_at.desc()).offset(skip).limit(limit)

        invitations_db = (await self.db_session.execute(stmt)).scalars().all()

        # response_list = [GroupInvitationResponse.model_validate(inv) for inv in invitations_db] # Pydantic v2
        response_list = [GroupInvitationResponse.from_orm(inv) for inv in invitations_db] # Pydantic v1
        logger.info(f"Retrieved {len(response_list)} pending invitations for group ID '{group_id}'.")
        return response_list

    async def cleanup_expired_invitations(self) -> int:
        logger.info("Cleaning up expired group invitations...")
        now = datetime.now(timezone.utc)

        stmt = select(GroupInvitation).where(
            GroupInvitation.status == "pending",
            GroupInvitation.expires_at < now
        )
        expired_invitations_db = (await self.db_session.execute(stmt)).scalars().all()

        if not expired_invitations_db:
            logger.info("No pending invitations found to mark as expired.")
            return 0

        count = 0
        for inv_db in expired_invitations_db:
            inv_db.status = "expired"
            self.db_session.add(inv_db)
            count +=1

        if count > 0:
            await self.commit()
        logger.info(f"Successfully marked {count} pending invitations as expired.")
        return count

logger.info("GroupInvitationService class defined.")
