"""Monte Carlo simulation for project roadmap analysis."""

from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional, Tuple

import pandas as pd

from roadmap_analyzer.config import AppConfig
from roadmap_analyzer.models import SimulationResult, SimulationRun, SimulationStats, WorkItem
from roadmap_analyzer.utils import (
    add_working_days,
    convert_to_date,
    get_quarter_from_date,
    is_working_day,
    triangular_random,
)


def get_working_days_in_quarter(year: int, quarter: int) -> int:
    """Calculate the number of working days in a specific quarter.

    Args:
        year: The year
        quarter: The quarter (1-4)

    Returns:
        Number of working days in the quarter
    """
    # Determine start and end dates for the quarter
    start_month = (quarter - 1) * 3 + 1
    end_month = quarter * 3

    start_date = datetime(year, start_month, 1).date()
    if end_month == 12:
        end_date = datetime(year, end_month, 31).date()
    else:
        end_date = datetime(year, end_month + 1, 1).date() - timedelta(days=1)

    # Count working days
    working_days = 0
    current_date = start_date
    while current_date <= end_date:
        if is_working_day(current_date):
            working_days += 1
        current_date += timedelta(days=1)

    return working_days


def get_quarter_info(date_obj: datetime.date, config: AppConfig) -> Tuple[str, int, float]:
    """Get quarter information including capacity per working day.

    Args:
        date_obj: The date to get quarter info for
        config: Application configuration

    Returns:
        Tuple of (quarter_string, working_days_in_quarter, capacity_per_working_day)
    """
    quarter_str = get_quarter_from_date(date_obj)
    year = date_obj.year
    quarter = (date_obj.month - 1) // 3 + 1

    working_days = get_working_days_in_quarter(year, quarter)
    capacity_per_working_day = config.simulation.default_capacity_per_quarter / working_days

    return quarter_str, working_days, capacity_per_working_day


def get_remaining_working_days_in_quarter(date_obj: datetime.date) -> int:
    """Calculate the number of remaining working days in the quarter from a given date.

    Args:
        date_obj: The starting date

    Returns:
        Number of remaining working days in the quarter (including the start date if it's a working day)
    """
    year = date_obj.year
    quarter = (date_obj.month - 1) // 3 + 1

    # Determine end date for the quarter
    end_month = quarter * 3
    if end_month == 12:
        end_date = datetime(year, end_month, 31).date()
    else:
        end_date = datetime(year, end_month + 1, 1).date() - timedelta(days=1)

    # Count working days
    working_days = 0
    current_date = date_obj
    while current_date <= end_date:
        if is_working_day(current_date):
            working_days += 1
        current_date += timedelta(days=1)

    return working_days


def ensure_working_day(date_obj: datetime.date) -> datetime.date:
    """Ensure the given date is a working day (Mon-Fri).
    If it's not, return the next working day.

    Args:
        date_obj: The date to check

    Returns:
        A working day (either the same date or the next working day)
    """
    current_date = date_obj
    while not is_working_day(current_date):
        current_date += timedelta(days=1)
    return current_date


def calculate_remaining_capacity(start_date: datetime.date, capacity_per_quarter: float) -> Tuple[str, float]:
    """Calculate the remaining capacity in the quarter starting from a given date.

    Args:
        start_date: The start date within the quarter
        capacity_per_quarter: Total capacity for the quarter

    Returns:
        Tuple of (quarter_string, remaining_capacity)

    The remaining capacity is calculated as:
    [remaining capacity] = [remaining working days from start date] / [total working days in quarter] * [capacity_per_quarter]
    """
    quarter_str = get_quarter_from_date(start_date)
    year = start_date.year
    quarter = (start_date.month - 1) // 3 + 1

    # Get total working days in the quarter
    total_working_days = get_working_days_in_quarter(year, quarter)

    # Get remaining working days in the quarter (including the start date if it's a working day)
    remaining_working_days = get_remaining_working_days_in_quarter(start_date)

    # Calculate the remaining capacity based on the proportion of working days left
    remaining_capacity_ratio = remaining_working_days / total_working_days
    remaining_capacity = capacity_per_quarter * remaining_capacity_ratio

    return quarter_str, remaining_capacity


def _simulate_single_work_item(
    work_item: WorkItem,
    start_date: datetime.date,
    capacity_per_quarter: int,
    completion_dates: Dict[int, datetime.date],
    capacity_usage: Dict[str, float],
    config: AppConfig,
) -> SimulationResult:
    """Simulate a single work item and calculate its completion date.

    Args:
        work_item: The work item to simulate
        start_date: The overall project start date
        capacity_per_quarter: Available capacity per quarter
        completion_dates: Dictionary of completion dates for dependencies
        capacity_usage: Dictionary tracking capacity usage by quarter
        config: Application configuration

    Returns:
        SimulationResult for the work item
    """
    # Sample effort from triangular distribution
    effort = triangular_random(work_item.best_estimate, work_item.most_likely_estimate, work_item.worst_estimate)

    # Determine start date considering dependencies
    project_start_date = _determine_start_date(work_item, start_date, completion_dates)

    # Calculate completion date based on effort and capacity
    completion_date = _calculate_completion_date(project_start_date, effort, capacity_per_quarter, capacity_usage, config)

    # Store the completion date for potential dependencies
    completion_dates[work_item.position] = completion_date

    # Create and return a SimulationResult object
    return SimulationResult(
        name=work_item.initiative,
        position=work_item.position,
        effort=effort,
        start_date=project_start_date,
        completion_date=completion_date,
        due_date=work_item.due_date,
        on_time=convert_to_date(completion_date) <= convert_to_date(work_item.due_date),
    )


