# backend/app/src/models/groups/invitation.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає модель SQLAlchemy `GroupInvitationModel` для зберігання запрошень
користувачів до груп. Запрошення можуть бути у вигляді унікального посилання або QR-коду.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Integer # type: ignore
from sqlalchemy.dialects.postgresql import UUID # type: ignore
from sqlalchemy.orm import relationship # type: ignore
import uuid # Для роботи з UUID
from datetime import datetime, timedelta # Для роботи з датами та часом

from backend.app.src.models.base import BaseModel # Використовуємо BaseModel

class GroupInvitationModel(BaseModel):
    """
    Модель для зберігання запрошень до груп.

    Атрибути:
        id (uuid.UUID): Унікальний ідентифікатор запрошення (успадковано).
        group_id (uuid.UUID): Ідентифікатор групи, до якої надсилається запрошення.
        invitation_code (str): Унікальний код запрошення (наприклад, для URL або QR-коду).
        email_invited (str | None): Електронна пошта користувача, якого запрошують (якщо запрошення іменне).
        user_id_invited (uuid.UUID | None): Ідентифікатор існуючого користувача, якого запрошують.
        user_id_creator (uuid.UUID): Ідентифікатор користувача (адміна групи), який створив запрошення.
        role_to_assign_id (uuid.UUID): Ідентифікатор ролі, яка буде призначена користувачеві при прийнятті запрошення.
        expires_at (datetime | None): Дата та час закінчення терміну дії запрошення. NULL означає безстрокове.
        max_uses (int | None): Максимальна кількість разів, яку можна використати це запрошення. NULL означає необмежено.
        current_uses (int): Поточна кількість використань запрошення.
        is_active (bool): Чи є запрошення активним (може бути деактивовано адміном).
        status_id (uuid.UUID | None): Статус запрошення (наприклад, "надіслано", "прийнято", "прострочено", "скасовано").
                                      Посилається на StatusModel.

        created_at (datetime): Дата та час створення запрошення (успадковано).
        updated_at (datetime): Дата та час останнього оновлення (успадковано).

    Зв'язки:
        group (relationship): Зв'язок з GroupModel.
        creator (relationship): Зв'язок з UserModel (хто створив).
        invited_user (relationship): Зв'язок з UserModel (кого запросили, якщо відомо).
        role_to_assign (relationship): Зв'язок з UserRoleModel.
        status (relationship): Зв'язок зі StatusModel.
    """
    __tablename__ = "group_invitations"

    group_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True)

    invitation_code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)

    email_invited: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    user_id_invited: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", name="fk_group_invitations_user_invited_id", ondelete="SET NULL"), nullable=True, index=True)

    user_id_creator: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", name="fk_group_invitations_user_creator_id", ondelete="CASCADE"), nullable=False, index=True) # Якщо автор видаляється, його запрошення теж

    role_to_assign_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user_roles.id", name="fk_group_invitations_role_id", ondelete="RESTRICT"), nullable=False)

    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    max_uses: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    current_uses: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    status_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("statuses.id", name="fk_group_invitations_status_id", ondelete="SET NULL"), nullable=True, index=True)

    # --- Зв'язки (Relationships) ---
    group: Mapped["GroupModel"] = relationship(back_populates="invitations")

    # TODO: Узгодити back_populates з UserModel
    creator: Mapped["UserModel"] = relationship(foreign_keys=[user_id_creator], back_populates="created_group_invitations")
    invited_user: Mapped[Optional["UserModel"]] = relationship(foreign_keys=[user_id_invited], back_populates="received_group_invitations")

    role_to_assign: Mapped["UserRoleModel"] = relationship(foreign_keys=[role_to_assign_id], back_populates="group_invitations_assigning_this_role")

    status: Mapped[Optional["StatusModel"]] = relationship(foreign_keys=[status_id], back_populates="group_invitations_with_this_status")


    def __repr__(self) -> str:
        """
        Повертає рядкове представлення об'єкта моделі GroupInvitationModel.
        """
        return f"<{self.__class__.__name__}(id='{self.id}', group_id='{self.group_id}', code='{self.invitation_code}')>"

# TODO: Перевірити відповідність `technical-task.md`:
# - "(адмін групи) відправити запрошення користувача на приєднання до групи за посиланням/QR-коду (унікальний в рамках групи)"
#   - `invitation_code` для унікального посилання. QR-код генерується на основі цього коду.
#   - Унікальність `invitation_code` забезпечена на рівні БД.
#   - "в рамках групи" - `group_id` пов'язує запрошення з групою.

# TODO: Узгодити назву таблиці `group_invitations` з `structure-claude-v3.md`. Відповідає.
# Використання `BaseModel` як основи.
# Ключові поля: `group_id`, `invitation_code`, `user_id_creator`, `role_to_assign_id`.
# Додаткові поля для гнучкості: `email_invited`, `user_id_invited`, `expires_at`, `max_uses`, `current_uses`, `is_active`, `status_id`.
# `ondelete="CASCADE"` для `group_id` означає, що при видаленні групи її запрошення також видаляються.
# `ondelete` для `user_id` (creator, invited) та `role_to_assign_id` за замовчуванням (NO ACTION або RESTRICT),
# що є прийнятним, оскільки видалення користувача або ролі не повинно автоматично видаляти запрошення,
# але може зробити їх недійсними (це обробляється логікою).
# Зв'язки визначені.
# Все виглядає логічно.
# Поле `status_id` дозволяє відстежувати життєвий цикл запрошення (наприклад, "pending", "accepted", "expired", "revoked").
# Поля `max_uses` та `current_uses` дозволяють створювати запрошення з обмеженою кількістю активацій.
# `is_active` дозволяє адміністратору вручну вмикати/вимикати запрошення.
# `expires_at` для обмеження часу дії запрошення.
# `email_invited` та `user_id_invited` для персоналізованих запрошень. Якщо обидва NULL, то запрошення загальне.
# Унікальність `invitation_code` важлива для функціонування посилань.
