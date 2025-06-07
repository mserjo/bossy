# backend/app/src/core/permissions.py

"""
This module defines more granular permission checking logic, possibly as FastAPI
dependencies or callable classes/functions. It builds upon the user authentication
provided by `core.dependencies`.
"""

from functools import wraps
from typing import Callable, List, Optional, Any, Coroutine, Type # Added Type for Enum hint
from enum import Enum # Added for require_roles example

from fastapi import Depends, HTTPException, status, Request

# Using placeholder UserModel from core.dependencies for now.
# Replace with actual import: from backend.app.src.models.auth import User as UserModel
from backend.app.src.core.dependencies import get_current_active_user, UserModel # get_current_user_optional would be needed for AllowAll with optional auth

# Using placeholder GroupRole from core.dicts for now.
# Replace with actual import if different: from backend.app.src.core.dicts import GroupRole
from backend.app.src.core.dicts import GroupRole

# Placeholder for actual database session and group membership repository/service
# from backend.app.src.config.database import AsyncSession, get_db
# from backend.app.src.repositories.groups import GroupMembershipRepository # Example

class Permission:
    """Base class for defining a permission."""
    async def has_permission(self, request: Request, user: UserModel, **kwargs: Any) -> bool:
        raise NotImplementedError("Permission check not implemented.")

class IsAuthenticated(Permission):
    """Allows access only to authenticated users."""
    async def has_permission(self, request: Request, user: UserModel, **kwargs: Any) -> bool:
        return user is not None and user.is_active

class IsSuperuser(Permission):
    """Allows access only to superusers."""
    async def has_permission(self, request: Request, user: UserModel, **kwargs: Any) -> bool:
        return user is not None and user.is_active and hasattr(user, 'is_superuser') and user.is_superuser

class IsGroupAdmin(Permission):
    """
    Allows access only to users who are admins of a specific group.
    This permission requires `group_id` to be passed to the `PermissionDependency`.
    """
    async def has_permission(self, request: Request, user: UserModel, **kwargs: Any) -> bool:
        if not (user and user.is_active):
            return False

        group_id = kwargs.get("group_id")
        if group_id is None:
            # This indicates a configuration error in how the permission is used.
            # Log this error appropriately in a real application.
            # print("Error: group_id not provided for IsGroupAdmin permission check.")
            return False

        # Placeholder logic for checking group admin status.
        # In a real application, this would involve a database query:
        # async with get_db() as db_session:
        #     membership_repo = GroupMembershipRepository(db_session)
        #     membership = await membership_repo.get_by_user_and_group(user_id=user.id, group_id=group_id)
        #     return membership is not None and membership.role == GroupRole.ADMIN

        # For placeholder purposes:
        # If user is a superuser, grant admin access to any group for testing.
        if hasattr(user, 'is_superuser') and user.is_superuser:
            return True
        # Simulate user 1 being admin of group 1, user 2 admin of group 2 etc.
        # This is highly simplified and for demonstration only.
        if hasattr(user, 'id') and user.id == group_id:
            # print(f"User {user.id} is considered admin of group {group_id} (placeholder logic)")
            return True

        # print(f"User {user.id} is NOT admin of group {group_id} (placeholder logic)")
        return False

class AllowAll(Permission):
    """Allows access to any user, including anonymous ones (if no auth is enforced prior)."""
    async def has_permission(self, request: Request, user: Optional[UserModel], **kwargs: Any) -> bool:
        # If using get_current_active_user, user will not be None unless that dependency is changed.
        # If an optional authentication (get_current_user_optional) was used, then user could be None.
        return True

# --- Permission Dependency Factory ---

