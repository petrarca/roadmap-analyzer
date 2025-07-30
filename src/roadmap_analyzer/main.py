import locale
from datetime import timedelta

import streamlit as st

# Initialize locale for number formatting
try:
    locale.setlocale(locale.LC_ALL, "")  # Use user's default locale
except locale.Error:
    # Fallback to C locale if user's locale is not available
    locale.setlocale(locale.LC_ALL, "C")

# Import custom modules
from roadmap_analyzer.capacity import CapacityCalculator, TimePeriodType
from roadmap_analyzer.capacity_chart import create_capacity_chart
from roadmap_analyzer.capacity_loader import create_capacity_dataframe, load_capacity_data
from roadmap_analyzer.components import (
    add_notification,
    display_data_tab,
    display_sidebar_controls,
    display_simulation_metrics,
    display_status_tab,
    show_welcome_screen,
)
from roadmap_analyzer.config import AppConfig, load_config
from roadmap_analyzer.config_loader import load_and_apply_config
from roadmap_analyzer.data_loader import load_work_items
from roadmap_analyzer.gantt_chart import create_gantt_chart
from roadmap_analyzer.probability_chart import create_probability_chart
from roadmap_analyzer.simulation import SimulationEngine
from roadmap_analyzer.statistics import display_detailed_statistics
from roadmap_analyzer.utils import format_number, is_working_day

# Load application configuration
APP_CONFIG: AppConfig = load_config()

# Page configuration using config model
st.set_page_config(page_title=APP_CONFIG.ui.page_title, page_icon=APP_CONFIG.ui.page_icon, layout=APP_CONFIG.ui.layout)

