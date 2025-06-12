# backend/app/src/services/groups/invitation.py
# import logging # Замінено на централізований логер
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

# Повні шляхи імпорту
from backend.app.src.services.base import BaseService
from backend.app.src.models.groups.invitation import GroupInvitation  # Модель SQLAlchemy GroupInvitation
from backend.app.src.models.groups.group import Group  # Для контексту групи
from backend.app.src.models.auth.user import User  # Для запрошеного користувача та того, хто запрошує
from backend.app.src.models.dictionaries.user_roles import UserRole  # Для ролі, яка буде призначена при прийнятті
from backend.app.src.models.groups.membership import GroupMembership  # Для перевірки існуючого членства

from backend.app.src.schemas.groups.invitation import (  # Схеми Pydantic
    GroupInvitationCreate,
    GroupInvitationResponse,
    # GroupInvitationAccept # Не використовується як тип параметра, код передається напряму
)
from backend.app.src.schemas.groups.membership import GroupMembershipResponse  # Для типу повернення accept_invitation
from backend.app.src.services.groups.membership import GroupMembershipService  # Для додавання користувача до групи

from backend.app.src.config.logging import logger  # Централізований логер
from backend.app.src.config import settings  # Для доступу до конфігурацій

# Термін дії запрошення за замовчуванням (наприклад, 7 днів)
# TODO: Перенести DEFAULT_INVITATION_EXPIRE_DAYS до settings.py
DEFAULT_INVITATION_EXPIRE_DAYS = getattr(settings, 'DEFAULT_INVITATION_EXPIRE_DAYS', 7)


