# backend/app/src/api/v1/tasks/reviews.py
# -*- coding: utf-8 -*-
"""
Ендпоінти для управління відгуками на завдання/події API v1.

Цей модуль надає API для:
- Створення користувачем відгуку (коментар, рейтинг) на завдання/подію.
- Перегляду відгуків для конкретного завдання/події.
- Можливо, оновлення/видалення власних відгуків (якщо дозволено).
- Можливо, модерації відгуків адміністратором.

Можливість залишати відгуки та їх видимість може налаштовуватися адміном групи.
"""

from fastapi import APIRouter, Depends, status
from typing import List
from backend.app.src.config.logging import get_logger
# TODO: Імпортувати схеми, сервіси, залежності.

logger = get_logger(__name__)
router = APIRouter()

# Шляхи будуть відносно /groups/{group_id}/tasks/{task_id}/reviews

@router.post(
    "", # Тобто /groups/{group_id}/tasks/{task_id}/reviews
    # response_model=TaskReviewSchema,
    status_code=status.HTTP_201_CREATED,
    tags=["Tasks", "Task Reviews"],
    summary="Залишити відгук на завдання/подію (заглушка)"
    # dependencies=[Depends(group_member_can_review_task)]
)
async def create_task_review(
    group_id: int,
    task_id: int,
    # review_data: TaskReviewCreateSchema, # (rating, comment)
    # current_user: UserModel = Depends(CurrentActiveUser)
):
    logger.info(f"Користувач (ID TODO) залишає відгук на завдання {task_id} (група {group_id}) (заглушка).")
    # TODO: Реалізувати логіку створення відгуку.
    # Перевірити, чи користувач може залишати відгук (напр. чи завдання завершене, чи він учасник).
    # Перевірити, чи налаштування групи дозволяють відгуки.
    return {"review_id": "rev_789", "task_id": task_id, "user_id": "TODO", "rating": 5, "comment": "Чудове завдання!"}

@router.get(
    "",
    # response_model=List[TaskReviewSchema],
    tags=["Tasks", "Task Reviews"],
    summary="Отримати список відгуків для завдання/події (заглушка)"
    # dependencies=[Depends(group_member_can_view_reviews)]
)
async def list_task_reviews(
    group_id: int,
    task_id: int,
):
    logger.info(f"Запит списку відгуків для завдання {task_id} (група {group_id}) (заглушка).")
    # TODO: Реалізувати логіку отримання списку відгуків.
    # Врахувати налаштування видимості відгуків.
    return [
        {"review_id": "rev_123", "user_id": 1, "username": "user1", "rating": 5, "comment": "Дуже сподобалось!"},
        {"review_id": "rev_456", "user_id": 2, "username": "user2", "rating": 4, "comment": "Нормально."}
    ]

@router.put(
    "/{review_id}",
    # response_model=TaskReviewSchema,
    tags=["Tasks", "Task Reviews"],
    summary="Оновити власний відгук (заглушка)"
    # dependencies=[Depends(is_review_author_or_admin)]
)
async def update_task_review(
    group_id: int,
    task_id: int,
    review_id: str, # Або int
    # review_update_data: TaskReviewUpdateSchema,
    # current_user: UserModel = Depends(CurrentActiveUser)
):
    logger.info(f"Користувач (ID TODO) оновлює відгук {review_id} для завдання {task_id} (група {group_id}) (заглушка).")
    # TODO: Реалізувати логіку оновлення відгуку. Перевірити права.
    return {"review_id": review_id, "message": "Відгук оновлено."}

@router.delete(
    "/{review_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Tasks", "Task Reviews"],
    summary="Видалити власний відгук або модерація (заглушка)"
    # dependencies=[Depends(is_review_author_or_admin)]
)
async def delete_task_review(
    group_id: int,
    task_id: int,
    review_id: str, # Або int
    # current_user: UserModel = Depends(CurrentActiveUser)
):
    logger.info(f"Користувач (ID TODO) видаляє відгук {review_id} для завдання {task_id} (група {group_id}) (заглушка).")
    # TODO: Реалізувати логіку видалення відгуку. Перевірити права.
    return

# Роутер буде підключений в backend/app/src/api/v1/tasks/__init__.py
