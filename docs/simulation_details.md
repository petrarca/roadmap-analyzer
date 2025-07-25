# Monte Carlo Simulation for Project Roadmap Analysis

This document explains in detail how the Monte Carlo simulation works in the Project Roadmap Analyzer, including the principles and rules that govern the calculations.

## Table of Contents

1. [Overview](#overview)
2. [Core Principles](#core-principles)
3. [Simulation Process](#simulation-process)
4. [Capacity Management](#capacity-management)
5. [Date Calculations](#date-calculations)
6. [Statistical Analysis](#statistical-analysis)
7. [Technical Implementation](#technical-implementation)

## Overview

The Monte Carlo simulation is used to predict project completion dates based on effort estimates and available capacity. By running thousands of simulations with randomized effort values, we can generate statistical distributions of possible completion dates and calculate the probability of meeting deadlines.

## Core Principles

The simulation follows these fundamental principles:

1. **Working Days**: Only weekdays (Monday through Friday) are considered working days. Weekends are skipped in all calculations.

2. **Quarterly Capacity**: Capacity is defined per quarter and is evenly distributed across all working days in that quarter.

3. **Effort Distribution**: Project effort is modeled using a triangular distribution with three points:
   - Best case estimate (optimistic)
   - Most likely estimate (realistic)
   - Worst case estimate (pessimistic)

4. **Dependencies**: Work items can depend on other work items, meaning they can only start after their dependencies are completed.

5. **Capacity Constraints**: The simulation respects capacity constraints, ensuring that work is only performed when capacity is available.

## Simulation Process

The simulation follows these steps for each run:

1. **Initialization**: Set up the simulation environment with the project start date (which must be a working day).

2. **For each work item**:
   - Sample an effort value from the triangular distribution
   - Determine the start date (considering dependencies)
   - Calculate the completion date based on effort and available capacity
   - Record the results

3. **Statistical Analysis**: After all simulation runs, analyze the results to calculate percentiles and probabilities.

## Capacity Management

Capacity is managed according to these rules:

1. **Quarterly Allocation**: Total capacity is allocated per quarter.

2. **Even Distribution**: Capacity is evenly distributed across all working days in a quarter.
   ```
   Capacity per working day = Quarterly capacity / Number of working days in quarter
   ```

3. **Remaining Capacity**: When a project starts mid-quarter, the remaining capacity is calculated as:
   ```
   Remaining capacity = (Remaining working days in quarter / Total working days in quarter) * Quarterly capacity
   ```

4. **Capacity Usage**: As work items consume capacity, the available capacity for subsequent items is reduced accordingly.

5. **Quarter Transitions**: When a quarter's capacity is fully used, work continues in the next quarter.

## Date Calculations

Date calculations follow these rules:

1. **Project Start Date**: Must be a working day. If a weekend is provided, it's adjusted to the next working day.

2. **Dependency Start Dates**: When a work item depends on another, its start date is the completion date of the dependency.

3. **Completion Date Calculation**: 
   - Calculate how much effort can be completed with the available capacity
   - Determine how many working days this corresponds to
   - Add these working days to the start date

4. **Working Days Only**: When adding days to dates, weekends are skipped.

## Statistical Analysis

After running multiple simulations, the results are analyzed to generate:

1. **Percentile Dates**: 
   - P10 (Best case): 10th percentile of completion dates
   - P50 (Most likely): 50th percentile (median) of completion dates
   - P90 (Worst case): 90th percentile of completion dates

2. **On-Time Probability**: Percentage of simulations where the work item completes on or before its due date.

## Technical Implementation

The simulation is implemented in a modular way to reduce cognitive complexity:

1. **`run_monte_carlo_simulation`**: Main function that coordinates the simulation process.

2. **`_simulate_single_work_item`**: Simulates a single work item, calculating its effort and completion date.

3. **`_determine_start_date`**: Determines the start date for a work item, considering dependencies.

4. **`_calculate_completion_date`**: Calculates the completion date based on effort and capacity.

5. **`_get_available_capacity`**: Calculates the available capacity for a specific quarter.

6. **`_move_to_next_quarter`**: Handles transitions between quarters.

7. **`_calculate_exact_completion_date`**: Calculates the exact completion date within a quarter.

8. **`calculate_remaining_capacity`**: Calculates the remaining capacity in a quarter based on the start date.

9. **`analyze_results`**: Analyzes simulation results to generate statistics.

10. **`calculate_start_dates`**: Calculates start dates for visualization purposes.

---

This implementation ensures accurate simulation of project timelines while respecting capacity constraints and dependencies, providing valuable insights for project planning and risk assessment.
