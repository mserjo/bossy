# Makefile
# # Цей Makefile надає набір зручних команд для управління проєктом,
# # автоматизації повсякденних завдань розробки та взаємодії
# # з Docker-контейнерами. Команди спрощують такі операції, як запуск
# # та зупинка середовища, збірка образів, виконання тестів,
# # лінтинг коду, управління міграціями бази даних тощо.
# #
# # Для перегляду списку доступних команд та їх опису виконайте: make help

# --- Змінні ---
# Отримання UID та GID поточного користувача для правильного встановлення прав на файли,
# що створюються в контейнерах, особливо для Linux хостів.
# Для macOS та Windows це зазвичай не так критично, але не завадить.
UID := $(shell id -u)
GID := $(shell id -g)

# Базові команди Docker Compose
# Використовуємо docker-compose.yml та docker-compose.dev.yml за замовчуванням для розробки
COMPOSE_FILES := -f docker-compose.yml -f docker-compose.dev.yml
DOCKER_COMPOSE := docker-compose $(COMPOSE_FILES)

# Команда для запуску команд всередині backend сервісу
# Припускаємо, що назва сервісу в dev файлі залишається 'backend'.
# Опція -u $(UID):$(GID) запускає команду від імені поточного користувача хост-системи,
# щоб уникнути проблем з правами доступу до файлів, створених/змінених в контейнері.
BACKEND_EXEC := $(DOCKER_COMPOSE) exec -u $(UID):$(GID) backend
PYTHON_EXEC := $(BACKEND_EXEC) python
# Приклад для manage.py, якщо такий використовується (наприклад, в Django)
MANAGE_PY_EXEC := $(PYTHON_EXEC) ./scripts/manage.py # Припускаючи, що є такий скрипт або аналог в ./backend/scripts/

# Налаштування для Alembic (якщо manage.py не використовується для міграцій)
# Команди Alembic будуть виконуватися в контейнері backend.
ALEMBIC_EXEC := $(BACKEND_EXEC) alembic

