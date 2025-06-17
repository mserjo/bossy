# backend/tests/integration/test_api/test_v1/test_i18n_integration.py
import pytest
from typing import AsyncGenerator, Dict, Optional

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.src.models.auth.user import User as UserModel
from backend.app.src.schemas.auth.user import UserResponseSchema
from backend.app.src.core.dependencies import get_current_active_user, get_db
from backend.app.src.config.security import create_access_token
from backend.app.src.config.database import Base
from backend.app.src.core.middleware.i18n_middleware import LanguageMiddleware # Import the middleware

# Test Database (in-memory SQLite)
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocalTestI18n = sessionmaker(
    autocommit=False, autoflush=False, bind=test_engine, class_=AsyncSession
)

async def override_get_db_test_i18n() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocalTestI18n() as session:
        yield session

# Test FastAPI app for i18n
i18n_test_app = FastAPI(title="I18nTestApp")

# Apply LanguageMiddleware
i18n_test_app.add_middleware(LanguageMiddleware)

# Override get_db dependency for this app
i18n_test_app.dependency_overrides[get_db] = override_get_db_test_i18n


# A protected route that uses a dependency that can raise a translated error
@i18n_test_app.get("/i18n/protected-route-inactive-user", response_model=UserResponseSchema)
async def protected_route_inactive_user(
    current_user: UserModel = Depends(get_current_active_user)
):
    return current_user # Should not be reached if user is inactive

# Another route for a different error
@i18n_test_app.get("/i18n/protected-route-not-superuser")
async def protected_route_not_superuser(
    current_user: UserModel = Depends(get_current_active_user) # First active
    # Then, imagine another dependency that checks for superuser and raises:
    # current_superuser: UserModel = Depends(get_current_superuser) # This would be more direct
):
    # Simulate a check that would be in get_current_superuser
    if not current_user.is_superuser:
        # We need to import _ from i18n to use it here for the test,
        # or rely on the fact that HTTPException in get_current_superuser is already translated
        # The key "dependencies.auth.not_superuser" is what get_current_superuser uses.
        # For this test, we will directly raise an exception with a known key
        # if the dependency itself is not directly used in this test route.
        # However, get_current_superuser is already i18n enabled.
        # Let's make a route that uses it.

    # This route is not ideal for testing get_current_superuser directly unless we add it
    # For now, let's focus on the inactive_user error from get_current_active_user
    return {"message": "This route is for other tests if needed."}


# TestClient for the i18n_test_app
client_i18n = TestClient(i18n_test_app)

@pytest.fixture(scope="function")
async def setup_i18n_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def db_session_for_i18n_setup() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocalTestI18n() as session:
        yield session

@pytest.fixture
async def inactive_test_user(db_session_for_i18n_setup: AsyncSession) -> UserModel:
    user = UserModel(
        username="inactiveuser",
        email="inactive@example.com",
        hashed_password="hashed_password",
        is_active=False, # Key for this test
        is_superuser=False,
        name="Inactive User"
    )
    db_session_for_i18n_setup.add(user)
    await db_session_for_i18n_setup.commit()
    await db_session_for_i18n_setup.refresh(user)
    return user

def get_auth_headers_for_user(user: UserModel) -> Dict[str, str]:
    # The get_current_user dependency (placeholder part) needs to resolve this.
    # We need to ensure the token's 'sub' or 'user_id' matches what get_current_user expects.
    # The placeholder logic in dependencies.py's get_current_user is:
    # if user_identifier == "testuser@example.com" or user_identifier == "123": current_user = UserModel(...)
    # This will NOT work with our dynamically created inactive_test_user.
    #
    # SOLUTION: The `get_current_user` dependency in `core/dependencies.py` was planned
    # to be updated to fetch users from the DB. If that change was made and merged,
    # then this token generation should work by creating a token that `decode_token` can parse
    # and whose `sub` or `user_id` claim can be used by `get_current_user` to fetch the actual user
    # from the test DB via the overridden `get_db` session.
    #
    # Assuming get_current_user uses session.get(UserModel, token_data.user_id)
    # or similar that hits the test DB.
    token = create_access_token(data={"sub": user.username, "user_id": user.id, "type": "access"})
    return {"Authorization": f"Bearer {token}"}

