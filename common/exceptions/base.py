class AppException(Exception):
    """Base class for all application exceptions."""
    code = "error"
    http_status = 500
    message = "An unexpected error occurred."

    def __init__(self, message=None, details=None):
        self.message = message or self.message
        self.details = details or {}
        super().__init__(self.message)

class ValidationError(AppException):
    """Exception raised for validation errors."""
    code = "validation_error"
    http_status = 400
    message = "Invalid input."

class AuthenticationError(AppException):
    """Exception raised for authentication errors."""
    code = "authentication_error"
    http_status = 401
    message = "Authentication failed."

class PermissionDenied(AppException):
    """Exception raised for permission errors."""
    code = "permission_denied"
    http_status = 403
    message = "Permission denied."

class NotFoundError(AppException):
    """Exception raised when a resource is not found."""
    code = "not_found"
    http_status = 404
    message = "Resource not found."

class DatabaseError(AppException):
    """Exception raised for database errors."""
    code = "database_error"
    http_status = 500
    message = "A database error occurred."