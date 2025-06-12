# backend/app/src/services/bonuses/account.py
"""
Сервіс для управління бонусними рахунками користувачів.

Надає функціонал для створення, отримання, оновлення балансу
та перегляду бонусних рахунків, а також для запису транзакцій.
"""
from typing import List, Optional # Tuple, Any видалено, оскільки не використовуються в сигнатурах
from uuid import UUID
from decimal import Decimal  # Для точних розрахунків балансу
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select # Оновлено імпорт
from sqlalchemy.orm import selectinload, noload
from sqlalchemy.exc import IntegrityError

from backend.app.src.services.base import BaseService
from backend.app.src.models.bonuses.account import UserAccount  # Модель SQLAlchemy UserAccount
from backend.app.src.models.auth.user import User  # Для зв'язку рахунку з користувачем
from backend.app.src.models.groups.group import Group  # Якщо рахунки для групи користувачів
from backend.app.src.models.bonuses.transaction import AccountTransaction  # Модель для транзакцій

from backend.app.src.schemas.bonuses.account import (  # Pydantic Схеми
    UserAccountResponse,
    # UserAccountCreate, # Не використовується прямо, оскільки рахунки створюються автоматично або через get_or_create
    # UserAccountUpdate, # Для ручних коригувань адміністратором (не реалізовано в цьому сервісі)
)
from backend.app.src.schemas.bonuses.transaction import AccountTransactionResponse
from backend.app.src.config import logger  # Використання спільного логера з конфігу
from backend.app.src.config import settings  # Для доступу до конфігурацій


# TODO: [Exceptions] Перенести кастомні помилки до backend/app/src/core/exceptions.py
class InsufficientFundsError(ValueError):
    """Помилка недостатньо коштів на рахунку."""

    def __init__(self, message="Недостатньо коштів на рахунку", current_balance: Optional[Decimal] = None):  # i18n
        self.current_balance = current_balance
        super().__init__(message)


