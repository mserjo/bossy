# backend/app/src/api/v1/system/init_data_endpoints.py
# -*- coding: utf-8 -*-
"""
API ендпоінт для ініціалізації початкових даних системи.

Надає захищений ендпоінт, який дозволяє суперкористувачам
запускати процес заповнення бази даних початковими даними,
такими як довідники, системні користувачі, базові налаштування тощо.
"""

import logging
import asyncio # Для імітації тривалого процесу
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status

# Залежності API
from app.src.api.dependencies import get_current_active_superuser

# Сервіси (заглушки, будуть визначені в app.src.services.system.initialization)
# from app.src.services.system.initialization_service import InitialDataService

logger = logging.getLogger(__name__)

router = APIRouter()

# --- Заглушка для сервісу ініціалізації даних ---
class FakeInitialDataService:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._is_running_lock = asyncio.Lock() # Для запобігання одночасному запуску
        self._initialization_done_once = False # Прапорець, що ініціалізація вже проводилась (для ідемпотентності заглушки)

    async def initialize_base_dictionaries(self) -> Dict[str, Any]:
        self.logger.info("FakeInitialDataService: Ініціалізація базових довідників...")
        await asyncio.sleep(0.5) # Імітація роботи з БД
        # У реальному сервісі:
        # created_count = await dictionary_repository.create_initial_statuses_if_not_exist()
        # created_count += await dictionary_repository.create_initial_user_roles_if_not_exist()
        # ... і так далі для всіх довідників
        self.logger.info("FakeInitialDataService: Базові довідники успішно ініціалізовані/перевірені.")
        return {"dictionaries_initialized": True, "details": "Статуси, Ролі, Типи користувачів, Типи груп тощо (заглушка)."}

    async def create_system_users(self) -> Dict[str, Any]:
        self.logger.info("FakeInitialDataService: Створення/перевірка системних користувачів (odin, shadow)...")
        await asyncio.sleep(0.3) # Імітація роботи з БД
        # У реальному сервісі:
        # odin_created_or_exists = await user_service.create_user_if_not_exists(SUPERUSER_ODIN_DATA)
        # shadow_created_or_exists = await user_service.create_user_if_not_exists(SYSTEM_BOT_SHADOW_DATA)
        self.logger.info("FakeInitialDataService: Системні користувачі 'odin' та 'shadow' успішно перевірені/створені.")
        return {"system_users_created_or_verified": True, "details": "Користувачі 'odin' та 'shadow' перевірені/створені (заглушка)."}

    async def setup_default_settings(self) -> Dict[str, Any]:
        self.logger.info("FakeInitialDataService: Встановлення системних налаштувань за замовчуванням...")
        await asyncio.sleep(0.2)
        # У реальному сервісі:
        # await system_settings_service.apply_default_settings_if_not_set()
        self.logger.info("FakeInitialDataService: Системні налаштування за замовчуванням встановлені/перевірені.")
        return {"default_settings_applied": True, "details": "Базові системні налаштування встановлено (заглушка)."}


    async def run_full_initialization(self) -> Dict[str, Any]:
        if self._is_running_lock.locked():
            self.logger.warning("FakeInitialDataService: Спроба повторного запуску ініціалізації, поки попередня ще виконується.")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Процес ініціалізації вже запущено. Будь ласка, зачекайте."
            )

        async with self._is_running_lock: # Захоплюємо лок
            self.logger.info("FakeInitialDataService: Початок повного процесу ініціалізації даних...")
            # if self._initialization_done_once: # Імітація ідемпотентності для заглушки
            #     self.logger.info("FakeInitialDataService: Ініціалізація вже проводилася раніше. Пропускаємо (ідемпотентність заглушки).")
            #     return {
            #         "status": "skipped_already_done",
            #         "message": "Ініціалізація початкових даних вже проводилася раніше (заглушка)."
            #     }

            results = {}
            all_steps_successful = True
            try:
                results["dictionaries"] = await self.initialize_base_dictionaries()
                if not results["dictionaries"].get("dictionaries_initialized"): all_steps_successful = False

                await asyncio.sleep(0.1)

                results["system_users"] = await self.create_system_users()
                if not results["system_users"].get("system_users_created_or_verified"): all_steps_successful = False

                await asyncio.sleep(0.1)

                results["default_settings"] = await self.setup_default_settings()
                if not results["default_settings"].get("default_settings_applied"): all_steps_successful = False

                # Додайте інші кроки ініціалізації тут

                if all_steps_successful:
                    self.logger.info("FakeInitialDataService: Повний процес ініціалізації даних успішно завершено.")
                    self._initialization_done_once = True # Позначаємо, що ініціалізація пройшла
                    return {
                        "status": "success",
                        "message": "Ініціалізація початкових даних системи успішно завершена (заглушка).",
                        "details": results
                    }
                else:
                    self.logger.error("FakeInitialDataService: Один або декілька кроків ініціалізації не вдалися.")
                    return {
                        "status": "error",
                        "message": "Під час ініціалізації виникли помилки на деяких кроках.",
                        "details": results
                    }
            except Exception as e:
                self.logger.error(f"FakeInitialDataService: Критична помилка під час ініціалізації даних: {e}", exc_info=True)
                # self._is_running_lock вже звільнено завдяки context manager
                return { # Повертаємо помилку, але HTTP статус буде встановлено в ендпоінті
                    "status": "critical_error",
                    "message": f"Критична помилка під час ініціалізації: {str(e)}",
                    "details": results # Часткові результати, якщо є
                }
        # Лок автоматично звільняється тут

