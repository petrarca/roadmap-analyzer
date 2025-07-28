"""Configuration loading functionality for the roadmap analyzer."""

from typing import Any, Dict, Optional

import pandas as pd
import streamlit as st

from roadmap_analyzer.components import add_notification
from roadmap_analyzer.config import AppConfig


def load_config_from_excel(file_path: str, app_config: AppConfig) -> Optional[Dict[str, Any]]:
    """Load configuration from Excel file if a Config tab exists.

    Args:
        file_path (str): Path to the Excel file
        app_config (AppConfig): Current application configuration

    Returns:
        Optional[Dict[str, Any]]: Dictionary of configuration values if successful, None otherwise
    """
    try:
        # Check if the Excel file has a Config tab
        excel_file = pd.ExcelFile(file_path)
        if "Config" not in excel_file.sheet_names:
            # No Config tab, return None silently (no warning needed)
            return None

        # Read the Config tab
        df = pd.read_excel(file_path, sheet_name="Config")

        # Check if the required columns exist
        if "Config" not in df.columns or "Value" not in df.columns:
            add_notification("⚠️ Config tab found but missing required columns (Config, Value)", "warning")
            return None

        # Extract configuration values
        config_dict = {}
        for _, row in df.iterrows():
            config_name = row["Config"]
            config_value = row["Value"]

            # Skip rows with empty config names
            if pd.isna(config_name) or not config_name:
                continue

            # Store the configuration value
            config_dict[config_name] = config_value

        if config_dict:
            # Create a summary of loaded values for the notification
            config_summary = ", ".join([f"{k}={v}" for k, v in config_dict.items()])
            add_notification(f"✅ Loaded {len(config_dict)} configuration values from Excel ({config_summary})", "info")
        else:
            add_notification("⚠️ Config tab found but no valid configuration entries", "warning")

        return config_dict

    except FileNotFoundError:
        add_notification(f"File not found: {file_path}", "error")
        return None
    except Exception as e:
        add_notification(f"Error loading configuration: {str(e)}", "error")
        return None


def _handle_start_date(value):
    """Handle start date configuration value.

    Args:
        value: The start date value from the configuration
    """
    if pd.notna(value):
        # Store as ISO format string if it's a valid date
        try:
            if isinstance(value, pd.Timestamp):
                # Store as ISO format string
                value = value.strftime("%Y-%m-%d %H:%M:%S")
            elif isinstance(value, str):
                # Try to parse as date and format
                value = pd.to_datetime(value).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            # If parsing fails, store as is
            pass

        # Store in session state for later use
        st.session_state["start_date"] = value


def _parse_capacity_value(value):
    """Parse capacity value with optional suffixes like '/q' for quarterly.

    Args:
        value: The capacity value to parse, which might include a suffix

    Returns:
        int or float: The parsed numeric value

    Raises:
        ValueError: If the value cannot be parsed
    """
    if isinstance(value, (int, float)):
        return value

    if isinstance(value, str):
        # Handle capacity values with suffixes
        if value.lower().endswith("/q"):
            # Extract the numeric part before '/q'
            numeric_part = value.lower().split("/q")[0].strip()
            return int(numeric_part) if numeric_part.isdigit() else float(numeric_part)
        # Future extension for monthly values
        # elif value.lower().endswith('/m'):
        #     numeric_part = value.lower().split('/m')[0].strip()
        #     return int(numeric_part) if numeric_part.isdigit() else float(numeric_part)

    # If no special handling needed, convert directly
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return float(value)


def _set_nested_attribute(target, attr_path, value):
    """Set a nested attribute in a Pydantic model.

    Args:
        target: Target object to set attribute on
        attr_path: List of attribute names to navigate
        value: Value to set

    Returns:
        bool: True if successful, False otherwise
    """
    # Navigate to the nested attribute
    for i, attr in enumerate(attr_path):
        if i == len(attr_path) - 1:
            # Last attribute, set the value
            try:
                # Get current value to determine type
                current_value = getattr(target, attr)

                # Special handling for capacity values
                if attr == "default_capacity_per_quarter" and isinstance(value, str):
                    try:
                        value = _parse_capacity_value(value)
                    except (ValueError, TypeError) as e:
                        add_notification(f"⚠️ Could not parse capacity value '{value}': {str(e)}", "warning")
                        return False
                # Standard type conversion
                elif isinstance(current_value, int) and not isinstance(value, int):
                    value = int(value)
                elif isinstance(current_value, float) and not isinstance(value, float):
                    value = float(value)
                elif isinstance(current_value, str) and not isinstance(value, str):
                    value = str(value)

                setattr(target, attr, value)
                return True
            except (ValueError, TypeError, AttributeError) as e:
                add_notification(f"⚠️ Could not set attribute {attr} to {value}: {str(e)}", "warning")
                return False
        else:
            # Navigate to the next level
            try:
                target = getattr(target, attr)
            except AttributeError:
                add_notification(f"⚠️ Attribute {attr} not found", "warning")
                return False
    return False


def apply_config_values(config_dict: Dict[str, Any], app_config: AppConfig) -> AppConfig:
    """Apply configuration values from dictionary to AppConfig.

    Args:
        config_dict (Dict[str, Any]): Dictionary of configuration values
        app_config (AppConfig): Current application configuration

    Returns:
        AppConfig: Updated application configuration
    """
    if not config_dict:
        return app_config

    # Create a copy of the current configuration
    updated_config = app_config.model_copy(deep=True)

    # Map configuration keys to their respective fields in the AppConfig structure
    config_mapping = {
        # Simulation config
        "Start date": None,  # Special handling for date values
        "Capacity": "simulation.default_capacity_per_quarter",
        "Iterations": "simulation.default_num_simulations",
        # Other possible mappings (commented out until needed)
        # "Working days per quarter": "simulation.working_days_per_quarter",
        # "Page title": "ui.page_title",
        # "Page icon": "ui.page_icon",
    }

    # Store any loaded values in session state for UI controls to use
    # This ensures the UI controls will use these values when they're displayed

    # Apply mapped configuration values
    for key, value in config_dict.items():
        if key in config_mapping:
            if key == "Start date":
                _handle_start_date(value)
            else:
                # Handle nested attributes using the mapping
                attr_path = config_mapping[key].split(".")
                _set_nested_attribute(updated_config, attr_path, value)

                # Also store in session state for UI controls to access
                if key == "Capacity":
                    # Store the parsed capacity value in session state
                    try:
                        parsed_value = _parse_capacity_value(value) if isinstance(value, str) else value
                        st.session_state["capacity_per_quarter"] = parsed_value
                    except Exception:
                        pass
                elif key == "Iterations":
                    # Store the iterations value in session state
                    try:
                        iterations_value = int(value) if not isinstance(value, int) else value
                        st.session_state["num_simulations"] = iterations_value
                    except Exception:
                        pass

    return updated_config


def load_and_apply_config(file_path: str, app_config: AppConfig) -> AppConfig:
    """Load configuration from Excel and apply it to the application configuration.

    This is a convenience function that combines load_config_from_excel and apply_config_values.

    Args:
        file_path (str): Path to the Excel file
        app_config (AppConfig): Current application configuration

    Returns:
        AppConfig: Updated application configuration
    """
    config_dict = load_config_from_excel(file_path, app_config)
    if config_dict:
        return apply_config_values(config_dict, app_config)
    return app_config
