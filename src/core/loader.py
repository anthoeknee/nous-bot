from typing import Dict, Set, Callable, Any
from pathlib import Path
import importlib
import inspect
from collections import defaultdict
import networkx as nx
from src.utils.logging import get_logger

logger = get_logger()


class ModuleLoader:
    """
    Handles discovery, dependency resolution, and loading of bot modules.
    """

    def __init__(self, modules_path: str = "src/modules"):
        self.modules_path = Path(modules_path)
        self.discovered_modules: Dict[str, Any] = {}
        self.setup_functions: Dict[str, Callable] = {}
        self.dependencies: Dict[str, Set[str]] = defaultdict(set)
        self.loaded_modules: Set[str] = set()

    def discover_modules(self) -> None:
        """
        Recursively discover all Python modules in the modules directory.
        """
        logger.info(f"Discovering modules in {self.modules_path}")

        for file_path in self.modules_path.rglob("*.py"):
            if file_path.name.startswith("_"):
                continue

            relative_path = file_path.relative_to(Path("."))
            module_path = str(relative_path).replace("/", ".").replace("\\", ".")[:-3]

            try:
                module = importlib.import_module(module_path)
                self.discovered_modules[module_path] = module

                # Look for setup function
                if hasattr(module, "setup"):
                    self.setup_functions[module_path] = getattr(module, "setup")
                    self._analyze_dependencies(module_path)

            except Exception as e:
                logger.error(f"Failed to import module {module_path}: {str(e)}")

        logger.info(f"Discovered {len(self.discovered_modules)} modules")

    def _analyze_dependencies(self, module_path: str) -> None:
        """
        Analyze setup function signature to determine required dependencies.
        """
        setup_func = self.setup_functions[module_path]
        signature = inspect.signature(setup_func)

        for param_name, param in signature.parameters.items():
            # Skip self parameter for class methods
            if param_name == "self":
                continue

            # Add parameter as dependency
            self.dependencies[module_path].add(param_name)

    def _resolve_load_order(self) -> list[str]:
        """
        Use topological sorting to determine correct module load order.
        """
        graph = nx.DiGraph()

        # Add all modules as nodes
        for module in self.setup_functions.keys():
            graph.add_node(module)

        # Add dependency edges
        for module, deps in self.dependencies.items():
            for dep in deps:
                # Find modules that provide this dependency
                providers = self._find_dependency_providers(dep)
                if providers:
                    for provider in providers:
                        graph.add_edge(provider, module)

        try:
            # Perform topological sort
            return list(nx.topological_sort(graph))
        except nx.NetworkXUnfeasible:
            logger.error("Circular dependency detected in modules")
            raise ValueError("Circular dependency detected")

    def _find_dependency_providers(self, dependency: str) -> Set[str]:
        """
        Find modules that provide a given dependency.
        """
        providers = set()

        for module_path, module in self.discovered_modules.items():
            if hasattr(module, f"provide_{dependency}"):
                providers.add(module_path)

        return providers

    async def load_all(self, bot: Any) -> None:
        """
        Load all modules in the correct order.

        Args:
            bot: The Discord bot instance
        """
        if not self.discovered_modules:
            self.discover_modules()

        load_order = self._resolve_load_order()
        logger.info(f"Loading modules in order: {load_order}")

        for module_path in load_order:
            await self.load_module(module_path, bot)

    async def load_module(self, module_path: str, bot: Any) -> None:
        """
        Load a single module and its dependencies.

        Args:
            module_path: The module path to load
            bot: The Discord bot instance
        """
        if module_path in self.loaded_modules:
            return

        logger.info(f"Loading module: {module_path}")

        try:
            # Collect dependencies
            deps = {}
            for dep in self.dependencies[module_path]:
                provider = next(iter(self._find_dependency_providers(dep)), None)
                if provider:
                    module = self.discovered_modules[provider]
                    deps[dep] = getattr(module, f"provide_{dep}")()
                else:
                    # Check if dependency is a service
                    from src.services import get_services

                    try:
                        deps[dep] = get_services().get_service(dep)
                    except KeyError:
                        logger.warning(f"Dependency {dep} not found for {module_path}")

            # Call setup function with dependencies
            setup_func = self.setup_functions[module_path]
            await setup_func(bot, **deps)

            self.loaded_modules.add(module_path)
            logger.info(f"Successfully loaded module: {module_path}")

        except Exception as e:
            logger.error(f"Failed to load module {module_path}: {str(e)}")
            raise
