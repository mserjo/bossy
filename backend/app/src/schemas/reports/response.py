# backend/app/src/schemas/reports/response.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає Pydantic схеми для представлення даних у відповідях API,
що містять результати згенерованих звітів.
Структура цих схем буде сильно залежати від конкретного типу звіту.
"""

from pydantic import Field
from typing import Optional, List, Dict, Any, Union
import uuid
from datetime import datetime, date
from decimal import Decimal

from backend.app.src.schemas.base import BaseSchema
# Можуть знадобитися інші схеми для вкладених даних, наприклад:
# from backend.app.src.schemas.auth.user import UserPublicSchema
# from backend.app.src.schemas.tasks.task import TaskSimpleSchema

# --- Базова схема для елемента даних у звіті (якщо звіти табличні) ---
class ReportDataItemSchema(BaseSchema):
    """
    Базова схема для одного рядка даних у звіті.
    Конкретні звіти будуть успадковувати та додавати свої поля.
    """
    # Це може бути порожньою, оскільки поля залежать від звіту.
    pass

# --- Приклади схем для даних конкретних звітів ---

# Приклад: Дані для звіту по активності користувача
class UserActivityDataItemSchema(ReportDataItemSchema):
    user_id: uuid.UUID
    user_name: Optional[str] = None # Може бути додано сервісом
    activity_type: str # Наприклад, "task_completed", "reward_redeemed", "comment_posted"
    activity_timestamp: datetime
    related_entity_id: Optional[uuid.UUID] = None # Наприклад, ID завдання або нагороди
    related_entity_name: Optional[str] = None # Назва пов'язаної сутності
    bonus_change: Optional[Decimal] = None # Зміна балансу бонусів, пов'язана з цією активністю

class UserActivityReportDataSchema(BaseSchema):
    # report_metadata: ReportSchema # Метадані самого звіту (з report.py)
    user_id_filter: Optional[uuid.UUID] = Field(None, description="Звіт для конкретного користувача (якщо застосовано)")
    date_from: Optional[date]
    date_to: Optional[date]
    activities: List[UserActivityDataItemSchema] = Field(default_factory=list)
    summary: Optional[Dict[str, Any]] = Field(None, description="Підсумкова інформація (наприклад, загальна кількість активностей)")

# Приклад: Дані для звіту по популярності завдань
class TaskPopularityDataItemSchema(ReportDataItemSchema):
    task_id: uuid.UUID
    task_name: str
    task_type_name: Optional[str] = None
    completions_count: int = 0
    total_bonus_awarded: Optional[Decimal] = None
    # ... інші метрики ...

class TaskPopularityReportDataSchema(BaseSchema):
    # report_metadata: ReportSchema
    group_id_filter: Optional[uuid.UUID] = Field(None, description="Звіт для конкретної групи")
    date_from: Optional[date]
    date_to: Optional[date]
    tasks: List[TaskPopularityDataItemSchema] = Field(default_factory=list)
    summary: Optional[Dict[str, Any]] = Field(None, description="Підсумки (наприклад, найпопулярніше завдання)")


# Приклад: Дані для звіту по динаміці бонусів
class BonusDynamicsDataItemSchema(ReportDataItemSchema):
    # Може бути згруповано по користувачах або по днях/тижнях
    period_label: str # Наприклад, дата, тиждень, місяць, або user_name
    total_earned_bonuses: Decimal = Decimal('0.0')
    total_spent_bonuses: Decimal = Decimal('0.0')
    net_bonus_change: Decimal = Decimal('0.0')
    # transactions_count: int = 0

class BonusDynamicsReportDataSchema(BaseSchema):
    # report_metadata: ReportSchema
    group_id_filter: Optional[uuid.UUID] = Field(None)
    date_from: Optional[date]
    date_to: Optional[date]
    dynamics: List[BonusDynamicsDataItemSchema] = Field(default_factory=list)
    summary: Optional[Dict[str, Any]] = Field(None)


# --- Загальна схема відповіді, що містить дані звіту ---
# Ця схема може використовуватися, якщо звіт повертається як JSON у тілі відповіді,
# а не як посилання на файл.
class ReportDataResponseSchema(BaseSchema):
    """
    Загальна схема для відповіді, що містить дані згенерованого звіту.
    Поле `data` буде містити специфічну структуру для кожного типу звіту.
    """
    report_code: str = Field(..., description="Код типу звіту, що повертається")
    generated_at: datetime = Field(..., description="Час генерації даних звіту")
    parameters_used: Optional[Dict[str, Any]] = Field(None, description="Параметри, що були використані для генерації")

    # Дані звіту. Тип `Any` дозволяє гнучкість, але краще використовувати
    # `Union` з усіма можливими схемами даних звітів, якщо їх небагато.
    # Або ж, кожен ендпоінт звіту повертає свою чітко типізовану схему.
    # Поки що `Any` для загальності.
    # data: Any = Field(..., description="Дані звіту")

    # Приклад з Union (якщо є відомий набір схем даних звітів):
    data: Union[
        UserActivityReportDataSchema,
        TaskPopularityReportDataSchema,
        BonusDynamicsReportDataSchema,
        Dict[str, Any] # Запасний варіант для інших або простих звітів
    ] = Field(..., description="Дані звіту")


# TODO: Визначити конкретні схеми даних для кожного типу звіту, передбаченого в ТЗ.
# Наведені вище - лише приклади.
#
# Структура даних звіту (`...ReportDataSchema`) має бути добре продумана,
# щоб бути інформативною та легкою для використання на клієнті (наприклад, для побудови графіків).
#
# `ReportDataResponseSchema` - це обгортка, яка може містити метадані про звіт
# (код, час генерації, параметри) та самі дані.
#
# Якщо звіти завжди повертаються як файли (PDF, CSV), то цей файл `response.py`
# може бути непотрібним, або містити лише схему, що підтверджує початок генерації
# та посилання на статус запиту звіту (з `ReportSchema` з `report.py`).
#
# Поточний підхід передбачає, що деякі звіти можуть повертати дані як JSON,
# тому ці схеми є доречними.
#
# `report_metadata` в кожній `...ReportDataSchema` (закоментоване) - це якщо потрібно
# дублювати метадані з `ReportModel` прямо в даних звіту. Зазвичай це не потрібно,
# якщо метадані звіту (як запису в БД) та дані звіту (результат) розділені.
#
# Використання `Union` в `ReportDataResponseSchema.data` є хорошим способом
# типізувати можливі структури даних, якщо їх набір відомий і обмежений.
# Якщо типів звітів багато або їх структура дуже динамічна, `Dict[str, Any]`
# може бути більш практичним, але менш безпечним з точки зору типів.
#
# Все виглядає як хороший початок для визначення схем відповідей звітів.
# Подальша деталізація залежатиме від специфікацій кожного звіту.
# Назва файлу `response.py` відповідає `structure-claude-v3.md`.
#
# Все виглядає добре.