# Кольори для виводу в терміналі (опціонально)
GREEN=[0;32m
YELLOW=[0;33m
RESET=[0m

.PHONY: help up down logs build rebuild ps stop clean lint test shell makemigrations migrate superuser seed format prod-up prod-down prod-logs prod-rebuild

# --- Основні команди ---
help: ## Показати цей список команд та їх опис (українською)
	@echo "${GREEN}Доступні команди:${RESET}"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z0-9_-]+:.*?## / {printf "${YELLOW}%-25s${RESET} %s\n", $$1, $$2}' $(MAKEFILE_LIST) | sort

up: ## Запустити сервіси в режимі розробки (detached, з видаленням orphan контейнерів)
	@echo "${GREEN}Запуск Docker Compose сервісів (dev)...${RESET}"
	$(DOCKER_COMPOSE) up -d --remove-orphans
	@echo "${GREEN}Сервіси запущені. Використовуйте 'make logs' для перегляду логів.${RESET}"

down: ## Зупинити та видалити контейнери, мережі (dev, томи зберігаються)
	@echo "${YELLOW}Зупинка Docker Compose сервісів (dev)...${RESET}"
	$(DOCKER_COMPOSE) down --remove-orphans
	@echo "${GREEN}Сервіси зупинені, контейнери та мережі видалені.${RESET}"

logs: ## Показати логи всіх сервісів (dev) або конкретного (напр. make logs service=backend)
	@echo "${GREEN}Перегляд логів... (Ctrl+C для виходу)${RESET}"
	$(DOCKER_COMPOSE) logs -f $(service)

# --- Команди для збірки та очищення ---
build: ## Зібрати або перезібрати образи для dev (без кешу: make build service=backend no_cache=true)
ifeq ($(no_cache),true)
	@echo "${YELLOW}Перезбірка образу для сервісу $(or $(service), 'всіх визначених') без кешу (dev)...${RESET}"
	$(DOCKER_COMPOSE) build --no-cache $(service)
else
	@echo "${GREEN}Збірка/перезбірка образів для сервісу $(or $(service), 'всіх визначених') (dev)...${RESET}"
	$(DOCKER_COMPOSE) build $(service)
endif
	@echo "${GREEN}Збірку завершено.${RESET}"

rebuild: ## Перезібрати всі образи для dev примусово без використання кешу
	@echo "${YELLOW}Примусова перезбірка всіх образів без кешу (dev)...${RESET}"
	$(DOCKER_COMPOSE) build --no-cache
	@echo "${GREEN}Образи перезібрані.${RESET}"

ps: ## Показати статус запущених контейнерів (dev)
	@echo "${GREEN}Статус контейнерів (dev):${RESET}"
	$(DOCKER_COMPOSE) ps

stop: ## Зупинити запущені сервіси без їх видалення (dev)
	@echo "${YELLOW}Зупинка сервісів без видалення контейнерів (dev)...${RESET}"
	$(DOCKER_COMPOSE) stop
	@echo "${GREEN}Сервіси зупинені.${RESET}"

clean: ## Повністю очистити систему dev: зупинити, видалити контейнери, мережі, томи та образи
	@echo "${YELLOW}УВАГА: Ця команда видалить контейнери, мережі, ВСІ томи (включаючи дані БД!) та образи, пов'язані з dev конфігурацією.${RESET}"
	@read -p "Ви впевнені, що хочете продовжити? Введіть 'так' або 'yes': " confirm; \
	if [[ "$$confirm" == "yes" || "$$confirm" == "так" ]]; then \
		echo "${YELLOW}Очищення системи (dev)...${RESET}"; \
		$(DOCKER_COMPOSE) down -v --remove-orphans --rmi all; \
		echo "${GREEN}Система (dev) очищена: контейнери, мережі, томи та образи видалені.${RESET}"; \
	else \
		echo "${GREEN}Очищення скасовано.${RESET}"; \
	fi

# --- Команди для розробки та тестування ---
lint: ## Запустити лінтери (напр. Ruff, MyPy) всередині backend контейнера
	@echo "${GREEN}Запуск лінтерів в контейнері backend...${RESET}"
	# Приклад для ruff (якщо використовується)
	$(BACKEND_EXEC) ruff check .
	# Приклад для mypy (якщо використовується)
	# $(BACKEND_EXEC) mypy .
	# $(PYTHON_EXEC) ./scripts/run_linters.py # Або через спеціальний скрипт, якщо є

test: ## Запустити тести (напр. Pytest) всередині backend контейнера
	@echo "${GREEN}Запуск тестів в контейнері backend...${RESET}"
	$(BACKEND_EXEC) pytest
	# $(PYTHON_EXEC) ./scripts/run_tests.py # Або через спеціальний скрипт, якщо є

shell: ## Відкрити інтерактивну оболонку (bash) всередині backend контейнера
	@echo "${GREEN}Підключення до оболонки (bash) контейнера backend...${RESET}"
	$(DOCKER_COMPOSE) exec backend bash

# --- Команди для бази даних (Alembic) ---
# Переконайтесь, що Alembic налаштований (env.py) для роботи зі змінними середовища з .env файлу.
makemigrations: ## Створити нову міграцію Alembic (напр. make makemigrations msg="add_user_table")
	@echo "${GREEN}Створення нової міграції Alembic...${RESET}"
	@read -p "Введіть опис для міграції (напр. add_user_table): " msg; \
	if [ -z "$$msg" ]; then \
		echo "${YELLOW}Повідомлення не може бути порожнім. Створення міграції скасовано.${RESET}"; \
		exit 1; \
	fi; \
	$(ALEMBIC_EXEC) revision -m "$$msg"

migrate: ## Застосувати міграції Alembic до бази даних (до останньої версії)
	@echo "${GREEN}Застосування міграцій Alembic (upgrade head)...${RESET}"
	$(ALEMBIC_EXEC) upgrade head

# --- Команди для управління додатком (приклади) ---
# Шляхи до скриптів вказані відносно кореневої директорії додатку всередині контейнера (напр. /app/scripts/)
superuser: ## Створити суперкористувача (приклад, потребує ./scripts/create_superuser.py)
	@echo "${GREEN}Створення суперкористувача (через ./scripts/create_superuser.py)...${RESET}"
	$(PYTHON_EXEC) ./scripts/create_superuser.py
	# Або: $(MANAGE_PY_EXEC) createsuperuser # Якщо використовується manage.py

seed: ## Заповнити базу даних початковими даними (приклад, потребує ./scripts/run_seed.py)
	@echo "${GREEN}Заповнення БД початковими даними (через ./scripts/run_seed.py)...${RESET}"
	$(PYTHON_EXEC) ./scripts/run_seed.py
	# Або: $(MANAGE_PY_EXEC) seed # Якщо використовується manage.py

format: ## Форматувати код за допомогою Black та iSort всередині backend контейнера
	@echo "${GREEN}Форматування коду (Black, iSort) в контейнері backend...${RESET}"
	$(BACKEND_EXEC) black .
	$(BACKEND_EXEC) isort .

# --- Команди для продуктивного середовища (приклади) ---
# Ці команди використовують docker-compose.prod.yml. Розкоментуйте та налаштуйте за потреби.
# PROD_COMPOSE_FILES := -f docker-compose.yml -f docker-compose.prod.yml
# PROD_DOCKER_COMPOSE := docker-compose $(PROD_COMPOSE_FILES)

# prod-up: ## Запустити сервіси в режимі продуктиву (detached, з прод конфігурацією)
# 	@echo "${GREEN}Запуск Docker Compose сервісів (prod)...${RESET}"
# 	$(PROD_DOCKER_COMPOSE) up -d --remove-orphans

# prod-down: ## Зупинити та видалити контейнери, мережі, томи (prod)
# 	@echo "${YELLOW}Зупинка Docker Compose сервісів (prod) з видаленням томів...${RESET}"
# 	$(PROD_DOCKER_COMPOSE) down -v --remove-orphans

# prod-logs: ## Показати логи всіх сервісів (prod) або конкретного (напр. make prod-logs service=backend)
# 	@echo "${GREEN}Перегляд логів (prod)... (Ctrl+C для виходу)${RESET}"
# 	$(PROD_DOCKER_COMPOSE) logs -f $(service)

# prod-rebuild: ## Перезібрати всі образи для prod примусово без використання кешу
# 	@echo "${YELLOW}Примусова перезбірка всіх образів без кешу (prod)...${RESET}"
# 	$(PROD_DOCKER_COMPOSE) build --no-cache

.DEFAULT_GOAL := help
