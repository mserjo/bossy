# backend/app/src/repositories/auth/user_repository.py
"""
Репозиторій для моделі "Користувач" (User).

Цей модуль визначає клас `UserRepository`, який успадковує `BaseRepository`
та надає специфічні методи для роботи з користувачами, такі як отримання
користувача за email або номером телефону, а також кастомізовані методи
створення та оновлення, що враховують хешування паролю.
"""

from typing import Optional, Dict, Any
from sqlalchemy import select  # update as sqlalchemy_update не потрібен, оскільки оновлення йде через setattr
from sqlalchemy.ext.asyncio import AsyncSession

# Абсолютний імпорт базового репозиторію
from backend.app.src.repositories.base import BaseRepository
# Абсолютний імпорт моделі User та схем UserCreateSchema, UserUpdateSchema
from backend.app.src.models.auth.user import User
from backend.app.src.schemas.auth.user import UserCreateSchema, UserUpdateSchema
# Абсолютний імпорт функції хешування паролю
from backend.app.src.config.security import get_password_hash
from backend.app.src.config.logging import get_logger # Стандартизований імпорт логера
# Отримання логера для цього модуля
logger = get_logger(__name__)

class UserRepository(BaseRepository[User, UserCreateSchema, UserUpdateSchema]):
    """
    Репозиторій для управління записами користувачів (`User`).

    Успадковує базові CRUD-методи від `BaseRepository` та надає
    додаткові методи для пошуку користувачів за унікальними полями,
    а також перевантажує методи створення та оновлення для обробки паролів.
    """

    def __init__(self):
        """
        Ініціалізує репозиторій для моделі `User`.
        """
        super().__init__(model=User)
        logger.info(f"Репозиторій для моделі '{self.model.__name__}' ініціалізовано.")

    async def get_by_email(self, session: AsyncSession, email: str) -> Optional[User]:
        """
        Отримує одного користувача за його електронною поштою.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            email (str): Електронна пошта користувача для пошуку.

        Returns:
            Optional[User]: Екземпляр моделі `User`, якщо знайдено, інакше None.
        """
        logger.debug(f"Отримання користувача за email: {email}")
        stmt = select(self.model).where(self.model.email == email)
        try:
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Помилка при отриманні користувача за email {email}: {e}", exc_info=True)
            return None

    async def get_by_phone_number(self, session: AsyncSession, phone_number: str) -> Optional[User]:
        """
        Отримує одного користувача за його номером телефону.
        Припускає, що номери телефонів зберігаються в унікальному форматі.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            phone_number (str): Номер телефону користувача для пошуку.

        Returns:
            Optional[User]: Екземпляр моделі `User`, якщо знайдено, інакше None.
        """
        logger.debug(f"Отримання користувача за номером телефону: {phone_number}")
        stmt = select(self.model).where(self.model.phone_number == phone_number)
        try:
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Помилка при отриманні користувача за номером телефону {phone_number}: {e}", exc_info=True)
            return None

    async def create(self, session: AsyncSession, *, obj_in: UserCreateSchema) -> User:
        """
        Створює нового користувача в базі даних.
        Пароль з вхідної схеми хешується перед збереженням.
        Метод перевантажує `BaseRepository.create`.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            obj_in (UserCreateSchema): Pydantic схема з даними для створення користувача.

        Returns:
            User: Створений екземпляр моделі `User`.
        """
        logger.debug(f"Створення нового користувача з email: {obj_in.email}")
        create_data = obj_in.model_dump()

        # Хешування пароля
        if obj_in.password:
            create_data["hashed_password"] = get_password_hash(obj_in.password)
        del create_data["password"]  # Видаляємо пароль у відкритому вигляді

        # TODO: [Обробка `user_type_code` та `system_role_code`]
        #       Перевірити `technical_task.txt` та `structure-claude-v2.md` для визначення,
        #       чи ці поля мають бути *_id чи *_code у схемі UserCreateSchema та моделі User.
        #       Якщо схема містить *_code, а модель *_id, тут або на сервісному рівні
        #       потрібно реалізувати логіку перетворення кодів на відповідні ID з довідників.
        #       Приклад:
        #       if "user_type_code" in create_data:
        #           user_type_code = create_data.pop("user_type_code")
        #           # user_type = await UserTypeRepository(session).get_by_code(user_type_code)
        #           # if user_type: create_data["user_type_id"] = user_type.id
        #           # else: handle error or default
        #       Аналогічно для system_role_code.
        #       Поточна реалізація припускає, що або модель приймає *_code напряму (менш ймовірно для FK),
        #       або ці поля вже є *_id у схемі, або їх обробка відбувається поза цим методом.
        #       Якщо ці *_code поля не є частиною моделі User, їх слід видалити з create_data.
        #       Наприклад, якщо модель User очікує user_type_id, а не user_type_code:
        #       if "user_type_code" in create_data: del create_data["user_type_code"]
        #       if "system_role_code" in create_data: del create_data["system_role_code"]

        db_obj = self.model(**create_data)

        try:
            async with session.begin_nested() if session.in_transaction() else session.begin():
                session.add(db_obj)
                await session.flush()
                await session.refresh(db_obj)
            logger.info(f"Створено користувача: {db_obj.email}, ID: {db_obj.id}")
            return db_obj
        except Exception as e:
            logger.error(f"Помилка при створенні користувача {obj_in.email}: {e}", exc_info=True)
            # TODO: Підняти специфічне виключення програми (наприклад, UserCreateError) з сервісного рівня.
            raise


    async def update(self, session: AsyncSession, *, db_obj: User, obj_in: UserUpdateSchema) -> User:
        """
        Оновлює існуючий запис користувача в базі даних.
        Якщо надано новий пароль, він хешується перед збереженням.
        Метод перевантажує `BaseRepository.update`.

        Args:
            session (AsyncSession): Асинхронна сесія SQLAlchemy.
            db_obj (User): Екземпляр моделі `User`, який потрібно оновити.
            obj_in (UserUpdateSchema): Pydantic схема з даними для оновлення.

        Returns:
            User: Оновлений екземпляр моделі `User`.
        """
        logger.debug(f"Оновлення користувача з ID: {db_obj.id}")
        update_data = obj_in.model_dump(exclude_unset=True)

        if "password" in update_data and update_data["password"] is not None:
            logger.debug(f"Оновлення паролю для користувача ID: {db_obj.id}")
            update_data["hashed_password"] = get_password_hash(update_data["password"])
            del update_data["password"]
        elif "password" in update_data:  # Якщо password є, але None
            del update_data["password"]

        # TODO: [Обробка `user_type_code` та `system_role_code` при оновленні]
        #       Аналогічно до методу `create`, перевірити `technical_task.txt` та `structure-claude-v2.md`.
        #       Якщо ці поля дозволено оновлювати і вони надані як *_code, потрібна логіка перетворення.
        #       if "user_type_code" in update_data: del update_data["user_type_code"] # Приклад видалення, якщо не обробляється
        #       if "system_role_code" in update_data: del update_data["system_role_code"] # Приклад видалення

        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
            else:
                logger.warning(
                    f"Спроба оновити неіснуюче поле '{field}' для користувача ID {db_obj.id}"
                )
        try:
            async with session.begin_nested() if session.in_transaction() else session.begin():
                session.add(db_obj)
                await session.flush()
                await session.refresh(db_obj)
            logger.info(f"Оновлено користувача: {db_obj.email}, ID: {db_obj.id}")
        return db_obj


