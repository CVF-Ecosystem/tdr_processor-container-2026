# TDR Processor Plugins

This directory contains custom extractor plugins for non-standard TDR file formats.

## Creating a Plugin

1. Create a Python file named `extractor_<name>.py` in this directory
2. Define the required attributes and class

### Plugin Template

```python
# plugins/extractor_my_format.py
"""
Custom extractor for My Format TDR files.
"""
from pathlib import Path
from utils.plugin_loader import BaseExtractor

# Required: Unique name for this plugin
EXTRACTOR_NAME = "my_format"

# Optional: Filename patterns this plugin handles (fnmatch syntax)
SUPPORTED_PATTERNS = ["MY_FORMAT_*.xlsx", "CUSTOM_*.xlsx"]


class MyFormatExtractor(BaseExtractor):
    """Custom extractor for My Format TDR files."""

    def can_handle(self, filepath: Path) -> bool:
        """Optional: Add custom detection logic."""
        # Check file content or name to determine if this extractor applies
        return "MY_FORMAT" in filepath.name.upper()

    def extract_vessel_info(self) -> dict:
        """Extract vessel summary from custom format."""
        info = {"Filename": self.filename_str}
        # ... your extraction logic ...
        self.vessel_name = info.get("Vessel Name")
        self.voyage_no = info.get("Voyage")
        return info

    def extract_qc_productivity(self) -> list:
        """Extract QC productivity from custom format."""
        if not self.vessel_name or not self.voyage_no:
            return []
        # ... your extraction logic ...
        return []

    def extract_delay_details(self, ref_date) -> list:
        """Extract delay details from custom format."""
        if not self.vessel_name or not self.voyage_no:
            return []
        # ... your extraction logic ...
        return []

    def extract_container_details(self) -> list:
        """Extract container details from custom format."""
        if not self.vessel_name or not self.voyage_no:
            return []
        # ... your extraction logic ...
        return []


# Required: The extractor class to use
EXTRACTOR_CLASS = MyFormatExtractor
```

## Available Base Methods

Your extractor inherits from `BaseExtractor` which provides:
- `self.worksheet` - openpyxl Worksheet object
- `self.filepath_obj` - Path to the Excel file
- `self.filename_str` - Filename string for logging
- `self.vessel_name` - Set this in `extract_vessel_info()`
- `self.voyage_no` - Set this in `extract_vessel_info()`
- `self.reference_date_for_events` - Set this for time parsing

## Plugin Loading

Plugins are automatically discovered and loaded when the application starts.
The plugin with the first matching `SUPPORTED_PATTERNS` is used for each file.
If no plugin matches, the default `DataExtractor` is used.
