"""Data loading functionality for the roadmap analyzer."""

from typing import Any, Dict, List

import pandas as pd
import streamlit as st
from pydantic import ValidationError

from roadmap_analyzer.components import add_notification
from roadmap_analyzer.config import AppConfig
from roadmap_analyzer.loader_utils import create_column_mapping, find_sheet_name_case_insensitive
from roadmap_analyzer.models import WorkItem


def _find_and_read_data_sheet(file_path: str) -> pd.DataFrame:
    """Find and read the data sheet from an Excel file.

    Attempts to read from "Items" sheet first, falls back to default sheet if not found.

    Args:
        file_path (str): Path to the Excel file

    Returns:
        pd.DataFrame: DataFrame with the data

    Raises:
        Exception: If the file cannot be read
    """
    excel_file = pd.ExcelFile(file_path)
    items_sheet = find_sheet_name_case_insensitive(excel_file.sheet_names, "Items")

    if items_sheet:
        df = pd.read_excel(file_path, sheet_name=items_sheet)
        add_notification(f"✅ Successfully loaded data from '{items_sheet}' sheet", "success")
    else:
        # If "Items" sheet doesn't exist, try default sheet
        add_notification("⚠️ 'Items' sheet not found, trying default sheet...", "warning")
        df = pd.read_excel(file_path)
        add_notification("✅ Successfully loaded data from default sheet", "success")

    return df


def _check_required_columns(df: pd.DataFrame, required_cols: List[str]) -> List[str]:
    """Check if all required columns exist in the DataFrame.

    Args:
        df (pd.DataFrame): DataFrame to check
        required_cols (List[str]): List of required column names

    Returns:
        List[str]: List of missing columns, empty if all required columns exist
    """
    column_mapping = create_column_mapping(df.columns)
    missing_cols = []

    for col in required_cols:
        if col.lower() not in column_mapping:
            missing_cols.append(col)

    return missing_cols


