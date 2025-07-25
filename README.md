# Roadmap Analyzer

A Streamlit application for Project Roadmap Monte Carlo Analysis to assess on-time delivery probabilities.

## Setup

This project uses [Task](https://taskfile.dev/) for managing development tasks and [uv](https://github.com/astral-sh/uv) for Python package management.

### Prerequisites

- Python 3.9 or higher
- [Task](https://taskfile.dev/) - Task runner
- [uv](https://github.com/astral-sh/uv) - Python package installer

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

Format and check code:

```bash
task format
task check
```

Run all quality checks:

```bash
task fct
```

Clean up temporary files:

```bash
task clean
```
