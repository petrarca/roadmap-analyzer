"""
Capacity loader module for roadmap analyzer.
Handles loading capacity data from Excel files.
"""

import re
from datetime import datetime
from typing import Dict, Optional, Tuple

import pandas as pd

from roadmap_analyzer.capacity import TimePeriodType


def parse_period(period_str: str) -> Tuple[int, int, TimePeriodType]:
    """
    Parse a period string into year, period number, and period type.
    
    Args:
        period_str: String representation of period (e.g., "2025.1" or "2025.Q1")
        
    Returns:
        Tuple of (year, period_number, period_type)
        
    Raises:
        ValueError: If the period string format is invalid
    """
    # Try to match quarterly format (e.g., "2025.Q1")
    quarterly_match = re.match(r"(\d{4})\.Q(\d)", str(period_str))
    if quarterly_match:
        year = int(quarterly_match.group(1))
        quarter = int(quarterly_match.group(2))
        if quarter < 1 or quarter > 4:
            raise ValueError(f"Invalid quarter number: {quarter}. Must be between 1 and 4.")
        return year, quarter, TimePeriodType.QUARTERLY
    
    # Try to match monthly format (e.g., "2025.1")
    monthly_match = re.match(r"(\d{4})\.(\d{1,2})", str(period_str))
    if monthly_match:
        year = int(monthly_match.group(1))
        month = int(monthly_match.group(2))
        if month < 1 or month > 12:
            raise ValueError(f"Invalid month number: {month}. Must be between 1 and 12.")
        return year, month, TimePeriodType.MONTHLY
    
    raise ValueError(f"Invalid period format: {period_str}. Expected format: YYYY.M or YYYY.QN")


def format_period(year: int, period: int, period_type: TimePeriodType) -> str:
    """
    Format year and period into a standardized period string.
    
    Args:
        year: Year number
        period: Period number (month or quarter)
        period_type: Type of period (monthly or quarterly)
        
    Returns:
        Formatted period string
    """
    if period_type == TimePeriodType.QUARTERLY:
        return f"{year}-Q{period}"
    else:  # MONTHLY
        return f"{year}-{period:02d}"


def load_capacity_data(file_path: str, sheet_name: str = "Capacity") -> Dict[str, float]:
    """
    Load capacity data from an Excel file.
    
    Args:
        file_path: Path to the Excel file
        sheet_name: Name of the sheet containing capacity data
        
    Returns:
        Dictionary mapping period strings to capacity values
    """
    try:
        # Try to read the capacity sheet
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        
        # Check if required columns exist
        if "Period" not in df.columns or "Capacity" not in df.columns:
            return {}
        
        # Create a dictionary of period -> capacity
        capacity_dict = {}
        for _, row in df.iterrows():
            try:
                period_str = str(row["Period"])
                capacity = float(row["Capacity"])
                
                # Parse and validate the period format
                year, period, period_type = parse_period(period_str)
                
                # Store with standardized format
                standardized_period = format_period(year, period, period_type)
                capacity_dict[standardized_period] = capacity
                
            except (ValueError, TypeError) as e:
                # Skip invalid rows but continue processing
                print(f"Warning: Skipping invalid capacity row: {row}. Error: {e}")
                continue
        
        return capacity_dict
    
    except pd.errors.EmptyDataError:
        # Return empty dict if sheet is empty
        return {}
    except FileNotFoundError:
        # Return empty dict if file doesn't exist
        return {}
    except ValueError as e:
        # This is likely a "Worksheet named 'Capacity' not found" error, which is normal and expected
        # Since capacity data is optional, we silently return an empty dict
        if "not found" in str(e) and sheet_name in str(e):
            return {}
        # For other value errors, print a warning
        print(f"Warning: Error loading capacity data: {e}")
        return {}
    except Exception as e:
        # Return empty dict for other errors, but print a warning
        print(f"Warning: Error loading capacity data: {e}")
        return {}


def get_capacity_for_period(
    capacity_dict: Dict[str, float],
    year: int,
    period: int,
    period_type: TimePeriodType,
    default_capacity: float
) -> float:
    """
    Get capacity for a specific period, falling back to default if not found.
    
    Args:
        capacity_dict: Dictionary of period capacities
        year: Year to look up
        period: Period number (month or quarter)
        period_type: Type of period (monthly or quarterly)
        default_capacity: Default capacity to use if period not found
        
    Returns:
        Capacity value for the period
    """
    period_key = format_period(year, period, period_type)
    return capacity_dict.get(period_key, default_capacity)


def create_capacity_dataframe(
    capacity_dict: Dict[str, float],
    start_date: datetime,
    end_date: datetime,
    period_type: TimePeriodType,
    default_capacity: float
) -> pd.DataFrame:
    """
    Create a DataFrame with capacity data for visualization.
    
    Args:
        capacity_dict: Dictionary of period capacities
        start_date: Start date for capacity planning
        end_date: End date for capacity planning
        period_type: Type of period (monthly or quarterly)
        default_capacity: Default capacity to use if period not found
        
    Returns:
        DataFrame with periods and capacity values
    """
    # Determine the range of periods to include
    start_year = start_date.year
    end_year = end_date.year
    
    if period_type == TimePeriodType.MONTHLY:
        start_period = start_date.month
        # Calculate the number of months between start and end dates
        total_months = (end_year - start_year) * 12 + end_date.month - start_date.month + 1
        periods_per_year = 12
    else:  # QUARTERLY
        start_period = (start_date.month - 1) // 3 + 1
        # Calculate the number of quarters between start and end dates
        start_quarter = (start_year, start_period)
        end_quarter = (end_year, (end_date.month - 1) // 3 + 1)
        total_periods = (end_quarter[0] - start_quarter[0]) * 4 + end_quarter[1] - start_quarter[1] + 1
        periods_per_year = 4
    
    # Create data for DataFrame
    data = []
    current_year = start_year
    current_period = start_period
    
    if period_type == TimePeriodType.MONTHLY:
        for _ in range(total_months):
            period_key = format_period(current_year, current_period, period_type)
            capacity = capacity_dict.get(period_key, default_capacity)
            
            # Format period for display
            if period_type == TimePeriodType.MONTHLY:
                month_name = datetime(current_year, current_period, 1).strftime("%b")
                display_period = f"{month_name} {current_year}"
            else:
                display_period = f"Q{current_period} {current_year}"
                
            data.append({
                "Period": period_key,
                "DisplayPeriod": display_period,
                "Capacity": capacity,
                "Year": current_year,
                "PeriodNumber": current_period
            })
            
            # Move to next period
            current_period += 1
            if current_period > periods_per_year:
                current_period = 1
                current_year += 1
    else:  # QUARTERLY
        for _ in range(total_periods):
            period_key = format_period(current_year, current_period, period_type)
            capacity = capacity_dict.get(period_key, default_capacity)
            
            display_period = f"Q{current_period} {current_year}"
                
            data.append({
                "Period": period_key,
                "DisplayPeriod": display_period,
                "Capacity": capacity,
                "Year": current_year,
                "PeriodNumber": current_period
            })
            
            # Move to next period
            current_period += 1
            if current_period > periods_per_year:
                current_period = 1
                current_year += 1
    
    return pd.DataFrame(data)
