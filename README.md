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
