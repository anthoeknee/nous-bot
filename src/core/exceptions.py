class NexusError(Exception):
    """Base exception for all application errors"""

    def __init__(self, message="A Nexus application error occurred", *args, **kwargs):
        self.message = message
        super().__init__(message, *args, **kwargs)

    def __str__(self):
        return f"{self.__class__.__name__}: {self.message}"


class ServiceError(NexusError):
    """Base exception for service-related errors"""

    def __init__(self, message="A service error occurred", *args, **kwargs):
        super().__init__(message, *args, **kwargs)


class DatabaseError(ServiceError):
    """Exception raised for database-related errors"""

    def __init__(self, message="A database error occurred", *args, **kwargs):
        super().__init__(message, *args, **kwargs)


class CacheError(ServiceError):
    """Exception raised for cache-related errors"""

    def __init__(self, message="A cache error occurred", *args, **kwargs):
        super().__init__(message, *args, **kwargs)


class ConfigError(NexusError):
    """Exception raised for configuration-related errors"""

    def __init__(self, message="A configuration error occurred", *args, **kwargs):
        super().__init__(message, *args, **kwargs)


class ValidationError(NexusError):
    """Exception raised for data validation errors"""

    def __init__(self, message="A validation error occurred", *args, **kwargs):
        super().__init__(message, *args, **kwargs)


class AuthenticationError(NexusError):
    """Exception raised for authentication-related errors"""

    def __init__(self, message="An authentication error occurred", *args, **kwargs):
        super().__init__(message, *args, **kwargs)


class AuthorizationError(NexusError):
    """Exception raised for authorization-related errors"""

    def __init__(self, message="An authorization error occurred", *args, **kwargs):
        super().__init__(message, *args, **kwargs)


class RateLimitError(NexusError):
    """Exception raised for rate limiting errors"""

    def __init__(self, message="A rate limit error occurred", *args, **kwargs):
        super().__init__(message, *args, **kwargs)


class ResourceNotFoundError(NexusError):
    """Exception raised when a requested resource is not found"""

    def __init__(self, message="Resource not found", *args, **kwargs):
        super().__init__(message, *args, **kwargs)


class ResourceConflictError(NexusError):
    """Exception raised when there's a conflict with existing resources"""

    def __init__(self, message="Resource conflict occurred", *args, **kwargs):
        super().__init__(message, *args, **kwargs)


class ExternalServiceError(NexusError):
    """Exception raised for external service integration errors"""

    def __init__(self, message="An external service error occurred", *args, **kwargs):
        super().__init__(message, *args, **kwargs)
