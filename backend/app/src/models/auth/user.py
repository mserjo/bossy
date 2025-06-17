# backend/app/src/models/auth/user.py
# -*- coding: utf-8 -*-
"""
Модель SQLAlchemy для сутності "Користувач".

Цей модуль визначає модель `User`, яка представляє користувачів системи.
Модель успадковує `BaseMainModel` для отримання стандартного набору полів
(id, часові мітки, м'яке видалення, назва, опис тощо) та додає специфічні
атрибути користувача, такі як email, хешований пароль, статуси активності
та суперкористувача, особисту інформацію, контактні дані та зв'язки
з іншими моделями (сесії, токени оновлення, аватари, членство в групах,
тип та системна роль користувача).
"""
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.src.config import settings # Added import
from backend.app.src.models.base import BaseMainModel
from backend.app.src.models.dictionaries.statuses import Status # Added import
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

# _repr_fields з BaseMainModel та його міксинів будуть автоматично зібрані
# через __repr__ в Base. Додамо специфічні для User поля в _repr_fields тут.

# Попереднє оголошення типів для уникнення циклічних імпортів,
# якщо ці моделі імпортують User або знаходяться в інших файлах.
if TYPE_CHECKING:
    from backend.app.src.models.dictionaries.user_types import UserType
    from backend.app.src.models.dictionaries.user_roles import UserRole
    from backend.app.src.models.auth.session import UserSession  # Модель сесій користувачів
    from backend.app.src.models.auth.token import RefreshToken  # Модель токенів оновлення
    from backend.app.src.models.files.avatar import UserAvatar  # Модель аватарів користувачів
    from backend.app.src.models.groups.membership import GroupMembership  # Модель членства в групах
    from backend.app.src.models.dictionaries.statuses import Status # Added import for TYPE_CHECKING


