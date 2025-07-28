"""Tests for the capacity calculation module."""

from datetime import date
from unittest.mock import Mock

import pytest

from roadmap_analyzer.capacity import (
    CapacityCalculator,
    TimePeriodType,
)
from roadmap_analyzer.config import AppConfig


class TestCapacityCalculator:
    """Test cases for the CapacityCalculator class."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration for testing."""
        config = Mock(spec=AppConfig)
        config.simulation = Mock()
        config.simulation.default_capacity_per_quarter = 60.0
        return config

    @pytest.fixture
    def quarterly_calculator(self, mock_config):
        """Create a quarterly capacity calculator for testing."""
        return CapacityCalculator(mock_config, TimePeriodType.QUARTERLY)

    @pytest.fixture
    def monthly_calculator(self, mock_config):
        """Create a monthly capacity calculator for testing."""
        return CapacityCalculator(mock_config, TimePeriodType.MONTHLY)

    def test_quarterly_calculator_initialization(self, mock_config):
        """Test that quarterly calculator initializes correctly."""
        calculator = CapacityCalculator(mock_config, TimePeriodType.QUARTERLY)
        assert calculator.config == mock_config
        assert calculator.period_type == TimePeriodType.QUARTERLY
        assert calculator._capacity_overrides == {}

    def test_monthly_calculator_initialization(self, mock_config):
        """Test that monthly calculator initializes correctly."""
        calculator = CapacityCalculator(mock_config, TimePeriodType.MONTHLY)
        assert calculator.config == mock_config
        assert calculator.period_type == TimePeriodType.MONTHLY
        assert calculator._capacity_overrides == {}

    def test_capacity_override(self, quarterly_calculator):
        """Test setting and using capacity overrides."""
        quarterly_calculator.set_capacity_override("2024-Q1", 80.0)
        assert quarterly_calculator._capacity_overrides["2024-Q1"] == 80.0

        # Test multiple overrides
        quarterly_calculator.set_capacity_override("2024-Q2", 90.0)
        assert len(quarterly_calculator._capacity_overrides) == 2
        assert quarterly_calculator._capacity_overrides["2024-Q2"] == 90.0

    def test_get_working_days_in_quarter(self, quarterly_calculator):
        """Test calculation of working days in quarters."""
        # Q1 2024 (Jan-Mar): Should have working days
        working_days_q1 = quarterly_calculator.get_working_days_in_period(2024, 1)
        assert isinstance(working_days_q1, int)
        assert working_days_q1 > 0

        # Q2 2024 (Apr-Jun)
        working_days_q2 = quarterly_calculator.get_working_days_in_period(2024, 2)
        assert isinstance(working_days_q2, int)
        assert working_days_q2 > 0

        # Q4 2024 (Oct-Dec) - includes year end
        working_days_q4 = quarterly_calculator.get_working_days_in_period(2024, 4)
        assert isinstance(working_days_q4, int)
        assert working_days_q4 > 0

    def test_get_working_days_in_month(self, monthly_calculator):
        """Test calculation of working days in months."""
        # January 2024
        working_days_jan = monthly_calculator.get_working_days_in_period(2024, 1)
        assert isinstance(working_days_jan, int)
        assert working_days_jan > 0

        # February 2024 (leap year)
        working_days_feb = monthly_calculator.get_working_days_in_period(2024, 2)
        assert isinstance(working_days_feb, int)
        assert working_days_feb > 0

        # December 2024
        working_days_dec = monthly_calculator.get_working_days_in_period(2024, 12)
        assert isinstance(working_days_dec, int)
        assert working_days_dec > 0

    def test_unsupported_period_type(self, mock_config):
        """Test that unsupported period types raise errors."""
        calculator = CapacityCalculator(mock_config, TimePeriodType.QUARTERLY)
        calculator.period_type = "invalid"  # Simulate invalid period type

        with pytest.raises(ValueError, match="Unsupported period type"):
            calculator.get_working_days_in_period(2024, 1)

    def test_get_quarter_info(self, quarterly_calculator):
        """Test getting quarter information."""
        test_date = date(2024, 2, 15)  # Q1 2024
        period_str, working_days, capacity_per_day = quarterly_calculator.get_period_info(test_date)

        assert period_str == "2024-Q1"
        assert isinstance(working_days, int)
        assert working_days > 0
        assert isinstance(capacity_per_day, float)
        assert capacity_per_day > 0

    def test_get_quarter_info_with_override(self, quarterly_calculator):
        """Test getting quarter information with capacity override."""
        test_date = date(2024, 2, 15)  # Q1 2024
        quarterly_calculator.set_capacity_override("2024-Q1", 100.0)

        period_str, working_days, capacity_per_day = quarterly_calculator.get_period_info(test_date)

        assert period_str == "2024-Q1"
        expected_capacity_per_day = 100.0 / working_days
        assert abs(capacity_per_day - expected_capacity_per_day) < 0.01

    def test_get_month_info(self, monthly_calculator):
        """Test getting month information."""
        test_date = date(2024, 2, 15)  # February 2024
        period_str, working_days, capacity_per_day = monthly_calculator.get_period_info(test_date)

        assert period_str == "2024-02"
        assert isinstance(working_days, int)
        assert working_days > 0
        assert isinstance(capacity_per_day, float)
        assert capacity_per_day > 0

    def test_get_month_info_with_override(self, monthly_calculator):
        """Test getting month information with capacity override."""
        test_date = date(2024, 2, 15)  # February 2024
        monthly_calculator.set_capacity_override("2024-02", 25.0)

        period_str, working_days, capacity_per_day = monthly_calculator.get_period_info(test_date)

        assert period_str == "2024-02"
        expected_capacity_per_day = 25.0 / working_days
        assert abs(capacity_per_day - expected_capacity_per_day) < 0.01

    def test_get_remaining_working_days_in_quarter(self, quarterly_calculator):
        """Test calculation of remaining working days in quarter."""
        # Test from beginning of quarter
        start_of_q1 = date(2024, 1, 1)
        remaining_days = quarterly_calculator.get_remaining_working_days_in_period(start_of_q1)
        total_days = quarterly_calculator.get_working_days_in_period(2024, 1)

        # Remaining days should be close to total days (accounting for Jan 1 being a holiday)
        assert remaining_days <= total_days
        assert remaining_days > 0

        # Test from middle of quarter
        mid_q1 = date(2024, 2, 15)
        remaining_mid = quarterly_calculator.get_remaining_working_days_in_period(mid_q1)
        assert remaining_mid < remaining_days
        assert remaining_mid > 0

    def test_get_remaining_working_days_in_month(self, monthly_calculator):
        """Test calculation of remaining working days in month."""
        # Test from beginning of month
        start_of_month = date(2024, 2, 1)
        remaining_days = monthly_calculator.get_remaining_working_days_in_period(start_of_month)
        total_days = monthly_calculator.get_working_days_in_period(2024, 2)

        assert remaining_days <= total_days
        assert remaining_days > 0

        # Test from middle of month
        mid_month = date(2024, 2, 15)
        remaining_mid = monthly_calculator.get_remaining_working_days_in_period(mid_month)
        assert remaining_mid < remaining_days
        assert remaining_mid > 0

    def test_calculate_remaining_capacity(self, quarterly_calculator):
        """Test calculation of remaining capacity."""
        test_date = date(2024, 2, 15)
        capacity_per_quarter = 60.0

        period_str, remaining_capacity = quarterly_calculator.calculate_remaining_capacity(test_date, capacity_per_quarter)

        assert period_str == "2024-Q1"
        assert isinstance(remaining_capacity, float)
        assert 0 < remaining_capacity <= capacity_per_quarter

    def test_calculate_remaining_capacity_start_of_period(self, quarterly_calculator):
        """Test remaining capacity calculation at start of period."""
        start_of_q2 = date(2024, 4, 1)
        capacity_per_quarter = 60.0

        period_str, remaining_capacity = quarterly_calculator.calculate_remaining_capacity(start_of_q2, capacity_per_quarter)

        assert period_str == "2024-Q2"
        # Should be close to full capacity at start of quarter
        assert remaining_capacity > capacity_per_quarter * 0.9


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration for testing."""
        config = Mock(spec=AppConfig)
        config.simulation = Mock()
        config.simulation.default_capacity_per_quarter = 60.0
        return config

    def test_leap_year_february(self, mock_config):
        """Test calculations for February in a leap year."""
        calculator = CapacityCalculator(mock_config, TimePeriodType.MONTHLY)

        # 2024 is a leap year
        working_days_2024 = calculator.get_working_days_in_period(2024, 2)
        # 2023 is not a leap year
        working_days_2023 = calculator.get_working_days_in_period(2023, 2)

        # Both should be positive, but 2024 might have one more working day
        assert working_days_2024 > 0
        assert working_days_2023 > 0

    def test_year_end_quarter(self, mock_config):
        """Test Q4 calculations that span year end."""
        calculator = CapacityCalculator(mock_config, TimePeriodType.QUARTERLY)

        working_days_q4 = calculator.get_working_days_in_period(2024, 4)
        assert working_days_q4 > 0

        # Test getting info for December date
        dec_date = date(2024, 12, 15)
        period_str, working_days, capacity_per_day = calculator.get_period_info(dec_date)
        assert period_str == "2024-Q4"
        assert working_days == working_days_q4

    def test_zero_capacity_override(self, mock_config):
        """Test behavior with zero capacity override."""
        calculator = CapacityCalculator(mock_config, TimePeriodType.QUARTERLY)
        calculator.set_capacity_override("2024-Q1", 0.0)

        test_date = date(2024, 1, 15)
        period_str, working_days, capacity_per_day = calculator.get_period_info(test_date)

        assert capacity_per_day == 0.0

    def test_very_high_capacity_override(self, mock_config):
        """Test behavior with very high capacity override."""
        calculator = CapacityCalculator(mock_config, TimePeriodType.QUARTERLY)
        calculator.set_capacity_override("2024-Q1", 10000.0)

        test_date = date(2024, 1, 15)
        period_str, working_days, capacity_per_day = calculator.get_period_info(test_date)

        assert capacity_per_day > 100.0  # Should be very high

    def test_end_of_period_remaining_capacity(self, mock_config):
        """Test remaining capacity calculation at end of period."""
        calculator = CapacityCalculator(mock_config, TimePeriodType.QUARTERLY)

        # Last day of Q1
        end_of_q1 = date(2024, 3, 29)  # Assuming this is a working day
        period_str, remaining_capacity = calculator.calculate_remaining_capacity(end_of_q1, 60.0)

        # Should have very little remaining capacity
        assert remaining_capacity < 10.0


if __name__ == "__main__":
    pytest.main([__file__])
