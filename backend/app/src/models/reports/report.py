# backend/app/src/models/reports/report.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає модель SQLAlchemy `ReportModel` для зберігання інформації
про запити на генерацію звітів, їх параметри та, можливо, посилання на згенеровані файли.
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, LargeBinary # type: ignore
from sqlalchemy.dialects.postgresql import UUID, JSONB # type: ignore
from sqlalchemy.orm import relationship # type: ignore
import uuid # Для роботи з UUID
from datetime import datetime # Для роботи з датами та часом

# Використовуємо BaseModel, оскільки це запис про звіт, а не основна сутність.
# Якщо звіти мають назву/опис, можна розглянути BaseMainModel.
# Поки що звіт - це результат запиту з параметрами.
from backend.app.src.models.base import BaseModel

class ReportModel(BaseModel):
    """
    Модель для зберігання метаданих про згенеровані звіти або запити на їх генерацію.

    Атрибути:
        id (uuid.UUID): Унікальний ідентифікатор запису звіту (успадковано).
        report_code (str): Унікальний код (тип) звіту (наприклад, "user_activity", "task_popularity").
                           TODO: Визначити Enum або довідник для типів звітів.
        requested_by_user_id (uuid.UUID | None): Ідентифікатор користувача, який замовив звіт.
                                                 NULL, якщо звіт системний або згенерований автоматично.
        group_id (uuid.UUID | None): Ідентифікатор групи, для якої генерується звіт (якщо звіт специфічний для групи).

        parameters (JSONB | None): Параметри, використані для генерації звіту (наприклад, діапазон дат, фільтри).
        status_id (uuid.UUID): Статус генерації звіту (наприклад, "в черзі", "генерується", "готовий", "помилка").
                               Посилається на StatusModel.

        generated_at (datetime | None): Час, коли звіт був успішно згенерований.
        file_id (uuid.UUID | None): Ідентифікатор файлу (з FileModel), якщо звіт збережено як файл (PDF, CSV).
        # cached_data (JSONB | None): Кешовані дані звіту, якщо він не зберігається як файл, а дані невеликі.
        # expires_at (datetime | None): Час, до якого кешовані дані або файл звіту є актуальними.

        created_at (datetime): Дата та час запиту на звіт (успадковано).
        updated_at (datetime): Дата та час останнього оновлення статусу (успадковано).

    Зв'язки:
        requester (relationship): Зв'язок з UserModel (хто замовив).
        group (relationship): Зв'язок з GroupModel (для якої групи звіт).
        status (relationship): Зв'язок зі StatusModel.
        generated_file (relationship): Зв'язок з FileModel.
    """
    __tablename__ = "reports"

    # Код типу звіту, наприклад, 'USER_ACTIVITY_REPORT', 'TASK_POPULARITY_REPORT', 'BONUS_DYNAMICS_REPORT'.
    # TODO: Створити Enum або довідник для ReportCode.
    report_code: Column[str] = Column(String(100), nullable=False, index=True)

    # Користувач, який запросив звіт. Може бути NULL для системних звітів.
    # TODO: Замінити "users.id" на константу або імпорт моделі UserModel.
    requested_by_user_id: Column[uuid.UUID | None] = Column(UUID(as_uuid=True), ForeignKey("users.id", name="fk_reports_requester_id", ondelete="SET NULL"), nullable=True, index=True)

    # Група, для якої генерується звіт. Може бути NULL для глобальних системних звітів.
    # TODO: Замінити "groups.id" на константу або імпорт моделі GroupModel.
    group_id: Column[uuid.UUID | None] = Column(UUID(as_uuid=True), ForeignKey("groups.id", name="fk_reports_group_id", ondelete="CASCADE"), nullable=True, index=True)

    # Параметри, використані для генерації звіту (фільтри, діапазони дат тощо).
    parameters: Column[JSONB | None] = Column(JSONB, nullable=True)

    # Статус генерації звіту.
    # TODO: Замінити "statuses.id" на константу або імпорт моделі StatusModel.
    status_id: Column[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("statuses.id", name="fk_reports_status_id"), nullable=False, index=True)

    generated_at: Column[DateTime | None] = Column(DateTime(timezone=True), nullable=True)

    # Посилання на згенерований файл (якщо звіт зберігається як файл).
    # TODO: Замінити "files.id" на константу або імпорт моделі FileModel.
    file_id: Column[uuid.UUID | None] = Column(UUID(as_uuid=True), ForeignKey("files.id", name="fk_reports_file_id", ondelete="SET NULL"), nullable=True, index=True, unique=True)
    # `unique=True` для file_id, якщо один файл відповідає одному запису звіту.

    # --- Зв'язки (Relationships) ---
    requester = relationship("UserModel", foreign_keys=[requested_by_user_id]) # back_populates="requested_reports" буде в UserModel
    group = relationship("GroupModel", foreign_keys=[group_id]) # back_populates="reports" буде в GroupModel
    status = relationship("StatusModel", foreign_keys=[status_id]) # back_populates="report_statuses" буде в StatusModel
    generated_file = relationship("FileModel", foreign_keys=[file_id]) # back_populates="report_for_file" буде в FileModel

    def __repr__(self) -> str:
        """
        Повертає рядкове представлення об'єкта моделі ReportModel.
        """
        return f"<{self.__class__.__name__}(id='{self.id}', report_code='{self.report_code}', status_id='{self.status_id}')>"

# TODO: Перевірити відповідність `technical-task.md`:
# - "детальні звіти по активності користувачів, популярності завдань/нагород, динаміці накопичення бонусів..."
#   - `report_code` буде визначати тип звіту. `parameters` для фільтрації.
# - "Персоналізовані звіти для користувачів"
#   - `requested_by_user_id` може вказувати на користувача, для якого звіт.
#   - Або `parameters` можуть містити `user_id` для фільтрації персонального звіту.

# TODO: Узгодити назву таблиці `reports` з `structure-claude-v3.md`. Відповідає.
# Використання `BaseModel` як основи.
# Ключові поля: `report_code`, `status_id`.
# Додаткові поля: `requested_by_user_id`, `group_id`, `parameters`, `generated_at`, `file_id`.
# `JSONB` для `parameters` для гнучкості.
# `ondelete="SET NULL"` для `requested_by_user_id` та `file_id`.
# `ondelete="CASCADE"` для `group_id`.
# Зв'язки визначені.
# Все виглядає логічно для системи, де звіти можуть генеруватися асинхронно
# і зберігатися як файли або кешуватися.
# Якщо звіти завжди генеруються динамічно і не зберігаються, ця таблиця може бути непотрібною,
# або використовуватися лише для логування запитів на звіти.
# Поточна модель передбачає можливість асинхронної генерації та збереження.
# Статуси можуть бути: "REQUESTED", "QUEUED", "PROCESSING", "COMPLETED", "FAILED".
# `file_id` посилається на майбутню `FileModel`.
# `group_id` дозволяє створювати звіти в контексті групи. Якщо `NULL`, то звіт глобальний.
# `requested_by_user_id` для відстеження, хто замовив звіт, або для кого він.
# `report_code` - ключове поле для визначення логіки генерації звіту.
# `updated_at` буде оновлюватися при зміні `status_id` або `file_id`.
# `created_at` - час запиту.
# `generated_at` - час успішної генерації.
