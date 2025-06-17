# backend/tests/integration/test_api/test_v1/test_dependencies_integration.py
import pytest
from typing import AsyncGenerator, Dict

from fastapi import FastAPI, Depends, HTTPException, status, Path
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

# Models and Schemas needed for setup
from backend.app.src.models.auth.user import User as UserModel
from backend.app.src.models.groups.group import Group as GroupModel
from backend.app.src.models.groups.membership import GroupMembership as GroupMembershipModel
from backend.app.src.models.dictionaries.group_types import GroupType as GroupTypeModel # Needed for Group creation
from backend.app.src.core.dicts import GroupRole
from backend.app.src.schemas.auth.user import UserResponseSchema # For endpoint response

# Core components to test/use
from backend.app.src.core.dependencies import get_current_group_admin, get_current_active_user, get_db
from backend.app.src.config.security import create_access_token # To generate tokens
from backend.app.src.config.database import Base # For test DB setup

# Test Database Setup
from sqlalchemy.ext.asyncio import create_async_engine
# from sqlalchemy.orm import sessionmaker # sessionmaker is already imported from sqlalchemy.ext.asyncio for AsyncSession

# Use a separate in-memory SQLite for integration tests for speed and isolation
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False) # echo=False for cleaner test output
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=test_engine, class_=AsyncSession
)

async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session

# Test FastAPI app
app = FastAPI()

# This is a placeholder for the actual UserResponseSchema which might have more fields
# For testing, we only care about 'username' as asserted.
# If UserResponseSchema has from_attributes = True, it can map from UserModel.
@app.get("/groups/{group_id}/protected-admin-route", response_model=UserResponseSchema)
async def protected_group_admin_route(
    group_id: int = Path(..., description="The ID of the group to access"),
    current_admin: UserModel = Depends(get_current_group_admin) # The dependency to test
):
    return current_admin

# Apply the override for get_db for this test app
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="function", autouse=True) # autouse=True to apply to all tests in this module
async def setup_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def db_session_for_setup() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session

@pytest.fixture
async def test_user_regular(db_session_for_setup: AsyncSession) -> UserModel:
    user = UserModel(username="testuser_reg", email="reg@example.com", hashed_password="hashed_password", is_active=True, is_superuser=False, name="Test User Reg")
    db_session_for_setup.add(user)
    await db_session_for_setup.commit()
    await db_session_for_setup.refresh(user)
    return user

@pytest.fixture
async def test_user_group_admin(db_session_for_setup: AsyncSession) -> UserModel:
    user = UserModel(username="testuser_admin", email="admin@example.com", hashed_password="hashed_password", is_active=True, is_superuser=False, name="Test User Admin")
    db_session_for_setup.add(user)
    await db_session_for_setup.commit()
    await db_session_for_setup.refresh(user)
    return user

@pytest.fixture
async def test_user_superuser(db_session_for_setup: AsyncSession) -> UserModel:
    user = UserModel(username="testuser_super", email="super@example.com", hashed_password="hashed_password", is_active=True, is_superuser=True, name="Test User Super")
    db_session_for_setup.add(user)
    await db_session_for_setup.commit()
    await db_session_for_setup.refresh(user)
    return user

@pytest.fixture
async def default_group_type(db_session_for_setup: AsyncSession) -> GroupTypeModel:
    # Create a default group type if your Group model requires group_type_id
    group_type = GroupTypeModel(code="DEFAULT", name="Default Type")
    db_session_for_setup.add(group_type)
    await db_session_for_setup.commit()
    await db_session_for_setup.refresh(group_type)
    return group_type

@pytest.fixture
async def test_group(db_session_for_setup: AsyncSession, test_user_regular: UserModel, default_group_type: GroupTypeModel) -> GroupModel:
    group = GroupModel(name="Test Group", created_by_user_id=test_user_regular.id, group_type_id=default_group_type.id)
    db_session_for_setup.add(group)
    await db_session_for_setup.commit()
    await db_session_for_setup.refresh(group)
    return group

@pytest.fixture
async def group_admin_membership(db_session_for_setup: AsyncSession, test_group: GroupModel, test_user_group_admin: UserModel) -> GroupMembershipModel:
    membership = GroupMembershipModel(user_id=test_user_group_admin.id, group_id=test_group.id, role=GroupRole.ADMIN, is_active=True)
    db_session_for_setup.add(membership)
    await db_session_for_setup.commit()
    await db_session_for_setup.refresh(membership)
    return membership

