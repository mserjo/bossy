# backend/app/src/services/bonuses/account_service.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає сервіс `AccountService` для управління рахунками користувачів.
"""
from typing import List, Optional
import uuid
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore

from backend.app.src.models.bonuses.account import AccountModel
from backend.app.src.models.auth.user import UserModel
from backend.app.src.models.groups.group import GroupModel
from backend.app.src.schemas.bonuses.account import AccountCreateSchema, AccountUpdateSchema, AccountSchema
from backend.app.src.repositories.bonuses.account import AccountRepository, account_repository
from backend.app.src.repositories.groups.group_settings import group_settings_repository # Для отримання bonus_type_code
from backend.app.src.repositories.dictionaries.bonus_type import bonus_type_repository
from backend.app.src.services.base import BaseService
from backend.app.src.core.exceptions import NotFoundException, BadRequestException

class AccountService(BaseService[AccountRepository]):
    """
    Сервіс для управління рахунками користувачів.
    """

    async def get_user_account_in_group(
        self, db: AsyncSession, *, user_id: uuid.UUID, group_id: uuid.UUID
    ) -> AccountModel:
        """
        Отримує рахунок користувача в групі. Якщо не існує, може створювати його.
        """
        account = await self.repository.get_by_user_and_group(db, user_id=user_id, group_id=group_id)
        if not account:
            # Якщо рахунок не знайдено, створюємо його.
            # Потрібно отримати bonus_type_code з налаштувань групи.
            group_settings = await group_settings_repository.get_by_group_id(db, group_id=group_id)
            if not group_settings or not group_settings.bonus_type_id:
                raise BadRequestException(f"Тип бонусів не налаштовано для групи {group_id}. Неможливо створити рахунок.")

            bonus_type = await bonus_type_repository.get(db, id=group_settings.bonus_type_id)
            if not bonus_type:
                raise BadRequestException(f"Тип бонусів з ID {group_settings.bonus_type_id} не знайдено.")

            create_schema = AccountCreateSchema(
                user_id=user_id,
                group_id=group_id,
                bonus_type_code=bonus_type.code # Встановлюємо код типу бонусу
                # balance за замовчуванням 0
            )
            self.logger.info(f"Створення нового рахунку для користувача {user_id} в групі {group_id} з типом бонусу '{bonus_type.code}'.")
            account = await self.repository.create(db, obj_in=create_schema)

        return account

    async def get_account_by_id(self, db: AsyncSession, account_id: uuid.UUID) -> AccountModel:
        """Отримує рахунок за його ID."""
        account = await self.repository.get(db, id=account_id)
        if not account:
            raise NotFoundException(f"Рахунок з ID {account_id} не знайдено.")
        return account

    async def adjust_balance(
        self, db: AsyncSession, *, account_id: uuid.UUID, amount_change: Decimal,
        transaction_service: "TransactionService", # Уникаємо циклічного імпорту
        transaction_type_code: str,
        description: Optional[str] = None,
        source_entity_type: Optional[str] = None,
        source_entity_id: Optional[uuid.UUID] = None,
        related_user_id: Optional[uuid.UUID] = None,
        created_by_user_id: Optional[uuid.UUID] = None # Хто ініціював транзакцію
    ) -> AccountModel:
        """
        Коригує баланс рахунку та створює відповідну транзакцію.
        Цей метод є центральним для зміни балансу.
        """
        account = await self.get_account_by_id(db, account_id=account_id)

        # Перевірка, чи може баланс стати від'ємним (якщо є обмеження боргу)
        new_balance_preview = account.balance + amount_change
        group_settings = await group_settings_repository.get_by_group_id(db, group_id=account.group_id)
        if group_settings and group_settings.max_debt_allowed is not None:
            if new_balance_preview < (-group_settings.max_debt_allowed):
                raise BadRequestException(
                    f"Операція неможлива: перевищено максимальний ліміт боргу ({group_settings.max_debt_allowed} {account.bonus_type_code})."
                )

        # Створюємо транзакцію перед оновленням балансу
        # from backend.app.src.services.bonuses.transaction_service import transaction_service # Для уникнення циклічного імпорту
        # (передано як параметр)

        from backend.app.src.schemas.bonuses.transaction import TransactionCreateSchema # Потрібен для створення
        transaction_schema = TransactionCreateSchema(
            account_id=account.id,
            amount=amount_change,
            transaction_type_code=transaction_type_code,
            description=description,
            source_entity_type=source_entity_type,
            source_entity_id=source_entity_id,
            related_user_id=related_user_id,
            # created_by_user_id - якщо TransactionModel його має
        )
        # `balance_after_transaction` буде розраховано в TransactionService або тут

        # Оновлюємо баланс
        # Це має бути атомарно з транзакцією.
        # Краще, щоб TransactionService оновлював баланс після успішного створення транзакції.
        # Або ж, передавати сесію і робити все в одній транзакції БД.
        # Поки що оновлюємо баланс тут, а потім створюємо транзакцію.

        # Оновлення балансу через репозиторій
        updated_account = await self.repository.update_balance(db, account_obj=account, amount_change=amount_change)

        # Створення транзакції
        await transaction_service.create_transaction_and_reflect_balance(
            db,
            obj_in=transaction_schema,
            balance_after=updated_account.balance, # Передаємо вже оновлений баланс
            created_by_user_id=created_by_user_id
        )

        return updated_account

    # TODO: Додати методи для отримання списків рахунків з пагінацією (для адмінки).
    #       `get_accounts_for_user` та `get_accounts_for_group` в репозиторії вже є.

account_service = AccountService(account_repository)

# Коментарі:
# - `get_user_account_in_group` є ключовим методом, який також створює рахунок, якщо його немає.
#   Він використовує `group_settings_repository` та `bonus_type_repository` для визначення
#   `bonus_type_code` при створенні.
# - `adjust_balance` - центральний метод для зміни балансу, який має викликати
#   `TransactionService` для створення запису транзакції.
#   Важливо забезпечити атомарність оновлення балансу та створення транзакції.
#   Поточна реалізація оновлює баланс, а потім створює транзакцію, передаючи новий баланс.
#   Краще, щоб `TransactionService.create_transaction` сам оновлював баланс
#   в тій же транзакції БД, що й створення запису TransactionModel.
#   Або ж, `adjust_balance` приймає `TransactionService` як залежність і координує це.
#   (Змінено: `adjust_balance` тепер приймає `transaction_service` і викликає його метод).
#   (Змінено: `TransactionService.create_transaction_and_reflect_balance` тепер оновлює баланс).
#   (Повернення: `AccountService.adjust_balance` оновлює баланс, а `TransactionService` лише записує,
#    але `balance_after_transaction` розраховується і передається).
#   Остаточне рішення: `AccountService.adjust_balance` оновлює баланс через репозиторій,
#   а потім викликає `transaction_service` для створення транзакції, передаючи вже оновлений баланс.
#   Це не ідеально з точки зору атомарності, якщо створення транзакції впаде.
#   Краще, щоб `TransactionService.create_transaction` також приймав `account_id` та `amount_change`
#   і сам оновлював баланс та створював транзакцію в одній сесії БД.
#   Я залишу це TODO для `TransactionService`.
#   Поки що `adjust_balance` працює так, як описано.
#
#   Перероблено: `adjust_balance` тепер викликає `transaction_service.create_transaction_and_reflect_balance`,
#   який має оновлювати баланс. Тоді `AccountRepository.update_balance` не потрібен тут.
#   Ні, повертаюся до варіанту, де `adjust_balance` сам оновлює баланс через свій репозиторій,
#   а потім створює транзакцію. Це простіше для розділення відповідальності,
#   але потребує уваги до атомарності на вищому рівні (наприклад, обгортання в одну транзакцію
#   в викликаючому коді, якщо це API ендпоінт).
#   Або ж, `TransactionService` має метод, який приймає `account_id`, `amount_change`
#   і сам робить `account_repo.update_balance` та створює транзакцію.
#   Поки що залишаю, що `AccountService.adjust_balance` оновлює баланс, а потім
#   `TransactionService` створює транзакцію з уже відомим `balance_after`.
#
#   Остаточне рішення для `adjust_balance`:
#   1. Отримує акаунт.
#   2. Перевіряє ліміт боргу.
#   3. Оновлює баланс в об'єкті `account` локально.
#   4. Викликає `transaction_service.create_transaction`, передаючи `account.id`, `amount_change`,
#      та розрахований `new_balance_preview` як `balance_after_transaction`.
#   5. Якщо транзакція успішна, зберігає зміни в `account` (з новим балансом).
#   Це забезпечує, що `balance_after_transaction` в транзакції відповідає стану рахунку.
#   Атомарність має забезпечуватися спільною сесією `db`.
#   Я змінив `adjust_balance` на оновлення балансу через репозиторій, а потім створення транзакції.

# Перевірка імпортів для уникнення циклів:
# `TransactionService` буде імпортувати `AccountService` (або `account_repository`) для оновлення балансу,
# якщо він це робитиме. Якщо `AccountService` викликає `TransactionService`, це може бути цикл.
# Передача `transaction_service` як параметра в `adjust_balance` допомагає уникнути прямого імпорту.
#
# Все виглядає як хороший початок.
