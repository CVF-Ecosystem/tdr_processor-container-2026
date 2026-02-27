# utils/plugin_loader.py
"""
Plugin system for TDR Processor custom extractors.

Allows users to add custom data extractors for non-standard TDR formats
by placing Python files in the 'plugins/' directory.

Plugin Convention:
    Each plugin file must define:
    - EXTRACTOR_NAME: str - unique identifier for this extractor
    - EXTRACTOR_CLASS: type - class that inherits from BaseExtractor
    - SUPPORTED_PATTERNS: List[str] - filename patterns this extractor handles

Example plugin file (plugins/extractor_custom_format.py):
    from utils.plugin_loader import BaseExtractor

    EXTRACTOR_NAME = "custom_format"
    SUPPORTED_PATTERNS = ["CUSTOM_*.xlsx", "SPECIAL_*.xlsx"]

    class CustomFormatExtractor(BaseExtractor):
        def extract_vessel_info(self) -> dict:
            # Custom extraction logic
            return {"Vessel Name": ..., "Voyage": ...}

Usage:
    from utils.plugin_loader import PluginLoader

    loader = PluginLoader()
    loader.load_plugins()
    extractor_class = loader.get_extractor_for_file("CUSTOM_001.xlsx")
"""
import importlib
import importlib.util
import logging
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Type


# ============================================================================
# BASE EXTRACTOR INTERFACE
# ============================================================================

class BaseExtractor(ABC):
    """
    Abstract base class for all TDR data extractors.

    Custom extractors must inherit from this class and implement
    all abstract methods.

    Attributes:
        worksheet: openpyxl Worksheet object
        filepath_obj: Path to the source Excel file
        filename_str: Filename string for logging
        vessel_name: Extracted vessel name (set by extract_vessel_info)
        voyage_no: Extracted voyage number (set by extract_vessel_info)
        reference_date_for_events: Reference date for time parsing
    """

    def __init__(self, worksheet, filepath_obj: Path):
        """
        Initialize extractor with worksheet and file path.

        Args:
            worksheet: openpyxl Worksheet object
            filepath_obj: Path to the Excel file
        """
        self.worksheet = worksheet
        self.filepath_obj = filepath_obj
        self.filename_str = filepath_obj.name
        self.vessel_name = None
        self.voyage_no = None
        self.reference_date_for_events = None

    @abstractmethod
    def extract_vessel_info(self) -> dict:
        """
        Extract vessel summary information.

        Returns:
            Dict with vessel info including Vessel Name, Voyage, ATB, ATD, etc.
        """
        ...

    @abstractmethod
    def extract_qc_productivity(self) -> list:
        """
        Extract QC crane productivity data.

        Returns:
            List of dicts, one per QC crane per vessel call.
        """
        ...

    @abstractmethod
    def extract_delay_details(self, ref_date) -> list:
        """
        Extract delay/stop event details.

        Args:
            ref_date: Reference date for time parsing

        Returns:
            List of dicts, one per delay event.
        """
        ...

    @abstractmethod
    def extract_container_details(self) -> list:
        """
        Extract container discharge/load summary.

        Returns:
            List of dicts in long format (one row per category/size/operation).
        """
        ...

    def can_handle(self, filepath: Path) -> bool:
        """
        Check if this extractor can handle the given file.

        Default implementation returns True (handles all files).
        Override to add file-specific detection logic.

        Args:
            filepath: Path to the file to check

        Returns:
            True if this extractor can handle the file
        """
        return True


# ============================================================================
# PLUGIN LOADER
# ============================================================================

