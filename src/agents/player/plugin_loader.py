"""Plugin loader for external strategy implementations.

This module provides functionality to discover and load strategy plugins
from the plugins directory at runtime, enabling extensibility without
modifying core code.

Example Usage:
    from agents.player.plugin_loader import PluginManager

    manager = PluginManager()
    manager.discover_plugins()

    # All discovered strategies are now registered
    strategy = get_strategy("my_custom_strategy")
"""

import importlib.util
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Type

from .strategy import STRATEGIES, ParityStrategy

logger = logging.getLogger(__name__)


class PluginError(Exception):
    """Exception raised for plugin-related errors."""

    pass


class PluginManager:
    """Manages discovery and loading of strategy plugins.

    The plugin manager scans the plugins directory for subdirectories
    containing Python modules that implement the ParityStrategy interface.

    Plugin Structure:
        plugins/
        └── my_strategy/
            ├── __init__.py
            └── strategy.py  # Contains STRATEGY_CLASS or ParityStrategy subclass

    Attributes:
        plugins_dir: Path to the plugins directory
        loaded_plugins: Dictionary of loaded plugin names to strategy instances
    """

    def __init__(self, plugins_dir: Optional[Path] = None):
        """Initialize the plugin manager.

        Args:
            plugins_dir: Custom plugins directory path. If None, uses
                         the default 'plugins' directory relative to this module.
        """
        if plugins_dir is None:
            self.plugins_dir = Path(__file__).parent / "plugins"
        else:
            self.plugins_dir = Path(plugins_dir)

        self.loaded_plugins: Dict[str, ParityStrategy] = {}
        self._discovered_modules: List[str] = []

    def discover_plugins(self) -> List[str]:
        """Discover and load all plugins from the plugins directory.

        Scans the plugins directory for subdirectories containing valid
        strategy implementations and loads them into the global STRATEGIES
        registry.

        Returns:
            List of successfully loaded plugin names.

        Raises:
            PluginError: If the plugins directory doesn't exist.
        """
        if not self.plugins_dir.exists():
            logger.info(f"Plugins directory not found: {self.plugins_dir}")
            return []

        if not self.plugins_dir.is_dir():
            raise PluginError(f"Plugins path is not a directory: {self.plugins_dir}")

        loaded = []
        for item in self.plugins_dir.iterdir():
            if item.is_dir() and not item.name.startswith("_"):
                try:
                    strategy = self._load_plugin(item)
                    if strategy:
                        name = strategy.get_name()
                        self.loaded_plugins[name] = strategy
                        STRATEGIES[name] = strategy
                        loaded.append(name)
                        logger.info(f"Loaded plugin strategy: {name}")
                except Exception as e:
                    logger.warning(f"Failed to load plugin from {item}: {e}")

        self._discovered_modules = loaded
        return loaded

    def _load_plugin(self, plugin_dir: Path) -> Optional[ParityStrategy]:
        """Load a single plugin from a directory.

        Args:
            plugin_dir: Path to the plugin directory.

        Returns:
            Instantiated ParityStrategy if successful, None otherwise.
        """
        # Look for strategy.py first, then __init__.py
        module_files = ["strategy.py", "__init__.py"]

        for module_file in module_files:
            module_path = plugin_dir / module_file
            if module_path.exists():
                return self._load_module(module_path, plugin_dir.name)

        logger.debug(f"No valid module found in plugin directory: {plugin_dir}")
        return None

    def _load_module(self, module_path: Path, plugin_name: str) -> Optional[ParityStrategy]:
        """Load a Python module and extract the strategy class.

        Args:
            module_path: Path to the Python module file.
            plugin_name: Name to use for the module in sys.modules.

        Returns:
            Instantiated ParityStrategy if found, None otherwise.
        """
        module_name = f"plugins.{plugin_name}"

        try:
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            if spec is None or spec.loader is None:
                return None

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            # Look for STRATEGY_CLASS attribute first
            if hasattr(module, "STRATEGY_CLASS"):
                strategy_class = getattr(module, "STRATEGY_CLASS")
                if isinstance(strategy_class, type) and issubclass(
                    strategy_class, ParityStrategy
                ):
                    return strategy_class()

            # Otherwise, find any ParityStrategy subclass
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, ParityStrategy)
                    and attr is not ParityStrategy
                ):
                    return attr()

            logger.debug(f"No ParityStrategy subclass found in {module_path}")
            return None

        except Exception as e:
            logger.error(f"Error loading module {module_path}: {e}")
            raise PluginError(f"Failed to load plugin module: {e}") from e

    def get_loaded_plugins(self) -> Dict[str, ParityStrategy]:
        """Get all loaded plugin strategies.

        Returns:
            Dictionary mapping strategy names to strategy instances.
        """
        return self.loaded_plugins.copy()

    def reload_plugins(self) -> List[str]:
        """Reload all plugins, refreshing any changes.

        Returns:
            List of reloaded plugin names.
        """
        # Clear existing plugin registrations
        for name in self._discovered_modules:
            if name in STRATEGIES:
                del STRATEGIES[name]
            if name in self.loaded_plugins:
                del self.loaded_plugins[name]

        self._discovered_modules.clear()

        # Re-discover
        return self.discover_plugins()

    def unload_plugin(self, name: str) -> bool:
        """Unload a specific plugin.

        Args:
            name: Name of the plugin to unload.

        Returns:
            True if plugin was unloaded, False if not found.
        """
        if name in self.loaded_plugins:
            del self.loaded_plugins[name]
            if name in STRATEGIES:
                del STRATEGIES[name]
            if name in self._discovered_modules:
                self._discovered_modules.remove(name)
            logger.info(f"Unloaded plugin: {name}")
            return True
        return False


# Global plugin manager instance
_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """Get or create the global plugin manager instance.

    Returns:
        The global PluginManager instance.
    """
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager


def discover_and_load_plugins() -> List[str]:
    """Convenience function to discover and load all plugins.

    Returns:
        List of loaded plugin names.
    """
    manager = get_plugin_manager()
    return manager.discover_plugins()


def register_external_strategy(strategy: ParityStrategy) -> None:
    """Register an external strategy instance.

    This allows programmatic registration of strategies without
    using the file-based plugin system.

    Args:
        strategy: An instance of ParityStrategy to register.

    Raises:
        ValueError: If strategy is not a valid ParityStrategy instance.
    """
    if not isinstance(strategy, ParityStrategy):
        raise ValueError("Strategy must be an instance of ParityStrategy")

    name = strategy.get_name()
    STRATEGIES[name] = strategy
    logger.info(f"Registered external strategy: {name}")