if __name__ == "__main__":
    # Демонстраційний блок для UserRepository.
    # Потребує макетів для AsyncSession, UserCreateSchema, UserUpdateSchema, User моделі.
    logger.info("--- Репозиторій Користувачів (UserRepository) ---")

    # Концептуальна демонстрація. Реальне тестування потребує інтеграційних тестів.
    # from backend.app.src.core.dependencies import UserModel as User # Використання UserModel-заповнювача

    logger.info(f"Репозиторій працює з моделлю: {User.__name__}")
    logger.info(f"  Очікує схему створення: {UserCreateSchema.__name__}")
    logger.info(f"  Очікує схему оновлення: {UserUpdateSchema.__name__}")

    logger.info("\nОсновні методи:")
    logger.info("  - get_by_email(email: str)")
    logger.info("  - get_by_phone_number(phone_number: str)")
    logger.info("  - create(obj_in: UserCreateSchema) -> User (з хешуванням паролю)")
    logger.info("  - update(*, db_obj: User, obj_in: UserUpdateSchema) -> User (з хешуванням паролю, якщо надано)")
    logger.info("  - get(record_id: Any) (успадковано)")
    logger.info("  - get_multi(...) (успадковано)")
    logger.info("  - delete(record_id: Any) (успадковано)")
    logger.info("  - soft_delete(db_obj: User) (успадковано, якщо модель User підтримує)")
    logger.info("  - count(filters: List) (успадковано)")

    logger.info("\nПримітка: Повноцінне тестування репозиторіїв слід проводити з реальною тестовою базою даних.")
    logger.info(
        "TODO: Реалізувати логіку перетворення *code (напр. user_type_code) на *_id в методах create/update, або перенести це на сервісний рівень.")
