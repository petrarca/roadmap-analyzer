"""Utility functions for Excel loaders to support case-insensitive operations."""

from typing import Dict, List, Optional


def find_sheet_name_case_insensitive(sheet_names: List[str], target_name: str) -> Optional[str]:
    """
    Find a sheet name in a case-insensitive manner.

    Args:
        sheet_names: List of available sheet names
        target_name: Target sheet name to find (case-insensitive)

    Returns:
        The actual sheet name with correct case if found, None otherwise
    """
    target_lower = target_name.lower()
    for name in sheet_names:
        if name.lower() == target_lower:
            return name
    return None


def create_column_mapping(columns) -> Dict[str, str]:
    """
    Create a mapping of lowercase column names to actual column names.

    Args:
        columns: DataFrame columns or list of column names

    Returns:
        Dictionary mapping lowercase column names to actual column names
    """
    return {col.lower(): col for col in columns}


def get_column_case_insensitive(row, column_mapping: Dict[str, str], column_name: str):
    """
    Get a column value using case-insensitive column name.

    Args:
        row: DataFrame row
        column_mapping: Mapping of lowercase column names to actual column names
        column_name: Column name to access (case-insensitive)

    Returns:
        Column value if found, None otherwise
    """
    column_lower = column_name.lower()
    if column_lower in column_mapping:
        return row[column_mapping[column_lower]]
    return None
