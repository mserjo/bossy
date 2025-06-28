# backend/app/src/tasks/integrations/__init__.py
# -*- coding: utf-8 -*-
"""
Ініціалізаційний файл для пакету 'integrations' фонових завдань.

Цей пакет містить фонові завдання, пов'язані з обробкою та синхронізацією
даних з зовнішніми інтеграціями. Наприклад:
- `calendar.py`: Завдання для періодичної синхронізації з календарями
  (Google Calendar, Outlook Calendar).
- `messenger.py`: Завдання для обробки вхідних повідомлень або інших
  асинхронних операцій з месенджерами.
- `tracker.py`: Завдання для періодичної синхронізації з таск-трекерами
  (Jira, Trello).

Кожен файл зазвичай визначає одну або декілька функцій завдань.

Цей файл робить каталог 'integrations' (в contexti tasks) пакетом Python.
Він може експортувати завдання для їх реєстрації в планувальнику
або для прямого виклику з сервісів інтеграцій.
"""

# TODO: Імпортувати та експортувати конкретні функції завдань,
# коли вони будуть визначені у файлах цього пакету.

# Приклад експорту для Celery завдань:
# from .calendar import sync_google_calendar_task, sync_outlook_calendar_task
# from .messenger import process_incoming_telegram_message_task
# from .tracker import sync_jira_issues_task, sync_trello_cards_task
#
# __all__ = [
#     "sync_google_calendar_task",
#     "sync_outlook_calendar_task",
#     "process_incoming_telegram_message_task",
#     "sync_jira_issues_task",
#     "sync_trello_cards_task",
# ]

# На даний момент, поки завдання не визначені, файл може залишатися таким.
pass
