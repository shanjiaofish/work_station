class BaseAppException(Exception):
    """Base exception class for application"""
    def __init__(self, message, status_code=500, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload

class ValidationError(BaseAppException):
    """Raised when input validation fails"""
    def __init__(self, message, payload=None):
        super().__init__(message, 400, payload)

class NotFoundError(BaseAppException):
    """Raised when resource is not found"""
    def __init__(self, message="Resource not found", payload=None):
        super().__init__(message, 404, payload)

class DatabaseError(BaseAppException):
    """Raised when database operation fails"""
    def __init__(self, message="Database operation failed", payload=None):
        super().__init__(message, 500, payload)

class ExternalAPIError(BaseAppException):
    """Raised when external API call fails"""
    def __init__(self, message="External API call failed", payload=None):
        super().__init__(message, 502, payload)

class FileProcessingError(BaseAppException):
    """Raised when file processing fails"""
    def __init__(self, message="File processing failed", payload=None):
        super().__init__(message, 422, payload)