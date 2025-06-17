# backend/scripts/cleanup_temp_data.py
# -*- coding: utf-8 -*-
"""
Скрипт для очищення старих тимчасових файлів у вказаних директоріях.

Дозволяє видаляти файли, що відповідають певним шаблонам (patterns)
та є старшими за вказану кількість днів (max_age_days).
Підтримує режим "пробного запуску" (--dry-run) для перегляду файлів,
які будуть видалені, без фактичного видалення.
Також має опцію примусового видалення без підтвердження (--force).
"""
import os
import sys
import logging
import argparse
import glob
from datetime import datetime, timedelta, timezone
from typing import List

# Налаштування базового логування для скрипта
# Використовуємо стандартний логер, оскільки цей скрипт є утилітою командного рядка
# і може не мати доступу до конфігурації логування основного додатку.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Додавання шляху до батьківської директорії (backend), щоб дозволити імпорт з backend.app.src.*
# Це корисно, якщо, наприклад, DEFAULT_TARGET_DIRECTORIES потрібно брати з backend.app.src.core.settings
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)  # Директорія 'backend'
if BACKEND_DIR not in sys.path:
    sys.path.append(BACKEND_DIR)
    logger.debug(f"Додано '{BACKEND_DIR}' до sys.path для можливого імпорту модулів додатку.")

# TODO: Розглянути можливість завантаження цих значень з конфігураційного файлу додатка,
#       якщо скрипт буде тісно інтегрований з основним додатком.
#       Наприклад: from backend.app.src.core.settings import settings
#                 DEFAULT_TARGET_DIRECTORIES = settings.TEMP_DATA_CLEANUP_DIRS
DEFAULT_TARGET_DIRECTORIES: List[str] = [
    os.path.join(BACKEND_DIR, "temp_uploads"),  # Директорія для тимчасових завантажень (приклад)
    os.path.join(BACKEND_DIR, "logs", "archived_logs")  # Директорія для старих архівів логів (приклад)
]
DEFAULT_FILE_PATTERNS: List[str] = ["*.tmp", "*.temp", "*.bak", "*.old", "*.log.*.gz"]
DEFAULT_MAX_AGE_DAYS: int = 30  # Видаляти файли, старші за 30 днів


def _(text: str) -> str:
    """Базова функція-заглушка для інтернаціоналізації рядків."""
    # У реальному сценарії тут була б інтеграція з gettext або іншою i18n бібліотекою.
    return text


def confirm_action(prompt: str) -> bool:
    """
    Запитує підтвердження дії від користувача.

    Args:
        prompt: Повідомлення-запит для користувача.

    Returns:
        True, якщо користувач підтвердив дію ('так'), False в іншому випадку ('ні').
    """
    while True:
        try:
            # i18n: User confirmation prompt
            response = input(f"{prompt} [{_('так')}/{_('ні')}]: ").strip().lower()
        except KeyboardInterrupt:
            logger.warning(_("\nДію скасовано користувачем (Ctrl+C)."))  # i18n
            return False
        if response == _("так"):  # i18n
            return True
        elif response == _("ні"):  # i18n
            return False
        else:
            # i18n: Invalid input for confirmation
            # Використовуємо print замість logger.info для прямого відгуку користувачу на його введення
            print(_("Будь ласка, введіть 'так' або 'ні'."))


