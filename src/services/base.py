from typing import Any, Dict, Optional
import logging
import asyncio
from datetime import datetime
from contextlib import asynccontextmanager

from .interface import ServiceInterface, ServiceStatus


class BaseService(ServiceInterface):
    """Enhanced base implementation for services"""

    def __init__(self, name: str):
        self._name = name
        self._status = ServiceStatus.UNINITIALIZED
        self._last_error: Optional[Exception] = None
        self._start_time: Optional[datetime] = None
        self._logger = logging.getLogger(f"service.{name}")
        self._lock = asyncio.Lock()
        self._health_check_interval = 30  # seconds
        self._health_check_task: Optional[asyncio.Task] = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def status(self) -> ServiceStatus:
        return self._status

    @property
    def uptime(self) -> Optional[float]:
        """Return service uptime in seconds"""
        if self._start_time and self.status == ServiceStatus.RUNNING:
            return (datetime.now() - self._start_time).total_seconds()
        return None

    async def initialize(self, **kwargs) -> None:
        async with self._lock:
            if self._status != ServiceStatus.UNINITIALIZED:
                return

            try:
                self._status = ServiceStatus.INITIALIZING
                await self._initialize(**kwargs)
                self._status = ServiceStatus.INITIALIZED
                self._logger.info(f"Service '{self.name}' initialized successfully")
            except Exception as e:
                self._status = ServiceStatus.ERROR
                self._last_error = e
                self._logger.error(f"Failed to initialize service '{self.name}': {e}")
                raise

    async def start(self) -> None:
        async with self._lock:
            if self._status != ServiceStatus.INITIALIZED:
                raise RuntimeError(
                    f"Service '{self.name}' must be initialized before starting"
                )

            try:
                self._status = ServiceStatus.STARTING
                await self._start()
                self._status = ServiceStatus.RUNNING
                self._start_time = datetime.now()
                self._start_health_check()
                self._logger.info(f"Service '{self.name}' started successfully")
            except Exception as e:
                self._status = ServiceStatus.ERROR
                self._last_error = e
                self._logger.error(f"Failed to start service '{self.name}': {e}")
                raise

    async def stop(self) -> None:
        async with self._lock:
            if self._status != ServiceStatus.RUNNING:
                return

            try:
                self._status = ServiceStatus.STOPPING
                self._stop_health_check()
                await self._stop()
                self._status = ServiceStatus.STOPPED
                self._start_time = None
                self._logger.info(f"Service '{self.name}' stopped successfully")
            except Exception as e:
                self._status = ServiceStatus.ERROR
                self._last_error = e
                self._logger.error(f"Failed to stop service '{self.name}': {e}")
                raise

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check and return status information"""
        health_info = {
            "name": self.name,
            "status": self.status.value,
            "uptime": self.uptime,
            "last_error": str(self._last_error) if self._last_error else None,
            "details": await self._health_check(),
        }
        return health_info

    async def cleanup(self) -> None:
        """Cleanup service resources"""
        try:
            await self.stop()
            await self._cleanup()
            self._logger.info(f"Service '{self.name}' cleaned up successfully")
        except Exception as e:
            self._logger.error(f"Failed to cleanup service '{self.name}': {e}")
            raise

    @asynccontextmanager
    async def session(self):
        """Context manager for service sessions"""
        if self.status != ServiceStatus.RUNNING:
            raise RuntimeError(f"Service '{self.name}' is not running")
        try:
            yield self
        except Exception as e:
            self._logger.error(f"Error in service session: {e}")
            raise

    def _start_health_check(self) -> None:
        """Start periodic health check"""

        async def health_check_loop():
            while True:
                try:
                    await self.health_check()
                    await asyncio.sleep(self._health_check_interval)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self._logger.error(f"Health check failed: {e}")

        self._health_check_task = asyncio.create_task(health_check_loop())

    def _stop_health_check(self) -> None:
        """Stop periodic health check"""
        if self._health_check_task:
            self._health_check_task.cancel()

    # Methods to be implemented by subclasses
    async def _initialize(self, **kwargs) -> None:
        """Internal initialization implementation"""
        pass

    async def _start(self) -> None:
        """Internal start implementation"""
        pass

    async def _stop(self) -> None:
        """Internal stop implementation"""
        pass

    async def _cleanup(self) -> None:
        """Internal cleanup implementation"""
        pass

    async def _health_check(self) -> Dict[str, Any]:
        """Internal health check implementation"""
        return {}