# Expected messages from previously created/viewed messages.json files
# These should match the keys "dependencies.auth.inactive_user"
EXPECTED_MSG_UK = "Неактивний користувач."
EXPECTED_MSG_EN = "Inactive user."

@pytest.mark.asyncio
async def test_inactive_user_default_language(
    setup_i18n_database, inactive_test_user: UserModel
):
    """Test that an inactive user error is returned in the default language (uk)."""
    # To make this test work, the placeholder user loading in `get_current_user`
    # needs to be replaced with actual DB lookup using the session.
    # For now, we will mock/override get_current_user to return our inactive_test_user directly.
    async def mock_get_current_user_returns_inactive():
        return inactive_test_user

    # get_current_active_user calls get_current_user.
    # So overriding get_current_user is what we need.
    # However, the dependency is get_current_active_user.
    # If get_current_user is not using the DB, we have to mock one level up.
    i18n_test_app.dependency_overrides[get_current_active_user] = lambda: inactive_test_user


    headers = get_auth_headers_for_user(inactive_test_user)
    # No Accept-Language header, should default to 'uk'
    response = client_i18n.get("/i18n/protected-route-inactive-user", headers=headers)

    assert response.status_code == 403
    assert response.json()["detail"] == EXPECTED_MSG_UK
    assert response.headers.get("Content-Language") == "uk"

    i18n_test_app.dependency_overrides = {} # Clean up
    i18n_test_app.dependency_overrides[get_db] = override_get_db_test_i18n


@pytest.mark.asyncio
async def test_inactive_user_uk_language(
    setup_i18n_database, inactive_test_user: UserModel
):
    """Test that an inactive user error is returned in Ukrainian when requested."""
    i18n_test_app.dependency_overrides[get_current_active_user] = lambda: inactive_test_user
    headers = get_auth_headers_for_user(inactive_test_user)
    headers["Accept-Language"] = "uk"

    response = client_i18n.get("/i18n/protected-route-inactive-user", headers=headers)

    assert response.status_code == 403
    assert response.json()["detail"] == EXPECTED_MSG_UK
    assert response.headers.get("Content-Language") == "uk"

    i18n_test_app.dependency_overrides = {}
    i18n_test_app.dependency_overrides[get_db] = override_get_db_test_i18n

@pytest.mark.asyncio
async def test_inactive_user_en_language(
    setup_i18n_database, inactive_test_user: UserModel
):
    """Test that an inactive user error is returned in English when requested."""
    i18n_test_app.dependency_overrides[get_current_active_user] = lambda: inactive_test_user
    headers = get_auth_headers_for_user(inactive_test_user)
    headers["Accept-Language"] = "en"

    response = client_i18n.get("/i18n/protected-route-inactive-user", headers=headers)

    assert response.status_code == 403
    assert response.json()["detail"] == EXPECTED_MSG_EN
    assert response.headers.get("Content-Language") == "en"

    i18n_test_app.dependency_overrides = {}
    i18n_test_app.dependency_overrides[get_db] = override_get_db_test_i18n

@pytest.mark.asyncio
async def test_inactive_user_fallback_language(
    setup_i18n_database, inactive_test_user: UserModel
):
    """Test language fallback (e.g., fr -> en)."""
    i18n_test_app.dependency_overrides[get_current_active_user] = lambda: inactive_test_user
    headers = get_auth_headers_for_user(inactive_test_user)
    headers["Accept-Language"] = "fr, en;q=0.9" # French not supported, English is

    response = client_i18n.get("/i18n/protected-route-inactive-user", headers=headers)

    assert response.status_code == 403
    assert response.json()["detail"] == EXPECTED_MSG_EN # Fallback to English
    assert response.headers.get("Content-Language") == "en"

    i18n_test_app.dependency_overrides = {}
    i18n_test_app.dependency_overrides[get_db] = override_get_db_test_i18n
