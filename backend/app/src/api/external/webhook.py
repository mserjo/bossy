# backend/app/src/api/external/webhook.py
from typing import Any, Dict, Optional # Додано Optional
from fastapi import APIRouter, Depends, Request, Header, HTTPException, status # Додано Optional
from sqlalchemy.ext.asyncio import AsyncSession
import logging

# from app.src.core.dependencies import get_db_session # Якщо потрібен доступ до БД
# from app.src.services.external.webhook import WebhookService # Майбутній сервіс для обробки вебхуків

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post(
    "/generic", # Шлях відносно /external/webhook/generic (або просто /external/generic)
    summary="Загальний приймач вебхуків",
    description="""Приймає вебхуки від неспецифікованих зовнішніх сервісів.
    На даний момент цей ендпоінт є концептуальним (placeholder) і лише логує отримані дані.
    В майбутньому тут буде реалізована логіка валідації (наприклад, перевірка підпису) та маршрутизації до відповідних обробників."""
)
async def generic_webhook_receiver(
    request: Request, # Використовуємо Request для доступу до тіла, заголовків тощо.
    # x_webhook_signature: Optional[str] = Header(None, alias="X-Webhook-Signature"), # Приклад для підпису
    # db: AsyncSession = Depends(get_db_session), # Якщо обробник потребує БД
    # webhook_service: WebhookService = Depends() # Якщо є загальний сервіс
):
    '''
    Загальний ендпоінт для прийому вебхуків.
    - Логує заголовки та тіло запиту.
    - В майбутньому: валідація підпису, маршрутизація до сервісів.
    '''
    headers = dict(request.headers)
    body = await request.body()

    logger.info(f"Отримано загальний вебхук:")
    logger.info(f"Заголовки: {headers}")
    try:
        # Спробуємо розпарсити тіло як JSON для логування, якщо можливо
        json_body = await request.json()
        logger.info(f"Тіло (JSON): {json_body}")
    except Exception:
        logger.info(f"Тіло (raw, не JSON): {body.decode(errors='ignore')}")

    # Тут може бути логіка для визначення типу вебхука та його обробки
    # Наприклад, webhook_service.process_generic_webhook(headers=headers, body=body)

    # Поки що просто повертаємо успішну відповідь
    return {"status": "received", "message": "Загальний вебхук отримано та залоговано."}

# Міркування:
# 1.  Placeholder: Цей ендпоінт є заглушкою для неспецифікованих вебхуків.
# 2.  Безпека: Для реальних вебхуків критично важливою є валідація (перевірка підписів, токенів).
#     Це має бути реалізовано перед обробкою будь-яких даних. Коментарі про це додані.
# 3.  Обробка: `WebhookService` (або більш спеціалізовані сервіси) має обробляти логіку вебхуків.
# 4.  Асинхронність: Обробка вебхуків може бути тривалою, тому варто розглянути використання фонових завдань (BackgroundTasks).
# 5.  Коментарі: Українською мовою.
# 6.  URL: Цей роутер буде підключений до `external_api_router` (в `external/__init__.py`),
#     можливо з префіксом `/webhook`. Тоді шлях буде `/external/webhook/generic`.
