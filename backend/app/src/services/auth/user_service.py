# backend/app/src/services/auth/user_service.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає сервіс `UserService` для управління користувачами.
Він інкапсулює бізнес-логіку, пов'язану зі створенням, отриманням,
оновленням та видаленням користувачів, а також управлінням їх профілями,
паролями та статусами.
"""

from typing import List, Optional, Union, Dict, Any
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from backend.app.src.models.auth.user import UserModel
from backend.app.src.schemas.auth.user import UserCreateSchema, UserUpdateSchema, UserAdminUpdateSchema, UserSchema
from backend.app.src.repositories.auth.user_repository import UserRepository
from backend.app.src.repositories.dictionaries.status_repository import StatusRepository # Для статусів
from backend.app.src.repositories.dictionaries.user_role_repository import UserRoleRepository # Для ролей
from backend.app.src.services.base import BaseService
from backend.app.src.core.security import get_password_hash, verify_password
from backend.app.src.core.exceptions import NotFoundException, BadRequestException, ForbiddenException
from backend.app.src.core.constants import USER_TYPE_SUPERADMIN, STATUS_ACTIVE_CODE, STATUS_PENDING_EMAIL_VERIFICATION_CODE, ROLE_USER_CODE
from backend.app.src.config.logging import logger

class UserService(BaseService[UserRepository]):
    """
    Сервіс для управління користувачами.
    """
    def __init__(self, db_session: AsyncSession):
        super().__init__(UserRepository(db_session)) # Передаємо екземпляр репозиторія
        self.db_session = db_session # Зберігаємо сесію для використання в цьому сервісі
        self.status_repo = StatusRepository(db_session) # Для роботи зі статусами
        self.user_role_repo = UserRoleRepository(db_session) # Для роботи з ролями

    async def get_user_by_id(self, user_id: uuid.UUID) -> Optional[UserModel]:
        user = await self.repository.get(id=user_id)
        # Не кидаємо NotFoundException тут, щоб дозволити перевірку існування
        return user

    async def get_user_by_email(self, email: str) -> Optional[UserModel]:
        return await self.repository.get_by_email(email=email)

    async def get_user_by_username(self, username: str) -> Optional[UserModel]:
        return await self.repository.get_by_username(username=username)

    async def get_user_by_identifier(self, identifier: str) -> Optional[UserModel]:
        return await self.repository.get_by_identifier(identifier=identifier)

    async def create_user(self, *, obj_in: UserCreateSchema) -> UserModel:
        logger.debug(f"Спроба створити користувача з email: {obj_in.email}")
        existing_user_email = await self.get_user_by_email(email=obj_in.email)
        if existing_user_email:
            logger.warning(f"Користувач з email {obj_in.email} вже існує.")
            raise BadRequestException(detail_key="error_user_email_exists", email=obj_in.email)

        # obj_in.username - це поле name з UserCreateSchema. UserModel.name - це теж поле name.
        if obj_in.name: # Перевіряємо поле name зі схеми
            existing_user_by_name = await self.repository.get_by_username(username=obj_in.name) # get_by_username шукає по UserModel.name
            if existing_user_by_name:
                logger.warning(f"Користувач з ім'ям '{obj_in.name}' вже існує.")
                raise BadRequestException(detail_key="error_user_username_exists", username=obj_in.name)


        if obj_in.phone_number:
            existing_user_phone = await self.repository.get_by_phone_number(phone_number=obj_in.phone_number)
            if existing_user_phone:
                logger.warning(f"Користувач з номером телефону {obj_in.phone_number} вже існує.")
                raise BadRequestException(detail_key="error_user_phone_exists", phone=obj_in.phone_number)

        # Валідація пароля вже виконана на рівні схеми UserCreateSchema
        hashed_password = get_password_hash(obj_in.password)
        # Виключаємо confirm_password при створенні даних для моделі
        user_create_data = obj_in.model_dump(exclude={"password", "confirm_password"}, exclude_unset=True)
        user_create_data["hashed_password"] = hashed_password

        # Встановлення початкового статусу
        # user_type_code встановлюється за замовчуванням в схемі або передається
        if not user_create_data.get("state_id"):
            initial_status = await self.status_repo.get_by_code(code=STATUS_PENDING_EMAIL_VERIFICATION_CODE)
            if initial_status:
                user_create_data["state_id"] = initial_status.id
            else:
                logger.error(f"Початковий статус {STATUS_PENDING_EMAIL_VERIFICATION_CODE} не знайдено в довіднику! Користувач буде створений без явного статусу.")

        # Логіка для `role_id` видалена, оскільки `UserModel` не має цього поля.
        # `user_type_code` керує типом користувача (superadmin, user, bot).
        # Ролі в групах керуються через `GroupMembershipModel`.

        # Встановлення user_type_id
        from backend.app.src.repositories.dictionaries.user_type import user_type_repository # Локальний імпорт
        user_type_code = user_create_data.pop("user_type_code", "user") # Видаляємо з даних, бо в моделі user_type_id
        user_type = await user_type_repository.get_by_code(self.db_session, code=user_type_code)
        if user_type:
            user_create_data["user_type_id"] = user_type.id
        else:
            logger.error(f"Тип користувача з кодом '{user_type_code}' не знайдено! Користувач буде створений без типу.")
            # Можна кинути виняток або встановити дефолтний тип, якщо є.

        # Створюємо Pydantic схему з підготовленими даними, щоб передати в self.repository.create
        # Це не потрібно, якщо self.repository.create приймає словник.
        # Поточний BaseRepository.create приймає obj_in: CreateSchemaType.
        # Але UserCreateSchema не має user_type_id, state_id, hashed_password.
        # Тому потрібно або створити модель напряму, або BaseRepository.create має приймати словник.
        # BaseRepository.create: db_obj = self.model(**obj_in.model_dump())
        # Це означає, що obj_in має бути схемою, яка відповідає полям моделі.
        # Простіше створити модель напряму тут:
        db_user = UserModel(**user_create_data)
        self.db_session.add(db_user)
        try:
            await self.db_session.commit()
            await self.db_session.refresh(db_user)
            logger.info(f"Створено нового користувача: {db_user.email} (ID: {db_user.id})")
            return db_user
        except Exception as e: # TODO: Обробляти IntegrityError
            await self.db_session.rollback()
            logger.error(f"Помилка створення користувача {user_create_data.get('email')}: {e}", exc_info=True)
            raise BadRequestException(detail="Помилка при створенні користувача в базі даних.")


    async def update_user_profile(self, *, current_user: UserModel, obj_in: UserUpdateSchema) -> UserModel:
        update_data = obj_in.model_dump(exclude_unset=True)

        if "username" in update_data and update_data["username"] != current_user.username: # username тут - це поле name
            existing_user_by_name = await self.get_user_by_username(username=update_data["username"])
            if existing_user_by_name and existing_user_by_name.id != current_user.id:
                raise BadRequestException(detail_key="error_user_username_exists", username=update_data["username"])

        # Email не можна змінювати через цей метод, для цього має бути окремий процес з верифікацією
        if "email" in update_data:
            del update_data["email"]

        updated_user = await self.repository.update(db_obj=current_user, obj_in=update_data)
        logger.info(f"Оновлено профіль користувача {current_user.email}.")
        return updated_user

    async def admin_update_user(
        self, *, user_to_update_id: uuid.UUID, obj_in: UserAdminUpdateSchema, admin_user: UserModel
    ) -> UserModel:
        user_to_update = await self.repository.get_user_with_details(db=self.db_session, user_id=user_to_update_id)
        if not user_to_update:
            # Використовуємо ключ для локалізації
            raise NotFoundException(detail_key="error_resource_not_found_details", resource_name="User", identifier=str(user_to_update_id))

        if admin_user.user_type_code != USER_TYPE_SUPERADMIN:
            can_admin_group_user = False
            if admin_user.id == user_to_update_id:
                pass

            if not admin_user.group_memberships or not hasattr(admin_user.group_memberships[0], 'role'):
                admin_user_details = await self.repository.get_user_with_details(db=self.db_session, user_id=admin_user.id)
                if not admin_user_details:
                     raise ForbiddenException(detail_key="error_failed_to_verify_admin_rights") # Новий ключ
                admin_user_group_memberships = admin_user_details.group_memberships
            else:
                admin_user_group_memberships = admin_user.group_memberships

            admin_group_ids_where_admin = {
                gm.group_id for gm in admin_user_group_memberships if gm.role and gm.role.code == ROLE_ADMIN_CODE
            }
            target_user_group_ids = {gm.group_id for gm in user_to_update.group_memberships}

            if admin_group_ids_where_admin.intersection(target_user_group_ids):
                can_admin_group_user = True

            if not can_admin_group_user:
                 raise ForbiddenException(detail_key="error_admin_update_user_insufficient_privileges") # Новий ключ
            # TODO: Додати більш гранульовану перевірку: адмін групи не може підвищити/змінити роль іншого адміна,
            #       не може змінити user_type_code тощо.

        update_data = obj_in.model_dump(exclude_unset=True)

        if "email" in update_data and update_data["email"] != user_to_update.email:
            existing = await self.get_user_by_email(email=update_data["email"])
            if existing and existing.id != user_to_update.id:
                raise BadRequestException(detail_key="error_user_email_exists", email=update_data["email"])

        if "username" in update_data and update_data["username"] != user_to_update.username: # username - це поле name
            existing = await self.get_user_by_username(username=update_data["username"])
            if existing and existing.id != user_to_update.id:
                raise BadRequestException(detail_key="error_user_username_exists", username=update_data["username"])

        if "password" in update_data and update_data["password"]:
            update_data["hashed_password"] = get_password_hash(update_data["password"])
            del update_data["password"] # Видаляємо пароль у відкритому вигляді

        # Обробка user_type_code
        if "user_type_code" in update_data and update_data["user_type_code"]:
            from backend.app.src.repositories.dictionaries.user_type import user_type_repository # Локальний імпорт
            user_type_code_to_set = update_data.pop("user_type_code")
            user_type = await user_type_repository.get_by_code(self.db_session, code=user_type_code_to_set)
            if not user_type:
                raise BadRequestException(detail_key="error_user_type_not_found", code=user_type_code_to_set) # Новий ключ
            if admin_user.user_type_code != USER_TYPE_SUPERADMIN and user_type_code_to_set == USER_TYPE_SUPERADMIN:
                raise ForbiddenException(detail_key="error_cannot_set_superuser_type") # Новий ключ
            update_data["user_type_id"] = user_type.id
        elif "user_type_id" in update_data:
            from backend.app.src.repositories.dictionaries.user_type import user_type_repository
            user_type_to_set = await user_type_repository.get(self.db_session, id=update_data["user_type_id"])
            if not user_type_to_set:
                 raise BadRequestException(detail_key="error_user_type_id_not_found", id=update_data['user_type_id']) # Новий ключ
            if admin_user.user_type_code != USER_TYPE_SUPERADMIN and user_type_to_set.code == USER_TYPE_SUPERADMIN:
                raise ForbiddenException(detail_key="error_cannot_set_superuser_type")


        if "state_code" in update_data and update_data["state_code"]:
            state_code_to_set = update_data.pop("state_code")
            state = await self.status_repo.get_by_code(self.db_session, code=state_code_to_set)
            if not state:
                raise BadRequestException(detail_key="error_status_not_found", code=state_code_to_set) # Новий ключ
            update_data["state_id"] = state.id
            if state_code_to_set == STATUS_ACTIVE_CODE:
                update_data["is_email_verified"] = True # Припускаємо, що активний означає верифікований
                # is_active встановлюється моделлю або тут, якщо потрібно.
                # В UserModel is_active успадковано, але не має прямого зв'язку зі state_id в моделі.
                # Поки що не встановлюємо is_active тут, покладаючись на загальну логіку або тригери.
            elif state_code_to_set == STATUS_PENDING_EMAIL_VERIFICATION_CODE:
                 update_data["is_email_verified"] = False


        updated_user = await self.repository.update(db=self.db_session, db_obj=user_to_update, obj_in=update_data)
        logger.info(f"Адміністратор {admin_user.email} оновив користувача {updated_user.email}.")
        return updated_user

    async def delete_user(self, *, user_to_delete_id: uuid.UUID, soft_delete: bool = True, actor: UserModel) -> Optional[UserModel]:
        user_to_delete = await self.repository.get_user_with_details(db=self.db_session, user_id=user_to_delete_id)
        if not user_to_delete:
            raise NotFoundException(f"Користувача з ID {user_to_delete_id} не знайдено для видалення.")

        # Перевірка прав актора
        if actor.user_type_code != USER_TYPE_SUPERADMIN:
            if actor.id == user_to_delete_id:
                # Користувач може "видалити" (деактивувати) свій акаунт, якщо це дозволено
                # Це, ймовірно, має бути soft_delete і зміна статусу на "деактивований" або "заплановано видалення"
                # Поки що, якщо користувач видаляє сам себе, це буде soft_delete.
                if not soft_delete: # Користувач не може себе фізично видалити
                    raise ForbiddenException("Ви не можете фізично видалити власний обліковий запис.")
            else:
                # Перевірка, чи є actor адміном групи, до якої належить user_to_delete
                # Завантажуємо деталі actor, якщо вони ще не завантажені повністю
                if not actor.group_memberships or not hasattr(actor.group_memberships[0], 'role'):
                    actor_details = await self.repository.get_user_with_details(db=self.db_session, user_id=actor.id)
                    if not actor_details:
                        raise ForbiddenException("Не вдалося перевірити права адміністратора.")
                    actor_group_memberships = actor_details.group_memberships
                else:
                    actor_group_memberships = actor.group_memberships

                admin_group_ids_where_admin = {
                    gm.group_id for gm in actor_group_memberships if gm.role and gm.role.code == ROLE_ADMIN_CODE
                }
                target_user_group_ids = {gm.group_id for gm in user_to_delete.group_memberships}

                can_admin_delete_user = False
                if admin_group_ids_where_admin.intersection(target_user_group_ids):
                    # Перевірка, чи не намагається адмін групи видалити іншого адміна тієї ж групи
                    # або користувача з вищим user_type_code (наприклад, superadmin)
                    if user_to_delete.user_type_code == USER_TYPE_SUPERADMIN:
                        raise ForbiddenException("Адміністратор групи не може видалити супер-адміністратора.")

                    is_target_also_admin_in_common_groups = False
                    for gm_target in user_to_delete.group_memberships:
                        if gm_target.group_id in admin_group_ids_where_admin and \
                           gm_target.role and gm_target.role.code == ROLE_ADMIN_CODE:
                            is_target_also_admin_in_common_groups = True
                            break
                    if is_target_also_admin_in_common_groups and user_to_delete.id != actor.id : # Адмін не може видалити іншого адміна спільної групи
                        raise ForbiddenException("Адміністратор групи не може видалити іншого адміністратора цієї ж групи.")

                    can_admin_delete_user = True

                if not can_admin_delete_user:
                    raise ForbiddenException("Недостатньо прав для видалення цього користувача. Адміністратор групи може видаляти тільки звичайних користувачів своїх груп.")

        # Супер-адмін може видаляти будь-кого (крім, можливо, себе, якщо є така логіка)
        if actor.user_type_code == USER_TYPE_SUPERADMIN and actor.id == user_to_delete_id and not soft_delete:
            raise ForbiddenException("Супер-адміністратор не може фізично видалити сам себе.")


        if soft_delete:
            # Передаємо db_session та actor.id для updated_by_user_id
            deleted_user = await self.repository.soft_delete(db=self.db_session, db_obj=user_to_delete, current_user_id=actor.id)
            if deleted_user: # soft_delete може повернути None, якщо модель не підтримує
                logger.info(f"Користувача {user_to_delete.email} м'яко видалено користувачем {actor.email}.")
            else:
                # Це не мало б статися для UserModel, яка успадковує BaseMainModel
                logger.error(f"Не вдалося м'яко видалити користувача {user_to_delete.email}: модель не підтримує або інша помилка.")
            raise BadRequestException(detail_key="error_soft_delete_failed") # Новий ключ
            return deleted_user
        else: # Hard delete
            if actor.user_type_code != USER_TYPE_SUPERADMIN:
                raise ForbiddenException(detail_key="error_hard_delete_not_authorized") # Новий ключ
            user_email_before_delete = user_to_delete.email
            deleted_obj = await self.repository.delete(db=self.db_session, id=user_to_delete_id)
            if deleted_obj:
                logger.info(f"Користувача {user_email_before_delete} фізично видалено супер-адміністратором {actor.email}.")
            else:
                logger.warning(f"Спроба фізично видалити користувача {user_email_before_delete}, але він не був знайдений для видалення.")
        return user_to_delete

    async def get_active_user_by_id_for_auth(self, user_id: uuid.UUID) -> UserModel:
        """
        Отримує активного користувача за ID з деталями, необхідними для автентифікації.
        Кидає винятки, якщо користувач не знайдений, видалений, неактивний або має невідповідний статус.
        """
        user = await self.repository.get_user_with_details(db=self.db_session, user_id=user_id)
        if not user:
            raise NotFoundException(detail_key="error_user_not_found_for_auth") # Новий ключ
        if user.is_deleted:
            logger.warning(f"Спроба автентифікації для видаленого користувача: {user.email}")
            raise ForbiddenException(detail_key="error_user_account_deleted") # Новий ключ

        if not user.state:
            logger.error(f"У користувача {user.email} відсутній об'єкт статусу (state is None). Вважаємо неактивним.")
            raise ForbiddenException(detail_key="error_user_status_undefined") # Новий ключ

        if user.state.code != STATUS_ACTIVE_CODE:
            logger.warning(f"Спроба автентифікації для користувача {user.email} зі статусом '{user.state.code}' ('{user.state.name}').")
            raise ForbiddenException(detail_key="error_user_account_not_active", status_name=user.state.name) # Новий ключ

        # if not user.is_email_verified: # Ця перевірка може бути частиною логіки STATUS_ACTIVE_CODE
        #     logger.warning(f"Спроба входу для користувача {user.email} з непідтвердженим email.")
        #     raise ForbiddenException(detail_key="error_user_email_not_verified") # Новий ключ

        logger.debug(f"Користувач {user_id} ({user.email}) пройшов перевірку активності для автентифікації.")
        return user

    async def change_user_password(self, *, user: UserModel, old_password: str, new_password: str) -> bool:
        from backend.app.src.core.validators import is_strong_password

        if not verify_password(old_password, user.hashed_password):
            logger.warning(f"Невдала спроба зміни пароля для користувача {user.email}: неправильний старий пароль.")
            raise BadRequestException(detail_key="error_invalid_current_password") # Новий ключ

        if old_password == new_password:
            raise BadRequestException(detail_key="error_new_password_same_as_old") # Новий ключ

        try:
            is_strong_password(new_password)
        except ValueError as e: # is_strong_password кидає ValueError з повідомленням
            # Повідомлення з is_strong_password вже може бути локалізованим, якщо валідатор це підтримує.
            # Або ж ми можемо мати загальний ключ для помилки надійності пароля.
            # Поки що передаємо повідомлення з валідатора.
            raise BadRequestException(detail=str(e))

        user.hashed_password = get_password_hash(new_password)
        # Помилка відступу тут: наступні два рядки мають бути на тому ж рівні, що й user.hashed_password
        await self.repository.update(db_obj=user, obj_in={"hashed_password": user.hashed_password})
        logger.info(f"Пароль для користувача {user.email} успішно змінено.")

        # TODO: Інвалідувати всі активні сесії/refresh токени цього користувача (крім поточного, якщо можливо).
        #       Це може вимагати виклику TokenService або SessionService.
        from backend.app.src.repositories.auth.token import refresh_token_repository # Використовуємо репозиторій
        await refresh_token_repository.revoke_all_tokens_for_user(db=self.db_session, user_id=user.id) # Виправлено назву методу
        logger.info(f"Всі refresh-токени для користувача {user.email} було інвалідовано після зміни пароля.")
        return True

    async def reset_user_password(self, *, user: UserModel, new_password: str) -> bool:
        from backend.app.src.core.validators import is_strong_password
        is_strong_password(new_password) # Кине ValueError, якщо пароль не відповідає вимогам

        user.hashed_password = get_password_hash(new_password)
        await self.repository.update(db=self.db_session, db_obj=user, obj_in={"hashed_password": user.hashed_password}) # Додано db=self.db_session
        logger.info(f"Пароль для користувача {user.email} успішно скинуто.")

        # TODO: Інвалідувати всі активні сесії/refresh токени цього користувача.
        from backend.app.src.repositories.auth.token import refresh_token_repository
        await refresh_token_repository.revoke_all_tokens_for_user(db=self.db_session, user_id=user.id) # Виправлено назву методу
        logger.info(f"Всі refresh-токени для користувача {user.email} було інвалідовано після скидання пароля.")
        return True

    async def mark_email_as_verified(self, *, user: UserModel) -> UserModel:
        if user.is_email_verified:
            logger.info(f"Email для користувача {user.email} вже підтверджено.")
            return user

        update_data = {"is_email_verified": True}
        active_status = await self.status_repo.get_by_code(code=STATUS_ACTIVE_CODE)
        if active_status:
            update_data["state_id"] = active_status.id

        updated_user = await self.repository.update(db_obj=user, obj_in=update_data)
        logger.info(f"Email для користувача {user.email} успішно підтверджено, статус оновлено.")
        return updated_user

# Екземпляр сервісу не створюємо тут глобально.
