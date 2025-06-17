# backend/tests/unit/test_services/test_auth/test_user_service.py
import pytest # Using pytest for async testing and fixtures
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession # Added for type hinting mock_db_session

from backend.app.src.services.auth.user import UserService
from backend.app.src.schemas.auth.user import UserCreateSchema
from backend.app.src.models.auth.user import User
from backend.app.src.models.dictionaries.user_types import UserType
from backend.app.src.models.dictionaries.user_roles import UserRole
from backend.app.src.models.dictionaries.statuses import Status
from backend.app.src.core.security import get_password_hash # For password comparison if needed, or mock it

# Mock settings if your service directly uses it, though UserService typically doesn't for create_user logic.
# mock_settings = MagicMock()
# mock_settings.DEBUG = False # Example

@pytest.fixture
def mock_db_session():
    session = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    return session

@pytest.fixture
def user_service(mock_db_session: AsyncMock) -> UserService:
    return UserService(db_session=mock_db_session)

@pytest.fixture
def user_create_schema_data() -> dict:
    return {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "password123",
        "name": "New User",
        # user_type_code is provided by the service method's default if not in schema
        # system_role_code will default to "USER" in service if None or not in schema
    }

@pytest.mark.asyncio
async def test_create_user_with_valid_state_code(
    user_service: UserService,
    mock_db_session: AsyncMock,
    user_create_schema_data: dict
):
    # user_type_code is passed as method argument to create_user in this test
    user_create_data_dict = {**user_create_schema_data, "state_code": "ACTIVE_STATUS"}
    user_create_data = UserCreateSchema(**user_create_data_dict)


    # Mock DB responses
    mock_user_type = UserType(id=1, code="REGULAR_USER", name="Regular")
    mock_system_role = UserRole(id=1, code="USER", name="User") # Default role
    mock_active_status = Status(id=10, code="ACTIVE_STATUS", name="Active")

    # Configure side_effects for session.execute
    # Order of execution:
    # 1. _check_existing_user (username)
    # 2. _check_existing_user (email)
    # 3. UserType fetch (for user_type_code passed to method)
    # 4. Status fetch for state_code
    # 5. UserRole for default system_role_code ("USER")
    execute_results = [
        MagicMock(scalar_one_or_none=MagicMock(return_value=None)), # username check
        MagicMock(scalar_one_or_none=MagicMock(return_value=None)), # email check
        MagicMock(scalar_one_or_none=MagicMock(return_value=mock_user_type)), # UserType fetch
        MagicMock(scalar_one_or_none=MagicMock(return_value=mock_active_status)), # Status fetch for state_code
        MagicMock(scalar_one_or_none=MagicMock(return_value=mock_system_role))  # UserRole for default system_role
    ]
    mock_db_session.execute.side_effect = execute_results

    # Mock get_password_hash
    with patch('backend.app.src.services.auth.user.get_password_hash', return_value="hashed_password") as mock_hash:
        # Pass user_type_code explicitly as per service method signature
        created_user_response = await user_service.create_user(
            user_create_data=user_create_data,
            user_type_code="REGULAR_USER"
            # role_codes and is_superuser_creation use defaults
        )

    # Assertions
    mock_db_session.add.assert_called_once()
    added_user_instance = mock_db_session.add.call_args[0][0]
    assert isinstance(added_user_instance, User)
    assert added_user_instance.username == user_create_data.username
    assert added_user_instance.email == user_create_data.email.lower()
    assert added_user_instance.hashed_password == "hashed_password"
    assert added_user_instance.user_type_id == mock_user_type.id
    assert added_user_instance.system_role_id == mock_system_role.id # Check default system role
    assert added_user_instance.state_id == mock_active_status.id # Key assertion for this test

    mock_db_session.commit.assert_awaited_once()
    mock_db_session.refresh.assert_awaited_once_with(
        added_user_instance,
        attribute_names=['roles', 'user_type', 'state', 'system_role', 'avatar']
    )

    assert created_user_response is not None
    assert created_user_response.username == user_create_data.username
    # Further assertions on created_user_response can be added if needed

@pytest.mark.asyncio
async def test_create_user_with_default_pending_verification_state(
    user_service: UserService,
    mock_db_session: AsyncMock,
    user_create_schema_data: dict
):
    # state_code is not provided in schema, service should use "PENDING_VERIFICATION"
    user_create_data = UserCreateSchema(**user_create_schema_data)

    mock_user_type = UserType(id=1, code="REGULAR_USER", name="Regular")
    mock_pending_status = Status(id=11, code="PENDING_VERIFICATION", name="Pending")
    mock_system_role = UserRole(id=1, code="USER", name="User")

    execute_results = [
        MagicMock(scalar_one_or_none=MagicMock(return_value=None)), # username
        MagicMock(scalar_one_or_none=MagicMock(return_value=None)), # email
        MagicMock(scalar_one_or_none=MagicMock(return_value=mock_user_type)), # UserType
        MagicMock(scalar_one_or_none=MagicMock(return_value=mock_pending_status)), # Status for PENDING_VERIFICATION
        MagicMock(scalar_one_or_none=MagicMock(return_value=mock_system_role))  # UserRole for default system_role
    ]
    mock_db_session.execute.side_effect = execute_results

    with patch('backend.app.src.services.auth.user.get_password_hash', return_value="hashed_password"):
        await user_service.create_user(
            user_create_data=user_create_data,
            user_type_code="REGULAR_USER" # Explicitly pass to method
        )

    added_user_instance = mock_db_session.add.call_args[0][0]
    assert added_user_instance.state_id == mock_pending_status.id

@pytest.mark.asyncio
async def test_create_user_with_invalid_state_code(
    user_service: UserService,
    mock_db_session: AsyncMock,
    user_create_schema_data: dict
):
    user_create_data_dict = {**user_create_schema_data, "state_code": "INVALID_STATUS_CODE"}
    user_create_data = UserCreateSchema(**user_create_data_dict)


    mock_user_type = UserType(id=1, code="REGULAR_USER", name="Regular")
    # mock_system_role is not needed here as the error should raise before its query

    execute_results = [
        MagicMock(scalar_one_or_none=MagicMock(return_value=None)), # username
        MagicMock(scalar_one_or_none=MagicMock(return_value=None)), # email
        MagicMock(scalar_one_or_none=MagicMock(return_value=mock_user_type)), # UserType
        MagicMock(scalar_one_or_none=MagicMock(return_value=None)), # Status fetch for INVALID_STATUS_CODE (returns None)
    ]
    mock_db_session.execute.side_effect = execute_results


    with patch('backend.app.src.services.auth.user.get_password_hash', return_value="hashed_password"):
        with pytest.raises(ValueError, match="Статус користувача 'INVALID_STATUS_CODE' не знайдено."):
            await user_service.create_user(
                user_create_data=user_create_data,
                user_type_code="REGULAR_USER" # Explicitly pass to method
            )

    mock_db_session.add.assert_not_called()
    mock_db_session.commit.assert_not_awaited()

```
