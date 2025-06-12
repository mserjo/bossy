# backend/app/src/utils/converters.py
# -*- coding: utf-8 -*-
"""
Модуль конвертерів даних.

Цей модуль надає функції для перетворення даних між різними типами або форматами.
Наприклад, конвертація тексту у форматі Markdown в HTML.
"""
import logging
from typing import Optional, Any, List, Dict

try:
    import markdown
except ImportError:
    markdown = None # type: ignore

logger = logging.getLogger(__name__)

def markdown_to_html(markdown_text: Optional[str]) -> str:
    """
    Конвертує рядок у форматі Markdown в HTML.
    Потребує встановленої бібліотеки 'markdown'.
    Якщо бібліотека не встановлена або вхідні дані None, повертає оригінальний текст
    або порожній рядок для None входу.

    Args:
        markdown_text: Рядок, що містить текст у форматі Markdown. Може бути None.

    Returns:
        HTML-представлення тексту Markdown, або оригінальний текст, якщо
        бібліотека markdown недоступна, або порожній рядок, якщо вхідні дані None.
    """
    if markdown_text is None:
        return ""

    if markdown:
        try:
            extensions = ['fenced_code', 'tables', 'extra']
            html = markdown.markdown(markdown_text, extensions=extensions)
            logger.debug(f"Конвертовано Markdown текст (довжина {len(markdown_text)}) в HTML (довжина {len(html)}).")
            return html
        except Exception as e:
            logger.error(f"Помилка конвертації Markdown в HTML: {e}", exc_info=True)
            return markdown_text
    else:
        logger.warning("Бібліотека Markdown не встановлена. Неможливо конвертувати Markdown в HTML. Повертається оригінальний текст.")
        return markdown_text

if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- Демонстрація утиліт для конвертації даних ---")

    logger.info("\n--- Конвертація Markdown в HTML ---")
    md_text1 = "**Привіт** `Світ`!\n\n- Елемент 1\n- Елемент 2\n\n[Google](https://google.com)"
    html1 = markdown_to_html(md_text1)
    logger.info(f"Markdown:\n{md_text1}\nHTML:\n{html1}\n")

    md_text2 = "```python\ndef привіт():\n  print('Привіт')\n```"
    html2 = markdown_to_html(md_text2)
    logger.info(f"Markdown (Блок коду):\n{md_text2}\nHTML:\n{html2}\n")

    md_text_table = """
| Заголовок 1 | Заголовок 2 |
|-------------|-------------|
| Комірка 1   | Комірка 2   |
| Комірка 3   | Комірка 4   |
"""
    html_table = markdown_to_html(md_text_table)
    logger.info(f"Markdown (Таблиця):\n{md_text_table}\nHTML:\n{html_table}\n")

    md_none = None
    html_none = markdown_to_html(md_none)
    logger.info(f"Markdown (Вхід None):\n{md_none}\nHTML:\n'{html_none}' (Очікується: '')\n")
    assert html_none == ""

    if not markdown:
        logger.warning("Бібліотека Markdown не встановлена, тому тести конвертації HTML показують резервну поведінку.")
    else:
        assert "<strong" in html1
        assert "<pre><code" in html2  # TODO: Перевірити чи локалізація тексту не вплине на цей assert
        assert "<table" in html_table # TODO: Перевірити чи локалізація тексту не вплине на цей assert
