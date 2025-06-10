# backend/app/src/utils/converters.py

"""
Utility functions for converting data between different types or formats.
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
    Converts a Markdown formatted string to HTML.
    Requires the 'markdown' library to be installed.
    If the library is not installed or input is None, it returns the original text
    or an empty string for None input.

    Args:
        markdown_text: The string containing Markdown formatted text. Can be None.

    Returns:
        The HTML representation of the Markdown text, or the original text if
        markdown library is unavailable, or an empty string if input is None.
    """
    if markdown_text is None:
        return ""

    if markdown:
        try:
            extensions = ['fenced_code', 'tables', 'extra']
            html = markdown.markdown(markdown_text, extensions=extensions)
            logger.debug(f"Converted markdown text (length {len(markdown_text)}) to HTML (length {len(html)}).")
            return html
        except Exception as e:
            logger.error(f"Error converting Markdown to HTML: {e}", exc_info=True)
            return markdown_text
    else:
        logger.warning("Markdown library is not installed. Cannot convert Markdown to HTML. Returning original text.")
        return markdown_text

if __name__ == "__main__":
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("--- Data Conversion Utilities --- Demonstration")

    logger.info("\n--- Markdown to HTML Conversion ---")
    md_text1 = "**Hello** `World`!\n\n- Item 1\n- Item 2\n\n[Google](https://google.com)"
    html1 = markdown_to_html(md_text1)
    logger.info(f"Markdown:\n{md_text1}\nHTML:\n{html1}\n")

    md_text2 = "```python\ndef hello():\n  print('Hello')\n```"
    html2 = markdown_to_html(md_text2)
    logger.info(f"Markdown (Code Block):\n{md_text2}\nHTML:\n{html2}\n")

    md_text_table = """
| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |
| Cell 3   | Cell 4   |
"""
    html_table = markdown_to_html(md_text_table)
    logger.info(f"Markdown (Table):\n{md_text_table}\nHTML:\n{html_table}\n")

    md_none = None
    html_none = markdown_to_html(md_none)
    logger.info(f"Markdown (None input):\n{md_none}\nHTML:\n'{html_none}' (Expected: '')\n")
    assert html_none == ""

    if not markdown:
        logger.warning("Markdown library not installed, so HTML conversion tests are showing fallback behavior.")
    else:
        assert "<strong" in html1
        assert "<pre><code" in html2
        assert "<table" in html_table
