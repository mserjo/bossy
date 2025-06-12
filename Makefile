# Makefile
# # Цей Makefile містить набір корисних команд для управління проектом.
# # Команди призначені для спрощення розробки та взаємодії з Docker-контейнерами.

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
# Використовуємо backend_dev, якщо сервіс у docker-compose.dev.yml названий так,
# або backend, якщо назва сервісу не змінюється.
# Припускаємо, що назва сервісу в dev файлі залишається 'backend'.
BACKEND_EXEC := $(DOCKER_COMPOSE) exec -u $(UID):$(GID) backend
PYTHON_EXEC := $(BACKEND_EXEC) python
MANAGE_PY_EXEC := $(PYTHON_EXEC) ./scripts/manage.py # Припускаючи, що є такий скрипт або аналог

# Налаштування для Alembic (якщо manage.py не використовується для міграцій)
ALEMBIC_EXEC := $(BACKEND_EXEC) alembic

# Кольори для виводу (опціонально)
GREEN=[0;32m
YELLOW=[0;33m
RESET=[0m

.PHONY: help up down logs build rebuild ps stop clean lint test shell makemigrations migrate superuser seed format

# --- Основні команди ---
help: ## Показати цей список команд та їх опис
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\n${YELLOW}%-20s${RESET} %s\n", $$1, $$2}' $(MAKEFILE_LIST) | sort

up: ## Запустити сервіси в режимі розробки (detached)
	@echo "${GREEN}Запуск Docker Compose сервісів (dev)...${RESET}"
	$(DOCKER_COMPOSE) up -d --remove-orphans
	@echo "${GREEN}Сервіси запущені. Використовуйте 'make logs' для перегляду логів.${RESET}"

down: ## Зупинити та видалити сервіси, визначені в dev (зберігає томи)
	@echo "${YELLOW}Зупинка Docker Compose сервісів (dev)...${RESET}"
	$(DOCKER_COMPOSE) down
	@echo "${GREEN}Сервіси зупинені.${RESET}"

logs: ## Показати логи всіх сервісів (dev) або конкретного сервісу (make logs service=backend)
	@echo "${GREEN}Перегляд логів... (Ctrl+C для виходу)${RESET}"
	$(DOCKER_COMPOSE) logs -f $(service)

# --- Команди для збірки та очищення ---
build: ## Зібрати або перезібрати образи для dev (без кешу для конкретного сервісу: make build service=backend no_cache=true)
ifeq ($(no_cache),true)
	@echo "${YELLOW}Перезбірка образу для сервісу $(service) без кешу...${RESET}"
	$(DOCKER_COMPOSE) build --no-cache $(service)
else
	@echo "${GREEN}Збірка образів для сервісу $(service)...${RESET}"
	$(DOCKER_COMPOSE) build $(service)
endif

rebuild: ## Перезібрати всі образи для dev без використання кешу
	@echo "${YELLOW}Перезбірка всіх образів без кешу (dev)...${RESET}"
	$(DOCKER_COMPOSE) build --no-cache
	@echo "${GREEN}Образи перезібрані.${RESET}"

ps: ## Показати статус запущених контейнерів (dev)
	@echo "${GREEN}Статус контейнерів (dev):${RESET}"
	$(DOCKER_COMPOSE) ps

stop: ## Зупинити сервіси без їх видалення (dev)
	@echo "${YELLOW}Зупинка сервісів (dev)...${RESET}"
	$(DOCKER_COMPOSE) stop
	@echo "${GREEN}Сервіси зупинені.${RESET}"

clean: ## Зупинити та видалити контейнери, мережі, томи та образи, визначені в dev
	@echo "${YELLOW}УВАГА: Ця команда видалить контейнери, мережі та ВСІ томи (включаючи дані БД!).${RESET}"
	@read -p "Ви впевнені, що хочете продовжити? [y/N]: " confirm && [[ $$confirm == [yY] || $$confirm == [уУ] ]] || exit 1
	$(DOCKER_COMPOSE) down -v --remove-orphans
	@echo "${GREEN}Система очищена (dev).${RESET}"

# --- Команди для розробки та тестування ---
lint: ## Запустити лінтери (flake8, mypy, ruff тощо) всередині backend контейнера
	@echo "${GREEN}Запуск лінтерів...${RESET}"
	# Приклад для ruff (якщо використовується)
	$(BACKEND_EXEC) ruff check .
	# Приклад для mypy (якщо використовується)
	# $(BACKEND_EXEC) mypy .
	# $(PYTHON_EXEC) ./scripts/run_linters.py # Або через спеціальний скрипт

test: ## Запустити тести всередині backend контейнера
	@echo "${GREEN}Запуск тестів...${RESET}"
	$(BACKEND_EXEC) pytest
	# $(PYTHON_EXEC) ./scripts/run_tests.py # Або через спеціальний скрипт

shell: ## Відкрити інтерактивну оболонку (bash) всередині backend контейнера
	@echo "${GREEN}Підключення до оболонки backend контейнера...${RESET}"
	$(DOCKER_COMPOSE) exec backend bash

# --- Команди для бази даних (Alembic) ---
# Переконайтесь, що Alembic налаштований для роботи з env.py та змінними середовища
makemigrations: ## Створити нову міграцію Alembic (наприклад, make makemigrations message="add_user_table")
	@echo "${GREEN}Створення нової міграції Alembic...${RESET}"
	@read -p "Введіть повідомлення для міграції: " msg; 	$(ALEMBIC_EXEC) revision -m "$$msg"

migrate: ## Застосувати міграції Alembic до бази даних
	@echo "${GREEN}Застосування міграцій Alembic...${RESET}"
	$(ALEMBIC_EXEC) upgrade head

# --- Команди для управління додатком ---
superuser: ## Створити суперкористувача (якщо є відповідний скрипт)
	@echo "${GREEN}Створення суперкористувача...${RESET}"
	$(PYTHON_EXEC) ./scripts/create_superuser.py
	# Або: $(MANAGE_PY_EXEC) createsuperuser

seed: ## Заповнити базу даних початковими даними (якщо є відповідний скрипт)
	@echo "${GREEN}Заповнення бази даних початковими даними...${RESET}"
	$(PYTHON_EXEC) ./scripts/run_seed.py
	# Або: $(MANAGE_PY_EXEC) seed

format: ## Форматувати код за допомогою black, isort (якщо використовуються)
	@echo "${GREEN}Форматування коду...${RESET}"
	$(BACKEND_EXEC) black .
	$(BACKEND_EXEC) isort .

# --- Команди для продуктивного середовища ---
# Ці команди використовують docker-compose.prod.yml
# PROD_COMPOSE_FILES := -f docker-compose.yml -f docker-compose.prod.yml
# PROD_DOCKER_COMPOSE := docker-compose $(PROD_COMPOSE_FILES)

# prod-up: ## Запустити сервіси в режимі продуктиву (detached)
# 	@echo "${GREEN}Запуск Docker Compose сервісів (prod)...${RESET}"
# 	$(PROD_DOCKER_COMPOSE) up -d --remove-orphans

# prod-down: ## Зупинити та видалити сервіси, визначені в prod
# 	@echo "${YELLOW}Зупинка Docker Compose сервісів (prod)...${RESET}"
# 	$(PROD_DOCKER_COMPOSE) down -v

# prod-logs: ## Показати логи всіх сервісів (prod) або конкретного (make prod-logs service=backend)
# 	@echo "${GREEN}Перегляд логів (prod)... (Ctrl+C для виходу)${RESET}"
# 	$(PROD_DOCKER_COMPOSE) logs -f $(service)

# prod-rebuild: ## Перезібрати всі образи для prod без використання кешу
# 	@echo "${YELLOW}Перезбірка всіх образів без кешу (prod)...${RESET}"
# 	$(PROD_DOCKER_COMPOSE) build --no-cache

.DEFAULT_GOAL := help