def _process_date_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Process date columns in the DataFrame.

    Args:
        df (pd.DataFrame): DataFrame to process

    Returns:
        pd.DataFrame: Processed DataFrame
    """
    column_mapping = create_column_mapping(df.columns)

    # Convert due dates to datetime
    due_date_col = column_mapping.get("due date")
    if due_date_col:
        df[due_date_col] = pd.to_datetime(df[due_date_col])

    # Convert start dates to datetime if the column exists
    start_date_col = column_mapping.get("start date")
    if start_date_col:
        df[start_date_col] = pd.to_datetime(df[start_date_col], errors="coerce")

    return df


def load_project_data(file_path: str, config: AppConfig) -> pd.DataFrame:
    """Load project data from Excel file.

    Attempts to read from "Items" sheet first, falls back to default sheet if not found.
    Sheet names and column names are case-insensitive.

    Args:
        file_path (str): Path to the Excel file containing project data
        config (AppConfig): Application configuration

    Returns:
        pd.DataFrame or None: DataFrame with project data if successful, None if failed
    """
    try:
        # Find and read the data sheet
        try:
            df = _find_and_read_data_sheet(file_path)
        except Exception as e:
            add_notification(f"Error reading Excel file: {str(e)}", "error")
            return None

        # Check required columns
        missing_cols = _check_required_columns(df, config.data.required_columns)
        if missing_cols:
            st.error(f"Missing required columns: {missing_cols}")
            return None

        # Process date columns
        df = _process_date_columns(df)

        # Clean up dependency column for PyArrow compatibility
        column_mapping = create_column_mapping(df.columns)
        dependency_col = column_mapping.get("dependency")
        if dependency_col:
            df[dependency_col] = df[dependency_col].astype("Int64")  # Nullable integer type

        return df

    except FileNotFoundError:
        add_notification(f"File not found: {file_path}", "error")
        return None
    except Exception as e:
        add_notification(f"Error loading file: {str(e)}", "error")
        return None


def _get_column_names(column_mapping: Dict[str, str]) -> Dict[str, str]:
    """Get column names from column mapping.

    Args:
        column_mapping (Dict[str, str]): Mapping of lowercase column names to actual column names

    Returns:
        Dict[str, str]: Dictionary of column types to actual column names
    """
    return {
        "position": column_mapping.get("position"),
        "item": column_mapping.get("item"),
        "due_date": column_mapping.get("due date"),
        "dependency": column_mapping.get("dependency"),
        "start_date": column_mapping.get("start date"),
        "priority": column_mapping.get("priority"),
        "best": column_mapping.get("best"),
        "likely": column_mapping.get("likely"),
        "worst": column_mapping.get("worst"),
    }


def _check_required_work_item_columns(columns: Dict[str, str]) -> List[str]:
    """Check if all required columns for work items exist.

    Args:
        columns (Dict[str, str]): Dictionary of column types to actual column names

    Returns:
        List[str]: List of missing columns, empty if all required columns exist
    """
    required_columns = ["position", "item", "due_date", "best", "likely", "worst"]
    missing = []

    for col_type in required_columns:
        if not columns.get(col_type):
            # Convert to display name (e.g., "due_date" -> "Due date")
            display_name = col_type.replace("_", " ").title()
            missing.append(display_name)

    return missing


def _extract_work_item_data(row: pd.Series, columns: Dict[str, str]) -> Dict[str, Any]:
    """Extract work item data from a DataFrame row.

    Args:
        row (pd.Series): DataFrame row
        columns (Dict[str, str]): Dictionary of column types to actual column names

    Returns:
        Dict[str, Any]: Dictionary of work item data
    """
    # Handle optional fields with None defaults
    dependency = None
    if columns["dependency"] and not pd.isna(row[columns["dependency"]]):
        dependency = row[columns["dependency"]]

    start_date = None
    if columns["start_date"] and not pd.isna(row[columns["start_date"]]):
        start_date = row[columns["start_date"]]

    priority = None
    if columns["priority"] and not pd.isna(row[columns["priority"]]):
        priority = row[columns["priority"]]

    # Return work item data dictionary
    return {
        "position": row[columns["position"]],
        "Item": row[columns["item"]],
        "due_date": row[columns["due_date"]],
        "Start date": start_date,  # Uses alias for start_date field
        "Priority": priority,  # Uses alias for priority field
        "dependency": dependency,
        "Best": row[columns["best"]],  # Uses alias for best_estimate field
        "Likely": row[columns["likely"]],  # Uses alias for most_likely_estimate field
        "Worst": row[columns["worst"]],  # Uses alias for worst_estimate field
    }


def _display_validation_errors(errors: List[str]) -> None:
    """Display validation errors in Streamlit.

    Args:
        errors (List[str]): List of error messages
    """
    if errors:
        st.error("Validation errors in work items:")
        for error in errors:
            st.error(error)


def convert_to_work_items(df: pd.DataFrame, config: AppConfig) -> List[WorkItem]:
    """Convert DataFrame to a list of WorkItem objects.

    Args:
        df (pd.DataFrame): DataFrame with work item data
        config (AppConfig): Application configuration

    Returns:
        List[WorkItem]: List of validated WorkItem objects
    """
    if df is None or df.empty:
        return []

    work_items = []
    validation_errors = []

    # Create case-insensitive column mapping
    column_mapping = create_column_mapping(df.columns)

    # Get column names
    columns = _get_column_names(column_mapping)

    # Check required columns
    missing_cols = _check_required_work_item_columns(columns)
    if missing_cols:
        error_msg = f"Missing required columns: {', '.join(missing_cols)}"
        validation_errors.append(error_msg)
        _display_validation_errors(validation_errors)
        return []

    # Convert each row to a WorkItem
    for _, row in df.iterrows():
        try:
            # Extract work item data
            item_data = _extract_work_item_data(row, columns)

            # Create and add work item
            work_item = WorkItem(**item_data)
            work_items.append(work_item)

        except ValidationError as e:
            # Get position for error message
            position = row[columns["position"]] if columns["position"] else "unknown"
            # Collect validation errors
            error_msg = f"Error in row {position}: {str(e)}"
            validation_errors.append(error_msg)

    # Display validation errors if any
    _display_validation_errors(validation_errors)

    return work_items


def load_work_items(file_path: str, config: AppConfig) -> List[WorkItem]:
    """Load and convert work items from Excel file.

    This is a convenience function that combines load_project_data and convert_to_work_items.

    Args:
        file_path (str): Path to the Excel file
        config (AppConfig): Application configuration

    Returns:
        List[WorkItem]: List of validated WorkItem objects
    """
    df = load_project_data(file_path, config)
    return convert_to_work_items(df, config)
