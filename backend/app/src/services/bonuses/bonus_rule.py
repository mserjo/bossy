# backend/app/src/services/bonuses/bonus_rule.py
"""
Сервіс для управління правилами нарахування бонусів.

Відповідає за створення, оновлення, видалення, отримання та пошук
правил нарахування бонусів, враховуючи їх специфічність та умови застосування.
"""
from typing import List, Optional, Dict, TYPE_CHECKING # Any видалено, Dict використовується, TYPE_CHECKING додано
# UUID видалено, оскільки всі ID, що були UUID, змінено на int, і uuid4() тут не використовується
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_ # Оновлено імпорт select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from backend.app.src.services.base import BaseService
from backend.app.src.models.bonuses.bonus import BonusRule
from backend.app.src.models.groups.group import Group
from backend.app.src.models.dictionaries.task_types import TaskType
from backend.app.src.models.tasks.task import Task
# from backend.app.src.models.tasks.event import Event # Якщо правила можуть бути пов'язані з подіями
from backend.app.src.models.auth.user import User

from backend.app.src.schemas.bonuses.bonus_rule import (
    BonusRuleCreate,
    BonusRuleUpdate,
    BonusRuleResponse
)
from backend.app.src.config.logging import get_logger # Стандартизований імпорт логера
logger = get_logger(__name__) # Ініціалізація логера
from backend.app.src.config import settings

if TYPE_CHECKING: # Умовний імпорт для TYPE_CHECKING
    pass


