# backend/app/src/repositories/groups/settings_repository.py
"""
Репозиторій для моделі "Налаштування Групи" (GroupSetting).

Цей модуль визначає клас `GroupSettingRepository`, який успадковує `BaseRepository`
та надає специфічні методи для роботи з налаштуваннями груп, зокрема
отримання налаштувань за ID групи.
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Абсолютний імпорт базового репозиторію
from backend.app.src.repositories.base import BaseRepository
# Абсолютний імпорт моделі та схем
from backend.app.src.models.groups.settings import GroupSetting
from backend.app.src.schemas.groups.settings import GroupSettingCreateSchema, GroupSettingUpdateSchema
from backend.app.src.config.logging import get_logger # Імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)


class GroupSettingRepository(BaseRepository[GroupSetting, GroupSettingCreateSchema, GroupSettingUpdateSchema]):
    """
    Репозиторій для управління записами налаштувань груп (`GroupSetting`).

    Успадковує базові CRUD-методи від `BaseRepository` та надає
    додатковий метод для отримання налаштувань за `group_id`, оскільки
    зв'язок між групою та її налаштуваннями є один-до-одного.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Ініціалізує репозиторій для моделі `GroupSetting`.

        Args:
            db_session (AsyncSession): Асинхронна сесія SQLAlchemy.
        """
        super().__init__(db_session=db_session, model=GroupSetting)

    async def get_by_group_id(self, group_id: int) -> Optional[GroupSetting]:
        """
        Отримує запис налаштувань для вказаної групи.

        Args:
            group_id (int): ID групи.

        Returns:
            Optional[GroupSetting]: Екземпляр моделі `GroupSetting`, якщо знайдено, інакше None.
        """
        stmt = select(self.model).where(self.model.group_id == group_id)
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    # Метод create успадковано. При створенні GroupSetting через репозиторій,
    # group_id має бути частиною GroupSettingCreateSchema.
    # Модель GroupSetting має unique constraint на group_id, тому другий раз
    # створити налаштування для тієї ж групи не вдасться.

    # Метод update успадковано. db_obj буде екземпляром GroupSetting.
    # obj_in буде GroupSettingUpdateSchema.


if __name__ == "__main__":
    # Демонстраційний блок для GroupSettingRepository.
    logger.info("--- Репозиторій Налаштувань Груп (GroupSettingRepository) ---")

    logger.info("Для тестування GroupSettingRepository потрібна асинхронна сесія SQLAlchemy та налаштована БД.")
    logger.info(f"Він успадковує методи від BaseRepository для моделі {GroupSetting.__name__}.")
    logger.info(
        f"  Очікує схему створення: {GroupSettingCreateSchema.__name__}")  # GroupSettingCreateSchema має містити group_id
    logger.info(f"  Очікує схему оновлення: {GroupSettingUpdateSchema.__name__}")

    logger.info("\nСпецифічні методи:")
    logger.info("  - get_by_group_id(group_id: int)")

    logger.info("\nПримітка: Повноцінне тестування репозиторіїв слід проводити з реальною тестовою базою даних.")
    logger.info("При створенні налаштувань через `create()`, `group_id` має бути в схемі `GroupSettingCreateSchema`.")
