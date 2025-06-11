# backend/app/src/repositories/groups/__init__.py
"""
Репозиторії для моделей, пов'язаних з "Групами", в програмі Kudos.

Цей пакет містить класи репозиторіїв для кожної моделі, що стосується груп,
таких як самі групи, членство в них, налаштування груп та запрошення до груп.

Кожен репозиторій успадковує `BaseRepository` (або його похідні, наприклад,
`BaseDictionaryRepository`, хоча тут це нерелевантно) та надає
спеціалізований інтерфейс для роботи з конкретною моделлю даних.
"""

from .group_repository import GroupRepository
from .membership_repository import GroupMembershipRepository
from .settings_repository import GroupSettingRepository
from .invitation_repository import GroupInvitationRepository

__all__ = [
    "GroupRepository",
    "GroupMembershipRepository",
    "GroupSettingRepository",
    "GroupInvitationRepository",
]
