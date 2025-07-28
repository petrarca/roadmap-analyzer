"""Utility functions for the roadmap analyzer."""

from datetime import date, timedelta
from typing import Union

import numpy as np
import pandas as pd


def convert_to_date(date_obj):
    """Convert various date objects to datetime.date"""
    if hasattr(date_obj, "date") and callable(getattr(date_obj, "date")):
        # It's a datetime or Timestamp with a date() method
        return date_obj.date()
    elif isinstance(date_obj, date):
        # It's already a date object
        return date_obj
    else:
        # Try to convert to string and parse
        try:
            return pd.to_datetime(str(date_obj)).date()
        except (ValueError, TypeError):
            # Return the original if all else fails
            return date_obj


def triangular_random(min_val, mode_val, max_val):
    """Generate random value from triangular distribution.

    Args:
        min_val (float): Minimum value
        mode_val (float): Most likely value
        max_val (float): Maximum value

    Returns:
        float: Random value from triangular distribution
    """
    return np.random.triangular(min_val, mode_val, max_val)


def add_working_days(start_date, days):
    """Add working days to a date (excluding weekends).

    Args:
        start_date (date): Starting date
        days (int): Number of working days to add

    Returns:
        date: Date after adding working days
    """
    current = start_date
    days_added = 0

    while days_added < days:
        current += timedelta(days=1)
        if current.weekday() < 5:  # Monday = 0, Friday = 4
            days_added += 1

    return current


def get_quarter_from_date(date_obj):
    """Get quarter string from date.

    Args:
        date_obj (date): Date object

    Returns:
        str: Quarter string in format 'YYYY-QN'
    """
    year = date_obj.year
    quarter = (date_obj.month - 1) // 3 + 1
    return f"{year}-Q{quarter}"


def is_working_day(date_obj: Union[date, pd.Timestamp]) -> bool:
    """Check if a date is a working day (Monday-Friday).

    Args:
        date_obj: The date to check

    Returns:
        True if the date is a working day (Monday-Friday), False otherwise
    """
    # Convert pandas Timestamp to date if needed
    if hasattr(date_obj, "date") and callable(getattr(date_obj, "date")):
        date_obj = date_obj.date()

    # Monday = 0, Friday = 4, Saturday = 5, Sunday = 6
    return date_obj.weekday() < 5


def prepare_dataframe_for_display(df):
    """Prepare DataFrame for Streamlit display with PyArrow compatibility.

    This function ensures all columns have types that are compatible with PyArrow
    serialization, preventing Streamlit display errors.

    Args:
        df: DataFrame to prepare

    Returns:
        DataFrame with PyArrow-compatible column types
    """
    df_copy = df.copy()

    # Handle columns that might contain mixed int/None values
    for col in df_copy.columns:
        # Skip columns with all None/NaN values
        if df_copy[col].isna().all():
            continue

        # Get non-null values for type checking
        non_null_values = df_copy[col].dropna()
        if len(non_null_values) > 0:
            # Check if all non-null values could be numeric
            if all(isinstance(x, (int, float)) or (isinstance(x, str) and x.replace(".", "").isdigit()) for x in non_null_values):
                try:
                    # Test conversion to numeric
                    pd.to_numeric(non_null_values, errors="raise")
                    # If successful, convert to nullable integer
                    df_copy[col] = pd.to_numeric(df_copy[col], errors="coerce").astype("Int64")
                except (ValueError, TypeError):
                    # Keep as object type if not numeric
                    pass

    return df_copy
