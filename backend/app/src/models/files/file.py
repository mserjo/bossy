# backend/app/src/models/files/file.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає модель SQLAlchemy `FileModel` для зберігання метаданих
про завантажені файли в системі. Це можуть бути аватари користувачів,
іконки груп, нагород, бейджів, додатки до завдань тощо.
Самі файли зберігаються в файловій системі або хмарному сховищі,
а ця модель містить посилання на них та їх метадані.
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Boolean # type: ignore
from sqlalchemy.dialects.postgresql import UUID, JSONB # type: ignore
from sqlalchemy.orm import relationship # type: ignore
import uuid # Для роботи з UUID
from datetime import datetime # Для роботи з датами та часом

# Використовуємо BaseModel, оскільки це запис про файл.
# Якщо файли мають "назву" чи "опис", які надає користувач, можна розглянути BaseMainModel.
# Але зазвичай назва файлу - це `original_filename`, а опис може бути в `metadata`.
# Поки що BaseModel.
from backend.app.src.models.base import BaseModel

class FileModel(BaseModel):
    """
    Модель для зберігання метаданих про завантажені файли.

    Атрибути:
        id (uuid.UUID): Унікальний ідентифікатор файлу (успадковано).

        storage_path (str): Шлях до файлу в сховищі (наприклад, відносний шлях у файловій системі
                            або ключ об'єкта в S3).
        original_filename (str): Оригінальна назва файлу, завантаженого користувачем.
        mime_type (str): MIME-тип файлу (наприклад, "image/jpeg", "application/pdf").
        file_size_bytes (int): Розмір файлу в байтах.

        uploaded_by_user_id (uuid.UUID | None): Ідентифікатор користувача, який завантажив файл.
                                                 NULL, якщо файл системний.
        group_context_id (uuid.UUID | None): Ідентифікатор групи, в контексті якої завантажено файл
                                             (наприклад, для файлів, специфічних для групи).

        # Тип файлу або призначення (для категоризації)
        file_category_code (str | None): Код категорії файлу (наприклад, "AVATAR", "GROUP_ICON", "TASK_ATTACHMENT", "REWARD_IMAGE").
                                        TODO: Визначити Enum або довідник.

        # Додаткові метадані (наприклад, розміри зображення, тривалість відео)
        metadata (JSONB | None): Додаткові метадані про файл.

        # Статус файлу (якщо потрібен процес обробки або модерації)
        # status_id (uuid.UUID | None): Статус файлу (наприклад, "завантажується", "доступний", "на модерації", "видалено").
        #                               Посилається на StatusModel.

        is_public (bool): Чи є файл публічно доступним (наприклад, через пряме посилання без автентифікації).
                          За замовчуванням False.

        created_at (datetime): Дата та час завантаження файлу (успадковано).
        updated_at (datetime): Дата та час останнього оновлення метаданих (успадковано).

    Зв'язки:
        uploader (relationship): Зв'язок з UserModel (хто завантажив).
        group_context (relationship): Зв'язок з GroupModel (контекст групи).
        # status (relationship): Зв'язок зі StatusModel.
        # avatar_for_user (relationship): Зворотний зв'язок від AvatarModel (якщо цей файл є аватаром).
        # icon_for_group (relationship): Зворотний зв'язок від GroupModel.icon_file_id.
        # icon_for_reward (relationship): Зворотний зв'язок від RewardModel.icon_file_id.
        # icon_for_badge (relationship): Зворотний зв'язок від BadgeModel.icon_file_id.
        # icon_for_level (relationship): Зворотний зв'язок від LevelModel.icon_file_id.
        # report_file (relationship): Зворотний зв'язок від ReportModel.file_id.
    """
    __tablename__ = "files"

    # Шлях/ключ у файловому сховищі. Має бути унікальним.
    storage_path: Column[str] = Column(String(1024), nullable=False, unique=True, index=True)
    original_filename: Column[str] = Column(String(255), nullable=False)
    mime_type: Column[str] = Column(String(100), nullable=False, index=True)
    file_size_bytes: Column[Integer] = Column(Integer, nullable=False) # Використовуємо Integer, PostgreSQL підтримує до 2GB. Для більших - BigInteger.

    # Хто завантажив файл
    # TODO: Замінити "users.id" на константу або імпорт моделі UserModel.
    uploaded_by_user_id: Column[uuid.UUID | None] = Column(UUID(as_uuid=True), ForeignKey("users.id", name="fk_files_uploader_id", ondelete="SET NULL"), nullable=True, index=True)

    # Контекст групи, якщо файл специфічний для групи
    # TODO: Замінити "groups.id" на константу або імпорт моделі GroupModel.
    group_context_id: Column[uuid.UUID | None] = Column(UUID(as_uuid=True), ForeignKey("groups.id", name="fk_files_group_context_id", ondelete="CASCADE"), nullable=True, index=True)

    # Категорія файлу
    # TODO: Створити Enum або довідник для FileCategory.
    # Приклади: "USER_AVATAR", "GROUP_ICON", "REWARD_ICON", "BADGE_ICON", "LEVEL_ICON", "TASK_ATTACHMENT", "REPORT_FILE".
    file_category_code: Column[str | None] = Column(String(50), nullable=True, index=True)

    metadata: Column[JSONB | None] = Column(JSONB, nullable=True) # Наприклад, {"width": 100, "height": 100} для зображень

    # status_id: Column[uuid.UUID | None] = Column(UUID(as_uuid=True), ForeignKey("statuses.id"), nullable=True, index=True)

    is_public: Column[bool] = Column(Boolean, default=False, nullable=False, index=True)


    # --- Зв'язки (Relationships) ---
    # TODO: Узгодити back_populates="uploaded_files" з UserModel
    uploader: Mapped[Optional["UserModel"]] = relationship(foreign_keys=[uploaded_by_user_id], back_populates="uploaded_files")
    # TODO: Узгодити back_populates="context_files" з GroupModel (або specific, e.g., group_icons)
    group_context: Mapped[Optional["GroupModel"]] = relationship(foreign_keys=[group_context_id], back_populates="context_files")
    # status: Mapped[Optional["StatusModel"]] = relationship(foreign_keys=[status_id]) # Якщо буде status_id

    # Зворотні зв'язки від моделей, що використовують цей файл як іконку/аватар/звіт
    # Ці зв'язки є один-до-одного (або один-до-багатьох, якщо файл може бути кількома аватарами, що малоймовірно для унікального file_id в AvatarModel)
    # `uselist=False` вказує на один-до-одного з боку "один".

    # Для GroupModel.icon_file_id
    group_icon_for: Mapped[Optional["GroupModel"]] = relationship(back_populates="icon_file", foreign_keys="[GroupModel.icon_file_id]")
    # Для RewardModel.icon_file_id
    reward_icon_for: Mapped[Optional["RewardModel"]] = relationship(back_populates="icon_file", foreign_keys="[RewardModel.icon_file_id]")
    # Для BadgeModel.icon_file_id
    badge_icon_for: Mapped[Optional["BadgeModel"]] = relationship(back_populates="icon_file", foreign_keys="[BadgeModel.icon_file_id]")
    # Для LevelModel.icon_file_id
    level_icon_for: Mapped[Optional["LevelModel"]] = relationship(back_populates="icon_file", foreign_keys="[LevelModel.icon_file_id]")
    # Для ReportModel.file_id
    report_file_for: Mapped[Optional["ReportModel"]] = relationship(back_populates="generated_file", foreign_keys="[ReportModel.file_id]")
    # Для TeamModel.icon_file_id
    team_icon_for: Mapped[Optional["TeamModel"]] = relationship(back_populates="icon_file", foreign_keys="[TeamModel.icon_file_id]")

    # Для AvatarModel.file_id (один файл може бути пов'язаний з одним записом аватара)
    # Зв'язок з AvatarModel, де цей файл використовується.
    # В AvatarModel є file = relationship("FileModel"), тому тут має бути зворотний.
    avatar_entry: Mapped[Optional["AvatarModel"]] = relationship(back_populates="file")

    def __repr__(self) -> str:
        """
        Повертає рядкове представлення об'єкта моделі FileModel.
        """
        return f"<{self.__class__.__name__}(id='{self.id}', filename='{self.original_filename}', path='{self.storage_path}')>"

