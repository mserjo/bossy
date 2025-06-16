# backend/app/src/api/v1/system/init_data.py
# -*- coding: utf-8 -*-
"""
API ендпоінт для ініціалізації початкових даних системи.

Надає захищений ендпоінт, який дозволяє суперкористувачам
запускати процес заповнення бази даних початковими даними,
такими як довідники, системні користувачі, базові налаштування тощо.

Сумісність: Python 3.13, SQLAlchemy v2, Pydantic v2.
"""

from typing import Dict, Any, Optional, List
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, ConfigDict

# Залежності API та моделі користувача
from backend.app.src.api.dependencies import get_current_active_superuser
from backend.app.src.models.auth import User as UserModel  # Для типізації current_user

# Сервіс ініціалізації
from backend.app.src.services.system.initial_data_service import (
    InitialDataService,
    InitializationResult as ServiceInitializationResult,  # Результат з сервісу
    InitializationStepDetail as ServiceStepDetail  # Деталі кроку з сервісу
)
# Логер з конфігурації
from backend.app.src.config.logging import logger  # Використовуємо централізований логер

router = APIRouter()


# --- Pydantic схеми для відповіді ---

class InitializationStatusEnum(str, Enum):
    """
    Можливі статуси процесу ініціалізації.
    """
    SUCCESS = "success"  # Успішно завершено
    SKIPPED_ALREADY_DONE = "skipped_already_done"  # Пропущено, бо вже виконувалось
    PARTIAL_SUCCESS = "partial_success"  # Частково успішно (деякі кроки могли не виконатись)
    ERROR = "error"  # Загальна помилка під час виконання
    CRITICAL_ERROR = "critical_error"  # Критична помилка, що перервала процес
    CONFLICT = "conflict"  # Конфлікт, наприклад, процес вже запущено


class InitializationStepResponse(BaseModel):
    """
    Схема для представлення результату окремого кроку ініціалізації.
    """
    model_config = ConfigDict(from_attributes=True)

    step_name: str = Field(..., description="Назва кроку ініціалізації.")  # i18n
    success: bool = Field(..., description="Чи успішно виконано крок.")
    message: Optional[str] = Field(None, description="Повідомлення про результат кроку.")  # i18n
    details: Optional[Dict[str, Any]] = Field(None, description="Додаткові деталі виконання кроку.")


class FullInitializationResponse(BaseModel):
    """
    Схема для відповіді ендпоінта ініціалізації даних.
    """
    model_config = ConfigDict(from_attributes=True)

    overall_status: InitializationStatusEnum = Field(..., description="Загальний статус процесу ініціалізації.")
    message: str = Field(..., description="Загальне повідомлення про результат.")  # i18n
    steps: List[InitializationStepResponse] = Field(default_factory=list,
                                                    description="Результати окремих кроків ініціалізації.")


# --- Ендпоінт ---

