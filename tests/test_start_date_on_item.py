"""Test the optional start date feature for work items."""

from datetime import date, datetime

import pytest

from roadmap_analyzer.capacity import CapacityCalculator, TimePeriodType
from roadmap_analyzer.config import AppConfig
from roadmap_analyzer.models import WorkItem
from roadmap_analyzer.simulation import SimulationEngine


@pytest.fixture
def config():
    """Create a test configuration."""
    return AppConfig()


@pytest.fixture
def capacity_calculator(config):
    """Create a test capacity calculator."""
    return CapacityCalculator(config, TimePeriodType.QUARTERLY)


@pytest.fixture
def simulation_engine(config, capacity_calculator):
    """Create a test simulation engine."""
    return SimulationEngine(config, capacity_calculator)


def test_start_date_respected_when_no_dependency():
    """Test that start date is respected when there's no dependency."""
    config = AppConfig()
    capacity_calculator = CapacityCalculator(config, TimePeriodType.QUARTERLY)
    simulation_engine = SimulationEngine(config, capacity_calculator)

    # Create work item with start date later than project start
    work_item = WorkItem(
        position=1,
        item="Test Task",
        due_date=datetime(2024, 6, 1),
        start_date=datetime(2024, 3, 15),  # Start date specified
        best_estimate=5.0,
        most_likely_estimate=10.0,
        worst_estimate=15.0,
    )

    project_start = date(2024, 3, 1)  # Earlier than work item start date

    # Reset state and determine start date
    simulation_engine._reset_state()
    actual_start = simulation_engine._determine_start_date(work_item, project_start)

    # Should use work item start date (converted to date and ensured working day)
    expected_start = date(2024, 3, 15)  # Friday, should remain the same
    assert actual_start == expected_start


def test_start_date_ignored_when_earlier_than_project_start():
    """Test that start date is ignored when it's earlier than project start."""
    config = AppConfig()
    capacity_calculator = CapacityCalculator(config, TimePeriodType.QUARTERLY)
    simulation_engine = SimulationEngine(config, capacity_calculator)

    # Create work item with start date earlier than project start
    work_item = WorkItem(
        position=1,
        item="Test Task",
        due_date=datetime(2024, 6, 1),
        start_date=datetime(2024, 2, 15),  # Earlier than project start
        best_estimate=5.0,
        most_likely_estimate=10.0,
        worst_estimate=15.0,
    )

    project_start = date(2024, 3, 1)  # Later than work item start date

    # Reset state and determine start date
    simulation_engine._reset_state()
    actual_start = simulation_engine._determine_start_date(work_item, project_start)

    # Should use project start date
    assert actual_start == project_start


def test_dependency_overrides_start_date():
    """Test that dependency completion date overrides start date when later."""
    config = AppConfig()
    capacity_calculator = CapacityCalculator(config, TimePeriodType.QUARTERLY)
    simulation_engine = SimulationEngine(config, capacity_calculator)

    # Create work item with dependency and start date
    work_item = WorkItem(
        position=2,
        item="Dependent Task",
        due_date=datetime(2024, 6, 1),
        start_date=datetime(2024, 3, 15),  # Earlier than dependency completion
        dependency=1,  # Depends on position 1
        best_estimate=5.0,
        most_likely_estimate=10.0,
        worst_estimate=15.0,
    )

    project_start = date(2024, 3, 1)
    dependency_completion = date(2024, 4, 1)  # Later than start date

    # Set up completion dates (simulate dependency already completed)
    simulation_engine._reset_state()
    simulation_engine.completion_dates[1] = dependency_completion

    actual_start = simulation_engine._determine_start_date(work_item, project_start)

    # Should use dependency completion date (ensured working day)
    expected_start = date(2024, 4, 1)  # Monday, should remain the same
    assert actual_start == expected_start


def test_start_date_overrides_dependency_when_later():
    """Test that start date overrides dependency completion when start date is later."""
    config = AppConfig()
    capacity_calculator = CapacityCalculator(config, TimePeriodType.QUARTERLY)
    simulation_engine = SimulationEngine(config, capacity_calculator)

    # Create work item with dependency and start date
    work_item = WorkItem(
        position=2,
        item="Dependent Task",
        due_date=datetime(2024, 6, 1),
        start_date=datetime(2024, 4, 15),  # Later than dependency completion
        dependency=1,  # Depends on position 1
        best_estimate=5.0,
        most_likely_estimate=10.0,
        worst_estimate=15.0,
    )

    project_start = date(2024, 3, 1)
    dependency_completion = date(2024, 4, 1)  # Earlier than start date

    # Set up completion dates (simulate dependency already completed)
    simulation_engine._reset_state()
    simulation_engine.completion_dates[1] = dependency_completion

    actual_start = simulation_engine._determine_start_date(work_item, project_start)

    # Should use work item start date (ensured working day)
    expected_start = date(2024, 4, 15)  # Monday, should remain the same
    assert actual_start == expected_start


def test_no_start_date_uses_default_logic():
    """Test that when no start date is specified, default logic is used."""
    config = AppConfig()
    capacity_calculator = CapacityCalculator(config, TimePeriodType.QUARTERLY)
    simulation_engine = SimulationEngine(config, capacity_calculator)

    # Create work item without start date
    work_item = WorkItem(
        position=1,
        item="Test Task",
        due_date=datetime(2024, 6, 1),
        # start_date=None (default)
        best_estimate=5.0,
        most_likely_estimate=10.0,
        worst_estimate=15.0,
    )

    project_start = date(2024, 3, 1)

    # Reset state and determine start date
    simulation_engine._reset_state()
    actual_start = simulation_engine._determine_start_date(work_item, project_start)

    # Should use project start date
    assert actual_start == project_start


def test_start_date_ensures_working_day():
    """Test that start date is adjusted to working day if needed."""
    config = AppConfig()
    capacity_calculator = CapacityCalculator(config, TimePeriodType.QUARTERLY)
    simulation_engine = SimulationEngine(config, capacity_calculator)

    # Create work item with start date on weekend (Saturday)
    work_item = WorkItem(
        position=1,
        item="Test Task",
        due_date=datetime(2024, 6, 1),
        start_date=datetime(2024, 3, 16),  # Saturday
        best_estimate=5.0,
        most_likely_estimate=10.0,
        worst_estimate=15.0,
    )

    project_start = date(2024, 3, 1)

    # Reset state and determine start date
    simulation_engine._reset_state()
    actual_start = simulation_engine._determine_start_date(work_item, project_start)

    # Should be adjusted to next Monday
    expected_start = date(2024, 3, 18)  # Monday
    assert actual_start == expected_start
