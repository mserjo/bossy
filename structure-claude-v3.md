# structure-claude-v3.md
# Bossy 
# Детальна структура проекту
bossy/                                 # Кореневий каталог проекту
├── README.md                          # Основна документація проекту: опис, інструкції по запуску, посилання
├── LICENSE                            # Текст ліцензії, під якою розповсюджується проект
├── .gitignore                         # Список файлів та папок, які Git повинен ігнорувати (логи, віртуальні середовища, тощо)
├── .env                               # Змінні оточення (ключі, паролі, налаштування)
├── .env.example                       # Приклад файлу змінних середовища з необхідними ключами для конфігурації проекту
├── docker-compose.yml                 # Основний файл конфігурації Docker Compose для запуску всіх сервісів проекту (база даних, backend, frontend, Redis)
├── docker-compose.dev.yml             # Додаткова конфігурація Docker Compose для середовища розробки (наприклад, з hot-reload, debug tools)
├── docker-compose.prod.yml            # Додаткова конфігурація Docker Compose для продакшн середовища (оптимізовані налаштування)
├── Makefile                           # Файл для автоматизації часто використовуваних команд розробки (запуск, тести, міграції, лінтинг)
├── requirements.txt                   # Список Python залежностей для скриптів, що можуть знаходитись на кореневому рівні проекту (якщо є)
│
├── docs/                             # Каталог з усією документацією проекту
│   ├── README.md                     # Головна сторінка документації, індекс та навігація по розділах
│   ├── api/                          # Каталог для API документації
│   │   ├── openapi.json              # Специфікація API у форматі OpenAPI 3.x (генерується автоматично FastAPI)
│   │   ├── postman/                  # Колекції та середовища Postman для тестування API
│   │   │   ├── bossy_api.postman_collection.json           # JSON файл з колекцією запитів Postman для всіх ендпоінтів API
│   │   │   ├── bossy_environments.postman_environment.json # JSON файл з налаштуваннями середовищ Postman (dev, staging, prod)
│   │   │   └── README.md                                   # Інструкції по імпорту та використанню колекцій Postman
│   │   └── swagger/                  # Документація для Swagger UI (зазвичай вбудована в FastAPI на /docs або /redoc)
│   │       └── swagger.json          # Swagger специфікація API
│   │
│   ├── architecture/                 # Каталог з архітектурною документацією
│   │   ├── system_overview.md        # Загальний опис архітектури системи, її компонентів та взаємодій
│   │   ├── database_design.md        # Опис схеми бази даних, таблиць, зв'язків, індексів та обґрунтування вибору
│   │   ├── api_design.md             # Принципи та конвенції дизайну API, версіонування, формати запитів/відповідей
│   │   ├── security.md               # Опис аспектів безпеки системи: аутентифікація, авторизація, захист даних
│   │   └── diagrams/                 # Каталог з візуальними діаграмами архітектури
│   │       ├── component_diagram.puml  # Компонентна діаграма системи у форматі PlantUML, що показує основні компоненти та їх зв'язки
│   │       ├── database_erd.puml       # ER (Entity-Relationship) діаграма бази даних у форматі PlantUML
│   │       ├── business_process.bpmn   # Діаграми бізнес-процесів у форматі BPMN, що описують ключові сценарії користувачів
│   │       ├── deployment_diagram.puml # Діаграма розгортання системи у форматі PlantUML, що показує розміщення компонентів на серверах
│   │       └── technology_stack_diagram.puml # Діаграма, що візуалізує стек технологій, які використовуються в проекті (PlantUML)
│   │
│   ├── deployment/                   # Каталог з документацією по розгортанню проекту
│   │   ├── docker.md                 # Детальні інструкції по роботі з Docker та Docker Compose для проекту
│   │   ├── kubernetes.md             # Інструкції та конфігураційні файли для розгортання в Kubernetes (якщо планується)
│   │   └── production.md             # Рекомендації та кроки для розгортання проекту в продакшн середовищі
│   │
│   └── user_guide/                   # Каталог з посібниками для користувачів системи
│       ├── admin_guide.md            # Керівництво для супер-адміністратора системи (налаштування, моніторинг)
│       ├── group_admin_guide.md      # Керівництво для адміністратора групи (керування групою, користувачами, завданнями)
│       ├── user_guide.md             # Керівництво для звичайного користувача системи (виконання завдань, перегляд бонусів)
│       └── api_guide.md              # Керівництво по використанню API для розробників зовнішніх систем
│
├── .pre-commit-config.yaml           # Налаштування pre-commit хуків
├── .github/                          # GitHub Actions для CI/CD
│   └── workflows/                    # Папка з workflow файлами
│       ├── ci.yml                    # Continuous Integration pipeline
│       ├── cd.yml                    # Continuous Deployment pipeline
│       └── tests.yml                 # Автоматичне тестування
│
├── backend/                         # Каталог з кодом backend частини проекту (Python, FastAPI)
│   ├── Dockerfile                   # Інструкції для Docker по збірці образу backend для проду
│   ├── Dockerfile.dev               # Інструкції для Docker по збірці образу backend для розробки
│   ├── requirements.txt             # Список основних Python залежностей для backend (FastAPI, Pydantic, SQLAlchemy, etc.)
│   ├── requirements-dev.txt         # Список Python залежностей для розробки backend (pytest, black, ruff, etc.)
│   ├── pytest.ini                   # Конфігураційний файл для тестового фреймворку pytest
│   ├── pyproject.toml               # Конфігураційний файл для Python проекту (PEP 518), використовується для налаштувань інструментів (Black, Ruff, Mypy)
│   ├── alembic.ini                  # Конфігураційний файл для Alembic - інструменту міграцій бази даних
│   ├── .env.example                 # Приклад файлу змінних середовища для backend (DB_URL, JWT_SECRET, etc.)
│   │
│   ├── alembic/             # Каталог для міграцій бази даних (Alembic)
│   │   ├── __init__.py      # Ініціалізаційний файл пакету `alembic`
│   │   ├── env.py           # Конфігураційний скрипт Alembic, який виконується при запуску міграцій
│   │   ├── script.py.mako   # Шаблон для генерації нових файлів міграцій Alembic
│   │   └── versions/        # Каталог, де зберігаються згенеровані Alembic файли версій міграцій
│   │       ├── __init__.py  # Ініціалізаційний файл пакету `versions`
│   │       └── README.md    # Інструкції та рекомендації по роботі з міграціями Alembic
│   │       # Тут будуть файли типу: xxxxxxxxxx_create_users_table.py, yyyyyyyyyy_add_indexes_to_tasks.py ...
│   │
│   ├── app/                         # Основний каталог з кодом FastAPI додатку
│   │   ├── __init__.py              # Ініціалізаційний файл пакету `app`, дозволяє Python розглядати каталог як пакет
│   │   ├── main.py                  # Головний файл запуску FastAPI додатку: створення екземпляру FastAPI, підключення роутерів, middleware, обробників подій
│   │   │
│   │   └── src/                     # Каталог з основним вихідним кодом backend логіки
│   │       ├── __init__.py          # Ініціалізаційний файл пакету `src`
│   │       │
│   │       ├── config/              # Каталог з конфігураційними файлами додатку
│   │       │   ├── __init__.py      # Ініціалізаційний файл пакету `config`
│   │       │   ├── settings.py      # Модуль для завантаження та валідації налаштувань додатку за допомогою Pydantic Settings (змінні середовища, константи)
│   │       │   ├── database.py      # Модуль для конфігурації підключення до бази даних PostgreSQL (SQLAlchemy engine, session factory)
│   │       │   ├── redis.py         # Модуль для конфігурації підключення до Redis для черг та кешування (опціонально)
│   │       │   ├── celery.py        # Модуль для конфігурації підключення до Celery (опціонально)
│   │       │   ├── firebase.py      # Модуль для конфігурації підключення до Firebase (опціонально)
│   │       │   ├── elasticsearch.py # Модуль для конфігурації підключення до Elasticsearch (опціонально)
│   │       │   ├── logging.py       # Модуль для налаштування системи логування backend (рівні, формати, файли логів)
│   │       │   └── security.py      # Модуль для налаштувань безпеки: параметри JWT, хешування паролів, CORS політики
│   │       │
│   │       ├── core/                # Каталог з основними, загальними компонентами системи
│   │       │   ├── __init__.py      # Ініціалізаційний файл пакету `core`
│   │       │   ├── base.py          # Модуль з базовими класами для сервісів, репозиторіїв, якщо потрібні спільні методи або логіка
│   │       │   ├── exceptions.py    # Модуль для визначення кастомних класів винятків (HTTP винятки, помилки бізнес-логіки)
│   │       │   ├── constants.py     # Модуль для визначення глобальних констант системи (наприклад, дефолтні значення, ключі)
│   │       │   ├── dicts.py         # Модуль для системних довідників, які не зберігаються в БД (наприклад, Enum для внутрішніх станів)
│   │       │   ├── decorators.py    # Модуль для кастомних декораторів, які використовуються в системі.
│   │       │   ├── events.py        # Модуль для визначення та обробки системних подій (якщо використовується event-driven підхід)
│   │       │   ├── permissions.py   # Модуль для реалізації системи дозволів та перевірки прав доступу (FastAPI dependencies)
│   │       │   ├── dependencies.py  # Модуль для визначення FastAPI залежностей (наприклад, `get_db_session`, `get_current_user`)
│   │       │   ├── middleware.py    # Модуль для визначення кастомних FastAPI middleware (наприклад, логування запитів, обробка сесій)
│   │       │   ├── validators.py    # Модуль для кастомних функцій-валідаторів даних (використовуються в Pydantic схемах або сервісах)
│   │       │   ├── utils.py         # Модуль з різноманітними утилітарними функціями (робота з датами, рядками, тощо)
│   │       │   └── i18n.py          # Модуль для налаштування інтернаціоналізації та локалізації (наприклад, з FastAPI-babel)
│   │       │
│   │       ├── models/              # Каталог для визначення SQLAlchemy моделей бази даних
│   │       │   ├── __init__.py      # Ініціалізаційний файл пакету `models`, може експортувати всі моделі для зручного імпорту
│   │       │   ├── base.py          # Модуль з базовим класом `BaseModel` (SQLAlchemy DeclarativeBase, спільні поля як id, created_at, updated_at) та `BaseMainModel` (успадковує BaseModel, додає name, description, state, group_id, deleted_at, notes)
│   │       │   ├── mixins.py        # Модуль з SQLAlchemy міксинами для додавання спільної функціональності (...)
│   │       │   │
│   │       │   ├── system/            # Каталог для системних моделей
│   │       │   │   ├── __init__.py    # Ініціалізаційний файл пакету `system.models`
│   │       │   │   ├── settings.py    # SQLAlchemy модель для зберігання налаштувань системи (...)
│   │       │   │   ├── cron.py        # SQLAlchemy модель для системних задач (cron) (...)
│   │       │   │   ├── monitoring.py  # SQLAlchemy моделі для збору даних моніторингу (...)
│   │       │   │   └── health.py      # SQLAlchemy моделі для health check (...)
│   │       │   │
│   │       │   ├── dictionaries/      # Каталог для моделей довідників (кожен успадковує `BaseDictModel`)
│   │       │   │   ├── __init__.py    # Ініціалізаційний файл пакету `dictionaries.models`
│   │       │   │   ├── base.py        # Базовий клас `BaseDictModel` для моделей довідників (успадковує `BaseMainModel`, додає `code`)
│   │       │   │   ├── status.py      # SQLAlchemy модель для довідника "Статуси" (...)
│   │       │   │   ├── user_role.py   # SQLAlchemy модель для довідника "Ролі користувачів" (...)
│   │       │   │   ├── group_type.py  # SQLAlchemy модель для довідника "Типи груп" (...)
│   │       │   │   ├── task_type.py   # SQLAlchemy модель для довідника "Типи завдань" (...)
│   │       │   │   ├── bonus_type.py  # SQLAlchemy модель для довідника "Типи бонусів" (...)
│   │       │   │   └── integration.py # SQLAlchemy модель для довідника "Типи зовнішніх інтеграцій" (...)
│   │       │   │
│   │       │   ├── auth/            # Каталог для моделей, пов'язаних з аутентифікацією та користувачами
│   │       │   │   ├── __init__.py  # Ініціалізаційний файл пакету `auth.models`
│   │       │   │   ├── user.py      # SQLAlchemy модель "Користувач", успадковує `BaseMainModel` (...)
│   │       │   │   ├── token.py     # SQLAlchemy модель для зберігання Refresh токенів (...)
│   │       │   │   └── session.py   # SQLAlchemy модель для сесій користувачів (...)
│   │       │   │
│   │       │   ├── groups/            # Каталог для моделей, пов'язаних з групами
│   │       │   │   ├── __init__.py    # Ініціалізаційний файл пакету `groups.models`
│   │       │   │   ├── group.py       # SQLAlchemy модель "Група", успадковує `BaseMainModel` (...)
│   │       │   │   ├── settings.py    # SQLAlchemy модель для налаштувань конкретної групи (...)
│   │       │   │   ├── membership.py  # SQLAlchemy модель "Членство в групі", зв'язок user-group з роллю (...)
│   │       │   │   ├── invitation.py  # SQLAlchemy модель "Запрошення до групи" (...)
│   │       │   │   ├── template.py    # SQLAlchemy модель "Шаблон групи" (...)
│   │       │   │   ├── poll.py        # SQLAlchemy модель "Опитування/Голосування" (...)
│   │       │   │   ├── poll_option.py # SQLAlchemy модель "Варіант відповіді в опитуванні" (...)
│   │       │   │   └── poll_vote.py   # SQLAlchemy модель "Голос в опитуванні" (...)
│   │       │   │
│   │       │   ├── tasks/           # Каталог для моделей, пов'язаних із завданнями та подіями
│   │       │   │   ├── __init__.py  # Ініціалізаційний файл пакету `tasks.models`
│   │       │   │   ├── task.py      # SQLAlchemy модель "Завдання/Подія", успадковує `BaseMainModel` (з полем task_type) (...)
│   │       │   │   ├── assignment.py# SQLAlchemy модель "Призначення завдання/події" (...)
│   │       │   │   ├── completion.py# SQLAlchemy модель "Виконання завдання/події" (...)
│   │       │   │   ├── dependency.py# SQLAlchemy модель "Зв'язки між завданнями (для підзадач)" (...)
│   │       │   │   ├── proposal.py  # SQLAlchemy модель "Пропозиція завдання/події" (...)
│   │       │   │   └── review.py    # SQLAlchemy модель "Відгук на завдання" (...)
│   │       │   │
│   │       │   ├── teams/           # Каталог для моделей, пов'язаних із командами для командних завдань
│   │       │   │   ├── __init__.py  # Ініціалізаційний файл пакету `teams.models`
│   │       │   │   ├── team.py      # SQLAlchemy модель "Команда" (...)
│   │       │   │   └── membership.py# SQLAlchemy модель "Членство в команді" (...)
│   │       │   │
│   │       │   ├── bonuses/         # Каталог для моделей, пов'язаних з бонусами та рахунками
│   │       │   │   ├── __init__.py  # Ініціалізаційний файл пакету `bonuses.models`
│   │       │   │   ├── bonus.py     # SQLAlchemy модель "Бонус", опис правила нарахування/штрафу для завдання/події (...)
│   │       │   │   ├── account.py   # SQLAlchemy модель "Рахунок користувача" (...)
│   │       │   │   ├── transaction.py# SQLAlchemy модель "Транзакція по рахунку" (...)
│   │       │   │   └── reward.py    # SQLAlchemy модель "Нагорода", успадковує `BaseMainModel` (...)
│   │       │   │
│   │       │   ├── gamification/    # Каталог для моделей, пов'язаних з геймифікацією
│   │       │   │   ├── __init__.py  # Ініціалізаційний файл пакету `gamification.models`
│   │       │   │   ├── level.py     # SQLAlchemy модель "Рівень", як довідник або налаштування (...)
│   │       │   │   ├── user_level.py# SQLAlchemy модель "Рівень користувача", зв'язок користувача з рівнем (...)
│   │       │   │   ├── badge.py     # SQLAlchemy модель "Бейдж" (...), успадковує `BaseMainModel`
│   │       │   │   ├── achievement.py# SQLAlchemy модель "Досягнення користувача", зв'язок user-badge (...)
│   │       │   │   └── rating.py    # SQLAlchemy модель "Рейтинг користувача" (...)
│   │       │   │
│   │       │   ├── reports/         # Каталог для моделей, пов'язаних зі звітами
│   │       │   │   ├── __init__.py  # Ініціалізаційний файл пакету `reports.models`
│   │       │   │   └── report.py    # SQLAlchemy модель "Звіт", Параметри генерації (...)
│   │       │   │
│   │       │   ├── notifications/   # Каталог для моделей, пов'язаних зі сповіщеннями
│   │       │   │   ├── __init__.py  # Ініціалізаційний файл пакету `notifications.models`
│   │       │   │   ├── notification.py# SQLAlchemy модель "Сповіщення" (...)
│   │       │   │   ├── template.py  # SQLAlchemy модель "Шаблон сповіщення" (...)
│   │       │   │   └── delivery.py  # SQLAlchemy модель "Статус доставки сповіщення" (...)
│   │       │   │
│   │       │   └── files/           # Каталог для моделей, пов'язаних з файлами
│   │       │       ├── __init__.py  # Ініціалізаційний файл пакету `files.models`
│   │       │       ├── file.py      # SQLAlchemy модель "Файл" (...), метадані файлу
│   │       │       └── avatar.py    # SQLAlchemy модель "Аватар користувача", зв'язок User-FileRecord (...)
│   │       │
│   │       ├── schemas/             # Каталог для Pydantic схем (валідація даних API запитів/відповідей)
│   │       │   ├── __init__.py      # Ініціалізаційний файл пакету `schemas`, може експортувати всі схеми
│   │       │   ├── base.py          # Модуль з базовими Pydantic схемами (...)
│   │       │   │
│   │       │   ├── system/          # Pydantic схеми для системних сутностей
│   │       │   │   ├── __init__.py  # Ініціалізація пакету `system.schemas`
│   │       │   │   ├── settings.py  # Pydantic схеми для SystemSetting (...)
│   │       │   │   ├── cron_task.py # Pydantic схеми для CronTask (...)
│   │       │   │   ├── monitoring.py# Pydantic схеми для (...)
│   │       │   │   └── health.py    # Pydantic схеми для (...)
│   │       │   │
│   │       │   ├── auth/            # Pydantic схеми для аутентифікації та користувачів
│   │       │   │   ├── __init__.py  # Ініціалізація пакету `auth.schemas`
│   │       │   │   ├── user.py      # Pydantic схеми для User (...)
│   │       │   │   ├── token.py     # Pydantic схеми для Token (...)
│   │       │   │   └── login.py     # Pydantic схеми для Login (...)
│   │       │   │
│   │       │   ├── dictionaries/           # Pydantic схеми для довідників
│   │       │   │   ├── __init__.py         # Ініціалізація пакету `dictionaries.schemas`
│   │       │   │   ├── base_dict.py        # Базові Pydantic схеми для довідників (...)
│   │       │   │   ├── status.py           # Pydantic схеми для Status (...)
│   │       │   │   ├── user_role.py        # Pydantic схеми для UserRole (...)
│   │       │   │   ├── group_type.py       # Pydantic схеми для GroupType (...)
│   │       │   │   ├── task_type.py        # Pydantic схеми для TaskType (...)
│   │       │   │   ├── bonus_type.py       # Pydantic схеми для BonusType (...)
│   │       │   │   └── integration_type.py # Pydantic схеми для IntegrationType (...)
│   │       │   │
│   │       │   ├── groups/           # Pydantic схеми для груп
│   │       │   │   ├── __init__.py   # Ініціалізація пакету `groups.schemas`
│   │       │   │   ├── group.py      # Pydantic схеми для Group (...)
│   │       │   │   ├── settings.py   # Pydantic схеми для GroupSetting (...)
│   │       │   │   ├── membership.py # Pydantic схеми для GroupMembership (...)
│   │       │   │   ├── invitation.py # Pydantic схеми для GroupInvitation (...)
│   │       │   │   ├── template.py   # Pydantic схеми для GroupTemplate (...)
│   │       │   │   └── poll.py       # Pydantic схеми для Poll, PollOption, PollVote (...)
│   │       │   │
│   │       │   ├── tasks/           # Pydantic схеми для завдань
│   │       │   │   ├── __init__.py  # Ініціалізація пакету `tasks.schemas`
│   │       │   │   ├── task.py      # Pydantic схеми для Task (...)
│   │       │   │   ├── assignment.py# Pydantic схеми для TaskAssignment (...)
│   │       │   │   ├── completion.py# Pydantic схеми для TaskCompletion (...)
│   │       │   │   ├── proposal.py  # Pydantic схеми для TaskProposal (...)
│   │       │   │   └── review.py    # Pydantic схеми для TaskReview (...)
│   │       │   │
│   │       │   ├── teams/           # Pydantic схеми для команд
│   │       │   │   ├── __init__.py  # Ініціалізація пакету `teams.schemas`
│   │       │   │   ├── team.py      # Pydantic схеми для Team (...)
│   │       │   │   └── membership.py# Pydantic схеми для TeamMembership (...)
│   │       │   │
│   │       │   ├── bonuses/         # Pydantic схеми для бонусів
│   │       │   │   ├── __init__.py  # Ініціалізація пакету `bonuses.schemas`
│   │       │   │   ├── bonus_rule.py# Pydantic схеми для BonusRule (...)
│   │       │   │   ├── account.py   # Pydantic схеми для UserAccount (...)
│   │       │   │   ├── transaction.py# Pydantic схеми для AccountTransaction (...)
│   │       │   │   └── reward.py    # Pydantic схеми для Reward (...)
│   │       │   │
│   │       │   ├── gamification/    # Pydantic схеми для геймифікації
│   │       │   │   ├── __init__.py  # Ініціалізація пакету `gamification.schemas`
│   │       │   │   ├── level.py     # Pydantic схеми для Level (...)
│   │       │   │   ├── user_level.py# Pydantic схеми для UserLevel (...)
│   │       │   │   ├── badge.py     # Pydantic схеми для Badge (...)
│   │       │   │   ├── achievement.py# Pydantic схеми для UserAchievement (...)
│   │       │   │   └── rating.py    # Pydantic схеми для UserGroupRating (...)
│   │       │   │
│   │       │   ├── reports/         # Pydantic схеми для звітів
│   │       │   │   ├── __init__.py  # Ініціалізація пакету `reports.schemas`
│   │       │   │   ├── request.py   # Схеми для запиту параметрів звіту (...)
│   │       │   │   └── response.py  # Схеми для відповіді з даними звіту (...)
│   │       │   │
│   │       │   ├── notifications/   # Pydantic схеми для сповіщень
│   │       │   │   ├── __init__.py  # Ініціалізація пакету `notifications.schemas`
│   │       │   │   ├── notification.py# Pydantic схеми для Notification (...)
│   │       │   │   ├── template.py  # Pydantic схеми для NotificationTemplate (...)
│   │       │   │   └── delivery.py  # Pydantic схеми для NotificationDeliveryAttempt (...)
│   │       │   │
│   │       │   └── files/           # Pydantic схеми для файлів
│   │       │       ├── __init__.py  # Ініціалізація пакету `files.schemas`
│   │       │       ├── file.py      # Pydantic схеми для FileRecord (...)
│   │       │       └── avatar.py    # Pydantic схеми для UserAvatar (...)
│   │       │
│   │       ├── repositories/        # Каталог для репозиторіїв - шару абстракції для доступу до даних
│   │       │   ├── __init__.py      # Ініціалізаційний файл пакету `repositories`, може експортувати всі репозиторії
│   │       │   ├── base.py          # Модуль з базовим класом репозиторію `BaseRepository` (CRUD операції)
│   │       │   │
│   │       │   ├── system/          # Репозиторії для системних сутностей
│   │       │   │   ├── __init__.py  # Ініціалізація пакету `system.repositories`
│   │       │   │   ├── settings.py  # Репозиторій для SystemSetting (...)
│   │       │   │   ├── cron_task.py # Репозиторій для CronTask (...)
│   │       │   │   ├── monitoring.py# Репозиторій для SystemLog (...)
│   │       │   │   └── health.py    # Репозиторій для ServiceHealthStatus (...)
│   │       │   │
│   │       │   ├── auth/            # Репозиторії для аутентифікації та користувачів
│   │       │   │   ├── __init__.py  # Ініціалізація пакету `auth.repositories`
│   │       │   │   ├── user.py      # Репозиторій для User (...)
│   │       │   │   ├── token.py     # Репозиторій для RefreshToken (...)
│   │       │   │   └── session.py   # Репозиторій для UserSession (...)
│   │       │   │
│   │       │   ├── dictionaries/           # Репозиторії для довідників
│   │       │   │   ├── __init__.py         # Ініціалізація пакету `dictionaries.repositories`
│   │       │   │   ├── base_dict.py        # Базовий репозиторій для довідників (...)
│   │       │   │   ├── status.py           # Репозиторій для Status (...)
│   │       │   │   ├── user_role.py        # Репозиторій для UserRole (...)
│   │       │   │   ├── group_type.py       # Репозиторій для GroupType (...)
│   │       │   │   ├── task_type.py        # Репозиторій для TaskType (...)
│   │       │   │   ├── bonus_type.py       # Репозиторій для BonusType (...)
│   │       │   │   └── integration_type.py # Репозиторій для MessengerPlatform (...)
│   │       │   │
│   │       │   ├── groups/          # Репозиторії для груп
│   │       │   │   ├── __init__.py  # Ініціалізація пакету `groups.repositories`
│   │       │   │   ├── group.py     # Репозиторій для Group (...)
│   │       │   │   ├── settings.py  # Репозиторій для GroupSetting (...)
│   │       │   │   ├── membership.py# Репозиторій для GroupMembership (...)
│   │       │   │   ├── invitation.py# Репозиторій для GroupInvitation (...)
│   │       │   │   ├── template.py  # Репозиторій для GroupTemplate (...)
│   │       │   │   └── poll.py      # Репозиторій для GroupPool (...)
│   │       │   │
│   │       │   ├── tasks/           # Репозиторії для завдань
│   │       │   │   ├── __init__.py  # Ініціалізація пакету `tasks.repositories`
│   │       │   │   ├── task.py      # Репозиторій для Task (...)
│   │       │   │   ├── assignment.py# Репозиторій для TaskAssignment (...)
│   │       │   │   ├── completion.py# Репозиторій для TaskCompletion (...)
│   │       │   │   ├── proposal.py  # Репозиторій для TaskProposal (...)
│   │       │   │   └── review.py    # Репозиторій для TaskReview (...)
│   │       │   │
│   │       │   ├── teams/           # Репозиторії для команд
│   │       │   │   ├── __init__.py  # Ініціалізація пакету `teams.repositories`
│   │       │   │   ├── team.py      # Репозиторій для Team (...)
│   │       │   │   └── membership.py# Репозиторій для TeamMembership (...)
│   │       │   │
│   │       │   ├── bonuses/         # Репозиторії для бонусів
│   │       │   │   ├── __init__.py  # Ініціалізація пакету `bonuses.repositories`
│   │       │   │   ├── bonus_rule.py# Репозиторій для BonusRule (...)
│   │       │   │   ├── account.py   # Репозиторій для UserAccount (...)
│   │       │   │   ├── transaction.py# Репозиторій для AccountTransaction (...)
│   │       │   │   └── reward.py    # Репозиторій для Reward (...)
│   │       │   │
│   │       │   ├── gamification/    # Репозиторії для геймифікації
│   │       │   │   ├── __init__.py  # Ініціалізація пакету `gamification.repositories`
│   │       │   │   ├── level.py     # Репозиторій для Level (...)
│   │       │   │   ├── user_level.py# Репозиторій для UserLevel (...)
│   │       │   │   ├── badge.py     # Репозиторій для Badge (...)
│   │       │   │   ├── achievement.py# Репозиторій для UserAchievement (...)
│   │       │   │   └── rating.py    # Репозиторій для UserGroupRating (...)
│   │       │   │
│   │       │   ├── reports/         # Репозиторії для звітів
│   │       │   │   ├── __init__.py  # Ініціалізація пакету `reports.repositories`
│   │       │   │   └── report.py    # Репозиторій для отримання даних для звітів (може не бути прямої моделі) (...)
│   │       │   │
│   │       │   ├── notifications/   # Репозиторії для сповіщень
│   │       │   │   ├── __init__.py  # Ініціалізація пакету `notifications.repositories`
│   │       │   │   ├── notification.py# Репозиторій для Notification (...)
│   │       │   │   ├── template.py  # Репозиторій для NotificationTemplate (...)
│   │       │   │   └── delivery.py  # Репозиторій для NotificationDeliveryAttempt (...)
│   │       │   │
│   │       │   └── files/           # Репозиторії для файлів
│   │       │       ├── __init__.py  # Ініціалізація пакету `files.repositories`
│   │       │       ├── file.py      # Репозиторій для FileRecord (...)
│   │       │       └── avatar.py    # Репозиторій для UserAvatar (...)
│   │       │
│   │       ├── services/            # Каталог для сервісів - шару бізнес-логіки
│   │       │   ├── __init__.py      # Ініціалізаційний файл пакету `services`, може експортувати всі сервіси
│   │       │   ├── base.py          # Модуль з базовим класом сервісу `BaseService` (якщо є спільна логіка)
│   │       │   │
│   │       │   ├── system/          # Системні сервіси
│   │       │   │   ├── __init__.py  # Ініціалізація пакету `system.services`
│   │       │   │   ├── settings.py  # Сервіс для управління налаштуваннями системи (...)
│   │       │   │   ├── cron_task.py # Сервіс для системних задач (cron) (...)
│   │       │   │   ├── monitoring.py# Сервіс для логіки моніторингу системи (...)
│   │       │   │   ├── health.py    # Сервіс для перевірки стану системи (...)
│   │       │   │   └── initialization.py# Сервіс для ініціалізації початкових даних (...)
│   │       │   │
│   │       │   ├── auth/            # Сервіси, пов'язані з аутентифікацією та користувачами
│   │       │   │   ├── __init__.py  # Ініціалізація пакету `auth.services`
│   │       │   │   ├── user.py      # Сервіс для управління користувачами (...)
│   │       │   │   ├── token.py     # Сервіс для генерації та валідації токенів (...)
│   │       │   │   ├── password.py  # Сервіс для роботи з паролями (...)
│   │       │   │   └── session.py   # Сервіс для управління сесіями користувачів (...)
│   │       │   │
│   │       │   ├── dictionaries/           # Сервіси для роботи з довідниками
│   │       │   │   ├── __init__.py         # Ініціалізація пакету `dictionaries.services`
│   │       │   │   ├── base_dict.py        # Базовий сервіс для довідників (...)
│   │       │   │   ├── status.py           # Сервіс для Status (...)
│   │       │   │   ├── user_role.py        # Сервіс для UserRole (...)
│   │       │   │   ├── group_type.py       # Сервіс для GroupType (...)
│   │       │   │   ├── task_type.py        # Сервіс для TaskType (...)
│   │       │   │   ├── bonus_type.py       # Сервіс для BonusType (...)
│   │       │   │   └── integration_type.py # Сервіс для IntegrationType (...)
│   │       │   │
│   │       │   ├── groups/          # Сервіси для роботи з групами
│   │       │   │   ├── __init__.py  # Ініціалізація пакету `groups.services`
│   │       │   │   ├── group.py     # Сервіс для управління групами (...)
│   │       │   │   ├── settings.py  # Сервіс для управління налаштуваннями групи (...)
│   │       │   │   ├── membership.py# Сервіс для управління членством в групі (...)
│   │       │   │   ├── invitation.py# Сервіс для управління запрошеннями до групи (...)
│   │       │   │   ├── template.py  # Сервіс для управління (...)
│   │       │   │   └── poll.py      # Сервіс для управління (...)
│   │       │   │
│   │       │   ├── tasks/           # Сервіси для роботи з завданнями
│   │       │   │   ├── __init__.py  # Ініціалізація пакету `tasks.services`
│   │       │   │   ├── task.py      # Сервіс для управління завданнями (...)
│   │       │   │   ├── assignment.py# Сервіс для логіки призначення завдань (...)
│   │       │   │   ├── completion.py# Сервіс для логіки виконання та підтвердження завдань (...)
│   │       │   │   ├── proposal.py  # Сервіс для логіки (...)
│   │       │   │   ├── review.py    # Сервіс для управління відгуками на завдання (...)
│   │       │   │   └── scheduler.py # Сервіс для логіки планувальника завдань (...)
│   │       │   │
│   │       │   ├── teams/           # Сервіси для роботи з командами
│   │       │   │   ├── __init__.py  # Ініціалізація пакету `teams.services`
│   │       │   │   ├── team.py      # Сервіс для логіки (...)
│   │       │   │   └── membership.py# Сервіс для логіки (...)
│   │       │   │
│   │       │   ├── bonuses/         # Сервіси для роботи з бонусами
│   │       │   │   ├── __init__.py  # Ініціалізація пакету `bonuses.services`
│   │       │   │   ├── bonus_rule.py# Сервіс для управління правилами бонусів (...)
│   │       │   │   ├── account.py   # Сервіс для управління рахунками користувачів (...)
│   │       │   │   ├── transaction.py# Сервіс для створення транзакцій (...)
│   │       │   │   ├── reward.py    # Сервіс для управління нагородами (...)
│   │       │   │   └── calculation.py# Сервіс для складних розрахунків бонусів (...)
│   │       │   │
│   │       │   ├── gamification/    # Сервіси для логіки геймифікації
│   │       │   │   ├── __init__.py  # Ініціалізація пакету `gamification.services`
│   │       │   │   ├── level.py     # Сервіс для управління рівнями (...)
│   │       │   │   ├── user_level.py# Сервіс для розрахунку та оновлення рівнів користувачів (...)
│   │       │   │   ├── badge.py     # Сервіс для управління бейджами (...)
│   │       │   │   ├── achievement.py# Сервіс для видачі досягнень (...)
│   │       │   │   └── rating.py    # Сервіс для розрахунку та оновлення рейтингів (...)
│   │       │   │
│   │       │   ├── reports/         # Сервіси для генерації звітів
│   │       │   │   ├── __init__.py  # Ініціалізація пакету `reports.services`
│   │       │   │   └── generation.py# Сервіс для (...)
│   │       │   │
│   │       │   ├── notifications/   # Сервіси для роботи зі сповіщеннями
│   │       │   │   ├── __init__.py  # Ініціалізація пакету `notifications.services`
│   │       │   │   ├── notification.py# Сервіс для створення та управління внутрішніми сповіщеннями (...)
│   │       │   │   ├── template.py  # Сервіс для роботи з шаблонами сповіщень (...)
│   │       │   │   ├── delivery.py  # Сервіс для логіки доставки сповіщень через різні канали (...)
│   │       │   │   ├── email.py     # Сервіс для відправки сповіщень по email (...)
│   │       │   │   ├── sms.py       # Сервіс для відправки сповіщень по SMS (...)
│   │       │   │   └── messenger.py # Сервіс для відправки сповіщень через месенджери (...)
│   │       │   │
│   │       │   ├── integrations/    # Сервіси для інтеграції з зовнішніми системами
│   │       │   │   ├── __init__.py  # Ініціалізація пакету `integrations.services`
│   │       │   │   ├── base_calendar.py  # Базовий сервіс для інтеграції з календарями (...)
│   │       │   │   ├── base_messenger.py # Базовий сервіс для інтеграції з месенджерами (...)
│   │       │   │   ├── base_tracker.py   # Базовий сервіс для інтеграції з трекерами (...)
│   │       │   │   ├── google.py    # Сервіс для інтеграції з Google Calendar (...)
│   │       │   │   ├── outlook.py   # Сервіс для інтеграції з Outlook Calendar (...)
│   │       │   │   ├── telegram.py  # Сервіс для інтеграції з Telegram (...)
│   │       │   │   ├── viber.py     # Сервіс для інтеграції з Viber (...)
│   │       │   │   ├── slack.py     # Сервіс для інтеграції з Slack (...)
│   │       │   │   ├── whatsapp.py  # Сервіс для інтеграції з WhatsApp (...)
│   │       │   │   ├── teams.py     # Сервіс для інтеграції з Microsoft Teams (...)
│   │       │   │   ├── jira.py      # Сервіс для інтеграції з Jira (...)
│   │       │   │   └── trello.py    # Сервіс для інтеграції з Trello (...)
│   │       │   │
│   │       │   ├── files/           # Сервіси для роботи з файлами
│   │       │   │   ├── __init__.py  # Ініціалізація пакету `files.services`
│   │       │   │   ├── file.py      # Сервіс для управління метаданими файлів (...)
│   │       │   │   ├── avatar.py    # Сервіс для управління аватарами користувачів (...)
│   │       │   │   └── storage.py   # Сервіс для взаємодії з файловим сховищем (...)
│   │       │   │
│   │       │   └── cache/           # Сервіси для роботи з кешем
│   │       │       ├── __init__.py  # Ініціалізація пакету `cache.services`
│   │       │       ├── redis.py     # Сервіс для роботи з Redis як кешем (...)
│   │       │       └── memory.py    # Сервіс для роботи з in-memory кешем (...)
│   │       │
│   │       ├── api/                 # Каталог для API ендпоінтів (FastAPI routers)
│   │       │   ├── __init__.py      # Ініціалізаційний файл пакету `api`, може агрегувати роутери версій
│   │       │   ├── dependencies.py  # Модуль зі специфічними залежностями для API (...)
│   │       │   ├── middleware.py    # Модуль зі специфічним middleware для API (APIKeyMiddleware, якщо потрібно) (...)
│   │       │   ├── router.py        # Головний роутер API, який підключає роутери різних версій (наприклад, `/api/v1`)
│   │       │   ├── exceptions.py    # Модуль для визначення та реєстрації обробників винятків для API (...)
│   │       │   │
│   │       │   ├── v1/              # Каталог для API версії 1
│   │       │   │   ├── __init__.py  # Ініціалізаційний файл пакету `v1` API
│   │       │   │   ├── router.py    # Головний роутер для API v1, який підключає роутери для окремих сутностей
│   │       │   │   │
│   │       │   │   ├── system/      # Ендпоінти для системних функцій
│   │       │   │   │   ├── __init__.py  # Ініціалізація пакету `system.api.v1`
│   │       │   │   │   ├── settings.py  # API для налатування системи
│   │       │   │   │   ├── cron_task.py # API для системних задач (cron)
│   │       │   │   │   ├── monitoring.py# API для отримання даних 
│   │       │   │   │   ├── health.py    # API для health check (`/health`)
│   │       │   │   │   └── init_data.py # API для запуску ініціалізації початкових даних
│   │       │   │   │
│   │       │   │   ├── auth/        # Ендпоінти для аутентифікації та управління профілем
│   │       │   │   │   ├── __init__.py  # Ініціалізація пакету `auth.api.v1`
│   │       │   │   │   ├── login.py     # API для логіну, логауту, отримання/оновлення токенів
│   │       │   │   │   ├── register.py  # API для реєстрації нових користувачів
│   │       │   │   │   ├── token.py     # API для роботи з токенами (наприклад, refresh)
│   │       │   │   │   ├── password.py  # API для зміни та відновлення паролю
│   │       │   │   │   └── profile.py   # API для перегляду та оновлення профілю користувача
│   │       │   │   │
│   │       │   │   ├── dictionaries/ # Ендпоінти для роботи з довідниками
│   │       │   │   │   ├── __init__.py          # Ініціалізація пакету `dictionaries.api.v1`
│   │       │   │   │   ├── statuses.py          # API для Status
│   │       │   │   │   ├── user_roles.py        # API для UserRole
│   │       │   │   │   ├── group_types.py       # API для GroupType
│   │       │   │   │   ├── task_types.py        # API для TaskType
│   │       │   │   │   ├── bonus_types.py       # API для BonusType
│   │       │   │   │   └── integration_types.py # API для IntegrationType
│   │       │   │   │
│   │       │   │   ├── users/        # Ендпоінти для управління користувачами (для суперюзера)
│   │       │   │   │   ├── __init__.py  # Ініціалізація пакету `users.api.v1`
│   │       │   │   │   └── users.py     # API для CRUD операцій з користувачами (суперюзер)
│   │       │   │   │
│   │       │   │   ├── groups/       # Ендпоінти для роботи з групами
│   │       │   │   │   ├── __init__.py  # Ініціалізація пакету `groups.api.v1`
│   │       │   │   │   ├── groups.py    # API для CRUD операцій з групами
│   │       │   │   │   ├── settings.py  # API для налаштувань групи
│   │       │   │   │   ├── membership.py# API для управління членством в групі
│   │       │   │   │   ├── invitation.py# API для управління запрошеннями до групи
│   │       │   │   │   ├── templates.py # API для шаблонів груп
│   │       │   │   │   ├── polls.py     # API для 
│   │       │   │   │   └── reports.py   # API для отримання звітів по групі
│   │       │   │   │
│   │       │   │   ├── tasks/        # Ендпоінти для роботи з завданнями та подіями
│   │       │   │   │   ├── __init__.py   # Ініціалізація пакету `tasks.api.v1`
│   │       │   │   │   ├── tasks.py      # API для CRUD операцій з завданнями
│   │       │   │   │   ├── assignments.py# API для призначення завдань
│   │       │   │   │   ├── completions.py# API для відмітки виконання та підтвердження завдань
│   │       │   │   │   ├── proposals.py  # API для пропозицій
│   │       │   │   │   └── reviews.py    # API для відгуків на завдання
│   │       │   │   │
│   │       │   │   ├── teams/          # Ендпоінти для роботи з командами
│   │       │   │   │   ├── __init__.py # Ініціалізація пакету `teams.api.v1`
│   │       │   │   │   ├── teams.py    # API для команд
│   │       │   │   │   └── members.py  # API для управління членством в команді
│   │       │   │   │
│   │       │   │   ├── bonuses/      # Ендпоінти для роботи з бонусами, рахунками та нагородами
│   │       │   │   │   ├── __init__.py    # Ініціалізація пакету `bonuses.api.v1`
│   │       │   │   │   ├── bonus_rules.py # API для CRUD BonusRule
│   │       │   │   │   ├── accounts.py    # API для перегляду рахунків та виписок
│   │       │   │   │   ├── transactions.py# API для перегляду/створення транзакцій
│   │       │   │   │   └── rewards.py     # API для CRUD Reward та їх отримання
│   │       │   │   │
│   │       │   │   ├── gamification/ # Ендпоінти для геймифікації
│   │       │   │   │   ├── __init__.py    # Ініціалізація пакету `gamification.api.v1`
│   │       │   │   │   ├── levels.py      # API для CRUD Level та перегляду UserLevel
│   │       │   │   │   ├── badges.py      # API для CRUD Badge та перегляду UserAchievement (бейджи)
│   │       │   │   │   ├── achievements.py# API для перегляду UserAchievement (загальних)
│   │       │   │   │   └── ratings.py     # API для перегляду UserGroupRating
│   │       │   │   │
│   │       │   │   ├── reports/      # Ендпоінти для генерації та отримання звітів
│   │       │   │   │   ├── __init__.py  # Ініціалізація пакету `reports.api.v1`
│   │       │   │   │   └── reports.py   # API для 
│   │       │   │   │
│   │       │   │   ├── notifications/# Ендпоінти для роботи зі сповіщеннями
│   │       │   │   │   ├── __init__.py     # Ініціалізація пакету `notifications.api.v1`
│   │       │   │   │   ├── notifications.py# API для перегляду сповіщень, відмітки як прочитані
│   │       │   │   │   ├── templates.py    # API для CRUD NotificationTemplate
│   │       │   │   │   └── delivery.py     # API для перегляду NotificationDeliveryAttempt
│   │       │   │   │
│   │       │   │   ├── integrations/ # Ендпоінти для управління інтеграціями
│   │       │   │   │   ├── __init__.py   # Ініціалізація пакету `integrations.api.v1`
│   │       │   │   │   ├── calendars.py  # API для налаштування синхронізації з календарями
│   │       │   │   │   ├── messengers.py # API для налаштування сповіщень через месенджери
│   │       │   │   │   └── trackers.py   # API для налаштування інтеграції з трекерами
│   │       │   │   │
│   │       │   │   └── files/        # Ендпоінти для роботи з файлами
│   │       │   │       ├── __init__.py   # Ініціалізація пакету `files.api.v1`
│   │       │   │       ├── files.py      # API для загальних операцій з FileRecord
│   │       │   │       └── avatars.py    # API спеціально для управління UserAvatar
│   │       │   │
│   │       │   ├── graphql/           # Каталог для GraphQL API (наприклад, з Strawberry або Ariadne). Тут зосереджена вся логіка, специфічна для GraphQL.
│   │       │   │   ├── __init__.py    # Ініціалізація пакету `graphql.api`. Може містити екземпляр GraphQLApp (наприклад, `strawberry.Schema` або `ariadne.GraphQL`), який потім монтується в основному FastAPI додатку в `app/main.py` або `app/src/api/router.py`.
│   │       │   │   ├── schema.py      # Головний файл GraphQL схеми. Визначає кореневі типи `Query`, `Mutation`, та, за потреби, `Subscription`. Він імпортує та об'єднує типи, резолвери запитів, мутацій та підписок з відповідних підкаталогів. Наприклад: `schema = strawberry.Schema(query=Query, mutation=Mutation, subscription=Subscription)`.
│   │       │   │   ├── dataloaders.py # Містить класи `DataLoader` (наприклад, з бібліотеки `aiodataloader`). Даталоадери використовуються для ефективного пакетного завантаження пов'язаних даних та вирішення проблеми N+1 запитів до бази даних в межах одного GraphQL запиту. Кожен даталоадер зазвичай відповідає за завантаження певного типу даних (наприклад, `UserLoaderById`, `GroupLoaderByUserId`). Екземпляри даталоадерів створюються для кожного запиту і передаються через GraphQL контекст.
│   │       │   │   ├── context.py     # Визначає функцію або клас для створення GraphQL контексту (`Context`). Контекст - це об'єкт, що передається в кожен GraphQL резолвер під час виконання запиту. Він може містити корисні для резолверів об'єкти, такі як: сесія бази даних (`db_session`), поточний аутентифікований користувач (`current_user`), екземпляри даталоадерів (`dataloaders`), запит (`request` від FastAPI).
│   │       │   │   ├── directives.py  # (Опціонально) Визначення кастомних GraphQL директив, якщо вони потрібні для розширення функціональності схеми (наприклад, директиви для перевірки прав доступу `@hasPermission(permission: "...")`, форматування рядків `@uppercase`). Strawberry та Ariadne мають свої способи визначення директив.
│   │       │   │   ├── scalars.py     # (Опціонально) Визначення кастомних скалярних типів GraphQL (наприклад, `DateTime`, `UUID`, `JSONString`, `PositiveInt`), якщо стандартних (`String`, `Int`, `Float`, `Boolean`, `ID`) недостатньо. Це дозволяє валідувати та серіалізувати специфічні формати даних.
│   │       │   │   │
│   │       │   │   ├── types/         # Каталог для визначення GraphQL типів (`ObjectType`, `InputType`, `InterfaceType`, `UnionType`, `EnumType`). Кожен файл зазвичай відповідає за типи, пов'язані з певною доменною сутністю.
│   │       │   │   │   ├── __init__.py     # Ініціалізація пакету `graphql.api.types`. Може експортувати всі типи для зручного імпорту в `schema.py` або в інші файли типів (для уникнення циклічних залежностей використовуються forward references або `strawberry.LazyType`).
│   │       │   │   │   ├── base.py         # (Опціонально) Базові GraphQL типи, інтерфейси (наприклад, `Node` для Relay-сумісності, що вимагає поля `id: ID!`), або спільні поля, які можуть успадковуватися іншими типами. Може містити GraphQL інтерфейси (наприклад, `TimestampedInterface` з полями `createdAt`, `updatedAt`).
│   │       │   │   │   ├── system.py       # GraphQL типи для системних сутностей (наприклад, `SystemSettingType`, `CronTaskType`, `SystemLogEntryType`).
│   │       │   │   │   ├── user.py         # GraphQL типи для користувачів та пов'язаних сутностей (наприклад, `UserType`, `UserRoleType`, `UserProfileType`, `AuthPayloadType` для відповіді логіну). Також може містити інпут-типи: `UserInputType`, `UserCreateInputType`, `UserUpdateInputType`.
│   │       │   │   │   ├── group.py        # GraphQL типи для груп та пов'язаних сутностей (наприклад, `GroupType`, `GroupMembershipType`, `GroupSettingsType`, `PollType`, `PollOptionType`, `PollVoteType`). Інпут-типи: `GroupCreateInputType`, `GroupUpdateInputType`.
│   │       │   │   │   ├── task.py         # GraphQL типи для завдань, подій та пов'язаних сутностей (наприклад, `TaskType`, `TaskCompletionType`, `TaskAssignmentType`, `TaskProposalType`, `TaskReviewType`). Інпут-типи: `TaskCreateInputType`.
│   │       │   │   │   ├── team.py         # GraphQL типи для команд (наприклад, `TeamType`, `TeamMembershipType`).
│   │       │   │   │   ├── bonus.py        # GraphQL типи для бонусів, нагород, рахунків (наприклад, `RewardType`, `UserAccountType`, `AccountTransactionType`, `BonusRuleType`). Інпут-типи: `RedeemRewardInputType`.
│   │       │   │   │   ├── gamification.py # GraphQL типи для елементів геймифікації (наприклад, `BadgeType`, `LevelType`, `UserAchievementType`, `UserGroupRatingType`).
│   │       │   │   │   ├── notification.py # GraphQL типи для сповіщень (`NotificationType`, `NotificationTemplateType`).
│   │       │   │   │   ├── file.py         # GraphQL типи для файлів (`FileRecordType`, `UserAvatarType`).
│   │       │   │   │   ├── dictionary.py   # GraphQL типи для довідників (`StatusType`, `GroupTypeType` і т.д., якщо вони потрібні в GraphQL).
│   │       │   │   │   └── input.py        # (Альтернативно до розміщення в кожному файлі) Загальний файл для всіх або деяких інпут-типів, якщо їх багато і це покращує структуру.
│   │       │   │   │
│   │       │   │   ├── queries/       # Каталог для визначення GraphQL запитів (резолверів для полів кореневого типу `Query`). Кожен файл містить резолвери для отримання даних певної категорії.
│   │       │   │   │   ├── __init__.py     # Ініціалізація пакету `graphql.api.queries`. Збирає всі резолвери запитів (зазвичай це клас `Query` з методами-резолверами, або окремі функції, декоровані `@strawberry.field` або `@Query.field`) для передачі в `schema.py`.
│   │       │   │   │   ├── system.py       # Резолвери для запитів, пов'язаних із системними сутностями (наприклад, `getSystemSettings`, `listCronTasks`).
│   │       │   │   │   ├── user.py         # Резолвери для запитів, пов'язаних з користувачами (наприклад, `me` (поточний користувач), `userById`, `usersList`).
│   │       │   │   │   ├── group.py        # Резолвери для запитів, пов'язаних з групами (наприклад, `groupById`, `userGroups`, `listPollsInGroup`).
│   │       │   │   │   ├── task.py         # Резолвери для запитів, пов'язаних із завданнями (наприклад, `tasksInGroup`, `taskById`).
│   │       │   │   │   ├── team.py         # Резолвери для запитів, пов'язаних з командами.
│   │       │   │   │   ├── bonus.py        # Резолвери для запитів, пов'язаних з бонусами та нагородами (наприклад, `userAccount`, `listRewards`).
│   │       │   │   │   ├── gamification.py # Резолвери для запитів, пов'язаних з геймифікацією (наприклад, `userBadges`, `groupLeaderboard`).
│   │       │   │   │   ├── report.py       # Резолвери для запитів, пов'язаних зі звітами (наприклад, `generateUserActivityReport`).
│   │       │   │   │   └── dictionary.py   # Резолвери для запитів до довідників (наприклад, `listStatuses`, `listTaskTypes`).
│   │       │   │   │
│   │       │   │   ├── mutations/     # Каталог для визначення GraphQL мутацій (резолверів для полів кореневого типу `Mutation`). Мутації використовуються для зміни даних на сервері.
│   │       │   │   │   ├── __init__.py     # Ініціалізація пакету `graphql.api.mutations`. Збирає всі резолвери мутацій (зазвичай це клас `Mutation` з методами-резолверами, або окремі функції, декоровані `@strawberry.mutation` або `@Mutation.field`) для передачі в `schema.py`.
│   │       │   │   │   ├── auth.py         # Резолвери для мутацій, пов'язаних з аутентифікацією (наприклад, `login`, `register`, `refreshToken`, `logout`, `requestPasswordReset`, `confirmPasswordReset`).
│   │       │   │   │   ├── user.py         # Резолвери для мутацій, пов'язаних з користувачами (наприклад, `updateUserProfile`, `updateUserAvatar`; створення користувачів може бути в `auth` або тут, якщо це адміністративна дія).
│   │       │   │   │   ├── group.py        # Резолвери для мутацій, пов'язаних з групами (наприклад, `createGroup`, `updateGroupSettings`, `inviteUserToGroup`, `joinGroup`, `leaveGroup`, `createPoll`).
│   │       │   │   │   ├── task.py         # Резолвери для мутацій, пов'язаних із завданнями (наприклад, `createTask`, `updateTask`, `deleteTask`, `assignTaskToUser`, `setTaskStatus`, `submitTaskProposal`, `reviewTask`).
│   │       │   │   │   ├── team.py         # Резолвери для мутацій, пов'язаних з командами (наприклад, `createTeam`, `addUserToTeam`).
│   │       │   │   │   ├── bonus.py        # Резолвери для мутацій, пов'язаних з бонусами (наприклад, `redeemReward`, `grantManualBonus` (адміністративна), `sendThankYouBonus`).
│   │       │   │   │   ├── gamification.py # (Опціонально) Мутації для геймифікації, якщо є прямі дії користувача, що впливають на неї, окрім автоматичних нарахувань.
│   │       │   │   │   ├── notification.py # Резолвери для мутацій, пов'язаних зі сповіщеннями (наприклад, `markNotificationAsRead`, `updateNotificationSettings`).
│   │       │   │   │   ├── file.py         # Резолвери для мутацій, пов'язаних із завантаженням файлів (наприклад, `uploadFile` для аватарок, іконок).
│   │       │   │   │   └── system.py       # Резолвери для мутацій, пов'язаних з системними налаштуваннями (наприклад, `updateSystemSetting` для superadmin).
│   │       │   │   │
│   │       │   │   └── subscriptions/ # Каталог для визначення GraphQL підписок (резолверів для полів кореневого типу `Subscription`), якщо вони використовуються для отримання даних в реальному часі через WebSockets.
│   │       │   │       ├── __init__.py     # Ініціалізація пакету `graphql.api.subscriptions`. Збирає всі резолвери підписок (зазвичай це клас `Subscription` з методами-резолверами) для передачі в `schema.py`.
│   │       │   │       ├── notification.py # Резолвери для підписок на нові сповіщення для поточного користувача.
│   │       │   │       └── task.py         # Резолвери для підписок на оновлення стану завдань в реальному часі (наприклад, в певній групі).
│   │       │   │
│   │       │   └── external/        # Каталог для API, призначених для взаємодії з зовнішніми системами (вебхуки)
│   │       │       ├── __init__.py    # Ініціалізація пакету `external.api`
│   │       │       ├── webhook.py     # Загальний ендпоінт для прийому вебхуків від різних сервісів
│   │       │       ├── calendar.py    # Ендпоінти для вебхуків від календарних сервісів (Google Calendar, Outlook)
│   │       │       ├── messenger.py   # Ендпоінти для вебхуків від месенджерів (Telegram, Viber, Slack, Teams)
│   │       │       └── tracker.py     # Ендпоінти для вебхуків від трекерів (Jira, Trello)
│   │       │
│   │       ├── tasks/               # Каталог для фонових завдань (Celery, FastAPI BackgroundTasks, APScheduler)
│   │       │   ├── __init__.py      # Ініціалізаційний файл пакету `tasks` (фонові)
│   │       │   ├── base.py          # Базовий клас для фонових завдань (наприклад, `BaseTask` для Celery)
│   │       │   ├── scheduler.py     # Конфігурація планувальника завдань (Celery Beat або налаштування APScheduler)
│   │       │   │
│   │       │   ├── system/          # Системні фонові завдання
│   │       │   │   ├── __init__.py  # Ініціалізація пакету `system.tasks`
│   │       │   │   ├── cleanup.py   # Завдання для періодичного очищення (CleanupTask: OldLogs, TempFiles, StaleSessions)
│   │       │   │   ├── backup.py    # Завдання для створення резервних копій (DatabaseBackupTask)
│   │       │   │   ├── cron_task.py # Завдання для виконання користувацьких CronTask
│   │       │   │   └── monitoring.py# Завдання для збору даних моніторингу (SystemMetricsCollectorTask)
│   │       │   │
│   │       │   ├── notifications/   # Фонові завдання для відправки сповіщень
│   │       │   │   ├── __init__.py  # Ініціалізація пакету `notifications.tasks`
│   │       │   │   ├── email.py     # Завдання для асинхронної відправки email (SendEmailTask)
│   │       │   │   ├── sms.py       # Завдання для асинхронної відправки SMS (SendSmsTask)
│   │       │   │   └── messenger.py # Завдання для асинхронної відправки через месенджери (SendMessengerNotificationTask)
│   │       │   │
│   │       │   ├── integrations/    # Фонові завдання для обробки інтеграцій
│   │       │   │   ├── __init__.py  # Ініціалізація пакету `integrations.tasks`
│   │       │   │   ├── calendar.py  # Завдання для періодичної синхронізації (SyncCalendarTask: Google, Outlook)
│   │       │   │   ├── messenger.py # Завдання для обробки вхідних повідомлень (ProcessIncomingMessengerMessageTask)
│   │       │   │   └── tracker.py   # Завдання для періодичної синхронізації (SyncTrackerTask: Jira, Trello)
│   │       │   │
│   │       │   └── gamification/    # Фонові завдання для логіки геймифікації
│   │       │       ├── __init__.py  # Ініціалізація пакету `gamification.tasks`
│   │       │       ├── levels.py    # Завдання для періодичного перерахунку рівнів (RecalculateUserLevelsTask)
│   │       │       ├── badges.py    # Завдання для автоматичної видачі бейджів (AwardBadgesTask)
│   │       │       └── ratings.py   # Завдання для періодичного перерахунку рейтингів (UpdateUserRatingsTask)
│   │       │
│   │       ├── utils/               # Каталог для різноманітних утилітарних функцій
│   │       │   ├── __init__.py      # Ініціалізаційний файл пакету `utils`
│   │       │   ├── hash.py          # Функції для хешування даних (якщо не в `core.security`)
│   │       │   ├── security.py      # Додаткові утиліти безпеки (генерація CSRF токенів, тощо)
│   │       │   ├── validators.py    # Набір загальних валідаторів даних (phone_number_validator, strong_password_validator)
│   │       │   ├── formatters.py    # Функції для форматування даних (date_formatter, currency_formatter)
│   │       │   ├── generators.py    # Функції для генерації даних (generate_random_code, generate_unique_slug)
│   │       │   ├── converters.py    # Функції для конвертації даних (markdown_to_html,
│   │       │   └── helpers.py       # Різноманітні дрібні допоміжні функції (get_object_or_404_custom)
│   │       │
│   │       ├── locales/              # Каталог для файлів локалізації backend
│   │       │   ├── __init__.py           # Ініціалізація пакету `locales`
│   │       │   ├── en/               # Каталог для англійської локалізації
│   │       │   │   └── messages.json # Файл перекладів для англійської мови
│   │       │   └── uk/               # Каталог для української локалізації
│   │       │       └── messages.json # Файл перекладів для української мови
│   │       │
│   │       ├── templates/                 # Шаблони для email/SMS
│   │       │   ├── __init__.py           # Ініціалізація пакету `templates`
│   │       │   ├── email/                 # Email шаблони
│   │       │   │   ├── welcome.html       # Вітальний email
│   │       │   │   ├── password_reset.html # Email для скидання пароля
│   │       │   │   └── task_notification.html # Email сповіщення про завдання
│   │       │   └── sms/                   # SMS шаблони
│   │       │       └── verification.txt   # SMS для верифікації
│   │       │
│   │       ├── workers/                  # Каталог для фонових завдань (Celery tasks).
│   │       │   ├── __init__.py           # Ініціалізація пакету `workers`
│   │       │   ├── base_task.py          # Базовий клас для Celery завдань, якщо потрібна спільна логіка
│   │       │   ├── system_tasks.py       # Celery завдання для системних операцій: очищення логів, резервне копіювання
│   │       │   ├── notification_tasks.py # Celery завдання для асинхронної відправки сповіщень (email, sms, push)
│   │       │   └── integration_tasks.py  # Celery завдання для взаємодії з зовнішніми інтеграціями (синхронізація календарів)
│   │       │
│   │       └── static/              # Каталог для статичних файлів, які можуть обслуговуватися backend
│   │           ├── images/          # Каталог для завантажених зображень
│   │           │   ├── avatars/     # Зображення аватарів користувачів (user_id_timestamp.jpg)
│   │           │   ├── groups/      # Зображення іконок груп (group_id_icon.png)
│   │           │   ├── rewards/     # Зображення іконок нагород (reward_id_image.svg)
│   │           │   └── badges/      # Зображення іконок бейджів (badge_id_icon.png)
│   │           ├── files/           # Каталог для інших типів завантажених файлів (task_attachment_id.pdf)
│   │           └── temp/            # Каталог для тимчасових файлів (upload_session_id.tmp)
│   │
│   ├── tests/                       # Каталог з тестами для backend (використовуючи pytest)
│   │   ├── __init__.py              # Ініціалізаційний файл пакету `tests`
│   │   ├── conftest.py              # Конфігурація pytest, фікстури, хелпери
│   │   ├── pytest.ini               # Конфігурація pytest
│   │   ├── data/                   # Тестові дані
│   │   │   ├── __init__.py              # Ініціалізація пакету тестових даних
│   │   │   ├── fixtures/                # Каталог для визначення pytest фікстур
│   │   │   │   ├── __init__.py          # Ініціалізація пакету `fixtures`
│   │   │   │   ├── test_database.py          # Фікстури для роботи з тестовою базою даних (...)
│   │   │   │   ├── test_users.py             # Фікстури для користувачів (...)
│   │   │   │   ├── test_groups.py            # Фікстури для груп (...)
│   │   │   │   ├── test_teams.py             # Фікстури для команд (...)
│   │   │   │   ├── test_tasks.py             # Фікстури для завдань (...)
│   │   │   │   ├── test_bonuses.py           # Фікстури для бонусів (...)
│   │   │   │   ├── test_dictionaries.py      # Фікстури для довідників (...)
│   │   │   │   ├── test_gamification.py      # Фікстури для геймифікації (...)
│   │   │   │   ├── test_notifications.py     # Фікстури для сповіщень (...)
│   │   │   │   ├── test_achievements.py      # Фікстури для досягнень (...)
│   │   │   │   ├── test_rewards.py           # Фікстури для нагород (...)
│   │   │   │   ├── test_reports.py           # Фікстури для звітів (...)
│   │   │   │   └── test_files.py             # Фікстури для файлів (...)
│   │   │   ├── factories/                   # Factory classes для створення тестових об'єктів
│   │   │   │   ├── __init__.py              # Ініціалізація пакету фабрик
│   │   │   │   ├── test_base_factory.py          # Базовий клас для всіх фабрик
│   │   │   │   ├── test_user_factory.py          # Фабрика для створення тестових користувачів
│   │   │   │   ├── test_group_factory.py         # Фабрика для створення тестових груп
│   │   │   │   ├── test_team_factory.py          # Фабрика для створення тестових команд
│   │   │   │   ├── test_task_factory.py          # Фабрика для створення тестових завдань
│   │   │   │   ├── test_reward_factory.py        # Фабрика для створення тестових нагород
│   │   │   │   ├── test_transaction_factory.py   # Фабрика для створення тестових транзакцій
│   │   │   │   ├── test_achievement_factory.py   # Фабрика для створення тестових досягнень
│   │   │   │   ├── test_notification_factory.py  # Фабрика для створення тестових сповіщень
│   │   │   │   └── test_dictionary_factory.py    # Фабрика для створення тестових довідників
│   │   │   └── samples/                     # Приклади тестових файлів
│   │   │       ├── __init__.py              # Ініціалізація пакету зразків
│   │   │       ├── images/                  # Тестові зображення (аватари, іконки)
│   │   │       │   ├── test_avatar_test.jpg      # Тестовий аватар користувача
│   │   │       │   ├── test_group_icon_test.png  # Тестова іконка групи
│   │   │       │   └── test_reward_icon_test.svg # Тестова іконка нагороди
│   │   │       └── documents/               # Тестові документи
│   │   │           ├── test_report.pdf      # Тестовий звіт pdf
│   │   │           ├── test_report.html     # Тестовий звіт html
│   │   │           └── test_export.xlsx     # Тестовий експорт даних
│   │   │
│   │   ├── unit/                    # Каталог для unit-тестів
│   │   │   ├── __init__.py          # Ініціалізація пакету `unit` тестів
│   │   │   ├── core/                           # Тести основних компонентів системи
│   │   │   │   ├── __init__.py                 # Ініціалізація тестів core
│   │   │   │   ├── test_database.py            # Тести підключення до БД
│   │   │   │   ├── test_config.py              # Тести конфігурації системи
│   │   │   │   ├── test_constants.py           # Тести констант системи
│   │   │   │   ├── test_exceptions.py          # Тести кастомних винятків
│   │   │   │   ├── test_logging.py             # Тести системи логування
│   │   │   │   ├── test_security.py            # Тести безпеки (JWT, rate limiting)
│   │   │   │   ├── test_permissions.py         # Тести системи дозволів
│   │   │   │   ├── test_dependencies.py        # Тести FastAPI dependencies
│   │   │   │   └── test_middleware.py          # Тести middleware компонентів
│   │   │   │
│   │   │   ├── models/         # unit-тести для SQLAlchemy моделей
│   │   │   │   ├── __init__.py      # Ініціалізація пакету `models`
│   │   │   │   ├── system/     # Тести для system моделей
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── test_settings.py
│   │   │   │   │   ├── test_cron.py
│   │   │   │   │   └── test_monitoring.py
│   │   │   │   │   ├── test_health.py
│   │   │   │   ├── auth/       # Тести для auth моделей
│   │   │   │   │   ├── __init__.py           # Ініціалізація тестів auth моделей
│   │   │   │   │   ├── test_user.py    # Тести моделі користувача
│   │   │   │   │   ├── test_token.py   # Тести моделі токенів
│   │   │   │   │   └── test_session.py # Тести моделі сесій
│   │   │   │   ├── dictionary/ # Тести для dictionary моделей
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── test_status.py      # Тести моделі 
│   │   │   │   │   ├── test_user_role.py   # Тести моделі 
│   │   │   │   │   ├── test_group_type.py  # Тести моделі 
│   │   │   │   │   ├── test_task_type.py   # Тести моделі 
│   │   │   │   │   ├── test_bonus_type.py  # Тести моделі 
│   │   │   │   │   └── test_integration.py # Тести моделі 
│   │   │   │   ├── group/     # Тести для group моделей
│   │   │   │   │   ├── __init__.py  # Ініціалізація тестів group моделей
│   │   │   │   │   ├── test_group.py       # Тести моделі групи
│   │   │   │   │   ├── test_settings.py    # Тести налаштувань групи
│   │   │   │   │   ├── test_membership.py  # Тести членства
│   │   │   │   │   ├── test_invitation.py  # Тести запрошень
│   │   │   │   │   ├── test_template.py    # Тести
│   │   │   │   │   ├── test_poll.py        # Тести
│   │   │   │   │   ├── test_poll_option.py # Тести
│   │   │   │   │   └── test_poll_vote.py   # Тести
│   │   │   │   ├── task/      # Тести для task моделей
│   │   │   │   │   ├── __init__.py  # Ініціалізація тестів task моделей
│   │   │   │   │   ├── test_task.py       # Тести моделі завдання
│   │   │   │   │   ├── test_assignment.py # Тести призначення
│   │   │   │   │   ├── test_completion.py # Тести виконання
│   │   │   │   │   ├── test_dependency.py # Тести 
│   │   │   │   │   ├── test_proposal.py   # Тести 
│   │   │   │   │   └── test_review.py     # Тести відгуків
│   │   │   │   ├── team/      # Тести для team моделей
│   │   │   │   │   ├── __init__.py  # Ініціалізація тестів team моделей
│   │   │   │   │   ├── test_team.py       # Тести 
│   │   │   │   │   └── test_membership.py # Тести 
│   │   │   │   ├── bonus/    # Тести для bonus моделей
│   │   │   │   │   ├── __init__.py  # Ініціалізація тестів bonus моделей
│   │   │   │   │   ├── test_bonus.py       # Тести моделі бонусу
│   │   │   │   │   ├── test_account.py     # Тести рахунку
│   │   │   │   │   ├── test_transaction.py # Тести транзакцій
│   │   │   │   │   └── test_reward.py      # Тести нагород
│   │   │   │   ├── gamification/ # Тести для gamification моделей
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── test_level.py
│   │   │   │   │   ├── test_badge.py
│   │   │   │   │   ├── test_achievement.py
│   │   │   │   │   └── test_rating.py
│   │   │   │   ├── report/ # Тести для report моделей
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   └── test_report.py
│   │   │   │   ├── notification/ # Тести для notification моделей
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── test_notification.py
│   │   │   │   │   ├── test_template.py
│   │   │   │   │   └── test_delivery.py
│   │   │   │   └── file/      # Тести для file моделей
│   │   │   │       ├── __init__.py
│   │   │   │       └── test_file.py
│   │   │   │
│   │   │   ├── schemas/         # unit-тести для Pydantic схем
│   │   │   │   ├── __init__.py      # Ініціалізація пакету `schemas`
│   │   │   │   ├── system/     # Тести для system схем
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── test_settings.py
│   │   │   │   │   ├── test_cron.py
│   │   │   │   │   └── test_monitoring.py
│   │   │   │   │   ├── test_health.py
│   │   │   │   ├── auth/       # Тести для auth схем
│   │   │   │   │   ├── __init__.py     # Ініціалізація пакету
│   │   │   │   │   ├── test_user.py    # Тести користувача
│   │   │   │   │   ├── test_token.py   # Тести токенів
│   │   │   │   │   └── test_session.py # Тести сесій
│   │   │   │   ├── dictionary/ # Тести для dictionary схем
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── test_status.py      # Тести 
│   │   │   │   │   ├── test_user_role.py   # Тести 
│   │   │   │   │   ├── test_group_type.py  # Тести 
│   │   │   │   │   ├── test_task_type.py   # Тести 
│   │   │   │   │   ├── test_bonus_type.py  # Тести 
│   │   │   │   │   └── test_integration.py # Тести 
│   │   │   │   ├── group/     # Тести для group схем
│   │   │   │   │   ├── __init__.py  # Ініціалізація пакету
│   │   │   │   │   ├── test_group.py       # Тести групи
│   │   │   │   │   ├── test_settings.py    # Тести налаштувань групи
│   │   │   │   │   ├── test_membership.py  # Тести членства
│   │   │   │   │   ├── test_invitation.py  # Тести запрошень
│   │   │   │   │   ├── test_template.py    # Тести
│   │   │   │   │   ├── test_poll.py        # Тести
│   │   │   │   │   ├── test_poll_option.py # Тести
│   │   │   │   │   └── test_poll_vote.py   # Тести
│   │   │   │   ├── task/      # Тести для task схем
│   │   │   │   │   ├── __init__.py  # Ініціалізація пакету
│   │   │   │   │   ├── test_task.py       # Тести завдання
│   │   │   │   │   ├── test_assignment.py # Тести призначення
│   │   │   │   │   ├── test_completion.py # Тести виконання
│   │   │   │   │   ├── test_dependency.py # Тести 
│   │   │   │   │   ├── test_proposal.py   # Тести 
│   │   │   │   │   └── test_review.py     # Тести відгуків
│   │   │   │   ├── team/      # Тести для team схем
│   │   │   │   │   ├── __init__.py  # Ініціалізація пакету team
│   │   │   │   │   ├── test_team.py       # Тести 
│   │   │   │   │   └── test_membership.py # Тести 
│   │   │   │   ├── bonus/    # Тести для bonus схем
│   │   │   │   │   ├── __init__.py  # Ініціалізація пакету
│   │   │   │   │   ├── test_bonus.py       # Тести бонусу
│   │   │   │   │   ├── test_account.py     # Тести рахунку
│   │   │   │   │   ├── test_transaction.py # Тести транзакцій
│   │   │   │   │   └── test_reward.py      # Тести нагород
│   │   │   │   ├── gamification/ # Тести для gamification схем
│   │   │   │   │   ├── __init__.py          # Ініціалізація пакету
│   │   │   │   │   ├── test_level.py
│   │   │   │   │   ├── test_badge.py
│   │   │   │   │   ├── test_achievement.py
│   │   │   │   │   └── test_rating.py
│   │   │   │   ├── report/ # Тести для report схем
│   │   │   │   │   ├── __init__.py        # Ініціалізація пакету
│   │   │   │   │   └── test_report.py
│   │   │   │   ├── notification/ # Тести для notification схем
│   │   │   │   │   ├── __init__.py          # Ініціалізація пакету
│   │   │   │   │   ├── test_notification.py
│   │   │   │   │   ├── test_template.py
│   │   │   │   │   └── test_delivery.py
│   │   │   │   └── file/      # Тести для file схем
│   │   │   │       ├── __init__.py       # Ініціалізація пакету
│   │   │   │       └── test_file.py
│   │   │   │
│   │   │   ├── services/       # Юніт-тести для сервісів
│   │   │   │   ├── __init__.py      # Ініціалізація пакету `services`
│   │   │   │   ├── system/     # Тести для system сервісів
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── test_initialization_service.py
│   │   │   │   │   └── test_settings_service.py
│   │   │   │   ├── auth/       # Тести для auth сервісів
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── test_user_service.py
│   │   │   │   │   ├── test_token_service.py
│   │   │   │   │   └── test_password_service.py
│   │   │   │   ├── group/     # Тести для group сервісів
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── test_group_service.py
│   │   │   │   │   ├── test_membership_service.py
│   │   │   │   │   └── test_invitation_service.py
│   │   │   │   ├── task/      # Тести для task сервісів
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── test_task_service.py
│   │   │   │   │   ├── test_completion_service.py
│   │   │   │   │   └── test_scheduler_service.py
│   │   │   │   ├── bonus/    # Тести для bonus сервісів
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── test_bonus_rule_service.py
│   │   │   │   │   ├── test_account_service.py
│   │   │   │   │   └── test_calculation_service.py
│   │   │   │   ├── gamification/ # Тести для gamification сервісів
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── test_level_service.py
│   │   │   │   │   └── test_badge_service.py
│   │   │   │   ├── notification/ # Тести для notification сервісів
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── test_internal_notification_service.py
│   │   │   │   │   └── test_email_notification_service.py
│   │   │   │   ├── integration/  # Тести для integration сервісів
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── test_google_calendar_service.py
│   │   │   │   │   └── test_telegram_integration_service.py
│   │   │   │   └── file/       # Тести для file сервісів
│   │   │   │       ├── __init__.py
│   │   │   │       └── test_file_service.py
│   │   │   │
│   │   │   ├── repositories/        # unit-тести репозиторіїв (доступ до даних)
│   │   │   │   ├── __init__.py      # Ініціалізація пакету `repositories`
│   │   │   │   ├── system/     # Тести для system схем
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── test_settings.py
│   │   │   │   │   ├── test_cron.py
│   │   │   │   │   └── test_monitoring.py
│   │   │   │   │   ├── test_health.py
│   │   │   │   ├── auth/       # Тести для auth схем
│   │   │   │   │   ├── __init__.py     # Ініціалізація пакету
│   │   │   │   │   ├── test_user.py    # Тести користувача
│   │   │   │   │   ├── test_token.py   # Тести токенів
│   │   │   │   │   └── test_session.py # Тести сесій
│   │   │   │   ├── dictionary/ # Тести для dictionary схем
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── test_status.py      # Тести 
│   │   │   │   │   ├── test_user_role.py   # Тести 
│   │   │   │   │   ├── test_group_type.py  # Тести 
│   │   │   │   │   ├── test_task_type.py   # Тести 
│   │   │   │   │   ├── test_bonus_type.py  # Тести 
│   │   │   │   │   └── test_integration.py # Тести 
│   │   │   │   ├── group/     # Тести для group схем
│   │   │   │   │   ├── __init__.py  # Ініціалізація пакету
│   │   │   │   │   ├── test_group.py       # Тести групи
│   │   │   │   │   ├── test_settings.py    # Тести налаштувань групи
│   │   │   │   │   ├── test_membership.py  # Тести членства
│   │   │   │   │   ├── test_invitation.py  # Тести запрошень
│   │   │   │   │   ├── test_template.py    # Тести
│   │   │   │   │   ├── test_poll.py        # Тести
│   │   │   │   │   ├── test_poll_option.py # Тести
│   │   │   │   │   └── test_poll_vote.py   # Тести
│   │   │   │   ├── task/      # Тести для task схем
│   │   │   │   │   ├── __init__.py  # Ініціалізація пакету
│   │   │   │   │   ├── test_task.py       # Тести завдання
│   │   │   │   │   ├── test_assignment.py # Тести призначення
│   │   │   │   │   ├── test_completion.py # Тести виконання
│   │   │   │   │   ├── test_dependency.py # Тести 
│   │   │   │   │   ├── test_proposal.py   # Тести 
│   │   │   │   │   └── test_review.py     # Тести відгуків
│   │   │   │   ├── team/      # Тести для team схем
│   │   │   │   │   ├── __init__.py  # Ініціалізація пакету team
│   │   │   │   │   ├── test_team.py       # Тести 
│   │   │   │   │   └── test_membership.py # Тести 
│   │   │   │   ├── bonus/    # Тести для bonus схем
│   │   │   │   │   ├── __init__.py  # Ініціалізація пакету
│   │   │   │   │   ├── test_bonus.py       # Тести бонусу
│   │   │   │   │   ├── test_account.py     # Тести рахунку
│   │   │   │   │   ├── test_transaction.py # Тести транзакцій
│   │   │   │   │   └── test_reward.py      # Тести нагород
│   │   │   │   ├── gamification/ # Тести для gamification схем
│   │   │   │   │   ├── __init__.py          # Ініціалізація пакету
│   │   │   │   │   ├── test_level.py
│   │   │   │   │   ├── test_badge.py
│   │   │   │   │   ├── test_achievement.py
│   │   │   │   │   └── test_rating.py
│   │   │   │   ├── report/ # Тести для report схем
│   │   │   │   │   ├── __init__.py        # Ініціалізація пакету
│   │   │   │   │   └── test_report.py
│   │   │   │   └── notification/ # Тести для notification схем
│   │   │   │       ├── __init__.py          # Ініціалізація пакету
│   │   │   │       ├── test_notification.py
│   │   │   │       ├── test_template.py
│   │   │   │       └── test_delivery.py
│   │   │   │
│   │   │   ├── tasks/                    # Тести фонових завдань (Celery)
│   │   │   │   ├── __init__.py           # Ініціалізація тестів tasks
│   │   │   │   ├── test_base.py          # Тести базового класу завдань
│   │   │   │   ├── test_notification.py  # Тести завдань розсилки сповіщень
│   │   │   │   ├── test_cleanup.py       # Тести завдань очищення логів
│   │   │   │   ├── test_backup.py        # Тести завдань резервного копіювання
│   │   │   │   ├── test_report.py        # Тести завдань генерації звітів
│   │   │   │   ├── test_achievement.py   # Тести завдань нарахування досягнень
│   │   │   │   ├── test_reminder.py      # Тести завдань нагадувань
│   │   │   │   └── test_integration.py   # Тести завдань інтеграцій
│   │   │   │
│   │   │   ├── migrations/                     # Тести міграцій БД
│   │   │   │   ├── __init__.py                 # Ініціалізація тестів міграцій
│   │   │   │   ├── test_migration_utils.py     # Тести утиліт міграцій
│   │   │   │   └── test_data_migrations.py     # Тести міграцій даних
│   │   │   │
│   │   │   └── utils/          # Юніт-тести для утилітарних функцій
│   │   │       ├── __init__.py      # Ініціалізація пакету `utils`
│   │   │       ├── test_security.py
│   │   │       ├── test_generators.py
│   │   │       ├── test_validators.py    # Тести валідаторів даних
│   │   │       ├── test_formatters.py    # Тести форматування даних
│   │   │       ├── test_converters.py    # Тести конвертерів даних
│   │   │       ├── test_generators.py    # Тести генераторів (токени, коди)
│   │   │       ├── test_encryption.py    # Тести шифрування/дешифрування
│   │   │       ├── test_hash.py          # Тести хешування паролів
│   │   │       ├── test_date.py          # Тести роботи з датами
│   │   │       ├── test_file.py          # Тести роботи з файлами
│   │   │       ├── test_image.py         # Тести обробки зображень
│   │   │       ├── test_email.py         # Тести відправки email
│   │   │       ├── test_sms.py           # Тести відправки SMS
│   │   │       ├── test_qr.py            # Тести генерації QR-кодів
│   │   │       ├── test_export.py        # Тести експорту даних
│   │   │       └── test_localization.py  # Тести локалізації
│   │   │
│   │   ├── integration/             # Каталог для інтеграційних тестів
│   │   │   ├── __init__.py          # Ініціалізація пакету `integration` тестів
│   │   │   ├── api/                 # Інтеграційні тести для API ендпоінтів
│   │   │   │   ├── __init__.py      # Ініціалізація пакету `test_api`
│   │   │   │   ├── graphql/                    # Тести GraphQL API
│   │   │   │   │   ├── __init__.py             # Ініціалізація тестів GraphQL
│   │   │   │   │   ├── test_auth_mutations.py  # Тести мутацій аутентифікації
│   │   │   │   │   ├── test_user_queries.py    # Тести запитів користувачів
│   │   │   │   │   ├── test_user_mutations.py  # Тести мутацій користувачів
│   │   │   │   │   ├── test_group_queries.py   # Тести запитів груп
│   │   │   │   │   ├── test_group_mutations.py # Тести мутацій груп
│   │   │   │   │   ├── test_task_queries.py    # Тести запитів завдань
│   │   │   │   │   ├── test_task_mutations.py  # Тести мутацій завдань
│   │   │   │   │   ├── test_reward_queries.py  # Тести запитів нагород
│   │   │   │   │   ├── test_reward_mutations.py # Тести мутацій нагород
│   │   │   │   │   ├── test_account_queries.py # Тести запитів рахунків
│   │   │   │   │   ├── test_transaction_queries.py # Тести запитів транзакцій
│   │   │   │   │   ├── test_achievement_queries.py # Тести запитів досягнень
│   │   │   │   │   ├── test_notification_queries.py # Тести запитів сповіщень
│   │   │   │   │   ├── test_report_queries.py  # Тести запитів звітів
│   │   │   │   │   └── test_directory_queries.py # Тести запитів довідників
│   │   │   │   ├── rest/                       # Тести REST API (якщо є)
│   │   │   │   │   ├── __init__.py             # Ініціалізація тестів REST
│   │   │   │   │   ├── test_health_endpoints.py # Тести health check endpoints
│   │   │   │   │   ├── test_file_endpoints.py  # Тести завантаження файлів
│   │   │   │   │   ├── test_webhook_endpoints.py # Тести веб-хук endpoints
│   │   │   │   │   └── test_integration_endpoints.py # Тести інтеграційних endpoints
│   │   │   │   └── common/                     # Спільні тести API
│   │   │   │       ├── __init__.py             # Ініціалізація спільних тестів API
│   │   │   │       ├── test_authentication.py  # Тести аутентифікації API
│   │   │   │       ├── test_authorization.py   # Тести авторизації API
│   │   │   │       ├── test_rate_limiting.py   # Тести rate limiting
│   │   │   │       ├── test_cors.py            # Тести CORS заголовків
│   │   │   │       ├── test_security_headers.py # Тести безпекових заголовків
│   │   │   │       ├── test_error_handling.py  # Тести обробки помилок
│   │   │   │       └── test_pagination.py      # Тести пагінації
│   │   │   │
│   │   │   ├── database/       # Інтеграційні тести, специфічні для бази даних
│   │   │   │   ├── __init__.py                 # Ініціалізація пакету
│   │   │   │   ├── test_connection_pool.py     # Тести пулу з'єднань
│   │   │   │   ├── test_transactions.py        # Тести транзакцій БД
│   │   │   │   ├── test_relationships.py       # Тести зв'язків між таблицями
│   │   │   │   ├── test_constraints.py         # Тести обмежень БД
│   │   │   │   ├── test_indexes.py             # Тести індексів БД
│   │   │   │   ├── test_migrations.py          # Тести застосування міграцій
│   │   │   │   └── test_data_integrity.py      # Тести цілісності даних
│   │   │   │
│   │   │   └── external/ # Інтеграційні тести для взаємодії з зовнішніми сервісами
│   │   │       ├── __init__.py      # Ініціалізація пакету
│   │   │       ├── test_google_calendar_integration.py # (з моками або тестовим акаунтом)
│   │   │       ├── test_telegram_bot_integration.py
│   │   │       └── test_email_sending_integration.py
│   │   │
│   │   ├── performance/                        # Тести продуктивності
│   │   │   ├── __init__.py                     # Ініціалізація тестів продуктивності
│   │   │   ├── test_api_performance.py         # Тести швидкодії API
│   │   │   ├── test_database_performance.py    # Тести продуктивності БД
│   │   │   ├── test_query_performance.py       # Тести швидкодії запитів
│   │   │   ├── test_concurrent_access.py       # Тести паралельного доступу
│   │   │   ├── test_memory_usage.py            # Тести використання пам'яті
│   │   │   ├── test_cache_performance.py       # Тести продуктивності кешу
│   │   │   └── test_load_scenarios.py          # Тести навантажувальних сценаріїв
│   │   ├── security/                           # Тести безпеки
│   │   │   ├── __init__.py                     # Ініціалізація тестів безпеки
│   │   │   ├── test_authentication_security.py # Тести безпеки аутентифікації
│   │   │   ├── test_authorization_security.py  # Тести безпеки авторизації
│   │   │   ├── test_input_validation.py        # Тести валідації вводу
│   │   │   ├── test_sql_injection.py           # Тести на SQL ін'єкції
│   │   │   ├── test_xss_protection.py          # Тести захисту від XSS
│   │   │   ├── test_csrf_protection.py         # Тести захисту від CSRF
│   │   │   ├── test_rate_limiting_security.py  # Тести безпеки rate limiting
│   │   │   ├── test_file_upload_security.py    # Тести безпеки завантаження файлів
│   │   │   └── test_data_encryption.py         # Тести шифрування даних
│   │   │   
│   │   ├── e2e/                                # End-to-end тести
│   │   │   ├── __init__.py                     # Ініціалізація E2E тестів
│   │   │   ├── test_complete_user_journey.py   # Тести повного шляху користувача
│   │   │   ├── test_admin_workflow.py          # Тести робочого процесу адміністратора
│   │   │   ├── test_group_lifecycle.py         # Тести жизненного циклу групи
│   │   │   ├── test_task_lifecycle.py          # Тести жизненного циклу завдання
│   │   │   ├── test_reward_lifecycle.py        # Тести жизненного циклу нагороди
│   │   │   ├── test_notification_system.py     # Тести системи сповіщень
│   │   │   ├── test_reporting_system.py        # Тести системи звітності
│   │   │   └── test_backup_system.py           # Тести системи резервного копіювання
│   │   ├── helpers/                            # Допоміжні функції для тестів
│   │   │   ├── __init__.py                     # Ініціалізація хелперів
│   │   │   ├── auth_helpers.py                 # Хелпери для аутентифікації в тестах
│   │   │   ├── database_helpers.py             # Хелпери для роботи з БД в тестах
│   │   │   ├── api_helpers.py                  # Хелпери для тестування API
│   │   │   ├── mock_helpers.py                 # Хелпери для створення моків
│   │   │   ├── assertion_helpers.py            # Кастомні assertion функції
│   │   │   ├── data_generators.py              # Генератори тестових даних
│   │   │   ├── file_helpers.py                 # Хелпери для роботи з файлами
│   │   │   ├── time_helpers.py                 # Хелпери для роботи з часом
│   │   │   └── cleanup_helpers.py              # Хелпери для очищення після тестів
│   │   ├── mocks/                              # Моки зовнішніх сервісів
│   │   │   ├── __init__.py                     # Ініціалізація моків
│   │   │   ├── email_mock.py                   # Мок email сервісу
│   │   │   ├── sms_mock.py                     # Мок SMS сервісу
│   │   │   ├── calendar_mock.py                # Мок календарних сервісів
│   │   │   ├── messenger_mock.py               # Мок месенджерів
│   │   │   ├── redis_mock.py                   # Мок Redis
│   │   │   ├── elasticsearch_mock.py           # Мок Elasticsearch
│   │   │   ├── firebase_mock.py                # Мок Firebase
│   │   │   ├── push_notification_mock.py       # Мок push сповіщень
│   │   │   └── webhook_mock.py                 # Мок веб-хуків
│   │   ├── stress/                             # Стрес тести
│   │   │   ├── __init__.py                     # Ініціалізація стрес тестів
│   │   │   ├── test_high_load.py               # Тести високого навантаження
│   │   │   ├── test_concurrent_users.py        # Тести багатьох користувачів одночасно
│   │   │   ├── test_memory_pressure.py         # Тести тиску на пам'ять
│   │   │   ├── test_database_stress.py         # Стрес тести БД
│   │   │   └── test_api_stress.py              # Стрес тести API
│   │   ├── compatibility/                      # Тести сумісності
│   │   │   ├── __init__.py                     # Ініціалізація тестів сумісності
│   │   │   ├── test_python_versions.py         # Тести різних версій Python
│   │   │   ├── test_database_versions.py       # Тести різних версій PostgreSQL
│   │   │   ├── test_browser_compatibility.py   # Тести сумісності з браузерами
│   │   │   └── test_api_versions.py            # Тести версій API
│   │   ├── regression/                         # Регресійні тести
│   │   │   ├── __init__.py                     # Ініціалізація регресійних тестів
│   │   │   ├── test_bug_fixes.py               # Тести виправлень багів
│   │   │   ├── test_feature_stability.py       # Тести стабільності функцій
│   │   │   └── test_performance_regression.py  # Тести регресії продуктивності
│   │   ├── coverage/                           # Звіти покриття тестами
│   │   │   ├── __init__.py                     # Ініціалізація покриття
│   │   │   ├── .gitkeep                        # Файл для збереження папки в git
│   │   │   └── README.md                       # Опис звітів покриття
│   │   ├── reports/                            # Звіти тестування
│   │   │   ├── __init__.py                     # Ініціалізація звітів
│   │   │   ├── .gitkeep                        # Файл для збереження папки в git
│   │   │   └── README.md                       # Опис звітів тестування
│   │   ├── docker/                             # Docker файли для тестування
│   │   │   ├── __init__.py                     # Ініціалізація Docker тестів
│   │   │   ├── docker-compose.test.yml         # Docker Compose для тестового середовища
│   │   │   ├── Dockerfile.test                 # Dockerfile для тестів
│   │   │   ├── test-entrypoint.sh              # Скрипт запуску тестів в контейнері
│   │   │   └── test-environment.env            # Змінні середовища для тестів
│   │   │
│   │   └── workflows/                      # Тести комплексних робочих процесів
│   │       ├── __init__.py                 # Ініціалізація тестів workflow
│   │       ├── test_user_registration_flow.py # Тести процесу реєстрації користувача
│   │       ├── test_group_creation_flow.py # Тести процесу створення групи
│   │       ├── test_task_execution_flow.py # Тести процесу виконання завдань
│   │       ├── test_reward_purchase_flow.py # Тести процесу купівлі нагород
│   │       ├── test_achievement_earning_flow.py # Тести процесу отримання досягнень
│   │       ├── test_notification_flow.py   # Тести процесу сповіщень
│   │       ├── test_backup_restore_flow.py # Тести процесу резервного копіювання
│   │       └── test_system_initialization_flow.py # Тести процесу ініціалізації
│   │   
│   ├── scripts/                     # Каталог для допоміжних скриптів
│   │   ├── __init__.py              # Ініціалізація пакету `scripts`
│   │   ├── db_init.sh               # Скрипт для ініціалізації бази даних
│   │   ├── db_backup.py             # Скрипт для створення резервної копії бази даних
│   │   ├── db_restore.py            # Скрипт для відновлення бази даних з резервної копії
│   │   ├── deploy.sh                # Скрипт для деплою на продакшен
│   │   ├── check-health.sh          # Скрипт для перевірки стану системи
│   │   ├── run_server.py            # Скрипт для запуску backend додатку (uvicorn)
│   │   ├── run_migrations.py        # Скрипт для виконання міграцій Alembic (`alembic upgrade head`)
│   │   ├── run_seed.py              # Скрипт для наповнення бази даних початковими даними
│   │   ├── create_superuser.py      # Скрипт для створення суперюзера з командного рядка
│   │   ├── create_system_users.py   # Скрипт для створення системних користувачів (odin, shadow)
│   │   ├── run_tests.py             # Скрипт для запуску всіх тестів (pytest)
│   │   ├── run_linters.py           # Скрипт для запуску лінтерів (black, ruff)
│   │   ├── generate_openapi_spec.py # Скрипт для генерації openapi.json
│   │   └── cleanup_temp_data.py     # Скрипт для очищення тимчасових даних
│   │
│   └── logs/                        # Каталог для зберігання файлів логів backend
│       ├── app.log                  # Основний файл логів додатку
│       ├── error.log                # Файл логів для помилок та винятків
│       ├── access.log               # Файл логів для запитів доступу (якщо налаштовано)
│       ├── debug.log                # Файл логів для відлагоджувальної інформації
│       ├── alembic.log              # Файл логів для міграцій Alembic
│       └── celery_worker.log        # Файл логів для Celery worker (якщо використовується)
│
├── frontend/                        # Каталог з кодом frontend частини проекту (Flutter)
│   ├── README.md                    # Документація для frontend частини: інструкції по збірці, запуску, тестуванню
│   ├── pubspec.yaml                 # Конфігураційний файл Flutter проекту: метадані, залежності
│   ├── pubspec.lock                 # Автоматично згенерований файл, що фіксує версії всіх залежностей
│   ├── analysis_options.yaml        # Конфігураційний файл для статичного аналізатора Dart (правила лінтингу)
│   ├── l10n.yaml                    # Конфігураційний файл для інструменту генерації локалізації Flutter
│   │
│   ├── android/                     # Каталог зі специфічними файлами для Android платформи (стандартна структура)
│   │   └── (деталізація пропущена для стислості, стандартна структура Flutter)
│   ├── ios/                         # Каталог зі специфічними файлами для iOS платформи (стандартна структура)
│   │   └── (деталізація пропущена для стислості, стандартна структура Flutter)
│   ├── web/                         # Каталог зі специфічними файлами для Web платформи (стандартна структура)
│   │   └── (деталізація пропущена для стислості, стандартна структура Flutter)
│   ├── windows/                     # Каталог зі специфічними файлами для Windows платформи (стандартна структура)
│   │   └── (деталізація пропущена для стислості, стандартна структура Flutter)
│   ├── macos/                       # Каталог зі специфічними файлами для macOS платформи (стандартна структура)
│   │   └── (деталізація пропущена для стислості, стандартна структура Flutter)
│   ├── linux/                       # Каталог зі специфічними файлами для Linux платформи (стандартна структура)
│   │   └── (деталізація пропущена для стислості, стандартна структура Flutter)
│   │
│   ├── lib/                         # Основний каталог з Dart кодом Flutter додатку
│   │   ├── main.dart                # Головний файл, точка входу Flutter додатку (функція `main`)
│   │   ├── app.dart                 # Кореневий віджет додатку (MaterialApp/CupertinoApp, налаштування тем, роутингу, локалізації)
│   │   │
│   │   ├── core/                    # Каталог з основними, загальними компонентами, утилітами та сервісами frontend
│   │   │   ├── config/              # Конфігурація frontend додатку
│   │   │   │   ├── app_config.dart  # Клас для конфігурації (API URL, ключі, середовища: dev, prod)
│   │   │   │   └── environment.dart # Enum або клас для визначення поточного середовища
│   │   │   ├── constants/           # Константи, що використовуються в усьому додатку
│   │   │   │   ├── app_constants.dart # Загальні константи (назви, ключі для сховища, розміри)
│   │   │   │   ├── route_constants.dart # Константи для імен маршрутів навігації
│   │   │   │   └── api_constants.dart   # Константи для шляхів API ендпоінтів
│   │   │   ├── di/                  # Налаштування Dependency Injection (get_it або Provider)
│   │   │   │   └── service_locator.dart # Файл для реєстрації та отримання залежностей
│   │   │   ├── errors/              # Обробка помилок та винятків на frontend
│   │   │   │   ├── failures.dart    # Класи для представлення бізнес-логічних помилок (NetworkFailure, ServerFailure, CacheFailure)
│   │   │   │   └── exceptions.dart  # Класи для представлення технічних винятків (ApiException, LocalStorageException)
│   │   │   ├── usecases/            # Business logic use cases (Clean Architecture)
│   │   │   │   └── usecase.dart     # Base use case class
│   │   │   ├── mixins/              # Dart mixins
│   │   │   ├── navigation/          # Логіка навігації (GoRouter, AutoRoute або стандартний Navigator)
│   │   │   │   ├── app_router.dart  # Конфігурація роутера, визначення маршрутів (GoRouter config)
│   │   │   │   └── app_routes.dart  # Список імен маршрутів та шляхів (якщо не в route_constants)
│   │   │   ├── network/             # Компоненти для роботи з мережею
│   │   │   │   ├── api_client.dart  # Клієнт для взаємодії з backend API (використовуючи `dio` або `http`)
│   │   │   │   ├── dio_provider.dart# (Якщо dio) Провайдер для екземпляру Dio
│   │   │   │   └── interceptors/    # Інтерсептори для API запитів
│   │   │   │       ├── auth_interceptor.dart # Додавання токенів авторизації
│   │   │   │       ├── logging_interceptor.dart # Логування запитів/відповідей
│   │   │   │       └── error_interceptor.dart   # Обробка HTTP помилок
│   │   │   ├── services/            # Загальні сервіси, що використовуються в різних частинах додатку
│   │   │   │   ├── auth_service.dart # Сервіс для управління станом аутентифікації
│   │   │   │   ├── internal_notification_service.dart # Сервіс для відображення внутрішніх сповіщень (snackbars, toasts)
│   │   │   │   ├── local_storage_service.dart # Абстракція для роботи з локальним сховищем (shared_preferences, Hive)
│   │   │   │   ├── sync_service.dart # Сервіс для синхронізації даних (online/offline)
│   │   │   │   ├── file_picker_service.dart # Сервіс для вибору файлів
│   │   │   │   └── permission_handler_service.dart # Сервіс для запиту дозволів (камера, сховище)
│   │   │   ├── theme/               # Компоненти для управління темами оформлення
│   │   │   │   ├── app_theme.dart   # Визначення основних тем (світла, темна), їх властивостей (ThemeData)
│   │   │   │   ├── app_colors.dart  # Палітра кольорів, що використовується в темах
│   │   │   │   ├── app_text_styles.dart # Визначення стилів тексту для різних елементів UI
│   │   │   │   ├── app_spacing.dart # Константи для відступів та розмірів
│   │   │   │   └── theme_provider.dart # Провайдер (StateNotifier, Cubit) для зміни поточної теми
│   │   │   ├── utils/               # Різноманітні утилітарні функції для frontend
│   │   │   │   ├── validators.dart  # Функції-валідатори для полів вводу форм (email, password, notEmpty)
│   │   │   │   ├── formatters.dart  # Форматери для даних (date, currency, timeAgo)
│   │   │   │   ├── logger.dart      # Налаштування та екземпляр логера (наприклад, пакет `logger`)
│   │   │   │   ├── debouncer.dart   # Клас для реалізації debounce логіки
│   │   │   │   └── network_info.dart# Утиліта для перевірки стану мережі
│   │   │   └── widgets/             # Загальні, перевикористовувані UI віджети
│   │   │       ├── buttons/         # Віджети кнопок
│   │   │       │   ├── primary_button.dart
│   │   │       │   ├── secondary_button.dart
│   │   │       │   └── icon_button_custom.dart
│   │   │       ├── inputs/          # Віджети полів вводу
│   │   │       │   ├── custom_text_field.dart
│   │   │       │   └── password_field.dart
│   │   │       ├──feedback/        # Віджети для зворотного зв'язку
│   │   │       │   ├── loading_indicator.dart
│   │   │       │   ├── error_message.dart
│   │   │       │   └── empty_state_widget.dart
│   │   │       ├── dialogs/         # Віджети діалогів
│   │   │       │   ├── confirmation_dialog.dart
│   │   │       │   └── info_dialog.dart
│   │   │       ├── app_bar/         # Кастомний AppBar
│   │   │       │   └── custom_app_bar.dart
│   │   │       ├── lists/           # Віджети для списків
│   │   │       │   └── paginated_list_view.dart
│   │   │       └── avatar_widget.dart # Віджет для відображення аватара
│   │   │
│   │   ├── data/                    # Шар даних: реалізація репозиторіїв, робота з джерелами даних
│   │   │   ├── datasources/         # Джерела даних
│   │   │   │   ├── local/           # Локальні джерела даних
│   │   │   │   │   ├── auth_local_datasource.dart
│   │   │   │   │   ├── group_local_datasource.dart
│   │   │   │   │   ├── task_local_datasource.dart
│   │   │   │   │   ├── user_profile_local_datasource.dart
│   │   │   │   │   ├── dictionary_local_datasource.dart
│   │   │   │   │   ├── bonus_local_datasource.dart
│   │   │   │   │   ├── gamification_local_datasource.dart
│   │   │   │   │   └── app_database.dart # (SQFlite/Drift) Визначення локальної БД
│   │   │   │   └── remote/          # Віддалені джерела даних (взаємодія з API)
│   │   │   │       ├── auth_remote_datasource.dart
│   │   │   │       ├── user_remote_datasource.dart # Для операцій з користувачами (superuser)
│   │   │   │       ├── group_remote_datasource.dart
│   │   │   │       ├── task_remote_datasource.dart
│   │   │   │       ├── bonus_remote_datasource.dart
│   │   │   │       ├── dictionary_remote_datasource.dart
│   │   │   │       ├── gamification_remote_datasource.dart
│   │   │   │       ├── notification_remote_datasource.dart
│   │   │   │       ├── file_remote_datasource.dart
│   │   │   │       └── system_remote_datasource.dart # Для системних налаштувань/моніторингу
│   │   │   ├── models/              # Моделі даних (DTO), з fromJson/toJson
│   │   │   │   ├── auth/
│   │   │   │   │   ├── user_model.dart
│   │   │   │   │   ├── token_model.dart
│   │   │   │   │   └── login_request_model.dart
│   │   │   │   ├── groups/
│   │   │   │   │   ├── group_model.dart
│   │   │   │   │   ├── group_settings_model.dart
│   │   │   │   │   ├── group_member_model.dart
│   │   │   │   │   └── group_invitation_model.dart
│   │   │   │   ├── tasks/
│   │   │   │   │   ├── task_model.dart
│   │   │   │   │   ├── event_model.dart
│   │   │   │   │   ├── task_assignment_model.dart
│   │   │   │   │   ├── task_completion_model.dart
│   │   │   │   │   └── task_review_model.dart
│   │   │   │   ├── bonuses/
│   │   │   │   │   ├── bonus_rule_model.dart
│   │   │   │   │   ├── user_account_model.dart
│   │   │   │   │   ├── account_transaction_model.dart
│   │   │   │   │   └── reward_model.dart
│   │   │   │   ├── dictionaries/
│   │   │   │   │   ├── status_model.dart
│   │   │   │   │   ├── user_role_model.dart
│   │   │   │   │   ├── user_type_model.dart
│   │   │   │   │   ├── group_type_model.dart
│   │   │   │   │   ├── task_type_model.dart
│   │   │   │   │   ├── bonus_type_model.dart
│   │   │   │   │   ├── calendar_model.dart
│   │   │   │   │   └── messenger_model.dart
│   │   │   │   ├── gamification/
│   │   │   │   │   ├── level_model.dart
│   │   │   │   │   ├── user_level_model.dart
│   │   │   │   │   ├── badge_model.dart
│   │   │   │   │   ├── user_achievement_model.dart
│   │   │   │   │   └── user_group_rating_model.dart
│   │   │   │   ├── notifications/
│   │   │   │   │   ├── notification_model.dart
│   │   │   │   │   └── notification_template_model.dart
│   │   │   │   ├── files/
│   │   │   │   │   └── file_record_model.dart
│   │   │   │   ├── system/
│   │   │   │   │   ├── system_settings_model.dart
│   │   │   │   │   └── system_log_model.dart
│   │   │   │   └── base/
│   │   │   │       └── paginated_response_model.dart
│   │   │   └── repositories_impl/   # Реалізація інтерфейсів репозиторіїв
│   │   │       ├── auth_repository_impl.dart
│   │   │       ├── user_repository_impl.dart
│   │   │       ├── group_repository_impl.dart
│   │   │       ├── task_repository_impl.dart
│   │   │       ├── bonus_repository_impl.dart
│   │   │       ├── dictionary_repository_impl.dart
│   │   │       ├── gamification_repository_impl.dart
│   │   │       ├── notification_repository_impl.dart
│   │   │       ├── file_repository_impl.dart
│   │   │       └── system_repository_impl.dart
│   │   │
│   │   ├── domain/                  # Шар доменної логіки: сутності, інтерфейси репозиторіїв, use cases
│   │   │   ├── entities/            # Доменні сутності (чисті Dart об'єкти)
│   │   │   │   ├── auth/
│   │   │   │   │   ├── user_entity.dart
│   │   │   │   │   └── token_entity.dart
│   │   │   │   ├── groups/
│   │   │   │   │   ├── group_entity.dart # ... і так далі, дзеркально до моделей
│   │   │   │   ├── tasks/
│   │   │   │   │   └── task_entity.dart  # ...
│   │   │   │   ├── bonuses/
│   │   │   │   │   └── bonus_rule_entity.dart # ...
│   │   │   │   ├── dictionaries/
│   │   │   │   │   └── status_entity.dart # ...
│   │   │   │   ├── gamification/
│   │   │   │   │   └── badge_entity.dart # ...
│   │   │   │   ├── notifications/
│   │   │   │   │   └── notification_entity.dart # ...
│   │   │   │   ├── files/
│   │   │   │   │   └── file_record_entity.dart # ...
│   │   │   │   └── system/
│   │   │   │       └── system_settings_entity.dart # ...
│   │   │   ├── repositories/        # Абстракції (інтерфейси) репозиторіїв
│   │   │   │   ├── auth_repository.dart
│   │   │   │   ├── user_repository.dart
│   │   │   │   ├── group_repository.dart
│   │   │   │   ├── task_repository.dart
│   │   │   │   ├── bonus_repository.dart
│   │   │   │   ├── dictionary_repository.dart
│   │   │   │   ├── gamification_repository.dart
│   │   │   │   ├── notification_repository.dart
│   │   │   │   ├── file_repository.dart
│   │   │   │   └── system_repository.dart
│   │   │   └── usecases/            # Use cases, що інкапсулюють конкретні операції бізнес-логіки
│   │   │       ├── auth/
│   │   │       │   ├── login_usecase.dart
│   │   │       │   ├── register_usecase.dart
│   │   │       │   ├── logout_usecase.dart
│   │   │       │   ├── get_current_user_usecase.dart
│   │   │       │   └── refresh_token_usecase.dart
│   │   │       ├── user/ # Use cases для управління користувачами (superuser)
│   │   │       │   ├── get_users_usecase.dart
│   │   │       │   ├── update_user_role_usecase.dart
│   │   │       │   └── delete_user_usecase.dart
│   │   │       ├── groups/
│   │   │       │   ├── create_group_usecase.dart
│   │   │       │   ├── get_group_details_usecase.dart
│   │   │       │   ├── get_user_groups_usecase.dart
│   │   │       │   ├── invite_user_to_group_usecase.dart
│   │   │       │   └── update_group_settings_usecase.dart
│   │   │       ├── tasks/
│   │   │       │   ├── create_task_usecase.dart
│   │   │       │   ├── get_tasks_in_group_usecase.dart
│   │   │       │   ├── complete_task_usecase.dart
│   │   │       │   └── assign_task_usecase.dart
│   │   │       ├── bonuses/
│   │   │       │   ├── get_user_account_usecase.dart
│   │   │       │   ├── redeem_reward_usecase.dart
│   │   │       │   └── get_rewards_list_usecase.dart
│   │   │       ├── dictionaries/
│   │   │       │   └── get_dictionary_items_usecase.dart # (e.g. get_statuses_usecase)
│   │   │       ├── gamification/
│   │   │       │   ├── get_user_badges_usecase.dart
│   │   │       │   └── get_group_ratings_usecase.dart
│   │   │       ├── notifications/
│   │   │       │   ├── get_notifications_usecase.dart
│   │   │       │   └── mark_notification_as_read_usecase.dart
│   │   │       ├── files/
│   │   │       │   └── upload_avatar_usecase.dart
│   │   │       └── system/
│   │   │           ├── get_system_settings_usecase.dart
│   │   │           └── update_system_setting_usecase.dart
│   │   │
│   │   ├── features/                # Функціональні модулі (фічі) додатку
│   │   │   ├── auth/                # Модуль аутентифікації
│   │   │   │   ├── presentation/
│   │   │   │   │   ├── manager/ (cubit, bloc, provider, riverpod provider)
│   │   │   │   │   │   ├── login_manager.dart # (e.g. LoginCubit/LoginNotifier)
│   │   │   │   │   │   ├── login_state.dart
│   │   │   │   │   │   ├── register_manager.dart
│   │   │   │   │   │   └── register_state.dart
│   │   │   │   │   ├── pages/
│   │   │   │   │   │   ├── login_page.dart
│   │   │   │   │   │   ├── register_page.dart
│   │   │   │   │   │   └── forgot_password_page.dart
│   │   │   │   │   └── widgets/
│   │   │   │   │       ├── login_form.dart
│   │   │   │   │       └── register_form.dart
│   │   │   ├── onboarding/          # Модуль ознайомлення (якщо є)
│   │   │   │   ├── presentation/
│   │   │   │   │   ├── manager/
│   │   │   │   │   │   └── onboarding_manager.dart
│   │   │   │   │   ├── pages/
│   │   │   │   │   │   └── onboarding_page.dart
│   │   │   │   │   └── widgets/
│   │   │   │   │       └── onboarding_carousel.dart
│   │   │   ├── dashboard/           # Головний екран/панель приладів
│   │   │   │   ├── presentation/
│   │   │   │   │   ├── manager/
│   │   │   │   │   │   └── dashboard_manager.dart
│   │   │   │   │   ├── pages/
│   │   │   │   │   │   └── dashboard_page.dart
│   │   │   │   │   └── widgets/
│   │   │   │   │       ├── summary_card.dart
│   │   │   │   │       └── quick_actions_widget.dart
│   │   │   ├── groups/              # Модуль груп
│   │   │   │   ├── presentation/
│   │   │   │   │   ├── manager/
│   │   │   │   │   │   ├── group_list_manager.dart
│   │   │   │   │   │   ├── group_details_manager.dart
│   │   │   │   │   │   └── group_create_manager.dart
│   │   │   │   │   ├── pages/
│   │   │   │   │   │   ├── group_list_page.dart
│   │   │   │   │   │   ├── group_details_page.dart
│   │   │   │   │   │   ├── create_group_page.dart
│   │   │   │   │   │   └── group_settings_page.dart
│   │   │   │   │   └── widgets/
│   │   │   │   │       ├── group_list_item.dart
│   │   │   │   │       ├── group_members_widget.dart
│   │   │   │   │       └── group_invitation_dialog.dart
│   │   │   ├── tasks/               # Модуль завдань
│   │   │   │   ├── presentation/
│   │   │   │   │   ├── manager/
│   │   │   │   │   │   ├── task_list_manager.dart
│   │   │   │   │   │   ├── task_details_manager.dart
│   │   │   │   │   │   └── task_create_manager.dart
│   │   │   │   │   ├── pages/
│   │   │   │   │   │   ├── task_list_page.dart
│   │   │   │   │   │   ├── task_details_page.dart
│   │   │   │   │   │   └── create_task_page.dart
│   │   │   │   │   └── widgets/
│   │   │   │   │       ├── task_list_item.dart
│   │   │   │   │       ├── task_filter_widget.dart
│   │   │   │   │       └── task_completion_button.dart
│   │   │   ├── bonuses_rewards/     # Модуль бонусів та нагород
│   │   │   │   ├── presentation/
│   │   │   │   │   ├── manager/
│   │   │   │   │   │   ├── user_account_manager.dart
│   │   │   │   │   │   └── reward_list_manager.dart
│   │   │   │   │   ├── pages/
│   │   │   │   │   │   ├── user_account_page.dart
│   │   │   │   │   │   └── reward_store_page.dart
│   │   │   │   │   └── widgets/
│   │   │   │   │       ├── transaction_history_widget.dart
│   │   │   │   │       └── reward_list_item.dart
│   │   │   ├── gamification/        # Модуль геймифікації
│   │   │   │   ├── presentation/
│   │   │   │   │   ├── manager/
│   │   │   │   │   │   ├── user_progress_manager.dart # (Рівні, досягнення)
│   │   │   │   │   │   └── group_leaderboard_manager.dart
│   │   │   │   │   ├── pages/
│   │   │   │   │   │   ├── user_achievements_page.dart
│   │   │   │   │   │   └── group_leaderboard_page.dart
│   │   │   │   │   └── widgets/
│   │   │   │   │       ├── badge_widget.dart
│   │   │   │   │       └── progress_bar_widget.dart
│   │   │   ├── notifications_feature/ # Модуль сповіщень (щоб не плутати з core/services/notification_service)
│   │   │   │   ├── presentation/
│   │   │   │   │   ├── manager/
│   │   │   │   │   │   └── notification_list_manager.dart
│   │   │   │   │   ├── pages/
│   │   │   │   │   │   └── notification_list_page.dart
│   │   │   │   │   └── widgets/
│   │   │   │   │       └── notification_item_widget.dart
│   │   │   ├── profile/             # Модуль профілю користувача
│   │   │   │   ├── presentation/
│   │   │   │   │   ├── manager/
│   │   │   │   │   │   └── user_profile_manager.dart
│   │   │   │   │   ├── pages/
│   │   │   │   │   │   ├── user_profile_page.dart
│   │   │   │   │   │   └── edit_profile_page.dart
│   │   │   │   │   └── widgets/
│   │   │   │   │       ├── avatar_upload_widget.dart
│   │   │   │   │       └── change_password_form.dart
│   │   │   ├── settings_app/        # Модуль налаштувань додатку (тема, мова)
│   │   │   │   ├── presentation/
│   │   │   │   │   ├── manager/
│   │   │   │   │   │   └── app_settings_manager.dart
│   │   │   │   │   ├── pages/
│   │   │   │   │   │   └── app_settings_page.dart
│   │   │   │   │   └── widgets/
│   │   │   │   │       ├── theme_selector_widget.dart
│   │   │   │   │       └── language_selector_widget.dart
│   │   │   ├── admin/               # Модуль для адміністративних функцій (суперюзер, адмін групи)
│   │   │   │   ├── presentation/
│   │   │   │   │   ├── manager/
│   │   │   │   │   │   ├── system_settings_manager.dart # (Суперюзер)
│   │   │   │   │   │   ├── user_management_manager.dart   # (Суперюзер)
│   │   │   │   │   │   └── group_admin_tools_manager.dart # (Адмін групи)
│   │   │   │   │   ├── pages/
│   │   │   │   │   │   ├── admin_dashboard_page.dart
│   │   │   │   │   │   ├── manage_users_page.dart
│   │   │   │   │   │   ├── manage_dictionaries_page.dart
│   │   │   │   │   │   └── system_monitoring_page.dart
│   │   │   │   │   └── widgets/
│   │   │   │   │       └── dictionary_edit_dialog.dart
│   │   │   └── common_widgets/        # Загальні віджети, які використовуються в декількох фічах, але не є core.widgets
│   │   │       └── confirmation_bottom_sheet.dart
│   │   │
│   │   ├── l10n/                    # Каталог для файлів локалізації (.arb)
│   │   │   ├── app_en.arb           # Файл локалізації для англійської мови
│   │   │   └── app_uk.arb           # Файл локалізації для української мови
│   │   │
│   │   └── generated/               # Каталог для автоматично згенерованих файлів
│   │       ├── l10n.dart            # Згенерований файл для доступу до локалізованих рядків
│   │       ├── app_localizations.dart # (Або інша назва залежно від інструменту)
│   │       └── (файли від freezed, json_serializable, mockito, etc.)
│   │
│   ├── assets/                      # Каталог для статичних ресурсів frontend
│   │   ├── images/                  # Зображення, що використовуються в UI
│   │   │   ├── logo/
│   │   │   │   └── app_logo.png
│   │   │   │   └── app_logo_dark.png
│   │   │   ├── icons/
│   │   │   │   ├── task_icon.svg
│   │   │   │   └── reward_icon.png
│   │   │   ├── illustrations/
│   │   │   │   └── empty_state_tasks.png
│   │   │   └── placeholders/
│   │   │       └── avatar_placeholder.jpg
│   │   ├── fonts/                   # Файли шрифтів
│   │   │   ├── Roboto-Regular.ttf
│   │   │   └── Roboto-Bold.ttf
│   │   └── data/                    # Статичні дані, наприклад, json-файли
│   │       └── default_config.json
│   │
│   └── test/                        # Каталог з тестами для Flutter додатку
│       ├── widget_test.dart         # Приклад віджет-тесту (часто генерується автоматично)
│       ├── core/                    # Тести для компонентів з `core`
│       │   ├── services/
│       │   │   └── auth_service_test.dart
│       │   └── utils/
│       │       └── validators_test.dart
│       ├── data/                    # Тести для `data` шару
│       │   ├── models/
│       │   │   ├── auth/
│       │   │   │   └── user_model_test.dart # ... і так далі для всіх моделей
│       │   │   └── groups/
│       │   │       └── group_model_test.dart
│       │   ├── datasources/
│       │   │   ├── remote/
│       │   │   │   └── auth_remote_datasource_test.dart # ... і так далі
│       │   │   └── local/
│       │   │       └── auth_local_datasource_test.dart
│       │   └── repositories_impl/
│       │       └── auth_repository_impl_test.dart # ... і так далі
│       ├── domain/                  # Тести для `domain` шару
│       │   ├── usecases/
│       │   │   ├── auth/
│       │   │   │   └── login_usecase_test.dart # ... і так далі для всіх usecases
│       │   │   └── groups/
│       │   │       └── create_group_usecase_test.dart
│       │   └── entities/
│       │       └── user_entity_test.dart # Тести для логіки в entities (якщо є)
│       ├── features/                # Тести для фіч (переважно state management)
│       │   ├── auth/
│       │   │   └── presentation/
│       │   │       └── manager/
│       │   │           └── login_manager_test.dart # ... і так далі для всіх managers/cubits
│       │   └── groups/
│       │       └── presentation/
│       │           └── manager/
│       │               └── group_list_manager_test.dart
│       ├── integration_test/        # Інтеграційні тести (взаємодія UI + логіка)
│       │   ├── app_test.dart        # Тест, що запускає весь додаток
│       │   └── auth_flow_test.dart  # Тест для потоку аутентифікації
│       ├── e2e/                     # End-to-end тести (використовуючи `patrol` або `flutter_driver`)
│       │   ├── patrol_test.dart     # (Якщо Patrol)
│       │   └── app_e2e.dart         # (Якщо flutter_driver)
│       ├── mocks/                   # Моки для використання в тестах
│       │   ├── core/
│       │   │   └── mock_local_storage_service.dart
│       │   ├── data/
│       │   │   ├── datasources/
│       │   │   │   └── mock_auth_remote_datasource.dart
│       │   │   └── repositories/
│       │   │       └── mock_auth_repository.dart # ... і так далі для всіх репозиторіїв
│       │   └── generated.mocks.dart # (Якщо використовується mockito build_runner)
│       └── fixtures/                # Фікстури (JSON-файли з відповідями API) для тестів
│           ├── auth/
│           │   ├── login_success_response.json
│           │   └── user_profile_response.json
│           └── groups/
│               └── group_list_response.json
│
└── .vscode/                         # Каталог з налаштуваннями для редактора VS Code
    ├── launch.json                  # Конфігурації запуску та відладки для VS Code (для backend та frontend)
    └── settings.json                # Налаштування робочого простору VS Code (форматування, лінтери, рекомендовані розширення)
