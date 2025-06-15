# backend/app/src/services/groups/membership.py
# import logging # Замінено на централізований логер
from typing import List, Optional
# UUID видалено
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func # sqlalchemy.future тепер select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
# func вже імпортовано

# Повні шляхи імпорту
from backend.app.src.services.base import BaseService
from backend.app.src.models.groups.membership import GroupMembership
from backend.app.src.repositories.groups.membership_repository import GroupMembershipRepository # Імпорт репозиторію
from backend.app.src.models.groups.group import Group
from backend.app.src.models.auth.user import User
from backend.app.src.models.dictionaries.user_roles import UserRole
from backend.app.src.models.files.file import FileRecord # Для UserAvatar -> FileRecord в list_group_members
from backend.app.src.models.files.avatar import UserAvatar # Для User -> UserAvatar в list_group_members


from backend.app.src.schemas.groups.membership import (
    GroupMembershipResponse,
    GroupMemberResponse,
    GroupMembershipCreateSchema # Додано
)
from backend.app.src.config.logging import logger
from backend.app.src.config import settings

ADMIN_ROLE_CODE = "ADMIN"
USER_ROLE_CODE = "USER"


class GroupMembershipService(BaseService):
    """
    Сервіс для управління членством користувачів у групах, включаючи їхні ролі та статус.
    Обробляє додавання користувачів до груп, їх видалення, оновлення ролей та перелік членів.
    """

    def __init__(self, db_session: AsyncSession):
        super().__init__(db_session)
        self.membership_repo = GroupMembershipRepository() # Ініціалізація репозиторію
        logger.info("GroupMembershipService ініціалізовано.")

    async def _get_membership_orm_with_relations(self, group_id: int, user_id: int) -> Optional[GroupMembership]: # Змінено UUID на int
        """Внутрішній метод для отримання ORM моделі GroupMembership з завантаженими зв'язками."""
        # Залишаємо прямий запит для гнучкого selectinload
        return (await self.db_session.execute(
            select(GroupMembership).options(
                selectinload(GroupMembership.user).options(selectinload(User.user_type)),
                selectinload(GroupMembership.group).options(selectinload(Group.group_type)),
                selectinload(GroupMembership.role)
            ).where(
                GroupMembership.group_id == group_id,
                GroupMembership.user_id == user_id
            )
        )).scalar_one_or_none()

    async def add_member_to_group(
            self,
            group_id: int, # Змінено UUID на int
            user_id: int, # Змінено UUID на int
            role_code: str,
            added_by_user_id: Optional[int] = None, # Змінено UUID на int
            commit_session: bool = True
    ) -> GroupMembershipResponse:
        """
        Додає користувача до групи з вказаною роллю.
        Запобігає додаванню, якщо користувач вже є активним членом.
        Реактивує та оновлює роль, якщо користувач є неактивним членом.

        :param group_id: ID групи.
        :param user_id: ID користувача для додавання.
        :param role_code: Код ролі для призначення користувачеві в цій групі.
        :param added_by_user_id: ID користувача, що виконує дію.
        :param commit_session: Якщо True, сесія буде закомічена.
        :return: Pydantic схема GroupMembershipResponse створеного або оновленого членства.
        :raises ValueError: Якщо групу, користувача або роль не знайдено, або якщо виникає конфлікт. # i18n
        """
        logger.debug(f"Спроба додати користувача ID '{user_id}' до групи ID '{group_id}' з роллю '{role_code}'.")

        group = await self.db_session.get(Group, group_id)
        if not group: raise ValueError(f"Групу з ID '{group_id}' не знайдено.")  # i18n

        user = await self.db_session.get(User, user_id)
        if not user: raise ValueError(f"Користувача з ID '{user_id}' не знайдено.")  # i18n

        role = (await self.db_session.execute(
            select(UserRole).where(UserRole.code == role_code))
                ).scalar_one_or_none()
        if not role: raise ValueError(f"Роль з кодом '{role_code}' не знайдено.")  # i18n

        membership_db = await self._get_membership_orm_with_relations(group_id, user_id)

        current_time = datetime.now(timezone.utc)

        if membership_db:  # Якщо запис членства існує
            if membership_db.is_active:
                if membership_db.user_role_id == role.id:
                    logger.info(f"Користувач '{user_id}' вже активний член групи '{group_id}' з роллю '{role_code}'.")
                    return GroupMembershipResponse.model_validate(membership_db)  # Pydantic v2
                else:
                    # Користувач активний, але роль інша - оновлюємо роль
                    logger.info(
                        f"Користувач '{user_id}' активний в групі '{group_id}', але з іншою роллю. Оновлення ролі на '{role_code}'.")
                    # Це фактично стає операцією оновлення ролі.
                    return await self.update_member_role(group_id, user_id, role_code,
                                                         updated_by_user_id=added_by_user_id,
                                                         commit_session=commit_session)
            else:  # Був неактивним членом - реактивуємо та оновлюємо роль
                logger.info(
                    f"Реактивація та оновлення ролі для неактивного члена ID '{user_id}' в групі ID '{group_id}'.")
                membership_db.is_active = True
                membership_db.user_role_id = role.id
                membership_db.joined_at = current_time  # Оновлюємо дату приєднання при реактивації
                membership_db.added_by_user_id = added_by_user_id  # Хто додав/поновив
                membership_db.removed_at = None  # Очищаємо дані про попереднє видалення
                membership_db.removed_by_user_id = None
                # `updated_at` оновлюється автоматично моделлю
        else:  # Новий член
            logger.info(f"Додавання нового члена ID '{user_id}' до групи ID '{group_id}' з роллю '{role_code}'.")
            membership_db = GroupMembership(
                group_id=group_id,
                user_id=user_id,
                user_role_id=role.id,
                is_active=True,
                added_by_user_id=added_by_user_id,
                joined_at=current_time
                # `created_at`, `updated_at` встановлюються автоматично
            )
            self.db_session.add(membership_db)

        if commit_session:
            try:
                await self.commit()
                # Після коміту, оновлюємо об'єкт для завантаження зв'язків (якщо вони ще не завантажені)
                await self.db_session.refresh(membership_db, attribute_names=['user', 'group', 'role'])
            except IntegrityError as e:
                await self.rollback()
                logger.error(f"Помилка цілісності '{user_id}' до групи '{group_id}': {e}", exc_info=settings.DEBUG)
                # i18n
                raise ValueError(f"Не вдалося додати користувача до групи через конфлікт даних: {e}")
        else:  # Якщо коміт контролюється ззовні, просто робимо flush для отримання ID
            await self.db_session.flush([membership_db])
            # Завантаження зв'язків для відповіді, якщо потрібно (може бути небезпечно без коміту)
            # Якщо потрібно повернути повний об'єкт, краще це робити після фінального коміту.

        logger.info(
            f"Користувач ID '{user_id}' успішно доданий/реактивований в групі ID '{group_id}' з роллю '{role.name}'.")
        # Якщо commit_session=False, зв'язки можуть бути не повністю завантажені для Pydantic валідації,
        # тому, можливо, краще повертати ORM об'єкт або тільки ID, якщо немає коміту.
        # Для простоти, припускаємо, що якщо commit_session=False, то об'єкт може бути неповним для відповіді.
        # Однак, якщо flush виконано, ID будуть доступні.
        # Для консистентної відповіді, коли commit_session=False, можливо, краще, щоб викликаючий код сам формував відповідь.
        # Поки що, повертаємо те, що є.
        if not commit_session:  # Якщо не комітимо, то зв'язки можуть бути не завантажені
            await self.db_session.refresh(membership_db, attribute_names=['user', 'group', 'role'])  # Спробуємо оновити

        return GroupMembershipResponse.model_validate(membership_db)  # Pydantic v2

    async def remove_member_from_group(self, group_id: UUID, user_id: UUID,
                                       removed_by_user_id: Optional[UUID] = None) -> bool:
        """
        Видаляє користувача з групи шляхом деактивації його членства.
        Обробляє логіку, наприклад, "адмін не може покинути групу, якщо він єдиний адмін".

        :param group_id: ID групи.
        :param user_id: ID користувача для видалення.
        :param removed_by_user_id: ID користувача, що виконує дію.
        :return: True, якщо видалення успішне, False - інакше.
        :raises ValueError: Якщо користувач є останнім адміном у групі. # i18n
        """
        logger.debug(f"Спроба видалення користувача ID '{user_id}' з групи ID '{group_id}'.")

        membership_db = await self._get_membership_orm_with_relations(group_id, user_id)

        if not membership_db or not membership_db.is_active:
            logger.warning(
                f"Активне членство для користувача ID '{user_id}' в групі ID '{group_id}' не знайдено. Видалення неможливе.")
            return False

        # Перевірка, чи користувач є останнім адміном
        if membership_db.role and membership_db.role.code == ADMIN_ROLE_CODE:
            other_active_admins_count = await self.membership_repo.count_active_admins_in_group( # Використання репозиторію
                session=self.db_session, group_id=group_id, exclude_user_id=user_id
            )

            if other_active_admins_count == 0:
                msg = "Неможливо видалити останнього адміністратора з групи. Спочатку призначте іншого адміністратора."
                logger.warning(f"Користувач ID '{user_id}' є останнім адміном в групі ID '{group_id}'. {msg}")
                raise ValueError(msg)

        membership_db.is_active = False
        membership_db.removed_at = datetime.now(timezone.utc)
        membership_db.removed_by_user_id = removed_by_user_id
        # `updated_at` оновлюється автоматично

        self.db_session.add(membership_db)
        await self.commit()

        logger.info(f"Користувач ID '{user_id}' успішно видалений (деактивований) з групи ID '{group_id}'.")
        return True

    async def update_member_role(
            self, group_id: int, user_id: int, new_role_code: str, # Змінено UUID на int
            updated_by_user_id: Optional[int] = None, commit_session: bool = True # Змінено UUID на int
    ) -> GroupMembershipResponse:
        """
        Оновлює роль користувача в групі.
        Обробляє логіку, якщо понижується останній адмін.

        :param group_id: ID групи.
        :param user_id: ID користувача.
        :param new_role_code: Новий код ролі.
        :param updated_by_user_id: ID користувача, що виконує оновлення.
        :param commit_session: Якщо True, сесія буде закомічена.
        :return: Pydantic схема оновленого GroupMembershipResponse.
        :raises ValueError: Якщо членство або нова роль не знайдено, або якщо відбувається спроба понизити останнього адміна. # i18n
        """
        logger.debug(
            f"Спроба оновлення ролі для користувача ID '{user_id}' в групі ID '{group_id}' на роль '{new_role_code}'.")

        membership_db = await self._get_membership_orm_with_relations(group_id, user_id)

        if not membership_db or not membership_db.is_active:
            # i18n
            raise ValueError(f"Активне членство для користувача ID '{user_id}' в групі ID '{group_id}' не знайдено.")

        new_role_db = (await self.db_session.execute(
            select(UserRole).where(UserRole.code == new_role_code))
                       ).scalar_one_or_none()
        if not new_role_db:
            raise ValueError(f"Роль з кодом '{new_role_code}' не знайдено.")  # i18n

        if membership_db.user_role_id == new_role_db.id:
            logger.info(
                f"Користувач ID '{user_id}' в групі ID '{group_id}' вже має роль '{new_role_code}'. Оновлення не потрібне.")
            return GroupMembershipResponse.model_validate(membership_db)  # Pydantic v2

        # Перевірка, чи не понижується останній адмін
        if membership_db.role and membership_db.role.code == ADMIN_ROLE_CODE and new_role_db.code != ADMIN_ROLE_CODE:
            other_active_admins_count = await self.membership_repo.count_active_admins_in_group( # Використання репозиторію
                session=self.db_session, group_id=group_id, exclude_user_id=user_id
            )
            if other_active_admins_count == 0:
                msg = "Неможливо змінити роль останнього адміністратора. Спочатку призначте іншого адміністратора."
                logger.warning(f"Користувач ID '{user_id}' є останнім адміном в групі ID '{group_id}'. {msg}")
                raise ValueError(msg)

        membership_db.user_role_id = new_role_db.id
        membership_db.updated_by_user_id = updated_by_user_id
        # `updated_at` оновлюється автоматично. Можна додати `role_updated_at`, якщо таке поле є.
        if hasattr(membership_db, 'role_updated_at'):
            setattr(membership_db, 'role_updated_at', datetime.now(timezone.utc))

        self.db_session.add(membership_db)
        if commit_session:
            await self.commit()
            # Потрібно перезавантажити для відповіді зі зв'язками
            refreshed_membership = await self._get_membership_orm_with_relations(group_id, user_id)
            if not refreshed_membership: # Малоймовірно
                raise RuntimeError("Не вдалося перезавантажити членство після оновлення ролі.")
            membership_db = refreshed_membership
        else:
            await self.db_session.flush([membership_db])
            # Потенційно потрібно refresh, якщо далі використовуються зв'язки до коміту
            await self.db_session.refresh(membership_db, attribute_names=['user', 'group', 'role'])


        logger.info(f"Роль для користувача ID '{user_id}' в групі ID '{group_id}' оновлено на '{new_role_db.name}'.")
        return GroupMembershipResponse.model_validate(membership_db)

    async def list_group_members(
            self, group_id: int, skip: int = 0, limit: int = 100, is_active: Optional[bool] = True # Змінено UUID на int
    ) -> List[GroupMemberResponse]:
        """Перелічує членів групи."""
        logger.debug(f"Перелік членів для групи ID: {group_id}, активні: {is_active}, пропустити={skip}, ліміт={limit}")

        # Залишаємо прямий запит для гнучкого selectinload
        stmt = select(GroupMembership).options(
            selectinload(GroupMembership.user).options(
                selectinload(User.user_type),
                selectinload(User.avatar).options(selectinload(UserAvatar.file_record)) # Змінено на file_record
            ),
            selectinload(GroupMembership.role)
        ).where(GroupMembership.group_id == group_id)

        if is_active is not None:
            stmt = stmt.where(GroupMembership.is_active == is_active)

        # Сортування за іменем користувача (username), якщо воно є в моделі User.
        # Якщо User не має username, потрібно змінити на інше поле або видалити сортування.
        # Припускаємо, що User.username існує.
        stmt = stmt.join(User, GroupMembership.user_id == User.id).order_by(User.email).offset(skip).limit(limit) # Змінено на email для прикладу

        memberships_db_list = (await self.db_session.execute(stmt)).scalars().unique().all()

        response_list = [GroupMemberResponse.model_validate(m) for m in memberships_db_list]
        logger.info(f"Отримано {len(response_list)} членів для групи ID '{group_id}'.")
        return response_list

    async def get_membership_details(self, group_id: int, user_id: int) -> Optional[GroupMembershipResponse]: # Змінено UUID на int
        """Отримує деталі членства для конкретного користувача в групі."""
        logger.debug(f"Отримання деталей членства для користувача ID {user_id} в групі ID {group_id}")

        membership_db = await self._get_membership_orm_with_relations(group_id, user_id)
        if not membership_db:
            logger.info(f"Членство для користувача ID {user_id} в групі ID {group_id} не знайдено.")
            return None

        return GroupMembershipResponse.model_validate(membership_db)  # Pydantic v2


logger.debug(f"{GroupMembershipService.__name__} (сервіс членства в групах) успішно визначено.")