_fake_init_data_service = FakeInitialDataService() # Екземпляр сервісу-заглушки

# --- Ендпоінт ---

@router.post(
    "/trigger-initialization",
    summary="Запустити процес ініціалізації/перевірки початкових даних системи",
    description="Цей ендпоінт запускає процес заповнення або перевірки бази даних "
                "необхідними початковими даними (довідники, системні користувачі, базові налаштування). "
                "Доступно тільки суперкористувачам. "
                "Реальний сервіс ініціалізації має бути **ідемпотентним** (безпечним для повторного запуску).",
    dependencies=[Depends(get_current_active_superuser)], # Захист ендпоінта
    responses={
        status.HTTP_200_OK: {"description": "Процес ініціалізації успішно запущено та завершено (або вже був виконаний)."},
        status.HTTP_409_CONFLICT: {"description": "Процес ініціалізації вже виконується."},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Помилка під час процесу ініціалізації."}
    }
)
async def trigger_system_data_initialization(
    # У реальному проекті сервіс ін'єктувався б так:
    # service: InitialDataService = Depends(get_initial_data_service_dependency),
    current_user: Dict[str, Any] = Depends(get_current_active_superuser) # Для логування, хто запустив
):
    """
    Запускає сервіс для ініціалізації або перевірки початкових даних системи.
    Включає:
    - Ініціалізацію базових довідників (ролі, статуси, типи тощо).
    - Створення/перевірку системних користувачів (наприклад, суперкористувач `odin`).
    - Встановлення системних налаштувань за замовчуванням.

    Цей процес має бути ідемпотентним.
    """
    triggered_by_username = current_user.get("username", "unknown_superuser")
    logger.info(f"Запит на ініціалізацію початкових даних системи від суперкористувача '{triggered_by_username}'.")

    try:
        # result = await service.run_full_initialization() # Реальний виклик
        result = await _fake_init_data_service.run_full_initialization() # Виклик заглушки

        result_status = result.get("status")
        if result_status == "error" or result_status == "critical_error":
            # Якщо сервіс сам обробив помилку і повернув відповідний статус
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("message", "Невідома помилка під час ініціалізації даних.")
            )
        # elif result_status == "skipped_already_done":
        #     # Можна повернути 200 OK з відповідним повідомленням, або інший статус, наприклад, 202 Accepted
        #     return result

        logger.info(f"Ініціалізація даних, запущена '{triggered_by_username}', успішно оброблена. Статус: {result_status}.")
        return result # Повертаємо результат від сервісу (успіх або "skipped")

    except HTTPException as http_exc: # Наприклад, HTTP_409_CONFLICT з сервісу
        logger.warning(f"HTTP виняток під час ініціалізації даних: {http_exc.detail}")
        raise http_exc # Перепрокидаємо далі
    except Exception as e:
        logger.error(f"Непередбачена помилка під час виклику сервісу ініціалізації даних: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Критична помилка на сервері під час спроби ініціалізації даних: {str(e)}"
        )

logger.info("Маршрутизатор для ендпоінта ініціалізації даних API v1 (`init_data_endpoints.router`) визначено.")
