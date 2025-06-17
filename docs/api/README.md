# API Документація

Цей розділ містить детальну інформацію про API системи Kudos.

## Розділи
- [OpenAPI Специфікація](./openapi.json) (буде згенеровано автоматично)
- [Postman Колекції](./postman/README.md)
- [Swagger UI](./swagger/README.md) (зазвичай доступно через /docs або /redoc в запущеному додатку)

## Language Support / Локалізація

The API supports responses in multiple languages. Currently supported languages are:
-   English (`en`)
-   Ukrainian (`uk`) - Default

### Language Negotiation

The language of API responses, particularly for error messages and schema descriptions (as visible in tools like Swagger UI), is determined by the `Accept-Language` HTTP header sent with your request.

If the `Accept-Language` header is not provided, or if none of the requested languages are supported, the API will respond in the default language, which is Ukrainian (`uk`).

**Examples:**

*   To request responses in Ukrainian:
    ```
    Accept-Language: uk
    ```
*   To request responses in English:
    ```
    Accept-Language: en
    ```
*   To specify language preference with quality factors (e.g., Ukrainian preferred, then English as fallback):
    ```
    Accept-Language: uk-UA, uk;q=0.9, en-US;q=0.8, en;q=0.7
    ```

The API will attempt to honor the highest priority supported language from your `Accept-Language` header. The chosen language will also be indicated in the `Content-Language` header of the response.