def _determine_start_date(work_item: WorkItem, default_start_date: datetime.date, completion_dates: Dict[int, datetime.date]) -> datetime.date:
    """Determine the start date for a work item considering dependencies.

    Args:
        work_item: The work item to determine start date for
        default_start_date: The default project start date
        completion_dates: Dictionary of completion dates for dependencies

    Returns:
        The start date for the work item
    """
    project_start_date = default_start_date

    if work_item.has_dependency:
        dep_completion = completion_dates.get(work_item.dependency)
        if dep_completion and dep_completion > project_start_date:
            # Ensure the dependency completion date is a working day
            project_start_date = ensure_working_day(dep_completion)

    return project_start_date


def _calculate_completion_date(
    start_date: datetime.date,
    effort: float,
    capacity_per_quarter: int,
    capacity_usage: Dict[str, float],
    config: AppConfig,
) -> datetime.date:
    """Calculate the completion date for a work item based on effort and capacity.

    Args:
        start_date: The start date for the work item
        effort: The effort required for the work item
        capacity_per_quarter: Available capacity per quarter
        capacity_usage: Dictionary tracking capacity usage by quarter
        config: Application configuration

    Returns:
        The completion date for the work item
    """
    remaining_effort = effort
    current_date = start_date

    while remaining_effort > 0:
        # Get quarter information and working days in quarter
        quarter_str, working_days_in_quarter = get_quarter_info(current_date, config)[:2]

        # Calculate available capacity for this quarter
        available_capacity = _get_available_capacity(quarter_str, current_date, capacity_per_quarter, capacity_usage)

        # Determine how much effort can be completed in this quarter
        effort_this_quarter = min(remaining_effort, available_capacity)
        capacity_usage[quarter_str] += effort_this_quarter
        remaining_effort -= effort_this_quarter

        if remaining_effort > 0:
            # Move to next quarter if more effort remains
            current_date = _move_to_next_quarter(current_date)
        else:
            # Calculate exact completion date within this quarter
            current_date = _calculate_exact_completion_date(current_date, effort_this_quarter, capacity_per_quarter, working_days_in_quarter)

    return current_date


def _get_available_capacity(
    quarter_str: str,
    current_date: datetime.date,
    capacity_per_quarter: int,
    capacity_usage: Dict[str, float],
) -> float:
    """Get the available capacity for a quarter.

    Args:
        quarter_str: The quarter string identifier
        current_date: The current date within the quarter
        capacity_per_quarter: Total capacity for the quarter
        capacity_usage: Dictionary tracking capacity usage by quarter

    Returns:
        Available capacity for the quarter
    """
    if quarter_str not in capacity_usage:
        # For the first quarter of a work item, calculate remaining capacity
        _, remaining_capacity = calculate_remaining_capacity(current_date, capacity_per_quarter)
        capacity_usage[quarter_str] = 0
        return remaining_capacity
    else:
        # For subsequent quarters, use remaining capacity
        return capacity_per_quarter - capacity_usage[quarter_str]


