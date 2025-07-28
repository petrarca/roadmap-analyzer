import sys
from datetime import datetime, timedelta
from typing import List

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from roadmap_analyzer.capacity import CapacityCalculator, TimePeriodType
from roadmap_analyzer.config import APP_CONFIG
from roadmap_analyzer.data_loader import load_work_items
from roadmap_analyzer.models import WorkItem
from roadmap_analyzer.simulation import SimulationEngine
from roadmap_analyzer.utils import convert_to_date, is_working_day

# Page configuration using config model
st.set_page_config(page_title=APP_CONFIG.ui.page_title, page_icon=APP_CONFIG.ui.page_icon, layout=APP_CONFIG.ui.layout)

# Title and description
st.title("📊 Project Roadmap Monte Carlo Analysis")
st.markdown("Analyze project timelines with Monte Carlo simulation to assess on-time delivery probabilities")

# Sidebar for configuration
st.sidebar.header("⚙️ Configuration")

# Get default file path from command line arguments if provided
default_file_path = ""
if len(sys.argv) > 1:
    default_file_path = sys.argv[1]

# File path input with on_change detection
file_path = st.sidebar.text_input(
    "Excel File Path",
    value=default_file_path,
    help="Path to the Excel file containing project data",
    key="file_path_input",  # Add a key for state management
)

# Check if Enter was pressed (detected by change in session state)
file_reload = st.sidebar.button("Reload Data", help="Reload data from the Excel file")

# Capacity input
capacity_per_quarter = st.sidebar.number_input(
    "Quarterly Capacity (PD)",
    value=APP_CONFIG.simulation.default_capacity_per_quarter,
    step=50,
    help="Available person days (PD) per quarter for project work",
)

# Number of simulations
num_simulations = st.sidebar.selectbox(
    "Number of Simulations",
    options=APP_CONFIG.simulation.simulation_options,
    index=len(APP_CONFIG.simulation.simulation_options) - 1,  # Default to highest option
    help="More simulations = more accurate results but slower processing",
)

# Start date - use today's date as default
start_date = st.sidebar.date_input("Project Start Date", value=datetime.now().date(), help="When the projects will begin")

# Check if the selected date is a working day
if not is_working_day(start_date):
    st.sidebar.warning(f"⚠️ {start_date.strftime('%Y-%m-%d')} is not a working day (weekend). Projects will start on the next working day.")
    # Calculate the next working day
    next_working_day = start_date
    while not is_working_day(next_working_day):
        next_working_day += timedelta(days=1)
    st.sidebar.info(f"Next working day: {next_working_day.strftime('%Y-%m-%d')}")

# Add a separator in the sidebar
st.sidebar.markdown("---")

# Run simulation button in sidebar
run_simulation = st.sidebar.button("🚀 Run Monte Carlo Simulation", type="primary")


# DataFrame utilities for Streamlit display