def PermissionDependency(
    permissions: List[Permission],
    require_all: bool = True,
    allow_superuser_override: bool = True
) -> Callable[..., Coroutine[Any, Any, UserModel]]:
    """
    FastAPI dependency that checks if the current user has the required permissions.

    Args:
        permissions (List[Permission]): A list of permission instances to check.
        require_all (bool): If True, all permissions in the list must be met.
                            If False, at least one permission must be met.
        allow_superuser_override (bool): If True, a superuser bypasses all other permission checks.

    Returns:
        A FastAPI dependency callable.
    """
    async def _permission_checker(
        request: Request,
        user: UserModel = Depends(get_current_active_user) # Ensures user is active
        # If you need to support optional authentication for some permissions (e.g. AllowAll with specific checks):
        # user: Optional[UserModel] = Depends(get_current_user_optional) # Needs get_current_user_optional
    ) -> UserModel:
        # get_current_active_user already raises 401 if not authenticated or inactive
        # So, user object here should always be an active UserModel instance.

        # Superuser override
        if allow_superuser_override and hasattr(user, 'is_superuser') and user.is_superuser:
            return user

        # Extract path parameters for permissions that might need them (e.g., group_id)
        path_params = request.path_params

        results = []
        for perm_instance in permissions:
            # Pass path_params or specific relevant parts to has_permission
            # For IsGroupAdmin, it expects 'group_id' in kwargs
            kwargs_for_perm = {}
            if isinstance(perm_instance, IsGroupAdmin) and 'group_id' in path_params:
                try:
                    kwargs_for_perm['group_id'] = int(path_params['group_id'])
                except ValueError:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid group_id format in path.")

            # For AllowAll, user might be None if an optional auth dependency was used.
            # However, with get_current_active_user, user is guaranteed.
            # If AllowAll is the only permission, this check is somewhat redundant here
            # but kept for logical completeness of the Permission class structure.
            has_perm = await perm_instance.has_permission(request, user, **kwargs_for_perm)
            results.append(has_perm)

        if not results: # Should not happen if permissions list is not empty
             raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No permissions were checked."
            )

        if require_all and not all(results):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have sufficient permissions to perform this action."
            )
        if not require_all and not any(results):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have any of the required permissions for this action."
            )
        return user
    return _permission_checker

# Example of a simpler role-based permission decorator (not a class-based Permission)
# This is an alternative or complementary approach.

def require_roles(allowed_roles: List[Union[str, Enum]]): # Allow Enum members too
    """
    Decorator to restrict access to users with specific roles.
    Assumes user object has a `roles` attribute (e.g., List[str] or List[UserRoleEnum]).
    This is a conceptual example; for FastAPI, it's better to make this a dependency.
    """
    def decorator(func: Callable[..., Any]):
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any):
            # This is a simplified example. In FastAPI, 'user' would come from a Depends()
            user: Optional[UserModel] = kwargs.get('user') # Or 'current_user' depending on arg name

            if not user or not hasattr(user, 'roles'): # Check if user has 'roles' attribute
                # print("User object or user.roles not found for @require_roles check.")
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User roles not available or user not provided.")

            user_roles = getattr(user, 'roles')
            if not isinstance(user_roles, list):
                # print(f"user.roles is not a list: {user_roles}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User roles attribute is misconfigured.")

            # Convert allowed_roles to their values if they are Enums
            allowed_role_values = [role.value if isinstance(role, Enum) else role for role in allowed_roles]

            # Check if any of the user's roles (also converting if they are Enums) match allowed roles
            user_has_role = False
            for user_role in user_roles:
                user_role_value = user_role.value if isinstance(user_role, Enum) else user_role
                if user_role_value in allowed_role_values:
                    user_has_role = True
                    break

            if not user_has_role:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Requires one of roles: {allowed_role_values}")
            return await func(*args, **kwargs)
        return wrapper
    return decorator