class User(BaseMainModel):
    """
    Модель користувача системи.

    Успадковує `BaseMainModel` і додає специфічні поля для користувача.
    Поле `name` з `BaseMainModel` може використовуватися як відображуване ім'я
    або повне ім'я (ПІБ). Поле `description` може містити біографію або іншу інформацію.
    Поле `state` може відображати стан користувача (наприклад, з `core.dicts.UserState`).
    Поле `group_id` з `BaseMainModel` тут, ймовірно, не буде використовуватися напряму,
    оскільки зв'язок з групами реалізується через таблицю членства `GroupMembership`.
    """
    __tablename__ = "users"

    # --- Основні облікові дані ---
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False, comment="Електронна пошта користувача (унікальна)"
    )
    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
        comment="Унікальне ім'я користувача для входу або ідентифікації"
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Хешований пароль користувача"
    )  # Довжина може бути збільшена, якщо використовуються дуже стійкі алгоритми хешування

    # --- Статуси користувача ---
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False,
                                            comment="Чи активний обліковий запис користувача")
    is_superuser: Mapped[bool] = mapped_column(default=False, nullable=False,
                                               comment="Чи має користувач права суперкористувача")
    # Примітка: поле `state` успадковане з BaseMainModel (через StateMixin)
    # і може використовуватися для більш гранульованих станів, наприклад, UserState.ACTIVE.

    # --- Особиста інформація (необов'язкова) ---
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="Ім'я користувача")
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True,
                                                     comment="Прізвище користувача (індексоване)")
    middle_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="По батькові користувача")

    # --- Контактна інформація (необов'язкова) ---
    phone_number: Mapped[Optional[str]] = mapped_column(
        String(30), unique=True, nullable=True, index=True,
        comment="Номер телефону користувача (унікальний, якщо вказано)"
    )

    # --- Інформація для відстеження ---
    last_login_at: Mapped[Optional[datetime]] = mapped_column(nullable=True,
                                                              comment="Час останнього входу користувача в систему")

    # --- Зв'язки з довідниками (тип та системна роль) ---
    user_type_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('dict_user_types.id', name='fk_user_user_type_id', ondelete='SET NULL'),
        nullable=True,
        comment="ID типу користувача з довідника dict_user_types"
    )
    # Системна роль користувача (наприклад, 'superuser', 'user', 'bot')
    # відрізняється від ролей в групах.
    system_role_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('dict_user_roles.id', name='fk_user_system_role_id', ondelete='SET NULL'),
        nullable=True,
        comment="ID системної ролі користувача з довідника dict_user_roles"
    )

    # --- Зв'язки (Relationships) ---
    user_type: Mapped[Optional["UserType"]] = relationship(foreign_keys=[user_type_id], lazy="selectin")
    system_role: Mapped[Optional["UserRole"]] = relationship(foreign_keys=[system_role_id], lazy="selectin")
    # Зв'язок зі станом користувача через успадковане поле state_id з StateMixin
    state: Mapped[Optional["Status"]] = relationship(foreign_keys="User.state_id", lazy="selectin")

    sessions: Mapped[List["UserSession"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )
    avatar: Mapped[Optional["UserAvatar"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False, lazy="selectin"
    )
    # Зв'язок з таблицею членства в групах
    memberships: Mapped[List["GroupMembership"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )

    # Поля для __repr__, успадковані з BaseMainModel та його міксинів, будуть автоматично
    # зібрані кастомним методом __repr__ в класі Base.
    # Додаємо специфічні для User поля, які хочемо бачити в repr.
    _repr_fields = ["username", "email", "is_active", "is_superuser", "first_name", "last_name"]

    @property
    def avatar_url(self) -> Optional[str]:
        """
        Повертає повний URL до активного аватара користувача або None.
        """
        if self.avatar and self.avatar.is_active and self.avatar.file_record and self.avatar.file_record.file_path:
            # settings.SERVER_HOST має бути встановлений, наприклад, "http://localhost:8000"
            # settings.STATIC_URL має бути встановлений, наприклад, "/static/"
            base_url = str(settings.SERVER_HOST).rstrip('/')
            file_path = str(self.avatar.file_record.file_path)

            if file_path.startswith('/'):
                # Якщо file_path - це вже абсолютний шлях (наприклад, /media/avatars/...)
                return f"{base_url}{file_path}"
            else:
                # Якщо file_path відносний (наприклад, avatars/user_1/avatar.jpg)
                # і має бути об'єднаний з settings.STATIC_URL
                static_url_prefix = str(getattr(settings, 'STATIC_URL', '/static/'))
                if not static_url_prefix.startswith('/'):
                    static_url_prefix = '/' + static_url_prefix
                if not static_url_prefix.endswith('/'):
                    static_url_prefix += '/'

                # Об'єднуємо base_url, static_url_prefix та file_path
                # file_path.lstrip('/') для уникнення подвійних слешів, якщо static_url_prefix вже закінчується на /
                return f"{base_url}{static_url_prefix}{file_path.lstrip('/')}"
        return None


if __name__ == "__main__":
    # Демонстраційний блок для моделі User.
    logger.info("--- Модель Користувача (User) ---")
    logger.info(f"Назва таблиці: {User.__tablename__}")

    logger.info("\nОчікувані поля (успадковані та власні):")
    # Поля з BaseMainModel та його міксинів:
    # id, name, description, state, group_id (може бути None), notes, created_at, updated_at, deleted_at
    # Власні поля User:
    # email, hashed_password, is_active, is_superuser, first_name, last_name, middle_name,
    # phone_number, last_login_at, user_type_id, system_role_id

    # Використовуємо інтроспекцію SQLAlchemy, якщо це можливо (поза контекстом реальної БД це обмежено)
    # Або просто перелічимо їх для ясності
    expected_fields = [
        'id', 'name', 'description', 'state', 'group_id', 'notes',
        'created_at', 'updated_at', 'deleted_at',
        'email', 'hashed_password', 'is_active', 'is_superuser',
        'first_name', 'last_name', 'middle_name', 'phone_number',
        'last_login_at', 'user_type_id', 'system_role_id'
    ]
    for field in expected_fields:
        logger.info(f"  - {field}")

    logger.info("\nОчікувані зв'язки (relationships):")
    expected_relationships = ['user_type', 'system_role', 'sessions', 'refresh_tokens', 'avatar', 'memberships']
    for rel in expected_relationships:
        logger.info(f"  - {rel}")

    # Приклад створення екземпляра (без взаємодії з БД)
    # У реальному коді це робиться через сесію SQLAlchemy.
    example_user = User(
        id=1,  # Зазвичай встановлюється БД
        name="Іван Франко",  # Успадковане поле, може бути ПІБ
        email="ivan.franko@example.com",
        hashed_password="some_secure_hash_here",  # В реальності тут буде результат get_password_hash()
        is_active=True,
        is_superuser=False,
        first_name="Іван",
        last_name="Франко",
        phone_number="+380991234567",
        state="active",  # Успадковане поле, наприклад, з UserState Enum
        # user_type_id, system_role_id - зазвичай встановлюються через зв'язані об'єкти або ID
    )
    example_user.created_at = datetime.now(timezone.utc)  # Імітація

    logger.info(f"\nПриклад екземпляра User (без сесії):\n  {example_user}")
    # Очікуваний __repr__ (порядок може відрізнятися, але 'id' має бути першим):
    # <User(id=1, email='ivan.franko@example.com', first_name='Іван', is_active=True, is_superuser=False, last_name='Франко', name='Іван Франко', state='active', created_at=...)>

    logger.info("\nПримітка: Для повноцінної роботи з моделлю та її зв'язками потрібна сесія SQLAlchemy та підключення до БД.")
