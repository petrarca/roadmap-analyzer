"""Unit tests for the simulation module."""

import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from roadmap_analyzer.config import SimulationConfig
from roadmap_analyzer.models import WorkItem
from roadmap_analyzer.simulation import (
    calculate_remaining_capacity,
    ensure_working_day,
    get_quarter_info,
    get_remaining_working_days_in_quarter,
    get_working_days_in_quarter,
    run_monte_carlo_simulation,
)
from roadmap_analyzer.utils import is_working_day


class TestSimulation(unittest.TestCase):
    """Test cases for simulation functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a test configuration
        sim_config = SimulationConfig(
            default_capacity_per_quarter=100,  # Simple value for testing
            working_days_per_quarter=65,
        )
        self.config = MagicMock()
        self.config.simulation = sim_config

        # Create test work items
        self.work_item1 = WorkItem(
            position=1,
            initiative="Test Item 1",
            due_date=datetime(2025, 12, 31).date(),
            best_estimate=5.0,
            most_likely_estimate=10.0,
            worst_estimate=15.0,
            dependency=None,
        )

        self.work_item2 = WorkItem(
            position=2,
            initiative="Test Item 2",
            due_date=datetime(2026, 3, 31).date(),
            best_estimate=8.0,
            most_likely_estimate=12.0,
            worst_estimate=20.0,
            dependency=1,  # Depends on work_item1
        )

    def test_is_working_day(self):
        """Test is_working_day function."""
        # Monday (should be a working day)
        monday = datetime(2025, 7, 28).date()  # July 28, 2025 is a Monday
        self.assertTrue(is_working_day(monday))

        # Friday (should be a working day)
        friday = datetime(2025, 8, 1).date()  # August 1, 2025 is a Friday
        self.assertTrue(is_working_day(friday))

        # Saturday (should not be a working day)
        saturday = datetime(2025, 8, 2).date()  # August 2, 2025 is a Saturday
        self.assertFalse(is_working_day(saturday))

        # Sunday (should not be a working day)
        sunday = datetime(2025, 8, 3).date()  # August 3, 2025 is a Sunday
        self.assertFalse(is_working_day(sunday))

    def test_ensure_working_day(self):
        """Test ensure_working_day function."""
        # If given a working day, should return the same day
        monday = datetime(2025, 7, 28).date()  # Monday
        self.assertEqual(ensure_working_day(monday), monday)

        # If given a weekend day, should return the next working day (Monday)
        saturday = datetime(2025, 8, 2).date()  # Saturday
        expected_monday = datetime(2025, 8, 4).date()  # Next Monday
        self.assertEqual(ensure_working_day(saturday), expected_monday)

        sunday = datetime(2025, 8, 3).date()  # Sunday
        self.assertEqual(ensure_working_day(sunday), expected_monday)

    def test_get_working_days_in_quarter(self):
        """Test get_working_days_in_quarter function."""
        # Q3 2025 (July-September)
        # This will vary by year but we can calculate it manually for verification
        q3_working_days = get_working_days_in_quarter(2025, 3)

        # Manual calculation for Q3 2025
        start_date = datetime(2025, 7, 1).date()
        end_date = datetime(2025, 9, 30).date()

        working_days = 0
        current = start_date
        while current <= end_date:
            if is_working_day(current):
                working_days += 1
            current += timedelta(days=1)

        self.assertEqual(q3_working_days, working_days)

    def test_get_quarter_info(self):
        """Test get_quarter_info function."""
        # Test with a date in Q3 2025
        test_date = datetime(2025, 8, 15).date()  # August 15, 2025
        quarter_str, working_days, capacity_per_day = get_quarter_info(test_date, self.config)

        # Verify quarter string
        self.assertEqual(quarter_str, "2025-Q3")

        # Verify working days matches our calculation
        calculated_working_days = get_working_days_in_quarter(2025, 3)
        self.assertEqual(working_days, calculated_working_days)

        # Verify capacity per working day
        expected_capacity_per_day = 100 / calculated_working_days  # 100 is our test capacity
        self.assertEqual(capacity_per_day, expected_capacity_per_day)

    def test_get_remaining_working_days(self):
        """Test get_remaining_working_days_in_quarter function."""
        # Start from August 15, 2025 (in Q3)
        start_date = datetime(2025, 8, 15).date()
        end_date = datetime(2025, 9, 30).date()  # End of Q3

        # Calculate manually
        working_days = 0
        current = start_date
        while current <= end_date:
            if is_working_day(current):
                working_days += 1
            current += timedelta(days=1)

        # Compare with function
        calculated_days = get_remaining_working_days_in_quarter(start_date)
        self.assertEqual(calculated_days, working_days)

    def test_calculate_remaining_capacity(self):
        """Test calculate_remaining_capacity function."""
        # Start from August 15, 2025 (in Q3)
        start_date = datetime(2025, 8, 15).date()
        capacity_per_quarter = 100  # Use the same value as in the test config

        # Get remaining working days
        remaining_days = get_remaining_working_days_in_quarter(start_date)

        # Calculate expected capacity
        total_working_days = get_working_days_in_quarter(2025, 3)
        capacity_per_day = capacity_per_quarter / total_working_days
        expected_capacity = remaining_days * capacity_per_day

        # Compare with function
        quarter_str, calculated_capacity = calculate_remaining_capacity(start_date, capacity_per_quarter)
        self.assertEqual(quarter_str, "2025-Q3")
        self.assertEqual(calculated_capacity, expected_capacity)

    @patch("roadmap_analyzer.simulation.triangular_random")
    def test_simple_simulation(self, mock_triangular):
        """Test a simple simulation with one work item."""
        # Set up the mock to return a fixed value
        mock_triangular.return_value = 10.0

        # Create a simple work item with slightly different estimates
        # to avoid the triangular distribution error
        work_item = WorkItem(
            position=1,
            initiative="Simple Test",
            due_date=datetime(2025, 12, 31).date(),
            best_estimate=9.0,
            most_likely_estimate=10.0,
            worst_estimate=11.0,
            dependency=None,
        )

        # Run a single simulation
        start_date = datetime(2025, 8, 1).date()  # Friday
        results = run_monte_carlo_simulation(
            work_items=[work_item],
            capacity_per_quarter=100,
            start_date=start_date,
            num_simulations=1,
            config=self.config,
        )

        # Check results
        self.assertEqual(len(results), 1)
        self.assertEqual(len(results[0].results), 1)

        result = results[0].results[0]
        self.assertEqual(result.effort, 10.0)

        # Calculate expected completion date
        # With capacity of 100 per quarter and working days calculated from our function
        working_days = get_working_days_in_quarter(2025, 3)
        capacity_per_day = 100 / working_days

        # 10 effort units / capacity_per_day = number of working days needed
        days_needed = int(10.0 / capacity_per_day)
        expected_completion = start_date
        for _ in range(days_needed):
            expected_completion = expected_completion + timedelta(days=1)
            while not is_working_day(expected_completion):
                expected_completion = expected_completion + timedelta(days=1)

        # Compare completion dates (might be off by 1 day due to rounding)
        completion_diff = abs((result.completion_date.date() - expected_completion).days)
        self.assertLessEqual(completion_diff, 1)

    @patch("roadmap_analyzer.simulation.triangular_random")
    def test_dependency_simulation(self, mock_triangular):
        """Test simulation with dependencies."""
        # Set up the mock to return specific values for each call
        mock_triangular.side_effect = [4.0, 7.0]  # First call for work_item1, second for work_item2

        # Create two work items with dependencies and slightly different estimates
        work_item1 = WorkItem(
            position=1,
            initiative="First Item",
            due_date=datetime(2025, 12, 31).date(),
            best_estimate=4.0,
            most_likely_estimate=5.0,
            worst_estimate=6.0,
            dependency=None,
        )

        work_item2 = WorkItem(
            position=2,
            initiative="Second Item",
            due_date=datetime(2026, 3, 31).date(),
            best_estimate=7.0,
            most_likely_estimate=8.0,
            worst_estimate=9.0,
            dependency=1,  # Depends on work_item1
        )

        # Run a single simulation
        start_date = datetime(2025, 8, 1).date()  # Friday
        results = run_monte_carlo_simulation(
            work_items=[work_item1, work_item2],
            capacity_per_quarter=100,
            start_date=start_date,
            num_simulations=1,
            config=self.config,
        )

        # Check results
        self.assertEqual(len(results), 1)
        self.assertEqual(len(results[0].results), 2)

        # Get results for both items
        result1 = next(r for r in results[0].results if r.position == 1)
        result2 = next(r for r in results[0].results if r.position == 2)

        # Verify efforts
        self.assertEqual(result1.effort, 4.0)
        self.assertEqual(result2.effort, 7.0)

        # Verify dependency: item2 should start after item1 completes
        self.assertEqual(result2.start_date.date(), result1.completion_date.date())


if __name__ == "__main__":
    unittest.main()
