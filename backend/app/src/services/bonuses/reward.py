# backend/app/src/services/bonuses/reward.py
# -*- coding: utf-8 -*-
"""
Сервіс для управління винагородами в бонусній системі.

Відповідає за створення, оновлення, видалення, отримання винагород
та обробку процесу їх отримання користувачами за бонусні бали.
"""
from typing import List, Optional
from decimal import Decimal
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from backend.app.src.services.base import BaseService
from backend.app.src.models.bonuses.reward import Reward
from backend.app.src.models.bonuses.user_reward_redemption import UserRewardRedemption
from backend.app.src.models.groups.group import Group
from backend.app.src.models.auth.user import User
from backend.app.src.core.dicts import TransactionType # Імпорт TransactionType Enum

from backend.app.src.schemas.bonuses.reward import (
    RewardCreate,
    RewardUpdate,
    RewardResponse,
    RedeemRewardRequest,
    UserRewardRedemptionResponse
)
# AccountTransactionCreate не використовується напряму цим сервісом
from backend.app.src.services.bonuses.account import UserAccountService
from backend.app.src.config.logging import get_logger
from backend.app.src.core.i18n import _
logger = get_logger(__name__)
from backend.app.src.config import settings
from backend.app.src.core.exceptions import RewardUnavailableError, RedemptionConditionError # Імпорт перенесених винятків