def cleanup_files(directories: List[str], patterns: List[str], max_age_days: int, dry_run: bool, force: bool):
    """
    Знаходить та видаляє старі тимчасові файли.

    Args:
        directories: Список шляхів до директорій для очищення.
        patterns: Список шаблонів імен файлів для пошуку (наприклад, `*.tmp`).
        max_age_days: Максимальний вік файлів у днях. Файли старші за цей вік будуть видалені.
        dry_run: Якщо True, файли лише перелічуються, але не видаляються.
        force: Якщо True, видалення відбувається без запиту на підтвердження (ігнорується, якщо `dry_run` True).
    """
    # i18n: Log message - Cleanup process started
    logger.info(_("Початок процесу очищення тимчасових даних."))
    if dry_run:
        # i18n: Log message - Dry run mode enabled
        logger.info(_("РЕЖИМ ПРОБНОГО ЗАПУСКУ (DRY RUN): Файли не будуть видалені."))

    cutoff_time = datetime.now(timezone.utc) - timedelta(days=max_age_days)
    # i18n: Log message - Cutoff time for file deletion
    logger.info(_("Видалятимуться файли, старші за: {cutoff_date} ({days} днів).").format(
        cutoff_date=cutoff_time.strftime('%Y-%m-%d %H:%M:%S %Z'),
        days=max_age_days
    ))

    files_to_delete: List[str] = []

    for directory in directories:
        if not os.path.isdir(directory):
            # i18n: Log message - Directory not found or not a directory
            logger.warning(
                _("Директорія '{directory}' не існує або не є директорією. Пропускаємо.").format(directory=directory))
            continue

        # i18n: Log message - Searching files in directory
        logger.info(_("Пошук файлів у директорії: '{directory}'").format(directory=directory))
        for pattern in patterns:
            # TODO: Додати опцію --recursive для рекурсивного пошуку в піддиректоріях.
            #       Для цього можна використовувати os.walk() або glob.glob() з `recursive=True`.
            search_path = os.path.join(directory, pattern)
            # Використовуємо glob.escape для екранування спеціальних символів у шляху, якщо вони можуть там бути.
            # Однак, тут pattern є glob-шаблоном, тому екранувати його не потрібно.
            for filepath in glob.glob(search_path):
                if os.path.isfile(filepath):  # Переконуємося, що це файл, а не директорія
                    try:
                        file_mod_time_ts = os.path.getmtime(filepath)
                        file_mod_time_dt = datetime.fromtimestamp(file_mod_time_ts, timezone.utc)

                        if file_mod_time_dt < cutoff_time:
                            files_to_delete.append(filepath)
                            logger.debug(
                                _("Знайдено файл для видалення: {filepath} (остання зміна: {mod_time})").format(
                                    filepath=filepath,
                                    mod_time=file_mod_time_dt.strftime('%Y-%m-%d %H:%M:%S %Z')
                                )
                            )
                    except Exception as e:
                        # i18n: Log message - Error getting file info
                        logger.error(
                            _("Не вдалося отримати інформацію про файл '{filepath}': {error}").format(filepath=filepath,
                                                                                                      error=e))

    if not files_to_delete:
        # i18n: Log message - No old files found
        logger.info(_("Старих тимчасових файлів для видалення не знайдено."))
        return

    # i18n: Log message - Found files to delete (count)
    logger.info(_("Знайдено {count} файлів для видалення:").format(count=len(files_to_delete)))
    for f_path in files_to_delete:
        logger.info(f"  - {f_path}")  # Шляхи до файлів не перекладаємо

    if dry_run:
        # i18n: Log message - Dry run finished
        logger.info(_("Завершено пробний запуск. Файли не видалено."))
        return

    # Запит на підтвердження, якщо не в режимі --force
    proceed_with_deletion = force  # Якщо force=True, то одразу proceed_with_deletion=True
    if not force:  # Якщо force=False, то питаємо користувача
        # i18n: User confirmation prompt for deletion
        proceed_with_deletion = confirm_action(
            _("Ви впевнені, що хочете видалити {count} файлів?").format(count=len(files_to_delete))
        )

    if proceed_with_deletion:
        deleted_count = 0
        error_count = 0
        for filepath in files_to_delete:
            try:
                os.remove(filepath)
                # i18n: Log message - File successfully deleted
                logger.info(_("Файл '{filepath}' успішно видалено.").format(filepath=filepath))
                deleted_count += 1
            except OSError as e:
                # i18n: Log message - Error deleting file
                logger.error(_("Не вдалося видалити файл '{filepath}': {error}").format(filepath=filepath, error=e))
                error_count += 1

        # i18n: Log message - Deletion process summary
        logger.info(_("Процес видалення завершено. Видалено файлів: {deleted_count}. Помилок: {error_count}.").format(
            deleted_count=deleted_count, error_count=error_count
        ))
    else:
        # i18n: Log message - Deletion cancelled by user
        logger.info(_("Видалення скасовано користувачем."))


