# backend/app/src/core/middleware/i18n_middleware.py
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from typing import List, Optional, Callable, Awaitable # Додано Callable, Awaitable

from backend.app.src.core.i18n import current_request_language
from backend.app.src.config.logging import get_logger
logger = get_logger(__name__)

SUPPORTED_LANGUAGES: List[str] = ["uk", "en"]
DEFAULT_LANGUAGE: str = "uk"

class LanguageMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        lang_code = DEFAULT_LANGUAGE

        accept_language_header: Optional[str] = request.headers.get("Accept-Language")

        if accept_language_header:
            languages = [lang.split(';')[0].strip() for lang in accept_language_header.split(',')]
            for lang in languages:
                main_lang_part = lang.split('-')[0].lower()
                if main_lang_part in SUPPORTED_LANGUAGES:
                    lang_code = main_lang_part
                    logger.debug(f"Language selected from Accept-Language header: {lang_code} (from {lang})")
                    break
            else:
                logger.debug(f"No supported language found in Accept-Language header ('{accept_language_header}'). Using default: {DEFAULT_LANGUAGE}")
        else:
            logger.debug(f"Accept-Language header not found. Using default language: {DEFAULT_LANGUAGE}")

        token = current_request_language.set(lang_code)
        try:
            response = await call_next(request)
        finally:
            current_request_language.reset(token)

        response.headers["Content-Language"] = lang_code
        return response

if __name__ == "__main__":
    # Example of how the parsing works (for testing the middleware logic directly)
    print(f"Supported: {SUPPORTED_LANGUAGES}, Default: {DEFAULT_LANGUAGE}")

    test_headers = [
        "uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7",
        "en-GB,en;q=0.9",
        "fr-CH, fr;q=0.9, en;q=0.8, de;q=0.7, *;q=0.5",
        "es",
        None,
        "invalid-lang, en",
        "uk,en",
        "en,uk"
    ]

    for header_val in test_headers:
        selected = DEFAULT_LANGUAGE
        if header_val:
            langs = [lang.split(';')[0].strip() for lang in header_val.split(',')]
            for lang_item in langs:
                main_part = lang_item.split('-')[0].lower()
                if main_part in SUPPORTED_LANGUAGES:
                    selected = main_part
                    break
        print(f"Header: '{header_val}' -> Selected: '{selected}'")
