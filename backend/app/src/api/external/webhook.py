# backend/app/src/api/external/webhook.py
# -*- coding: utf-8 -*-
"""
Загальні обробники вебхуків від зовнішніх сервісів.

Цей модуль може містити ендпоінти для прийому вебхуків від сервісів,
для яких ще не створено спеціалізованих обробників (наприклад, у `calendar.py` чи `messenger.py`),
або для дуже загальних потреб інтеграції.
"""
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Request, Header, HTTPException, status
# from sqlalchemy.ext.asyncio import AsyncSession # Розкоментувати, якщо потрібен доступ до БД
# import logging # Замінено на централізований логер

# Повні шляхи імпорту
# from backend.app.src.api.dependencies import get_api_db_session # Якщо потрібен доступ до БД
# from backend.app.src.services.external.webhook_service import WebhookService # Приклад майбутнього сервісу
from backend.app.src.config.logging import logger # Централізований логер
from backend.app.src.config import settings # Для доступу до секретів, якщо потрібна валідація

router = APIRouter()

@router.post(
    "/generic",
    summary="Загальний приймач вебхуків", # i18n
    description="""Приймає вебхуки від неспецифікованих зовнішніх сервісів.
    **УВАГА: Цей ендпоінт є концептуальним (заглушкою) і не реалізує жодних механізмів безпеки
    (валідація підпису, токенів тощо) за замовчуванням. Не використовувати в продакшені без належної валідації!**
    Він лише логує отримані дані. В майбутньому тут може бути реалізована логіка
    маршрутизації до відповідних обробників на основі заголовків або тіла запиту.""", # i18n
    deprecated=True # Позначаємо як застарілий, щоб підкреслити його статус заглушки
)
async def generic_webhook_receiver(
    request: Request,
    # TODO: Для реального використання додати параметри для валідації, наприклад:
    # x_custom_signature: Optional[str] = Header(None, alias="X-Custom-Signature"),
    # api_key: Optional[str] = Query(None) # Або інший механізм автентифікації
    # db: AsyncSession = Depends(get_api_db_session), # Якщо обробник потребує БД
    # webhook_service: WebhookService = Depends() # Якщо є загальний сервіс
):
    """
    Загальний ендпоінт для прийому вебхуків.
    - Логує заголовки та тіло запиту.
    - **ПОПЕРЕДЖЕННЯ**: Не має вбудованої валідації чи безпеки. Призначений для демонстрації або відладки.
    """
    # TODO: Критично! Перед використанням в реальних умовах, додати надійну валідацію
    #  (перевірка підписів HMAC, IP-адрес, секретних токенів тощо) для кожного очікуваного типу вебхука.
    #  Без валідації цей ендпоінт є вразливим.

    headers = dict(request.headers)
    body = await request.body() # Отримуємо тіло як байти

    logger.info(f"Отримано запит на загальний вебхук (/generic):")
    logger.info(f"  Метод: {request.method}")
    logger.info(f"  URL: {request.url}")
    logger.info(f"  Клієнт: {request.client.host if request.client else 'N/A'}:{request.client.port if request.client else 'N/A'}")
    logger.info(f"  Заголовки: {headers}")

    try:
        # Спроба розпарсити тіло як JSON для більш читабельного логування
        json_body = await request.json() # Цей метод вже був викликаний, якщо content-type JSON, інакше може бути помилка
                                         # Краще використовувати body, яке вже прочитано
        logger.info(f"  Тіло (спроба JSON): {json_body}")
    except Exception:
        # Якщо не JSON, логуємо як необроблений рядок (з обмеженням довжини)
        logger.info(f"  Тіло (raw, не JSON): {body.decode(errors='ignore')[:1000]}...") # Обмеження довжини для логу

    # Тут може бути логіка для визначення типу вебхука та його маршрутизації
    # на основі заголовків або вмісту тіла.
    # Наприклад:
    # if "X-Github-Event" in headers:
    #     # await process_github_webhook(json_body)
    #     pass
    # elif "X-Gitlab-Event" in headers:
    #     # await process_gitlab_webhook(json_body)
    #     pass

    # Поки що просто повертаємо успішну відповідь
    # i18n
    return {"status": "received", "message": "Загальний вебхук отримано та залоговано. Потрібна реалізація обробки та валідації."}


logger.info("Роутер для загальних вебхуків (`/external/webhook`) визначено.")