def prepare_dataframe_for_display(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare DataFrame for Streamlit display with PyArrow compatibility.

    This function ensures all columns have types that are compatible with PyArrow
    serialization, preventing Streamlit display errors.

    Args:
        df: DataFrame to prepare

    Returns:
        DataFrame with PyArrow-compatible column types
    """
    df_copy = df.copy()

    # Handle columns that might contain mixed int/None values
    for col in df_copy.columns:
        # Check for columns with mixed numeric/None values (common PyArrow issue)
        if df_copy[col].dtype in ["object", "float64"] and col.lower() in ["dependency", "dependencies"]:
            # Convert to nullable integer type for PyArrow compatibility
            df_copy[col] = df_copy[col].astype("Int64")
        elif df_copy[col].dtype == "object":
            # Check if column contains only numeric values and None/NaN
            non_null_values = df_copy[col].dropna()
            if len(non_null_values) > 0:
                # Try to detect if all non-null values are numeric
                try:
                    # Test conversion to numeric
                    pd.to_numeric(non_null_values, errors="raise")
                    # If successful, convert to nullable integer
                    df_copy[col] = pd.to_numeric(df_copy[col], errors="coerce").astype("Int64")
                except (ValueError, TypeError):
                    # Keep as object type if not numeric
                    pass

    return df_copy


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
                "Item": item.initiative,
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
def create_gantt_chart(stats, project_start_date, work_items):
    """Create Gantt chart visualization"""
    # Create figure
    fig = go.Figure()

    # Sort projects by position
    project_order = {item.initiative: item.position for item in work_items}
    sorted_projects = sorted(stats.items(), key=lambda x: project_order[x[0]])
    # Reverse the order to match the data table (C1 at the top)
    sorted_projects = list(reversed(sorted_projects))

    for idx, (project_name, project_stats) in enumerate(sorted_projects):
        # Use idx directly to maintain original data order (top to bottom)
        y_pos = idx

        # Start dates should already be calculated in run_simulation_workflow
        # If they're missing, skip this project (shouldn't happen in normal flow)
        if project_stats.start_p10 is None:
            continue

        # P90 range (worst case)
        fig.add_trace(
            go.Scatter(
                x=[project_stats.start_p90, project_stats.p90],
                y=[y_pos - 0.15, y_pos - 0.15],  # Offset to avoid overlap
                mode="lines",
                line=dict(color="#FF7F7F", width=20),  # Brighter red for worst case
                name="P90 Range",
                showlegend=(idx == 0),
                hovertemplate=f"{project_name}<br>Start: %{{x[0]|%b %d, %Y}}<br>P90: %{{x[1]|%b %d, %Y}}<extra></extra>",
            )
        )

        # P50 range (most likely)
        fig.add_trace(
            go.Scatter(
                x=[project_stats.start_p50, project_stats.p50],
                y=[y_pos, y_pos],  # Keep at center
                mode="lines",
                line=dict(color="#FFA500", width=15),  # Orange for most likely
                name="P50 Range",
                showlegend=(idx == 0),
                hovertemplate=f"{project_name}<br>Start: %{{x[0]|%b %d, %Y}}<br>P50: %{{x[1]|%b %d, %Y}}<extra></extra>",
            )
        )

        # P10 range (best case)
        fig.add_trace(
            go.Scatter(
                x=[project_stats.start_p10, project_stats.p10],
                y=[y_pos + 0.15, y_pos + 0.15],  # Offset to avoid overlap
                mode="lines",
                line=dict(color="#4CAF50", width=10),  # Deeper green for best case
                name="P10 Range",
                showlegend=(idx == 0),
                hovertemplate=f"{project_name}<br>Start: %{{x[0]|%b %d, %Y}}<br>P10: %{{x[1]|%b %d, %Y}}<extra></extra>",
            )
        )

        # Due date marker - make it more prominent
        fig.add_trace(
            go.Scatter(
                x=[project_stats.due_date],
                y=[y_pos],
                mode="markers",
                marker=dict(symbol="diamond", size=12, color="blue", line=dict(color="darkblue", width=2)),
                name="Due Date",
                showlegend=(idx == 0),
                hovertemplate=f"{project_name}<br>Due Date: %{{x|%b %d, %Y}}<extra></extra>",
            )
        )

        # Add vertical line for due date to make it even more visible
        fig.add_trace(
            go.Scatter(
                x=[project_stats.due_date, project_stats.due_date],
                y=[y_pos - 0.3, y_pos + 0.3],
                mode="lines",
                line=dict(color="blue", width=3, dash="dash"),
                name="Due Date Line",
                showlegend=False,
                hovertemplate=f"{project_name}<br>Due Date: %{{x[0]|%b %d, %Y}}<extra></extra>",
            )
        )

    fig.update_layout(
        title="Project Timeline with Confidence Intervals",
        xaxis_title="Date",
        yaxis=dict(
            ticktext=[p[0] for p in sorted_projects],  # Already reversed to match data table
            tickvals=list(range(len(sorted_projects))),
            tickmode="array",
        ),
        height=100 + len(sorted_projects) * 80,
        showlegend=True,
        hovermode="closest",
    )

    return fig


# Create probability chart
def create_probability_chart(stats):
    """Create bar chart of on-time probabilities"""
    projects = list(stats.keys())
    probabilities = [stats[p].on_time_probability for p in projects]

    # Color based on probability using config
    prob_colors = APP_CONFIG.ui.probability_colors
    colors = [prob_colors.high if p >= 80 else prob_colors.medium if p >= 30 else prob_colors.low for p in probabilities]

    fig = go.Figure(data=[go.Bar(x=projects, y=probabilities, text=[f"{p:.1f}%" for p in probabilities], textposition="auto", marker_color=colors)])

    fig.update_layout(
        title="On-Time Delivery Probability by Project", xaxis_title="Project", yaxis_title="Probability (%)", yaxis_range=[0, 105], showlegend=False
    )

    return fig


# UI Helper Functions
def show_welcome_screen():
    """Display welcome screen with example format when no file is provided."""
    st.info("👋 Welcome! Please enter an Excel file path in the sidebar to load your project data.")

    # Show example format
    st.subheader("📋 Expected Excel Format:")
    example_df = pd.DataFrame(
        {
            "Position": [1, 2, 3],
            "Item": ["Project A", "Project B", "Project C"],
            "Due date": ["30/11/2025", "30/11/2025", "30/05/2026"],
            "Dependency": ["", "1", "2"],  # Keep as strings to avoid mixed types
            "Best": [10, 15, 8],
            "Likely": [15, 20, 12],
            "Worst": [25, 30, 18],
        }
    )
    st.dataframe(example_df, use_container_width=True)

    st.markdown(
        """
        ### 📝 Instructions:
        1. Create an Excel file with the columns shown above
        2. Enter the file path in the sidebar
        3. Adjust the configuration settings as needed
        4. Click "Run Monte Carlo Simulation" to analyze your projects
        
        ### 📊 What you'll get:
        - **Timeline Analysis**: See when projects are likely to complete
        - **Risk Assessment**: Understand probability of on-time delivery
        - **Resource Planning**: Optimize capacity allocation
        - **Dependency Impact**: Visualize how delays cascade through projects
        """
    )


def display_data_tab(work_items):
    """Display the data tab with loaded work items."""
    st.subheader("Loaded Project Data")

    # Create display-ready DataFrame using centralized function
    display_df = create_work_items_display_dataframe(work_items)
    st.dataframe(display_df, use_container_width=True)


def display_simulation_metrics(stats):
    """Display simulation metrics and alerts."""
    col1, col2, col3, col4 = st.columns(4)

    total_projects = len(stats)
    on_time_projects = sum(1 for s in stats.values() if s.on_time_probability >= 50)
    avg_probability = np.mean([s.on_time_probability for s in stats.values()])

    col1.metric("Total Projects", total_projects)
    col2.metric("Likely On-Time", f"{on_time_projects}/{total_projects}")
    col3.metric("Avg. On-Time Probability", f"{avg_probability:.1f}%")
    col4.metric("At-Risk Projects", total_projects - on_time_projects)

    # Alert box
    if on_time_projects == total_projects:
        st.success("✅ All projects have a good probability of meeting their deadlines!")
    elif on_time_projects >= total_projects * 0.7:
        st.warning("⚠️ Some projects may face delays. Consider increasing capacity or adjusting timelines.")
    else:
        st.error("🚨 Many projects are at risk of delays. Review capacity allocation and dependencies.")


def display_detailed_statistics(stats):
    """Display detailed statistics table with styling."""
    st.subheader("📈 Detailed Statistics")

    stats_df = pd.DataFrame(
        [
            {
                "Project": project,
                "Due Date": stats[project].due_date.strftime("%b %d, %Y"),
                "P10 (Best Case)": stats[project].p10.strftime("%b %d, %Y"),
                "P50 (Most Likely)": stats[project].p50.strftime("%b %d, %Y"),
                "P90 (Worst Case)": stats[project].p90.strftime("%b %d, %Y"),
                "On-Time Probability": f"{stats[project].on_time_probability:.1f}%",
            }
            for project in stats
        ]
    )

    # Apply color styling to dates based on whether they're on time
    def style_dates(val, project, col):
        due_date = convert_to_date(stats[project].due_date)

        if col == "P10 (Best Case)":
            date_val = convert_to_date(stats[project].p10)
            on_time = date_val <= due_date
        elif col == "P50 (Most Likely)":
            date_val = convert_to_date(stats[project].p50)
            on_time = date_val <= due_date
        elif col == "P90 (Worst Case)":
            date_val = convert_to_date(stats[project].p90)
            on_time = date_val <= due_date
        else:
            return val

        if on_time:
            return f'<span style="color: green;">{val}</span>'
        else:
            return f'<span style="color: red;">{val}</span>'

    # Apply color styling to probability based on value
    def style_probability(val, prob):
        prob_value = float(prob.strip("%"))
        if prob_value >= 90:
            return f'<span style="color: green;">{val}</span>'
        elif prob_value >= 40:
            return f'<span style="color: orange;">{val}</span>'
        else:
            return f'<span style="color: red;">{val}</span>'

    # Create styled dataframe
    styled_df = stats_df.copy()

    # Apply styling to dates and probability
    for idx, row in styled_df.iterrows():
        project = row["Project"]
        prob = row["On-Time Probability"]

        styled_df.at[idx, "P10 (Best Case)"] = style_dates(row["P10 (Best Case)"], project, "P10 (Best Case)")
        styled_df.at[idx, "P50 (Most Likely)"] = style_dates(row["P50 (Most Likely)"], project, "P50 (Most Likely)")
        styled_df.at[idx, "P90 (Worst Case)"] = style_dates(row["P90 (Worst Case)"], project, "P90 (Worst Case)")
        styled_df.at[idx, "On-Time Probability"] = style_probability(prob, prob)

    # Display the styled dataframe
    st.markdown(styled_df.to_html(escape=False, index=False), unsafe_allow_html=True)

    # Add some CSS to improve the table styling
    st.markdown(
        """
    <style>
    table {
        width: 100%;
        border-collapse: collapse;
    }
    th {
        background-color: #f2f2f2;
        font-weight: bold;
        text-align: left;
        padding: 8px;
    }
    td {
        padding: 8px;
        border-bottom: 1px solid #ddd;
    }
    tr:nth-child(even) {
        background-color: #f9f9f9;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )


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
    # Check if file path is empty
    if not file_path.strip():
        show_welcome_screen()
        return

    # Load data if file path is provided
    work_items = load_work_items(file_path, APP_CONFIG)

    if not work_items:
        st.error(f"Could not load file: {file_path}. Please check that the file exists and has the correct format.")

        # Show expected format
        st.subheader("Expected Excel Format:")
        example_df = pd.DataFrame(
            {
                "Position": [1, 2, 3],
                "Item": ["Project A", "Project B", "Project C"],
                "Due date": ["30/11/2025", "30/11/2025", "30/05/2026"],
                "Dependency": [None, 1, None],
                "Best": [2400, 250, 1400],
                "Likely": [2832, 295, 1652],
                "Worst": [3120, 325, 1820],
            }
        )
        # Use centralized function to ensure PyArrow compatibility
        example_df = prepare_dataframe_for_display(example_df)
        st.dataframe(example_df)
        return

    # Create main tabs for data view and simulation view
    data_tab, simulation_tab = st.tabs(["📋 Project Data", "📊 Simulation Results"])

    # Data tab content
    with data_tab:
        display_data_tab(work_items)

    # Simulation tab content
    with simulation_tab:
        # Check if the run simulation button in sidebar was clicked
        if run_simulation:
            with st.spinner("Running simulations..."):
                stats = run_simulation_workflow(work_items, capacity_per_quarter, start_date, num_simulations)

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
