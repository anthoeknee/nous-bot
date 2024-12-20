class NexusError(Exception):
    """Base exception for all application errors"""

    pass


class ServiceError(NexusError):
    """Base exception for service-related errors"""

    pass


class DatabaseError(ServiceError):
    """Exception raised for database-related errors"""

    pass


class CacheError(ServiceError):
    """Exception raised for cache-related errors"""

    pass


class ConfigError(NexusError):
    """Exception raised for configuration-related errors"""

    pass


class ValidationError(NexusError):
    """Exception raised for data validation errors"""

    pass


class AuthenticationError(NexusError):
    """Exception raised for authentication-related errors"""

    pass


class AuthorizationError(NexusError):
    """Exception raised for authorization-related errors"""

    pass


class RateLimitError(NexusError):
    """Exception raised for rate limiting errors"""

    pass


class ResourceNotFoundError(NexusError):
    """Exception raised when a requested resource is not found"""

    pass


class ResourceConflictError(NexusError):
    """Exception raised when there's a conflict with existing resources"""

    pass


class ExternalServiceError(NexusError):
    """Exception raised for external service integration errors"""

    pass
