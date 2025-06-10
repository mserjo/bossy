# backend/app/src/models/files/file.py
"""
Модель SQLAlchemy для сутності "Запис Файлу" (FileRecord).

Цей модуль визначає модель `FileRecord`, яка зберігає метадані
про завантажені файли в системі Kudos, такі як ім'я файлу, шлях,
тип MIME, розмір та інформацію про завантажувача.
"""
from datetime import datetime  # Необхідно для TYPE_CHECKING
from typing import TYPE_CHECKING, Optional, Dict, Any

from sqlalchemy import String, ForeignKey, Integer, JSON, func  # Integer для file_size, JSON для metadata
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Абсолютний імпорт базових класів та Enum
from backend.app.src.models.base import Base
from backend.app.src.models.mixins import TimestampedMixin
from backend.app.src.core.dicts import FileType as FileTypeEnum  # Enum для поля purpose

if TYPE_CHECKING:
    from backend.app.src.models.auth.user import User


class FileRecord(Base, TimestampedMixin):
    """
    Модель Запису Файлу.

    Зберігає метадані про кожен завантажений файл.

    Атрибути:
        id (Mapped[int]): Унікальний ідентифікатор запису файлу.
        file_name (Mapped[str]): Оригінальне ім'я файлу, надане користувачем або згенероване.
        file_path (Mapped[str]): Унікальний шлях до файлу на сервері або ключ в об'єктному сховищі.
        mime_type (Mapped[str]): MIME-тип файлу (наприклад, "image/jpeg", "application/pdf").
        file_size (Mapped[int]): Розмір файлу в байтах.
        uploader_user_id (Mapped[Optional[int]]): ID користувача, який завантажив файл.
        purpose (Mapped[Optional[str]]): Призначення файлу (наприклад, "avatar", "task_attachment").
                                         Використовує значення з `core.dicts.FileType`.
        metadata (Mapped[Optional[Dict[str, Any]]]): Додаткові метадані у форматі JSON (наприклад, розміри зображення).

        uploader (Mapped[Optional["User"]]): Зв'язок з користувачем, який завантажив файл.
        created_at, updated_at: Успадковано від `TimestampedMixin`.
    """
    __tablename__ = "file_records"

    id: Mapped[int] = mapped_column(
        primary_key=True, index=True, autoincrement=True, comment="Унікальний ідентифікатор запису файлу"
    )
    file_name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Оригінальне або згенероване ім'я файлу"
    )
    file_path: Mapped[str] = mapped_column(
        String(1024), nullable=False, unique=True, index=True, comment="Шлях до файлу на сервері або ключ в сховищі"
    )
    mime_type: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="MIME-тип файлу (наприклад, image/png)"
    )
    file_size: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="Розмір файлу в байтах"
    )
    uploader_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('users.id', name='fk_file_record_uploader_id', ondelete="SET NULL"),
        nullable=True,  # Може бути NULL, якщо файл системний або завантажувач видалений
        index=True,
        comment="ID користувача, який завантажив файл"
    )

    # Використовуємо значення з Enum FileType
    # TODO: Переконатися, що SQLEnum імпортовано та використовується, якщо тип колонки в БД є Enum.
    # purpose: Mapped[Optional[FileTypeEnum]] = mapped_column(SQLEnum(FileTypeEnum), nullable=True, index=True)
    purpose: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, index=True, comment="Призначення файлу (avatar, task_attachment тощо)"
    )

    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Додаткові метадані файлу (наприклад, розміри зображення)"
    )

    # --- Зв'язки (Relationships) ---
    uploader: Mapped[Optional["User"]] = relationship(foreign_keys=[uploader_user_id], lazy="selectin")
    # Зв'язок з UserAvatar (якщо потрібно знати, чи є цей файл аватаром)
    # user_avatar_link: Mapped[Optional["UserAvatar"]] = relationship(back_populates="file_record", lazy="selectin") # Якщо UserAvatar має back_populates

    # Поля для __repr__
    _repr_fields = ["id", "file_name", "mime_type", "file_size", "uploader_user_id", "purpose"]


if __name__ == "__main__":
    # Демонстраційний блок для моделі FileRecord.
    print("--- Модель Запису Файлу (FileRecord) ---")
    print(f"Назва таблиці: {FileRecord.__tablename__}")

    print("\nОчікувані поля:")
    expected_fields = [
        'id', 'file_name', 'file_path', 'mime_type', 'file_size',
        'uploader_user_id', 'purpose', 'metadata',
        'created_at', 'updated_at'
    ]
    for field in expected_fields:
        print(f"  - {field}")

    print("\nОчікувані зв'язки (relationships):")
    expected_relationships = ['uploader']  # , 'user_avatar_link' (якщо додано)
    for rel in expected_relationships:
        print(f"  - {rel}")

    # Приклад створення екземпляра (без взаємодії з БД)
    from datetime import timezone

    example_file = FileRecord(
        id=1,
        file_name="profile_pic.jpg",
        file_path="/uploads/avatars/user1/profile_pic.jpg",
        mime_type="image/jpeg",
        file_size=102400,  # 100 KB
        uploader_user_id=101,
        purpose=FileTypeEnum.AVATAR.value,  # Використання значення Enum
        metadata={"width": 500, "height": 500}
    )
    # Імітуємо часові мітки
    example_file.created_at = datetime.now(tz=timezone.utc)
    example_file.updated_at = datetime.now(tz=timezone.utc)

    print(f"\nПриклад екземпляра FileRecord (без сесії):\n  {example_file}")
    # Очікуваний __repr__ (порядок може відрізнятися):
    # <FileRecord(id=1, file_name='profile_pic.jpg', mime_type='image/jpeg', file_size=102400, uploader_user_id=101, purpose='avatar', created_at=...)>

    print("\nПримітка: Для повноцінної роботи з моделлю потрібна сесія SQLAlchemy та підключення до БД.")
    print(
        f"Використовується FileType Enum для поля 'purpose', наприклад: FileTypeEnum.TASK_ATTACHMENT = '{FileTypeEnum.TASK_ATTACHMENT.value}'")
