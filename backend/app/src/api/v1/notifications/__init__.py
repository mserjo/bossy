# backend/app/src/api/v1/notifications/__init__.py
from fastapi import APIRouter

# Імпортуємо роутери з файлів цього модуля
from .notifications import router as user_notifications_router
from .templates import router as notification_templates_router
from .delivery import router as notification_delivery_router

# Створюємо агрегований роутер для всіх ендпоінтів, пов'язаних із системою сповіщень
notifications_router = APIRouter()

# Підключення роутера для сповіщень користувача (перегляд, позначення як прочитані)
# Його шляхи (напр. / та /{notification_id}) будуть відносні до префіксу notifications_router (/notifications)
notifications_router.include_router(user_notifications_router, tags=["User Notifications"])

# Підключення роутера для шаблонів сповіщень (керування адміном)
notifications_router.include_router(notification_templates_router, prefix="/templates", tags=["Notification Templates (Admin)"])

# Підключення роутера для статусів доставки сповіщень (перегляд адміном)
notifications_router.include_router(notification_delivery_router, prefix="/delivery", tags=["Notification Delivery Status (Admin)"])


# Експортуємо notifications_router для використання в головному v1_router (app/src/api/v1/router.py)
__all__ = ["notifications_router"]