# TODO: Перевірити відповідність `technical-task.md`:
# - "підтримка завантаження файлів (аватари, іконки груп/нагород), локально"
#   - Ця модель для метаданих. `storage_path` вказує на місцезнаходження.
#   - "локально" - означає, що файли зберігаються на сервері, а не в зовнішньому сховищі (хоча модель гнучка).

# TODO: Узгодити назву таблиці `files` з `structure-claude-v3.md`. Відповідає.
# Використання `BaseModel` як основи.
# Ключові поля: `storage_path`, `original_filename`, `mime_type`, `file_size_bytes`.
# Додаткові поля: `uploaded_by_user_id`, `group_context_id`, `file_category_code`, `metadata`, `is_public`.
# `storage_path` має бути унікальним.
# `ondelete="SET NULL"` для `uploaded_by_user_id`.
# `ondelete="CASCADE"` для `group_context_id`.
# Зв'язки визначені.
# `JSONB` для `metadata`.
# `file_category_code` важливий для розрізнення призначення файлів.
# `is_public` для контролю доступу.
# Все виглядає логічно.
# Самі файли будуть оброблятися окремим сервісом (збереження, видача).
# Ця модель лише зберігає інформацію про них.
# Розмір файлу `file_size_bytes` - Integer достатньо для файлів до 2GB.
# Якщо очікуються більші файли, потрібно використовувати `BigInteger`.
# `updated_at` буде оновлюватися при зміні метаданих (наприклад, `is_public`).
# `created_at` - час завантаження.
# Поле `status_id` (закоментоване) може знадобитися, якщо є процес модерації або обробки файлів
# (наприклад, генерація thumbnails для зображень).
# Поки що для простоти без нього.
