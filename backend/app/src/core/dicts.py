# backend/app/src/core/dicts.py
# -*- coding: utf-8 -*-
"""
Цей модуль призначений для визначення системних довідників, які не зберігаються
в базі даних, а є частиною коду, наприклад, у вигляді Enum-класів.
"""

from enum import Enum
from typing import List # Додано для типізації в методах Enum

# Імпорт констант для узгодження значень
from backend.app.src.core import constants

class NotificationChannelEnum(str, Enum):
    """Канали доставки сповіщень."""
    IN_APP = constants.NOTIFICATION_CHANNEL_IN_APP
    EMAIL = constants.NOTIFICATION_CHANNEL_EMAIL
    SMS = constants.NOTIFICATION_CHANNEL_SMS
    PUSH_FCM = constants.NOTIFICATION_CHANNEL_PUSH_FCM
    PUSH_APNS = constants.NOTIFICATION_CHANNEL_PUSH_APNS
    TELEGRAM_BOT = constants.NOTIFICATION_CHANNEL_TELEGRAM
    SLACK = constants.NOTIFICATION_CHANNEL_SLACK # Використовує константу NOTIFICATION_CHANNEL_SLACK

    @classmethod
    def get_email_channels(cls) -> List['NotificationChannelEnum']:
        return [cls.EMAIL]

class TransactionTypeEnum(str, Enum):
    """Типи фінансових транзакцій по бонусних рахунках."""
    TASK_REWARD = constants.TRANSACTION_TYPE_TASK_REWARD
    TASK_PENALTY = constants.TRANSACTION_TYPE_TASK_PENALTY
    REWARD_PURCHASE = constants.TRANSACTION_TYPE_REWARD_PURCHASE
    MANUAL_CREDIT = constants.TRANSACTION_TYPE_MANUAL_CREDIT
    MANUAL_DEBIT = constants.TRANSACTION_TYPE_MANUAL_DEBIT
    THANK_YOU_SENT = constants.TRANSACTION_TYPE_THANK_YOU_SENT
    THANK_YOU_RECEIVED = constants.TRANSACTION_TYPE_THANK_YOU_RECEIVED
    INITIAL_BALANCE = constants.TRANSACTION_TYPE_INITIAL_BALANCE
    PROPOSAL_BONUS = constants.TRANSACTION_TYPE_PROPOSAL_BONUS
    STREAK_BONUS = constants.TRANSACTION_TYPE_STREAK_BONUS # Використовує константу
    SYSTEM_ADJUSTMENT_CREDIT = constants.TRANSACTION_TYPE_SYSTEM_ADJUSTMENT_CREDIT # Використовує константу
    SYSTEM_ADJUSTMENT_DEBIT = constants.TRANSACTION_TYPE_SYSTEM_ADJUSTMENT_DEBIT # Використовує константу

class BadgeConditionTypeEnum(str, Enum):
    """Типи умов для отримання бейджів."""
    TASK_COUNT_TOTAL = constants.BADGE_CONDITION_TASK_COUNT_TOTAL # Використовує константу
    TASK_COUNT_TYPE = constants.BADGE_CONDITION_TASK_COUNT_TYPE   # Використовує константу
    TASK_STREAK = constants.BADGE_CONDITION_TASK_STREAK         # Використовує константу
    FIRST_TO_COMPLETE_TASK = constants.BADGE_CONDITION_FIRST_TO_COMPLETE_TASK # Використовує константу
    SPECIFIC_TASK_COMPLETED = constants.BADGE_CONDITION_SPECIFIC_TASK_COMPLETED # Використовує константу
    MANUAL_AWARD = constants.BADGE_CONDITION_MANUAL_AWARD        # Використовує константу
    CUSTOM_EVENT = constants.BADGE_CONDITION_CUSTOM_EVENT       # Використовує константу
    BONUS_POINTS_EARNED = constants.BADGE_CONDITION_BONUS_POINTS_EARNED # Використовує константу

class RatingTypeEnum(str, Enum):
    """Типи рейтингів користувачів."""
    BY_TASKS_COMPLETED_OVERALL = constants.RATING_TYPE_BY_TASKS_COMPLETED_OVERALL
    BY_BONUS_POINTS_EARNED_OVERALL = constants.RATING_TYPE_BY_BONUS_POINTS_EARNED_OVERALL
    BY_CURRENT_BALANCE = constants.RATING_TYPE_BY_CURRENT_BALANCE
    BY_TASKS_COMPLETED_PERIOD = constants.RATING_TYPE_BY_TASKS_COMPLETED_PERIOD
    BY_BONUS_POINTS_EARNED_PERIOD = constants.RATING_TYPE_BY_BONUS_POINTS_EARNED_PERIOD

