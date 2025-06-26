# backend/app/src/schemas/teams/membership.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає Pydantic схеми для моделі `TeamMembershipModel`.
Схеми використовуються для валідації даних при додаванні/оновленні учасників команди
та відображенні інформації про членство в команді.
"""

from pydantic import Field
from typing import Optional, List, ForwardRef
import uuid
from datetime import datetime

from backend.app.src.schemas.base import BaseSchema, AuditDatesSchema
# Потрібно буде імпортувати схеми для зв'язків:
# from backend.app.src.schemas.auth.user import UserPublicSchema
# from backend.app.src.schemas.teams.team import TeamSimpleSchema

UserPublicSchema = ForwardRef('backend.app.src.schemas.auth.user.UserPublicSchema')
TeamSimpleSchema = ForwardRef('backend.app.src.schemas.teams.team.TeamSimpleSchema')

# --- Схема для відображення інформації про членство в команді (для читання) ---
class TeamMembershipSchema(AuditDatesSchema): # Успадковує id, created_at, updated_at
    """
    Схема для представлення членства користувача в команді.
    `created_at` використовується як `joined_at`.
    """
    user_id: uuid.UUID = Field(..., description="ID користувача")
    team_id: uuid.UUID = Field(..., description="ID команди")
    role_in_team: Optional[str] = Field(None, max_length=100, description="Роль користувача в команді (якщо є, окрім лідера)")

    # --- Розгорнуті зв'язки (приклад) ---
    user: Optional[UserPublicSchema] = Field(None, description="Інформація про користувача-учасника")
    team: Optional[TeamSimpleSchema] = Field(None, description="Інформація про команду") # Може бути корисним, якщо список членств для користувача


# --- Схема для створення нового запису про членство в команді (додавання учасника) ---
class TeamMembershipCreateSchema(BaseSchema):
    """
    Схема для додавання користувача до команди.
    """
    user_id: uuid.UUID = Field(..., description="ID користувача, якого додають до команди")
    # team_id: uuid.UUID # Зазвичай team_id відомий з контексту (ендпоінт /teams/{team_id}/members)
    role_in_team: Optional[str] = Field(None, max_length=100, description="Роль користувача в команді (якщо є)")

    # Перевірка, що користувач є членом групи, до якої належить команда, - на сервісному рівні.

# --- Схема для оновлення інформації про членство в команді (наприклад, зміна ролі) ---
class TeamMembershipUpdateSchema(BaseSchema):
    """
    Схема для оновлення ролі користувача в команді.
    """
    role_in_team: Optional[str] = Field(None, max_length=100, description="Нова роль користувача в команді")

    # `user_id` та `team_id` зазвичай не змінюються для існуючого запису членства.

# TeamMembershipSchema.model_rebuild() # Для ForwardRef

# TODO: Переконатися, що схеми відповідають моделі `TeamMembershipModel`.
# `TeamMembershipModel` успадковує від `BaseModel`.
# `TeamMembershipSchema` успадковує від `AuditDatesSchema` і додає `user_id, team_id, role_in_team`.
# Розгорнуті зв'язки `user` (та закоментований `team`) додані з `ForwardRef`.
#
# `TeamMembershipCreateSchema`:
#   - `user_id` обов'язкове.
#   - `team_id` очікується з URL.
#   - `role_in_team` опціональне.
#
# `TeamMembershipUpdateSchema` дозволяє оновлювати `role_in_team`.
#
# `created_at` з `AuditDatesSchema` використовується як `joined_at`.
# Все виглядає узгоджено.
#
# Лідер команди визначається в `TeamModel.leader_user_id`.
# Якщо лідер також є звичайним членом (що логічно), то для нього також створюється
# запис в `TeamMembershipModel`, можливо, без специфічної `role_in_team` або зі значенням "member".
# Поле `role_in_team` призначене для інших можливих ролей всередині команди,
# якщо такі будуть потрібні (наприклад, "заступник", "скарбник" тощо).
# Якщо таких ролей немає, то `role_in_team` може бути завжди `None` або не використовуватися.
#
# Все виглядає добре.

TeamMembershipSchema.model_rebuild()
TeamMembershipCreateSchema.model_rebuild()
TeamMembershipUpdateSchema.model_rebuild()
