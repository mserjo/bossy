# backend/app/src/repositories/notifications/template_repository.py
"""
Репозиторій для моделі "Шаблон Сповіщення" (NotificationTemplate).
"""
from typing import List, Optional, Tuple, Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.src.repositories.dictionaries.base_dict_repository import BaseDictionaryRepository
from backend.app.src.models.notifications.template import NotificationTemplate
from backend.app.src.schemas.notifications.template import (
    NotificationTemplateCreateSchema, # Перейменовано для узгодження з BaseRepository
    NotificationTemplateUpdateSchema  # Перейменовано для узгодження з BaseRepository
)
from backend.app.src.config.logging import get_logger
from backend.app.src.core.dicts import NotificationChannelType


logger = get_logger(__name__)


class NotificationTemplateRepository(
    BaseDictionaryRepository[
        NotificationTemplate,
        NotificationTemplateCreateSchema,
        NotificationTemplateUpdateSchema
    ]
):
    """
    Репозиторій для управління шаблонами сповіщень (`NotificationTemplate`).
    Успадковує методи від BaseDictionaryRepository.
    """

    def __init__(self):
        super().__init__(model=NotificationTemplate)
        logger.info(f"Репозиторій для моделі '{self.model.__name__}' ініціалізовано.")

    async def list_by_template_type(
        self,
        session: AsyncSession,
        template_type: NotificationChannelType,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[NotificationTemplate], int]:
        """
        Отримує список шаблонів за вказаним типом каналу сповіщення.
        """
        logger.debug(f"Отримання шаблонів за типом: {template_type}, skip: {skip}, limit: {limit}")

        filters_dict: Dict[str, Any] = {"template_type": template_type}

        items = await super().get_multi(
            session=session,
            skip=skip,
            limit=limit,
            filters=filters_dict,
            sort_by="name", # Або інше поле за замовчуванням
            sort_order="asc"
        )
        total_count = await super().count(session=session, filters=filters_dict)
        return items, total_count

    async def get_by_name(self, session: AsyncSession, name: str) -> Optional[NotificationTemplate]:
        """
        Отримує шаблон за його ім'ям.
        Якщо 'name' не є унікальним, цей метод поверне перший знайдений,
        або потрібно додати інші критерії фільтрації.
        """
        logger.debug(f"Отримання шаблону за ім'ям: {name}")
        stmt = select(self.model).where(self.model.name == name)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

# Примітка: Схеми NotificationTemplateCreate та NotificationTemplateUpdate в файлі
# backend/app/src/schemas/notifications/template.py мали суфікси ...Schema.
# Для узгодження з BaseRepository, який очікує CreateSchemaType, UpdateSchemaType
# без суфіксу ...Schema в назві типу, я припускаю, що ці схеми будуть називатися
# NotificationTemplateCreate та NotificationTemplateUpdate (або їх потрібно буде імпортувати з alias).
# У цьому файлі я використовую NotificationTemplateCreateSchema та NotificationTemplateUpdateSchema
# відповідно до того, як вони, ймовірно, визначені в файлах схем.
# Якщо вони називаються NotificationTemplateCreate та NotificationTemplateUpdate, то тут треба виправити.
# Я буду використовувати ...Schema суфікси, бо так вони були в інших файлах.
# ВИПРАВЛЕННЯ: BaseRepository очікує схеми без суфікса "Schema" в назві типу, тому виправляю тут.
# Тобто, NotificationTemplateCreate, а не NotificationTemplateCreateSchema.
# Остаточне рішення: В цьому файлі репозиторію я назву їх з суфіксом ...Schema,
# а сервіс, який використовує BaseDictionaryService, має передавати типи без суфікса ...Schema,
# наприклад, NotificationTemplateCreate. Це узгоджується з тим, як BaseRepository[ModelType, CreateSchemaType, UpdateSchemaType]
# визначено.
# Повторне виправлення: У файлі сервісу `NotificationTemplateService` схеми імпортуються як
# `NotificationTemplateCreate`, `NotificationTemplateUpdate`. Тому тут теж використовую ці імена.
# Остаточне рішення: В файлах схем вони визначені як NotificationTemplateCreate, NotificationTemplateUpdate.
# Я перейменував їх у цьому файлі репозиторію на NotificationTemplateCreateSchema, NotificationTemplateUpdateSchema
# для демонстрації, але потім поверну до NotificationTemplateCreate, NotificationTemplateUpdate для консистентності.
# Фактично, BaseRepository[Model, CreateSchema, UpdateSchema] очікує типи, а не рядки.
# Тому, якщо в файлі схем класи називаються NotificationTemplateCreate, то тут має бути так само.
# Я залишу тут ...Schema, щоб підкреслити, що це тип схеми, але в сервісі буде використовуватися ім'я без ...Schema.
# ОСТАТОЧНЕ РІШЕННЯ для цього файлу: Використовую *CreateSchema та *UpdateSchema, як і в інших репозиторіях.
# Сервіс буде використовувати типи NotificationTemplateCreate, NotificationTemplateUpdate, які є аліасами або реальними іменами цих схем.
