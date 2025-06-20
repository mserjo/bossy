# backend/app/src/services/groups/settings.py
from typing import Optional, Any # List, Dict, UUID видалено
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select # sqlalchemy.future тепер select
# from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from backend.app.src.services.base import BaseService
from backend.app.src.models.groups.settings import GroupSetting
from backend.app.src.repositories.groups.settings_repository import GroupSettingRepository # Імпорт репозиторію
from backend.app.src.models.groups.group import Group
from backend.app.src.models.auth.user import User # Не використовується прямо, але може бути потрібне для аудиту в майбутньому
from backend.app.src.schemas.groups.settings import (
    GroupSettingCreate,
    GroupSettingUpdate,
    GroupSettingResponse
)
from backend.app.src.config import settings as global_settings
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)


class GroupSettingService(BaseService):
    """
    Сервіс для управління налаштуваннями, специфічними для окремих груп.
    Кожна група може мати власний набір конфігурацій, таких як назва валюти бонусів,
    ліміти боргу, політики перевірки завдань тощо.
    Передбачається, що для кожної групи існує не більше одного запису налаштувань.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        self.setting_repo = GroupSettingRepository() # Ініціалізація репозиторію
        logger.info("GroupSettingService ініціалізовано.")

    async def get_settings_for_group(self, group_id: int) -> Optional[GroupSettingResponse]: # Змінено UUID на int
        """
        Отримує налаштування для конкретної групи.
        Зазвичай група має один запис налаштувань.
        """
        logger.debug(f"Спроба отримання налаштувань для групи ID: {group_id}")

        settings_db = await self.setting_repo.get_by_group_id(session=self.db_session, group_id=group_id)
        # TODO: selectinload для GroupSetting, якщо потрібно, має бути в репозиторії get_by_group_id або тут після отримання.

        if settings_db:
            logger.info(f"Налаштування для групи ID '{group_id}' знайдено.")
            return GroupSettingResponse.model_validate(settings_db)
        else:
            logger.info(f"Запис налаштувань для групи ID '{group_id}' не знайдено.")
            # Тут можна реалізувати створення налаштувань за замовчуванням, якщо потрібно.
            # Наприклад, викликати self.create_or_update_group_settings(group_id, GroupSettingUpdate(), current_user_id)
            # щоб створити запис з default значеннями з моделі/схеми.
            return None

    async def create_or_update_group_settings(
            self,
            group_id: int, # Змінено UUID на int
            settings_data: GroupSettingUpdate,
            current_user_id: Optional[int] = None # Змінено UUID на int
    ) -> GroupSettingResponse:
        """
        Створює налаштування групи, якщо вони не існують, або оновлює їх, якщо існують.
        Це операція типу "upsert", специфічна для запису налаштувань групи.
        """
        log_actor = f"користувачем ID '{current_user_id}'" if current_user_id else "системою"
        logger.debug(f"Спроба створення/оновлення налаштувань для групи ID: {group_id} {log_actor}.")

        group_db = await self.db_session.get(Group, group_id) # Перевірка існування групи
        if not group_db:
            msg = f"Групу з ID '{group_id}' не знайдено."
            logger.error(msg + " Неможливо створити/оновити налаштування.")
            raise ValueError(msg)

        settings_db = await self.setting_repo.get_by_group_id(session=self.db_session, group_id=group_id)

        kwargs_for_repo: Dict[str, Any] = {}
        if current_user_id is not None:
            if hasattr(GroupSetting, 'updated_by_user_id'): # Модель GroupSetting може не мати цих полів
                 kwargs_for_repo['updated_by_user_id'] = current_user_id
            if not settings_db and hasattr(GroupSetting, 'created_by_user_id'):
                 kwargs_for_repo['created_by_user_id'] = current_user_id

        if settings_db:
            logger.info(f"Знайдено існуючі налаштування для групи ID '{group_id}'. Оновлення.")
            # updated_at оновлюється автоматично через TimestampedMixin в BaseRepository.update
            settings_db = await self.setting_repo.update(
                session=self.db_session, db_obj=settings_db, obj_in=settings_data, **kwargs_for_repo
            )
        else:
            logger.info(f"Існуючі налаштування для групи ID '{group_id}' не знайдено. Створення нового запису.")
            # Переконуємося, що group_id є в даних для створення
            create_data_dict = settings_data.model_dump(exclude_unset=True)
            create_data_dict['group_id'] = group_id

            # GroupSettingCreate може бути таким же як GroupSettingUpdate, або мати більше обов'язкових полів
            # Для простоти, припускаємо, що GroupSettingCreate може приймати ті ж поля, що й GroupSettingUpdate + group_id
            # Якщо GroupSettingCreate відрізняється, потрібно створити його екземпляр тут.
            # Поточний BaseRepository.create приймає CreateSchemaType.
            # Потрібно створити екземпляр GroupSettingCreateSchema.

            # Створюємо екземпляр GroupSettingCreateSchema, якщо він визначений
            # Якщо GroupSettingCreate не визначено або є плейсхолдером, це може викликати помилку.
            # Припускаємо, що GroupSettingCreateSchema існує та приймає ці поля.
            create_schema_instance = GroupSettingCreate(**create_data_dict)

            settings_db = await self.setting_repo.create(
                session=self.db_session, obj_in=create_schema_instance, **kwargs_for_repo
            )

        if not settings_db: # Якщо create або update повернули None (малоймовірно для BaseRepository)
            msg = f"Не вдалося зберегти налаштування для групи ID '{group_id}'."
            logger.error(msg)
            raise RuntimeError(msg) # Або більш специфічний виняток

        try:
            await self.commit()
            # Оновлюємо для отримання будь-яких значень БД за замовчуванням та зв'язків (якщо є)
            # Якщо repo.create/update повертають об'єкт, який вже є в сесії, refresh може бути достатньо.
            # Якщо потрібні зв'язки, які repo не завантажив, потрібен get_by_id з selectinload.
            # Наразі GroupSetting не має зв'язків у _load_relations.
            await self.db_session.refresh(settings_db)
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Помилка цілісності при збереженні налаштувань для групи ID '{group_id}': {e}",
                         exc_info=global_settings.DEBUG)
            raise ValueError(f"Не вдалося зберегти налаштування для групи ID '{group_id}' через конфлікт даних.")
        except Exception as e: # Обробка інших можливих помилок
            await self.rollback()
            logger.error(f"Неочікувана помилка при збереженні налаштувань для групи ID '{group_id}': {e}", exc_info=global_settings.DEBUG)
            raise


        logger.info(f"Налаштування для групи ID '{group_id}' успішно збережено.")
        return GroupSettingResponse.model_validate(settings_db)

    async def update_group_currency(self, group_id: int, currency_name: str, # Змінено UUID на int
                                    current_user_id: Optional[int] = None) -> GroupSettingResponse: # Змінено UUID на int
        """Оновлює тільки назву валюти для налаштувань групи."""
        log_actor = f"користувачем ID '{current_user_id}'" if current_user_id else "системою"
        logger.debug(f"Оновлення назви валюти для групи ID {group_id} на '{currency_name}' {log_actor}.")
        # Використовуємо GroupSettingUpdate для часткового оновлення
        update_payload = GroupSettingUpdate(currency_name=currency_name)
        return await self.create_or_update_group_settings(group_id, update_payload, current_user_id)

    async def get_group_setting_value(self, group_id: UUID, setting_key: str, default: Optional[Any] = None) -> \
    Optional[Any]:
        """
        Допоміжний метод для отримання значення конкретного налаштування для групи.

        :param group_id: ID групи.
        :param setting_key: Назва поля налаштування (наприклад, 'currency_name', 'max_debt_amount').
        :param default: Значення за замовчуванням, якщо налаштування або ключ не знайдено.
        :return: Значення налаштування або значення за замовчуванням.
        """
        logger.debug(f"Отримання значення налаштування за ключем '{setting_key}' в групі ID '{group_id}'.")
        group_settings_response = await self.get_settings_for_group(group_id)

        if group_settings_response:
            # Перевіряємо, чи Pydantic модель має такий атрибут
            if hasattr(group_settings_response, setting_key):
                value = getattr(group_settings_response, setting_key)
                logger.info(f"Знайдено значення '{value}' для ключа '{setting_key}' в групі ID '{group_id}'.")
                return value
            else:
                logger.warning(
                    f"Ключ налаштування '{setting_key}' не знайдено в налаштуваннях групи ID '{group_id}'. Повернення значення за замовчуванням.")
        else:  # Налаштування для групи взагалі не знайдено
            logger.info(
                f"Запис налаштувань для групи ID '{group_id}' не знайдено. Повернення значення за замовчуванням для ключа '{setting_key}'.")
        return default

    # TODO: Розглянути метод для видалення налаштувань групи, якщо це дозволено бізнес-логікою.
    # Зазвичай налаштування існують, поки існує група, або скидаються до значень за замовчуванням.
    # async def delete_group_settings(self, group_id: UUID) -> bool: ...


logger.debug(f"{GroupSettingService.__name__} (сервіс налаштувань груп) успішно визначено.")
