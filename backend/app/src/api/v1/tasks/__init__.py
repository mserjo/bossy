# backend/app/src/api/v1/tasks/__init__.py
from fastapi import APIRouter

# Імпортуємо роутери з файлів цього модуля
from .tasks import router as crud_tasks_router
from .events import router as events_router
from .assignments import router as task_assignments_router
from .completions import router as task_completions_router
from .reviews import router as task_reviews_router

# Створюємо агрегований роутер для всіх ендпоінтів, пов'язаних із задачами та подіями
tasks_router = APIRouter()

# Підключення роутера для CRUD операцій з задачами
# Його шляхи (напр. / та /{task_id}) будуть відносні до префіксу tasks_router (/tasks)
tasks_router.include_router(crud_tasks_router, tags=["Tasks Core"]) # Основні операції з задачами

# Підключення роутера для CRUD операцій з подіями
tasks_router.include_router(events_router, prefix="/events", tags=["Events Core"])

# Підключення роутера для призначень задач/подій
tasks_router.include_router(task_assignments_router, prefix="/assignments", tags=["Task/Event Assignments"])

# Підключення роутера для виконань задач/подій
tasks_router.include_router(task_completions_router, prefix="/completions", tags=["Task/Event Completions"])

# Підключення роутера для відгуків на задачі
tasks_router.include_router(task_reviews_router, prefix="/reviews", tags=["Task Reviews"])


# Експортуємо tasks_router для використання в головному v1_router (app/src/api/v1/router.py)
__all__ = ["tasks_router"]
