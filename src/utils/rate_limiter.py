import time
from typing import Callable, Any
from functools import wraps


class RateLimiter:
    def __init__(
        self,
        max_calls: int,
        time_window: float,
        backoff_factor: float = 2.0,
        max_retries: int = 3,
    ):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
        self.backoff_factor = backoff_factor
        self.max_retries = max_retries

    def _clean_old_calls(self) -> None:
        """Remove calls outside the time window."""
        current_time = time.time()
        self.calls = [t for t in self.calls if current_time - t < self.time_window]

    def wait_if_needed(self) -> None:
        """Wait if rate limit is exceeded."""
        self._clean_old_calls()
        if len(self.calls) >= self.max_calls:
            sleep_time = self.calls[0] + self.time_window - time.time()
            if sleep_time > 0:
                time.sleep(sleep_time)
            self._clean_old_calls()
        self.calls.append(time.time())

    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            retry_count = 0
            while retry_count <= self.max_retries:
                try:
                    self.wait_if_needed()
                    return func(*args, **kwargs)
                except Exception as e:
                    if retry_count == self.max_retries:
                        raise e
                    retry_count += 1
                    time.sleep(self.backoff_factor**retry_count)
            return None

        return wrapper
