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
│
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
│   ├── deployment/                   # Каталог з документацією по розгортанню проекту
│   │   ├── docker.md                 # Детальні інструкції по роботі з Docker та Docker Compose для проекту
│   │   ├── kubernetes.md             # Інструкції та конфігураційні файли для розгортання в Kubernetes (якщо планується)
│   │   └── production.md             # Рекомендації та кроки для розгортання проекту в продакшн середовищі
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
│   │       │   │   ├── settings.py    # SQLAlchemy модель для зберігання налаштувань системи (SystemSettingModel)
│   │       │   │   ├── cron.py        # SQLAlchemy модель для системних задач (cron) (CronModel)
│   │       │   │   ├── monitoring.py  # SQLAlchemy моделі для збору даних моніторингу (SystemLogModel, PerformanceMetricModel)
│   │       │   │   └── health.py      # SQLAlchemy моделі для health check (ServiceHealthStatusModel) - якщо перевіряється стан залежних сервісів
│   │       │   │
│   │       │   ├── dictionaries/      # Каталог для моделей довідників (кожен успадковує `BaseDictModel`)
│   │       │   │   ├── __init__.py    # Ініціалізаційний файл пакету `dictionaries.models`
│   │       │   │   ├── base.py        # Базовий клас `BaseDictModel` для моделей довідників (успадковує `BaseMainModel`, додає `code`)
│   │       │   │   ├── status.py      # SQLAlchemy модель для довідника "Статуси" (StatusModel)
│   │       │   │   ├── user_role.py   # SQLAlchemy модель для довідника "Ролі користувачів" (UserRoleModel)
│   │       │   │   ├── group_type.py  # SQLAlchemy модель для довідника "Типи груп" (GroupTypeModel)
│   │       │   │   ├── task_type.py   # SQLAlchemy модель для довідника "Типи завдань" (TaskTypeModel)
│   │       │   │   ├── bonus_type.py  # SQLAlchemy модель для довідника "Типи бонусів" (BonusTypeModel)
│   │       │   │   └── integration.py # SQLAlchemy модель для довідника "Типи зовнішніх інтеграцій" (IntegrationTypeModel)
│   │       │   │
│   │       │   ├── auth/            # Каталог для моделей, пов'язаних з аутентифікацією та користувачами
│   │       │   │   ├── __init__.py  # Ініціалізаційний файл пакету `auth.models`
│   │       │   │   ├── user.py      # SQLAlchemy модель "Користувач" (UserModel), успадковує `BaseMainModel`
│   │       │   │   ├── token.py     # SQLAlchemy модель для зберігання Refresh токенів (RefreshTokenModel)
│   │       │   │   └── session.py   # SQLAlchemy модель для сесій користувачів (UserSessionModel)
│   │       │   │
│   │       │   ├── groups/          # Каталог для моделей, пов'язаних з групами
│   │       │   │   ├── __init__.py  # Ініціалізаційний файл пакету `groups.models`
│   │       │   │   ├── group.py     # SQLAlchemy модель "Група" (GroupModel), успадковує `BaseMainModel`
│   │       │   │   ├── settings.py  # SQLAlchemy модель для налаштувань конкретної групи (GroupSettingModel)
│   │       │   │   ├── membership.py# SQLAlchemy модель "Членство в групі" (GroupMembershipModel), зв'язок user-group з роллю
│   │       │   │   └── invitation.py# SQLAlchemy модель "Запрошення до групи" (GroupInvitationModel)
│   │       │   │
│   │       │   ├── tasks/           # Каталог для моделей, пов'язаних із завданнями та подіями
│   │       │   │   ├── __init__.py  # Ініціалізаційний файл пакету `tasks.models`
│   │       │   │   ├── task.py      # SQLAlchemy модель "Завдання" (TaskModel), успадковує `BaseMainModel`
│   │       │   │   ├── event.py     # SQLAlchemy модель "Подія" (EventModel), успадковує `BaseMainModel`
│   │       │   │   ├── assignment.py# SQLAlchemy модель "Призначення завдання/події" (TaskAssignmentModel)
│   │       │   │   ├── completion.py# SQLAlchemy модель "Виконання завдання/події" (TaskCompletionModel)
│   │       │   │   ├── dependency.py# SQLAlchemy модель "Зв'язки між завданнями (для підзадач)" (TaskDependencyModel)
│   │       │   │   ├── proposal.py  # SQLAlchemy модель "Пропозиція завдання/події" (TaskProposalModel)
│   │       │   │   └── review.py    # SQLAlchemy модель "Відгук на завдання" (TaskReviewModel)
│   │       │   │
│   │       │   ├── teams/           # Каталог для моделей, пов'язаних із командами для командних завдань
│   │       │   │   ├── __init__.py  # Ініціалізаційний файл пакету `teams.models`
│   │       │   │   ├── team.py      # SQLAlchemy модель "Команда" (TeamModel)
│   │       │   │   └── membership.py# SQLAlchemy модель "Членство в команді" (TeamMembershipModel)
│   │       │   │
│   │       │   ├── bonuses/         # Каталог для моделей, пов'язаних з бонусами та рахунками
│   │       │   │   ├── __init__.py  # Ініціалізаційний файл пакету `bonuses.models`
│   │       │   │   ├── bonus.py     # SQLAlchemy модель "Бонус" (BonusRuleModel), опис правила нарахування/штрафу для завдання/події
│   │       │   │   ├── account.py   # SQLAlchemy модель "Рахунок користувача" (UserAccountModel)
│   │       │   │   ├── transaction.py# SQLAlchemy модель "Транзакція по рахунку" (AccountTransactionModel)
│   │       │   │   └── reward.py    # SQLAlchemy модель "Нагорода" (RewardModel), успадковує `BaseMainModel`
│   │       │   │
│   │       │   ├── gamification/    # Каталог для моделей, пов'язаних з геймифікацією
│   │       │   │   ├── __init__.py  # Ініціалізаційний файл пакету `gamification.models`
│   │       │   │   ├── level.py     # SQLAlchemy модель "Рівень" (LevelModel) - як довідник або налаштування
│   │       │   │   ├── user_level.py# SQLAlchemy модель "Рівень користувача" (UserLevelModel) - зв'язок користувача з рівнем
│   │       │   │   ├── badge.py     # SQLAlchemy модель "Бейдж" (BadgeModel), успадковує `BaseMainModel`
│   │       │   │   ├── achievement.py# SQLAlchemy модель "Досягнення користувача" (UserAchievementModel) - зв'язок user-badge
│   │       │   │   └── rating.py    # SQLAlchemy модель "Рейтинг користувача" (UserGroupRatingModel)
│   │       │   │
│   │       │   ├── reports/         # Каталог для моделей, пов'язаних зі звітами
│   │       │   │   ├── __init__.py  # Ініціалізаційний файл пакету `reports.models`
│   │       │   │   └── report.py    # SQLAlchemy модель "Звіт" (ReportModel) Параметри генерації
│   │       │   │
│   │       │   ├── notifications/   # Каталог для моделей, пов'язаних зі сповіщеннями
│   │       │   │   ├── __init__.py  # Ініціалізаційний файл пакету `notifications.models`
│   │       │   │   ├── notification.py# SQLAlchemy модель "Сповіщення" (NotificationModel)
│   │       │   │   ├── template.py  # SQLAlchemy модель "Шаблон сповіщення" (NotificationTemplateModel)
│   │       │   │   └── delivery.py  # SQLAlchemy модель "Статус доставки сповіщення" (NotificationDeliveryAttemptModel)
│   │       │   │
│   │       │   └── files/           # Каталог для моделей, пов'язаних з файлами
│   │       │       ├── __init__.py  # Ініціалізаційний файл пакету `files.models`
│   │       │       ├── file.py      # SQLAlchemy модель "Файл" (FileRecordModel), метадані файлу
│   │       │       ├── upload.py    # (Може бути частиною `FileRecord` або окремою логікою/сервісом)
│   │       │       └── avatar.py    # SQLAlchemy модель "Аватар користувача" (UserAvatarModel), зв'язок User-FileRecord
│   │       │
│   │       ├── schemas/             # Каталог для Pydantic схем (валідація даних API запитів/відповідей)
│   │       │   ├── __init__.py      # Ініціалізаційний файл пакету `schemas`, може експортувати всі схеми
│   │       │   ├── base.py          # Модуль з базовими Pydantic схемами (BaseSchema, IDSchema, PaginatedResponseSchema, BaseMainSchema)
│   │       │   │
│   │       │   ├── system/          # Pydantic схеми для системних сутностей
│   │       │   │   ├── __init__.py  # Ініціалізація пакету `system.schemas`
│   │       │   │   ├── settings.py  # Pydantic схеми для SystemSetting (SystemSettingCreateSchema, SystemSettingUpdateSchema, SystemSettingResponseSchema)
│   │       │   │   ├── monitoring.py# Pydantic схеми для SystemLogSchema, PerformanceMetricSchema
│   │       │   │   └── health.py    # Pydantic схеми для ServiceHealthStatusSchema, HealthCheckResponseSchema, ComponentHealthSchema
│   │       │   │
│   │       │   ├── auth/            # Pydantic схеми для аутентифікації та користувачів
│   │       │   │   ├── __init__.py  # Ініціалізація пакету `auth.schemas`
│   │       │   │   ├── user.py      # Pydantic схеми для User (UserCreateSchema, UserUpdateSchema, UserResponseSchema, ...)
│   │       │   │   ├── token.py     # Pydantic схеми для Token (TokenResponseSchema, TokenRequestSchema)
│   │       │   │   └── login.py     # Pydantic схеми для Login (LoginRequestSchema, PasswordResetRequestSchema, PasswordResetConfirmSchema)
│   │       │   │
│   │       │   ├── dictionaries/       # Pydantic схеми для довідників
│   │       │   │   ├── __init__.py     # Ініціалізація пакету `dictionaries.schemas`
│   │       │   │   ├── base_dict.py    # Базові Pydantic схеми для довідників (DictionaryCreate, DictionaryUpdate, DictionaryResponse)
│   │       │   │   ├── statuses.py     # Pydantic схеми для Status (StatusCreate, StatusUpdate, StatusResponse)
│   │       │   │   ├── user_roles.py   # Pydantic схеми для UserRole
│   │       │   │   ├── user_types.py   # Pydantic схеми для UserType
│   │       │   │   ├── group_types.py  # Pydantic схеми для GroupType
│   │       │   │   ├── task_types.py   # Pydantic схеми для TaskType
│   │       │   │   ├── bonus_types.py  # Pydantic схеми для BonusType
│   │       │   │   └── integrations.py # Pydantic схеми для Integration
│   │       │   │
│   │       │   ├── groups/          # Pydantic схеми для груп
│   │       │   │   ├── __init__.py  # Ініціалізація пакету `groups.schemas`
│   │       │   │   ├── group.py     # Pydantic схеми для Group (GroupCreate, GroupUpdate, GroupResponse, GroupDetailedResponse)
│   │       │   │   ├── settings.py  # Pydantic схеми для GroupSetting (GroupSettingUpdate, GroupSettingResponse)
│   │       │   │   ├── membership.py# Pydantic схеми для GroupMembership (MembershipCreate, MembershipUpdate, MembershipResponse)
│   │       │   │   └── invitation.py# Pydantic схеми для GroupInvitation (InvitationCreate, InvitationResponse, InvitationAccept)
│   │       │   │
│   │       │   ├── tasks/           # Pydantic схеми для завдань
│   │       │   │   ├── __init__.py  # Ініціалізація пакету `tasks.schemas`
│   │       │   │   ├── task.py      # Pydantic схеми для Task (TaskCreate, TaskUpdate, TaskResponse)
│   │       │   │   ├── event.py     # Pydantic схеми для Event (EventCreate, EventUpdate, EventResponse)
│   │       │   │   ├── assignment.py# Pydantic схеми для TaskAssignment (AssignmentCreate, AssignmentResponse)
│   │       │   │   ├── completion.py# Pydantic схеми для TaskCompletion (CompletionCreateRequest, CompletionUpdateRequest, CompletionResponse, CompletionAdminUpdateRequest)
│   │       │   │   └── review.py    # Pydantic схеми для TaskReview (ReviewCreate, ReviewUpdate, ReviewResponse)
│   │       │   │
│   │       │   ├── bonuses/         # Pydantic схеми для бонусів
│   │       │   │   ├── __init__.py  # Ініціалізація пакету `bonuses.schemas`
│   │       │   │   ├── bonus_rule.py# Pydantic схеми для BonusRule (BonusRuleCreate, BonusRuleUpdate, BonusRuleResponse)
│   │       │   │   ├── account.py   # Pydantic схеми для UserAccount (UserAccountResponse)
│   │       │   │   ├── transaction.py# Pydantic схеми для AccountTransaction (TransactionResponse, ManualTransactionRequest)
│   │       │   │   └── reward.py    # Pydantic схеми для Reward (RewardCreate, RewardUpdate, RewardResponse, RedeemRewardRequest)
│   │       │   │
│   │       │   ├── gamification/    # Pydantic схеми для геймифікації
│   │       │   │   ├── __init__.py  # Ініціалізація пакету `gamification.schemas`
│   │       │   │   ├── level.py     # Pydantic схеми для Level (LevelCreate, LevelUpdate, LevelResponse)
│   │       │   │   ├── user_level.py# Pydantic схеми для UserLevel (UserLevelResponse)
│   │       │   │   ├── badge.py     # Pydantic схеми для Badge (BadgeCreate, BadgeUpdate, BadgeResponse)
│   │       │   │   ├── achievement.py# Pydantic схеми для UserAchievement (UserAchievementResponse)
│   │       │   │   └── rating.py    # Pydantic схеми для UserGroupRating (UserGroupRatingResponse)
│   │       │   │
│   │       │   ├── notifications/   # Pydantic схеми для сповіщень
│   │       │   │   ├── __init__.py  # Ініціалізація пакету `notifications.schemas`
│   │       │   │   ├── notification.py# Pydantic схеми для Notification (NotificationResponse, NotificationUpdate)
│   │       │   │   ├── template.py  # Pydantic схеми для NotificationTemplate (TemplateCreate, TemplateUpdate, TemplateResponse)
│   │       │   │   └── delivery.py  # Pydantic схеми для NotificationDeliveryAttempt (DeliveryAttemptResponse)
│   │       │   │
│   │       │   └── files/           # Pydantic схеми для файлів
│   │       │       ├── __init__.py  # Ініціалізація пакету `files.schemas`
│   │       │       ├── file.py      # Pydantic схеми для FileRecord (FileRecordResponse)
│   │       │       ├── upload.py    # Pydantic схеми для процесу завантаження (FileUploadResponse, PresignedUrlResponse)
│   │       │       └── avatar.py    # Pydantic схеми для UserAvatar (UserAvatarResponse)
│   │       │
│   │       ├── repositories/        # Каталог для репозиторіїв - шару абстракції для доступу до даних
│   │       │   ├── __init__.py      # Ініціалізаційний файл пакету `repositories`, може експортувати всі репозиторії
│   │       │   ├── base.py          # Модуль з базовим класом репозиторію `BaseRepository` (CRUD операції)
│   │       │   │
│   │       │   ├── system/          # Репозиторії для системних сутностей
│   │       │   │   ├── __init__.py  # Ініціалізація пакету `system.repositories`
│   │       │   │   ├── settings.py  # Репозиторій для SystemSetting (SystemSettingRepository)
│   │       │   │   ├── monitoring.py# Репозиторій для SystemLog, PerformanceMetric (SystemLogRepository)
│   │       │   │   └── health.py    # Репозиторій для ServiceHealthStatus (ServiceHealthRepository)
│   │       │   │
│   │       │   ├── auth/            # Репозиторії для аутентифікації та користувачів
│   │       │   │   ├── __init__.py  # Ініціалізація пакету `auth.repositories`
│   │       │   │   ├── user.py      # Репозиторій для User (UserRepository)
│   │       │   │   ├── token.py     # Репозиторій для RefreshToken (RefreshTokenRepository)
│   │       │   │   └── session.py   # Репозиторій для UserSession (UserSessionRepository)
│   │       │   │
│   │       │   ├── dictionaries/       # Репозиторії для довідників
│   │       │   │   ├── __init__.py     # Ініціалізація пакету `dictionaries.repositories`
│   │       │   │   ├── base_dict.py    # Базовий репозиторій для довідників (BaseDictionaryRepository)
│   │       │   │   ├── statuses.py     # Репозиторій для Status (StatusRepository)
│   │       │   │   ├── user_roles.py   # Репозиторій для UserRole (UserRoleRepository)
│   │       │   │   ├── user_types.py   # Репозиторій для UserType (UserTypeRepository)
│   │       │   │   ├── group_types.py  # Репозиторій для GroupType (GroupTypeRepository)
│   │       │   │   ├── task_types.py   # Репозиторій для TaskType (TaskTypeRepository)
│   │       │   │   ├── bonus_types.py  # Репозиторій для BonusType (BonusTypeRepository)
│   │       │   │   └── integrations.py # Репозиторій для MessengerPlatform (IntegrationRepository)
│   │       │   │
│   │       │   ├── groups/          # Репозиторії для груп
│   │       │   │   ├── __init__.py  # Ініціалізація пакету `groups.repositories`
│   │       │   │   ├── group.py     # Репозиторій для Group (GroupRepository)
│   │       │   │   ├── settings.py  # Репозиторій для GroupSetting (GroupSettingRepository)
│   │       │   │   ├── membership.py# Репозиторій для GroupMembership (GroupMembershipRepository)
│   │       │   │   └── invitation.py# Репозиторій для GroupInvitation (GroupInvitationRepository)
│   │       │   │
│   │       │   ├── tasks/           # Репозиторії для завдань
│   │       │   │   ├── __init__.py  # Ініціалізація пакету `tasks.repositories`
│   │       │   │   ├── task.py      # Репозиторій для Task (TaskRepository)
│   │       │   │   ├── event.py     # Репозиторій для Event (EventRepository)
│   │       │   │   ├── assignment.py# Репозиторій для TaskAssignment (TaskAssignmentRepository)
│   │       │   │   ├── completion.py# Репозиторій для TaskCompletion (TaskCompletionRepository)
│   │       │   │   └── review.py    # Репозиторій для TaskReview (TaskReviewRepository)
│   │       │   │
│   │       │   ├── bonuses/         # Репозиторії для бонусів
│   │       │   │   ├── __init__.py  # Ініціалізація пакету `bonuses.repositories`
│   │       │   │   ├── bonus_rule.py# Репозиторій для BonusRule (BonusRuleRepository)
│   │       │   │   ├── account.py   # Репозиторій для UserAccount (UserAccountRepository)
│   │       │   │   ├── transaction.py# Репозиторій для AccountTransaction (AccountTransactionRepository)
│   │       │   │   └── reward.py    # Репозиторій для Reward (RewardRepository)
│   │       │   │
│   │       │   ├── gamification/    # Репозиторії для геймифікації
│   │       │   │   ├── __init__.py  # Ініціалізація пакету `gamification.repositories`
│   │       │   │   ├── level.py     # Репозиторій для Level (LevelRepository)
│   │       │   │   ├── user_level.py# Репозиторій для UserLevel (UserLevelRepository)
│   │       │   │   ├── badge.py     # Репозиторій для Badge (BadgeRepository)
│   │       │   │   ├── achievement.py# Репозиторій для UserAchievement (UserAchievementRepository)
│   │       │   │   └── rating.py    # Репозиторій для UserGroupRating (UserGroupRatingRepository)
│   │       │   │
│   │       │   ├── notifications/   # Репозиторії для сповіщень
│   │       │   │   ├── __init__.py  # Ініціалізація пакету `notifications.repositories`
│   │       │   │   ├── notification.py# Репозиторій для Notification (NotificationRepository)
│   │       │   │   ├── template.py  # Репозиторій для NotificationTemplate (NotificationTemplateRepository)
│   │       │   │   └── delivery.py  # Репозиторій для NotificationDeliveryAttempt (NotificationDeliveryAttemptRepository)
│   │       │   │
│   │       │   └── files/           # Репозиторії для файлів
│   │       │       ├── __init__.py  # Ініціалізація пакету `files.repositories`
│   │       │       ├── file.py      # Репозиторій для FileRecord (FileRecordRepository)
│   │       │       ├── upload.py    # Репозиторій завантаження
│   │       │       └── avatar.py    # Репозиторій для UserAvatar (UserAvatarRepository)
│   │       │
│   │       ├── services/            # Каталог для сервісів - шару бізнес-логіки
│   │       │   ├── __init__.py      # Ініціалізаційний файл пакету `services`, може експортувати всі сервіси
│   │       │   ├── base.py          # Модуль з базовим класом сервісу `BaseService` (якщо є спільна логіка)
│   │       │   │
│   │       │   ├── system/          # Системні сервіси
│   │       │   │   ├── __init__.py  # Ініціалізація пакету `system.services`
│   │       │   │   ├── settings.py  # Сервіс для управління налаштуваннями системи (SystemSettingService)
│   │       │   │   ├── monitoring.py# Сервіс для логіки моніторингу системи (SystemMonitoringService)
│   │       │   │   ├── health.py    # Сервіс для перевірки стану системи (HealthCheckService)
│   │       │   │   └── initialization.py# Сервіс для ініціалізації початкових даних (InitialDataService)
│   │       │   │
│   │       │   ├── auth/            # Сервіси, пов'язані з аутентифікацією та користувачами
│   │       │   │   ├── __init__.py  # Ініціалізація пакету `auth.services`
│   │       │   │   ├── user.py      # Сервіс для управління користувачами (UserService)
│   │       │   │   ├── token.py     # Сервіс для генерації та валідації токенів (TokenService)
│   │       │   │   ├── password.py  # Сервіс для роботи з паролями (PasswordService)
│   │       │   │   └── session.py   # Сервіс для управління сесіями користувачів (UserSessionService)
│   │       │   │
│   │       │   ├── dictionaries/       # Сервіси для роботи з довідниками
│   │       │   │   ├── __init__.py     # Ініціалізація пакету `dictionaries.services`
│   │       │   │   ├── base_dict.py    # Базовий сервіс для довідників (BaseDictionaryService)
│   │       │   │   ├── statuses.py     # Сервіс для Status (StatusService)
│   │       │   │   ├── user_roles.py   # Сервіс для UserRole (UserRoleService)
│   │       │   │   ├── user_types.py   # Сервіс для UserType (UserTypeService)
│   │       │   │   ├── group_types.py  # Сервіс для GroupType (GroupTypeService)
│   │       │   │   ├── task_types.py   # Сервіс для TaskType (TaskTypeService)
│   │       │   │   ├── bonus_types.py  # Сервіс для BonusType (BonusTypeService)
│   │       │   │   └── integrations.py # Сервіс для CalendarProvider (IntegrationService)
│   │       │   │
│   │       │   ├── groups/          # Сервіси для роботи з групами
│   │       │   │   ├── __init__.py  # Ініціалізація пакету `groups.services`
│   │       │   │   ├── group.py     # Сервіс для управління групами (GroupService)
│   │       │   │   ├── settings.py  # Сервіс для управління налаштуваннями групи (GroupSettingService)
│   │       │   │   ├── membership.py# Сервіс для управління членством в групі (GroupMembershipService)
│   │       │   │   └── invitation.py# Сервіс для управління запрошеннями до групи (GroupInvitationService)
│   │       │   │
│   │       │   ├── tasks/           # Сервіси для роботи з завданнями
│   │       │   │   ├── __init__.py  # Ініціалізація пакету `tasks.services`
│   │       │   │   ├── task.py      # Сервіс для управління завданнями (TaskService)
│   │       │   │   ├── event.py     # Сервіс для управління подіями (EventService)
│   │       │   │   ├── assignment.py# Сервіс для логіки призначення завдань (TaskAssignmentService)
│   │       │   │   ├── completion.py# Сервіс для логіки виконання та підтвердження завдань (TaskCompletionService)
│   │       │   │   ├── review.py    # Сервіс для управління відгуками на завдання (TaskReviewService)
│   │       │   │   └── scheduler.py # Сервіс для логіки планувальника завдань (TaskSchedulingService)
│   │       │   │
│   │       │   ├── bonuses/         # Сервіси для роботи з бонусами
│   │       │   │   ├── __init__.py  # Ініціалізація пакету `bonuses.services`
│   │       │   │   ├── bonus_rule.py# Сервіс для управління правилами бонусів (BonusRuleService)
│   │       │   │   ├── account.py   # Сервіс для управління рахунками користувачів (UserAccountService)
│   │       │   │   ├── transaction.py# Сервіс для створення транзакцій (AccountTransactionService)
│   │       │   │   ├── reward.py    # Сервіс для управління нагородами (RewardService)
│   │       │   │   └── calculation.py# Сервіс для складних розрахунків бонусів (BonusCalculationService)
│   │       │   │
│   │       │   ├── gamification/    # Сервіси для логіки геймифікації
│   │       │   │   ├── __init__.py  # Ініціалізація пакету `gamification.services`
│   │       │   │   ├── level.py     # Сервіс для управління рівнями (LevelService)
│   │       │   │   ├── user_level.py# Сервіс для розрахунку та оновлення рівнів користувачів (UserLevelService)
│   │       │   │   ├── badge.py     # Сервіс для управління бейджами (BadgeService)
│   │       │   │   ├── achievement.py# Сервіс для видачі досягнень (UserAchievementService)
│   │       │   │   └── rating.py    # Сервіс для розрахунку та оновлення рейтингів (UserRatingService)
│   │       │   │
│   │       │   ├── notifications/   # Сервіси для роботи зі сповіщеннями
│   │       │   │   ├── __init__.py  # Ініціалізація пакету `notifications.services`
│   │       │   │   ├── notification.py# Сервіс для створення та управління внутрішніми сповіщеннями (InternalNotificationService)
│   │       │   │   ├── template.py  # Сервіс для роботи з шаблонами сповіщень (NotificationTemplateService)
│   │       │   │   ├── delivery.py  # Сервіс для логіки доставки сповіщень через різні канали (NotificationDeliveryService)
│   │       │   │   ├── email.py     # Сервіс для відправки сповіщень по email (EmailNotificationService)
│   │       │   │   ├── sms.py       # Сервіс для відправки сповіщень по SMS (SmsNotificationService)
│   │       │   │   └── messenger.py # Сервіс для відправки сповіщень через месенджери (MessengerNotificationService)
│   │       │   │
│   │       │   ├── integrations/    # Сервіси для інтеграції з зовнішніми системами
│   │       │   │   ├── __init__.py  # Ініціалізація пакету `integrations.services`
│   │       │   │   ├── calendar.py  # Базовий сервіс для інтеграції з календарями (BaseCalendarIntegrationService)
│   │       │   │   ├── google.py    # Сервіс для інтеграції з Google Calendar (GoogleCalendarService)
│   │       │   │   ├── outlook.py   # Сервіс для інтеграції з Outlook Calendar (OutlookCalendarService)
│   │       │   │   ├── telegram.py  # Сервіс для інтеграції з Telegram (TelegramIntegrationService)
│   │       │   │   ├── viber.py     # Сервіс для інтеграції з Viber (ViberIntegrationService)
│   │       │   │   ├── slack.py     # Сервіс для інтеграції з Slack (SlackIntegrationService)
│   │       │   │   ├── whatsapp.py  # Сервіс для інтеграції з WhatsApp (WhatsAppIntegrationService)
│   │       │   │   └── teams.py     # Сервіс для інтеграції з Microsoft Teams (TeamsIntegrationService)
│   │       │   │
│   │       │   ├── files/           # Сервіси для роботи з файлами
│   │       │   │   ├── __init__.py  # Ініціалізація пакету `files.services`
│   │       │   │   ├── file.py      # Сервіс для управління метаданими файлів (FileRecordService)
│   │       │   │   ├── upload.py    # Сервіс для логіки завантаження файлів (FileUploadService)
│   │       │   │   ├── avatar.py    # Сервіс для управління аватарами користувачів (UserAvatarService)
│   │       │   │   └── storage.py   # Сервіс для взаємодії з файловим сховищем (LocalStorageService, S3StorageService)
│   │       │   │
│   │       │   └── cache/           # Сервіси для роботи з кешем
│   │       │       ├── __init__.py  # Ініціалізація пакету `cache.services`
│   │       │       ├── redis.py     # Сервіс для роботи з Redis як кешем (RedisCacheService)
│   │       │       └── memory.py    # Сервіс для роботи з in-memory кешем (InMemoryCacheService)
│   │       │
│   │       ├── api/                 # Каталог для API ендпоінтів (FastAPI routers)
│   │       │   ├── __init__.py      # Ініціалізаційний файл пакету `api`, може агрегувати роутери версій
│   │       │   ├── dependencies.py  # Модуль зі специфічними залежностями для API (get_current_active_superuser, get_current_active_group_admin)
│   │       │   ├── middleware.py    # Модуль зі специфічним middleware для API (APIKeyMiddleware, якщо потрібно)
│   │       │   ├── router.py        # Головний роутер API, який підключає роутери різних версій (наприклад, `/api/v1`)
│   │       │   ├── exceptions.py    # Модуль для визначення та реєстрації обробників винятків для API
│   │       │   │
│   │       │   ├── v1/              # Каталог для API версії 1
│   │       │   │   ├── __init__.py  # Ініціалізаційний файл пакету `v1` API
│   │       │   │   ├── router.py    # Головний роутер для API v1, який підключає роутери для окремих сутностей
│   │       │   │   │
│   │       │   │   ├── system/      # Ендпоінти для системних функцій
│   │       │   │   │   ├── __init__.py  # Ініціалізація пакету `system.api.v1`
│   │       │   │   │   ├── settings.py  # API для управління SystemSetting
│   │       │   │   │   ├── monitoring.py# API для отримання даних SystemLog, PerformanceMetric
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
│   │       │   │   │   ├── __init__.py   # Ініціалізація пакету `dictionaries.api.v1`
│   │       │   │   │   ├── statuses.py   # API для Status
│   │       │   │   │   ├── user_roles.py # API для UserRole
│   │       │   │   │   ├── user_types.py # API для UserType
│   │       │   │   │   ├── group_types.py# API для GroupType
│   │       │   │   │   ├── task_types.py # API для TaskType
│   │       │   │   │   ├── bonus_types.py# API для BonusType
│   │       │   │   │   ├── calendars.py  # API для CalendarProvider
│   │       │   │   │   └── messengers.py # API для MessengerPlatform
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
│   │       │   │   │   └── reports.py   # API для отримання звітів по групі
│   │       │   │   │
│   │       │   │   ├── tasks/        # Ендпоінти для роботи з завданнями та подіями
│   │       │   │   │   ├── __init__.py  # Ініціалізація пакету `tasks.api.v1`
│   │       │   │   │   ├── tasks.py     # API для CRUD операцій з завданнями
│   │       │   │   │   ├── events.py    # API для CRUD операцій з подіями
│   │       │   │   │   ├── assignments.py# API для призначення завдань
│   │       │   │   │   ├── completions.py# API для відмітки виконання та підтвердження завдань
│   │       │   │   │   └── reviews.py   # API для відгуків на завдання
│   │       │   │   │
│   │       │   │   ├── bonuses/      # Ендпоінти для роботи з бонусами, рахунками та нагородами
│   │       │   │   │   ├── __init__.py   # Ініціалізація пакету `bonuses.api.v1`
│   │       │   │   │   ├── bonus_rules.py# API для CRUD BonusRule
│   │       │   │   │   ├── accounts.py   # API для перегляду рахунків та виписок
│   │       │   │   │   ├── transactions.py# API для перегляду/створення транзакцій
│   │       │   │   │   └── rewards.py    # API для CRUD Reward та їх отримання
│   │       │   │   │
│   │       │   │   ├── gamification/ # Ендпоінти для геймифікації
│   │       │   │   │   ├── __init__.py   # Ініціалізація пакету `gamification.api.v1`
│   │       │   │   │   ├── levels.py     # API для CRUD Level та перегляду UserLevel
│   │       │   │   │   ├── badges.py     # API для CRUD Badge та перегляду UserAchievement (бейджи)
│   │       │   │   │   ├── achievements.py# API для перегляду UserAchievement (загальних)
│   │       │   │   │   └── ratings.py    # API для перегляду UserGroupRating
│   │       │   │   │
│   │       │   │   ├── notifications/# Ендпоінти для роботи зі сповіщеннями
│   │       │   │   │   ├── __init__.py   # Ініціалізація пакету `notifications.api.v1`
│   │       │   │   │   ├── notifications.py# API для перегляду сповіщень, відмітки як прочитані
│   │       │   │   │   ├── templates.py  # API для CRUD NotificationTemplate
│   │       │   │   │   └── delivery.py   # API для перегляду NotificationDeliveryAttempt
│   │       │   │   │
│   │       │   │   ├── integrations/ # Ендпоінти для управління інтеграціями
│   │       │   │   │   ├── __init__.py   # Ініціалізація пакету `integrations.api.v1`
│   │       │   │   │   ├── calendars.py  # API для налаштування синхронізації з календарями
│   │       │   │   │   └── messengers.py # API для налаштування сповіщень через месенджери
│   │       │   │   │
│   │       │   │   └── files/        # Ендпоінти для роботи з файлами
│   │       │   │       ├── __init__.py   # Ініціалізація пакету `files.api.v1`
│   │       │   │       ├── files.py      # API для загальних операцій з FileRecord
│   │       │   │       ├── uploads.py    # API для завантаження файлів (аватари, іконки)
│   │       │   │       └── avatars.py    # API спеціально для управління UserAvatar
│   │       │   │
│   │       │   ├── graphql/            # GraphQL API
│   │       │   │
│   │       │   │
│   │       │   └── external/        # Каталог для API, призначених для взаємодії з зовнішніми системами (вебхуки)
│   │       │       ├── __init__.py    # Ініціалізація пакету `external.api`
│   │       │       ├── webhook.py     # Загальний ендпоінт для прийому вебхуків від різних сервісів
│   │       │       ├── calendar.py    # Ендпоінти для вебхуків від календарних сервісів (Google Calendar, Outlook)
│   │       │       └── messenger.py   # Ендпоінти для вебхуків від месенджерів (Telegram, Viber, Slack, Teams)
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
│   │       │   │   └── messenger.py # Завдання для обробки вхідних повідомлень (ProcessIncomingMessengerMessageTask)
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
│   │       │   ├── en/               # Каталог для англійської локалізації
│   │       │   │   └── messages.json # Файл перекладів для англійської мови
│   │       │   └── uk/               # Каталог для української локалізації
│   │       │       └── messages.json # Файл перекладів для української мови
│   │       │
│   │       ├── templates/                 # Шаблони для email/SMS
│   │       │   ├── email/                 # Email шаблони
│   │       │   │   ├── welcome.html       # Вітальний email
│   │       │   │   ├── password_reset.html # Email для скидання пароля
│   │       │   │   └── task_notification.html # Email сповіщення про завдання
│   │       │   └── sms/                   # SMS шаблони
│   │       │       └── verification.txt   # SMS для верифікації
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
│   │   ├── conftest.py              # Глобальні фікстури та налаштування для тестів pytest (db_session, api_client, current_user_mock)
│   │   ├── fixtures/                # Каталог для визначення pytest фікстур
│   │   │   ├── __init__.py          # Ініціалізація пакету `fixtures`
│   │   │   ├── database.py          # Фікстури для роботи з тестовою базою даних
│   │   │   ├── users.py             # Фікстури для створення тестових користувачів (test_user, test_superuser, test_group_admin)
│   │   │   ├── groups.py            # Фікстури для створення тестових груп (test_group, test_group_with_members)
│   │   │   ├── tasks.py             # Фікстури для створення тестових завдань (test_task, test_event)
│   │   │   ├── bonuses.py           # Фікстури для створення тестових бонусів та нагород (test_bonus_rule, test_reward)
│   │   │   ├── dictionaries.py      # Фікстури для довідників (test_status, test_user_role)
│   │   │   ├── gamification.py      # Фікстури для геймифікації (test_badge, test_level)
│   │   │   ├── notifications.py     # Фікстури для сповіщень (test_notification_template)
│   │   │   └── files.py             # Фікстури для файлів (test_file_record)
│   │   │
│   │   ├── unit/                    # Каталог для unit-тестів
│   │   │   ├── __init__.py          # Ініціалізація пакету `unit` тестів
│   │   │   ├── test_models/         # unit-тести для SQLAlchemy моделей
│   │   │   │   ├── __init__.py      # Ініціалізація пакету `test_models`
│   │   │   │   ├── test_system/     # Тести для system моделей
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── test_system_settings_model.py
│   │   │   │   │   └── test_monitoring_model.py
│   │   │   │   ├── test_auth/       # Тести для auth моделей
│   │   │   │   │   ├── __init__.py           # Ініціалізація тестів auth моделей
│   │   │   │   │   ├── test_user_model.py    # Тести моделі користувача
│   │   │   │   │   ├── test_token_model.py   # Тести моделі токенів
│   │   │   │   │   └── test_session_model.py # Тести моделі сесій
│   │   │   │   ├── test_dictionaries/ # Тести для dictionary моделей
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── test_status_model.py
│   │   │   │   │   └── test_user_role_model.py # ... і так далі для всіх довідників
│   │   │   │   ├── test_groups/     # Тести для group моделей
│   │   │   │   │   ├── __init__.py  # Ініціалізація тестів group моделей
│   │   │   │   │   ├── test_group_model.py          # Тести моделі групи
│   │   │   │   │   ├── test_group_settings_model.py # Тести налаштувань групи
│   │   │   │   │   ├── test_membership_model.py     # Тести членства
│   │   │   │   │   └── test_invitation_model.py     # Тести запрошень
│   │   │   │   ├── test_tasks/      # Тести для task моделей
│   │   │   │   │   ├── __init__.py  # Ініціалізація тестів task моделей
│   │   │   │   │   ├── test_task_model.py       # Тести моделі завдання
│   │   │   │   │   ├── test_event_model.py      # Тести моделі події
│   │   │   │   │   ├── test_assignment_model.py # Тести призначення
│   │   │   │   │   ├── test_completion_model.py # Тести виконання
│   │   │   │   │   └── test_review_model.py     # Тести відгуків
│   │   │   │   ├── test_bonuses/    # Тести для bonus моделей
│   │   │   │       ├── __init__.py  # Ініціалізація тестів bonus моделей
│   │   │   │       ├── test_bonus_model.py       # Тести моделі бонусу
│   │   │   │       ├── test_account_model.py     # Тести рахунку
│   │   │   │       ├── test_transaction_model.py # Тести транзакцій
│   │   │   │       └── test_reward_model.py      # Тести нагород
│   │   │   │   ├── test_gamification/ # Тести для gamification моделей
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── test_level_model.py
│   │   │   │   │   ├── test_badge_model.py
│   │   │   │   │   └── test_achievement_model.py
│   │   │   │   ├── test_notifications/ # Тести для notification моделей
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── test_notification_model.py
│   │   │   │   │   └── test_template_model.py
│   │   │   │   └── test_files/      # Тести для file моделей
│   │   │   │       ├── __init__.py
│   │   │   │       └── test_file_record_model.py
│   │   │   │
│   │   │   ├── test_services/       # Юніт-тести для сервісів
│   │   │   │   ├── __init__.py      # Ініціалізація пакету `test_services`
│   │   │   │   ├── test_system/     # Тести для system сервісів
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── test_initialization_service.py
│   │   │   │   │   └── test_settings_service.py
│   │   │   │   ├── test_auth/       # Тести для auth сервісів
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── test_user_service.py
│   │   │   │   │   ├── test_token_service.py
│   │   │   │   │   └── test_password_service.py
│   │   │   │   ├── test_groups/     # Тести для group сервісів
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── test_group_service.py
│   │   │   │   │   ├── test_membership_service.py
│   │   │   │   │   └── test_invitation_service.py
│   │   │   │   ├── test_tasks/      # Тести для task сервісів
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── test_task_service.py
│   │   │   │   │   ├── test_completion_service.py
│   │   │   │   │   └── test_scheduler_service.py
│   │   │   │   ├── test_bonuses/    # Тести для bonus сервісів
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── test_bonus_rule_service.py
│   │   │   │   │   ├── test_account_service.py
│   │   │   │   │   └── test_calculation_service.py
│   │   │   │   ├── test_gamification/ # Тести для gamification сервісів
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── test_level_service.py
│   │   │   │   │   └── test_badge_service.py
│   │   │   │   ├── test_notifications/ # Тести для notification сервісів
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── test_internal_notification_service.py
│   │   │   │   │   └── test_email_notification_service.py
│   │   │   │   ├── test_integrations/  # Тести для integration сервісів
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── test_google_calendar_service.py
│   │   │   │   │   └── test_telegram_integration_service.py
│   │   │   │   └── test_files/       # Тести для file сервісів
│   │   │   │       ├── __init__.py
│   │   │   │       └── test_file_upload_service.py
│   │   │   │
│   │   │   └── test_utils/          # Юніт-тести для утилітарних функцій
│   │   │       ├── __init__.py      # Ініціалізація пакету `test_utils`
│   │   │       ├── test_hash_util.py
│   │   │       ├── test_security_util.py
│   │   │       ├── test_validators_util.py
│   │   │       ├── test_formatters_util.py
│   │   │       └── test_generators_util.py
│   │   │
│   │   ├── integration/             # Каталог для інтеграційних тестів
│   │   │   ├── __init__.py          # Ініціалізація пакету `integration` тестів
│   │   │   ├── test_api/            # Інтеграційні тести для API ендпоінтів
│   │   │   │   ├── __init__.py      # Ініціалізація пакету `test_api`
│   │   │   │   ├── test_system_api.py
│   │   │   │   ├── test_auth_api.py
│   │   │   │   ├── test_dictionaries_api.py
│   │   │   │   ├── test_users_api.py
│   │   │   │   ├── test_groups_api.py
│   │   │   │   ├── test_tasks_api.py
│   │   │   │   ├── test_bonuses_api.py
│   │   │   │   ├── test_gamification_api.py
│   │   │   │   ├── test_notifications_api.py
│   │   │   │   ├── test_integrations_api.py
│   │   │   │   └── test_files_api.py
│   │   │   │
│   │   │   ├── test_database/       # Інтеграційні тести, специфічні для бази даних
│   │   │   │   ├── __init__.py      # Ініціалізація пакету `test_database`
│   │   │   │   ├── test_migrations.py # Тести для перевірки коректності міграцій Alembic
│   │   │   │   ├── test_relationships.py# Тести для перевірки правильності SQLAlchemy зв'язків
│   │   │   │   └── test_constraints.py# Тести для перевірки обмежень бази даних
│   │   │   │
│   │   │   └── test_integrations_external/ # Інтеграційні тести для взаємодії з зовнішніми сервісами
│   │   │       ├── __init__.py      # Ініціалізація пакету `test_integrations_external`
│   │   │       ├── test_google_calendar_integration.py # (з моками або тестовим акаунтом)
│   │   │       ├── test_telegram_bot_integration.py
│   │   │       └── test_email_sending_integration.py
│   │   │
│   │   └── e2e/                     # Каталог для End-to-end тестів (через API)
│   │       ├── __init__.py          # Ініціалізація пакету `e2e` тестів
│   │       ├── test_full_user_registration_flow.py
│   │       ├── test_group_creation_and_management_flow.py
│   │       ├── test_task_lifecycle_flow.py
│   │       ├── test_bonus_awarding_flow.py
│   │       └── test_superuser_dictionary_management_flow.py
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