class BonusRuleService(BaseService):
    """
    Сервіс для управління правилами нарахування бонусів.
    Правила визначають умови, за яких нараховуються або списуються бали.
    Вони можуть бути пов'язані з типами завдань, конкретними завданнями/подіями або бути загальними.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        logger.info("BonusRuleService ініціалізовано.")

    async def get_bonus_rule_by_id(self, rule_id: int) -> Optional[BonusRuleResponse]: # rule_id змінено на int
        """
        Отримує правило нарахування бонусів за його ID, з завантаженими пов'язаними сутностями.

        :param rule_id: ID правила (int).
        :return: Pydantic схема BonusRuleResponse або None, якщо не знайдено.
        """
        logger.debug(f"Спроба отримання правила нарахування бонусів за ID: {rule_id}")

        stmt = select(BonusRule).options(
            selectinload(BonusRule.group),
            selectinload(BonusRule.task_type),
            selectinload(BonusRule.task),
            # selectinload(BonusRule.event), # Якщо поле event існує в моделі
            selectinload(BonusRule.created_by_user).options(selectinload(User.user_type)),
            selectinload(BonusRule.updated_by_user).options(selectinload(User.user_type))
        ).where(BonusRule.id == rule_id)

        rule_db = (await self.db_session.execute(stmt)).scalar_one_or_none()

        if rule_db:
            logger.info(f"Правило нарахування бонусів з ID '{rule_id}' знайдено.")
            return BonusRuleResponse.model_validate(rule_db)  # Pydantic v2
        logger.info(f"Правило нарахування бонусів з ID '{rule_id}' не знайдено.")
        return None

    async def create_bonus_rule(self, rule_data: BonusRuleCreate, creator_user_id: int) -> BonusRuleResponse: # creator_user_id змінено на int
        """
        Створює нове правило нарахування бонусів.

        :param rule_data: Дані для створення правила (Pydantic схема).
        :param creator_user_id: ID користувача (int), що створює правило.
        :return: Pydantic схема створеного BonusRuleResponse.
        :raises ValueError: Якщо пов'язані сутності не знайдено або ім'я правила не унікальне в межах області. # i18n
        """
        logger.debug(f"Спроба створення нового правила '{rule_data.name}' користувачем ID: {creator_user_id}")

        # Перевірка існування пов'язаних сутностей
        if rule_data.group_id and not await self.db_session.get(Group, rule_data.group_id):
            raise ValueError(f"Групу з ID '{rule_data.group_id}' не знайдено.")  # i18n
        if rule_data.task_type_id and not await self.db_session.get(TaskType, rule_data.task_type_id):
            raise ValueError(f"Тип завдання з ID '{rule_data.task_type_id}' не знайдено.")  # i18n
        if rule_data.task_id and not await self.db_session.get(Task, rule_data.task_id):
            raise ValueError(f"Завдання з ID '{rule_data.task_id}' не знайдено.")  # i18n

        # Перевірка унікальності імені правила в межах його області (глобальна або група)
        stmt_name_check = select(BonusRule.id).where(BonusRule.name == rule_data.name)
        scope_log_msg = "глобальній області"  # i18n
        if rule_data.group_id:
            stmt_name_check = stmt_name_check.where(BonusRule.group_id == rule_data.group_id)
            scope_log_msg = f"групі ID '{rule_data.group_id}'"  # i18n
        else:
            stmt_name_check = stmt_name_check.where(BonusRule.group_id.is_(None))

        if (await self.db_session.execute(stmt_name_check)).scalar_one_or_none():
            logger.warning(f"Правило з ім'ям '{rule_data.name}' вже існує в {scope_log_msg}.")
            raise ValueError(f"Правило з ім'ям '{rule_data.name}' вже існує в {scope_log_msg}.")  # i18n

        # Створення об'єкта моделі
        # created_at/updated_at встановлюються автоматично, якщо налаштовано в моделі
        new_rule_db = BonusRule(
            **rule_data.model_dump(),  # Pydantic v2
            created_by_user_id=creator_user_id,
            updated_by_user_id=creator_user_id  # При створенні updated_by_user_id = creator_user_id
        )

        self.db_session.add(new_rule_db)
        try:
            await self.commit()
            await self.db_session.refresh(new_rule_db, attribute_names=[
                'group', 'task_type', 'task', 'created_by_user', 'updated_by_user'
            ])  # Завантажуємо всі можливі зв'язки
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Помилка цілісності при створенні правила '{rule_data.name}': {e}", exc_info=settings.DEBUG)
            raise ValueError(f"Не вдалося створити правило через конфлікт даних: {e}")  # i18n
        except Exception as e:  # Обробка інших можливих помилок
            await self.rollback()
            logger.error(f"Неочікувана помилка при створенні правила '{rule_data.name}': {e}", exc_info=settings.DEBUG)
            raise  # Перекидаємо помилку далі

        logger.info(f"Правило '{new_rule_db.name}' (ID: {new_rule_db.id}) успішно створено.")
        return BonusRuleResponse.model_validate(new_rule_db)

    async def update_bonus_rule(
            self, rule_id: int, rule_update_data: BonusRuleUpdate, current_user_id: int # rule_id, current_user_id змінено на int
    ) -> Optional[BonusRuleResponse]:
        """
        Оновлює існуюче правило нарахування бонусів.

        :param rule_id: ID правила (int) для оновлення.
        :param rule_update_data: Дані для оновлення (Pydantic схема).
        :param current_user_id: ID користувача (int), що виконує оновлення.
        :return: Pydantic схема оновленого BonusRuleResponse або None, якщо правило не знайдено.
        :raises ValueError: Якщо пов'язані сутності не знайдено або ім'я правила не унікальне. # i18n
        """
        logger.debug(f"Спроба оновлення правила ID: {rule_id} користувачем ID: {current_user_id}")

        rule_db = await self.db_session.get(BonusRule, rule_id)
        if not rule_db:
            logger.warning(f"Правило ID '{rule_id}' не знайдено для оновлення.")
            return None

        update_data = rule_update_data.model_dump(exclude_unset=True)  # Pydantic v2

        # Перевірка існування нових пов'язаних сутностей, якщо вони змінюються
        if 'group_id' in update_data and rule_db.group_id != update_data['group_id']:
            if update_data['group_id'] and not await self.db_session.get(Group, update_data['group_id']):
                raise ValueError(f"Нова група з ID '{update_data['group_id']}' не знайдена.")  # i18n
        if 'task_type_id' in update_data and rule_db.task_type_id != update_data['task_type_id']:
            if update_data['task_type_id'] and not await self.db_session.get(TaskType, update_data['task_type_id']):
                raise ValueError(f"Новий тип завдання ID '{update_data['task_type_id']}' не знайдено.")  # i18n
        if 'task_id' in update_data and rule_db.task_id != update_data['task_id']:
            if update_data['task_id'] and not await self.db_session.get(Task, update_data['task_id']):
                raise ValueError(f"Нове завдання ID '{update_data['task_id']}' не знайдено.")  # i18n

        # Перевірка унікальності імені, якщо ім'я або група змінюються
        new_name = update_data.get('name', rule_db.name)
        # group_id може бути None, тому обережно з .get()
        new_group_id = update_data['group_id'] if 'group_id' in update_data else rule_db.group_id

        if ('name' in update_data and new_name != rule_db.name) or \
                ('group_id' in update_data and new_group_id != rule_db.group_id):
            stmt_name_check = select(BonusRule.id).where(
                BonusRule.name == new_name,
                BonusRule.id != rule_id  # Виключаємо поточне правило
            )
            scope_log_msg = "глобальній області"  # i18n
            if new_group_id is not None:
                stmt_name_check = stmt_name_check.where(BonusRule.group_id == new_group_id)
                scope_log_msg = f"групі ID '{new_group_id}'"  # i18n
            else:
                stmt_name_check = stmt_name_check.where(BonusRule.group_id.is_(None))

            if (await self.db_session.execute(stmt_name_check)).scalar_one_or_none():
                raise ValueError(f"Інше правило з ім'ям '{new_name}' вже існує в {scope_log_msg}.")  # i18n

        # Оновлення полів
        for field, value in update_data.items():
            setattr(rule_db, field, value)

        rule_db.updated_by_user_id = current_user_id
        # rule_db.updated_at оновлюється автоматично, якщо налаштовано в моделі, або:
        rule_db.updated_at = datetime.now(timezone.utc)

        self.db_session.add(rule_db)
        try:
            await self.commit()
            await self.db_session.refresh(rule_db, attribute_names=[
                'group', 'task_type', 'task', 'created_by_user', 'updated_by_user'
            ])
            logger.info(f"Правило ID '{rule_id}' успішно оновлено користувачем ID '{current_user_id}'.")
            return BonusRuleResponse.model_validate(rule_db)
        except IntegrityError as e:  # Обробка помилки унікальності на рівні БД
            await self.rollback()
            logger.error(f"Помилка цілісності при оновленні правила ID '{rule_id}': {e}", exc_info=settings.DEBUG)
            raise ValueError(f"Не вдалося оновити правило через конфлікт даних: {e}")  # i18n
        except Exception as e:
            await self.rollback()
            logger.error(f"Помилка при оновленні правила ID '{rule_id}': {e}", exc_info=settings.DEBUG)
            raise

    async def delete_bonus_rule(self, rule_id: int, current_user_id: int) -> bool: # rule_id, current_user_id змінено на int
        """
        Видаляє правило нарахування бонусів.

        :param rule_id: ID правила (int) для видалення.
        :param current_user_id: ID користувача (int), що виконує видалення (для аудиту).
        :return: True, якщо видалення успішне, False - якщо правило не знайдено.
        """
        logger.debug(f"Спроба видалення правила ID: {rule_id} користувачем ID: {current_user_id}")

        rule_db = await self.db_session.get(BonusRule, rule_id)
        if not rule_db:
            logger.warning(f"Правило ID '{rule_id}' не знайдено для видалення.")
            return False

        # TODO: Згідно technical_task.txt, перевірити, чи є обмеження на видалення правил (наприклад, якщо вони вже використовувались).
        # Наразі припускаємо пряме видалення.

        await self.db_session.delete(rule_db)
        await self.commit()
        logger.info(f"Правило ID '{rule_id}' успішно видалено користувачем ID '{current_user_id}'.")
        return True

    async def list_bonus_rules(
            self,
            group_id: Optional[int] = None, # Змінено Optional[UUID] на Optional[int]
            task_type_id: Optional[int] = None, # Змінено Optional[UUID] на Optional[int]
            task_id: Optional[int] = None, # Змінено Optional[UUID] на Optional[int]
            is_active: Optional[bool] = None,  # За замовчуванням не фільтрує за активністю, щоб показати всі
            valid_on_date: Optional[datetime] = None,  # Дата для перевірки активності правила (valid_from/valid_until)
            skip: int = 0,
            limit: int = 100,
            include_global_rules_if_group_given: bool = False
    ) -> List[BonusRuleResponse]:
        """
        Перелічує правила нарахування бонусів з можливістю фільтрації та пагінації.

        :param group_id: Фільтр за ID групи (int).
        :param task_type_id: Фільтр за ID типу завдання (int).
        :param task_id: Фільтр за ID завдання (int).
        :param is_active: Фільтр за статусом активності правила.
        :param valid_on_date: Якщо вказано, фільтрує правила, активні на цю дату.
        :param skip: Кількість записів для пропуску.
        :param limit: Максимальна кількість записів.
        :param include_global_rules_if_group_given: Якщо True та group_id вказано, включає також глобальні правила.
        :return: Список Pydantic схем BonusRuleResponse.
        """
        logger.debug(
            f"Перелік правил: group_id={group_id}, task_type_id={task_type_id}, task_id={task_id}, active={is_active}, valid_on={valid_on_date}, global_for_group={include_global_rules_if_group_given}")

        stmt = select(BonusRule).options(
            selectinload(BonusRule.group), selectinload(BonusRule.task_type),
            selectinload(BonusRule.task),
            selectinload(BonusRule.created_by_user).options(selectinload(User.user_type)),
            selectinload(BonusRule.updated_by_user).options(selectinload(User.user_type))
        )

        conditions = []
        if group_id is not None:
            if include_global_rules_if_group_given:
                conditions.append(or_(BonusRule.group_id == group_id, BonusRule.group_id.is_(None)))
            else:
                conditions.append(BonusRule.group_id == group_id)
        # Якщо group_id не вказано, не фільтруємо за групою (показує всі: і глобальні, і групові)
        # Для фільтрації тільки глобальних, якщо group_id is None, треба додати:
        # elif group_id is None and filter_only_global: conditions.append(BonusRule.group_id.is_(None))

        if task_type_id: conditions.append(BonusRule.task_type_id == task_type_id)
        if task_id: conditions.append(BonusRule.task_id == task_id)
        if is_active is not None:
            # Припускаємо, що 'active' є рядковим представленням активного стану в полі 'state'
            conditions.append(BonusRule.state == "active" if is_active else BonusRule.state != "active")

        if valid_on_date:
            # Правило активне, якщо valid_from <= valid_on_date AND (valid_until IS NULL OR valid_until >= valid_on_date)
            # Ігноруємо timezone для порівняння дат, якщо вони зберігаються як naive datetimes в БД.
            # Якщо в БД дати з timezone, valid_on_date теж має бути timezone-aware.
            # Припускаємо, що valid_on_date є timezone-aware (наприклад, UTC).
            conditions.append(
                and_(
                    or_(BonusRule.valid_from.is_(None), BonusRule.valid_from <= valid_on_date),
                    or_(BonusRule.valid_until.is_(None), BonusRule.valid_until >= valid_on_date)
                )
            )

        if conditions:
            stmt = stmt.where(*conditions)

        # TODO: Згідно technical_task.txt, уточнити поля для сортування.
        # Можливі поля: name, amount, state, valid_from, valid_until, created_at.
        # Потрібно реалізувати динамічне сортування аналогічно до UserService.list_users.
        stmt = stmt.order_by(BonusRule.group_id.nulls_first(), BonusRule.name).offset(skip).limit(limit)

        rules_db = (await self.db_session.execute(stmt)).scalars().unique().all()

        response_list = [BonusRuleResponse.model_validate(r) for r in rules_db]
        logger.info(f"Отримано {len(response_list)} правил нарахування бонусів.")
        return response_list

    async def get_applicable_bonus_rules(
            self,
            group_id: int,  # Змінено UUID на int
            task_id: Optional[int] = None,  # Змінено Optional[UUID] на Optional[int]
            task_type_id: Optional[int] = None,  # Змінено Optional[UUID] на Optional[int]
            # TODO: Розглянути `action_type: str` для більш складних умов, якщо потрібно (напр. 'TASK_COMPLETION')
    ) -> List[BonusRuleResponse]:
        """
        Отримує список правил, які потенційно застосовні до заданого контексту (група, завдання, тип завдання).
        Правила повинні бути активними та валідними на поточну дату.
        Повертає список, відсортований за специфічністю (найбільш специфічні перші).
        """
        current_time = datetime.now(timezone.utc)
        logger.debug(
            f"Пошук застосовних правил для group_id={group_id}, task_id={task_id}, task_type_id={task_type_id} на {current_time.isoformat()}")

        # Базові умови: правило активне та валідне за датою
        base_conditions = [
            BonusRule.state == "active", # Припускаємо, що 'active' є рядковим представленням активного стану
            or_(BonusRule.valid_from.is_(None), BonusRule.valid_from <= current_time),
            or_(BonusRule.valid_until.is_(None), BonusRule.valid_until >= current_time)
        ]

        # Формуємо умови для різних рівнів специфічності
        clauses = []

        # 1. Правила для конкретного завдання (найвищий пріоритет)
        #    (група завдання неявно враховується, якщо завдання належить групі; або правило може бути глобальним для завдання)
        if task_id:
            clauses.append(and_(*base_conditions, BonusRule.task_id == task_id))

        # 2. Правила для типу завдання (в межах групи або глобальні)
        if task_type_id:
            clauses.append(and_(
                *base_conditions,
                BonusRule.task_type_id == task_type_id,
                BonusRule.task_id.is_(None),  # Не пов'язане з конкретним завданням
                or_(BonusRule.group_id == group_id, BonusRule.group_id.is_(None))  # Або для цієї групи, або глобальне
            ))

        # 3. Загальні правила для конкретної групи
        clauses.append(and_(
            *base_conditions,
            BonusRule.group_id == group_id,
            BonusRule.task_id.is_(None),
            BonusRule.task_type_id.is_(None)
        ))

        # 4. Загальні глобальні правила
        clauses.append(and_(
            *base_conditions,
            BonusRule.group_id.is_(None),
            BonusRule.task_id.is_(None),
            BonusRule.task_type_id.is_(None)
        ))

        stmt = select(BonusRule).options(
            selectinload(BonusRule.group),
            selectinload(BonusRule.task_type),
            selectinload(BonusRule.task)
        ).where(or_(*clauses))

        # Сортування для пріоритезації: більш специфічні правила перші.
        # task_id (не NULL) > task_type_id (не NULL) > group_id (не NULL)
        stmt = stmt.order_by(
            BonusRule.task_id.desc().nulls_last(),
            BonusRule.task_type_id.desc().nulls_last(),
            BonusRule.group_id.desc().nulls_last(),
            BonusRule.name  # Додаткове сортування для стабільності
        )

        rules_db = (await self.db_session.execute(stmt)).scalars().unique().all()

        response_list = [BonusRuleResponse.model_validate(r) for r in rules_db]
        logger.info(f"Отримано {len(response_list)} застосовних правил, відсортованих за специфічністю.")
        return response_list


logger.debug("BonusRuleService клас визначено та завантажено.")
