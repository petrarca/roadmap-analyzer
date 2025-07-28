import sys
from datetime import timedelta
from typing import List

import pandas as pd
import streamlit as st

# Import custom modules
from roadmap_analyzer.capacity import CapacityCalculator, TimePeriodType
from roadmap_analyzer.components import (
    add_notification,
    display_data_tab,
    display_sidebar_controls,
    display_simulation_metrics,
    display_status_tab,
    show_welcome_screen,
)
from roadmap_analyzer.config import load_config
from roadmap_analyzer.config_loader import load_and_apply_config
from roadmap_analyzer.data_loader import load_work_items
from roadmap_analyzer.gantt_chart import create_gantt_chart
from roadmap_analyzer.models import WorkItem
from roadmap_analyzer.probability_chart import create_probability_chart
from roadmap_analyzer.simulation import SimulationEngine
from roadmap_analyzer.statistics import display_detailed_statistics
from roadmap_analyzer.utils import is_working_day, prepare_dataframe_for_display

# Load application configuration
APP_CONFIG = load_config()

# Page configuration using config model
st.set_page_config(page_title=APP_CONFIG.ui.page_title, page_icon=APP_CONFIG.ui.page_icon, layout=APP_CONFIG.ui.layout)

# Add custom CSS to reduce the font size of metric values
st.markdown(
    """
<style>
    /* Reduce the font size of metric values */
    [data-testid="stMetricValue"] {
        font-size: 1.5rem !important;
    }
    
    /* Also reduce the font size of metric labels */
    [data-testid="stMetricLabel"] {
        font-size: 0.9rem !important;
    }
    
    /* Adjust the delta value size */
    [data-testid="stMetricDelta"] {
        font-size: 0.9rem !important;
    }
</style>
""",
    unsafe_allow_html=True,
)

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


# Detailed statistics display moved to statistics.py


def run_simulation_workflow(work_items, capacity_value, start_date, time_period_type, num_simulations):
    """Run the Monte Carlo simulation workflow.

    Args:
        work_items: List of work items to simulate
        capacity_value: Capacity value per time period (quarter or month)
        start_date: Start date for the simulation
        time_period_type: Type of time period ("quarterly" or "monthly")
        num_simulations: Number of Monte Carlo simulations to run

    Returns:
        Simulation statistics
    """
    # Set up progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()

    # Ensure start_date is a working day
    if not is_working_day(start_date):
        original_date = start_date
        while not is_working_day(start_date):
            start_date += timedelta(days=1)
        message = f"Adjusted start date from {original_date.strftime('%Y-%m-%d')} (weekend) to {start_date.strftime('%Y-%m-%d')}"
        add_notification(f"{message} (next working day)", "info")

    def update_progress(progress, message):
        progress_bar.progress(progress)
        status_text.text(message)

    # Create capacity calculator with the selected time period
    period_type = TimePeriodType.QUARTERLY if time_period_type == "quarterly" else TimePeriodType.MONTHLY
    capacity_calculator = CapacityCalculator(APP_CONFIG, period_type)
    simulation_engine = SimulationEngine(APP_CONFIG, capacity_calculator)

    # Run simulation with progress callback
    # The capacity calculator already has the correct period type from initialization
    simulation_results = simulation_engine.run_monte_carlo_simulation(
        work_items, capacity_value, start_date, num_simulations, progress_callback=update_progress
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

    # Initialize file upload handling
    file_path = ""

    # Add title to sidebar before file uploader
    st.sidebar.title("📊 Project Roadmap Monte Carlo Analysis")

    uploaded_file = st.sidebar.file_uploader("Upload Excel File", type=["xlsx", "xls"])

    if uploaded_file:
        # Clear notifications when loading a new file
        # Initialize if needed
        if "notifications" not in st.session_state:
            st.session_state.notifications = []
        else:
            st.session_state.notifications = []

        # Add initial notification about clearing
        add_notification("Status messages cleared - loading new file", "info")

        # Save the uploaded file to a temporary location and use that path
        import tempfile

        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            file_path = tmp_file.name

        # Load configuration from Excel file if available
        # This needs to happen before the sidebar controls are displayed
        updated_config = load_and_apply_config(file_path, APP_CONFIG)

        # Load data if file path is provided
        work_items = load_work_items(file_path, updated_config)
    else:
        # No file uploaded
        show_welcome_screen()
        return

    # Get sidebar controls using the components module
    # This will now use the session state values set by load_and_apply_config
    _, start_date, capacity_value, time_period_type, num_simulations, run_simulation = display_sidebar_controls(file_path)

    if not work_items:
        error_msg = f"Could not load file: {file_path}. Please check that the file exists and has the correct format."
        add_notification(error_msg, "error", show_inline=True)
        show_welcome_screen()  # Show welcome screen with example format
        return

    # Create main tabs for data view, simulation view, and status
    data_tab, simulation_tab, status_tab = st.tabs(["📋 Roadmap data", "📊 Simulation results", "📝 Status"])

    # Data tab content
    with data_tab:
        display_data_tab(work_items)

    # Status tab content
    with status_tab:
        display_status_tab()

    # Simulation tab content
    with simulation_tab:
        # Check if the run simulation button in sidebar was clicked
        if run_simulation or st.session_state.stats is not None:
            # Run simulation if button was clicked
            if run_simulation:
                with st.spinner("Running simulations..."):
                    stats = run_simulation_workflow(work_items, capacity_value, start_date, time_period_type, num_simulations)
                    # Store results in session state for persistence
                    st.session_state.stats = stats
            else:
                # Use cached results from session state
                stats = st.session_state.stats

            # Summary metrics
            display_simulation_metrics(stats)

            # Visualizations
            st.subheader("📊 Visualizations")

            viz_tab1, viz_tab2, viz_tab3 = st.tabs(["Timeline View", "Probability Chart", "Detailed Statistics"])

            with viz_tab1:
                gantt_chart = create_gantt_chart(stats, work_items)
                st.plotly_chart(gantt_chart, use_container_width=True)

            with viz_tab2:
                # Create scatter plot visualization
                prob_chart = create_probability_chart(stats)
                st.plotly_chart(prob_chart, use_container_width=True)

            with viz_tab3:
                # Detailed statistics table in its own tab
                display_detailed_statistics(stats)


if __name__ == "__main__":
    # Command line arguments are automatically handled above
    main()
