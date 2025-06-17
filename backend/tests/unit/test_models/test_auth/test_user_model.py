# backend/tests/unit/test_models/test_auth/test_user_model.py
import unittest
from unittest.mock import MagicMock, PropertyMock

from backend.app.src.models.auth.user import User
from backend.app.src.models.files.avatar import UserAvatar
from backend.app.src.models.files.file import FileRecord

# Mock settings directly in the test module for simplicity
# In a larger setup, this might come from a conftest.py or a test utility
mock_settings = MagicMock()
mock_settings.SERVER_HOST = "http://localhost:8000"
mock_settings.STATIC_URL = "/static/"

class TestUserModelAvatarUrl(unittest.TestCase):

    def setUp(self):
        # Patch the settings module used by the User model's avatar_url property
        # This assumes the User model imports settings like:
        # from backend.app.src.config import settings as app_settings
        # If it's a direct import, patching might be more complex or require module-level patching.
        # For this example, we'll mock it as if it's accessible via a known path.
        # A simpler way for unit tests is often to inject dependencies or make them configurable.
        # Here, we assume 'backend.app.src.models.auth.user.settings' is the path to settings
        # as seen by the user.py module.

        # Simpler approach: mock the settings object that the property will use.
        # This requires that the User.avatar_url property can access our mock_settings.
        # This can be tricky if settings is imported directly at the module level of user.py.
        # For this test, we'll assume we can control what 'settings' the property sees.
        # One way is to ensure the User model gets 'settings' injected or uses a global
        # that can be patched. If it's a direct 'from backend.app.src.config import settings',
        # we'd need to patch 'backend.app.src.models.auth.user.settings'.

        # Let's assume direct patching for this subtask.
        # This requires the test runner environment to handle such patches correctly.
        self.settings_patcher = unittest.mock.patch('backend.app.src.models.auth.user.settings', mock_settings)
        self.mocked_settings = self.settings_patcher.start()

        self.user = User()
        self.user.id = 1
        self.user.username = "testuser"

        # Important: The User model's avatar_url property accesses settings via:
        # from backend.app.src.config import settings
        # So, we MUST patch 'backend.app.src.models.auth.user.settings'

    def tearDown(self):
        self.settings_patcher.stop()

    def test_avatar_url_no_avatar(self):
        self.user.avatar = None
        self.assertIsNone(self.user.avatar_url)

    def test_avatar_url_inactive_avatar(self):
        mock_avatar = MagicMock(spec=UserAvatar)
        mock_avatar.is_active = False
        mock_avatar.file_record = None # Does not matter here
        self.user.avatar = mock_avatar
        self.assertIsNone(self.user.avatar_url)

    def test_avatar_url_no_file_record(self):
        mock_avatar = MagicMock(spec=UserAvatar)
        mock_avatar.is_active = True
        mock_avatar.file_record = None
        self.user.avatar = mock_avatar
        self.assertIsNone(self.user.avatar_url)

    def test_avatar_url_no_file_path(self):
        mock_file_record = MagicMock(spec=FileRecord)
        mock_file_record.file_path = None

        mock_avatar = MagicMock(spec=UserAvatar)
        mock_avatar.is_active = True
        mock_avatar.file_record = mock_file_record
        self.user.avatar = mock_avatar
        self.assertIsNone(self.user.avatar_url)

    def test_avatar_url_with_relative_file_path(self):
        mock_file_record = MagicMock(spec=FileRecord)
        mock_file_record.file_path = "avatars/user1/image.png"

        mock_avatar = MagicMock(spec=UserAvatar)
        mock_avatar.is_active = True
        mock_avatar.file_record = mock_file_record
        self.user.avatar = mock_avatar

        expected_url = "http://localhost:8000/static/avatars/user1/image.png"
        self.assertEqual(self.user.avatar_url, expected_url)

    def test_avatar_url_with_absolute_file_path(self):
        mock_file_record = MagicMock(spec=FileRecord)
        mock_file_record.file_path = "/media/avatars/user1/image.png"

        mock_avatar = MagicMock(spec=UserAvatar)
        mock_avatar.is_active = True
        mock_avatar.file_record = mock_file_record
        self.user.avatar = mock_avatar

        expected_url = "http://localhost:8000/media/avatars/user1/image.png"
        self.assertEqual(self.user.avatar_url, expected_url)

    def test_avatar_url_base_url_ends_with_slash(self):
        self.mocked_settings.SERVER_HOST = "http://localhost:8000/" # Base URL ends with slash
        self.mocked_settings.STATIC_URL = "/static/"

        mock_file_record = MagicMock(spec=FileRecord)
        mock_file_record.file_path = "avatars/user1/image.png" # Relative path

        mock_avatar = MagicMock(spec=UserAvatar)
        mock_avatar.is_active = True
        mock_avatar.file_record = mock_file_record
        self.user.avatar = mock_avatar

        expected_url = "http://localhost:8000/static/avatars/user1/image.png"
        self.assertEqual(self.user.avatar_url, expected_url)

    def test_avatar_url_base_url_ends_with_slash_and_path_starts_with_slash(self):
        self.mocked_settings.SERVER_HOST = "http://localhost:8000/" # Base URL ends with slash

        mock_file_record = MagicMock(spec=FileRecord)
        mock_file_record.file_path = "/media/avatars/user1/image.png" # Absolute path

        mock_avatar = MagicMock(spec=UserAvatar)
        mock_avatar.is_active = True
        mock_avatar.file_record = mock_file_record
        self.user.avatar = mock_avatar

        # effective_base_url becomes "http://localhost:8000" (slash stripped)
        # then file_path is appended.
        expected_url = "http://localhost:8000/media/avatars/user1/image.png"
        self.assertEqual(self.user.avatar_url, expected_url)

    def test_avatar_url_static_url_no_trailing_slash(self):
        self.mocked_settings.SERVER_HOST = "http://localhost:8000"
        self.mocked_settings.STATIC_URL = "/static" # No trailing slash

        mock_file_record = MagicMock(spec=FileRecord)
        mock_file_record.file_path = "avatars/user1/image.png" # Relative path

        mock_avatar = MagicMock(spec=UserAvatar)
        mock_avatar.is_active = True
        mock_avatar.file_record = mock_file_record
        self.user.avatar = mock_avatar

        # static_url_prefix becomes "/static/"
        expected_url = "http://localhost:8000/static/avatars/user1/image.png"
        self.assertEqual(self.user.avatar_url, expected_url)

if __name__ == '__main__':
    unittest.main()
