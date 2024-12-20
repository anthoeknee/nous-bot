from typing import Dict, TypeVar, Callable, Any

T = TypeVar("T")


class Factory:
    def __init__(self):
        self._creators: Dict[str, Callable[..., Any]] = {}

    def register(self, key: str, creator: Callable[..., T]) -> None:
        """Register a new creator function for the given key."""
        self._creators[key] = creator

    def create(self, key: str, *args, **kwargs) -> T:
        """Create an instance using the registered creator function."""
        creator = self._creators.get(key)
        if not creator:
            raise ValueError(f"No creator registered for key: {key}")
        return creator(*args, **kwargs)

    def unregister(self, key: str) -> None:
        """Remove a creator function from the registry."""
        self._creators.pop(key, None)
