# backend/Dockerfile
# # Dockerfile для збірки образу backend-додатку Kudos (Virtus).
# # Використовує багатостадійну збірку для оптимізації розміру кінцевого образу
# # та для розділення середовищ розробки та продуктового.
# # Цільова версія Python: 3.13.

# --- Базовий образ (Base Stage) ---
# Використовуємо офіційний образ Python 3.13 slim.
FROM python:3.13-slim-bookworm AS base

# Встановлення змінних середовища для Python
ENV PYTHONDONTWRITEBYTECODE 1  # Запобігає створенню .pyc файлів, що не потрібно в контейнерах
ENV PYTHONUNBUFFERED 1         # Забезпечує негайний вивід з Python в консоль (логи)

# Встановлення системних залежностей, якщо вони потрібні (наприклад, для деяких C-розширень Python пакетів)
# Розкоментуйте та додайте необхідні пакети, якщо виникають помилки при встановленні Python залежностей.
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     # gcc libpq-dev \ # Приклад для psycopg2, якщо не використовується psycopg2-binary
#     # netcat-traditional \ # Може використовуватися для очікування запуску БД у entrypoint скрипті
#     && apt-get clean \
#     && rm -rf /var/lib/apt/lists/*

# Створення робочої директорії всередині контейнера
WORKDIR /app

# Створення непривілейованого користувача та групи 'appuser'/'appgroup' для запуску додатку
# Це підвищує безпеку, уникаючи запуску від імені root.
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# --- Образ для збірки залежностей (Builder Stage) ---
# Цей етап використовується для встановлення Python залежностей.
# Результати цього етапу (встановлені пакети) копіюються в продуктивний образ,
# що дозволяє тримати кінцевий образ меншим, не включаючи інструменти збірки.
FROM base AS builder

# Встановлення інструментів для збірки, якщо потрібні для деяких Python пакетів (наприклад, ті, що компілюються з C)
# RUN apt-get update && apt-get install -y --no-install-recommends build-essential libffi-dev python3-dev \
#     && apt-get clean \
#     && rm -rf /var/lib/apt/lists/*

# Копіювання файлу залежностей продуктивного середовища
COPY requirements.txt requirements.txt

# Оновлення pip та встановлення залежностей
# Використовуйте --no-cache-dir для зменшення розміру шару Docker.
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# --- Образ для розробки (Development Stage) ---
# Цей образ призначений для локальної розробки.
# Він включає вихідний код та залежності для розробки (включаючи dev-залежності).
FROM base AS development

# Копіювання файлів залежностей (основних та для розробки)
COPY requirements.txt requirements.txt
COPY requirements-dev.txt requirements-dev.txt # Файл з залежностями для розробки (тести, лінтери тощо)

# Оновлення pip та встановлення всіх залежностей
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements-dev.txt

# Копіювання всього коду додатку в робочу директорію /app
# У docker-compose.dev.yml цей код зазвичай монтується через volume для live-reload,
# але копіювання тут корисне для випадків, коли образ використовується окремо.
COPY . .

# Встановлення прав власності на файли для непривілейованого користувача
RUN chown -R appuser:appgroup /app
# Переключення на непривілейованого користувача
USER appuser

# Команда за замовчуванням для запуску сервера розробки Uvicorn з автоперезавантаженням.
# Може бути перевизначена в docker-compose.dev.yml.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# --- Образ для продуктивного середовища (Production Stage) ---
# Цей образ оптимізований для продуктивного використання: він має менший розмір
# та не містить зайвих інструментів для розробки або збірки.
FROM base AS production

# Копіювання встановлених Python пакетів (site-packages) з етапу 'builder'
# Це дозволяє уникнути включення інструментів збірки та кешу pip в кінцевий образ.
# Шлях /usr/local/lib/pythonX.Y/site-packages/ залежить від версії Python.
COPY --from=builder /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/
# Копіювання виконуваних файлів, встановлених пакетами (наприклад, uvicorn, alembic)
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Копіювання тільки необхідних файлів додатку для продуктивного середовища
# Це допомагає зменшити розмір образу та підвищити безпеку, не включаючи файли розробки.
# Переконайтеся, що .dockerignore налаштований для виключення непотрібних файлів при COPY . .
# Якщо .dockerignore не використовується активно, краще копіювати явно:
COPY ./app /app/app
COPY ./alembic /app/alembic
COPY ./scripts /app/scripts # Якщо використовуються в entrypoint або для інших завдань у продуктиві
COPY alembic.ini /app/alembic.ini
# COPY ./інші_необхідні_файли_або_модулі /app/ # Якщо є інші файли на верхньому рівні, потрібні для виконання

# Встановлення прав власності на файли для непривілейованого користувача
RUN chown -R appuser:appgroup /app
# Переключення на непривілейованого користувача
USER appuser

# Команда для запуску додатку в продуктивному режимі.
# Рекомендується використовувати Gunicorn або інший WSGI/ASGI сервер, оптимізований для продуктиву.
# Приклад з Gunicorn (розкоментуйте та налаштуйте кількість воркерів '-w'):
# CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", "--bind", "0.0.0.0:8000", "-w", "4"]
# Або просто Uvicorn, якщо Gunicorn не використовується:
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Опціонально: ENTRYPOINT для виконання скриптів перед запуском основного процесу CMD.
# Наприклад, для автоматичного застосування міграцій Alembic при старті контейнера.
# COPY ./docker-entrypoint.sh /docker-entrypoint.sh
# RUN chmod +x /docker-entrypoint.sh
# ENTRYPOINT ["/docker-entrypoint.sh"] # Цей скрипт потім повинен викликати CMD (напр. exec "$@")
