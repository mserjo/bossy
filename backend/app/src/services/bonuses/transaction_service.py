# backend/app/src/services/bonuses/transaction_service.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає сервіс `TransactionService` для управління транзакціями.
"""
from typing import List, Optional, Union, Dict, Any
import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore

from backend.app.src.models.bonuses.transaction import TransactionModel
from backend.app.src.models.auth.user import UserModel # Для created_by_user_id
from backend.app.src.schemas.bonuses.transaction import TransactionCreateSchema, TransactionSchema
from backend.app.src.repositories.bonuses.transaction import TransactionRepository, transaction_repository
from backend.app.src.repositories.bonuses.account import account_repository # Для перевірки рахунку
from backend.app.src.services.base import BaseService
from backend.app.src.core.exceptions import NotFoundException, BadRequestException

class TransactionService(BaseService[TransactionRepository]):
    """
    Сервіс для управління транзакціями.
    Основна відповідальність - створення транзакцій. Оновлення/видалення зазвичай не передбачено.
    """

    async def get_transaction_by_id(self, db: AsyncSession, transaction_id: uuid.UUID) -> TransactionModel:
        transaction = await self.repository.get(db, id=transaction_id)
        if not transaction:
            raise NotFoundException(f"Транзакцію з ID {transaction_id} не знайдено.")
        return transaction

    async def create_transaction_and_reflect_balance(
        self, db: AsyncSession, *,
        obj_in: TransactionCreateSchema,
        created_by_user_id: Optional[uuid.UUID] = None # Користувач, що ініціював дію (якщо є)
        # balance_after не передається, розраховується тут або береться з оновленого рахунку.
    ) -> TransactionModel:
        """
        Створює транзакцію та оновлює баланс відповідного рахунку.
        Цей метод має бути атомарним.
        """
        # 1. Перевірити існування рахунку
        account = await account_repository.get(db, id=obj_in.account_id)
        if not account:
            raise NotFoundException(f"Рахунок з ID {obj_in.account_id} для транзакції не знайдено.")

        # 2. Перевірити ліміт боргу, якщо сума від'ємна
        new_balance_preview = account.balance + obj_in.amount
        # Потрібен доступ до налаштувань групи
        from backend.app.src.repositories.groups.group_settings import group_settings_repository
        group_settings = await group_settings_repository.get_by_group_id(db, group_id=account.group_id)

        if obj_in.amount < 0 and group_settings and group_settings.max_debt_allowed is not None:
            if new_balance_preview < (-group_settings.max_debt_allowed):
                raise BadRequestException(
                    f"Операція неможлива: перевищено максимальний ліміт боргу ({group_settings.max_debt_allowed} {account.bonus_type_code})."
                )

        # 3. Оновити баланс рахунку
        account.balance = new_balance_preview
        # `updated_at` для рахунку оновиться автоматично
        # `created_by_user_id` та `updated_by_user_id` для рахунку (якщо є) - окреме питання.
        db.add(account)
        # Поки що не робимо commit для рахунку, щоб транзакція була атомарною.

        # 4. Створити запис транзакції
        # `created_by_user_id` для транзакції (якщо модель його має)
        # Модель TransactionModel успадковує created_by_user_id з BaseModel.
        obj_in_data = obj_in.model_dump(exclude_unset=True)

        # Створюємо об'єкт моделі транзакції
        db_transaction = self.repository.model(
            **obj_in_data,
            balance_after_transaction=new_balance_preview,
            created_by_user_id=created_by_user_id # Встановлюємо, хто ініціював
        )
        db.add(db_transaction)

        # 5. Застосувати зміни (commit) для обох операцій
        try:
            await db.commit()
            await db.refresh(account)
            await db.refresh(db_transaction)
        except Exception as e:
            await db.rollback()
            self.logger.error(f"Помилка при створенні транзакції та оновленні балансу: {e}")
            raise BadRequestException(f"Не вдалося виконати операцію з бонусами: {e}")

        return db_transaction


    async def get_transactions_for_account_paginated(
        self, db: AsyncSession, *,
        account_id: uuid.UUID,
        page: int = 1, size: int = 20, # Стандартні параметри пагінації
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        transaction_type_code: Optional[str] = None
    ) -> PaginatedResponse[TransactionModel]: # type: ignore
        """
        Отримує історію транзакцій для рахунку з пагінацією.
        """
        # Перевірка існування рахунку
        account = await account_repository.get(db, id=account_id)
        if not account:
            raise NotFoundException(f"Рахунок з ID {account_id} не знайдено.")

        # Формуємо фільтри для репозиторію
        filters: Dict[str, Any] = {"account_id": account_id}
        if date_from:
            filters["created_at__ge"] = date_from # Припускаючи, що BaseRepository підтримує __ge
        if date_to:
            from datetime import timedelta
            filters["created_at__lt"] = date_to + timedelta(days=1)
        if transaction_type_code:
            filters["transaction_type_code"] = transaction_type_code

        # Порядок сортування
        order_by = ["-created_at"] # Новіші спочатку

        # Використовуємо get_paginated з BaseRepository
        # Потрібно, щоб BaseRepository._apply_filters підтримував суфікси __ge, __lt
        # Поки що він підтримує лише рівність. Тому ця реалізація не зовсім точна.
        # Краще передати фільтри, які BaseRepository розуміє, або розширити його.
        #
        # Або ж, використовувати кастомний метод в TransactionRepository, який вже є:
        # `get_transactions_for_account`
        # Але він не повертає `PaginatedResponse`.
        #
        # Поки що, для демонстрації, припустимо, що `get_paginated` може працювати з простими фільтрами,
        # а для складних (діапазони дат) потрібна доробка `BaseRepository._apply_filters`.
        #
        # Альтернатива: отримати всі транзакції і зробити пагінацію в пам'яті (погано для великих об'ємів).
        # Або ж, `TransactionRepository` має мати свій `get_paginated_for_account`.

        # Для простоти, поки що викликаємо існуючий метод репозиторію без точної пагінації,
        # якщо фільтри по даті не підтримуються напряму в BaseRepository.get_paginated.
        # Або ж, реалізуємо логіку пагінації тут.

        # Реалізація пагінації тут:
        count_statement = select(func.count(self.repository.model.id)).where( # type: ignore
            self.repository.model.account_id == account_id
        )
        # Додаємо фільтри до count_statement
        if date_from: count_statement = count_statement.where(self.repository.model.created_at >= date_from) # type: ignore
        if date_to: count_statement = count_statement.where(self.repository.model.created_at < (date_to + timedelta(days=1))) # type: ignore
        if transaction_type_code: count_statement = count_statement.where(self.repository.model.transaction_type_code == transaction_type_code)

        total_items = (await db.execute(count_statement)).scalar_one()

        total_pages = (total_items + size - 1) // size if total_items > 0 else 0
        if page < 1: page = 1
        if page > total_pages and total_pages > 0: page = total_pages
        skip = (page - 1) * size

        items = await self.repository.get_transactions_for_account(
            db, account_id=account_id, skip=skip, limit=size,
            date_from=date_from, date_to=date_to, transaction_type_code=transaction_type_code
        )

        return PaginatedResponse(
            total=total_items,
            page=page,
            size=len(items), # Реальний розмір поточної сторінки
            pages=total_pages,
            items=items
        )

transaction_service = TransactionService(transaction_repository)

# TODO: Переконатися, що `TransactionCreateSchema` коректно визначена.
#       Вона має містити `account_id`, `amount`, `transaction_type_code` та опціональні поля.
#       `balance_after_transaction` та `created_by_user_id` встановлюються сервісом.
#
# TODO: Покращити логіку пагінації в `get_transactions_for_account_paginated`,
#       особливо якщо `BaseRepository._apply_filters` не підтримує діапазони дат.
#       Поточна реалізація робить окремий запит для підрахунку.
#
# TODO: Розглянути випадки, коли транзакція може бути не пов'язана з `created_by_user_id`
#       (наприклад, системні нарахування). У цьому випадку `created_by_user_id` буде `None`.
#
# Все виглядає як хороший початок для TransactionService.
# Ключовий метод `create_transaction_and_reflect_balance` забезпечує атомарність
# створення транзакції та оновлення балансу рахунку.
# Перевірка ліміту боргу також важлива.
# Логіка фільтрації та пагінації для історії транзакцій.
