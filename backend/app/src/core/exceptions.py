# backend/app/src/core/exceptions.py

"""
This module defines custom exception classes for the application.
These exceptions can be raised by services or other parts of the application
and then handled by FastAPI exception handlers to return appropriate HTTP responses.
"""

from typing import Optional, Dict, Any, List

class AppException(Exception):
    """
    Base class for custom application exceptions.

    Attributes:
        message (str): The error message associated with the exception.
        status_code (int): The HTTP status code to be returned to the client.
        detail (Optional[Any]): Additional details or structured error information.
    """
    def __init__(self, message: str, status_code: int = 500, detail: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.detail = detail if detail is not None else message

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(status_code={self.status_code}, message='{self.message}', detail='{self.detail}')"

# --- Specific Application Exceptions ---

class RecordNotFoundException(AppException):
    """Raised when a requested record is not found in the database."""
    def __init__(self, entity_name: str, identifier: Any, message: Optional[str] = None, detail: Optional[Any] = None):
        resolved_message = message or f"{entity_name} with identifier '{identifier}' not found."
        super().__init__(message=resolved_message, status_code=404, detail=detail)
        self.entity_name = entity_name
        self.identifier = identifier

class DuplicateRecordException(AppException):
    """Raised when attempting to create a record that already exists (violates uniqueness)."""
    def __init__(self, entity_name: str, identifier: Any, message: Optional[str] = None, detail: Optional[Any] = None):
        resolved_message = message or f"{entity_name} with identifier '{identifier}' already exists."
        super().__init__(message=resolved_message, status_code=409, detail=detail) # 409 Conflict
        self.entity_name = entity_name
        self.identifier = identifier

class AuthenticationException(AppException):
    """Raised for authentication failures (e.g., invalid credentials, bad token)."""
    def __init__(self, message: str = "Authentication failed.", detail: Optional[Any] = None, status_code: int = 401):
        super().__init__(message=message, status_code=status_code, detail=detail)

class AuthorizationException(AppException):
    """Raised when an authenticated user is not authorized to perform an action."""
    def __init__(self, message: str = "You are not authorized to perform this action.", detail: Optional[Any] = None, status_code: int = 403):
        super().__init__(message=message, status_code=status_code, detail=detail)

class ValidationException(AppException):
    """
    Raised when input data fails validation checks (e.g., Pydantic validation errors).
    The `errors` attribute can hold detailed validation error information.
    """
    def __init__(self, message: str = "Input validation failed.", errors: Optional[List[Dict[str, Any]]] = None, detail: Optional[Any] = None):
        super().__init__(message=message, status_code=422, detail=detail) # 422 Unprocessable Entity
        self.errors = errors # List of Pydantic-like error dicts

class BusinessLogicException(AppException):
    """
    Raised for general business logic errors that don't fit other categories.
    For example, trying to perform an action on an entity in an invalid state.
    """
    def __init__(self, message: str, detail: Optional[Any] = None, status_code: int = 400):
        super().__init__(message=message, status_code=status_code, detail=detail)

class ExternalServiceException(AppException):
    """Raised when an error occurs while interacting with an external service."""
    def __init__(self, service_name: str, message: str = "Error interacting with external service.", detail: Optional[Any] = None, status_code: int = 503):
        full_message = f"{message} (Service: {service_name})"
        super().__init__(message=full_message, status_code=status_code, detail=detail) # 503 Service Unavailable
        self.service_name = service_name

class RateLimitExceededException(AppException):
    """Raised when a user exceeds their request rate limit."""
    def __init__(self, message: str = "Rate limit exceeded. Please try again later.", detail: Optional[Any] = None, status_code: int = 429):
        super().__init__(message=message, status_code=status_code, detail=detail) # 429 Too Many Requests

class FileProcessingException(AppException):
    """Raised for errors during file uploads or processing."""
    def __init__(self, message: str = "Error processing file.", detail: Optional[Any] = None, status_code: int = 400):
        super().__init__(message=message, status_code=status_code, detail=detail)

# It's good practice to have a generic ServiceException if you have a clear service layer concept
# class ServiceException(AppException):
#     """Base exception for service layer specific errors."""
#     def __init__(self, message: str, detail: Optional[Any] = None, status_code: int = 500):
#         super().__init__(message, status_code=status_code, detail=detail)


if __name__ == "__main__":
    print("--- Core Custom Exceptions ---")

    def demonstrate_exception(exc_class, *args, **kwargs):
        try:
            raise exc_class(*args, **kwargs)
        except AppException as e:
            print(f"Caught: {e}")
            if hasattr(e, 'entity_name'):
                print(f"  Entity: {e.entity_name}, Identifier: {e.identifier}")
            if hasattr(e, 'errors') and e.errors:
                print(f"  Errors: {e.errors}")
            if hasattr(e, 'service_name'):
                print(f"  Service Name: {e.service_name}")

    demonstrate_exception(AppException, "A generic app error occurred.")
    demonstrate_exception(RecordNotFoundException, "User", "123")
    demonstrate_exception(RecordNotFoundException, "Product", "xyz", message="Custom message: Product xyz not available.")
    demonstrate_exception(DuplicateRecordException, "Email", "test@example.com")
    demonstrate_exception(AuthenticationException, "Invalid API key provided.")
    demonstrate_exception(AuthorizationException, "User does not have permission to delete this resource.")

    validation_errors_example = [
        {"loc": ("body", "email"), "msg": "value is not a valid email address", "type": "value_error.email"},
        {"loc": ("body", "password"), "msg": "ensure this value has at least 8 characters", "type": "value_error.too_short"}
    ]
    demonstrate_exception(ValidationException, "User registration data is invalid.", errors=validation_errors_example)
    demonstrate_exception(ValidationException, detail={"field": "custom_error_detail"})

    demonstrate_exception(BusinessLogicException, "Cannot deactivate account with outstanding balance.")
    demonstrate_exception(ExternalServiceException, "PaymentGateway", "Transaction timed out.")
    demonstrate_exception(RateLimitExceededException)
    demonstrate_exception(FileProcessingException, "Uploaded file type not supported.")

    # Example of how status_code might be used in a web framework context
    try:
        raise AuthorizationException()
    except AppException as e:
        http_response_status = e.status_code
        http_response_body = {"error": e.message, "detail": e.detail}
        print(f"\nSimulated HTTP Response:")
        print(f"  Status: {http_response_status}")
        print(f"  Body: {http_response_body}")