class GroupInvitationService(BaseService):
    """
    Сервіс для управління запрошеннями до груп.
    Обробляє створення, прийняття, відхилення, відкликання та перелік запрошень.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        self.membership_service = GroupMembershipService(db_session)  # Ініціалізація сервісу членства
        logger.info("GroupInvitationService ініціалізовано.")

    async def _get_orm_invitation_with_relations(self, invitation_id: Optional[UUID] = None,
                                                 invitation_code: Optional[str] = None) -> Optional[GroupInvitation]:
        """Внутрішній метод для отримання ORM моделі GroupInvitation з усіма зв'язками."""
        if not invitation_id and not invitation_code:
            return None

        stmt = select(GroupInvitation).options(
            selectinload(GroupInvitation.group),
            selectinload(GroupInvitation.inviter).options(selectinload(User.user_type)),
            selectinload(GroupInvitation.invited_user).options(selectinload(User.user_type)),
            selectinload(GroupInvitation.role_to_assign)
        )
        if invitation_id:
            stmt = stmt.where(GroupInvitation.id == invitation_id)
        elif invitation_code:  # Додано можливість пошуку за кодом
            stmt = stmt.where(GroupInvitation.invitation_code == invitation_code)

        return (await self.db_session.execute(stmt)).scalar_one_or_none()

    async def create_invitation(
            self,
            group_id: UUID,
            inviter_user_id: UUID,
            role_to_assign_code: str,  # Код ролі для призначення користувачеві при вступі
            invite_data: GroupInvitationCreate  # Містить опціональний email, кастомний термін дії
    ) -> GroupInvitationResponse:
        """
        Створює нове запрошення для користувача приєднатися до групи.

        :param group_id: ID групи, до якої запрошують.
        :param inviter_user_id: ID користувача, який створює запрошення (має бути адміном/авторизованим).
        :param role_to_assign_code: Код ролі, яку отримає запрошений користувач.
        :param invite_data: Додаткові дані, такі як цільовий email або кастомний термін дії.
        :return: Pydantic схема GroupInvitationResponse створеного запрошення.
        :raises ValueError: Якщо групу, запрошуючого, роль не знайдено, або користувач вже член/запрошений. # i18n
        """
        logger.debug(f"Спроба створення запрошення до групи ID '{group_id}' користувачем ID '{inviter_user_id}'.")

        group = await self.db_session.get(Group, group_id)
        if not group: raise ValueError(f"Групу з ID '{group_id}' не знайдено.")  # i18n

        # Перевірка прав запрошуючого (має бути адміном групи або суперюзером) - логіка API шару
        # Тут припускаємо, що перевірка вже пройдена.

        inviter = await self.db_session.get(User, inviter_user_id)
        if not inviter: raise ValueError(f"Користувача, що запрошує, з ID '{inviter_user_id}' не знайдено.")  # i18n

        role_to_assign = (await self.db_session.execute(
            select(UserRole).where(UserRole.code == role_to_assign_code)
        )).scalar_one_or_none()
        if not role_to_assign: raise ValueError(f"Роль з кодом '{role_to_assign_code}' не знайдено.")  # i18n

        invited_user_id: Optional[UUID] = None
        normalized_email: Optional[str] = None
        if invite_data.email:
            normalized_email = invite_data.email.lower()
            invited_user = (await self.db_session.execute(
                select(User).where(User.email == normalized_email)
            )).scalar_one_or_none()
            if invited_user:
                invited_user_id = invited_user.id
                active_member_id = (await self.db_session.execute(
                    select(GroupMembership.id).where(
                        GroupMembership.group_id == group_id,
                        GroupMembership.user_id == invited_user_id,
                        GroupMembership.is_active == True
                    )
                )).scalar_one_or_none()
                if active_member_id:
                    # i18n
                    raise ValueError(
                        f"Користувач з email '{normalized_email}' вже є активним членом групи '{group.name}'.")

            # Перевірка на існуюче активне запрошення для цього email/користувача до цієї групи
            conditions = [
                GroupInvitation.group_id == group_id,
                GroupInvitation.status == "pending",
                GroupInvitation.expires_at > datetime.now(timezone.utc)
            ]
            email_condition = GroupInvitation.email == normalized_email
            user_id_condition = GroupInvitation.invited_user_id == invited_user_id if invited_user_id else False  # type: ignore
            conditions.append(or_(email_condition, user_id_condition))

            if (await self.db_session.execute(select(GroupInvitation.id).where(*conditions))).scalar_one_or_none():
                # i18n
                raise ValueError(
                    f"Активне запрошення для '{normalized_email or f'користувача ID {invited_user_id}'}' до групи '{group.name}' вже існує.")

        invitation_code = str(uuid4())  # Унікальний код запрошення
        expire_duration_days = invite_data.custom_expire_days if invite_data.custom_expire_days is not None \
            else DEFAULT_INVITATION_EXPIRE_DAYS
        expires_at = datetime.now(timezone.utc) + timedelta(days=expire_duration_days)

        new_invitation_db = GroupInvitation(
            group_id=group_id,
            inviter_user_id=inviter_user_id,
            invited_user_id=invited_user_id,  # Може бути None, якщо запрошення не на конкретного користувача
            email=normalized_email,  # Може бути None
            role_id_to_assign=role_to_assign.id,
            invitation_code=invitation_code,
            status="pending",  # Початковий статус
            expires_at=expires_at
            # created_at, updated_at встановлюються автоматично
        )
        self.db_session.add(new_invitation_db)
        try:
            await self.commit()
            refreshed_invitation = await self._get_orm_invitation_with_relations(invitation_id=new_invitation_db.id)
            if not refreshed_invitation:  # Малоймовірно
                # i18n
                raise RuntimeError("Критична помилка: не вдалося отримати створене запрошення після збереження.")
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Помилка цілісності при створенні запрошення до групи ID '{group_id}': {e}",
                         exc_info=settings.DEBUG)
            # i18n
            raise ValueError(f"Не вдалося створити запрошення через конфлікт даних: {e}")

        logger.info(f"Запрошення з кодом '{invitation_code}' до групи ID '{group_id}' успішно створено.")
        return GroupInvitationResponse.model_validate(refreshed_invitation)  # Pydantic v2

    async def get_invitation_by_code(self, invitation_code: str) -> Optional[GroupInvitationResponse]:
        """Отримує запрошення за його унікальним кодом, якщо воно дійсне (в очікуванні та не прострочене)."""
        logger.debug(f"Спроба отримання запрошення за кодом: {invitation_code}")

        invitation_db = await self._get_orm_invitation_with_relations(invitation_code=invitation_code)

        if invitation_db:
            # Додаткова перевірка статусу та терміну дії тут, хоча _get_orm_invitation_with_relations може це робити
            if invitation_db.status == "pending" and invitation_db.expires_at > datetime.now(timezone.utc):
                logger.info(f"Дійсне активне запрошення знайдено за кодом '{invitation_code}'.")
                return GroupInvitationResponse.model_validate(invitation_db)  # Pydantic v2
            else:
                logger.warning(
                    f"Запрошення за кодом '{invitation_code}' знайдено, але воно не активне (статус: {invitation_db.status}, термін дії: {invitation_db.expires_at}).")
                return None  # Повертаємо None, якщо не відповідає критеріям "дійсного для прийняття"

        logger.warning(
            f"Дійсне активне запрошення за кодом '{invitation_code}' не знайдено. Можливо, недійсне, прострочене або вже використане.")
        return None

    async def accept_invitation(
            self, invitation_code: str, accepting_user_id: UUID
    ) -> GroupMembershipResponse:
        """
        Обробляє прийняття запрошення користувачем.
        Змінює статус запрошення та додає користувача до групи.
        Операція має бути атомарною.
        """
        logger.info(f"Користувач ID '{accepting_user_id}' намагається прийняти запрошення з кодом '{invitation_code}'.")

        # Отримуємо повний об'єкт запрошення для оновлення статусу
        invitation_db_record = await self._get_orm_invitation_with_relations(invitation_code=invitation_code)

        if not invitation_db_record:
            # i18n
            raise ValueError("Запрошення не знайдено.")
        if invitation_db_record.status != "pending":
            # i18n
            raise ValueError("Запрошення вже не активне (статус: {invitation_db_record.status}).")
        if invitation_db_record.expires_at <= datetime.now(timezone.utc):
            # i18n
            raise ValueError("Термін дії запрошення закінчився.")

        accepting_user = await self.db_session.get(User, accepting_user_id)
        if not accepting_user:
            # i18n
            raise ValueError("Користувача, що приймає запрошення, не знайдено.")

        # Перевірка відповідності користувача запрошенню
        if invitation_db_record.invited_user_id and invitation_db_record.invited_user_id != accepting_user_id:
            # i18n
            raise ValueError("Це запрошення призначене для іншого користувача.")
        if invitation_db_record.email and invitation_db_record.email.lower() != accepting_user.email.lower():
            # i18n
            raise ValueError("Це запрошення було надіслано на іншу адресу електронної пошти.")

        # Якщо запрошення не було прив'язане до конкретного user_id, оновлюємо його
        if not invitation_db_record.invited_user_id:
            invitation_db_record.invited_user_id = accepting_user_id

        invitation_db_record.status = "accepted"
        invitation_db_record.accepted_at = datetime.now(timezone.utc)
        invitation_db_record.responded_at = invitation_db_record.accepted_at  # Час відповіді = час прийняття
        self.db_session.add(invitation_db_record)

        if not invitation_db_record.role_to_assign:  # Мало бути завантажено
            # i18n
            raise RuntimeError("Внутрішня помилка: не вдалося визначити роль для призначення.")

        # Додавання користувача до групи. `add_member_to_group` має обробляти можливе існуюче неактивне членство.
        # `add_member_to_group` також повинен обробляти коміт або приймати параметр `commit_session=False`.
        # Для атомарності, тут ми не робимо коміт до успішного додавання члена.
        try:
            # Передаємо db_session, щоб membership_service використовував ту саму транзакцію
            new_membership = await self.membership_service.add_member_to_group(
                group_id=invitation_db_record.group_id,
                user_id=accepting_user_id,
                role_code=invitation_db_record.role_to_assign.code,
                added_by_user_id=invitation_db_record.inviter_user_id,
                commit_session=False  # Контролюємо коміт тут
            )
            await self.commit()  # Атомарний коміт для зміни статусу запрошення та створення членства
            logger.info(
                f"Запрошення з кодом '{invitation_code}' прийнято користувачем ID '{accepting_user_id}'. Користувача додано до групи.")
            return new_membership
        except ValueError as ve:  # Наприклад, якщо користувач вже активний член (обробка в add_member_to_group)
            await self.rollback()
            logger.error(f"Помилка створення членства при прийнятті запрошення '{invitation_code}': {ve}",
                         exc_info=True)
            # i18n
            raise ValueError(f"Не вдалося приєднатися до групи після прийняття запрошення: {ve}")
        except Exception as e:
            await self.rollback()
            logger.error(f"Неочікувана помилка при прийнятті запрошення '{invitation_code}': {e}",
                         exc_info=settings.DEBUG)
            raise

    async def decline_invitation(self, invitation_code: str, declining_user_id: Optional[UUID] = None) -> bool:
        """Відхиляє запрошення."""
        logger.info(
            f"Користувач ID '{declining_user_id or 'Анонім'}' намагається відхилити запрошення з кодом '{invitation_code}'.")

        invitation_db = await self._get_orm_invitation_with_relations(invitation_code=invitation_code)
        if not invitation_db:
            logger.warning(f"Запрошення '{invitation_code}' не знайдено.")
            return False
        if invitation_db.status != "pending" or invitation_db.expires_at <= datetime.now(timezone.utc):
            logger.warning(
                f"Запрошення '{invitation_code}' не активне або прострочене. Статус: {invitation_db.status}.")
            return False

        if declining_user_id and invitation_db.invited_user_id and invitation_db.invited_user_id != declining_user_id:
            logger.warning(
                f"Невідповідність ID користувача '{declining_user_id}' для відхилення запрошення '{invitation_code}', призначеного для ID '{invitation_db.invited_user_id}'.")
            return False  # Або кинути помилку дозволу

        invitation_db.status = "declined"
        invitation_db.responded_at = datetime.now(timezone.utc)
        self.db_session.add(invitation_db)
        await self.commit()
        logger.info(f"Запрошення з кодом '{invitation_code}' відхилено.")
        return True

    async def revoke_invitation(self, invitation_id: UUID, revoker_user_id: UUID) -> bool:
        """Відкликає запрошення (зазвичай автором запрошення або адміністратором групи)."""
        logger.info(f"Користувач ID '{revoker_user_id}' намагається відкликати запрошення ID '{invitation_id}'.")

        invitation_db = await self._get_orm_invitation_with_relations(invitation_id=invitation_id)
        if not invitation_db:
            logger.warning(f"Запрошення ID '{invitation_id}' не знайдено. Неможливо відкликати.")
            return False

        # TODO: Реалізувати перевірку дозволів: чи є revoker_user_id автором запрошення або адміністратором групи.
        # if not (invitation_db.inviter_user_id == revoker_user_id or
        #         await self.membership_service.is_user_group_admin(revoker_user_id, invitation_db.group_id)):
        #     raise PermissionError("Користувач не авторизований для відкликання цього запрошення.") # i18n

        if invitation_db.status != "pending":
            logger.warning(
                f"Запрошення ID '{invitation_id}' не в статусі 'pending' (статус: {invitation_db.status}). Неможливо відкликати.")
            return False
        if invitation_db.expires_at < datetime.now(timezone.utc):
            # Якщо вже прострочене, можна просто оновити статус на 'expired'
            if invitation_db.status != "expired":
                invitation_db.status = "expired"
                self.db_session.add(invitation_db)
                await self.commit()
            logger.warning(f"Запрошення ID '{invitation_id}' вже прострочене.")
            return False  # Вже не було активним для відкликання

        invitation_db.status = "revoked"
        invitation_db.responded_at = datetime.now(timezone.utc)  # Час відкликання
        self.db_session.add(invitation_db)
        await self.commit()
        logger.info(f"Запрошення ID '{invitation_id}' успішно відкликано користувачем ID '{revoker_user_id}'.")
        return True

    async def list_pending_invitations_for_group(self, group_id: UUID, skip: int = 0, limit: int = 100) -> List[
        GroupInvitationResponse]:
        """Перелічує активні (pending, не прострочені) запрошення для вказаної групи."""
        logger.debug(f"Перелік активних запрошень для групи ID: {group_id}, пропустити={skip}, ліміт={limit}")

        stmt = select(GroupInvitation).options(
            selectinload(GroupInvitation.inviter).options(selectinload(User.user_type)),
            selectinload(GroupInvitation.invited_user).options(selectinload(User.user_type)),
            selectinload(GroupInvitation.role_to_assign)
        ).where(
            GroupInvitation.group_id == group_id,
            GroupInvitation.status == "pending",
            GroupInvitation.expires_at > datetime.now(timezone.utc)
        ).order_by(GroupInvitation.created_at.desc()).offset(skip).limit(limit)

        invitations_db = (await self.db_session.execute(stmt)).scalars().all()
        response_list = [GroupInvitationResponse.model_validate(inv) for inv in invitations_db]  # Pydantic v2
        logger.info(f"Отримано {len(response_list)} активних запрошень для групи ID '{group_id}'.")
        return response_list

    async def cleanup_expired_invitations(self) -> int:
        """Оновлює статус прострочених запрошень на 'expired'."""
        logger.info("Очищення прострочених запрошень до груп...")
        now = datetime.now(timezone.utc)

        # Оновлюємо статус запрошень, які є 'pending' і вже прострочені
        update_stmt = GroupInvitation.__table__.update().where(
            GroupInvitation.status == "pending",
            GroupInvitation.expires_at < now
        ).values(status="expired", responded_at=now)  # responded_at як час "завершення"

        result = await self.db_session.execute(update_stmt)
        await self.commit()  # Застосовуємо зміни

        count = result.rowcount
        if count > 0:
            logger.info(f"Успішно позначено {count} 'pending' запрошень як 'expired'.")
        else:
            logger.info("Не знайдено 'pending' запрошень для позначення як 'expired'.")
        return count


logger.debug(f"{GroupInvitationService.__name__} (сервіс запрошень до груп) успішно визначено.")
