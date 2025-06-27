# backend/app/src/api/external/webhook.py
# -*- coding: utf-8 -*-
"""
Загальний ендпоінт для прийому вебхуків від різних сервісів.

Цей модуль може містити:
- Один або декілька загальних ендпоінтів, які приймають вебхуки.
- Логіку для ідентифікації джерела вебхука (наприклад, за заголовками, параметрами URL).
- Базову валідацію та передачу даних на подальшу обробку відповідним сервісам
  (наприклад, через черги завдань Celery або фонові задачі FastAPI).

Автентифікація вебхуків тут є критично важливою (наприклад, перевірка підпису, секретних токенів).
"""

from fastapi import APIRouter, Request, HTTPException, status, Depends, Body
from typing import Any, Dict

# from backend.app.src.config.logging import get_logger
# from backend.app.src.core.security import verify_webhook_signature # Приклад функції валідації

# logger = get_logger(__name__)
router = APIRouter()

# TODO: Реалізувати механізми безпеки для вебхуків (наприклад, перевірка підписів)
# async def verify_signature_dependency(request: Request, secret_token: str = "YOUR_SECRET_TOKEN"):
#     """
#     Приклад залежності для перевірки підпису вебхука.
#     Потребує реальної логіки перевірки.
#     """
#     # received_signature = request.headers.get("X-Webhook-Signature")
#     # if not verify_webhook_signature(await request.body(), secret_token, received_signature):
#     #     logger.warning(f"Невалідний підпис вебхука для {request.url.path}")
#     #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Невалідний підпис вебхука")
#     pass


@router.post("/generic", tags=["Webhooks"])
async def handle_generic_webhook(
    request: Request,
    payload: Dict[str, Any] = Body(...),
    # signature_check: Any = Depends(verify_signature_dependency) # Приклад використання залежності
):
    """
    Загальний ендпоінт для прийому вебхуків.

    Очікує JSON payload. Має бути захищений перевіркою підпису або іншим механізмом.
    Логіка маршрутизації на основі вмісту payload або заголовків запиту.

    Args:
        request (Request): Об'єкт запиту FastAPI.
        payload (Dict[str, Any]): Тіло запиту, розпарсений JSON.
    """
    # logger.info(f"Отримано загальний вебхук від {request.client.host} для {request.url.path}")
    # logger.debug(f"Payload вебхука: {payload}")

    # TODO: Додати логіку для ідентифікації джерела та типу вебхука.
    # Наприклад, перевірити наявність певних полів у payload або спеціальних заголовків.
    # source_service = request.headers.get("X-Source-Service", "unknown")

    # TODO: Додати логіку для передачі payload на подальшу обробку.
    # Це може бути виклик сервісу, постановка завдання в чергу (Celery) тощо.
    # if source_service == "service_A":
    #     # process_service_A_webhook(payload)
    #     pass
    # elif source_service == "service_B":
    #     # process_service_B_webhook(payload)
    #     pass
    # else:
    #     logger.warning(f"Невідомий тип вебхука або сервіс: {source_service}")
    #     # Можна повернути помилку, якщо вебхук не вдалося ідентифікувати.
    #     # raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Невідомий тип вебхука")

    return {"status": "success", "message": "Вебхук отримано та прийнято до обробки."}


# TODO: Додати інші специфічні загальні ендпоінти для вебхуків, якщо потрібно.
# Наприклад, якщо різні сервіси надсилають вебхуки на різні URL,
# але їх можна згрупувати під загальною логікою валідації чи маршрутизації.

# Цей роутер може бути підключений до головного API роутера
# або до спеціального роутера для зовнішніх API.
# Приклад підключення в backend/app/src/api/external/__init__.py або backend/app/src/api/router.py
# from backend.app.src.api.external.webhook import router as webhook_router
# main_router.include_router(webhook_router, prefix="/webhooks")