class PluginLoader:
    """
    Discovers and loads custom extractor plugins from the plugins/ directory.

    Plugins are Python files matching the pattern 'extractor_*.py' in the
    plugins/ directory. Each plugin must define EXTRACTOR_NAME, EXTRACTOR_CLASS,
    and optionally SUPPORTED_PATTERNS.

    Example:
        loader = PluginLoader()
        loader.load_plugins()
        extractor_class = loader.get_extractor_for_file("CUSTOM_001.xlsx")
        if extractor_class:
            extractor = extractor_class(worksheet, filepath)
    """

    def __init__(self, plugin_dir: Path = Path("plugins")):
        """
        Initialize plugin loader.

        Args:
            plugin_dir: Directory to search for plugin files
        """
        self.plugin_dir = plugin_dir
        self._plugins: Dict[str, Type[BaseExtractor]] = {}
        self._patterns: Dict[str, List[str]] = {}
        self._loaded = False

    def load_plugins(self) -> int:
        """
        Discover and load all plugins from the plugin directory.

        Returns:
            Number of plugins successfully loaded
        """
        if not self.plugin_dir.exists():
            logging.debug(f"[PluginLoader] Plugin directory '{self.plugin_dir}' not found. No plugins loaded.")
            self._loaded = True
            return 0

        loaded_count = 0
        plugin_files = list(self.plugin_dir.glob("extractor_*.py"))

        if not plugin_files:
            logging.debug(f"[PluginLoader] No plugin files found in '{self.plugin_dir}'")
            self._loaded = True
            return 0

        for plugin_file in plugin_files:
            try:
                plugin = self._load_plugin_file(plugin_file)
                if plugin:
                    loaded_count += 1
            except Exception as e:
                logging.error(f"[PluginLoader] Failed to load plugin '{plugin_file.name}': {e}")

        logging.info(f"[PluginLoader] Loaded {loaded_count} plugin(s) from '{self.plugin_dir}'")
        self._loaded = True
        return loaded_count

    def _load_plugin_file(self, plugin_file: Path) -> Optional[str]:
        """
        Load a single plugin file.

        Args:
            plugin_file: Path to the plugin Python file

        Returns:
            Plugin name if loaded successfully, None otherwise
        """
        module_name = f"plugins.{plugin_file.stem}"

        # Load module from file
        spec = importlib.util.spec_from_file_location(module_name, plugin_file)
        if not spec or not spec.loader:
            logging.warning(f"[PluginLoader] Cannot create module spec for '{plugin_file.name}'")
            return None

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        # Validate required attributes
        if not hasattr(module, "EXTRACTOR_NAME"):
            logging.warning(f"[PluginLoader] Plugin '{plugin_file.name}' missing EXTRACTOR_NAME")
            return None

        if not hasattr(module, "EXTRACTOR_CLASS"):
            logging.warning(f"[PluginLoader] Plugin '{plugin_file.name}' missing EXTRACTOR_CLASS")
            return None

        extractor_name = module.EXTRACTOR_NAME
        extractor_class = module.EXTRACTOR_CLASS

        # Validate class inherits from BaseExtractor
        if not (isinstance(extractor_class, type) and issubclass(extractor_class, BaseExtractor)):
            logging.warning(
                f"[PluginLoader] Plugin '{plugin_file.name}' EXTRACTOR_CLASS must inherit from BaseExtractor"
            )
            return None

        self._plugins[extractor_name] = extractor_class
        self._patterns[extractor_name] = getattr(module, "SUPPORTED_PATTERNS", ["*.xlsx"])

        logging.info(
            f"[PluginLoader] Loaded plugin '{extractor_name}' from '{plugin_file.name}' "
            f"(patterns: {self._patterns[extractor_name]})"
        )
        return extractor_name

    def get_extractor_for_file(self, filepath: Path) -> Optional[Type[BaseExtractor]]:
        """
        Find the appropriate extractor class for a given file.

        Checks plugins in order of registration. Returns the first plugin
        whose SUPPORTED_PATTERNS matches the filename.

        Args:
            filepath: Path to the file to find an extractor for

        Returns:
            Extractor class if found, None to use the default extractor
        """
        if not self._loaded:
            self.load_plugins()

        filename = filepath.name

        for plugin_name, extractor_class in self._plugins.items():
            patterns = self._patterns.get(plugin_name, [])
            for pattern in patterns:
                import fnmatch
                if fnmatch.fnmatch(filename, pattern):
                    logging.debug(
                        f"[PluginLoader] Using plugin '{plugin_name}' for file '{filename}'"
                    )
                    return extractor_class

        return None  # Use default extractor

    def list_plugins(self) -> List[Dict]:
        """
        Get information about all loaded plugins.

        Returns:
            List of dicts with plugin name, class, and supported patterns
        """
        if not self._loaded:
            self.load_plugins()

        return [
            {
                "name": name,
                "class": cls.__name__,
                "patterns": self._patterns.get(name, []),
                "module": cls.__module__,
            }
            for name, cls in self._plugins.items()
        ]

    @property
    def plugin_count(self) -> int:
        """Number of loaded plugins."""
        return len(self._plugins)


# ============================================================================
# GLOBAL PLUGIN LOADER INSTANCE
# ============================================================================

# Singleton instance - initialized lazily
_plugin_loader: Optional[PluginLoader] = None


def get_plugin_loader(plugin_dir: Path = Path("plugins")) -> PluginLoader:
    """
    Get the global plugin loader instance.

    Creates and loads plugins on first call.

    Args:
        plugin_dir: Directory to search for plugins

    Returns:
        Initialized PluginLoader instance
    """
    global _plugin_loader
    if _plugin_loader is None:
        _plugin_loader = PluginLoader(plugin_dir)
        _plugin_loader.load_plugins()
    return _plugin_loader
