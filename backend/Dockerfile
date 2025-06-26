# backend/Dockerfile
# -*- coding: utf-8 -*-
# Dockerfile для production середовища

# --- Етап 1: Збірка (Builder Stage) ---
# Використовуємо офіційний образ Python як базовий.
# Вказуємо версію Python, яка використовується в проекті (наприклад, 3.11 або 3.13, якщо доступний стабільний slim).
# Slim-версія менша за розміром.
FROM python:3.11-slim as builder

# Встановлюємо робочий каталог всередині контейнера
WORKDIR /opt/app

# Встановлюємо змінні середовища для Python
ENV PYTHONDONTWRITEBYTECODE 1 # Забороняє Python створювати .pyc файли
ENV PYTHONUNBUFFERED 1    # Забезпечує негайний вивід логів Python в консоль

# Оновлюємо pip та встановлюємо wheel для швидшої установки пакетів
RUN pip install --upgrade pip wheel

# Копіюємо файл requirements.txt та встановлюємо залежності
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо решту коду програми
# Припускаючи, що Dockerfile знаходиться в backend/, а код програми в backend/app/
COPY app /opt/app/app
COPY alembic /opt/app/alembic
COPY alembic.ini /opt/app/alembic.ini
# Якщо main.py знаходиться в backend/app/main.py, то він вже скопійований з app.

# --- Етап 2: Фінальний образ (Final Stage) ---
FROM python:3.11-slim

# Встановлюємо робочий каталог
WORKDIR /opt/app

# Змінні середовища
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV APP_ENV production

# Створюємо користувача без root-прав для запуску додатку
ARG APP_USER=appuser
ARG APP_USER_ID=1001
ARG APP_GROUP_ID=1001
RUN groupadd -g ${APP_GROUP_ID} ${APP_USER} && \
    useradd -u ${APP_USER_ID} -g ${APP_GROUP_ID} -m -s /bin/sh ${APP_USER}

# Копіюємо встановлені залежності (site-packages) та код програми з етапу збірки
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder /opt/app/app /opt/app/app
COPY --from=builder /opt/app/alembic /opt/app/alembic
COPY --from=builder /opt/app/alembic.ini /opt/app/alembic.ini

# Надаємо права на каталог додатку новому користувачеві
RUN chown -R ${APP_USER}:${APP_USER} /opt/app

# Переключаємося на користувача без root-прав
USER ${APP_USER}

# Порт, який додаток буде слухати
EXPOSE ${APP_PORT:-8000}

# Команда для запуску додатку
# Припускаючи, що main.py знаходиться в /opt/app/app/main.py
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "${APP_PORT:-8000}"]

# --- Healthcheck ---
# TODO: Створити ендпоінт /api/v1/system/health в додатку та розкоментувати.
# HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
#   CMD wget --quiet --tries=1 --spider http://localhost:${APP_PORT:-8000}/api/v1/system/health || exit 1