class UserAccountService(BaseService):
    """
    Сервіс для управління бонусними рахунками користувачів.
    Обробляє створення, отримання та відображення балансу.
    Зміни балансу повинні відбуватися атомарно через AccountTransactionService (або, як тут, створюючи транзакцію).
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        logger.info("UserAccountService ініціалізовано.")

    async def _get_user_account_orm(
            self,
            user_id: UUID,
            group_id: Optional[UUID] = None,
            load_relations: bool = True
    ) -> Optional[UserAccount]:
        """
        Внутрішній метод для отримання ORM моделі UserAccount.
        """
        log_msg = f"користувача ID '{user_id}'"
        if group_id: log_msg += f" у групі ID '{group_id}'"

        stmt = select(UserAccount).where(UserAccount.user_id == user_id)

        if group_id:
            stmt = stmt.where(UserAccount.group_id == group_id)
        else:
            # Згідно ТЗ, group_id nullable для глобального рахунку
            stmt = stmt.where(UserAccount.group_id.is_(None))

        if load_relations:
            options_to_load = [selectinload(UserAccount.user).options(selectinload(User.user_type))]
            if group_id:  # Завантажуємо групу тільки якщо вона є
                options_to_load.append(selectinload(UserAccount.group))
            stmt = stmt.options(*options_to_load)
        else:  # Якщо відносини не потрібні, явно їх не завантажуємо
            stmt = stmt.options(noload('*'))

        account_db = (await self.db_session.execute(stmt)).scalar_one_or_none()
        return account_db

    async def get_user_account(
            self,
            user_id: UUID,
            group_id: Optional[UUID] = None  # None для глобального рахунку
    ) -> Optional[UserAccountResponse]:
        """
        Отримує бонусний рахунок користувача.

        :param user_id: ID користувача.
        :param group_id: ID групи (None для глобального рахунку).
        :return: Pydantic схема відповіді UserAccountResponse або None.
        """
        log_msg = f"користувача ID '{user_id}'"
        if group_id:
            log_msg += f" в групі ID '{group_id}'"
        else:
            log_msg += " (глобальний)"
        logger.debug(f"Спроба отримання бонусного рахунку для {log_msg}.")

        account_db = await self._get_user_account_orm(user_id, group_id, load_relations=True)

        if account_db:
            logger.info(f"Бонусний рахунок знайдено для {log_msg}.")
            return UserAccountResponse.model_validate(account_db)  # Pydantic v2

        logger.info(f"Бонусний рахунок не знайдено для {log_msg}.")
        return None

    async def get_or_create_user_account(
            self,
            user_id: UUID,
            group_id: Optional[UUID] = None,  # None для глобального рахунку
            initial_balance: Decimal = Decimal("0.00")
    ) -> UserAccount:  # Повертає ORM модель для внутрішнього використання
        """
        Отримує або створює бонусний рахунок користувача.
        Повертає ORM модель UserAccount.

        :param user_id: ID користувача.
        :param group_id: ID групи (None для глобального).
        :param initial_balance: Початковий баланс, якщо рахунок створюється.
        :return: ORM модель UserAccount.
        :raises ValueError: Якщо користувача або групу не знайдено. # i18n
        """
        account_db = await self._get_user_account_orm(user_id, group_id,
                                                      load_relations=True)  # Завантажуємо відносини для можливого повернення
        if account_db:
            return account_db

        log_msg = f"користувача ID '{user_id}'"
        if group_id:
            log_msg += f" в групі ID '{group_id}'"
        else:
            log_msg += " (глобальний)"
        logger.info(f"Існуючий бонусний рахунок для {log_msg} не знайдено. Створення нового.")

        user = await self.db_session.get(User, user_id)
        if not user:
            logger.error(f"Користувача з ID '{user_id}' не знайдено при спробі створити бонусний рахунок.")
            raise ValueError(f"Користувача з ID '{user_id}' не знайдено.")  # i18n

        if group_id:
            group = await self.db_session.get(Group, group_id)
            if not group:
                logger.error(f"Групу з ID '{group_id}' не знайдено при спробі створити бонусний рахунок.")
                raise ValueError(f"Групу з ID '{group_id}' не знайдено.")  # i18n

        # Створюємо новий рахунок
        new_account_db = UserAccount(
            user_id=user_id,
            group_id=group_id,  # Може бути None для глобального
            balance=initial_balance,
            # created_at, updated_at - обробляються базовою моделлю або БД
            # last_transaction_at - буде None до першої транзакції
        )

        self.db_session.add(new_account_db)
        try:
            await self.commit()
            # Оновлюємо для завантаження зв'язків, якщо вони потрібні для відповіді або подальшої обробки
            await self.db_session.refresh(new_account_db, attribute_names=['user', 'group'] if group_id else ['user'])
            logger.info(f"Бонусний рахунок створено для {log_msg} з ID {new_account_db.id}.")
            return new_account_db
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Помилка цілісності при створенні рахунку для {log_msg}: {e}", exc_info=settings.DEBUG)
            # Спроба повторно отримати, якщо рахунок був створений конкурентно
            account_db_retry = await self._get_user_account_orm(user_id, group_id, load_relations=True)
            if account_db_retry:
                logger.info(
                    f"Рахунок для {log_msg} знайдено після помилки цілісності (ймовірно, створено конкурентно).")
                return account_db_retry
            raise ValueError(f"Не вдалося створити рахунок для {log_msg} через конфлікт даних.")  # i18n

    async def adjust_account_balance(
            self,
            user_id: UUID,
            amount: Decimal,
            transaction_type: str,  # Наприклад, 'ENROLLMENT', 'MANUAL_ADJUSTMENT', 'REWARD_PAYOUT', 'WITHDRAWAL'
            description: Optional[str] = None,
            related_entity_id: Optional[UUID] = None,  # ID пов'язаної сутності (наприклад, Reward.id)
            group_id: Optional[UUID] = None,  # None для глобального рахунку
            commit_session: bool = True  # Чи потрібно комітити сесію в цьому методі
    ) -> Tuple[UserAccountResponse, AccountTransactionResponse]:
        """
        Коригує баланс рахунку користувача, створюючи при цьому транзакцію.

        :param user_id: ID користувача.
        :param amount: Сума для коригування (додатня для поповнення, від'ємна для списання).
        :param transaction_type: Тип транзакції.
        :param description: Опис транзакції.
        :param related_entity_id: ID пов'язаної сутності.
        :param group_id: ID групи (None для глобального).
        :param commit_session: Якщо True, сесія буде закомічена.
        :return: Кортеж з оновленим UserAccountResponse та створеним AccountTransactionResponse.
        :raises InsufficientFundsError: Якщо коштів недостатньо для списання.
        :raises ValueError: Якщо рахунок користувача не знайдено.
        """
        log_msg = f"користувача ID '{user_id}'"
        if group_id:
            log_msg += f" в групі ID '{group_id}'"
        else:
            log_msg += " (глобальний)"
        logger.info(f"Спроба коригування балансу для {log_msg} на {amount}, тип: '{transaction_type}'.")

        # Отримуємо ORM модель рахунку
        account_db = await self.get_or_create_user_account(user_id, group_id)
        if not account_db:  # Практично неможливо, якщо get_or_create_user_account працює коректно
            logger.error(f"Рахунок для {log_msg} не знайдено навіть після get_or_create_user_account.")
            raise ValueError(f"Рахунок для {log_msg} не знайдено.")  # i18n

        current_balance = Decimal(account_db.balance)
        adjustment_amount = Decimal(amount)

        if adjustment_amount < Decimal("0.00") and current_balance < abs(adjustment_amount):
            logger.warning(
                f"Недостатньо коштів для {log_msg}. Поточний баланс: {current_balance}, спроба списання: {abs(adjustment_amount)}.")
            raise InsufficientFundsError(current_balance=current_balance)  # i18n

        new_balance = current_balance + adjustment_amount
        account_db.balance = new_balance
        account_db.last_transaction_at = datetime.now(timezone.utc)  # Оновлюємо час останньої транзакції
        # updated_at оновлюється автоматично базовою моделлю
        self.db_session.add(account_db)

        # Створення запису транзакції
        transaction_db = AccountTransaction(
            user_account_id=account_db.id,
            transaction_type=transaction_type,
            amount=adjustment_amount,
            balance_after_transaction=new_balance,
            description=description,
            related_entity_id=related_entity_id
            # created_at обробляється базовою моделлю
        )
        self.db_session.add(transaction_db)

        if commit_session:
            await self.commit()
        else:
            # Якщо сесія не комітиться тут, зміни будуть передані викликаючому коду.
            # Важливо забезпечити flush для отримання ID, якщо вони потрібні до коміту.
            await self.db_session.flush([account_db, transaction_db])

        # Оновлюємо для відповіді, щоб відобразити зміни та завантажені зв'язки
        # (get_or_create_user_account вже завантажив user/group)
        await self.db_session.refresh(account_db)
        await self.db_session.refresh(transaction_db,
                                      attribute_names=['account'])  # Завантажити зв'язок з рахунком для транзакції

        logger.info(
            f"Баланс для {log_msg} (ID Рахунку: {account_db.id}) скориговано на {adjustment_amount}. Новий баланс: {new_balance}.")

        return UserAccountResponse.model_validate(account_db), AccountTransactionResponse.model_validate(transaction_db)

    async def list_user_accounts(
            self,
            skip: int = 0,
            limit: int = 100,
            user_id: Optional[UUID] = None,  # Додано фільтр за user_id
            group_id: Optional[UUID] = None,  # Якщо вказано, фільтрує для цієї групи
            filter_global_only: bool = False,  # Якщо True і group_id не вказано, фільтрує тільки глобальні
            min_balance: Optional[Decimal] = None
    ) -> List[UserAccountResponse]:
        """
        Перелічує бонусні рахунки користувачів з фільтрами та пагінацією.

        :param skip: Кількість записів для пропуску.
        :param limit: Максимальна кількість записів.
        :param user_id: Опціональний фільтр за ID користувача.
        :param group_id: Опціональний фільтр за ID групи.
        :param filter_global_only: Якщо True, повертає тільки глобальні рахунки (group_id IS NULL).
                                   Ігнорується, якщо group_id вказано.
        :param min_balance: Опціональний фільтр для мінімального балансу.
        :return: Список Pydantic схем UserAccountResponse.
        """
        logger.debug(
            f"Перелік бонусних рахунків: user={user_id}, group={group_id}, global_only={filter_global_only}, min_balance={min_balance}, skip={skip}, limit={limit}")

        stmt = select(UserAccount).options(
            selectinload(UserAccount.user).options(selectinload(User.user_type)),
            selectinload(UserAccount.group)
            # Завжди намагаємось завантажити, SQLAlchemy впорається, якщо group_id є None
        )

        conditions = []
        if user_id:
            conditions.append(UserAccount.user_id == user_id)

        if group_id:  # Якщо group_id вказано, filter_global_only ігнорується
            conditions.append(UserAccount.group_id == group_id)
        elif filter_global_only:  # group_id не вказано, але потрібні тільки глобальні
            conditions.append(UserAccount.group_id.is_(None))
        # Якщо group_id не вказано і filter_global_only=False, то фільтр за групою не застосовується (всі рахунки для користувача або всі взагалі)

        if min_balance is not None:
            conditions.append(UserAccount.balance >= min_balance)

        if conditions:
            stmt = stmt.where(*conditions)

        # TODO: Згідно technical_task.txt, уточнити поля для сортування. Наразі: user_id, group_id.
        stmt = stmt.order_by(UserAccount.user_id, UserAccount.group_id).offset(skip).limit(limit)

        accounts_db = (await self.db_session.execute(stmt)).scalars().unique().all()

        response_list = [UserAccountResponse.model_validate(acc) for acc in accounts_db]
        logger.info(f"Отримано {len(response_list)} бонусних рахунків.")
        return response_list


logger.debug("UserAccountService клас визначено та завантажено.")
