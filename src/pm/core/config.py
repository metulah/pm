"""Core utilities for handling project configuration (.pm/config.toml)."""

import pathlib
import toml  # Use the added dependency
from typing import Dict, Any, Optional, List

# Correctly import the function from its actual location
# Import from new core location
from .utils import find_project_root

CONFIG_FILENAME = "config.toml"


def get_config_path() -> Optional[pathlib.Path]:
    """Finds the path to the config file (.pm/config.toml) by searching upwards."""
    project_root_str = find_project_root(
    )  # Returns the project root dir path as str, or None
    if project_root_str:
        project_root = pathlib.Path(project_root_str)
        # Construct path: project_root / .pm / config.toml
        return project_root / ".pm" / CONFIG_FILENAME
    return None


def load_config() -> Dict[str, Any]:
    """Loads the project configuration from .pm/config.toml.

    Returns:
        A dictionary containing the configuration, or an empty dictionary
        if the file doesn't exist or is empty. Returns an empty dict
        on parsing errors as well, logging a warning (TODO: Add logging).
    """
    config_path = get_config_path()
    if not config_path or not config_path.exists():
        return {}

    try:
        with config_path.open("r") as f:
            config_data = toml.load(f)
            return config_data if isinstance(config_data, dict) else {}
    except toml.TomlDecodeError:
        # TODO: Add proper logging/warning mechanism
        print(f"Warning: Could not parse {config_path}. Using empty config.")
        return {}
    except OSError as e:
        # TODO: Add proper logging/warning mechanism
        print(
            f"Warning: Could not read {config_path}: {e}. Using empty config.")
        return {}


def save_config(config_data: Dict[str, Any]) -> bool:
    """Saves the configuration data to .pm/config.toml.

    Ensures the .pm directory exists.

    Args:
        config_data: The dictionary containing configuration to save.

    Returns:
        True if saving was successful, False otherwise.
    """
    config_path = get_config_path()
    if not config_path:
        # This case should ideally be handled before calling save_config,
        # e.g., during `pm init` which establishes the .pm directory.
        # TODO: Add proper logging/error mechanism
        print("Error: Could not determine .pm directory location to save config.")
        return False

    pm_dir = config_path.parent
    try:
        # Ensure .pm directory exists
        pm_dir.mkdir(parents=True, exist_ok=True)
        with config_path.open("w") as f:
            toml.dump(config_data, f)
        return True
    except OSError as e:
        # TODO: Add proper logging/error mechanism
        print(f"Error: Could not write to {config_path}: {e}")
        return False


def get_active_guidelines() -> List[str]:
    """Gets the list of active guidelines from the config."""
    config = load_config()
    # Navigate safely: get 'guidelines' dict, then 'active' list
    guidelines_section = config.get("guidelines", {})
    if isinstance(guidelines_section, dict):
        active_list = guidelines_section.get("active", [])
        if isinstance(active_list, list):
            # Ensure all elements are strings
            return [str(item) for item in active_list]
    return []


def set_active_guidelines(guidelines: List[str]) -> bool:
    """Sets the list of active guidelines in the config."""
    config = load_config()
    if "guidelines" not in config or not isinstance(config["guidelines"], dict):
        config["guidelines"] = {}

    # Ensure all items are strings before saving
    config["guidelines"]["active"] = [str(g) for g in guidelines]
    return save_config(config)