class RewardService(BaseService):
    """
    Сервіс для управління винагородами, які користувачі можуть отримати за бонусні бали.
    Обробляє CRUD для винагород та процес їх отримання.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        self.account_service = UserAccountService(db_session)  # Ініціалізація сервісу рахунків
        logger.info("RewardService ініціалізовано.")

    async def get_reward_by_id(self, reward_id: int) -> Optional[RewardResponse]: # reward_id змінено на int
        """
        Отримує винагороду за її ID, з завантаженими пов'язаними сутностями.

        :param reward_id: ID винагороди (int).
        :return: Pydantic схема RewardResponse або None, якщо не знайдено.
        """
        logger.debug(f"Спроба отримання винагороди за ID: {reward_id}")

        stmt = select(Reward).options(
            selectinload(Reward.group),
            selectinload(Reward.created_by_user).options(selectinload(User.user_type)),
            selectinload(Reward.updated_by_user).options(selectinload(User.user_type))
        ).where(Reward.id == reward_id)

        reward_db = (await self.db_session.execute(stmt)).scalar_one_or_none()

        if reward_db:
            logger.info(f"Винагороду з ID '{reward_id}' знайдено.")
            return RewardResponse.model_validate(reward_db)  # Pydantic v2
        logger.info(f"Винагороду з ID '{reward_id}' не знайдено.")
        return None

    async def create_reward(self, reward_data: RewardCreate, creator_user_id: int) -> RewardResponse: # creator_user_id змінено на int
        """
        Створює нову винагороду.

        :param reward_data: Дані для створення винагороди (Pydantic схема).
        :param creator_user_id: ID користувача (int), що створює винагороду.
        :return: Pydantic схема створеної RewardResponse.
        :raises ValueError: Якщо пов'язані сутності не знайдено або ім'я винагороди не унікальне. # i18n
        """
        logger.debug(f"Спроба створення нової винагороди '{reward_data.name}' користувачем ID: {creator_user_id}")

        if reward_data.group_id and not await self.db_session.get(Group, reward_data.group_id):
            raise ValueError(_("group.errors.not_found_by_id", id=reward_data.group_id))

        stmt_name_check = select(Reward.id).where(Reward.name == reward_data.name)
        scope_log_msg_key = "global_scope"
        scope_params = {}
        if reward_data.group_id:
            stmt_name_check = stmt_name_check.where(Reward.group_id == reward_data.group_id)
            scope_log_msg_key = "in_group_scope"
            scope_params = {"group_id": reward_data.group_id}
        else:
            stmt_name_check = stmt_name_check.where(Reward.group_id.is_(None))

        translated_scope_log_msg = _(scope_log_msg_key, **scope_params)

        if (await self.db_session.execute(stmt_name_check)).scalar_one_or_none():
            # Log can use more detailed, non-translated scope if needed for internal debugging
            logger.warning(f"Винагорода з ім'ям '{reward_data.name}' вже існує в {translated_scope_log_msg} (raw scope for log: group_id={reward_data.group_id}).")
            raise ValueError(_("reward.errors.name_exists_in_scope", name=reward_data.name, scope=translated_scope_log_msg))

        new_reward_db = Reward(
            **reward_data.model_dump(),  # Pydantic v2
            created_by_user_id=creator_user_id,
            updated_by_user_id=creator_user_id
            # created_at, updated_at - обробляються базовою моделлю або БД
        )

        self.db_session.add(new_reward_db)
        try:
            await self.commit()
            await self.db_session.refresh(new_reward_db,
                                          attribute_names=['group', 'created_by_user', 'updated_by_user'])
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Помилка цілісності '{reward_data.name}': {e}", exc_info=settings.DEBUG)
            raise ValueError(_("reward.errors.create_conflict", error_message=str(e)))
        except Exception as e:
            await self.rollback()
            logger.error(f"Неочікувана помилка '{reward_data.name}': {e}", exc_info=settings.DEBUG)
            raise

        logger.info(f"Винагорода '{new_reward_db.name}' (ID: {new_reward_db.id}) успішно створена.")
        return RewardResponse.model_validate(new_reward_db)

    async def update_reward(
            self, reward_id: int, reward_update_data: RewardUpdate, current_user_id: int # ID змінено на int
    ) -> Optional[RewardResponse]:
        """Оновлює існуючу винагороду."""
        logger.debug(f"Спроба оновлення винагороди ID: {reward_id} користувачем ID: {current_user_id}")
        reward_db = await self.db_session.get(Reward, reward_id)
        if not reward_db:
            logger.warning(f"Винагорода ID '{reward_id}' не знайдена для оновлення.")
            return None

        update_data = reward_update_data.model_dump(exclude_unset=True)  # Pydantic v2

        if 'group_id' in update_data and reward_db.group_id != update_data['group_id']:
            if update_data['group_id'] and not await self.db_session.get(Group, update_data['group_id']):
                raise ValueError(_("group.errors.not_found_by_id", id=update_data['group_id']))

        new_name = update_data.get('name', reward_db.name)
        new_group_id = update_data['group_id'] if 'group_id' in update_data else reward_db.group_id
        if ('name' in update_data and new_name != reward_db.name) or \
                ('group_id' in update_data and new_group_id != reward_db.group_id):
            stmt_name_check = select(Reward.id).where(Reward.name == new_name, Reward.id != reward_id)

            scope_log_msg_key = "global_scope"
            scope_params = {}
            if new_group_id is not None:
                stmt_name_check = stmt_name_check.where(Reward.group_id == new_group_id)
                scope_log_msg_key = "in_group_scope"
                scope_params = {"group_id": new_group_id}
            else:
                stmt_name_check = stmt_name_check.where(Reward.group_id.is_(None))

            translated_scope_log_msg = _(scope_log_msg_key, **scope_params)
            if (await self.db_session.execute(stmt_name_check)).scalar_one_or_none():
                raise ValueError(_("reward.errors.name_exists_in_scope", name=new_name, scope=translated_scope_log_msg))

        for field, value in update_data.items():
            setattr(reward_db, field, value)

        reward_db.updated_by_user_id = current_user_id
        reward_db.updated_at = datetime.now(timezone.utc)

        self.db_session.add(reward_db)
        try:
            await self.commit()
            await self.db_session.refresh(reward_db, attribute_names=['group', 'created_by_user', 'updated_by_user'])
            logger.info(f"Винагорода ID '{reward_id}' успішно оновлена.")
            return RewardResponse.model_validate(reward_db)
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Помилка цілісності ID '{reward_id}': {e}", exc_info=settings.DEBUG)
            raise ValueError(_("reward.errors.update_conflict", error_message=str(e)))
        except Exception as e:
            await self.rollback()
            logger.error(f"Помилка оновлення ID '{reward_id}': {e}", exc_info=settings.DEBUG)
            raise

    async def delete_reward(self, reward_id: int, current_user_id: int) -> bool: # ID змінено на int
        """Видаляє винагороду."""
        # TODO: Згідно `technical_task.txt`, чи є обмеження на видалення (напр., якщо є активні отримання)?
        logger.debug(f"Спроба видалення винагороди ID: {reward_id} користувачем: {current_user_id}")
        reward_db = await self.db_session.get(Reward, reward_id)
        if not reward_db:
            logger.warning(f"Винагорода ID '{reward_id}' не знайдена для видалення.")
            return False

        await self.db_session.delete(reward_db)
        await self.commit()
        logger.info(f"Винагорода ID '{reward_id}' видалена користувачем {current_user_id}.")
        return True

    async def list_rewards(
            self, group_id: Optional[int] = None, is_active: Optional[bool] = True, # group_id змінено на Optional[int]
            min_stock: Optional[int] = None, max_points_cost: Optional[Decimal] = None,
            valid_on_date: Optional[datetime] = None,
            skip: int = 0, limit: int = 100,
            include_global_if_group_given: bool = True
    ) -> List[RewardResponse]:
        """Перелічує винагороди з фільтрами та пагінацією."""
        logger.debug(
            f"Перелік винагород: group_id={group_id}, активні={is_active}, запас>={min_stock}, ціна<={max_points_cost}, валідні_на={valid_on_date}, глобальні_для_групи={include_global_if_group_given}")

        stmt = select(Reward).options(
            selectinload(Reward.group),
            selectinload(Reward.created_by_user).options(selectinload(User.user_type))
        )
        conditions = []
        if group_id is not None:
            if include_global_if_group_given:
                conditions.append(or_(Reward.group_id == group_id, Reward.group_id.is_(None)))
            else:
                conditions.append(Reward.group_id == group_id)
        # Якщо group_id не вказано, за замовчуванням показує всі (і глобальні, і групові).
        # Щоб показувати тільки глобальні, якщо group_id is None, потрібен окремий прапорець/логіка.

        if is_active is not None:
            # Припускаємо, що 'active' є рядковим представленням активного стану в полі 'state'
            conditions.append(Reward.state == "active" if is_active else Reward.state != "active")
        if min_stock is not None: conditions.append(Reward.stock_available >= min_stock) # type: ignore
        if max_points_cost is not None: conditions.append(Reward.points_cost <= max_points_cost) # type: ignore
        if valid_on_date:
            conditions.append(and_(
                or_(Reward.valid_from.is_(None), Reward.valid_from <= valid_on_date),
                or_(Reward.valid_until.is_(None), Reward.valid_until >= valid_on_date)
            ))

        if conditions: stmt = stmt.where(*conditions)

        # TODO: Згідно `technical_task.txt`, уточнити поля та напрямки сортування.
        # Можливі поля для сортування: name, points_cost, stock_available, valid_from, valid_until, created_at.
        # Потрібно реалізувати динамічне сортування аналогічно до UserService.list_users.
        stmt = stmt.order_by(Reward.points_cost, Reward.name).offset(skip).limit(limit)
        rewards_db = (await self.db_session.execute(stmt)).scalars().unique().all()
        return [RewardResponse.model_validate(r) for r in rewards_db]

    async def redeem_reward(
            self, user_id: int, reward_id: int, redeem_data: RedeemRewardRequest, # user_id, reward_id змінено на int
            group_id_context: Optional[int] = None # group_id_context змінено на Optional[int]
            # Група, в контексті якої користувач намагається отримати винагороду
    ) -> UserRewardRedemptionResponse:
        """Обробляє запит користувача на отримання винагороди."""
        logger.info(
            f"Користувач ID '{user_id}' намагається отримати винагороду ID '{reward_id}'. Кількість: {redeem_data.quantity}")

        reward_db = await self.db_session.get(Reward, reward_id)
        current_time = datetime.now(timezone.utc)

        # Перевірка доступності винагороди
        if not reward_db: raise RewardUnavailableError(_("reward.errors.unavailable.not_found"))
        if not reward_db.is_active: raise RewardUnavailableError(_("reward.errors.unavailable.inactive"))
        if reward_db.valid_from and reward_db.valid_from > current_time:
            raise RewardUnavailableError(_("reward.errors.unavailable.not_yet_available", date=reward_db.valid_from.isoformat()))
        if reward_db.valid_until and reward_db.valid_until < current_time:
            raise RewardUnavailableError(_("reward.errors.unavailable.expired", date=reward_db.valid_until.isoformat()))

        # Перевірка контексту групи
        if reward_db.group_id is not None and reward_db.group_id != group_id_context:
            raise RedemptionConditionError(_("reward.errors.redeem.unavailable_in_group_context"))

        # Визначення рахунку для списання: груповий (якщо винагорода групова) або глобальний
        account_to_use_group_id = reward_db.group_id  # Якщо винагорода групова, то і рахунок груповий
        # Якщо винагорода глобальна (reward_db.group_id is None), то group_id_context не важливий для вибору рахунку,
        # використовується глобальний рахунок користувача (де group_id is None).
        # Однак, якщо group_id_context надано, він може бути використаний для інших цілей (наприклад, логування).
        # Для вибору рахунку: якщо винагорода групова, використовуємо group_id винагороди.
        # Якщо винагорода глобальна, використовуємо глобальний рахунок користувача (group_id=None).

        user_account_orm = await self.account_service.get_or_create_user_account(user_id,
                                                                                 group_id=account_to_use_group_id)

        quantity_to_redeem = redeem_data.quantity
        if quantity_to_redeem <= 0: raise ValueError(_("reward.errors.redeem.quantity_must_be_positive"))

        if reward_db.stock_available is not None and reward_db.stock_available < quantity_to_redeem:
            raise RewardUnavailableError(
                _("reward.errors.unavailable.insufficient_stock", name=reward_db.name, available_stock=reward_db.stock_available))

        if reward_db.max_per_user is not None:
            stmt = select(func.sum(UserRewardRedemption.quantity)).where(
                UserRewardRedemption.user_id == user_id,
                UserRewardRedemption.reward_id == reward_id,
                UserRewardRedemption.status == "COMPLETED"  # Рахуємо тільки успішні
            )
            already_redeemed_count = (await self.db_session.execute(stmt)).scalar_one_or_none() or 0
            if (already_redeemed_count + quantity_to_redeem) > reward_db.max_per_user:
                raise RedemptionConditionError(
                    _("reward.errors.redeem.user_limit_exceeded", limit=reward_db.max_per_user, redeemed_count=already_redeemed_count))

        total_cost = Decimal(reward_db.points_cost) * quantity_to_redeem
        if Decimal(user_account_orm.balance) < total_cost:  # Баланс з ORM моделі
            # The InsufficientFundsError itself is already internationalized at its definition
            raise InsufficientFundsError(current_balance=user_account_orm.balance)

        try:
            # Списання балів через adjust_account_balance, який створює транзакцію
            _updated_account_resp, transaction_resp = await self.account_service.adjust_account_balance(
                user_id=user_id,
                group_id=account_to_use_group_id,  # Рахунок, з якого списуємо
                amount=-total_cost,
                transaction_type=TransactionType.REWARD_REDEMPTION,
                description=_("reward.transaction_description_redeemed", quantity=quantity_to_redeem, name=reward_db.name),
                related_entity_id=reward_id,
                commit_session=False  # Важливо! Комміт буде в кінці redeem_reward
            )

            if reward_db.stock_available is not None:
                reward_db.stock_available -= quantity_to_redeem
            reward_db.updated_at = datetime.now(timezone.utc)  # Оновлюємо час оновлення винагороди
            self.db_session.add(reward_db)

            redemption_record = UserRewardRedemption(
                user_id=user_id,
                reward_id=reward_id,
                user_account_id=user_account_orm.id,  # ID рахунку з ORM моделі
                transaction_id=transaction_resp.id,  # ID транзакції з відповіді adjust_account_balance
                quantity=quantity_to_redeem,
                points_spent=total_cost,
                status="COMPLETED",  # Статус за замовчуванням, може бути іншим згідно ТЗ
                redeemed_at=datetime.now(timezone.utc),
                notes=redeem_data.notes
            )
            self.db_session.add(redemption_record)

            await self.commit()  # Атомарний комміт всіх змін

            await self.db_session.refresh(redemption_record,
                                          attribute_names=['user', 'reward', 'account', 'transaction'])
            logger.info(f"Користувач ID '{user_id}' успішно отримав {quantity_to_redeem} винагороди ID '{reward_id}'.")
            return UserRewardRedemptionResponse.model_validate(redemption_record)
        except Exception as e:  # Широкий except для відкату транзакції
            await self.rollback()
            logger.error(f"Неочікувана помилка '{user_id}', винагорода ID '{reward_id}': {e}", exc_info=settings.DEBUG)
            # Перетворюємо на специфічну помилку або ре-рейзимо оригінальну, якщо вона вже підходяща
            if not isinstance(e, (RewardUnavailableError, RedemptionConditionError,
                                  InsufficientFundsError, ValueError)): # Updated to use direct import
                raise RuntimeError(_("reward.errors.redeem.internal_server_error"))
            raise


logger.debug("RewardService клас визначено та завантажено.")
