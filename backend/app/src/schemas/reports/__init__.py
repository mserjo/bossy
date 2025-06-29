# backend/app/src/schemas/reports/__init__.py
# -*- coding: utf-8 -*-
"""
Ініціалізаційний файл для пакету схем, пов'язаних зі звітами (`reports`).

Цей файл робить доступними основні схеми звітів для імпорту з пакету
`backend.app.src.schemas.reports`.

Приклад імпорту:
from backend.app.src.schemas.reports import ReportSchema, ReportGenerationRequestSchema

Також цей файл може використовуватися для визначення змінної `__all__`,
яка контролює, що саме експортується при використанні `from . import *`.
"""

# Імпорт схем метаданих звіту (з report.py)
from backend.app.src.schemas.reports.report import (
    ReportSchema,
    ReportCreateSchema,
    ReportUpdateSchema,
)

# Імпорт схем для параметрів запиту на генерацію звіту (з request.py)
from backend.app.src.schemas.reports.request import (
    BaseReportRequestParams,
    UserActivityReportRequestParams,
    TaskPopularityReportRequestParams,
    BonusDynamicsReportRequestParams,
    ReportGenerationRequestSchema,
)

# Імпорт схем для даних у відповіді API (з response.py)
from backend.app.src.schemas.reports.response import (
    ReportDataItemSchema, # Базова схема для рядка даних
    UserActivityDataItemSchema,
    UserActivityReportDataSchema,
    TaskPopularityDataItemSchema,
    TaskPopularityReportDataSchema,
    BonusDynamicsDataItemSchema,
    BonusDynamicsReportDataSchema,
    ReportDataResponseSchema, # Загальна обгортка для відповіді з даними звіту
)

# Визначення змінної `__all__` для контролю публічного API пакету.
__all__ = [
    # Report Metadata Schemas (from report.py)
    "ReportSchema",
    "ReportCreateSchema",
    "ReportUpdateSchema",

    # Report Request Parameter Schemas (from request.py)
    "BaseReportRequestParams",
    "UserActivityReportRequestParams",
    "TaskPopularityReportRequestParams",
    "BonusDynamicsReportRequestParams",
    "ReportGenerationRequestSchema",

    # Report Data/Response Schemas (from response.py)
    "ReportDataItemSchema",
    "UserActivityDataItemSchema",
    "UserActivityReportDataSchema",
    "TaskPopularityDataItemSchema",
    "TaskPopularityReportDataSchema",
    "BonusDynamicsDataItemSchema",
    "BonusDynamicsReportDataSchema",
    "ReportDataResponseSchema",
]

# TODO: Переконатися, що всі необхідні схеми з цього пакету створені та включені до `__all__`.
# На даний момент включені схеми для метаданих звітів, параметрів запитів
# та приклади схем для даних у відповідях.
#
# Виклик model_rebuild для схем, що використовують ForwardRef,
# якщо вони є в цьому пакеті і залежать від інших схем цього ж пакету,
# або якщо це робиться централізовано тут.
# Наприклад, ReportSchema використовує ForwardRef.
# from typing import ForwardRef, List, Optional, Union, Any, Dict # Потрібні імпорти для контексту
# import uuid
# from datetime import datetime, date
# from decimal import Decimal
# from pydantic import BaseModel as PydanticBaseModel

# schemas_to_rebuild = [
#     ReportSchema,
#     # Інші схеми з цього пакету, якщо вони використовують ForwardRef на схеми цього ж пакету.
# ]

# for schema in schemas_to_rebuild:
#     try:
#         # schema.model_rebuild(force=True) # Pydantic v2
#         pass # Pydantic v2 зазвичай справляється
#     except Exception as e:
#         print(f"Warning: Could not rebuild schema {schema.__name__}: {e}")

# Поки що залишаю без явних викликів `model_rebuild`.

# Виклик model_rebuild для схем, що містять ForwardRef
# ReportSchema.model_rebuild() # Видалено, буде глобальний виклик
# ReportDataResponseSchema також може потребувати, якщо Union типи використовують ForwardRef,
# але зараз UserActivityReportDataSchema і т.д. не мають складних ForwardRef всередині.
# Якщо ReportDataResponseSchema.data буде містити схеми, що самі мають ForwardRef,
# то для ReportDataResponseSchema також може знадобитися model_rebuild.
# Поки що достатньо для ReportSchema.
# ReportDataResponseSchema.model_rebuild() # Видалено, буде глобальний виклик


# Все виглядає добре.