def _move_to_next_quarter(current_date: datetime.date) -> datetime.date:
    """Move to the first working day of the next quarter.

    Args:
        current_date: The current date

    Returns:
        The first working day of the next quarter
    """
    if current_date.month >= 10:
        # Move to Q1 of next year
        next_date = datetime(current_date.year + 1, 1, 1).date()
    else:
        # Move to next quarter in same year
        next_month = ((current_date.month - 1) // 3) * 3 + 4  # First month of next quarter
        next_date = datetime(current_date.year, next_month, 1).date()

    # Ensure it's a working day
    return ensure_working_day(next_date)


def _calculate_exact_completion_date(
    current_date: datetime.date,
    effort_this_quarter: float,
    capacity_per_quarter: float,
    working_days_in_quarter: int,
) -> datetime.date:
    """Calculate the exact completion date within a quarter.

    Args:
        current_date: The current date
        effort_this_quarter: The effort to be completed in this quarter
        capacity_per_quarter: Total capacity for the quarter
        working_days_in_quarter: Number of working days in the quarter

    Returns:
        The exact completion date
    """
    # Calculate how many working days are needed to complete the remaining effort
    effort_portion = effort_this_quarter / capacity_per_quarter
    working_days_needed = round(effort_portion * working_days_in_quarter)

    # Add these working days to the current date
    if working_days_needed > 0:
        return add_working_days(current_date, working_days_needed)
    return current_date


def run_monte_carlo_simulation(
    work_items: List[WorkItem],
    capacity_per_quarter: int,
    start_date: datetime.date,
    num_simulations: int,
    config: AppConfig,
    progress_callback: Optional[Callable[[float, str], None]] = None,
) -> List[SimulationRun]:
    """Run Monte Carlo simulation for project timeline using WorkItem objects.

    Args:
        work_items: List of WorkItem objects to simulate
        capacity_per_quarter: Available capacity per quarter in person-days
        start_date: Project start date
        num_simulations: Number of simulation runs
        config: Application configuration
        progress_callback: Optional callback function to report progress

    Returns:
        List of simulation results for each run
    """
    simulation_results = []

    # Ensure start_date is a working day
    start_date = ensure_working_day(start_date)

    for sim in range(num_simulations):
        # Update progress if callback is provided
        if progress_callback and sim % config.simulation.progress_update_interval == 0:
            progress = sim / num_simulations
            progress_callback(progress, f"Running simulation {sim + 1} of {num_simulations}...")

        # Track results for this simulation run
        project_results = []
        completion_dates = {}
        capacity_usage = {}

        # Simulate each work item
        for work_item in work_items:
            result = _simulate_single_work_item(work_item, start_date, capacity_per_quarter, completion_dates, capacity_usage, config)
            project_results.append(result)

        # Create a SimulationRun object
        simulation_run = SimulationRun(results=project_results)
        simulation_results.append(simulation_run)

    if progress_callback:
        progress_callback(1.0, "Simulation complete!")

    return simulation_results


def analyze_results(simulation_runs: List[SimulationRun], work_items: List[WorkItem]) -> Dict[str, SimulationStats]:
    """Analyze simulation results and calculate statistics.

    Args:
        simulation_results: Results from the Monte Carlo simulation
        work_items: List of WorkItem objects

    Returns:
        Dictionary of statistics for each project
    """
    # Create a dictionary to store statistics for each project
    stats = {}

    # Get project names and due dates from work items
    project_names = [item.initiative for item in work_items]
    due_dates = [item.due_date for item in work_items]

    for idx, project_name in enumerate(project_names):
        position = work_items[idx].position

        # Extract results for this project
        project_results = []
        for sim_run in simulation_runs:
            for result in sim_run.results:
                if result.position == position:
                    project_results.append(result)
                    break

        # Calculate statistics
        completion_dates = sorted([r.completion_date for r in project_results])
        on_time_count = sum(1 for r in project_results if r.on_time)
        n = len(completion_dates)

        # Calculate percentile indices with proper rounding
        # For P50, we want the median (middle value)
        p10_index = max(0, min(n - 1, round(n * 0.1) - 1))
        p50_index = max(0, min(n - 1, round(n * 0.5) - 1))
        p90_index = max(0, min(n - 1, round(n * 0.9) - 1))

        # Create a SimulationStats object
        stats[project_name] = SimulationStats(
            position=position,
            due_date=due_dates[idx],
            on_time_probability=(on_time_count / n) * 100,
            p10=completion_dates[p10_index],
            p50=completion_dates[p50_index],
            p90=completion_dates[p90_index],
            best_effort=work_items[idx].best_estimate,
            likely_effort=work_items[idx].most_likely_estimate,
            worst_effort=work_items[idx].worst_estimate,
        )

    return stats


def calculate_start_dates(stats: Dict[str, SimulationStats], work_items: List[WorkItem]) -> None:
    """Calculate start dates for each project based on dependencies.

    Args:
        stats: Dictionary of project statistics
        work_items: List of WorkItem objects

    Note:
        This function modifies the stats dictionary in-place
    """
    # First pass: set default start dates to project start date
    for project_name, project_stats in stats.items():
        default_start = pd.Timestamp(datetime.now().date())
        project_stats.start_p10 = getattr(project_stats, "start_date", default_start)
        project_stats.start_p50 = getattr(project_stats, "start_date", default_start)
        project_stats.start_p90 = getattr(project_stats, "start_date", default_start)

    # Create a lookup dictionary for work items by position
    position_to_work_item = {item.position: item for item in work_items}

    # Second pass: update start dates based on dependencies
    for project_name, project_stats in stats.items():
        # Find the work item for this project
        work_item = next((item for item in work_items if item.initiative == project_name), None)
        if not work_item or not work_item.has_dependency:
            continue

        # Get the dependency position
        dependency_position = work_item.dependency

        # Find the dependent work item
        dependent_work_item = position_to_work_item.get(dependency_position)
        if not dependent_work_item:
            continue

        # Get the dependent project name
        dependent_project = dependent_work_item.initiative
        if dependent_project not in stats:
            continue

        # Start dates are the completion dates of the dependency
        dep_stats = stats[dependent_project]
        project_stats.start_p10 = convert_to_date(dep_stats.p10)
        project_stats.start_p50 = convert_to_date(dep_stats.p50)
        project_stats.start_p90 = convert_to_date(dep_stats.p90)
