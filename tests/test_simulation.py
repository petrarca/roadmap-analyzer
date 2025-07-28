"""Unit tests for the simulation module."""

import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from roadmap_analyzer.capacity import (
    CapacityCalculator,
    TimePeriodType,
)
from roadmap_analyzer.models import WorkItem
from roadmap_analyzer.simulation import (
    SimulationEngine,
)
from roadmap_analyzer.utils import is_working_day


class TestSimulation(unittest.TestCase):
    """Test cases for the simulation module."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock configuration
        self.mock_config = MagicMock()
        self.mock_config.simulation = MagicMock()
        self.mock_config.simulation.default_capacity_per_quarter = 60

        # Create capacity calculator for dependency injection
        self.capacity_calculator = CapacityCalculator(self.mock_config)

        # Create simulation engine with injected capacity calculator
        self.engine = SimulationEngine(self.mock_config, self.capacity_calculator)

        # Also create an engine with default capacity calculator for testing
        self.engine_default = SimulationEngine(self.mock_config)

        # Sample work item
        self.work_item = WorkItem(
            position=1,
            item="Test Project",
            best_estimate=10,
            most_likely_estimate=15,
            worst_estimate=25,
            due_date=datetime(2024, 6, 30).date(),
            has_dependency=False,
            dependency=None,
        )

    def test_ensure_working_day(self):
        """Test ensure_working_day method."""
        # Test with a Monday (working day)
        monday = datetime(2024, 1, 1).date()  # This is a Monday
        result = self.engine.ensure_working_day(monday)
        self.assertEqual(result, monday)

        # Test with a Saturday (non-working day)
        saturday = datetime(2024, 1, 6).date()  # This is a Saturday
        result = self.engine.ensure_working_day(saturday)
        self.assertTrue(is_working_day(result))

        # Test with a Sunday (non-working day)
        sunday = datetime(2024, 1, 7).date()  # This is a Sunday
        result = self.engine.ensure_working_day(sunday)
        self.assertTrue(is_working_day(result))

    def test_get_working_days_in_quarter(self):
        """Test get_working_days_in_period method for quarters."""
        # Test Q1 2024
        working_days = self.capacity_calculator.get_working_days_in_period(2024, 1)
        self.assertIsInstance(working_days, int)
        self.assertGreater(working_days, 0)
        self.assertLess(working_days, 100)  # Sanity check

    def test_is_working_day(self):
        """Test is_working_day utility function."""
        # Test with a Monday
        monday = datetime(2024, 1, 1).date()
        self.assertTrue(is_working_day(monday))

        # Test with a Saturday
        saturday = datetime(2024, 1, 6).date()
        self.assertFalse(is_working_day(saturday))

        # Test with a Sunday
        sunday = datetime(2024, 1, 7).date()
        self.assertFalse(is_working_day(sunday))

    def test_get_quarter_info(self):
        """Test get_period_info method."""
        test_date = datetime(2024, 2, 15).date()
        quarter_str, working_days, capacity_per_day = self.capacity_calculator.get_period_info(test_date)

        self.assertEqual(quarter_str, "2024-Q1")
        self.assertIsInstance(working_days, int)
        self.assertGreater(working_days, 0)
        self.assertIsInstance(capacity_per_day, float)
        self.assertGreater(capacity_per_day, 0)

    def test_get_working_days_in_quarter_different_quarters(self):
        """Test get_working_days_in_period for different quarters."""
        for quarter in range(1, 5):
            working_days = self.capacity_calculator.get_working_days_in_period(2024, quarter)
            self.assertIsInstance(working_days, int)
            self.assertGreater(working_days, 50)  # Each quarter should have at least 50 working days
            self.assertLess(working_days, 70)  # But not more than 70

    def test_get_remaining_working_days(self):
        """Test get_remaining_working_days_in_period method."""
        # Test from beginning of quarter
        start_of_q1 = datetime(2024, 1, 1).date()
        remaining_days = self.capacity_calculator.get_remaining_working_days_in_period(start_of_q1)
        self.assertIsInstance(remaining_days, int)
        self.assertGreater(remaining_days, 0)

        # Test from middle of quarter
        mid_q1 = datetime(2024, 2, 15).date()
        remaining_mid = self.capacity_calculator.get_remaining_working_days_in_period(mid_q1)
        self.assertIsInstance(remaining_mid, int)
        self.assertGreater(remaining_mid, 0)
        self.assertLess(remaining_mid, remaining_days)  # Should be less than from start

    def test_calculate_remaining_capacity(self):
        """Test calculate_remaining_capacity method."""
        test_date = datetime(2024, 2, 15).date()
        capacity_per_quarter = 60.0
        total_working_days = self.capacity_calculator.get_working_days_in_period(2024, 1)
        remaining_working_days = self.capacity_calculator.get_remaining_working_days_in_period(test_date)

        quarter_str, remaining_capacity = self.capacity_calculator.calculate_remaining_capacity(test_date, capacity_per_quarter)

        self.assertEqual(quarter_str, "2024-Q1")
        self.assertIsInstance(remaining_capacity, float)
        self.assertGreater(remaining_capacity, 0)
        self.assertLessEqual(remaining_capacity, capacity_per_quarter)

        # Check that the calculation is correct
        expected_capacity = capacity_per_quarter * (remaining_working_days / total_working_days)
        self.assertAlmostEqual(remaining_capacity, expected_capacity, places=2)

    @patch("roadmap_analyzer.simulation.triangular_random")
    def test_simple_simulation(self, mock_triangular):
        """Test a simple simulation run."""
        # Mock the triangular random to return a fixed value
        mock_triangular.return_value = 15.0

        start_date = datetime(2024, 1, 1).date()
        capacity_per_quarter = 60
        num_simulations = 1

        # Run simulation
        results = self.engine.run_monte_carlo_simulation([self.work_item], capacity_per_quarter, start_date, num_simulations)

        # Verify results
        self.assertEqual(len(results), 1)
        self.assertEqual(len(results[0].results), 1)

        result = results[0].results[0]
        self.assertEqual(result.name, "Test Project")
        self.assertEqual(result.position, 1)
        self.assertEqual(result.effort, 15.0)
        self.assertIsInstance(result.completion_date, datetime)

        # Verify the mock was called
        mock_triangular.assert_called_once()

    @patch("roadmap_analyzer.simulation.triangular_random")
    def test_dependency_simulation(self, mock_triangular):
        """Test simulation with dependencies."""
        # Mock the triangular random to return fixed values
        mock_triangular.side_effect = [10.0, 20.0]  # First item: 10 days, second item: 20 days

        # Create two work items with dependency
        work_item1 = WorkItem(
            position=1,
            item="Project A",
            best_estimate=8,
            most_likely_estimate=10,
            worst_estimate=15,
            due_date=datetime(2024, 3, 31).date(),
            has_dependency=False,
            dependency=None,
        )

        work_item2 = WorkItem(
            position=2,
            item="Project B",
            best_estimate=15,
            most_likely_estimate=20,
            worst_estimate=30,
            due_date=datetime(2024, 6, 30).date(),
            has_dependency=True,
            dependency=1,  # Depends on Project A
        )

        start_date = datetime(2024, 1, 1).date()
        capacity_per_quarter = 60
        num_simulations = 1

        # Run simulation
        results = self.engine.run_monte_carlo_simulation([work_item1, work_item2], capacity_per_quarter, start_date, num_simulations)

        # Verify results
        self.assertEqual(len(results), 1)
        self.assertEqual(len(results[0].results), 2)

        # Verify efforts match mocked values
        result_a = next(r for r in results[0].results if r.name == "Project A")
        result_b = next(r for r in results[0].results if r.name == "Project B")

        self.assertEqual(result_a.effort, 10.0)
        self.assertEqual(result_b.effort, 20.0)

        # Project B should start after or at the same time as Project A completes
        # (depending on the dependency logic implementation)
        self.assertGreaterEqual(result_b.start_date.date(), result_a.completion_date.date())

        # Verify the mock was called twice
        self.assertEqual(mock_triangular.call_count, 2)

    def test_dependency_injection(self):
        """Test that dependency injection works correctly."""
        # Create a custom capacity calculator with monthly periods
        monthly_calculator = CapacityCalculator(self.mock_config, TimePeriodType.MONTHLY)

        # Create simulation engine with injected calculator
        engine_with_monthly = SimulationEngine(self.mock_config, monthly_calculator)

        # Verify the injected calculator is used
        self.assertIs(engine_with_monthly.capacity_calculator, monthly_calculator)
        self.assertEqual(engine_with_monthly.capacity_calculator.period_type, TimePeriodType.MONTHLY)

        # Test that default engine uses quarterly calculator
        self.assertEqual(self.engine_default.capacity_calculator.period_type, TimePeriodType.QUARTERLY)

        # Test that our main test engine uses the injected calculator
        self.assertIs(self.engine.capacity_calculator, self.capacity_calculator)
        self.assertEqual(self.engine.capacity_calculator.period_type, TimePeriodType.QUARTERLY)

    def test_default_capacity_calculator_creation(self):
        """Test that default capacity calculator is created when none is provided."""
        # Create engine without capacity calculator (should use default)
        default_engine = SimulationEngine(self.mock_config)

        # Verify default calculator is created
        self.assertIsInstance(default_engine.capacity_calculator, CapacityCalculator)
        self.assertEqual(default_engine.capacity_calculator.period_type, TimePeriodType.QUARTERLY)
        self.assertEqual(default_engine.capacity_calculator.config, self.mock_config)


if __name__ == "__main__":
    unittest.main()
