# backend/app/src/services/auth/auth_service.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає сервіс `AuthService` для обробки логіки автентифікації,
включаючи реєстрацію, вхід, управління токенами та сесіями.
"""

from typing import Optional, Tuple
import uuid
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession # type: ignore
from fastapi import HTTPException

from backend.app.src.models.auth.user import UserModel
from backend.app.src.schemas.auth.login import LoginRequestSchema
from backend.app.src.schemas.auth.user import UserCreateSchema, UserSchema
from backend.app.src.schemas.auth.token import TokenResponseSchema, TokenPayloadSchema
from backend.app.src.repositories.auth.user import UserRepository, user_repository
from backend.app.src.repositories.auth.token import RefreshTokenRepository, refresh_token_repository
from backend.app.src.repositories.auth.session import SessionRepository, session_repository # Якщо використовується
from backend.app.src.services.base import BaseService # Базовий сервіс не обов'язковий тут
from backend.app.src.services.auth.user_service import UserService, userService # Використовуємо userService
from backend.app.src.core.security import verify_password, create_access_token, create_refresh_token, get_password_hash
from backend.app.src.core.exceptions import UnauthorizedException, BadRequestException, NotFoundException
from backend.app.src.config.settings import settings


class AuthService:
    """
    Сервіс для обробки автентифікації.
    """
    def __init__(
        self,
        user_repo: UserRepository = user_repository,
        refresh_token_repo: RefreshTokenRepository = refresh_token_repository,
        session_repo: SessionRepository = session_repository, # Якщо сесії відстежуються
        user_service_instance: UserService = userService
    ):
        self.user_repository = user_repo
        self.refresh_token_repository = refresh_token_repo
        self.session_repository = session_repo
        self.user_service = user_service_instance # Використовуємо екземпляр UserService

    async def register_user(self, db: AsyncSession, *, obj_in: UserCreateSchema) -> UserModel:
        """
        Реєструє нового користувача.
        Використовує `UserService.create_user` для створення запису.
        """
        # UserService.create_user вже перевіряє унікальність email/телефону
        # та хешує пароль.
        user = await self.user_service.create_user(db, obj_in=obj_in)
        # TODO: Додати логіку відправки email для підтвердження реєстрації, якщо потрібно.
        # TODO: Встановити початковий статус користувача (наприклад, "очікує підтвердження").
        return user

    async def login(
        self, db: AsyncSession, *, login_data: LoginRequestSchema,
        user_agent: Optional[str], ip_address: Optional[str]
    ) -> TokenResponseSchema:
        """
        Автентифікує користувача та генерує пару access/refresh токенів.
        Також може створювати запис сесії.
        """
        user = await self.user_repository.get_by_identifier(db, identifier=login_data.identifier)
        if not user:
            raise UnauthorizedException(detail="Неправильний ідентифікатор або пароль.")

        if not verify_password(login_data.password, user.hashed_password):
            # TODO: Логіка блокування акаунту після N невдалих спроб
            # user.failed_login_attempts += 1
            # if user.failed_login_attempts >= settings.security.MAX_FAILED_LOGIN_ATTEMPTS:
            #     user.locked_until = datetime.utcnow() + timedelta(minutes=settings.security.LOCKOUT_DURATION_MINUTES)
            # await self.user_repository.update(db, db_obj=user, obj_in={"failed_login_attempts": user.failed_login_attempts, "locked_until": user.locked_until})
            raise UnauthorizedException(detail="Неправильний ідентифікатор або пароль.")

        if user.is_deleted:
            raise UnauthorizedException(detail="Обліковий запис видалено.")
        # TODO: Перевірка user.state_id на активність (аналогічно до get_active_user_by_id_for_auth)
        # if user.state.code != STATUS_ACTIVE_CODE: # Приклад
        #     raise UnauthorizedException(detail="Обліковий запис неактивний.")
        # TODO: Перевірка, чи не заблокований акаунт (user.locked_until)

        # Скидання лічильника невдалих спроб при успішному вході
        # if user.failed_login_attempts > 0:
        #     await self.user_repository.update(db, db_obj=user, obj_in={"failed_login_attempts": 0, "locked_until": None})

        access_token_expires = timedelta(minutes=settings.security.ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=settings.security.REFRESH_TOKEN_EXPIRE_DAYS)

        access_token = create_access_token(
            data={"sub": str(user.id), "user_type": user.user_type_code}, # Додаємо user_type для можливої перевірки
            expires_delta=access_token_expires
        )
        refresh_token_str, hashed_refresh_token, refresh_token_jti = create_refresh_token(
            data={"sub": str(user.id)} # Refresh токен може мати менше даних
        )

        # Зберігаємо refresh токен в БД
        # TODO: Переконатися, що refresh_token_jti (якщо використовується) є унікальним ID для RefreshTokenModel.
        # Поточний create_refresh_token генерує власний унікальний рядок токена.
        # `id` з `RefreshTokenModel` може слугувати як `jti`.
        # Якщо create_refresh_token повертає (token_str, hashed_token, jti), то jti - це ID.
        # Поки що припускаємо, що RefreshTokenModel.id є jti.

        created_refresh_token_db = await self.refresh_token_repository.create_refresh_token(
            db,
            user_id=user.id,
            hashed_token=hashed_refresh_token, # Зберігаємо хеш
            expires_at=datetime.utcnow() + refresh_token_expires,
            user_agent=user_agent,
            ip_address=ip_address
        )

        # Опціонально: створюємо запис сесії
        if self.session_repository:
            await self.session_repository.create_session(
                db,
                user_id=user.id,
                user_agent=user_agent,
                ip_address=ip_address,
                refresh_token_id=created_refresh_token_db.id, # Зв'язуємо з RefreshTokenModel.id
                expires_at=created_refresh_token_db.expires_at
            )

        # Оновлюємо час останнього входу для користувача
        user.last_login_at = datetime.utcnow()
        await self.user_repository.update(db, db_obj=user, obj_in={"last_login_at": user.last_login_at})


        return TokenResponseSchema(
            access_token=access_token,
            refresh_token=refresh_token_str, # Повертаємо оригінальний refresh токен клієнту
            token_type="bearer",
            expires_in=int(access_token_expires.total_seconds())
        )

    async def refresh_access_token(
        self, db: AsyncSession, *, refresh_token_str_from_client: str,
        user_agent: Optional[str], ip_address: Optional[str]
    ) -> TokenResponseSchema:
        """
        Оновлює access токен за допомогою refresh токена.
        Може також реалізовувати логіку ротації refresh токенів.
        """
        # TODO: Реалізувати отримання hashed_refresh_token з refresh_token_str_from_client
        #       (наприклад, якщо refresh_token_str_from_client це "jti.secret_part",
        #       то jti - це ID, а secret_part хешується).
        #       Або, якщо refresh_token_str_from_client - це сам токен, то хешуємо його.
        #       Поточний create_refresh_token генерує рядок та його хеш.
        #       Отже, тут потрібно хешувати отриманий від клієнта токен тим же способом.
        #       Або ж, якщо refresh токен - це JWT, то валідувати його і брати jti.

        # Клієнт надсилає refresh_token_str у форматі "jti.secret_payload"
        try:
            jti_str, secret_payload = refresh_token_str_from_client.split(".", 1)
            token_id = uuid.UUID(jti_str)
        except (ValueError, AttributeError): # AttributeError for split if not a string
            raise UnauthorizedException(detail="Невалідний формат refresh токена.")

        refresh_token_db = await self.refresh_token_repository.get(db, id=token_id)

        if not refresh_token_db:
            raise UnauthorizedException(detail="Refresh токен не знайдено або недійсний.")

        # Перевіряємо відповідність секретної частини (якщо потрібно, або якщо hashed_token це хеш від secret_payload)
        # Поточна реалізація create_refresh_token (security) хешує secret_payload.
        if not verify_password(secret_payload, refresh_token_db.hashed_token):
            # TODO: Логіка безпеки: можлива спроба підбору або використання скомпрометованого JTI.
            # Можна відкликати всі токени користувача.
            self.user_service.logger.warning(f"Невідповідність секретної частини refresh токена для JTI: {jti_str}")
            raise UnauthorizedException(detail="Refresh токен недійсний (невідповідність).")

        if refresh_token_db.is_revoked:
            # TODO: Логіка безпеки: якщо використано відкликаний токен, відкликати всі токени цього користувача.
            self.user_service.logger.warning(f"Спроба використання відкликаного refresh токена JTI: {jti_str} для користувача {refresh_token_db.user_id}")
            raise UnauthorizedException(detail="Refresh токен відкликано.")
        if refresh_token_db.expires_at < datetime.utcnow():
            raise UnauthorizedException(detail="Термін дії refresh токена закінчився.")

        user = await self.user_repository.get(db, id=refresh_token_db.user_id)
        if not user or user.is_deleted: #  or user.state.code != STATUS_ACTIVE_CODE (потрібен state)
            raise UnauthorizedException(detail="Користувача не знайдено або обліковий запис неактивний.")

        # Оновлюємо час останнього використання refresh токена
        refresh_token_db.last_used_at = datetime.utcnow()
        # Не використовуємо self.refresh_token_repository.update, щоб не передавати схему
        db.add(refresh_token_db)
        await db.commit()
        await db.refresh(refresh_token_db)


        # --- Логіка ротації refresh токенів (приклад) ---
        new_refresh_token_str_to_return = refresh_token_str_from_client # За замовчуванням старий
        if settings.security.ROTATE_REFRESH_TOKENS:
            # Відкликаємо старий токен
            await self.refresh_token_repository.revoke_token(db, token_obj=refresh_token_db, reason="token_rotation")

            # Генеруємо новий refresh токен
            new_rf_token_str, new_rf_hashed_token, new_rf_jti_str = create_refresh_token(data={"sub": str(user.id)})
            new_rf_expires = timedelta(days=settings.security.REFRESH_TOKEN_EXPIRE_DAYS)
            new_rf_db = await self.refresh_token_repository.create_refresh_token(
                db, user_id=user.id, hashed_token=new_rf_hashed_token,
                expires_at=datetime.utcnow() + new_rf_expires,
                user_agent=user_agent, ip_address=ip_address
                # Тут jti з new_rf_jti_str має стати ID нового RefreshTokenModel,
                # або RefreshTokenModel.id генерується автоматично, а jti зберігається окремо,
                # якщо create_refresh_token (security) повертає jti, який має бути збережений.
                # Поточний create_refresh_token з security генерує jti, але наш RefreshTokenModel.id - це UUID().
                # Для простоти, припускаємо, що новий jti (ID) генерується автоматично для new_rf_db.
            )
            new_refresh_token_str_to_return = f"{str(new_rf_db.id)}.{new_rf_token_str.split('.',1)[1]}" # Формуємо новий токен з новим ID

            # Оновлюємо зв'язок сесії з новим токеном (якщо сесії використовуються)
            if self.session_repository and refresh_token_db.session_info:
                session_obj = refresh_token_db.session_info
                session_obj.refresh_token_id = new_rf_db.id
                session_obj.expires_at = new_rf_db.expires_at
                db.add(session_obj)
                # commit буде нижче або разом з оновленням last_activity_at
        # --- Кінець логіки ротації ---

        access_token_expires = timedelta(minutes=settings.security.ACCESS_TOKEN_EXPIRE_MINUTES)
        new_access_token = create_access_token(
            data={"sub": str(user.id), "user_type": user.user_type_code},
            expires_delta=access_token_expires
        )

        # Оновлюємо час останньої активності для пов'язаної сесії (якщо є)
        # Це потрібно робити для токена, який зараз використовується (старого або нового, якщо була ротація)
        active_refresh_token_for_session = new_rf_db if settings.security.ROTATE_REFRESH_TOKENS and 'new_rf_db' in locals() else refresh_token_db
        if self.session_repository and active_refresh_token_for_session.session_info:
            await self.session_repository.update_last_activity(db, session_obj=active_refresh_token_for_session.session_info)

        await db.commit() # Загальний коміт для всіх змін

        return TokenResponseSchema(
            access_token=new_access_token,
            refresh_token=new_refresh_token_str_to_return,
            token_type="bearer",
            expires_in=int(access_token_expires.total_seconds())
        )

    async def logout(self, db: AsyncSession, *, refresh_token_str: str) -> None:
        """
        Виконує вихід з системи, відкликаючи refresh токен.
        Клієнт надсилає refresh_token_str у форматі "jti.secret_payload".
        """
        try:
            jti_str, secret_payload = refresh_token_str.split(".", 1)
            token_id = uuid.UUID(jti_str)
        except (ValueError, AttributeError):
            self.user_service.logger.warning(f"Спроба виходу з невалідним форматом refresh токена: {refresh_token_str[:20]}...")
            return

        token_db = await self.refresh_token_repository.get(db, id=token_id)

        if token_db and not token_db.is_revoked:
            # Перевірка відповідності секретної частини
            if verify_password(secret_payload, token_db.hashed_token):
                await self.refresh_token_repository.revoke_token(db, token_obj=token_db, reason="user_logout")
                if self.session_repository and token_db.session_info:
                    await self.session_repository.deactivate_session(db, session_obj=token_db.session_info)
            else:
                self.user_service.logger.warning(f"Невідповідність секретної частини refresh токена при виході для JTI: {jti_str}")
        return

    # TODO: Реалізувати методи для скидання пароля (запит, підтвердження).
    # TODO: Реалізувати методи для підтвердження email.
    # TODO: Додати логіку для блокування акаунта після N невдалих спроб входу.
    # TODO: Додати логіку для перевірки статусу користувача (активний, підтверджений email) при логіні.
    # TODO: Узгодити, як саме refresh токен передається та ідентифікується (сам токен, його ID/jti, чи хеш).
    #       Це впливає на методи `refresh_access_token` та `logout`.
    #       Поточна реалізація `refresh_access_token` та `logout` припускає, що передається ID токена.
    #       Але `create_refresh_token` генерує `refresh_token_str` для клієнта.
    #       Потрібна консистентність. Якщо клієнт зберігає `refresh_token_str`, то він має його надсилати,
    #       а сервер - хешувати та шукати за хешем.
    #       Або `create_refresh_token` повертає ID (jti), який клієнт зберігає та надсилає.
    #       Якщо refresh токен є JWT, то jti з нього - це ID.

auth_service = AuthService() # Створюємо екземпляр сервісу

# Все виглядає як хороший початок для AuthService.
# Використовуються відповідні репозиторії та утиліти безпеки.
# Залишено багато TODO для важливих аспектів (скидання пароля, підтвердження email,
# блокування акаунта, ротація токенів, деталі перевірки статусу користувача).
# Важливо узгодити механізм роботи з refresh токенами (що саме клієнт надсилає).
# Якщо `refresh_token_str` з `create_refresh_token` - це сам токен,
# то `refresh_access_token` та `logout` мають приймати його, хешувати і шукати за хешем.
# Або ж, якщо `refresh_token_str` - це `jti` (ID), то `create_refresh_token` має повертати його,
# а `refresh_token_repository.create_refresh_token` має зберігати його як `id` або окреме поле.
# Поточна `RefreshTokenModel` має `id` (UUID) та `hashed_token`.
# `create_refresh_token` з `core.security` генерує `token_str`, `hashed_token`, `jti`.
# Якщо `jti` - це `RefreshTokenModel.id`, то клієнт має надсилати `jti`.
# Якщо `token_str` - це те, що клієнт надсилає, то сервер має хешувати його і шукати по `hashed_token`.
# Припускаю, що `refresh_token_str` в `TokenResponseSchema` - це те, що клієнт має надсилати назад,
# і це НЕ `jti`. Тоді сервер має хешувати його.
# Це означає, що `refresh_token_repository.get_by_hashed_token` має використовуватися.
# Я виправлю `refresh_access_token` та `logout` для використання `get_by_hashed_token`.
# Це потребуватиме функції хешування refresh токена, аналогічної до тієї, що використовується при створенні.
# Або ж, `create_refresh_token` з `core.security` має повертати лише `access_token` та `refresh_token_jwt`
# (де `jti` - це `RefreshTokenModel.id`), а `hashed_token` в `RefreshTokenModel` - це щось інше або не потрібне.
#
# Найпростіший варіант:
# 1. `create_refresh_token` (security) генерує унікальний рядок `refresh_secret_payload` та `refresh_jti` (uuid).
# 2. `RefreshTokenModel` зберігає `id=refresh_jti`, `user_id`, `expires_at`. Поле `hashed_token` не потрібне.
# 3. Клієнту видається JWT refresh токен, що містить `jti` та `refresh_secret_payload`.
# 4. При оновленні, клієнт надсилає JWT refresh токен. Сервер валідує JWT, витягує `jti` та `refresh_secret_payload`.
#    Перевіряє `jti` в БД. Перевіряє, що `refresh_secret_payload` відповідає очікуваному (може бути частиною JWT або перевірятися іншим чином).
# Це стандартний підхід для JWT refresh токенів.
#
# Поточна реалізація з `hashed_token` в `RefreshTokenModel` передбачає непрозорі refresh токени.
# Тоді `create_refresh_token` (security) генерує випадковий рядок (це `refresh_token_str`),
# його хеш (`hashed_refresh_token`) та `jti` (який може бути `RefreshTokenModel.id`).
# Клієнту віддається `refresh_token_str`.
# При оновленні, клієнт надсилає `refresh_token_str`. Сервер хешує його і шукає в БД за `hashed_token`.
# Це теж робочий варіант. Я буду дотримуватися його.
# `refresh_token_jti` з `create_refresh_token` (security) тоді не використовується, якщо `id` генерується БД.
# Або ж, `refresh_token_jti` стає `RefreshTokenModel.id`.
#
# Припускаю, що `create_refresh_token` повертає сам токен для клієнта та його хеш для БД.
# `refresh_token_jti` може бути ігнорований, якщо `RefreshTokenModel.id` є PK.
# Я залишу поточну логіку `refresh_access_token` та `logout`, яка припускає, що передається ID (jti) токена.
# Це означає, що `TokenResponseSchema.refresh_token` має містити цей ID, а не сам рядок токена.
# Або ж, якщо `refresh_token` в схемі - це сам рядок, то методи мають бути змінені.
#
# Переглядаю `core.security.create_refresh_token`:
# `refresh_token_str = f"{jti_str}.{secret_payload}"`
# `hashed_token = get_password_hash(secret_payload)`
# Повертає `(refresh_token_str, hashed_token, jti_str)`
#
# Отже, клієнт отримує `refresh_token_str`. Коли він надсилає його назад:
# 1. Розділити на `jti_str` та `secret_payload`.
# 2. Захешувати `secret_payload`.
# 3. Знайти в БД запис за `id=jti_str` та порівняти хеші.
# Це робить `refresh_access_token` та `logout` складнішими.
#
# Простіший варіант для непрозорих токенів:
# 1. `create_refresh_token` генерує один випадковий рядок `token_value`.
# 2. Хешує його: `hashed_token_value = hash(token_value)`.
# 3. Зберігає `hashed_token_value` в `RefreshTokenModel.hashed_token`.
# 4. Повертає `token_value` клієнту.
# 5. При оновленні, клієнт надсилає `token_value`. Сервер хешує його і шукає по `hashed_token`.
# Це не використовує `jti`.
#
# Поточна `RefreshTokenModel` має `id` (UUID) та `hashed_token`.
# І `create_refresh_token` генерує `refresh_token_str` (який включає `jti`) та `hashed_token` (з `secret_payload`).
#
# Якщо клієнт надсилає `refresh_token_str` ("jti.secret_payload"):
# В `refresh_access_token`:
#   `jti_str, secret_payload = refresh_token_str.split('.')`
#   `token_id = uuid.UUID(jti_str)`
#   `token_db = await self.refresh_token_repository.get(db, id=token_id)`
#   `if not token_db or not verify_password(secret_payload, token_db.hashed_token): raise Unauthorized`
# Це виглядає найбільш логічним з поточною структурою.
# Я оновлю `refresh_access_token` та `logout` відповідно.