if __name__ == "__main__":
    print("--- Core Permissions ---")
    print("This module defines permission classes and a dependency factory for FastAPI.")

    # Mock user objects for demonstration
    active_user = UserModel(id=1, email="user@example.com", is_active=True)
    setattr(active_user, 'roles', ["user"]) # Add roles for require_roles demo

    inactive_user = UserModel(id=2, email="inactive@example.com", is_active=False)
    setattr(inactive_user, 'roles', ["user"])


    superuser_model = UserModel(id=3, email="super@example.com", is_active=True, is_superuser=True)
    setattr(superuser_model, 'roles', ["superuser", "user", "admin"])


    # User for group admin testing; placeholder: user ID 4 is admin of group 4
    admin_group1_user = UserModel(id=4, email="admin_g1@example.com", is_active=True)
    setattr(admin_group1_user, 'roles', ["group_admin", "user"])


    # Mock request object
    mock_request_group1 = Request(scope={"type": "http", "method": "GET", "path": "/groups/1/items", "path_params": {"group_id": "1"}})
    mock_request_group4 = Request(scope={"type": "http", "method": "GET", "path": "/groups/4/items", "path_params": {"group_id": "4"}})


    async def run_permission_check(perm_class, user, request_obj, **perm_kwargs):
        perm = perm_class()
        try:
            # Simulate how PermissionDependency would pass kwargs from path_params
            # For IsGroupAdmin, group_id comes from request.path_params if not in perm_kwargs
            final_kwargs = perm_kwargs.copy()
            if isinstance(perm, IsGroupAdmin) and 'group_id' not in final_kwargs and 'group_id' in request_obj.path_params:
                 final_kwargs['group_id'] = int(request_obj.path_params['group_id'])

            has_perm = await perm.has_permission(request_obj, user, **final_kwargs)
            print(f"User '{user.email if user else 'Anonymous'}' check for {perm.__class__.__name__} (path: {request_obj.url.path}, kwargs: {final_kwargs}): {'GRANTED' if has_perm else 'DENIED'}")
        except Exception as e:
            print(f"Error checking {perm.__class__.__name__} for '{user.email if user else 'Anonymous'}': {e}")

    # For require_roles decorator test
    @require_roles(["admin", GroupRole.ADMIN]) # GroupRole.ADMIN is "admin"
    async def decorated_func_for_admin(user: UserModel): # Changed arg name to 'user'
        print(f"User '{user.email}' accessed admin-only decorated function.")

    @require_roles(["user"])
    async def decorated_func_for_user(user: UserModel):
        print(f"User '{user.email}' accessed user-only decorated function.")

    import asyncio

    async def main():
        print("\n--- Testing Permission Classes ---")
        print("\nTesting IsAuthenticated:")
        await run_permission_check(IsAuthenticated, active_user, mock_request_group1)
        await run_permission_check(IsAuthenticated, inactive_user, mock_request_group1) # Denied (inactive)
        # await run_permission_check(IsAuthenticated, None, mock_request_group1) # Would fail in PermissionDependency due to get_current_active_user

        print("\nTesting IsSuperuser:")
        await run_permission_check(IsSuperuser, active_user, mock_request_group1) # Denied
        await run_permission_check(IsSuperuser, superuser_model, mock_request_group1) # Granted

        print("\nTesting IsGroupAdmin (placeholder logic):")
        # User ID 4 is admin of group 4 by placeholder logic
        await run_permission_check(IsGroupAdmin, admin_group1_user, mock_request_group4) # Granted (user 4, group 4)
        await run_permission_check(IsGroupAdmin, admin_group1_user, mock_request_group1) # Denied (user 4, group 1)
        await run_permission_check(IsGroupAdmin, superuser_model, mock_request_group1, group_id=99) # Superuser granted for group 99

        print("\nTesting AllowAll:")
        await run_permission_check(AllowAll, active_user, mock_request_group1)
        # await run_permission_check(AllowAll, None, mock_request_group1) # If using optional auth

        print("\n--- Testing @require_roles decorator (conceptual) ---")
        print("Note: This decorator is a simplified example for direct calls.")
        try:
            await decorated_func_for_admin(user=superuser_model) # Superuser has 'admin' role
        except HTTPException as e:
            print(f"Admin func access for superuser: {e.detail}")

        try:
            await decorated_func_for_admin(user=active_user) # Active_user does not have 'admin' role
        except HTTPException as e:
            print(f"Admin func access for active_user: {e.detail}")

        try:
            await decorated_func_for_user(user=active_user) # Active_user has 'user' role
        except HTTPException as e:
            print(f"User func access for active_user: {e.detail}")

        user_without_roles = UserModel(id=5, email="noroles@example.com", is_active=True)
        try:
            await decorated_func_for_user(user=user_without_roles)
        except HTTPException as e:
            print(f"User func access for user_without_roles: {e.detail}")


        print("\nNote: PermissionDependency factory would be used in FastAPI endpoint dependencies.")
        print("Example: `Depends(PermissionDependency([IsAuthenticated(), IsGroupAdmin()]))`")

    asyncio.run(main())
