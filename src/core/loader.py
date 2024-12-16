from typing import Dict, Set, Callable, Any
from pathlib import Path
import importlib
import inspect
import networkx as nx
from src.utils.logging import get_logger
import asyncio

logger = get_logger()


class ModuleLoader:
    """Handles discovery, dependency resolution, and loading of bot modules."""

    def __init__(self, modules_path: str = "src/modules"):
        self.modules_path = Path(modules_path).resolve()
        self.discovered_modules: Dict[str, Any] = {}
        self.setup_functions: Dict[str, Callable] = {}
        self.dependencies: Dict[str, Set[str]] = {}
        self.loaded_modules: Set[str] = set()

    def discover_modules(self) -> None:
        """Recursively discover all Python modules with setup functions."""
        if not self.modules_path.exists():
            logger.error(f"Modules directory not found: {self.modules_path}")
            return

        for file_path in self.modules_path.rglob("*.py"):
            if file_path.name.startswith("_") and not file_path.name.startswith("__"):
                continue

            try:
                module_path = (
                    str(file_path.relative_to(Path(".").resolve()))
                    .replace("/", ".")
                    .replace("\\", ".")[:-3]
                )

                module = importlib.import_module(module_path)

                if hasattr(module, "setup"):
                    self.discovered_modules[module_path] = module
                    self.setup_functions[module_path] = getattr(module, "setup")
                    self._analyze_dependencies(module_path)

            except Exception as e:
                logger.error(f"Failed to load {file_path}: {e}")

        logger.info(f"Discovered {len(self.discovered_modules)} modules")

    def _analyze_dependencies(self, module_path: str) -> None:
        """Extract module dependencies from setup function signature."""
        setup_func = self.setup_functions[module_path]
        params = inspect.signature(setup_func).parameters

        self.dependencies[module_path] = {
            param for param, _ in params.items() if param not in ("bot", "self")
        }

    def _resolve_load_order(self) -> list[str]:
        """Determine module load order using topological sorting."""
        graph = nx.DiGraph()

        # Add all modules and their dependencies
        for module in self.setup_functions:
            graph.add_node(module)
            for dep in self.dependencies.get(module, set()):
                for provider in self._find_dependency_providers(dep):
                    graph.add_edge(provider, module)

        try:
            ordered = list(nx.topological_sort(graph))
            remaining = set(self.setup_functions) - set(ordered)
            return ordered + list(remaining)
        except nx.NetworkXUnfeasible:
            raise ValueError("Circular dependency detected")

    def _find_dependency_providers(self, dependency: str) -> Set[str]:
        """Find modules that provide a given dependency."""
        return {
            module_path
            for module_path, module in self.discovered_modules.items()
            if hasattr(module, f"provide_{dependency}")
        }

    async def load_all(self, bot: Any) -> None:
        """Load all modules in parallel within dependency groups."""
        if not self.discovered_modules:
            self.discover_modules()

        # Group modules by dependency level
        load_order = self._resolve_load_order()
        dependency_groups = self._group_by_dependency_level(load_order)

        # Load each group in parallel
        for group in dependency_groups:
            tasks = [self.load_module(module_path, bot) for module_path in group]
            await asyncio.gather(*tasks)

    def _group_by_dependency_level(self, load_order: list[str]) -> list[set[str]]:
        """Group modules by their dependency level for parallel loading."""
        graph = nx.DiGraph()

        # Build dependency graph
        for module in load_order:
            graph.add_node(module)
            for dep in self.dependencies.get(module, set()):
                for provider in self._find_dependency_providers(dep):
                    graph.add_edge(provider, module)

        # Group nodes by their longest path length from root
        levels: Dict[int, set[str]] = {}
        for node in graph.nodes():
            # Find longest path length to this node
            paths = [len(path) for path in nx.all_simple_paths(graph, node, node)]
            level = max(paths) if paths else 0
            levels.setdefault(level, set()).add(node)

        # Return groups in order
        return [levels[level] for level in sorted(levels.keys())]

    async def load_module(self, module_path: str, bot: Any) -> None:
        """Load a single module with its dependencies."""
        if module_path in self.loaded_modules:
            return

        try:
            # Collect dependencies
            deps = {"bot": bot}
            for dep in self.dependencies.get(module_path, set()):
                if provider := next(iter(self._find_dependency_providers(dep)), None):
                    deps[dep] = getattr(
                        self.discovered_modules[provider], f"provide_{dep}"
                    )()
                else:
                    # Try to get from service manager
                    from src.services import get_services

                    try:
                        deps[dep] = get_services().get_service(dep)
                    except KeyError:
                        raise ValueError(f"Dependency not found: {dep}")

            await self.setup_functions[module_path](**deps)
            self.loaded_modules.add(module_path)
            logger.info(f"Loaded module: {module_path}")

        except Exception as e:
            logger.error(f"Failed to load {module_path}: {e}")
            raise
