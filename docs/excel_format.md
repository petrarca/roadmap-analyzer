# Excel File Format

This document describes the format requirements for Excel files used with the Roadmap Analyzer application.

> **NOTE**: Sheet names and column names are case-insensitive. The application will recognize names regardless of capitalization (e.g., "Items", "items", or "ITEMS" will all work). However, for consistency and readability, it's recommended to use the names as specified in this document.

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

### Column Details

#### Start Date

The **Start date** column specifies when a work item cannot start before a certain date. If provided, the simulation will ensure the work item doesn't start before this date, even if dependencies are complete earlier. When both dependencies and start dates exist, the simulation uses the later of the dependency completion date or the work item's start date.

Start dates are automatically adjusted to the next working day (Monday-Friday) if they fall on weekends. In the Gantt chart, start dates appear as green diamond markers with dashed lines.

## Config Sheet

The Config sheet contains simulation configuration parameters. This sheet is optional. If not provided, the application will use default values for all configuration parameters.

### Columns

| Column Name | Description | Format | Default Value |
|-------------|-------------|--------|---------------|
| Config | Name of the configuration parameter | Text | N/A |
| Value | Value of the configuration parameter | Text/Number | N/A |

### Supported Parameters

| Parameter | Description | Format | Default Value |
|-----------|-------------|--------|---------------|
| Start date | Project start date | Date (YYYY-MM-DD) | Current date |
| Time period | Time period type ('q'/'quarterly' or 'm'/'monthly') | Text | quarterly |
| Capacity | Default capacity per period in person-days | Number | 1300 |
| Iterations | Default number of Monte Carlo simulations to run | Integer | 10000 |

### Example

| Config | Value |
|-----------|-------|
| Start date | 2025-01-15 |
| Time period | quarterly |
| Capacity | 1500 |
| Iterations | 20000 |

## Capacity Sheet

The Capacity sheet contains period-specific capacity values. This sheet is optional. If not provided, the application will use the default capacity value for all periods.

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

### Handling Undefined Periods

When the simulation encounters a period that is not explicitly defined in the Capacity sheet, it automatically falls back to the default capacity value. This allows you to define capacity only for periods where you expect variations from the default.

For detailed information about variable capacity planning and how undefined periods are handled, see [Variable Capacity Documentation](variable_capacity.md).

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

1. **Column Names**: Use the column names as specified in this document (names are case-insensitive)
2. **Data Types**: Use appropriate data types for each column
3. **Required Columns**: Include all required columns in each sheet
4. **Sheet Names**: Use the sheet names as specified in this document (names are case-insensitive)
5. **Dates**: Use consistent date formats (YYYY-MM-DD recommended)
6. **Dependencies**: Ensure dependency references point to valid Position values
7. **Period Format**: Use consistent period formats within the Capacity sheet
