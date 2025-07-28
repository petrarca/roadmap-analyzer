"""Tests for the capacity loader module."""

import os
import tempfile
from datetime import date

import pandas as pd
import pytest

from roadmap_analyzer.capacity import CapacityCalculator, TimePeriodType
from roadmap_analyzer.capacity_loader import (
    create_capacity_dataframe,
    format_period,
    load_capacity_data,
    parse_period,
)
from roadmap_analyzer.config import load_config


@pytest.fixture
def app_config():
    """Create a test app configuration."""
    return load_config()


@pytest.fixture
def test_excel_file():
    """Create a temporary Excel file with test data."""
    # Create a temporary file
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as temp_file:
        temp_path = temp_file.name

    # Create test data
    roadmap_data = pd.DataFrame(
        {
            "Position": [1, 2, 3],
            "Item": ["Project A", "Project B", "Project C"],
            "Due date": ["2025-11-30", "2025-11-30", "2026-05-30"],
            "Dependency": [None, 1, None],
            "Best": [2400, 250, 1400],
            "Likely": [2832, 295, 1652],
            "Worst": [3120, 325, 1820],
        }
    )

    capacity_data = pd.DataFrame(
        {
            "Period": ["2025.Q1", "2025.Q2", "2025.Q3", "2025.Q4", "2026.1", "2026.2", "2026.3"],
            "Capacity": [1500, 1600, 1200, 1400, 500, 550, 600],
        }
    )

    # Write to Excel file with multiple sheets
    with pd.ExcelWriter(temp_path, engine="openpyxl") as writer:
        roadmap_data.to_excel(writer, sheet_name="Roadmap", index=False)
        capacity_data.to_excel(writer, sheet_name="Capacity", index=False)

    yield temp_path

    # Clean up the temporary file
    os.unlink(temp_path)


def test_parse_period():
    """Test parsing period strings."""
    # Test quarterly format
    year, period, period_type = parse_period("2025.Q1")
    assert year == 2025
    assert period == 1
    assert period_type == TimePeriodType.QUARTERLY

    # Test monthly format
    year, period, period_type = parse_period("2025.3")
    assert year == 2025
    assert period == 3
    assert period_type == TimePeriodType.MONTHLY

    # Test invalid formats
    with pytest.raises(ValueError):
        parse_period("invalid")

    with pytest.raises(ValueError):
        parse_period("2025.Q5")  # Invalid quarter

    with pytest.raises(ValueError):
        parse_period("2025.13")  # Invalid month


def test_format_period():
    """Test formatting period strings."""
    # Test quarterly format
    assert format_period(2025, 1, TimePeriodType.QUARTERLY) == "2025-Q1"

    # Test monthly format
    assert format_period(2025, 3, TimePeriodType.MONTHLY) == "2025-03"


def test_load_capacity_data(test_excel_file):
    """Test loading capacity data from Excel."""
    # Test loading capacity data
    capacity_dict = load_capacity_data(test_excel_file)
    assert len(capacity_dict) == 7
    assert capacity_dict["2025-Q1"] == 1500
    assert capacity_dict["2025-Q2"] == 1600
    assert capacity_dict["2025-Q3"] == 1200
    assert capacity_dict["2025-Q4"] == 1400
    assert capacity_dict["2026-01"] == 500
    assert capacity_dict["2026-02"] == 550
    assert capacity_dict["2026-03"] == 600

    # Test loading from non-existent file
    assert load_capacity_data("non_existent_file.xlsx") == {}

    # Test loading from file without Capacity sheet
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as temp_file:
        temp_path = temp_file.name
        pd.DataFrame({"A": [1, 2, 3]}).to_excel(temp_path, index=False)
        assert load_capacity_data(temp_path) == {}
        os.unlink(temp_path)


def test_create_capacity_dataframe(app_config):
    """Test creating capacity dataframe for visualization."""
    # Create test capacity dictionary
    capacity_dict = {
        "2025-Q1": 1500,
        "2025-Q2": 1600,
        "2025-Q3": 1200,
        "2025-Q4": 1400,
    }

    # Test quarterly capacity dataframe
    start_date = date(2025, 1, 1)
    end_date = date(2025, 12, 31)
    period_type = TimePeriodType.QUARTERLY
    default_capacity = 1300

    df = create_capacity_dataframe(capacity_dict, start_date, end_date, period_type, default_capacity)
    assert len(df) == 4
    assert df["Capacity"].tolist() == [1500, 1600, 1200, 1400]
    assert df["Period"].tolist() == ["2025-Q1", "2025-Q2", "2025-Q3", "2025-Q4"]

    # Test monthly capacity dataframe
    capacity_dict = {
        "2025-01": 500,
        "2025-02": 550,
        "2025-03": 600,
    }
    period_type = TimePeriodType.MONTHLY
    default_capacity = 450

    df = create_capacity_dataframe(capacity_dict, start_date, date(2025, 3, 31), period_type, default_capacity)
    assert len(df) == 3
    assert df["Capacity"].tolist() == [500, 550, 600]
    assert df["Period"].tolist() == ["2025-01", "2025-02", "2025-03"]

    # Test with missing periods (should use default capacity)
    capacity_dict = {
        "2025-01": 500,
        # 2025-02 is missing
        "2025-03": 600,
    }

    df = create_capacity_dataframe(capacity_dict, start_date, date(2025, 3, 31), period_type, default_capacity)
    assert len(df) == 3
    assert df["Capacity"].tolist() == [500, default_capacity, 600]


def test_capacity_calculator_integration(app_config, test_excel_file):
    """Test integration of capacity data with CapacityCalculator."""
    # Load capacity data
    capacity_dict = load_capacity_data(test_excel_file)
    assert len(capacity_dict) == 7

    # Create capacity calculator with quarterly periods
    calculator_quarterly = CapacityCalculator(app_config, TimePeriodType.QUARTERLY, capacity_dict)

    # Test that capacity overrides are correctly applied
    period_str, working_days, capacity_per_day = calculator_quarterly.get_period_info(date(2025, 1, 15))
    assert period_str == "2025-Q1"

    # Calculate expected capacity per day (1500 / working days in Q1)
    expected_capacity = 1500 / working_days
    assert abs(capacity_per_day - expected_capacity) < 0.001  # Use approximate equality for floating point

    # Create capacity calculator with monthly periods
    calculator_monthly = CapacityCalculator(app_config, TimePeriodType.MONTHLY, capacity_dict)

    # Test that capacity overrides are correctly applied for monthly periods
    period_str, _, capacity_per_day = calculator_monthly.get_period_info(date(2026, 1, 15))
    assert period_str == "2026-01"

    # Calculate expected capacity per day (500 / working days in Jan 2026)
    working_days = calculator_monthly.get_working_days_in_period(2026, 1)
    expected_capacity = 500 / working_days
    assert capacity_per_day == expected_capacity
