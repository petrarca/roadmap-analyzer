# Variable Capacity Support

This document explains how to use the variable capacity feature in the Roadmap Analyzer.

## Overview

The variable capacity feature allows you to define different capacity values for specific time periods (quarters or months). This is useful for more accurate planning when your team's capacity varies throughout the year due to:

- Planned vacations or holidays
- Team size changes
- Part-time allocations to other projects
- Seasonal variations in workload

## How to Use

### Excel File Format

To use variable capacity, add a sheet named "Capacity" to your Excel file with the following columns:

1. **Period**: The time period identifier in one of these formats:
   - Quarterly: `YYYY.QN` (e.g., "2025.Q1", "2025.Q2")
   - Monthly: `YYYY.M` (e.g., "2025.1", "2025.2", "2025.12")

2. **Capacity**: The capacity value for that period in person-days

Example:

| Period  | Capacity |
|---------|----------|
| 2025.Q1 | 1500     |
| 2025.Q2 | 1600     |
| 2025.Q3 | 1200     |
| 2025.Q4 | 1400     |
| 2026.1  | 500      |
| 2026.2  | 550      |
| 2026.3  | 600      |

### UI Integration

When you upload an Excel file with a "Capacity" sheet, the application will:

1. Automatically detect and load the capacity data
2. Display a success message with the number of capacity entries loaded
3. Show a "Capacity data" tab with a bar chart visualization of the capacity values
4. Use these capacity values in the Monte Carlo simulation

If no custom capacity data is found, the application will use the default capacity value specified in the sidebar.

### Mixing Period Types

You can include both quarterly and monthly period formats in the same capacity sheet. The application will use the appropriate values based on the selected time period type (quarterly or monthly) in the sidebar.

## Technical Details

### Capacity Calculator

The `CapacityCalculator` class has been enhanced to support variable capacity:

```python
# Create capacity calculator with variable capacity
capacity_calculator = CapacityCalculator(
    config,
    TimePeriodType.QUARTERLY,  # or TimePeriodType.MONTHLY
    capacity_dict              # Dictionary mapping period strings to capacity values
)
```

The capacity calculator will use the values from the capacity dictionary when available, falling back to the default capacity when a specific period is not defined.

### Period Identifiers

The application uses two different period identifier formats:

1. **External format** (used in Excel): `YYYY.QN` or `YYYY.M` (e.g., "2025.Q1" or "2025.1")
2. **Internal format** (used by CapacityCalculator): `YYYY-QN` or `YYYY-MM` (e.g., "2025-Q1" or "2025-01")

The `capacity_loader.py` module handles the conversion between these formats.

## Handling Capacity Outside Defined Periods

When the simulation needs capacity data for a period that is not explicitly defined in your capacity data, the system will automatically fall back to the default capacity value. This ensures that the simulation can run smoothly even when projecting far into the future beyond your defined capacity data.

The process works as follows:

1. When capacity is needed for a specific period (e.g., "2025-Q3" or "2026-01"), the system first checks if that period exists in the capacity overrides dictionary.

2. If found, the system uses the custom capacity value defined for that period.

3. If not found, the system falls back to the default capacity value:
   - For quarterly periods: The default capacity per quarter from the configuration
   - For monthly periods: The default quarterly capacity divided by 3

This approach provides flexibility - you only need to define capacity for periods where you expect variations from the default, and the system will handle all other periods automatically.

## Best Practices

1. **Consistent Time Periods**: Try to use either quarterly or monthly periods consistently for better predictability.

2. **Forward Planning**: Include capacity data for all periods where you expect variations from the default capacity. You don't need to define capacity for all future periods - the system will use the default for any undefined periods.

3. **Default Capacity**: Set a reasonable default capacity in the sidebar that represents your team's typical capacity. This will be used for all periods not explicitly defined.

4. **Visualization**: Use the capacity data visualization to verify your capacity plan before running simulations.

5. **Sensitivity Analysis**: Try different capacity scenarios to understand the impact on project timelines.

6. **Long-Term Forecasting**: For long-term forecasts, focus on defining capacity for near-term periods accurately, and let the system use default values for distant future periods where uncertainty is higher.
