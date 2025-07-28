import sys
from datetime import timedelta
from typing import List

import pandas as pd
import streamlit as st

# Import custom modules
from roadmap_analyzer.capacity import CapacityCalculator, TimePeriodType
from roadmap_analyzer.components import display_data_tab, display_sidebar_controls, display_simulation_metrics, show_welcome_screen
from roadmap_analyzer.config import load_config
from roadmap_analyzer.data_loader import load_work_items
from roadmap_analyzer.models import WorkItem
from roadmap_analyzer.simulation import SimulationEngine
from roadmap_analyzer.statistics import display_detailed_statistics
from roadmap_analyzer.utils import is_working_day, prepare_dataframe_for_display
from roadmap_analyzer.visualization import create_gantt_chart, create_probability_chart

# Load application configuration
APP_CONFIG = load_config()

# Page configuration using config model
st.set_page_config(page_title=APP_CONFIG.ui.page_title, page_icon=APP_CONFIG.ui.page_icon, layout=APP_CONFIG.ui.layout)

# Description in main area
st.markdown("Analyze project timelines with Monte Carlo simulation to assess on-time delivery probabilities")

# Get default file path from command line arguments if provided
default_file_path = ""
if len(sys.argv) > 1:
    default_file_path = sys.argv[1]


# DataFrame utilities for Streamlit display


def create_work_items_display_dataframe(work_items: List[WorkItem]) -> pd.DataFrame:
    """Create a display-ready DataFrame from WorkItem objects.

    Args:
        work_items: List of WorkItem objects

    Returns:
        PyArrow-compatible DataFrame ready for Streamlit display
    """
    display_df = pd.DataFrame(
        [
            {
                "Position": item.position,
                "Item": item.item,
                "Due date": item.due_date.strftime("%Y-%m-%d"),
                "Start date": item.start_date.strftime("%Y-%m-%d") if item.start_date else "",
                "Priority": item.priority if item.priority else "",
                "Dependency": item.dependency,  # Will be handled by prepare_dataframe_for_display
                "Best": item.best_estimate,
                "Likely": item.most_likely_estimate,
                "Worst": item.worst_estimate,
                "Expected Effort": round(item.expected_effort, 1),
            }
            for item in work_items
        ]
    )

    return prepare_dataframe_for_display(display_df)

    # Visualization functions

    # Create Gantt chart
    # Gantt chart creation moved to visualization.py

    # Create probability chart
    # Probability chart creation moved to visualization.py

    # UI Helper Functions
    # Create display-ready DataFrame using centralized function
    display_df = create_work_items_display_dataframe(work_items)
    st.dataframe(display_df, use_container_width=True)


# Detailed statistics display moved to statistics.py


def run_simulation_workflow(work_items, capacity_per_quarter, start_date, num_simulations):
    """Run the Monte Carlo simulation workflow."""
    # Set up progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()

    # Ensure start_date is a working day
    if not is_working_day(start_date):
        original_date = start_date
        while not is_working_day(start_date):
            start_date += timedelta(days=1)
        st.info(f"Adjusted start date from {original_date.strftime('%Y-%m-%d')} (weekend) to {start_date.strftime('%Y-%m-%d')} (next working day)")

    def update_progress(progress, message):
        progress_bar.progress(progress)
        status_text.text(message)

    # Create capacity calculator and simulation engine
    capacity_calculator = CapacityCalculator(APP_CONFIG, TimePeriodType.QUARTERLY)
    simulation_engine = SimulationEngine(APP_CONFIG, capacity_calculator)

    # Run simulation with progress callback
    simulation_results = simulation_engine.run_monte_carlo_simulation(
        work_items, capacity_per_quarter, start_date, num_simulations, progress_callback=update_progress
    )

    # Analyze results
    stats = simulation_engine.analyze_results(simulation_results, work_items)

    # Calculate start dates for Gantt chart
    simulation_engine.calculate_start_dates(stats, work_items, start_date)

    return stats


# Main app
def main():
    # Initialize session state for data persistence
    if "stats" not in st.session_state:
        st.session_state.stats = None

    # Get sidebar controls using the components module
    file_path, start_date, capacity_per_quarter, num_simulations, run_simulation = display_sidebar_controls()

    # Check if file path is empty
    if not file_path.strip():
        show_welcome_screen()
        return

    # Load data if file path is provided
    work_items = load_work_items(file_path, APP_CONFIG)

    if not work_items:
        st.error(f"Could not load file: {file_path}. Please check that the file exists and has the correct format.")
        show_welcome_screen()  # Show welcome screen with example format
        return

    # Create main tabs for data view and simulation view
    data_tab, simulation_tab = st.tabs(["📋 Roadmap data", "📊 Simulation results"])

    # Data tab content
    with data_tab:
        display_data_tab(work_items)

    # Simulation tab content
    with simulation_tab:
        # Check if the run simulation button in sidebar was clicked
        if run_simulation or st.session_state.stats is not None:
            # Run simulation if button was clicked
            if run_simulation:
                with st.spinner("Running simulations..."):
                    stats = run_simulation_workflow(work_items, capacity_per_quarter, start_date, num_simulations)
                    # Store results in session state for persistence
                    st.session_state.stats = stats
            else:
                # Use cached results from session state
                stats = st.session_state.stats

            # Summary metrics
            display_simulation_metrics(stats)

            # Visualizations
            st.subheader("📊 Visualizations")

            viz_tab1, viz_tab2 = st.tabs(["Timeline View", "Probability Chart"])

            with viz_tab1:
                gantt_chart = create_gantt_chart(stats, start_date, work_items)
                st.plotly_chart(gantt_chart, use_container_width=True)

            with viz_tab2:
                prob_chart = create_probability_chart(stats)
                st.plotly_chart(prob_chart, use_container_width=True)

            # Detailed statistics table
            display_detailed_statistics(stats)


if __name__ == "__main__":
    # Command line arguments are automatically handled above
    main()
