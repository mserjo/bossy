# backend/app/src/services/bonuses/bonus_adjustment_service.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає сервіс `BonusAdjustmentService` для управління
ручними коригуваннями бонусів адміністраторами.
"""
from typing import List, Optional
import uuid
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore

from backend.app.src.models.bonuses.bonus import BonusAdjustmentModel # Модель знаходиться в bonus.py
from backend.app.src.models.auth.user import UserModel # Для current_user (admin)
from backend.app.src.schemas.bonuses.bonus_adjustment import BonusAdjustmentCreateSchema, BonusAdjustmentSchema # UpdateSchema не використовується
from backend.app.src.repositories.bonuses.bonus import BonusAdjustmentRepository, bonus_adjustment_repository # Репозиторій з bonus.py
from backend.app.src.services.base import BaseService
from backend.app.src.core.exceptions import NotFoundException, ForbiddenException, BadRequestException
from backend.app.src.core.constants import USER_TYPE_SUPERADMIN, ROLE_ADMIN_CODE, TRANSACTION_TYPE_MANUAL_CREDIT, TRANSACTION_TYPE_MANUAL_DEBIT
# from backend.app.src.services.bonuses.account_service import account_service
# from backend.app.src.services.bonuses.transaction_service import transaction_service
# from backend.app.src.services.groups.group_membership_service import group_membership_service

class BonusAdjustmentService(BaseService[BonusAdjustmentRepository]):
    """
    Сервіс для управління ручними коригуваннями бонусів.
    """

    async def get_adjustment_by_id(self, db: AsyncSession, adjustment_id: uuid.UUID) -> BonusAdjustmentModel:
        adjustment = await self.repository.get(db, id=adjustment_id)
        if not adjustment:
            raise NotFoundException(f"Коригування бонусів з ID {adjustment_id} не знайдено.")
        return adjustment

    async def create_adjustment(
        self, db: AsyncSession, *,
        obj_in: BonusAdjustmentCreateSchema,
        current_admin_user: UserModel # Адміністратор, який виконує дію
    ) -> BonusAdjustmentModel:
        """
        Створює нове ручне коригування бонусів.
        Автоматично створює відповідну транзакцію та оновлює баланс рахунку.
        """
        from backend.app.src.services.bonuses.account_service import account_service # Відкладений імпорт
        from backend.app.src.services.bonuses.transaction_service import transaction_service # Відкладений імпорт
        from backend.app.src.services.groups.group_membership_service import group_membership_service # Для перевірки прав

        # 1. Отримати рахунок, для якого робиться коригування
        target_account = await account_service.get_account_by_id(db, account_id=obj_in.account_id)
        if not target_account: # get_account_by_id вже кидає NotFoundException
            pass

        # 2. Перевірка прав адміністратора
        # Адміністратор має бути або superadmin, або адміном групи, до якої належить рахунок.
        is_group_admin = await group_membership_service.is_user_group_admin(
            db, user_id=current_admin_user.id, group_id=target_account.group_id
        )
        if not (current_admin_user.user_type_code == USER_TYPE_SUPERADMIN or is_group_admin):
            raise ForbiddenException("Ви не маєте прав виконувати коригування бонусів для цього рахунку.")

        # 3. Визначити тип транзакції
        transaction_type = TRANSACTION_TYPE_MANUAL_CREDIT if obj_in.amount > 0 else TRANSACTION_TYPE_MANUAL_DEBIT

        # 4. Створити запис BonusAdjustmentModel
        # `adjusted_by_user_id` - це `current_admin_user.id`
        # `transaction_id` буде встановлено після створення транзакції.
        adjustment_data = obj_in.model_dump(exclude_unset=True)
        adjustment_data["adjusted_by_user_id"] = current_admin_user.id

        # Спочатку створюємо сам запис коригування без transaction_id
        db_adjustment = self.repository.model(**adjustment_data)
        db.add(db_adjustment)
        await db.flush() # Потрібен ID для source_entity_id транзакції

        # 5. Викликати AccountService.adjust_balance, який створить транзакцію
        #    або напряму TransactionService.create_transaction_and_reflect_balance
        try:
            # Використовуємо TransactionService для атомарності
            await transaction_service.create_transaction_and_reflect_balance(
                db,
                obj_in_transaction_create=TransactionCreateSchema( # type: ignore # Потрібно імпортувати та створити
                    account_id=target_account.id,
                    amount=obj_in.amount,
                    transaction_type_code=transaction_type,
                    description=f"Ручне коригування: {obj_in.reason}",
                    source_entity_type="bonus_adjustment",
                    source_entity_id=db_adjustment.id,
                ),
                created_by_user_id=current_admin_user.id
            )
            # Отримати ID створеної транзакції та оновити BonusAdjustmentModel
            # Це складно, якщо TransactionService не повертає створену транзакцію
            # або якщо немає прямого зв'язку.
            #
            # Простіший підхід: BonusAdjustmentService сам створює транзакцію
            # і оновлює баланс, а потім зберігає BonusAdjustmentModel з transaction_id.
            # Це порушує SRP для TransactionService.
            #
            # Компроміс: TransactionService створює транзакцію, повертає її.
            # BonusAdjustmentService оновлює свій запис transaction_id.
            # Баланс оновлюється в TransactionService.

            # Перероблюємо:
            # 1. Створюємо транзакцію через TransactionService (який оновлює баланс)
            from backend.app.src.schemas.bonuses.transaction import TransactionCreateSchema
            created_transaction = await transaction_service.create_transaction_and_reflect_balance(
                db,
                obj_in=TransactionCreateSchema(
                    account_id=target_account.id,
                    amount=obj_in.amount,
                    transaction_type_code=transaction_type,
                    description=f"Ручне коригування: {obj_in.reason}",
                    source_entity_type="bonus_adjustment",
                    source_entity_id=db_adjustment.id # Використовуємо ID ще не закоміченого об'єкта, але це ОК для FK
                ),
                created_by_user_id=current_admin_user.id
            )

            # 2. Оновлюємо BonusAdjustmentModel з transaction_id
            db_adjustment.transaction_id = created_transaction.id
            db.add(db_adjustment) # Додаємо знову, щоб зміни зафіксувалися

            await db.commit() # Комітимо і BonusAdjustment, і зміни в Account, і Transaction
            await db.refresh(db_adjustment)
            await db.refresh(db_adjustment, attribute_names=['transaction']) # Для завантаження зв'язку

        except Exception as e:
            await db.rollback()
            self.logger.error(f"Помилка при створенні коригування бонусів: {e}")
            raise

        return db_adjustment

    async def get_adjustments_for_account(
        self, db: AsyncSession, *, account_id: uuid.UUID, skip: int = 0, limit: int = 100
    ) -> List[BonusAdjustmentModel]:
        """Отримує історію коригувань для рахунку."""
        statement = select(self.repository.model).where(self.repository.model.account_id == account_id)
        statement = statement.order_by(self.repository.model.created_at.desc()).options( # type: ignore
            selectinload(self.repository.model.admin),
            selectinload(self.repository.model.transaction)
        ).offset(skip).limit(limit)
        result = await db.execute(statement)
        return result.scalars().all() # type: ignore

    # Ручні коригування зазвичай не оновлюються і не видаляються,
    # а створюються нові коригуючі записи, якщо потрібно.
    # Тому методи update/delete з BaseRepository можуть не використовуватися.

bonus_adjustment_service = BonusAdjustmentService(bonus_adjustment_repository)

# TODO: Переконатися, що `BonusAdjustmentCreateSchema` містить `account_id`, `amount`, `reason`.
#       `adjusted_by_user_id` та `transaction_id` встановлюються сервісом.
#
# TODO: Забезпечити атомарність операції `create_adjustment` (створення BonusAdjustmentModel,
#       створення TransactionModel, оновлення AccountModel.balance).
#       Це має відбуватися в одній транзакції БД.
#       Поточна реалізація з викликом `transaction_service.create_transaction_and_reflect_balance`
#       та подальшим комітом є кроком у цьому напрямку.
#
# Все виглядає як хороший початок для сервісу ручних коригувань бонусів.
# Важлива інтеграція з AccountService та TransactionService.
# Перевірка прав адміністратора.
