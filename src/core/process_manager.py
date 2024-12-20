import os
import sys
import time
import importlib
from typing import Dict, Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from src.utils import ColorLogger
from src.core.config import settings

logger = ColorLogger("ProcessManager", settings.log_level)


class ModuleReloader(FileSystemEventHandler):
    def __init__(self, src_path: str):
        self.src_path = src_path
        self.last_reload: Dict[str, float] = {}
        self.reload_cooldown = 1.0  # Seconds
        self.skip_patterns = {
            "__pycache__",
            ".pyc$",
            ".pyo$",
            ".pyd$",
            "process_manager.py",  # Prevent self-reload
        }
        self.loaded_modules: Set[str] = set()
        self._initialize_loaded_modules()

    def _initialize_loaded_modules(self) -> None:
        """Initialize the set of loaded modules from sys.modules."""
        self.loaded_modules = {
            name
            for name in sys.modules
            if name.startswith("src.") and "process_manager" not in name
        }

    def _should_skip(self, path: str) -> bool:
        """Check if the file should be skipped for reloading."""
        return any(pattern in path for pattern in self.skip_patterns)

    def _get_module_name(self, path: str) -> str:
        """Convert file path to module name."""
        rel_path = os.path.relpath(path, self.src_path)
        module_path = os.path.splitext(rel_path)[0].replace(os.sep, ".")
        return f"src.{module_path}"

    def _reload_module(self, module_name: str) -> None:
        """Safely reload a module and its dependencies."""
        try:
            if module_name in sys.modules:
                logger.info(f"Reloading module: {module_name}")
                importlib.reload(sys.modules[module_name])
                self.loaded_modules.add(module_name)
            else:
                logger.info(f"Loading new module: {module_name}")
                importlib.import_module(module_name)
                self.loaded_modules.add(module_name)
        except Exception as e:
            logger.error(f"Failed to reload {module_name}: {str(e)}")

    def on_modified(self, event):
        if event.is_directory or not event.src_path.endswith(".py"):
            return

        if self._should_skip(event.src_path):
            return

        current_time = time.time()
        if event.src_path in self.last_reload:
            if current_time - self.last_reload[event.src_path] < self.reload_cooldown:
                return

        self.last_reload[event.src_path] = current_time
        module_name = self._get_module_name(event.src_path)
        self._reload_module(module_name)


class ProcessManager:
    def __init__(self, src_path: str = "src"):
        self.src_path = os.path.abspath(src_path)
        self.observer = Observer()
        self.module_reloader = ModuleReloader(self.src_path)

    def start(self) -> None:
        """Start watching for file changes."""
        self.observer.schedule(self.module_reloader, self.src_path, recursive=True)
        self.observer.start()
        logger.info(f"Process Manager started watching: {self.src_path}")

    def stop(self) -> None:
        """Stop watching for file changes."""
        self.observer.stop()
        self.observer.join()
        logger.info("Process Manager stopped")

    @classmethod
    def initialize(cls) -> "ProcessManager":
        """Initialize and start the process manager."""
        manager = cls()
        manager.start()
        return manager
