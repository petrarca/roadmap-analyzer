# Roadmap Analyzer

A Streamlit application for Monte Carlo Analysis to assess on-time delivery probabilities for a project roadmap.

## Setup

This project uses [Task](https://taskfile.dev/) for managing development tasks and [uv](https://github.com/astral-sh/uv) for Python package management.

### Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) - Python package installer
- [Task](https://taskfile.dev/) - Task runner

### Installation

1. Clone the repository
2. Set up the development environment:

```bash
task setup
task install
```

## Usage

Run the Streamlit application:

```bash
task run
```

Or directly with:

```bash
uv run -m streamlit run src/roadmap_analyzer/main.py
```

## Input Data Format

The application accepts Excel files with specific sheets and column formats:

- **Data Sheet**: Contains work items, dependencies, and effort estimates
- **Config Sheet**: Contains simulation configuration parameters
- **Capacity Sheet** (Optional): Contains period-specific capacity values for variable capacity planning
  - Supports quarterly format: `2025.Q1`, `2025.Q2`, etc.
  - Supports monthly format: `2025.1`, `2025.2`, etc.
  - If omitted, uses fixed capacity from the default configuration

For detailed information about the Excel file format, see [Excel Format Documentation](docs/excel_format.md).

For comprehensive guidance on using variable capacity features, see [Variable Capacity Documentation](docs/variable_capacity.md).

## Examples

The project includes an `examples` directory containing sample data files and usage scenarios to help you get started with the roadmap analyzer.

## Simulation Methodology

The application uses Monte Carlo simulation to predict project completion dates based on effort estimates and capacity constraints. Key principles include:

- **Working Days**: Only weekdays (Monday-Friday) are considered working days
- **Flexible Capacity Management**: Supports both quarterly and monthly capacity allocation with:
  - **Fixed Capacity**: Uniform capacity across all periods using default values
  - **Variable Capacity**: Period-specific capacity values defined in Excel sheets
  - **Even Distribution**: Capacity is evenly distributed across working days within each period
- **Effort Distribution**: Uses triangular distribution (Best, Likely, Worst estimates)
- **Dependencies**: Respects work item dependencies in scheduling
- **Statistical Analysis**: Calculates P10, P50, P90 dates and on-time probabilities

### Capacity Allocation Options

The application provides flexible capacity management to accommodate different planning scenarios:

1. **Time Period Flexibility**:
   - **Quarterly**: Capacity allocated per quarter (e.g., Q1 2025, Q2 2025)
   - **Monthly**: Capacity allocated per month for more granular control

2. **Capacity Types**:
   - **Fixed Capacity**: Use a single default capacity value for all periods
   - **Variable Capacity**: Define specific capacity values for different periods to account for:
     - Planned vacations or holidays
     - Team size changes
     - Part-time allocations to other projects
     - Seasonal variations in workload

3. **Fallback Mechanism**: When using variable capacity, any periods not explicitly defined automatically use the default capacity value, ensuring seamless simulation execution.

### Detailed Documentation

For comprehensive information about the simulation methodology, including:
- Technical implementation details
- Capacity calculation formulas
- Date calculation rules
- Statistical analysis methods

Please refer to the **[Simulation Details Documentation](docs/simulation_details.md)**.

This documentation provides a deep dive into how the Monte Carlo simulation works, which is valuable for understanding the results and customizing the simulation parameters.

## Development

### Available Tasks

This project uses [Task](https://taskfile.dev/) to manage development workflows. Here's a complete list of available tasks:

| Task | Description | Command |
|------|-------------|--------|
| `setup` | Create a Python virtual environment | `task setup` |
| `install` | Install the package in development mode | `task install` |
| `format` | Format code using ruff | `task format` |
| `check` | Check and auto-fix code using ruff | `task check` |
| `test` | Run tests (succeeds if no tests found) | `task test` |
| `run` | Run the Streamlit application | `task run` |
| `clean` | Clean up temporary files and build artifacts | `task clean` |
| `fct` | Run format, check, and test in sequence | `task fct` |

### Common Workflows

**Setting up for development:**
```bash

# Initial setup
task setup
task install

# Start the application
task run
```

**Before committing code:**
```bash
# Run all quality checks (format, check, test)
task fct
```

**Cleaning up:**
```bash
task clean
```
