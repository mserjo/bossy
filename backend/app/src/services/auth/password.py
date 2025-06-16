# backend/app/src/services/auth/password.py
"""
Сервіс для управління паролями користувачів.

Надає функціонал для хешування та перевірки паролів,
а також для створення, валідації та використання токенів скидання пароля.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
# from uuid import UUID # Видалено, user_id та інші ID зазвичай int
import secrets # Для генерації безпечних випадкових токенів

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select # Оновлено імпорт

# Виправлені повні шляхи імпорту
from backend.app.src.services.base import BaseService
from backend.app.src.models.auth.user import User # Модель користувача SQLAlchemy
from backend.app.src.models.auth.password_reset_token import PasswordResetToken # Модель токена скидання пароля SQLAlchemy
from backend.app.src.core.security import get_password_hash, verify_password # Ключові утиліти для паролів
from backend.app.src.config import settings # Імпорт конфігурації
from backend.app.src.config.logging import get_logger # Стандартизований імпорт логера
logger = get_logger(__name__) # Ініціалізація логера

# Конфігурація часу дії токена скидання пароля перенесена до settings.py
# PASSWORD_RESET_TOKEN_EXPIRE_HOURS = 1 # Години -- видалено, використовуємо settings

class PasswordService(BaseService):
    """
    Сервіс для обробки операцій, пов'язаних з паролями, таких як хешування,
    перевірка та управління токенами скидання пароля.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Ініціалізація сервісу паролів.

        :param db_session: Асинхронна сесія бази даних.
        """
        super().__init__(db_session)
        logger.info("PasswordService ініціалізовано.")

    def get_hashed_password(self, password: str) -> str:
        """
        Хешує звичайний пароль за допомогою налаштованого алгоритму.

        :param password: Звичайний пароль для хешування.
        :return: Хешований пароль.
        """
        hashed_password = get_password_hash(password)
        logger.info("Пароль успішно хешовано.")
        return hashed_password

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Перевіряє звичайний пароль відносно хешованого пароля.

        :param plain_password: Звичайний пароль.
        :param hashed_password: Хешований пароль.
        :return: True, якщо пароль вірний, інакше False.
        """
        is_valid = verify_password(plain_password, hashed_password)
        if is_valid:
            logger.info("Перевірка пароля успішна.")
        else:
            logger.warning("Перевірка пароля не вдалася.")
        return is_valid

    async def create_password_reset_token(self, user_id: int) -> str:
        """
        Генерує безпечний токен скидання пароля, зберігає його хеш та повертає звичайний токен.
        Звичайний токен призначений для надсилання користувачеві (наприклад, електронною поштою) і має бути короткотривалим.
        Хеш зберігається в базі даних для подальшої перевірки токена.

        :param user_id: ID користувача, для якого створюється токен.
        :return: Звичайний токен скидання пароля.
        :raises ValueError: Якщо користувача не знайдено. # i18n
        """
        user = await self.db_session.get(User, user_id)
        if not user:
            logger.error(f"Користувача з ID '{user_id}' не знайдено. Неможливо створити токен скидання пароля.")
            raise ValueError(f"Користувача з ID '{user_id}' не знайдено.") # i18n

        update_stmt = (
            PasswordResetToken.__table__.update()
            .where(
                PasswordResetToken.user_id == user_id,
                PasswordResetToken.expires_at > datetime.now(timezone.utc),
                PasswordResetToken.is_used == False
            )
            .values(is_used=True, used_at=datetime.now(timezone.utc))
        )
        await self.db_session.execute(update_stmt)
        logger.info(f"Існуючі активні токени скидання пароля для користувача ID '{user_id}' позначено як використані.")

        plain_token = secrets.token_urlsafe(32)
        hashed_token = self.get_hashed_password(plain_token)

        # Використання значення з settings.py
        expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS)

        reset_token_db = PasswordResetToken(
            user_id=user_id,
            token_hash=hashed_token,
            expires_at=expires_at,
            is_used=False
        )

        self.db_session.add(reset_token_db)
        await self.commit()

        logger.info(f"Токен скидання пароля створено для користувача ID '{user_id}'. Звичайний токен (перші 8 символів для логу): {plain_token[:8]}...")
        return plain_token

    async def _get_valid_reset_token_db(self, plain_token: str, user_id: int) -> Optional[PasswordResetToken]:
        """
        Внутрішній допоміжний метод: знаходить не прострочений, невикористаний запис токена скидання пароля,
        зіставляючи хеш plain_token для конкретного користувача.
        УВАГА: Цей метод може бути неефективним, якщо у користувача багато активних токенів.
        Розглянути оптимізацію, якщо очікується велика кількість токенів на користувача.
        """
        stmt = select(PasswordResetToken).where(
            PasswordResetToken.user_id == user_id,
            PasswordResetToken.is_used == False,
            PasswordResetToken.expires_at > datetime.now(timezone.utc)
        ).order_by(PasswordResetToken.created_at.desc())

        potential_tokens_db = (await self.db_session.execute(stmt)).scalars().all()

        for token_db in potential_tokens_db:
            if self.verify_password(plain_token, token_db.token_hash):
                logger.debug(f"Знайдено валідний хеш токена для користувача ID '{user_id}'.")
                return token_db
        logger.debug(f"Валідний хеш токена не знайдено для користувача ID '{user_id}' серед {len(potential_tokens_db)} потенційних токенів.")
        return None


    async def validate_password_reset_token(self, plain_token: str, user_id: int) -> bool:
        """
        Перевіряє звичайний токен скидання пароля для користувача.
        """
        logger.debug(f"Перевірка токена скидання пароля для користувача ID '{user_id}'. Токен (перші 8 символів): {plain_token[:8]}...")
        token_db = await self._get_valid_reset_token_db(plain_token, user_id)
        if token_db:
            logger.info(f"Токен скидання пароля для користувача ID '{user_id}' валідний.")
            return True
        logger.warning(f"Токен скидання пароля для користувача ID '{user_id}' невалідний, прострочений, використаний або не знайдений.")
        return False

    async def reset_password_with_token(self, plain_token: str, user_id: int, new_password: str) -> bool:
        """
        Скидає пароль користувача за допомогою валідного токена. Токен позначається як використаний.
        Якщо новий пароль збігається зі старим, операція вважається успішною, токен використовується.
        """
        logger.info(f"Спроба скидання пароля для користувача ID '{user_id}' за допомогою токена (перші 8 символів): {plain_token[:8]}...")

        token_db = await self._get_valid_reset_token_db(plain_token, user_id)
        if not token_db:
            logger.warning(f"Надано невалідний, прострочений або використаний токен скидання пароля для користувача ID '{user_id}'. Пароль не скинуто.") # i18n
            return False

        user_db = await self.db_session.get(User, user_id)
        if not user_db:
            logger.error(f"Користувача з ID '{user_id}' не знайдено під час скидання пароля, хоча існував валідний токен. Виявлено неузгодженість.") # i18n
            token_db.is_used = True
            token_db.used_at = datetime.now(timezone.utc)
            self.db_session.add(token_db)
            await self.commit()
            return False

        password_changed = False
        if self.verify_password(new_password, user_db.hashed_password):
            logger.info(f"Користувач ID '{user_id}': Новий пароль для скидання збігається зі старим. Пароль не буде змінено, але токен буде використано.")
            # Згідно з політикою, це вважається успішним скиданням, токен використовується.
        else:
            user_db.hashed_password = self.get_hashed_password(new_password)
            password_changed = True
            logger.info(f"Пароль для користувача ID '{user_id}' буде змінено.")

        # Оновлюємо password_changed_at незалежно від того, чи змінився сам хеш пароля,
        # оскільки операція скидання пароля була успішно авторизована і виконана.
        user_db.password_changed_at = datetime.now(timezone.utc)
        token_db.is_used = True
        token_db.used_at = datetime.now(timezone.utc)

        self.db_session.add(user_db)
        self.db_session.add(token_db)

        try:
            await self.commit()
            if password_changed:
                logger.info(f"Пароль для користувача ID '{user_id}' успішно скинуто і змінено, токен позначено як використаний.")
            else:
                logger.info(f"Пароль для користувача ID '{user_id}' не змінено (збігається зі старим), але токен успішно позначено як використаний.")
            return True
        except Exception as e:
            await self.rollback()
            logger.error(f"Помилка під час комміту скидання пароля для користувача ID '{user_id}': {e}", exc_info=True)
            return False

    async def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """
        Дозволяє автентифікованому користувачеві змінити свій поточний пароль.
        Новий пароль не може збігатися зі старим.
        """
        logger.info(f"Користувач ID '{user_id}' намагається змінити пароль.")
        user_db = await self.db_session.get(User, user_id)
        if not user_db:
            logger.warning(f"Користувача ID '{user_id}' не знайдено для зміни пароля.")
            raise ValueError(f"Користувача ID '{user_id}' не знайдено.") # i18n

        if not self.verify_password(old_password, user_db.hashed_password):
            logger.warning(f"Перевірка старого пароля не вдалася для користувача ID '{user_id}'.")
            raise ValueError("Старий пароль невірний.") # i18n

        if self.verify_password(new_password, user_db.hashed_password):
            logger.warning(f"Користувач ID '{user_id}': Новий пароль не може бути таким самим, як старий пароль. Зміна не відбулася.")
            raise ValueError("Новий пароль не може бути таким самим, як старий пароль.") # i18n

        user_db.hashed_password = self.get_hashed_password(new_password)
        user_db.password_changed_at = datetime.now(timezone.utc) # Оновити позначку часу

        self.db_session.add(user_db)
        try:
            await self.commit()
            logger.info(f"Пароль успішно змінено для користувача ID '{user_id}'.")
            return True
        except Exception as e:
            await self.rollback()
            logger.error(f"Помилка під час комміту зміни пароля для користувача ID '{user_id}': {e}", exc_info=True)
            return False

logger.debug("PasswordService клас визначено та завантажено.")
