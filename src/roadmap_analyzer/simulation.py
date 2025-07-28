"""Monte Carlo simulation for project roadmap analysis."""

from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional

from roadmap_analyzer.capacity import (
    CapacityCalculator,
    TimePeriodType,
)
from roadmap_analyzer.config import AppConfig
from roadmap_analyzer.models import SimulationResult, SimulationRun, SimulationStats, WorkItem
from roadmap_analyzer.utils import (
    add_working_days,
    convert_to_date,
    is_working_day,
    triangular_random,
)


class SimulationEngine:
    """Monte Carlo simulation engine for project roadmap analysis.

    This class encapsulates all simulation functionality and provides better
    state management and configuration handling.
    """

    def __init__(self, config: AppConfig, capacity_calculator: Optional[CapacityCalculator] = None):
        """Initialize the simulation engine.

        Args:
            config: Application configuration
            capacity_calculator: Optional CapacityCalculator instance. If None, creates a default quarterly calculator.
        """
        self.config = config
        self.capacity_calculator = capacity_calculator or CapacityCalculator(config, TimePeriodType.QUARTERLY)
        self._reset_state()

    def _reset_state(self) -> None:
        """Reset the internal state for a new simulation run."""
        self.completion_dates: Dict[int, datetime.date] = {}
        self.capacity_usage: Dict[str, float] = {}

    def set_capacity_override(self, period_identifier: str, capacity: float) -> None:
        """Set a capacity override for a specific time period.

        Args:
            period_identifier: Identifier for the time period (e.g., "2024-Q1", "2024-01")
            capacity: Capacity value to use for this period
        """
        self.capacity_calculator.set_capacity_override(period_identifier, capacity)

    def ensure_working_day(self, date_obj: datetime.date) -> datetime.date:
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

    def _simulate_single_work_item(
        self,
        work_item: WorkItem,
        start_date: datetime.date,
        capacity_per_quarter: int,
    ) -> SimulationResult:
        """Simulate a single work item and calculate its completion date.

        Args:
            work_item: The work item to simulate
            start_date: The overall project start date
            capacity_per_quarter: Available capacity per quarter

        Returns:
            SimulationResult for the work item
        """
        # Sample effort from triangular distribution
        effort = triangular_random(work_item.best_estimate, work_item.most_likely_estimate, work_item.worst_estimate)

        # Determine start date considering dependencies
        project_start_date = self._determine_start_date(work_item, start_date)

        # Calculate completion date based on effort and capacity
        completion_date = self._calculate_completion_date(project_start_date, effort, capacity_per_quarter)

        # Store the completion date for potential dependencies
        self.completion_dates[work_item.position] = completion_date

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

    def _determine_start_date(self, work_item: WorkItem, default_start_date: datetime.date) -> datetime.date:
        """Determine the start date for a work item considering dependencies.

        Args:
            work_item: The work item to determine start date for
            default_start_date: The default project start date

        Returns:
            The start date for the work item
        """
        project_start_date = default_start_date

        if work_item.has_dependency:
            dep_completion = self.completion_dates.get(work_item.dependency)
            if dep_completion and dep_completion > project_start_date:
                # Ensure the dependency completion date is a working day
                project_start_date = self.ensure_working_day(dep_completion)

        return project_start_date

    def _calculate_completion_date(
        self,
        start_date: datetime.date,
        effort: float,
        capacity_per_quarter: int,
    ) -> datetime.date:
        """Calculate the completion date for a work item based on effort and capacity.

        Args:
            start_date: The start date for the work item
            effort: The effort required for the work item
            capacity_per_quarter: Available capacity per quarter

        Returns:
            The completion date for the work item
        """
        current_date = self.ensure_working_day(start_date)
        remaining_effort = effort

        while remaining_effort > 0:
            # Get quarter info for current date
            quarter_str, working_days_in_quarter, capacity_per_working_day = self.capacity_calculator.get_period_info(current_date)

            # Get available capacity for this quarter
            available_capacity = self._get_available_capacity(quarter_str, current_date, capacity_per_quarter)

            if available_capacity <= 0:
                # No capacity left in this quarter, move to next quarter
                current_date = self._move_to_next_quarter(current_date)
                continue

            # Calculate how much effort can be completed in this quarter
            effort_this_quarter = min(remaining_effort, available_capacity)

            # Update capacity usage for this quarter
            self.capacity_usage[quarter_str] = self.capacity_usage.get(quarter_str, 0) + effort_this_quarter

            # Calculate the exact completion date within this quarter
            if effort_this_quarter >= remaining_effort:
                # Work will be completed in this quarter
                completion_date = self._calculate_exact_completion_date(
                    current_date, effort_this_quarter, capacity_per_quarter, working_days_in_quarter
                )
                return completion_date
            else:
                # Work continues to next quarter
                remaining_effort -= effort_this_quarter
                current_date = self._move_to_next_quarter(current_date)

        return current_date

    def _get_available_capacity(
        self,
        quarter_str: str,
        current_date: datetime.date,
        capacity_per_quarter: int,
    ) -> float:
        """Get the available capacity for a quarter.

        Args:
            quarter_str: The quarter string identifier
            current_date: The current date within the quarter
            capacity_per_quarter: Total capacity for the quarter

        Returns:
            Available capacity for the quarter
        """
        used_capacity = self.capacity_usage.get(quarter_str, 0)

        # Calculate remaining capacity in the quarter from the current date
        quarter_str_calc, remaining_capacity = self.capacity_calculator.calculate_remaining_capacity(current_date, capacity_per_quarter)

        # The available capacity is the minimum of remaining capacity and unused capacity
        available_capacity = min(remaining_capacity, capacity_per_quarter - used_capacity)

        return max(0, available_capacity)

    def _move_to_next_quarter(self, current_date: datetime.date) -> datetime.date:
        """Move to the first working day of the next quarter.

        Args:
            current_date: The current date

        Returns:
            The first working day of the next quarter
        """
        year = current_date.year
        quarter = (current_date.month - 1) // 3 + 1

        if quarter == 4:
            # Move to Q1 of next year
            next_quarter_start = datetime(year + 1, 1, 1).date()
        else:
            # Move to next quarter of same year
            next_quarter_month = quarter * 3 + 1
            next_quarter_start = datetime(year, next_quarter_month, 1).date()

        return self.ensure_working_day(next_quarter_start)

    def _calculate_exact_completion_date(
        self,
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
        # Calculate effort per working day
        effort_per_working_day = capacity_per_quarter / working_days_in_quarter

        # Calculate how many working days are needed to complete the effort
        working_days_needed = effort_this_quarter / effort_per_working_day

        # Add the working days to the current date
        completion_date = add_working_days(current_date, int(working_days_needed))

        return completion_date

    def run_monte_carlo_simulation(
        self,
        work_items: List[WorkItem],
        capacity_per_quarter: int,
        start_date: datetime.date,
        num_simulations: int,
        progress_callback: Optional[Callable[[float, str], None]] = None,
    ) -> List[SimulationRun]:
        """Run Monte Carlo simulation for project timeline using WorkItem objects.

        Args:
            work_items: List of WorkItem objects to simulate
            capacity_per_quarter: Available capacity per quarter in person-days
            start_date: Project start date
            num_simulations: Number of simulation runs to perform
            progress_callback: Optional callback function for progress updates

        Returns:
            List of SimulationRun objects containing results from all simulations
        """
        simulation_results = []

        for i in range(num_simulations):
            # Reset state for each simulation run
            self._reset_state()

            # Run simulation for all work items
            simulation_run_results = []
            for work_item in work_items:
                result = self._simulate_single_work_item(work_item, start_date, capacity_per_quarter)
                simulation_run_results.append(result)

            # Create a SimulationRun object
            simulation_run = SimulationRun(results=simulation_run_results)
            simulation_results.append(simulation_run)

            # Update progress if callback is provided
            if progress_callback:
                progress = (i + 1) / num_simulations
                progress_callback(progress, f"Completed simulation {i + 1}/{num_simulations}")

        return simulation_results

    def analyze_results(self, simulation_runs: List[SimulationRun], work_items: List[WorkItem]) -> Dict[str, SimulationStats]:
        """Analyze simulation results and calculate statistics.

        Args:
            simulation_runs: Results from the Monte Carlo simulation
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

    def calculate_start_dates(self, stats: Dict[str, SimulationStats], work_items: List[WorkItem], project_start_date: datetime.date) -> None:
        """Calculate start dates for each project based on dependencies.

        Args:
            stats: Dictionary of project statistics
            work_items: List of WorkItem objects
            project_start_date: The actual project start date configured by the user

        Note:
            This function modifies the stats dictionary in-place
        """
        # First pass: set default start dates to the configured project start date
        for project_name, project_stats in stats.items():
            project_stats.start_p10 = project_start_date
            project_stats.start_p50 = project_start_date
            project_stats.start_p90 = project_start_date

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
