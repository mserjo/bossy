# backend/app/src/services/groups/invitation.py
from typing import List, Optional
from uuid import uuid4 # UUID тепер тільки для генерації коду
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from backend.app.src.services.base import BaseService
from backend.app.src.models.groups.invitation import GroupInvitation
from backend.app.src.repositories.groups.invitation_repository import GroupInvitationRepository # Імпорт репозиторію
from backend.app.src.models.groups.group import Group
from backend.app.src.models.auth.user import User
from backend.app.src.models.dictionaries.user_roles import UserRole
from backend.app.src.models.groups.membership import GroupMembership

from backend.app.src.schemas.groups.invitation import (
    GroupInvitationCreate,
    GroupInvitationResponse,
    GroupInvitationCreateInternal, # Для передачі в репозиторій
)
from backend.app.src.schemas.groups.membership import GroupMembershipResponse
from backend.app.src.services.groups.membership import GroupMembershipService
from backend.app.src.core.dicts import InvitationStatus, GroupRole # Імпорт Enum
from backend.app.src.config import settings
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

DEFAULT_INVITATION_EXPIRE_DAYS = getattr(settings, 'DEFAULT_INVITATION_EXPIRE_DAYS', 7)


class GroupInvitationService(BaseService):
    """
    Сервіс для управління запрошеннями до груп.
    Обробляє створення, прийняття, відхилення, відкликання та перелік запрошень.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        self.membership_service = GroupMembershipService(db_session)
        self.invitation_repo = GroupInvitationRepository() # Ініціалізація репозиторію
        logger.info("GroupInvitationService ініціалізовано.")

    async def _get_orm_invitation_with_relations_by_id(self, invitation_id: int) -> Optional[GroupInvitation]:
        """Внутрішній метод для отримання ORM моделі GroupInvitation за ID з усіма зв'язками."""
        # Цей метод залишається для отримання повного об'єкта для відповіді,
        # оскільки repo.get() може не завантажувати всі потрібні зв'язки.
        stmt = select(GroupInvitation).options(
            selectinload(GroupInvitation.group),
            selectinload(GroupInvitation.inviter).options(selectinload(User.user_type)),
            selectinload(GroupInvitation.invited_user).options(selectinload(User.user_type)),
            selectinload(GroupInvitation.role_to_assign) # UserRole, що призначається
        ).where(GroupInvitation.id == invitation_id)
        return (await self.db_session.execute(stmt)).scalar_one_or_none()

    async def _get_valid_invitation_by_code_with_relations(self, invitation_code: str) -> Optional[GroupInvitation]:
        """Отримує дійсне запрошення за кодом з усіма зв'язками."""
        # Спочатку отримуємо базовий об'єкт через репозиторій
        invitation_db = await self.invitation_repo.get_by_code(session=self.db_session, code=invitation_code)
        if invitation_db:
            if invitation_db.status == InvitationStatus.PENDING and invitation_db.expires_at > datetime.now(timezone.utc):
                # Якщо знайдено і дійсне, перезавантажуємо зі зв'язками
                return await self._get_orm_invitation_with_relations_by_id(invitation_db.id)
        return None


    async def create_invitation(
            self,
            group_id: int,
            inviter_user_id: int,
            role_to_assign_code: str,
            invite_data: GroupInvitationCreate
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
        if not group: raise ValueError(f"Групу з ID '{group_id}' не знайдено.")

        inviter = await self.db_session.get(User, inviter_user_id)
        if not inviter: raise ValueError(f"Користувача, що запрошує, з ID '{inviter_user_id}' не знайдено.")

        role_to_assign_db = (await self.db_session.execute( # Залишаємо прямий запит для UserRole
            select(UserRole).where(UserRole.code == role_to_assign_code)
        )).scalar_one_or_none()
        if not role_to_assign_db: raise ValueError(f"Роль з кодом '{role_to_assign_code}' не знайдено.")

        invited_user_id_found: Optional[int] = None
        normalized_email: Optional[str] = None
        if invite_data.email:
            normalized_email = invite_data.email.lower()
            invited_user = (await self.db_session.execute(
                select(User).where(User.email == normalized_email) # Залишаємо прямий запит для User
            )).scalar_one_or_none()
            if invited_user:
                invited_user_id_found = invited_user.id
                active_member_check = await self.membership_service.get_membership_by_user_and_group( # Використовуємо сервіс членства
                    user_id=invited_user_id_found, group_id=group_id
                )
                if active_member_check and active_member_check.is_active:
                    raise ValueError(
                        f"Користувач з email '{normalized_email}' вже є активним членом групи '{group.name}'.")

            # Перевірка на існуюче активне запрошення
            existing_invitation = await self.invitation_repo.get_by_email_and_group(
                session=self.db_session, email=normalized_email, group_id=group_id
            )
            if existing_invitation: # get_by_email_and_group тепер перевіряє статус і термін дії
                raise ValueError(
                    f"Активне запрошення для '{normalized_email}' до групи '{group.name}' вже існує.")

        if invited_user_id_found: # Якщо користувач знайдений за email, перевіряємо також за ID
             existing_invitation_by_id = await self.invitation_repo.get_by_user_and_group_active_pending(
                 session=self.db_session, user_id=invited_user_id_found, group_id=group_id
             )
             if existing_invitation_by_id:
                 raise ValueError(
                    f"Активне запрошення для користувача ID '{invited_user_id_found}' до групи '{group.name}' вже існує.")


        invitation_code_str = str(uuid4())
        expire_duration_days = invite_data.custom_expire_days if invite_data.custom_expire_days is not None \
            else DEFAULT_INVITATION_EXPIRE_DAYS
        expires_at_dt = datetime.now(timezone.utc) + timedelta(days=expire_duration_days)

        create_schema = GroupInvitationCreateInternal( # Використовуємо Internal схему для передачі всіх даних
            group_id=group_id,
            inviter_user_id=inviter_user_id,
            invited_user_id=invited_user_id_found,
            email=normalized_email,
            role_id_to_assign=role_to_assign_db.id,
            invitation_code=invitation_code_str,
            status=InvitationStatus.PENDING, # Використовуємо Enum
            expires_at=expires_at_dt
        )

        try:
            new_invitation_db = await self.invitation_repo.create(session=self.db_session, obj_in=create_schema)
            await self.commit()
            refreshed_invitation = await self._get_orm_invitation_with_relations_by_id(new_invitation_db.id)
            if not refreshed_invitation:
                raise RuntimeError("Критична помилка: не вдалося отримати створене запрошення після збереження.")
        except IntegrityError as e:
            await self.rollback()
            logger.error(f"Помилка цілісності при створенні запрошення до групи ID '{group_id}': {e}",
                         exc_info=settings.DEBUG)
            raise ValueError(f"Не вдалося створити запрошення через конфлікт даних: {e}")

        logger.info(f"Запрошення з кодом '{invitation_code_str}' до групи ID '{group_id}' успішно створено.")
        return GroupInvitationResponse.model_validate(refreshed_invitation)

    async def get_invitation_by_code(self, invitation_code: str) -> Optional[GroupInvitationResponse]:
        """Отримує запрошення за його унікальним кодом, якщо воно дійсне (в очікуванні та не прострочене)."""
        logger.debug(f"Спроба отримання запрошення за кодом: {invitation_code}")
        # _get_valid_invitation_by_code_with_relations вже перевіряє статус та термін дії
        invitation_db_with_relations = await self._get_valid_invitation_by_code_with_relations(invitation_code)

        if invitation_db_with_relations:
            logger.info(f"Дійсне активне запрошення знайдено за кодом '{invitation_code}'.")
            return GroupInvitationResponse.model_validate(invitation_db_with_relations)

        logger.warning(
            f"Дійсне активне запрошення за кодом '{invitation_code}' не знайдено. Можливо, недійсне, прострочене або вже використане.")
        return None

    async def accept_invitation(
            self, invitation_code: str, accepting_user_id: int # Змінено UUID на int
    ) -> GroupMembershipResponse:
        """
        Обробляє прийняття запрошення користувачем.
        Змінює статус запрошення та додає користувача до групи.
        Операція має бути атомарною.
        """
        logger.info(f"Користувач ID '{accepting_user_id}' намагається прийняти запрошення з кодом '{invitation_code}'.")

        invitation_db = await self.invitation_repo.get_by_code(session=self.db_session, code=invitation_code)

        if not invitation_db:
            raise ValueError("Запрошення не знайдено.")
        if invitation_db.status != InvitationStatus.PENDING: # Використовуємо Enum
            raise ValueError(f"Запрошення вже не активне (статус: {invitation_db.status.value}).")
        if invitation_db.expires_at <= datetime.now(timezone.utc):
            # Оновлюємо статус на EXPIRED, якщо ще не оновлено
            if invitation_db.status != InvitationStatus.EXPIRED:
                invitation_db.status = InvitationStatus.EXPIRED
                invitation_db.responded_at = invitation_db.expires_at # Час відповіді - час закінчення
                # Використовуємо repo.update або пряме оновлення, якщо update схема порожня
                self.db_session.add(invitation_db) # Якщо оновлюємо напряму
                # await self.invitation_repo.update(session=self.db_session, db_obj=invitation_db, obj_in={"status": InvitationStatus.EXPIRED, ...})
            raise ValueError("Термін дії запрошення закінчився.")

        accepting_user = await self.db_session.get(User, accepting_user_id)
        if not accepting_user:
            raise ValueError("Користувача, що приймає запрошення, не знайдено.")

        if invitation_db.invited_user_id and invitation_db.invited_user_id != accepting_user_id:
            raise ValueError("Це запрошення призначене для іншого користувача.")
        if invitation_db.email and invitation_db.email.lower() != accepting_user.email.lower():
            raise ValueError("Це запрошення було надіслано на іншу адресу електронної пошти.")

        if not invitation_db.invited_user_id:
            invitation_db.invited_user_id = accepting_user_id

        invitation_db.status = InvitationStatus.ACCEPTED # Використовуємо Enum
        invitation_db.accepted_at = datetime.now(timezone.utc)
        invitation_db.responded_at = invitation_db.accepted_at
        self.db_session.add(invitation_db) # Додаємо змінений об'єкт до сесії

        if not invitation_db.role_id_to_assign: # Перевірка, чи є роль для призначення
            # Якщо role_id_to_assign завантажується ліниво, може знадобитися await refresh(invitation_db, ['role_to_assign'])
            # Або _get_orm_invitation_with_relations_by_id(invitation_db.id) для перезавантаження
            # Якщо це поле є FK і не може бути None, то помилка на рівні даних
            loaded_invitation = await self._get_orm_invitation_with_relations_by_id(invitation_db.id)
            if not loaded_invitation or not loaded_invitation.role_to_assign:
                 raise RuntimeError("Внутрішня помилка: не вдалося визначити роль для призначення.")
            role_code_for_membership = loaded_invitation.role_to_assign.code
        else: # Якщо role_to_assign вже завантажено (наприклад, через eager loading в get_by_code)
            role_code_for_membership = invitation_db.role_to_assign.code


        try:
            new_membership = await self.membership_service.add_member_to_group(
                group_id=invitation_db.group_id,
                user_id=accepting_user_id,
                role_code=role_code_for_membership, # Передаємо код ролі
                added_by_user_id=invitation_db.inviter_user_id,
                commit_session=False
            )
            await self.commit()
            logger.info(
                f"Запрошення з кодом '{invitation_code}' прийнято користувачем ID '{accepting_user_id}'. Користувача додано до групи.")
            return new_membership
        except ValueError as ve:
            await self.rollback()
            logger.error(f"Помилка створення членства при прийнятті запрошення '{invitation_code}': {ve}",
                         exc_info=True)
            raise ValueError(f"Не вдалося приєднатися до групи після прийняття запрошення: {ve}")
        except Exception as e:
            await self.rollback()
            logger.error(f"Неочікувана помилка при прийнятті запрошення '{invitation_code}': {e}",
                         exc_info=settings.DEBUG)
            raise

    async def decline_invitation(self, invitation_code: str, declining_user_id: Optional[int] = None) -> bool: # Змінено UUID на int
        """Відхиляє запрошення."""
        logger.info(
            f"Користувач ID '{declining_user_id or 'Анонім'}' намагається відхилити запрошення з кодом '{invitation_code}'.")

        invitation_db = await self.invitation_repo.get_by_code(session=self.db_session, code=invitation_code)
        if not invitation_db:
            logger.warning(f"Запрошення '{invitation_code}' не знайдено.")
            return False
        if invitation_db.status != InvitationStatus.PENDING or invitation_db.expires_at <= datetime.now(timezone.utc):
            logger.warning(
                f"Запрошення '{invitation_code}' не активне або прострочене. Статус: {invitation_db.status.value}.")
            return False

        if declining_user_id and invitation_db.invited_user_id and invitation_db.invited_user_id != declining_user_id:
            logger.warning(
                f"Невідповідність ID користувача '{declining_user_id}' для відхилення запрошення '{invitation_code}', призначеного для ID '{invitation_db.invited_user_id}'.")
            return False

        invitation_db.status = InvitationStatus.DECLINED # Використовуємо Enum
        invitation_db.responded_at = datetime.now(timezone.utc)
        # Використовуємо repo.update, якщо схема оновлення це дозволяє, або пряме оновлення
        self.db_session.add(invitation_db) # Якщо оновлюємо напряму
        await self.commit()
        logger.info(f"Запрошення з кодом '{invitation_code}' відхилено.")
        return True

    async def revoke_invitation(self, invitation_id: int, revoker_user_id: int) -> bool: # Змінено UUID на int
        """Відкликає запрошення (зазвичай автором запрошення або адміністратором групи)."""
        logger.info(f"Користувач ID '{revoker_user_id}' намагається відкликати запрошення ID '{invitation_id}'.")

        invitation_db = await self.invitation_repo.get(session=self.db_session, id=invitation_id) # Використовуємо repo.get
        if not invitation_db:
            logger.warning(f"Запрошення ID '{invitation_id}' не знайдено. Неможливо відкликати.")
            return False

        # TODO: Реалізувати перевірку дозволів
        if invitation_db.status != InvitationStatus.PENDING:
            logger.warning(
                f"Запрошення ID '{invitation_id}' не в статусі 'pending' (статус: {invitation_db.status.value}). Неможливо відкликати.")
            return False
        if invitation_db.expires_at < datetime.now(timezone.utc):
            if invitation_db.status != InvitationStatus.EXPIRED:
                invitation_db.status = InvitationStatus.EXPIRED
                self.db_session.add(invitation_db)
                await self.commit()
            logger.warning(f"Запрошення ID '{invitation_id}' вже прострочене.")
            return False

        invitation_db.status = InvitationStatus.REVOKED # Використовуємо Enum
        invitation_db.responded_at = datetime.now(timezone.utc)
        self.db_session.add(invitation_db)
        await self.commit()
        logger.info(f"Запрошення ID '{invitation_id}' успішно відкликано користувачем ID '{revoker_user_id}'.")
        return True

    async def list_pending_invitations_for_group(self, group_id: int, skip: int = 0, limit: int = 100) -> List[ # Змінено UUID на int
        GroupInvitationResponse]:
        """Перелічує активні (pending, не прострочені) запрошення для вказаної групи."""
        logger.debug(f"Перелік активних запрошень для групи ID: {group_id}, пропустити={skip}, ліміт={limit}")

        # Використовуємо метод репозиторію
        invitations_db_list, _ = await self.invitation_repo.list_pending_by_group(
            session=self.db_session, group_id=group_id, skip=skip, limit=limit
        )

        # Для завантаження зв'язків для відповіді
        response_list = []
        for inv_base in invitations_db_list:
            detailed_inv = await self._get_orm_invitation_with_relations_by_id(inv_base.id)
            if detailed_inv:
                response_list.append(GroupInvitationResponse.model_validate(detailed_inv))

        logger.info(f"Отримано {len(response_list)} активних запрошень для групи ID '{group_id}'.")
        return response_list

    async def cleanup_expired_invitations(self) -> int:
        """Оновлює статус прострочених запрошень на 'expired'."""
        # Використовуємо метод репозиторію
        count = await self.invitation_repo.update_status_for_expired(session=self.db_session)
        if count > 0 : # Коміт потрібен, якщо update_status_for_expired не робить його сам
            await self.commit()
            logger.info(f"Успішно позначено {count} 'pending' запрошень як 'expired' (через сервіс).")
        else:
            logger.info("Не знайдено 'pending' запрошень для позначення як 'expired' (через сервіс).")
        return count


logger.debug(f"{GroupInvitationService.__name__} (сервіс запрошень до груп) успішно визначено.")
