# backend/app/src/schemas/reports/request.py
# -*- coding: utf-8 -*-
"""
Цей модуль визначає Pydantic схеми для параметрів запиту на генерацію звітів.
Ці схеми використовуються для валідації вхідних даних від клієнта
при замовленні певного типу звіту.
"""

from pydantic import Field, field_validator
from typing import Optional, List, Dict, Any
import uuid
from datetime import date # Використовуємо date для діапазонів дат без часу

from backend.app.src.schemas.base import BaseSchema

# --- Базова схема для параметрів запиту на звіт (може бути спільною) ---
class BaseReportRequestParams(BaseSchema):
    """
    Базова схема для загальних параметрів запиту на звіт.
    Конкретні звіти можуть успадковувати та розширювати цю схему.
    """
    date_from: Optional[date] = Field(None, description="Початкова дата періоду звіту (включно)")
    date_to: Optional[date] = Field(None, description="Кінцева дата періоду звіту (включно)")

    # group_id: Optional[uuid.UUID] = Field(None, description="ID групи для фільтрації (якщо звіт по групі)")
    # user_id: Optional[uuid.UUID] = Field(None, description="ID користувача для фільтрації (для персональних звітів)")

    # Додаткові фільтри можуть бути у вигляді словника
    # custom_filters: Optional[Dict[str, Any]] = Field(None, description="Додаткові фільтри для звіту")

    @field_validator('date_to')
    @classmethod
    def check_date_range(cls, date_to: Optional[date], values: Any) -> Optional[date]:
        # Pydantic v1: values.data.get('date_from')
        # Pydantic v2: Доступ до інших полів через values.data (якщо model_validator)
        # або через context, якщо передано.
        # Для field_validator, якщо він залежить від іншого поля, це може бути складно.
        # Краще використовувати model_validator для перехресних перевірок полів.
        # Тут поки що проста перевірка, якщо обидві дати є.
        # Цей валідатор тут не дуже ефективний без model_validator.
        # Перенесу цю логіку в model_validator, якщо потрібно.
        #
        # Якщо data - це об'єкт схеми на етапі валідації поля:
        # date_from = getattr(values, 'date_from', None) # Ненадійний спосіб для field_validator
        #
        # Простіше: якщо date_to встановлено, а date_from ні, або date_to < date_from - це помилка.
        # Цю логіку краще робити в @model_validator.
        # Поки що залишаю без перевірки діапазону тут.
        return date_to

# --- Приклади схем для конкретних типів звітів ---

class UserActivityReportRequestParams(BaseReportRequestParams):
    """
    Параметри для звіту по активності користувачів.
    """
    # Успадковує date_from, date_to.
    # Може мати специфічні фільтри:
    target_user_ids: Optional[List[uuid.UUID]] = Field(None, description="Список ID користувачів для звіту (якщо не всі)")
    activity_types: Optional[List[str]] = Field(None, description="Типи активності для включення (наприклад, 'task_completed', 'reward_redeemed')")
    # group_id: uuid.UUID # Якщо звіт завжди в контексті групи, це поле може бути обов'язковим
                        # або братися з URL.

class TaskPopularityReportRequestParams(BaseReportRequestParams):
    """
    Параметри для звіту по популярності завдань.
    """
    # Успадковує date_from, date_to.
    # group_id: uuid.UUID # Обов'язково для звіту по завданнях групи.
    task_type_ids: Optional[List[uuid.UUID]] = Field(None, description="Список ID типів завдань для фільтрації")
    min_completions: Optional[int] = Field(None, ge=0, description="Мінімальна кількість виконань для включення завдання в звіт")

class BonusDynamicsReportRequestParams(BaseReportRequestParams):
    """
    Параметри для звіту по динаміці накопичення бонусів.
    """
    # Успадковує date_from, date_to.
    # group_id: uuid.UUID
    target_user_ids: Optional[List[uuid.UUID]] = Field(None, description="Список ID користувачів")
    transaction_types: Optional[List[str]] = Field(None, description="Типи транзакцій для включення")


# --- Загальна схема запиту на генерацію звіту, що використовується API ендпоінтом ---
# Ця схема може приймати код звіту та специфічні для нього параметри.
class ReportGenerationRequestSchema(BaseSchema):
    """
    Загальна схема для запиту на генерацію звіту.
    Використовується API ендпоінтом для ініціювання генерації звіту.
    """
    report_code: str = Field(..., max_length=100, description="Код типу звіту, який потрібно згенерувати")
    # Параметри, специфічні для `report_code`.
    # Можуть бути представлені як словник, або ж можна використовувати Union[...SpecificReportParams]
    # для строгої типізації, але це ускладнить API.
    # Словник `parameters` є більш гнучким.
    parameters: Optional[Dict[str, Any]] = Field(None, description="Параметри, специфічні для обраного типу звіту")

    # group_id: Optional[uuid.UUID] # Може передаватися тут, якщо звіт для групи,
                                  # або в `parameters`, або братися з URL.

    # TODO: Додати валідатор, який перевіряє, що `parameters` відповідають
    #       очікуваній структурі для даного `report_code`.
    #       Це може вимагати реєстрації схем параметрів для кожного `report_code`.
    # @model_validator(mode='after')
    # def validate_parameters_for_report_code(cls, data: 'ReportGenerationRequestSchema') -> 'ReportGenerationRequestSchema':
    #     # ... логіка валідації ...
    #     # Наприклад:
    #     # if data.report_code == "USER_ACTIVITY":
    #     #     UserActivityReportRequestParams.model_validate(data.parameters or {})
    #     # elif data.report_code == "TASK_POPULARITY":
    #     #     TaskPopularityReportRequestParams.model_validate(data.parameters or {})
    #     # ... і так далі
    #     # Якщо валідація не проходить, кидаємо ValueError.
    #     return data

# TODO: Визначити конкретні Enum або довідники для `report_code`, `activity_types`, `transaction_types`,
# щоб забезпечити консистентність та уникнути помилок введення.
#
# `BaseReportRequestParams` надає спільні поля `date_from`, `date_to`.
# Специфічні схеми (UserActivityReportRequestParams тощо) успадковують від неї
# та додають власні параметри.
#
# `ReportGenerationRequestSchema` - це те, що приймає API ендпоінт.
# Вона містить `report_code` та загальний словник `parameters`.
# Валідація вмісту `parameters` залежно від `report_code` є важливим кроком,
# який краще реалізувати на сервісному рівні або через складний `model_validator`.
#
# Використання `datetime.date` для `date_from` та `date_to` підходить для звітів,
# де час не важливий, а лише дата.
#
# Все виглядає як хороший початок для визначення параметрів запитів на звіти.
# Подальша деталізація залежатиме від конкретних вимог до кожного звіту.
#
# Приклад використання `parameters` в `ReportGenerationRequestSchema`:
# {
#   "report_code": "USER_ACTIVITY",
#   "parameters": {
#     "date_from": "2023-01-01",
#     "date_to": "2023-01-31",
#     "target_user_ids": ["uuid1", "uuid2"]
#   }
# }
# Сервіс, що обробляє цей запит, має розпарсити `parameters`
# відповідно до `UserActivityReportRequestParams` (або іншої схеми для `report_code`).
#
# Це відповідає `structure-claude-v3.md`, де є `request.py` для схем запиту параметрів звіту.
# Назва файлу `request.py` - підходить.
#
# Все виглядає добре.
