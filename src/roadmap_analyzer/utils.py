"""Utility functions for the roadmap analyzer."""

from datetime import date, timedelta
from functools import lru_cache
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


@lru_cache(maxsize=10000)
def add_working_days(start_date, days):
    """Add working days to a date (excluding weekends).

    Args:
        start_date (date): Starting date
        days (int): Number of working days to add

    Returns:
        date: Date after adding working days
    """
    if days <= 0:
        return start_date

    # Optimize by calculating complete weeks first
    weeks, remaining_days = divmod(days, 5)
    result = start_date + timedelta(days=weeks * 7)

    # Handle remaining days
    if remaining_days > 0:
        # Get current weekday (0=Monday, 6=Sunday)
        current_weekday = result.weekday()

        # Calculate how many actual calendar days to add
        if current_weekday + remaining_days <= 4:  # Still within the work week
            result += timedelta(days=remaining_days)
        else:  # Need to skip weekend
            # Add days until Friday
            days_until_friday = 4 - current_weekday
            # Add remaining days after the weekend
            days_after_weekend = remaining_days - days_until_friday
            result += timedelta(days=days_until_friday + 2 + days_after_weekend)

    return result


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


@lru_cache(maxsize=10000)
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


def format_number(value: Union[int, float]) -> str:
    """Format a number with locale-aware thousand separators.

    Args:
        value: The numeric value to format

    Returns:
        Formatted string with locale-appropriate thousand separators
    """
    # Use :n format specifier for locale-aware number formatting
    # This respects the locale settings initialized in main.py
    return f"{int(value):n}"
