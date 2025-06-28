# backend/app/src/api/graphql/queries/report.py
# -*- coding: utf-8 -*-
"""
GraphQL запити (Queries), пов'язані зі звітами.
"""

import strawberry
from typing import Optional, List, Any, Dict # Dict[str, Any] або strawberry.JSON
from datetime import datetime

# Імпорт GraphQL типів
# Потрібно визначити GraphQL тип для представлення звіту,
# можливо, гнучкий, оскільки структура даних звітів може сильно відрізнятися.
# from backend.app.src.api.graphql.types.report import ReportType, AvailableReportType # Прикладні назви

# TODO: Імпортувати сервіси
# from backend.app.src.services.report.report_service import ReportService
# from backend.app.src.core.dependencies import get_current_active_user, get_current_superuser, get_current_group_admin

@strawberry.type
class ReportParameterType:
    """Опис параметра, необхідного для генерації звіту."""
    name: str = strawberry.field(description="Назва параметра.")
    description: Optional[str] = strawberry.field(description="Опис параметра.")
    type: str = strawberry.field(description="Тип даних параметра (напр., 'string', 'integer', 'date', 'boolean').")
    is_required: bool = strawberry.field(description="Чи є параметр обов'язковим.")

@strawberry.type
class AvailableReportType:
    """Опис доступного типу звіту."""
    code: str = strawberry.field(description="Унікальний код типу звіту.")
    name: str = strawberry.field(description="Людсько-читабельна назва звіту.")
    description: Optional[str] = strawberry.field(description="Опис звіту.")
    required_permissions: Optional[List[str]] = strawberry.field(description="Список прав, необхідних для генерації звіту (коди).")
    available_parameters: Optional[List[ReportParameterType]] = strawberry.field(description="Список параметрів, які можна передати для генерації звіту.")

@strawberry.type
class ReportType:
    """GraphQL тип для представлення згенерованого звіту."""
    report_code: str = strawberry.field(description="Код типу згенерованого звіту.")
    title: str = strawberry.field(description="Заголовок звіту.")
    generated_at: datetime = strawberry.field(description="Час генерації звіту.")
    # Параметри, що були використані для генерації (може бути JSON)
    parameters_used: Optional[strawberry.JSON] = strawberry.field(description="Параметри, використані для генерації звіту.")
    # Дані звіту (гнучка структура, тому JSON)
    data: strawberry.JSON = strawberry.field(description="Дані звіту у форматі JSON.")


@strawberry.input
class ReportGenerationParamsInput:
    """Вхідні параметри для генерації звіту (ключ-значення)."""
    # Оскільки параметри динамічні, важко визначити їх статично.
    # Один з варіантів - передавати як список пар ключ-значення або JSON об'єкт.
    # Або для кожного звіту мати свій Input тип.
    # Поки що, припустимо, що параметри передаються як JSON об'єкт.
    # Цей інпут може бути необов'язковим, якщо звіт не потребує параметрів.
    params_json: Optional[strawberry.JSON] = strawberry.field(description="JSON об'єкт з параметрами для звіту (ключ-значення).")
    group_id: Optional[strawberry.ID] = strawberry.field(description="ID групи, якщо звіт генерується в контексті групи.")
    # date_from: Optional[datetime] = None
    # date_to: Optional[datetime] = None


@strawberry.type
class ReportQueries:
    """
    Клас, що групує GraphQL запити, пов'язані зі звітами.
    """

    @strawberry.field(description="Отримати список доступних типів звітів для поточного користувача.")
    async def available_reports(self, info: strawberry.Info) -> List[AvailableReportType]:
        """
        Повертає список типів звітів, які може генерувати поточний користувач,
        разом з описом та необхідними параметрами.
        """
        # context = info.context
        # current_user = context.current_user # Потрібен для перевірки прав
        #
        # report_service = ReportService(context.db_session)
        # available_reports_data = await report_service.get_available_reports_list(user=current_user)
        # # Сервіс має повернути список даних, які можна перетворити на AvailableReportType
        # return [AvailableReportType(**data) for data in available_reports_data]

        # Заглушка
        return [
            AvailableReportType(code="user_activity_summary", name="Підсумок активності користувача", description="Загальний звіт по активності.", required_permissions=["view_reports"], available_parameters=[]),
            AvailableReportType(code="group_task_completion_rate", name="Рівень виконання завдань в групі", description="Статистика по завданнях.", required_permissions=["group_admin"], available_parameters=[ReportParameterType(name="group_id", description="ID групи", type="ID", is_required=True)])
        ]

    @strawberry.field(description="Згенерувати та отримати звіт за його кодом та параметрами.")
    async def generate_report(
        self, info: strawberry.Info,
        report_code: str = strawberry.field(description="Код типу звіту для генерації."),
        params: Optional[ReportGenerationParamsInput] = None
    ) -> Optional[ReportType]:
        """
        Генерує та повертає вказаний звіт.
        Права доступу перевіряються на основі типу звіту та переданих параметрів.
        """
        # context = info.context
        # current_user = context.current_user
        # if not current_user:
        #     raise Exception("Автентифікація обов'язкова")
        #
        # report_service = ReportService(context.db_session)
        #
        # # Перетворення вхідних GraphQL параметрів на формат, зрозумілий сервісу
        # service_params = {}
        # if params:
        #     if params.params_json:
        #         service_params.update(params.params_json)
        #     if params.group_id:
        #         # Розкодувати group_id, якщо потрібно
        #         service_params['group_id'] = Node.decode_id_to_int(params.group_id, "GroupType")
        #
        # # Сервіс має перевірити права доступу та згенерувати звіт
        # report_data_schema = await report_service.generate_report(
        #     report_code=report_code,
        #     params=service_params, # Передаємо підготовлені параметри
        #     requesting_user=current_user
        # )
        #
        # if not report_data_schema: # Якщо звіт не знайдено, немає даних або немає прав
        #     return None
        #
        # # Припускаємо, що report_data_schema - це Pydantic схема ReportResponseSchema з REST API
        # # Потрібно її адаптувати до GraphQL ReportType
        # return ReportType(
        #     report_code=report_data_schema.report_type,
        #     title=report_data_schema.title,
        #     generated_at=report_data_schema.generated_at,
        #     parameters_used=report_data_schema.parameters_used,
        #     data=report_data_schema.data
        # )

        # Заглушка
        if report_code == "user_activity_summary":
            return ReportType(
                report_code=report_code, title="Підсумок активності (заглушка)",
                generated_at=datetime.utcnow(), parameters_used=params.params_json if params else {},
                data={"total_logins": 10, "tasks_done": 5}
            )
        return None

# Експорт класу для агрегації в queries/__init__.py
__all__ = [
    "ReportQueries",
    "AvailableReportType",
    "ReportParameterType",
    "ReportType",
    "ReportGenerationParamsInput",
]
