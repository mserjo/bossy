# backend/app/src/services/bonuses/reward_service.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає сервіс `RewardService` для управління нагородами.
"""
from typing import List, Optional
import uuid
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore

from backend.app.src.models.bonuses.reward import RewardModel
from backend.app.src.models.auth.user import UserModel
from backend.app.src.schemas.bonuses.reward import RewardCreateSchema, RewardUpdateSchema, RewardSchema
from backend.app.src.repositories.bonuses.reward import RewardRepository, reward_repository
from backend.app.src.repositories.groups.group import group_repository # Для перевірки групи
from backend.app.src.repositories.dictionaries.status import status_repository # Для статусу
from backend.app.src.repositories.dictionaries.bonus_type import bonus_type_repository # Для типу бонусу
from backend.app.src.services.base import BaseService
from backend.app.src.core.exceptions import NotFoundException, ForbiddenException, BadRequestException
from backend.app.src.core.constants import USER_TYPE_SUPERADMIN, STATUS_ACTIVE_CODE, TRANSACTION_TYPE_REWARD_PURCHASE
# from backend.app.src.services.groups.group_membership_service import group_membership_service
# from backend.app.src.services.bonuses.account_service import account_service # Для списання бонусів
# from backend.app.src.services.bonuses.transaction_service import transaction_service # Для створення транзакції

class RewardService(BaseService[RewardRepository]):
    """
    Сервіс для управління нагородами.
    """

    async def get_reward_by_id(self, db: AsyncSession, reward_id: uuid.UUID, include_details: bool = True) -> RewardModel:
        reward = None
        if include_details:
            reward = await self.repository.get_reward_with_details(db, reward_id=reward_id)
        else:
            reward = await self.repository.get(db, id=reward_id)

        if not reward:
            raise NotFoundException(f"Нагороду з ID {reward_id} не знайдено.")
        return reward

    async def create_reward(
        self, db: AsyncSession, *, obj_in: RewardCreateSchema, group_id: uuid.UUID, current_user: UserModel
    ) -> RewardModel:
        """
        Створює нову нагороду в групі.
        """
        # Перевірка прав: адмін групи або superuser
        from backend.app.src.services.groups.group_membership_service import group_membership_service # Відкладений імпорт
        if not await group_membership_service.is_user_group_admin(db, user_id=current_user.id, group_id=group_id) and \
           current_user.user_type_code != USER_TYPE_SUPERADMIN:
            raise ForbiddenException("Лише адміністратор групи може створювати нагороди.")

        # Перевірка існування групи
        group = await group_repository.get(db, id=group_id)
        if not group:
            raise NotFoundException(f"Групу з ID {group_id} не знайдено.")

        # Перевірка існування типу бонусу
        bonus_type = await bonus_type_repository.get_by_code(db, code=obj_in.bonus_type_code)
        if not bonus_type:
            raise BadRequestException(f"Тип бонусу з кодом '{obj_in.bonus_type_code}' не знайдено.")
        # TODO: Перевірити, чи цей bonus_type_code відповідає типу бонусів, налаштованому для групи.
        # group_settings = await group_settings_repository.get_by_group_id(db, group_id=group_id)
        # if not group_settings or group_settings.bonus_type.code != obj_in.bonus_type_code: # Потрібен зв'язок bonus_type в GroupSettingsModel
        #     raise BadRequestException("Тип бонусу нагороди не відповідає типу бонусів групи.")

        # Встановлення початкового статусу (якщо є)
        if obj_in.state_id:
            status = await status_repository.get(db, id=obj_in.state_id)
            if not status:
                raise BadRequestException(f"Статус з ID {obj_in.state_id} не знайдено.")
        else: # Встановити дефолтний активний статус
            active_status = await status_repository.get_by_code(db, code=STATUS_ACTIVE_CODE)
            if not active_status:
                 raise BadRequestException(f"Дефолтний активний статус '{STATUS_ACTIVE_CODE}' не знайдено.")
            # obj_in.state_id = active_status.id # Не можна змінювати obj_in після model_dump
            # Краще передати state_id в create_reward_in_group або встановити в моделі за замовчуванням.
            # Поки що, якщо state_id не передано, він буде None (якщо поле nullable).
            # Модель RewardModel успадковує state_id від BaseMainModel, де воно nullable.
            # Сервіс має забезпечити встановлення валідного state_id.
            # Я додам його до create_data.
            pass


        create_data = obj_in.model_dump(exclude_unset=True)
        if not obj_in.state_id and 'active_status' in locals() and active_status:
             create_data['state_id'] = active_status.id


        return await self.repository.create_reward_in_group(db, obj_in_data=create_data, group_id=group_id) # type: ignore

    async def update_reward(
        self, db: AsyncSession, *, reward_id: uuid.UUID, obj_in: RewardUpdateSchema, current_user: UserModel
    ) -> RewardModel:
        """Оновлює існуючу нагороду."""
        db_reward = await self.get_reward_by_id(db, reward_id=reward_id, include_details=False)

        # Перевірка прав
        from backend.app.src.services.groups.group_membership_service import group_membership_service
        if not await group_membership_service.is_user_group_admin(db, user_id=current_user.id, group_id=db_reward.group_id) and \
           current_user.user_type_code != USER_TYPE_SUPERADMIN:
            raise ForbiddenException("Ви не маєте прав оновлювати цю нагороду.")

        # Перевірка bonus_type_code, якщо він змінюється (хоча це рідко)
        update_data = obj_in.model_dump(exclude_unset=True)
        if "bonus_type_code" in update_data and update_data["bonus_type_code"] != db_reward.bonus_type_code:
            bonus_type = await bonus_type_repository.get_by_code(db, code=update_data["bonus_type_code"])
            if not bonus_type:
                raise BadRequestException(f"Новий тип бонусу з кодом '{update_data['bonus_type_code']}' не знайдено.")
            # TODO: Додаткова перевірка сумісності з групою.

        return await self.repository.update(db, db_obj=db_reward, obj_in=update_data) # obj_in тут є словником

    async def delete_reward(self, db: AsyncSession, *, reward_id: uuid.UUID, current_user: UserModel) -> RewardModel:
        """Видаляє нагороду (м'яке видалення)."""
        db_reward = await self.get_reward_by_id(db, reward_id=reward_id, include_details=False)

        # Перевірка прав
        from backend.app.src.services.groups.group_membership_service import group_membership_service
        if not await group_membership_service.is_user_group_admin(db, user_id=current_user.id, group_id=db_reward.group_id) and \
           current_user.user_type_code != USER_TYPE_SUPERADMIN:
            raise ForbiddenException("Ви не маєте прав видаляти цю нагороду.")

        deleted_reward = await self.repository.soft_delete(db, db_obj=db_reward) # type: ignore
        if not deleted_reward:
            raise NotImplementedError("М'яке видалення не підтримується або не вдалося для нагород.")
        return deleted_reward

    async def purchase_reward(
        self, db: AsyncSession, *, reward_id: uuid.UUID, current_user: UserModel
    ) -> Dict[str, Any]: # Повертає, наприклад, { "message": "...", "transaction_id": ... }
        """
        Обробляє "покупку" нагороди користувачем.
        - Перевіряє доступність нагороди (активна, кількість).
        - Перевіряє, чи користувач може її отримати (max_per_user).
        - Перевіряє баланс користувача.
        - Списує бонуси з рахунку користувача (створює транзакцію).
        - Зменшує кількість доступних нагород.
        """
        reward = await self.get_reward_by_id(db, reward_id=reward_id) # З деталями (bonus_type_details)

        # 1. Перевірка доступності нагороди
        if reward.is_deleted or reward.state.code != STATUS_ACTIVE_CODE: # Потрібен state
            raise BadRequestException("Нагорода наразі недоступна.")
        if reward.quantity_available is not None and reward.quantity_available <= 0:
            raise BadRequestException("Ця нагорода закінчилася.")

        # 2. Перевірка, чи користувач є членом групи
        from backend.app.src.services.groups.group_membership_service import group_membership_service
        membership = await group_membership_service.get_membership_by_user_and_group(db, user_id=current_user.id, group_id=reward.group_id)
        if not membership: # Або якщо членство неактивне
            raise ForbiddenException("Лише члени групи можуть отримувати нагороди цієї групи.")

        # 3. Перевірка max_per_user
        if reward.max_per_user is not None:
            # Потрібно підрахувати, скільки разів цей користувач вже отримував цю нагороду
            # Це можна зробити через аналіз транзакцій типу REWARD_PURCHASE для цього user_id та reward_id
            # TODO: Реалізувати підрахунок отриманих нагород.
            # purchased_count = await transaction_repository.count_user_reward_purchases(db, user_id=current_user.id, reward_id=reward.id)
            purchased_count = 0 # Заглушка
            if purchased_count >= reward.max_per_user:
                raise BadRequestException(f"Ви вже досягли ліміту ({reward.max_per_user}) для отримання цієї нагороди.")

        # 4. Перевірка балансу користувача
        from backend.app.src.services.bonuses.account_service import account_service # Відкладений імпорт
        user_account = await account_service.get_user_account_in_group(db, user_id=current_user.id, group_id=reward.group_id)

        if user_account.bonus_type_code != reward.bonus_type_code:
            raise BadRequestException(f"Невідповідність типів бонусів: рахунок в '{user_account.bonus_type_code}', нагорода в '{reward.bonus_type_code}'.")
        if user_account.balance < reward.cost_points:
            raise BadRequestException(f"Недостатньо бонусів для отримання нагороди. Потрібно: {reward.cost_points}, у вас: {user_account.balance} {user_account.bonus_type_code}.")

        # 5. Списання бонусів (через AccountService, який створить транзакцію)
        from backend.app.src.services.bonuses.transaction_service import transaction_service # Відкладений імпорт

        # `adjust_balance` в `AccountService` має бути змінений, щоб приймати `transaction_service`
        # або `TransactionService` має метод, що робить і те, і інше.
        # Поточний `AccountService.adjust_balance` приймає `transaction_service`.

        await account_service.adjust_balance(
            db,
            account_id=user_account.id,
            amount_change=-reward.cost_points, # Списання
            transaction_service=transaction_service,
            transaction_type_code=TRANSACTION_TYPE_REWARD_PURCHASE,
            description=f"Покупка нагороди: {reward.name}",
            source_entity_type="reward",
            source_entity_id=reward.id,
            created_by_user_id=current_user.id # Користувач, що ініціював покупку
        )

        # 6. Зменшення кількості доступних нагород
        if reward.quantity_available is not None:
            updated_reward = await self.repository.decrement_quantity_available(db, reward_obj=reward, quantity_to_decrement=1)
            if not updated_reward: # Малоймовірно, якщо попередня перевірка пройшла
                 self.logger.error(f"Не вдалося зменшити кількість для нагороди {reward.id} після покупки.")
                 # Тут може бути потрібна логіка компенсації, якщо це можливо.
                 # Або ж, це має бути одна транзакція БД.
                 # Поки що просто логуємо.

        # TODO: Відправити сповіщення користувачеві про успішну покупку.
        # TODO: Якщо нагорода потребує ручного виконання, створити завдання для адміна або сповіщення.

        return {
            "message": f"Нагороду '{reward.name}' успішно отримано!",
            # "transaction_id": created_transaction.id # Якщо transaction_service повертає створену транзакцію
        }


reward_service = RewardService(reward_repository)

# TODO: Реалізувати TODO в `create_reward` (перевірка відповідності bonus_type_code групи).
# TODO: Реалізувати TODO в `purchase_reward` (підрахунок отриманих нагород, сповіщення, завдання для адміна).
# TODO: Забезпечити атомарність операції `purchase_reward` (списання бонусів + зменшення кількості).
#       Це має відбуватися в одній транзакції бази даних.
#       Поточна реалізація `decrement_quantity_available` робить commit. Це потрібно змінити,
#       щоб commit був один на всю операцію `purchase_reward`.
#       Найкраще, якщо `decrement_quantity_available` не робить commit, а лише додає до сесії.
#
# Все виглядає як хороший початок для RewardService. Ключовий метод - `purchase_reward`.
# Перевірка прав, доступності, балансу. Інтеграція з AccountService та TransactionService.
