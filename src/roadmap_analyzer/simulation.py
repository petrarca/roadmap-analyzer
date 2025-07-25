"""Monte Carlo simulation for project roadmap analysis."""

from datetime import datetime
from typing import Callable, Dict, List, Optional

import pandas as pd

from roadmap_analyzer.config import AppConfig
from roadmap_analyzer.models import SimulationResult, SimulationRun, SimulationStats, WorkItem
from roadmap_analyzer.utils import add_working_days, convert_to_date, get_quarter_from_date, triangular_random


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

    for sim in range(num_simulations):
        if progress_callback and sim % config.simulation.progress_update_interval == 0:
            progress = sim / num_simulations
            progress_callback(progress, f"Running simulation {sim + 1} of {num_simulations}...")

        project_results = []
        completion_dates = {}
        capacity_usage = {}

        for work_item in work_items:
            # Sample effort from triangular distribution
            effort = triangular_random(work_item.best_estimate, work_item.most_likely_estimate, work_item.worst_estimate)

            # Determine start date
            project_start_date = start_date
            if work_item.has_dependency:
                dep_completion = completion_dates.get(work_item.dependency)
                if dep_completion and dep_completion > project_start_date:
                    project_start_date = dep_completion

            # Calculate completion considering capacity constraints
            remaining_effort = effort
            current_date = project_start_date

            while remaining_effort > 0:
                quarter = get_quarter_from_date(current_date)
                if quarter not in capacity_usage:
                    capacity_usage[quarter] = 0

                available_capacity = capacity_per_quarter - capacity_usage[quarter]
                effort_this_quarter = min(remaining_effort, available_capacity)

                capacity_usage[quarter] += effort_this_quarter
                remaining_effort -= effort_this_quarter

                if remaining_effort > 0:
                    # Move to next quarter
                    if current_date.month >= 10:
                        current_date = current_date.replace(year=current_date.year + 1, month=1, day=1)
                    else:
                        current_date = current_date.replace(month=current_date.month + 3, day=1)
                else:
                    # Calculate exact completion date based on effort
                    # We need to calculate what fraction of the quarter was used
                    # and add the appropriate number of working days
                    fraction_of_quarter = effort_this_quarter / capacity_per_quarter
                    working_days_in_quarter = config.simulation.working_days_per_quarter
                    days_to_add = int(fraction_of_quarter * working_days_in_quarter)
                    current_date = add_working_days(current_date, days_to_add)

            completion_date = current_date
            completion_dates[work_item.position] = completion_date

            # Create a SimulationResult object
            result = SimulationResult(
                name=work_item.initiative,
                position=work_item.position,
                effort=effort,
                start_date=project_start_date,
                completion_date=completion_date,
                due_date=work_item.due_date,
                on_time=convert_to_date(completion_date) <= convert_to_date(work_item.due_date),
            )
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
        # Create a SimulationStats object
        stats[project_name] = SimulationStats(
            position=position,
            due_date=due_dates[idx],
            on_time_probability=(on_time_count / n) * 100,
            p10=completion_dates[int(n * 0.1)],
            p50=completion_dates[int(n * 0.5)],
            p90=completion_dates[int(n * 0.9)],
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
