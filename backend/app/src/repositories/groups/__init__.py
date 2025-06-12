# backend/app/src/repositories/groups/__init__.py
"""
Репозиторії для моделей, пов'язаних з "Групами", в програмі Kudos.

Цей пакет містить класи репозиторіїв для кожної моделі, що стосується груп,
таких як самі групи, членство в них, налаштування груп та запрошення до груп.

Кожен репозиторій успадковує `BaseRepository` (або його похідні, наприклад,
`BaseDictionaryRepository`, хоча тут це нерелевантно) та надає
спеціалізований інтерфейс для роботи з конкретною моделлю даних.
"""

from backend.app.src.repositories.groups.group_repository import GroupRepository
from backend.app.src.repositories.groups.membership_repository import GroupMembershipRepository
from backend.app.src.repositories.groups.settings_repository import GroupSettingRepository
from backend.app.src.repositories.groups.invitation_repository import GroupInvitationRepository

__all__ = [
    "GroupRepository",
    "GroupMembershipRepository",
    "GroupSettingRepository",
    "GroupInvitationRepository",
]
