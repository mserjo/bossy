# backend/app/src/tasks/notifications/__init__.py
# -*- coding: utf-8 -*-
"""
Ініціалізаційний файл для пакету 'notifications' фонових завдань.

Цей пакет містить фонові завдання, пов'язані з відправкою сповіщень
різними каналами. Наприклад:
- `email.py`: Завдання для асинхронної відправки email сповіщень.
- `sms.py`: Завдання для асинхронної відправки SMS сповіщень.
- `messenger.py`: Завдання для асинхронної відправки сповіщень через месенджери
  (Telegram, Viber, Slack, Teams тощо).
- Можливо, завдання для надсилання push-сповіщень (Firebase Cloud Messaging, APNS).

Кожен файл зазвичай визначає одну або декілька функцій завдань
(наприклад, для Celery, декорованих `@celery_app.task`).

Цей файл робить каталог 'notifications' (в contexti tasks) пакетом Python.
Він може експортувати завдання для їх реєстрації в планувальнику
або для прямого виклику з сервісів сповіщень.
"""

# TODO: Імпортувати та експортувати конкретні функції завдань,
# коли вони будуть визначені у файлах цього пакету.

# Приклад експорту для Celery завдань:
# from .email import send_email_task, send_bulk_email_task
# from .sms import send_sms_task
# from .messenger import send_telegram_message_task, send_slack_message_task
# # from .push import send_fcm_push_notification_task
#
# __all__ = [
#     "send_email_task",
#     "send_bulk_email_task",
#     "send_sms_task",
#     "send_telegram_message_task",
#     "send_slack_message_task",
#     # "send_fcm_push_notification_task",
# ]

# На даний момент, поки завдання не визначені, файл може залишатися таким.
pass
