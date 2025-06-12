# backend/app/src/services/bonuses/transaction.py
"""
Сервіс для управління транзакціями по бонусних рахунках.

Відповідає за створення записів транзакцій, забезпечуючи атомарне
та коректне оновлення балансів рахунків користувачів.
"""
from typing import List, Optional, Tuple
from uuid import UUID
from decimal import Decimal
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select # Оновлено імпорт
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from backend.app.src.services.base import BaseService
from backend.app.src.models.bonuses.transaction import AccountTransaction
from backend.app.src.models.bonuses.account import UserAccount
from backend.app.src.models.auth.user import User
# from backend.app.src.models.groups.group import Group # Не використовується прямо

from backend.app.src.schemas.bonuses.transaction import (
    AccountTransactionCreate,
    AccountTransactionResponse
)
from backend.app.src.schemas.bonuses.account import UserAccountResponse
from backend.app.src.services.bonuses.account import UserAccountService, InsufficientFundsError
from backend.app.src.config import logger  # Використання спільного логера з конфігу
from backend.app.src.config import settings


class AccountTransactionService(BaseService): # type: ignore
    """
    Сервіс для управління транзакціями по бонусних рахунках.
    Відповідає за створення записів транзакцій та забезпечення атомарного
    і коректного оновлення балансів рахунків користувачів.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        self.account_service = UserAccountService(db_session)  # Ініціалізація сервісу рахунків
        logger.info("AccountTransactionService ініціалізовано.")

    async def create_transaction(
            self,
            transaction_data: AccountTransactionCreate,
            user_id_for_account_lookup: Optional[UUID] = None,  # Якщо user_account_id не надано
            group_id_for_account_lookup: Optional[UUID] = None,  # Для визначення глобального чи групового рахунку
            commit_session: bool = True
    ) -> Tuple[AccountTransactionResponse, UserAccountResponse]:
        """
        Створює нову транзакцію та оновлює баланс відповідного рахунку.

        :param transaction_data: Дані для створення транзакції. `user_account_id` в цьому об'єкті є пріоритетним.
        :param user_id_for_account_lookup: ID користувача для пошуку/створення рахунку, якщо `transaction_data.user_account_id` не вказано.
        :param group_id_for_account_lookup: ID групи для пошуку/створення рахунку (None для глобального).
        :param commit_session: Якщо True, сесія буде закомічена. В іншому випадку, потрібен flush.
        :return: Кортеж з AccountTransactionResponse та оновленим UserAccountResponse.
        :raises ValueError: Якщо рахунок не знайдено або не надано достатньо даних для його ідентифікації.
        :raises InsufficientFundsError: Якщо коштів недостатньо для дебетової транзакції.
        """

        effective_account_id = transaction_data.user_account_id
        user_account_db: Optional[UserAccount] = None

        log_msg_context = f"тип '{transaction_data.transaction_type}', сума {transaction_data.amount}"
        logger.debug(f"Спроба створення транзакції: {log_msg_context}")

        if effective_account_id:
            # Завантажуємо UserAccount разом з user та group для повної відповіді
            user_account_db = await self.db_session.get(
                UserAccount,
                effective_account_id,
                options=[
                    selectinload(UserAccount.user).options(selectinload(User.user_type)),
                    selectinload(UserAccount.group)
                ]
            )
            if not user_account_db:
                logger.error(f"Рахунок користувача з ID '{effective_account_id}' не знайдено.")
                raise ValueError(f"Рахунок користувача з ID '{effective_account_id}' не знайдено.")  # i18n
        elif user_id_for_account_lookup:
            logger.debug(
                f"ID рахунку не надано, пошук/створення для користувача ID '{user_id_for_account_lookup}', група ID '{group_id_for_account_lookup}'.")
            # get_or_create_user_account повертає ORM модель, що добре для атомарності, якщо commit_session=False
            # Важливо: `get_or_create_user_account` не повинен комітити сесію сам, якщо ми хочемо повної атомарності тут.
            # Припускаємо, що якщо `get_or_create_user_account` створює новий рахунок, він може зробити проміжний коміт.
            # Це може бути прийнятним, якщо створення рахунку є окремою допустимою транзакцією.
            # TODO: Переглянути логіку комітів у get_or_create_user_account для забезпечення повної атомарності, якщо потрібно.
            user_account_db = await self.account_service.get_or_create_user_account(
                user_id=user_id_for_account_lookup,
                group_id=group_id_for_account_lookup
                # initial_balance встановлюється за замовчуванням у get_or_create_user_account
            )
            # Перезавантажуємо, щоб бути впевненими, що об'єкт належить поточній сесії з усіма зв'язками
            await self.db_session.refresh(user_account_db,
                                          attribute_names=['user', 'group'] if user_account_db.group_id else ['user'])

        else:
            logger.error("Не надано ID рахунку або ID користувача для пошуку/створення рахунку.")
            raise ValueError("Необхідно вказати user_account_id або user_id_for_account_lookup.")  # i18n

        if not user_account_db:  # Додаткова перевірка після всіх гілок
            logger.error("Рахунок користувача не вдалося ідентифікувати або створити.")
            raise ValueError("Рахунок користувача не вдалося ідентифікувати або створити.")  # i18n

        logger.info(
            f"Обробка транзакції для Рахунку ID: {user_account_db.id}, Користувач ID: {user_account_db.user_id}")

        current_balance = Decimal(user_account_db.balance)
        transaction_amount = Decimal(transaction_data.amount)

        if transaction_amount.is_signed() and current_balance < abs(transaction_amount):  # Перевірка для від'ємних сум
            logger.warning(
                f"Недостатньо коштів на Рахунку ID '{user_account_db.id}'. "
                f"Поточний: {current_balance}, Спроба списання: {abs(transaction_amount)}."
            )
            raise InsufficientFundsError(current_balance=current_balance)  # i18n

        new_balance = current_balance + transaction_amount

        # Створення транзакції
        # balance_after_transaction розраховується тут, не береться з transaction_data
        new_transaction_db = AccountTransaction(
            user_account_id=user_account_db.id,
            transaction_type=transaction_data.transaction_type,
            amount=transaction_amount,
            balance_after_transaction=new_balance,  # Розрахований новий баланс
            description=transaction_data.description,
            related_entity_id=transaction_data.related_entity_id
            # created_at встановлюється автоматично
        )

        # Оновлення рахунку
        user_account_db.balance = new_balance
        user_account_db.last_transaction_at = datetime.now(timezone.utc)
        # updated_at оновлюється автоматично

        self.db_session.add(new_transaction_db)
        self.db_session.add(user_account_db)  # Додаємо оновлений рахунок до сесії

        try:
            if commit_session:
                await self.commit()
            else:
                # Якщо сесія не комітиться тут, зміни будуть передані викликаючому коду.
                # Flush потрібен, щоб ID для new_transaction_db та user_account_db були доступні.
                await self.db_session.flush([new_transaction_db, user_account_db])

            # Оновлюємо об'єкти з БД для отримання фінального стану (наприклад, з default значеннями БД)
            await self.db_session.refresh(new_transaction_db)  # Зазвичай не має глибоких зв'язків
            await self.db_session.refresh(user_account_db,
                                          attribute_names=['user', 'group'] if user_account_db.group_id else ['user'])


        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Помилка цілісності '{user_account_db.id}': {e}", exc_info=settings.DEBUG)
            raise ValueError(f"Не вдалося створити транзакцію: конфлікт даних.")  # i18n
        except SQLAlchemyError as e:  # Більш загальна помилка БД
            await self.rollback()
            logger.error(f"Помилка БД '{user_account_db.id}': {e}", exc_info=settings.DEBUG)
            raise ValueError(f"Помилка бази даних під час обробки транзакції.")  # i18n

        logger.info(
            f"Транзакція ID '{new_transaction_db.id}' успішно створена для Рахунку ID '{user_account_db.id}'. "
            f"Старий баланс: {current_balance}, Сума: {transaction_amount}, Новий баланс: {new_balance}."
        )

        return (
            AccountTransactionResponse.model_validate(new_transaction_db),
            UserAccountResponse.model_validate(user_account_db)
        )

    async def list_transactions_for_account(
            self,
            user_account_id: UUID,
            skip: int = 0,
            limit: int = 100,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None,
            transaction_type: Optional[str] = None
    ) -> List[AccountTransactionResponse]:
        """
        Перелічує транзакції для конкретного бонусного рахунку.

        :param user_account_id: ID рахунку користувача.
        :param skip: Кількість записів для пропуску.
        :param limit: Максимальна кількість записів.
        :param start_date: Фільтр за початковою датою.
        :param end_date: Фільтр за кінцевою датою.
        :param transaction_type: Фільтр за типом транзакції.
        :return: Список Pydantic схем AccountTransactionResponse.
        """
        logger.debug(
            f"Перелік транзакцій для рахунку ID: {user_account_id}, тип: {transaction_type}, "
            f"період: [{start_date}-{end_date}], пропустити={skip}, ліміт={limit}"
        )

        stmt = select(AccountTransaction).options(
            selectinload(AccountTransaction.user_account).options(
                selectinload(UserAccount.user).options(selectinload(User.user_type)),
                selectinload(UserAccount.group)  # Завжди намагаємось завантажити, SQLAlchemy впорається
            )
        ).where(AccountTransaction.user_account_id == user_account_id)

        if start_date:
            stmt = stmt.where(AccountTransaction.created_at >= start_date)
        if end_date:
            # Для включення транзакцій до кінця дня, якщо end_date не має часу
            if end_date.hour == 0 and end_date.minute == 0 and end_date.second == 0:
                end_date_inclusive = end_date + timedelta(days=1) - timedelta.resolution
            else:
                end_date_inclusive = end_date
            stmt = stmt.where(AccountTransaction.created_at <= end_date_inclusive)
        if transaction_type:
            stmt = stmt.where(AccountTransaction.transaction_type == transaction_type)

        # TODO: Згідно technical_task.txt, уточнити поля для сортування. За замовчуванням - за спаданням дати створення.
        stmt = stmt.order_by(AccountTransaction.created_at.desc()).offset(skip).limit(limit)

        transactions_db = (await self.db_session.execute(stmt)).scalars().unique().all()

        response_list = [AccountTransactionResponse.model_validate(t) for t in transactions_db]
        logger.info(f"Отримано {len(response_list)} транзакцій для рахунку ID '{user_account_id}'.")
        return response_list

    async def get_transaction_by_id(self, transaction_id: UUID) -> Optional[AccountTransactionResponse]:
        """
        Отримує конкретну транзакцію за її ID.

        :param transaction_id: ID транзакції.
        :return: Pydantic схема AccountTransactionResponse або None.
        """
        logger.debug(f"Спроба отримання транзакції за ID: {transaction_id}")

        stmt = select(AccountTransaction).options(
            selectinload(AccountTransaction.user_account).options(
                selectinload(UserAccount.user).options(selectinload(User.user_type)),
                selectinload(UserAccount.group)
            )
        ).where(AccountTransaction.id == transaction_id)

        transaction_db = (await self.db_session.execute(stmt)).scalar_one_or_none()

        if transaction_db:
            logger.info(f"Транзакцію з ID '{transaction_id}' знайдено.")
            return AccountTransactionResponse.model_validate(transaction_db)

        logger.info(f"Транзакцію з ID '{transaction_id}' не знайдено.")
        return None


logger.debug("AccountTransactionService клас визначено та завантажено.")
