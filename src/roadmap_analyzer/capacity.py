"""Capacity calculation module for roadmap analysis.

This module provides flexible capacity calculations that can work with different time periods
(quarters, months) and capacity configurations.
"""

from datetime import date, datetime, timedelta
from enum import Enum
from functools import lru_cache
from typing import Dict, Optional, Tuple, Union

from roadmap_analyzer.config import AppConfig
from roadmap_analyzer.utils import get_quarter_from_date, is_working_day


class TimePeriodType(Enum):
    """Supported time period types for capacity calculations."""

    QUARTERLY = "quarterly"
    MONTHLY = "monthly"


class CapacityCalculator:
    """Flexible capacity calculator supporting different time periods and configurations."""

    def __init__(self, config: AppConfig, period_type: TimePeriodType = TimePeriodType.QUARTERLY, capacity_dict: Dict[str, float] = None) -> None:
        """Initialize the capacity calculator.

        Args:
            config: Application configuration
            period_type: Type of time period to use for calculations
            capacity_dict: Optional dictionary mapping period strings to capacity values
        """
        self.config = config
        self.period_type = period_type
        self._capacity_overrides: Dict[str, float] = {}

        # Initialize with capacity dictionary if provided
        if capacity_dict:
            self._capacity_overrides.update(capacity_dict)

    def set_capacity_override(self, period_identifier: str, capacity: float) -> None:
        """Set a capacity override for a specific time period.

        Args:
            period_identifier: Identifier for the time period (e.g., "2024-Q1", "2024-01")
            capacity: Capacity value to use for this period
        """
        self._capacity_overrides[period_identifier] = capacity

    def get_working_days_in_period(self, year_or_date: Union[int, date], period: Optional[int] = None) -> int:
        """Calculate the number of working days in a specific time period.

        This method can be called in two ways:
        1. get_working_days_in_period(year, period) - with year and period as separate arguments
        2. get_working_days_in_period(date_obj) - with a date object

        Args:
            year_or_date: Either the year (int) or a date object (datetime.date)
            period: The period number (1-4 for quarters, 1-12 for months), required if year_or_date is an int

        Returns:
            Number of working days in the period
        """
        # Handle case where a date object is passed
        if isinstance(year_or_date, date):
            date_obj = year_or_date
            year = date_obj.year
            if self.period_type == TimePeriodType.QUARTERLY:
                period = (date_obj.month - 1) // 3 + 1
            else:  # MONTHLY
                period = date_obj.month
        else:
            # Handle case where year and period are passed separately
            year = year_or_date
            if period is None:
                raise ValueError("Period must be provided when year is an integer")

        if self.period_type == TimePeriodType.QUARTERLY:
            return CapacityCalculator._get_working_days_in_quarter(year, period)
        elif self.period_type == TimePeriodType.MONTHLY:
            return self._get_working_days_in_month(year, period)
        else:
            raise ValueError(f"Unsupported period type: {self.period_type}")

    @staticmethod
    @lru_cache(maxsize=128)
    def _get_working_days_in_quarter(year: int, quarter: int) -> int:
        """Calculate the number of working days in a specific quarter."""
        start_month = (quarter - 1) * 3 + 1
        end_month = quarter * 3

        start_date = datetime(year, start_month, 1).date()
        if end_month == 12:
            end_date = datetime(year, end_month, 31).date()
        else:
            end_date = datetime(year, end_month + 1, 1).date() - timedelta(days=1)

        return CapacityCalculator._count_working_days(start_date, end_date)

    def _get_working_days_in_month(self, year: int, month: int) -> int:
        """Calculate the number of working days in a specific month."""
        start_date = datetime(year, month, 1).date()
        if month == 12:
            end_date = datetime(year, month, 31).date()
        else:
            end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)

        return self._count_working_days(start_date, end_date)

    @staticmethod
    @lru_cache(maxsize=128)
    def _count_working_days(start_date: date, end_date: date) -> int:
        """Count working days between two dates (inclusive)."""
        working_days = 0
        current_date = start_date
        while current_date <= end_date:
            if is_working_day(current_date):
                working_days += 1
            current_date += timedelta(days=1)
        return working_days

    def get_period_identifier(self, date_obj: date) -> str:
        """Get the period identifier string for a given date.

        Args:
            date_obj: The date to get period identifier for

        Returns:
            Period identifier string (e.g., "2025-Q1" or "2025-01")
        """
        if self.period_type == TimePeriodType.QUARTERLY:
            return get_quarter_from_date(date_obj)
        elif self.period_type == TimePeriodType.MONTHLY:
            return f"{date_obj.year}-{date_obj.month:02d}"
        else:
            raise ValueError(f"Unsupported period type: {self.period_type}")

    def get_period_info(self, date_obj: date) -> Tuple[str, int, float]:
        """Get period information including capacity per working day.

        Args:
            date_obj: The date to get period info for

        Returns:
            Tuple of (period_string, working_days_in_period, capacity_per_working_day)
        """
        if self.period_type == TimePeriodType.QUARTERLY:
            return self._get_quarter_info(date_obj)
        elif self.period_type == TimePeriodType.MONTHLY:
            return self._get_month_info(date_obj)
        else:
            raise ValueError(f"Unsupported period type: {self.period_type}")

    # Using a regular method instead of cached method to ensure capacity overrides are applied
    def _get_quarter_info(self, date_obj: date) -> Tuple[str, int, float]:
        """Get quarter information including capacity per working day."""
        quarter_str = get_quarter_from_date(date_obj)
        year = date_obj.year
        quarter = (date_obj.month - 1) // 3 + 1

        working_days = CapacityCalculator._get_working_days_in_quarter(year, quarter)

        # Check for capacity override
        capacity_per_period = self._capacity_overrides.get(quarter_str, self.config.simulation.default_capacity_per_quarter)

        capacity_per_working_day = capacity_per_period / working_days

        return quarter_str, working_days, capacity_per_working_day

    def _get_month_info(self, date_obj: date) -> Tuple[str, int, float]:
        """Get month information including capacity per working day."""
        month_str = f"{date_obj.year}-{date_obj.month:02d}"
        year = date_obj.year
        month = date_obj.month

        working_days = self._get_working_days_in_month(year, month)

        # For monthly calculations, we need to derive from quarterly capacity
        # This is a simple approach - could be made more sophisticated
        default_monthly_capacity = self.config.simulation.default_capacity_per_quarter / 3

        capacity_per_period = self._capacity_overrides.get(month_str, default_monthly_capacity)

        capacity_per_working_day = capacity_per_period / working_days

        return month_str, working_days, capacity_per_working_day

    def get_remaining_working_days_in_period(self, date_obj: date) -> int:
        """Calculate the number of remaining working days in the period from a given date.

        Args:
            date_obj: The starting date

        Returns:
            Number of remaining working days in the period (including the start date if it's a working day)
        """
        if self.period_type == TimePeriodType.QUARTERLY:
            return self._get_remaining_working_days_in_quarter(date_obj)
        elif self.period_type == TimePeriodType.MONTHLY:
            return self._get_remaining_working_days_in_month(date_obj)
        else:
            raise ValueError(f"Unsupported period type: {self.period_type}")

    def _get_remaining_working_days_in_quarter(self, date_obj: date) -> int:
        """Calculate the number of remaining working days in the quarter from a given date."""
        year = date_obj.year
        quarter = (date_obj.month - 1) // 3 + 1

        # Determine end date for the quarter
        end_month = quarter * 3
        if end_month == 12:
            end_date = datetime(year, end_month, 31).date()
        else:
            end_date = datetime(year, end_month + 1, 1).date() - timedelta(days=1)

        return self._count_working_days(date_obj, end_date)

    def _get_remaining_working_days_in_month(self, date_obj: date) -> int:
        """Calculate the number of remaining working days in the month from a given date."""
        year = date_obj.year
        month = date_obj.month

        # Determine end date for the month
        if month == 12:
            end_date = datetime(year, month, 31).date()
        else:
            end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)

        return self._count_working_days(date_obj, end_date)

    def calculate_remaining_capacity(self, start_date: date, capacity_per_period: float) -> Tuple[str, float]:
        """Calculate the remaining capacity in the period starting from a given date.

        Args:
            start_date: The start date within the period
            capacity_per_period: Total capacity for the period

        Returns:
            Tuple of (period_string, remaining_capacity)
        """
        period_str, total_working_days, _ = self.get_period_info(start_date)
        remaining_working_days = self.get_remaining_working_days_in_period(start_date)

        # Calculate the remaining capacity based on the proportion of working days left
        remaining_capacity_ratio = remaining_working_days / total_working_days
        remaining_capacity = capacity_per_period * remaining_capacity_ratio

        return period_str, remaining_capacity