@pytest.fixture
async def group_member_membership(db_session_for_setup: AsyncSession, test_group: GroupModel, test_user_regular: UserModel) -> GroupMembershipModel:
    membership = GroupMembershipModel(user_id=test_user_regular.id, group_id=test_group.id, role=GroupRole.MEMBER, is_active=True)
    db_session_for_setup.add(membership)
    await db_session_for_setup.commit()
    await db_session_for_setup.refresh(membership)
    return membership


def get_auth_headers(user_id: int, username: str) -> Dict[str, str]:
    token = create_access_token(data={"sub": username, "user_id": user_id, "type": "access"})
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_group_admin_can_access(
    setup_database, test_user_group_admin: UserModel, test_group: GroupModel, group_admin_membership: GroupMembershipModel
):
    headers = get_auth_headers(user_id=test_user_group_admin.id, username=test_user_group_admin.username)

    # For this integration test, we are testing get_current_group_admin.
    # It relies on get_current_active_user, which relies on get_current_user.
    # The get_current_user in dependencies.py has placeholder logic to retrieve users.
    # To make it work with our test DB users, we patch get_current_user.
    async def mock_get_current_user_direct_db_fetch(*args, **kwargs):
        # The real get_current_user is complex; for this test, we simplify its effect.
        # It should effectively return the user based on token.
        # Here, we directly return the user that the token *would* represent.
        # This bypasses the token decoding and placeholder user lookup in the original get_current_user.
        # This approach makes the test focus more on get_current_group_admin's DB logic.
        nonlocal test_user_group_admin # Capture from outer scope
        return test_user_group_admin

    app.dependency_overrides[get_current_active_user] = mock_get_current_user_direct_db_fetch

    response = client.get(f"/groups/{test_group.id}/protected-admin-route", headers=headers)

    assert response.status_code == 200
    assert response.json()["username"] == test_user_group_admin.username

    app.dependency_overrides.pop(get_current_active_user) # Clean up override

@pytest.mark.asyncio
async def test_superuser_can_access_group_admin_route(
    setup_database, test_user_superuser: UserModel, test_group: GroupModel
):
    headers = get_auth_headers(user_id=test_user_superuser.id, username=test_user_superuser.username)

    async def mock_get_current_user_direct_db_fetch_superuser():
        nonlocal test_user_superuser
        return test_user_superuser
    app.dependency_overrides[get_current_active_user] = mock_get_current_user_direct_db_fetch_superuser

    response = client.get(f"/groups/{test_group.id}/protected-admin-route", headers=headers)
    assert response.status_code == 200
    assert response.json()["username"] == test_user_superuser.username

    app.dependency_overrides.pop(get_current_active_user)


@pytest.mark.asyncio
async def test_regular_member_cannot_access_group_admin_route(
    setup_database, test_user_regular: UserModel, test_group: GroupModel, group_member_membership: GroupMembershipModel
):
    headers = get_auth_headers(user_id=test_user_regular.id, username=test_user_regular.username)

    async def mock_get_current_user_direct_db_fetch_regular():
        nonlocal test_user_regular
        return test_user_regular
    app.dependency_overrides[get_current_active_user] = mock_get_current_user_direct_db_fetch_regular

    response = client.get(f"/groups/{test_group.id}/protected-admin-route", headers=headers)
    assert response.status_code == 403
    # Assuming the i18n placeholder _() simply returns the string for now
    assert "Ви не є адміністратором цієї групи." in response.json()["detail"]

    app.dependency_overrides.pop(get_current_active_user)

@pytest.mark.asyncio
async def test_non_member_cannot_access_group_admin_route(
    setup_database, test_user_regular: UserModel,
    db_session_for_setup: AsyncSession, default_group_type: GroupTypeModel
):
    other_group = GroupModel(name="Other Group", created_by_user_id=test_user_regular.id, group_type_id=default_group_type.id)
    db_session_for_setup.add(other_group)
    await db_session_for_setup.commit()
    await db_session_for_setup.refresh(other_group)

    headers = get_auth_headers(user_id=test_user_regular.id, username=test_user_regular.username)

    async def mock_get_current_user_direct_db_fetch_non_member():
        nonlocal test_user_regular
        return test_user_regular
    app.dependency_overrides[get_current_active_user] = mock_get_current_user_direct_db_fetch_non_member

    response = client.get(f"/groups/{other_group.id}/protected-admin-route", headers=headers)
    assert response.status_code == 403
    assert "Ви не є адміністратором цієї групи." in response.json()["detail"]

    app.dependency_overrides.pop(get_current_active_user)

```