def main():
    # i18n: Argparse description
    parser = argparse.ArgumentParser(description=_("Скрипт для очищення старих тимчасових файлів."))

    parser.add_argument(
        "--dirs",
        nargs='+',
        default=DEFAULT_TARGET_DIRECTORIES,
        # i18n: Argparse help for --dirs
        help=_("Список директорій для сканування (через пробіл). За замовчуванням: {default_dirs}").format(
            default_dirs=' '.join(DEFAULT_TARGET_DIRECTORIES))
    )
    parser.add_argument(
        "--patterns",
        nargs='+',
        default=DEFAULT_FILE_PATTERNS,
        # i18n: Argparse help for --patterns
        help=_(
            "Список шаблонів файлів для пошуку (наприклад, '*.tmp', '*.log.old'). За замовчуванням: {default_patterns}").format(
            default_patterns=' '.join(DEFAULT_FILE_PATTERNS))
    )
    parser.add_argument(
        "--max-age-days",
        type=int,
        default=DEFAULT_MAX_AGE_DAYS,
        # i18n: Argparse help for --max-age-days
        help=_(
            "Максимальний вік файлів у днях, які залишаться. Старші будуть видалені. За замовчуванням: {default_days} днів.").format(
            default_days=DEFAULT_MAX_AGE_DAYS)
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        # i18n: Argparse help for --dry-run
        help=_("Пробний запуск: показати, які файли будуть видалені, але не видаляти їх.")
    )
    parser.add_argument(
        "--force",
        action="store_true",
        # i18n: Argparse help for --force
        help=_("Пропустити запит на підтвердження перед видаленням (НЕ РЕКОМЕНДУЄТЬСЯ).")
    )
    # TODO: Додати аргумент --recursive для рекурсивного обходу директорій.

    args = parser.parse_args()

    # Якщо --force і --dry-run вказані одночасно, --dry-run має перевагу для безпеки.
    # Фактично, --force ігнорується, якщо --dry-run активний.
    is_dry_run_active = args.dry_run
    is_force_active = args.force and not is_dry_run_active  # --force активний тільки якщо не --dry-run

    if is_force_active:
        # i18n: Log warning - --force mode enabled
        logger.warning(_("Запуск у режимі --force: файли будуть видалені БЕЗ ПІДТВЕРДЖЕННЯ."))

    if args.dry_run and args.force:
        logger.info(_("Вказано --dry-run та --force. Виконується режим --dry-run (файли не будуть видалені)."))

    cleanup_files(
        directories=args.dirs,
        patterns=args.patterns,
        max_age_days=args.max_age_days,
        dry_run=is_dry_run_active,  # Передаємо актуальний стан dry_run
        force=is_force_active  # Передаємо актуальний стан force
    )

    # i18n: Log message - Script finished
    logger.info(_("Скрипт очищення тимчасових даних завершив роботу."))


if __name__ == "__main__":
    # Приклади запуску (з українськими коментарями):
    # # Пробний запуск, покаже, які файли будуть видалені, але не видалить їх
    # python backend/scripts/cleanup_temp_data.py --dry-run
    #
    # # Видалити файли старші за 7 днів, що відповідають шаблонам *.log та *.tmp
    # # у директоріях /tmp/app_logs та temp_data (шляхи відносні або абсолютні)
    # python backend/scripts/cleanup_temp_data.py --max-age-days 7 --patterns "*.log" "*.tmp" --dirs "/tmp/app_logs" "temp_data"
    #
    # # Примусове видалення файлів старших за 30 днів (за замовчуванням) БЕЗ ПІДТВЕРДЖЕННЯ (НЕБЕЗПЕЧНО!)
    # python backend/scripts/cleanup_temp_data.py --force
    main()
