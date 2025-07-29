# Excel File Format

This document describes the format requirements for Excel files used with the Roadmap Analyzer application.

## Overview

The Roadmap Analyzer supports Excel files with the following sheets:

1. **Data** (required): Contains work item information and effort estimates
2. **Config** (optional): Contains configuration settings for the simulation
3. **Capacity** (optional): Contains period-specific capacity values

## Data Sheet

The Data sheet contains your work items and their effort estimates. This sheet is required.

### Columns

| Column Name | Description | Format | Required |
|-------------|-------------|--------|----------|
| Position | Numeric position/ID of the work item | Integer | Yes |
| Item | Name or description of the work item | Text | Yes |
| Due date | Target completion date | Date (YYYY-MM-DD) | No |
| Dependency | Position/ID of the work item this item depends on | Integer | No |
| Best | Best-case effort estimate | Number | Yes |
| Likely | Most likely effort estimate | Number | Yes |
| Worst | Worst-case effort estimate | Number | Yes |
| Priority | Priority of the work item (not currently used) | Text/Number | No |
| Start date | Fixed start date for the work item | Date (YYYY-MM-DD) | No |

### Example

| Position | Item | Due date | Dependency | Best | Likely | Worst | Priority | Start date |
|----------|------|----------|------------|------|--------|-------|----------|------------|
| 1 | Feature A | 2025-06-30 | | 100 | 120 | 150 | High | |
| 2 | Feature B | 2025-07-31 | 1 | 80 | 100 | 130 | Medium | |
| 3 | Feature C | 2025-08-31 | | 200 | 250 | 300 | Low | 2025-07-01 |

### Start Date Column Details

The **Start date** column allows you to specify when a work item cannot start before a certain date. This is useful for:

- **Resource Availability**: When team members or resources become available on specific dates
- **External Dependencies**: When waiting for external deliverables or approvals
- **Business Constraints**: When features must align with marketing campaigns or product launches
- **Regulatory Requirements**: When compliance or legal requirements dictate timing

#### How Start Dates Work

1. **Optional Constraint**: If no start date is specified (empty cell), the work item can start as soon as its dependencies are complete

2. **Constraint Enforcement**: Work items will never start before their specified start date, even if dependencies are complete earlier

3. **Dependency Integration**: When both dependencies and start dates exist, the simulation uses the **later** of:
   - The completion date of all dependencies
   - The work item's start date

4. **Working Day Adjustment**: Start dates are automatically adjusted to the next working day (Monday-Friday) if they fall on weekends

5. **Visualization**: 
   - Start dates appear as **green diamond markers** with dashed lines in the Gantt chart
   - Due dates appear as **blue diamond markers** with dashed lines
   - The **Statistics table** displays the original start date for each work item

#### Example Scenarios

**Scenario 1**: Feature C has a start date of 2025-07-01 but no dependencies
- Result: Feature C will start on 2025-07-01 (or next working day) regardless of project start date

**Scenario 2**: Feature B depends on Feature A (completed 2025-06-15) and has start date 2025-07-01
- Result: Feature B will start on 2025-07-01 since it's later than the dependency completion

**Scenario 3**: Feature D depends on Feature A (completed 2025-08-01) and has start date 2025-07-01
- Result: Feature D will start on 2025-08-01 since the dependency completion is later than the start date

## Config Sheet

The Config sheet contains simulation configuration parameters. This sheet is optional.

### Columns

| Column Name | Description | Format | Default Value |
|-------------|-------------|--------|---------------|
| Parameter | Name of the configuration parameter | Text | N/A |
| Value | Value of the configuration parameter | Text/Number | N/A |

### Supported Parameters

| Parameter | Description | Format | Default Value |
|-----------|-------------|--------|---------------|
| default_capacity_per_quarter | Default capacity per quarter in person-days | Number | 1300 |
| default_num_simulations | Default number of Monte Carlo simulations to run | Integer | 10000 |
| simulation_optimistic_weight | Weight for optimistic estimates in simulation | Number | 1.0 |
| simulation_pessimistic_weight | Weight for pessimistic estimates in simulation | Number | 1.0 |
| working_days_per_week | Number of working days per week | Integer | 5 |
| weekend_days | Days of the week considered weekend (0=Monday, 6=Sunday) | List of integers | [5, 6] |

### Example

| Parameter | Value |
|-----------|-------|
| default_capacity_per_quarter | 1500 |
| default_num_simulations | 20000 |
| simulation_optimistic_weight | 0.9 |
| simulation_pessimistic_weight | 1.1 |

## Capacity Sheet

The Capacity sheet contains period-specific capacity values. This sheet is optional.

### Columns

| Column Name | Description | Format | Required |
|-------------|-------------|--------|----------|
| Period | Time period identifier | Text (see formats below) | Yes |
| Capacity | Capacity value for the period in person-days | Number | Yes |

### Period Format

The Period column can use two formats:

1. **Quarterly**: `YYYY.QN` (e.g., "2025.Q1", "2025.Q2")
2. **Monthly**: `YYYY.M` (e.g., "2025.1", "2025.2", "2025.12")

Note: Internally, the application converts these to "YYYY-QN" and "YYYY-MM" formats.

### Example

| Period | Capacity |
|--------|----------|
| 2025.Q1 | 1500 |
| 2025.Q2 | 1600 |
| 2025.Q3 | 1200 |
| 2025.Q4 | 1400 |
| 2026.1 | 500 |
| 2026.2 | 550 |
| 2026.3 | 600 |

## Best Practices

1. **Column Names**: Ensure column names match exactly as specified (case-sensitive)
2. **Data Types**: Use appropriate data types for each column
3. **Required Columns**: Include all required columns in each sheet
4. **Sheet Names**: Use the exact sheet names as specified (case-sensitive)
5. **Dates**: Use consistent date formats (YYYY-MM-DD recommended)
6. **Dependencies**: Ensure dependency references point to valid Position values
7. **Period Format**: Use consistent period formats within the Capacity sheet
