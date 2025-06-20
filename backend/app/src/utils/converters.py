# backend/app/src/utils/converters.py
# -*- coding: utf-8 -*-
"""Модуль конвертерів даних.

Цей модуль надає функції для перетворення даних між різними типами або форматами.
Наприклад, сюди може входити конвертація тексту у форматі Markdown в HTML,
числових значень у різні системи числення, або перетворення структур даних.
"""
import logging # Імпортуємо logging для локального використання в __main__
from typing import Optional

from backend.app.src.config.logging import setup_logging
logger = setup_logging()

# Спроба імпортувати бібліотеку markdown.
# Якщо вона не встановлена, markdown буде None, і функція конвертації
# матиме резервну поведінку.
try:
    import markdown
except ImportError:
    markdown = None  # type: ignore
    logger.info("Бібліотека 'markdown' не встановлена. Функція markdown_to_html матиме обмежену функціональність.")


def markdown_to_html(markdown_text: Optional[str]) -> str:
    """Конвертує рядок у форматі Markdown в HTML.

    Потребує встановленої бібліотеки `markdown`.
    Якщо бібліотека `markdown` не встановлена або вхідний `markdown_text` є `None`,
    функція повертає порожній рядок для `None` або оригінальний текст,
    якщо бібліотека недоступна.

    Використовує розширення `fenced_code` (для блоків коду ```), `tables` (для таблиць),
    та `extra` (включає абревіатури, атрибути для елементів, виноски тощо).

    Args:
        markdown_text: Рядок, що містить текст у форматі Markdown. Може бути `None`.

    Returns:
        Рядок у форматі HTML, що є результатом конвертації.
        Повертає порожній рядок, якщо `markdown_text` є `None`.
        Повертає оригінальний `markdown_text`, якщо бібліотека `markdown` недоступна.
    """
    if markdown_text is None:
        logger.debug("Вхідний текст для markdown_to_html є None, повертається порожній рядок.")
        return ""

    if markdown:
        try:
            # Список розширень для Markdown для підтримки популярних функцій
            extensions = ['fenced_code', 'tables', 'extra']
            html: str = markdown.markdown(markdown_text, extensions=extensions)
            logger.debug("Конвертовано Markdown текст (довжина: %d) в HTML (довжина: %d).", len(markdown_text), len(html))
            return html
        except Exception as e:
            logger.error("Помилка під час конвертації Markdown в HTML: %s", e, exc_info=True)
            # У випадку помилки повертаємо оригінальний текст, щоб уникнути втрати даних
            return markdown_text
    else:
        logger.warning(
            "Бібліотека 'markdown' не встановлена. "
            "Неможливо конвертувати Markdown в HTML. Повертається оригінальний текст."
        )
        return markdown_text

# Блок для демонстрації та базового тестування функцій модуля,
# виконується тільки при прямому запуску файлу.
if __name__ == "__main__":
    # Налаштування базового логування для демонстрації, якщо ще не налаштовано.
    # Це не впливає на логування в основному додатку, яке керується централізованою конфігурацією.
    if not logging.getLogger().hasHandlers(): # Перевіряємо, чи є вже обробники у кореневого логера
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    # Використовуємо логер модуля для повідомлень в __main__
    main_logger = logging.getLogger(__name__) # Отримуємо логер для __main__ контексту
    main_logger.info("--- Демонстрація утиліт для конвертації даних ---")

    main_logger.info("\n--- Конвертація Markdown в HTML ---")
    md_text1 = "**Привіт** `Світ`!\n\n- Елемент 1\n- Елемент 2\n\n[Google](https://google.com)"
    html1 = markdown_to_html(md_text1)
    main_logger.info("Markdown:\n%s\nHTML:\n%s\n", md_text1, html1)

    md_text2 = "```python\ndef привіт():\n  print('Привіт')\n```"
    html2 = markdown_to_html(md_text2)
    main_logger.info("Markdown (Блок коду):\n%s\nHTML:\n%s\n", md_text_2, html2)

    md_text_table = """
| Заголовок 1 | Заголовок 2 |
|-------------|-------------|
| Комірка 1   | Комірка 2   |
| Комірка 3   | Комірка 4   |
"""
    html_table = markdown_to_html(md_text_table)
    main_logger.info("Markdown (Таблиця):\n%s\nHTML:\n%s\n", md_text_table, html_table)

    md_none = None
    html_none = markdown_to_html(md_none)
    main_logger.info("Markdown (Вхід None):\n%s\nHTML:\n'%s' (Очікується: '')\n", md_none, html_none)
    assert html_none == "", f"Очікувався порожній рядок для None входу, отримано: '{html_none}'"

    if not markdown:
        main_logger.warning(
            "Бібліотека Markdown не встановлена, тому тести конвертації HTML "
            "показують резервну поведінку (повернення оригінального тексту)."
        )
    else:
        assert "<strong" in html1, "Тег <strong> не знайдено в HTML."
        # Наявність тегів <pre><code> не залежить від локалізації тексту всередині них.
        assert "<pre><code" in html2, "Теги <pre><code> для блоку коду не знайдено в HTML."
        # Наявність тегу <table> не залежить від локалізації тексту всередині таблиці.
        assert "<table" in html_table, "Тег <table> не знайдено в HTML."
        main_logger.info("Базові перевірки HTML пройдені успішно.")