@router.post(
    "/trigger-initialization",
    response_model=FullInitializationResponse,
    summary="Запустити процес ініціалізації/перевірки початкових даних системи",  # i18n
    description="""Цей ендпоінт запускає процес заповнення або перевірки бази даних
необхідними початковими даними (довідники, системні користувачі, базові налаштування).
Доступно тільки суперкористувачам.
Реальний сервіс ініціалізації має бути **ідемпотентним** (безпечним для повторного запуску).""",  # i18n
    dependencies=[Depends(get_current_active_superuser)],  # Захист ендпоінта
    responses={
        status.HTTP_200_OK: {
            "description": "Процес ініціалізації успішно запущено та завершено, або вже був виконаний, або частково успішний."},
        # i18n
        status.HTTP_409_CONFLICT: {"description": "Процес ініціалізації вже виконується."},  # i18n
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Критична помилка під час процесу ініціалізації."}
        # i18n
    }
)
async def trigger_system_data_initialization(
        service: InitialDataService = Depends(),  # Впровадження залежності InitialDataService
        current_user: UserModel = Depends(get_current_active_superuser)  # Для логування, хто запустив
) -> FullInitializationResponse:
    """
    Запускає сервіс для ініціалізації або перевірки початкових даних системи.
    Включає:
    - Ініціалізацію базових довідників (ролі, статуси, типи тощо).
    - Створення/перевірку системних користувачів (наприклад, суперкористувач `odin`).
    - Встановлення системних налаштувань за замовчуванням.

    Цей процес має бути ідемпотентним.
    """
    triggered_by_username = current_user.username if current_user else "unknown_superuser"
    logger.info(
        f"Запит на ініціалізацію початкових даних системи від суперкористувача '{triggered_by_username}'.")  # i18n

    try:
        # Виклик реального сервісу
        service_result: ServiceInitializationResult = await service.run_full_initialization()

        # Перетворення результатів кроків сервісу на відповіді API
        api_steps_response: List[InitializationStepResponse] = []
        if service_result.step_details:
            for step_detail in service_result.step_details:
                api_steps_response.append(
                    InitializationStepResponse(
                        step_name=step_detail.step_name,
                        success=step_detail.success,
                        message=step_detail.message,
                        details=step_detail.details
                    )
                )

        api_response = FullInitializationResponse(
            overall_status=InitializationStatusEnum(service_result.status.value),
            # Переконуємося, що статус є членом Enum
            message=service_result.message,  # i18n
            steps=api_steps_response
        )

        if api_response.overall_status == InitializationStatusEnum.CRITICAL_ERROR:
            logger.error(
                f"Критична помилка під час ініціалізації даних, запущеної '{triggered_by_username}'. Деталі: {api_response.message}, Кроки: {api_response.steps}")  # i18n
            # Викидаємо HTTP виняток, щоб FastAPI повернув 500
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=api_response.message
            )
        elif api_response.overall_status == InitializationStatusEnum.CONFLICT:
            logger.warning(
                f"Конфлікт під час ініціалізації даних, запущеної '{triggered_by_username}': {api_response.message}")  # i18n
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=api_response.message
            )

        # Для SUCCESS, SKIPPED_ALREADY_DONE, PARTIAL_SUCCESS, ERROR (не критична) - повертаємо 200 OK
        # Логуємо відповідно
        if api_response.overall_status in [InitializationStatusEnum.ERROR, InitializationStatusEnum.PARTIAL_SUCCESS]:
            logger.warning(
                f"Ініціалізація даних, запущена '{triggered_by_username}', завершилася з проблемами. Статус: {api_response.overall_status}. Повідомлення: {api_response.message}. Кроки: {api_response.steps}")  # i18n
        else:
            logger.info(
                f"Ініціалізація даних, запущена '{triggered_by_username}', успішно оброблена. Статус: {api_response.overall_status}. Повідомлення: {api_response.message}.")  # i18n

        return api_response

    except HTTPException as http_exc:  # Перепрокидаємо HTTP винятки, що були викинуті вище
        raise http_exc
    except Exception as e:
        # Непередбачені помилки, які не були оброблені сервісом як ServiceInitializationResult
        logger.error(f"Непередбачена критична помилка під час виклику сервісу ініціалізації даних: {e}", exc_info=True)
        # Повертаємо стандартизовану відповідь про критичну помилку
        return FullInitializationResponse(
            overall_status=InitializationStatusEnum.CRITICAL_ERROR,
            message=f"Критична помилка на сервері: {str(e)}",  # i18n
            steps=[]
        )
        # Або, якщо хочемо, щоб FastAPI обробив це як 500 помилку, можна підняти HTTPException:
        # raise HTTPException(
        #     status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        #     detail=f"Критична помилка на сервері під час спроби ініціалізації даних: {str(e)}" # i18n
        # )


logger.info("Маршрутизатор для ендпоінта ініціалізації даних API v1 (`init_data.router`) визначено.")  # i18n
# Примітка: назва файлу init_data.py, лог повідомлення було init_data_endpoints.router. Виправлено на init_data.router.
