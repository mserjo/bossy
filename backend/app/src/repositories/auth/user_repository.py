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


# from backend.app.src.config.logging import get_logger # Якщо потрібне логування

# logger = get_logger(__name__)

class UserRepository(BaseRepository[User, UserCreateSchema, UserUpdateSchema]):
    """
    Репозиторій для управління записами користувачів (`User`).

    Успадковує базові CRUD-методи від `BaseRepository` та надає
    додаткові методи для пошуку користувачів за унікальними полями,
    а також перевантажує методи створення та оновлення для обробки паролів.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Ініціалізує репозиторій для моделі `User`.

        Args:
            db_session (AsyncSession): Асинхронна сесія SQLAlchemy.
        """
        super().__init__(db_session=db_session, model=User)

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Отримує одного користувача за його електронною поштою.

        Args:
            email (str): Електронна пошта користувача для пошуку.

        Returns:
            Optional[User]: Екземпляр моделі `User`, якщо знайдено, інакше None.
        """
        stmt = select(self.model).where(self.model.email == email)
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_phone_number(self, phone_number: str) -> Optional[User]:
        """
        Отримує одного користувача за його номером телефону.
        Припускає, що номери телефонів зберігаються в унікальному форматі.

        Args:
            phone_number (str): Номер телефону користувача для пошуку.

        Returns:
            Optional[User]: Екземпляр моделі `User`, якщо знайдено, інакше None.
        """
        stmt = select(self.model).where(self.model.phone_number == phone_number)
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, obj_in: UserCreateSchema) -> User:
        """
        Створює нового користувача в базі даних.
        Пароль з вхідної схеми хешується перед збереженням.

        Args:
            obj_in (UserCreateSchema): Pydantic схема з даними для створення користувача.

        Returns:
            User: Створений екземпляр моделі `User`.
        """
        create_data = obj_in.model_dump()

        # Хешування пароля
        create_data["hashed_password"] = get_password_hash(obj_in.password)
        del create_data["password"]  # Видаляємо пароль у відкритому вигляді

        # TODO: Обробка user_type_code та system_role_code
        # Якщо ці коди передаються, потрібно отримати відповідні ID з довідників
        # і записати їх у user_type_id та system_role_id.
        # Наприклад:
        # if obj_in.user_type_code:
        #     user_type = await UserTypeRepository(self.db_session).get_by_code(obj_in.user_type_code)
        #     if user_type:
        #         create_data["user_type_id"] = user_type.id
        #     # else: обробити помилку або встановити значення за замовчуванням
        # if "user_type_code" in create_data: del create_data["user_type_code"]
        # Аналогічно для system_role_code.
        # Наразі, якщо модель User має user_type_id/system_role_id, а схема - *code,
        # то пряме **create_data не спрацює без перетворення code в id.
        # Припускаємо, що модель User очікує user_type_id та system_role_id.
        # Або ж ці поля в UserCreateSchema мають бути *_id.
        # Поки що, для простоти, припускаємо, що модель User приймає *_code напряму,
        # або ці поля будуть оброблені на рівні сервісу.
        # Якщо модель User має user_type_id, а схема user_type_code, то це поле треба видалити з create_data
        # перед розпакуванням в модель, якщо воно не є полем моделі.
        # Наприклад:
        # if "user_type_code" in create_data: del create_data["user_type_code"]
        # if "system_role_code" in create_data: del create_data["system_role_code"]

        db_obj = self.model(**create_data)
        self.db_session.add(db_obj)
        await self.db_session.commit()
        await self.db_session.refresh(db_obj)
        # logger.info(f"Створено користувача: {db_obj.email}")
        return db_obj

    async def update(self, *, db_obj: User, obj_in: UserUpdateSchema) -> User:
        """
        Оновлює існуючий запис користувача в базі даних.
        Якщо надано новий пароль, він хешується перед збереженням.

        Args:
            db_obj (User): Екземпляр моделі `User`, який потрібно оновити.
            obj_in (UserUpdateSchema): Pydantic схема з даними для оновлення.

        Returns:
            User: Оновлений екземпляр моделі `User`.
        """
        update_data = obj_in.model_dump(exclude_unset=True)

        if "password" in update_data and update_data["password"] is not None:
            # Якщо пароль надано для оновлення
            update_data["hashed_password"] = get_password_hash(update_data["password"])
            del update_data["password"]
        elif "password" in update_data:  # Якщо password є, але None (це не типовий випадок для оновлення паролю)
            del update_data["password"]  # Просто видаляємо, щоб не намагатися встановити None в hashed_password

        # TODO: Аналогічна обробка для user_type_code та system_role_code, як у методі create,
        #       якщо ці поля дозволено оновлювати через коди.
        # if "user_type_code" in update_data: del update_data["user_type_code"]
        # if "system_role_code" in update_data: del update_data["system_role_code"]

        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
            # else:
            # logger.warning(f"Спроба оновити неіснуюче поле '{field}' для користувача ID {db_obj.id}")

        self.db_session.add(db_obj)
        await self.db_session.commit()
        await self.db_session.refresh(db_obj)
        # logger.info(f"Оновлено користувача: {db_obj.email}")
        return db_obj


if __name__ == "__main__":
    # Демонстраційний блок для UserRepository.
    # Потребує макетів для AsyncSession, UserCreateSchema, UserUpdateSchema, User моделі.
    print("--- Репозиторій Користувачів (UserRepository) ---")

    # Концептуальна демонстрація. Реальне тестування потребує інтеграційних тестів.
    # from backend.app.src.core.dependencies import UserModel as User # Використання UserModel-заповнювача

    print(f"Репозиторій працює з моделлю: {User.__name__}")
    print(f"  Очікує схему створення: {UserCreateSchema.__name__}")
    print(f"  Очікує схему оновлення: {UserUpdateSchema.__name__}")

    print("\nОсновні методи:")
    print("  - get_by_email(email: str)")
    print("  - get_by_phone_number(phone_number: str)")
    print("  - create(obj_in: UserCreateSchema) -> User (з хешуванням паролю)")
    print("  - update(*, db_obj: User, obj_in: UserUpdateSchema) -> User (з хешуванням паролю, якщо надано)")
    print("  - get(record_id: Any) (успадковано)")
    print("  - get_multi(...) (успадковано)")
    print("  - delete(record_id: Any) (успадковано)")
    print("  - soft_delete(db_obj: User) (успадковано, якщо модель User підтримує)")
    print("  - count(filters: List) (успадковано)")

    print("\nПримітка: Повноцінне тестування репозиторіїв слід проводити з реальною тестовою базою даних.")
    print(
        "TODO: Реалізувати логіку перетворення *code (напр. user_type_code) на *_id в методах create/update, або перенести це на сервісний рівень.")