# Add custom CSS for professional styling
st.markdown(
    """
<style>
    /* Import professional fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global font styling */
    .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
    }
    
    /* Main title styling */
    .main .block-container {
        padding-top: 2rem;
    }
    
    /* Metric styling */
    [data-testid="stMetricValue"] {
        font-size: 1.75rem !important;
        font-weight: 600 !important;
        color: #1f2937 !important;
        line-height: 1.2 !important;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.875rem !important;
        font-weight: 500 !important;
        color: #6b7280 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    [data-testid="stMetricDelta"] {
        font-size: 0.875rem !important;
        font-weight: 500 !important;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        padding: 8px 16px;
        font-weight: 500;
        font-size: 0.875rem;
        border-radius: 6px 6px 0 0;
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        color: #64748b;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #ffffff !important;
        color: #1e293b !important;
        border-bottom: 2px solid #3b82f6 !important;
    }
    
    /* Comprehensive table font size styling with high specificity */
    
    /* All Streamlit dataframes and tables */
    .stDataFrame, .stTable {
        font-size: 18px !important;
    }
    
    .stDataFrame table, .stTable table {
        font-size: 18px !important;
    }
    
    .stDataFrame tbody tr td, .stTable tbody tr td {
        font-size: 18px !important;
        color: #1f2937 !important;
        border-bottom: 1px solid #f1f5f9 !important;
    }
    
    .stDataFrame thead tr th, .stTable thead tr th {
        font-size: 17px !important;
        background-color: #f8fafc !important;
        color: #374151 !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        border-bottom: 2px solid #e2e8f0 !important;
    }
    
    /* Additional selectors for maximum coverage */
    div[data-testid="stDataFrame"] table {
        font-size: 18px !important;
    }
    
    div[data-testid="stDataFrame"] td, 
    div[data-testid="stDataFrame"] th {
        font-size: 18px !important;
    }
    
    /* Force font size on all table elements */
    .dataframe, .dataframe td, .dataframe th {
        font-size: 18px !important;
    }
    
    /* Streamlit's internal table classes */
    .element-container table {
        font-size: 18px !important;
    }
    
    .element-container td, .element-container th {
        font-size: 18px !important;
    }
    
    /* General table styling */
    .stDataFrame {
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #f8fafc;
    }
    
    /* Button styling */
    .stButton > button {
        font-weight: 500;
        border-radius: 6px;
        border: 1px solid #d1d5db;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        border-color: #9ca3af;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    .stButton > button[kind="primary"] {
        background-color: #3b82f6;
        border-color: #3b82f6;
        font-weight: 600;
    }
    
    .stButton > button[kind="primary"]:hover {
        background-color: #2563eb;
        border-color: #2563eb;
    }
    
    /* Subheader styling */
    .stApp h2 {
        color: #1e293b;
        font-weight: 600;
        margin-bottom: 1rem;
        border-bottom: 2px solid #e2e8f0;
        padding-bottom: 0.5rem;
    }
    
    .stApp h3 {
        color: #374151;
        font-weight: 500;
        margin-bottom: 0.75rem;
    }
    
    /* Info/warning/error message styling */
    .stAlert {
        border-radius: 8px;
        border-left: 4px solid;
        font-weight: 500;
    }
    
    /* File uploader styling */
    .stFileUploader {
        border: 2px dashed #d1d5db;
        border-radius: 8px;
        padding: 1rem;
        background-color: #f9fafb;
    }
    
    /* Progress bar styling */
    .stProgress .st-bo {
        background-color: #e5e7eb;
        border-radius: 4px;
    }
    
    .stProgress .st-bp {
        background-color: #3b82f6;
        border-radius: 4px;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Description in main area
st.markdown("Analyze project timelines with Monte Carlo simulation to assess on-time delivery probabilities")


def run_simulation_workflow(work_items, capacity_value, start_date, time_period_type, num_simulations, capacity_dict=None):
    """Run the Monte Carlo simulation workflow.

    Args:
        work_items: List of work items to simulate
        capacity_value: Capacity value per time period (quarter or month)
        start_date: Start date for the simulation
        time_period_type: Type of time period ("quarterly" or "monthly")
        num_simulations: Number of Monte Carlo simulations to run
        capacity_dict: Optional dictionary mapping period strings to capacity values

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

    # Create capacity calculator with the selected time period and capacity data
    period_type = TimePeriodType.QUARTERLY if time_period_type == "quarterly" else TimePeriodType.MONTHLY
    capacity_calculator = CapacityCalculator(APP_CONFIG, period_type, capacity_dict)
    simulation_engine = SimulationEngine(APP_CONFIG, capacity_calculator)

    # Run simulation with progress callback
    # The capacity calculator already has the correct period type from initialization
    # Note: capacity_dict is now passed directly to the CapacityCalculator constructor
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
    st.sidebar.title("Project Roadmap Monte Carlo Analysis")

    uploaded_file = st.sidebar.file_uploader("Upload Excel File", type=["xlsx", "xls"])

    if uploaded_file:
        # Clear notifications and simulation results when loading a new file
        # Initialize if needed
        if "notifications" not in st.session_state:
            st.session_state.notifications = []
        else:
            st.session_state.notifications = []
            
        # Clear simulation results when loading a new file
        st.session_state.stats = None

        # Add initial notification about clearing
        add_notification("Status messages and simulation results cleared - loading new file", "info")

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

    # Load capacity data if available
    capacity_dict = load_capacity_data(file_path)

    # Create main tabs for data view, capacity view, simulation view, and status
    data_tab, capacity_tab, simulation_tab, status_tab = st.tabs(["Roadmap Data", "Capacity Data", "Simulation Results", "Status"])

    # Data tab content
    with data_tab:
        display_data_tab(work_items)

    # Capacity tab content
    with capacity_tab:
        st.subheader("Capacity Planning")

        # Create capacity dataframe for visualization
        period_type = TimePeriodType.MONTHLY if time_period_type == "monthly" else TimePeriodType.QUARTERLY

        # Find the earliest start date and latest end date from work items
        earliest_start = start_date
        latest_end = max([item.due_date for item in work_items])

        # Create capacity dataframe
        capacity_df = create_capacity_dataframe(capacity_dict, earliest_start, latest_end, period_type, capacity_value)

        # Display capacity data in a table
        if not capacity_dict:
            st.info("No custom capacity data found. Using default capacity values.")
        else:
            # Use notification system instead of displaying message in the tab
            add_notification(f"✅ Loaded {len(capacity_dict)} custom capacity entries from Excel file", "info")

        # Create and display capacity chart
        capacity_chart = create_capacity_chart(capacity_df)
        st.plotly_chart(capacity_chart, use_container_width=True)

        # Display capacity data table
        if not capacity_df.empty:
            display_df = capacity_df[["DisplayPeriod", "Capacity"]].copy()
            display_df.columns = ["Period", "Capacity (PD)"]
            # Format capacity numbers with locale-aware thousand separators
            display_df["Capacity (PD)"] = display_df["Capacity (PD)"].apply(lambda x: format_number(x))

            # Apply styling to increase font size
            styled_capacity_df = display_df.style.set_table_styles(
                [
                    {"selector": "th", "props": [("font-size", "16px"), ("font-weight", "bold")]},
                    {"selector": "td", "props": [("font-size", "16px")]},
                    {"selector": "table", "props": [("font-size", "16px")]},
                ]
            )

            st.dataframe(styled_capacity_df, use_container_width=True)

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
            st.subheader("Visualizations")

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
        else:
            # Show informational message when no simulation results are available
            if uploaded_file and not run_simulation:
                st.info(
                    "📊 **New file loaded or parameters changed - Run simulation to see results**\n\n"
                    "Your file has been loaded successfully, but simulation results need to be generated.\n"
                    "Click the **'Run Simulation'** button in the sidebar to generate results.\n\n"
                    "Results will include timeline projections, probability charts, and detailed statistics."
                )
            else:
                st.info(
                    "📊 **No simulation results available**\n\n"
                    "To view simulation results and visualizations:\n"
                    "1. Configure your simulation parameters in the sidebar\n"
                    "2. Click the **'Run Simulation'** button\n\n"
                    "Results will include timeline projections, probability charts, and detailed statistics."
                )


if __name__ == "__main__":
    # Command line arguments are automatically handled above
    main()