class ReportCodeEnum(str, Enum):
    """Коди (типи) звітів, що генеруються системою."""
    USER_ACTIVITY = constants.REPORT_CODE_USER_ACTIVITY
    TASK_POPULARITY = constants.REPORT_CODE_TASK_POPULARITY
    REWARD_POPULARITY = constants.REPORT_CODE_REWARD_POPULARITY
    BONUS_DYNAMICS = constants.REPORT_CODE_BONUS_DYNAMICS
    INACTIVE_USERS = constants.REPORT_CODE_INACTIVE_USERS
    LAGGING_USERS = constants.REPORT_CODE_LAGGING_USERS
    GROUP_OVERVIEW = constants.REPORT_CODE_GROUP_OVERVIEW
    USER_PERSONAL_PROGRESS = constants.REPORT_CODE_USER_PERSONAL_PROGRESS
    ABANDONED_GROUPS = constants.REPORT_CODE_ABANDONED_GROUPS
    INACTIVE_GROUPS_REPORT = constants.REPORT_CODE_INACTIVE_GROUPS_REPORT

class NotificationTypeEnum(str, Enum):
    """Типи сповіщень."""
    TASK_COMPLETED_BY_USER = constants.NOTIFICATION_TYPE_TASK_COMPLETED
    TASK_STATUS_CHANGED_FOR_USER = constants.NOTIFICATION_TYPE_TASK_STATUS_CHANGED
    ACCOUNT_TRANSACTION = constants.NOTIFICATION_TYPE_ACCOUNT_TRANSACTION
    TASK_DEADLINE_REMINDER = constants.NOTIFICATION_TYPE_TASK_DEADLINE_REMINDER
    NEW_GROUP_INVITATION = constants.NOTIFICATION_TYPE_NEW_GROUP_INVITATION
    NEW_TASK_ASSIGNED = constants.NOTIFICATION_TYPE_NEW_TASK_ASSIGNED
    NEW_POLL_IN_GROUP = constants.NOTIFICATION_TYPE_NEW_POLL_IN_GROUP
    BIRTHDAY_GREETING = constants.NOTIFICATION_TYPE_BIRTHDAY_GREETING
    # Додати інші типи, якщо є в constants.py

class FileCategoryEnum(str, Enum):
    """Категорії файлів."""
    USER_AVATAR = constants.FILE_CATEGORY_USER_AVATAR
    GROUP_ICON = constants.FILE_CATEGORY_GROUP_ICON
    REWARD_ICON = constants.FILE_CATEGORY_REWARD_ICON
    BADGE_ICON = constants.FILE_CATEGORY_BADGE_ICON
    LEVEL_ICON = constants.FILE_CATEGORY_LEVEL_ICON
    TASK_ATTACHMENT = constants.FILE_CATEGORY_TASK_ATTACHMENT
    REPORT_FILE = constants.FILE_CATEGORY_REPORT_FILE

class TaskProposalStatusEnum(str, Enum):
    """Статуси пропозицій завдань."""
    PENDING_REVIEW = constants.TASK_PROPOSAL_STATUS_PENDING_CODE
    APPROVED = constants.TASK_PROPOSAL_STATUS_APPROVED_CODE
    REJECTED = constants.TASK_PROPOSAL_STATUS_REJECTED_CODE
    IMPLEMENTED = constants.TASK_PROPOSAL_STATUS_IMPLEMENTED_CODE

class NotificationDeliveryStatusEnum(str, Enum):
    """Статуси доставки сповіщень."""
    PENDING = constants.DELIVERY_STATUS_PENDING
    PROCESSING = constants.DELIVERY_STATUS_PROCESSING
    SENT = constants.DELIVERY_STATUS_SENT
    DELIVERED = constants.DELIVERY_STATUS_DELIVERED
    FAILED = constants.DELIVERY_STATUS_FAILED
    RETRYING = constants.DELIVERY_STATUS_RETRYING
    OPENED = constants.DELIVERY_STATUS_OPENED
    CLICKED = constants.DELIVERY_STATUS_CLICKED
    UNSUBSCRIBED = constants.DELIVERY_STATUS_UNSUBSCRIBED

class ReportStatusEnum(str, Enum):
    """Статуси генерації звітів."""
    QUEUED = constants.REPORT_STATUS_QUEUED
    PROCESSING = constants.REPORT_STATUS_PROCESSING
    COMPLETED = constants.REPORT_STATUS_COMPLETED
    FAILED = constants.REPORT_STATUS_FAILED
    CANCELLED = constants.REPORT_STATUS_CANCELLED

# Перевірка констант (деякі могли бути пропущені в constants.py або тут)
# Для RatingTypeEnum я додав використання констант, припускаючи, що вони є в constants.py.
# Якщо ні, їх треба буде додати в constants.py або залишити рядкові літерали тут.
#
# Узгодження TransactionTypeEnum з constants.py:
# STREAK_BONUS та SYSTEM_ADJUSTMENT_* тепер мають відповідні константи.
#
# Аналогічно для NotificationTypeEnum та FileCategoryEnum - значення взяті з відповідних констант.
#
# Все готово.
