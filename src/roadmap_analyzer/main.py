import sys
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


# Helper function to convert various date types to date objects
def _convert_to_date(date_obj):
    """Convert various date objects to datetime.date"""
    if hasattr(date_obj, "date") and callable(getattr(date_obj, "date")):
        # It's a datetime or Timestamp with a date() method
        return date_obj.date()
    elif isinstance(date_obj, date):
        # It's already a date object
        return date_obj
    else:
        # Try to convert to string and parse
        try:
            return pd.to_datetime(str(date_obj)).date()
        except (ValueError, TypeError):
            # Return the original if all else fails
            return date_obj


# Page configuration
st.set_page_config(page_title="Project Roadmap Monte Carlo Analysis", page_icon="📊", layout="wide")

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
    "Quarterly Capacity (PD)", value=1300, step=50, help="Available person days (PD) per quarter for project work"
)

# Number of simulations
num_simulations = st.sidebar.selectbox(
    "Number of Simulations",
    options=[5000, 10000, 20000],
    index=2,  # Default to 20000
    help="More simulations = more accurate results but slower processing",
)

# Start date - use today's date as default
start_date = st.sidebar.date_input("Project Start Date", value=datetime.now().date(), help="When the projects will begin")

# Add a separator in the sidebar
st.sidebar.markdown("---")

# Run simulation button in sidebar
run_simulation = st.sidebar.button("🚀 Run Monte Carlo Simulation", type="primary")


# Load data function
# Removed caching to allow reloading data when requested
def load_project_data(file_path):
    """Load project data from Excel file"""
    try:
        df = pd.read_excel(file_path)
        # Ensure required columns exist
        required_cols = ["Position", "Initiative", "Due date", "Dependency", "Best", "Most likely", "Worst"]
        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            st.error(f"Missing required columns: {missing_cols}")
            return None

        # Convert due dates to datetime
        df["Due date"] = pd.to_datetime(df["Due date"])

        # Clean up dependency column (convert to int or None)
        df["Dependency"] = df["Dependency"].apply(lambda x: int(x) if pd.notna(x) else None)

        return df
    except FileNotFoundError:
        st.error(f"File not found: {file_path}")
        return None
    except Exception as e:
        st.error(f"Error loading file: {str(e)}")
        return None


# Triangular distribution function
def triangular_random(min_val, mode_val, max_val):
    """Generate random value from triangular distribution"""
    return np.random.triangular(min_val, mode_val, max_val)


# Add working days function
def add_working_days(start_date, days):
    """Add working days to a date (excluding weekends)"""
    current = start_date
    days_added = 0

    while days_added < days:
        current += timedelta(days=1)
        if current.weekday() < 5:  # Monday = 0, Friday = 4
            days_added += 1

    return current


# Get quarter from date
def get_quarter_from_date(date):
    """Get quarter string from date"""
    year = date.year
    quarter = (date.month - 1) // 3 + 1
    return f"{year}-Q{quarter}"


# Monte Carlo simulation function
def run_monte_carlo_simulation(df, capacity_per_quarter, start_date, num_simulations):
    """Run Monte Carlo simulation for project timeline"""
    projects = df.to_dict("records")
    simulation_results = []

    progress_bar = st.progress(0)
    status_text = st.empty()

    for sim in range(num_simulations):
        if sim % 100 == 0:
            progress = sim / num_simulations
            progress_bar.progress(progress)
            status_text.text(f"Running simulation {sim + 1} of {num_simulations}...")

        project_results = []
        completion_dates = {}
        capacity_usage = {}

        for project in projects:
            # Sample effort from triangular distribution
            effort = triangular_random(project["Best"], project["Most likely"], project["Worst"])

            # Determine start date
            project_start_date = start_date
            if project["Dependency"] is not None:
                dep_completion = completion_dates.get(project["Dependency"])
                if dep_completion and dep_completion > project_start_date:
                    project_start_date = dep_completion

            # Calculate completion considering capacity constraints
            remaining_effort = effort
            current_date = project_start_date

            while remaining_effort > 0:
                quarter = get_quarter_from_date(current_date)
                if quarter not in capacity_usage:
                    capacity_usage[quarter] = 0

                available_capacity = capacity_per_quarter - capacity_usage[quarter]
                effort_this_quarter = min(remaining_effort, available_capacity)

                capacity_usage[quarter] += effort_this_quarter
                remaining_effort -= effort_this_quarter

                if remaining_effort > 0:
                    # Move to next quarter
                    if current_date.month >= 10:
                        current_date = current_date.replace(year=current_date.year + 1, month=1, day=1)
                    else:
                        current_date = current_date.replace(month=current_date.month + 3, day=1)
                else:
                    # Calculate exact completion date based on effort
                    # We need to calculate what fraction of the quarter was used
                    # and add the appropriate number of working days
                    fraction_of_quarter = effort_this_quarter / capacity_per_quarter
                    working_days_in_quarter = 65  # Approx. working days per quarter
                    days_to_add = int(fraction_of_quarter * working_days_in_quarter)
                    current_date = add_working_days(current_date, days_to_add)

            completion_date = current_date
            completion_dates[project["Position"]] = completion_date

            project_results.append(
                {
                    "name": project["Initiative"],
                    "position": project["Position"],
                    "effort": effort,
                    "start_date": project_start_date,
                    "completion_date": completion_date,
                    "due_date": project["Due date"],
                    "on_time": _convert_to_date(completion_date) <= _convert_to_date(project["Due date"]),
                }
            )

        simulation_results.append(project_results)

    progress_bar.progress(1.0)
    status_text.text("Simulation complete!")

    return simulation_results


# Calculate start dates for Gantt chart
def calculate_start_dates(stats, df):
    """Calculate start dates for each project based on dependencies"""
    # Sort projects by position to ensure dependencies are calculated first
    sorted_projects = sorted(stats.items(), key=lambda x: x[1]["position"])

    # First pass: set default start dates to project start date
    for project_name, project_stats in sorted_projects:
        project_stats["start_p10"] = project_stats.get("start_date", pd.Timestamp("2025-07-24"))
        project_stats["start_p50"] = project_stats.get("start_date", pd.Timestamp("2025-07-24"))
        project_stats["start_p90"] = project_stats.get("start_date", pd.Timestamp("2025-07-24"))

    # Second pass: update start dates based on dependencies
    for project_name, project_stats in sorted_projects:
        position = project_stats["position"]

        # Find the dependency for this project in the original dataframe
        dependency_position = None
        for _, row in df.iterrows():
            if row["Position"] == position and pd.notna(row["Dependency"]):
                dependency_position = int(row["Dependency"])
                break

        # If there's a dependency, update start dates
        if dependency_position is not None:
            for dep_name, dep_stats in stats.items():
                if dep_stats["position"] == dependency_position:
                    # Start dates are the completion dates of the dependency
                    project_stats["start_p10"] = _convert_to_date(dep_stats["p10"])
                    project_stats["start_p50"] = _convert_to_date(dep_stats["p50"])
                    project_stats["start_p90"] = _convert_to_date(dep_stats["p90"])
                    break


# Analyze results function
def analyze_results(simulation_results, df):
    """Analyze simulation results and calculate statistics"""
    stats = {}

    for idx, project in df.iterrows():
        project_name = project["Initiative"]
        position = project["Position"]

        # Extract results for this project
        project_results = []
        for sim in simulation_results:
            for result in sim:
                if result["position"] == position:
                    project_results.append(result)
                    break

        # Calculate statistics
        on_time_count = sum(1 for r in project_results if r["on_time"])
        completion_dates = [r["completion_date"] for r in project_results]
        completion_dates.sort()

        n = len(completion_dates)
        stats[project_name] = {
            "position": position,
            "due_date": project["Due date"],
            "on_time_probability": (on_time_count / n) * 100,
            "p10": completion_dates[int(n * 0.1)],
            "p50": completion_dates[int(n * 0.5)],
            "p90": completion_dates[int(n * 0.9)],
            "best_effort": project["Best"],
            "likely_effort": project["Most likely"],
            "worst_effort": project["Worst"],
        }

    return stats


# Create Gantt chart
def create_gantt_chart(stats, start_date, df):
    """Create Gantt chart visualization"""
    fig = go.Figure()

    # Sort projects by position
    sorted_projects = sorted(stats.items(), key=lambda x: x[1]["position"])

    for idx, (project_name, project_stats) in enumerate(sorted_projects):
        y_pos = len(sorted_projects) - idx - 1

        # Get the start dates for this project (accounting for dependencies)
        if "start_p10" not in project_stats:
            # Calculate start dates if not already present
            calculate_start_dates(stats, df)

        # P90 range (worst case)
        fig.add_trace(
            go.Scatter(
                x=[project_stats["start_p90"], project_stats["p90"]],
                y=[y_pos, y_pos],
                mode="lines",
                line=dict(color="lightcoral", width=20),
                name="P90 Range",
                showlegend=(idx == 0),
                hovertemplate=f"{project_name}<br>Start: %{{x[0]|%b %d, %Y}}<br>P90: %{{x[1]|%b %d, %Y}}<extra></extra>",
            )
        )

        # P50 range (most likely)
        fig.add_trace(
            go.Scatter(
                x=[project_stats["start_p50"], project_stats["p50"]],
                y=[y_pos, y_pos],
                mode="lines",
                line=dict(color="lightsalmon", width=15),
                name="P50 Range",
                showlegend=(idx == 0),
                hovertemplate=f"{project_name}<br>Start: %{{x[0]|%b %d, %Y}}<br>P50: %{{x[1]|%b %d, %Y}}<extra></extra>",
            )
        )

        # P10 range (best case)
        fig.add_trace(
            go.Scatter(
                x=[project_stats["start_p10"], project_stats["p10"]],
                y=[y_pos, y_pos],
                mode="lines",
                line=dict(color="lightgreen", width=10),
                name="P10 Range",
                showlegend=(idx == 0),
                hovertemplate=f"{project_name}<br>Start: %{{x[0]|%b %d, %Y}}<br>P10: %{{x[1]|%b %d, %Y}}<extra></extra>",
            )
        )

        # Due date marker
        fig.add_trace(
            go.Scatter(
                x=[project_stats["due_date"]],
                y=[y_pos],
                mode="markers",
                marker=dict(symbol="line-ns", size=20, color="blue"),
                name="Due Date",
                showlegend=(idx == 0),
                hovertemplate=f"{project_name}<br>Due: %{{x|%b %d, %Y}}<extra></extra>",
            )
        )

    fig.update_layout(
        title="Project Timeline with Confidence Intervals",
        xaxis_title="Date",
        yaxis=dict(ticktext=[p[0] for p in sorted_projects], tickvals=list(range(len(sorted_projects))), tickmode="array"),
        height=100 + len(sorted_projects) * 80,
        showlegend=True,
        hovermode="closest",
    )

    return fig


# Create probability chart
def create_probability_chart(stats):
    """Create bar chart of on-time probabilities"""
    projects = list(stats.keys())
    probabilities = [stats[p]["on_time_probability"] for p in projects]

    # Color based on probability
    colors = ["green" if p >= 80 else "orange" if p >= 30 else "red" for p in probabilities]

    fig = go.Figure(data=[go.Bar(x=projects, y=probabilities, text=[f"{p:.1f}%" for p in probabilities], textposition="auto", marker_color=colors)])

    fig.update_layout(
        title="On-Time Delivery Probability by Project", xaxis_title="Project", yaxis_title="Probability (%)", yaxis_range=[0, 105], showlegend=False
    )

    return fig


# Main app
def main():
    # Check if file path is empty
    if not file_path.strip():
        st.info("👋 Welcome! Please enter an Excel file path in the sidebar to load your project data.")

        # Show example format
        st.subheader("📋 Expected Excel Format:")
        example_df = pd.DataFrame(
            {
                "Position": [1, 2, 3],
                "Initiative": ["Project A", "Project B", "Project C"],
                "Due date": ["30/11/2025", "30/11/2025", "30/05/2026"],
                "Dependency": [None, 1, None],
                "Best": [2400, 250, 1400],
                "Most likely": [2832, 295, 1652],
                "Worst": [3120, 325, 1820],
            }
        )
        st.dataframe(example_df)

        # Add some helpful instructions
        st.markdown("""
        ### 🚀 Getting Started
        1. Enter the path to your Excel file in the sidebar
        2. Click 'Reload Data' to load your data
        3. Adjust the configuration settings as needed
        4. Click 'Run Monte Carlo Simulation' to analyze your project timeline
        
        You can also start the app with a file path: `streamlit run src/roadmap_analyzer/main.py -- your_file.xlsx`
        or use the task runner: `task run -- your_file.xlsx`
        """)
        return

    # Load data if file path is provided
    df = load_project_data(file_path)

    if df is None:
        st.error(f"Could not load file: {file_path}. Please check that the file exists and has the correct format.")

        # Show expected format
        st.subheader("Expected Excel Format:")
        example_df = pd.DataFrame(
            {
                "Position": [1, 2, 3],
                "Initiative": ["Project A", "Project B", "Project C"],
                "Due date": ["30/11/2025", "30/11/2025", "30/05/2026"],
                "Dependency": [None, 1, None],
                "Best": [2400, 250, 1400],
                "Most likely": [2832, 295, 1652],
                "Worst": [3120, 325, 1820],
            }
        )
        st.dataframe(example_df)
        return

    # Create main tabs for data view and simulation view
    data_tab, simulation_tab = st.tabs(["📋 Project Data", "📊 Simulation Results"])

    # Data tab content
    with data_tab:
        st.subheader("Loaded Project Data")
        st.dataframe(df)

    # Simulation tab content
    with simulation_tab:
        # Check if the run simulation button in sidebar was clicked
        if run_simulation:
            with st.spinner("Running simulations..."):
                # Run simulation
                simulation_results = run_monte_carlo_simulation(df, capacity_per_quarter, start_date, num_simulations)

                # Analyze results
                stats = analyze_results(simulation_results, df)

                # Display results
                st.success(f"✅ Completed {num_simulations:,} simulations!")

                # Summary metrics
                col1, col2, col3, col4 = st.columns(4)

                total_projects = len(stats)
                on_time_projects = sum(1 for s in stats.values() if s["on_time_probability"] >= 50)
                avg_probability = np.mean([s["on_time_probability"] for s in stats.values()])

                col1.metric("Total Projects", total_projects)
                col2.metric("Likely On-Time", f"{on_time_projects}/{total_projects}")
                col3.metric("Average Probability", f"{avg_probability:.1f}%")
                col4.metric("Capacity/Quarter", f"{capacity_per_quarter:,} PD")

                # Alert box
                if on_time_projects == total_projects:
                    st.success("✅ All projects have a good probability of meeting their deadlines!")
                elif on_time_projects >= total_projects * 0.7:
                    st.warning("⚠️ Some projects may face delays. Consider increasing capacity or adjusting timelines.")
                else:
                    st.error("❌ Most projects are at risk of missing deadlines. Immediate action required!")

                # Visualizations
                st.subheader("📊 Visualizations")

                viz_tab1, viz_tab2 = st.tabs(["Timeline View", "Probability Chart"])

                with viz_tab1:
                    gantt_chart = create_gantt_chart(stats, start_date, df)
                    st.plotly_chart(gantt_chart, use_container_width=True)

                with viz_tab2:
                    prob_chart = create_probability_chart(stats)
                    st.plotly_chart(prob_chart, use_container_width=True)

                # Detailed statistics table
                st.subheader("📈 Detailed Statistics")

                stats_df = pd.DataFrame(
                    [
                        {
                            "Project": project,
                            "Due Date": stats[project]["due_date"].strftime("%b %d, %Y"),
                            "P10 (Best Case)": stats[project]["p10"].strftime("%b %d, %Y"),
                            "P50 (Most Likely)": stats[project]["p50"].strftime("%b %d, %Y"),
                            "P90 (Worst Case)": stats[project]["p90"].strftime("%b %d, %Y"),
                            "On-Time Probability": f"{stats[project]['on_time_probability']:.1f}%",
                        }
                        for project in stats
                    ]
                )

                # Apply color styling to dates based on whether they're on time
                def style_dates(val, project, col):
                    due_date = _convert_to_date(stats[project]["due_date"])

                    if col == "P10 (Best Case)":
                        date_val = _convert_to_date(stats[project]["p10"])
                        on_time = date_val <= due_date
                    elif col == "P50 (Most Likely)":
                        date_val = _convert_to_date(stats[project]["p50"])
                        on_time = date_val <= due_date
                    elif col == "P90 (Worst Case)":
                        date_val = _convert_to_date(stats[project]["p90"])
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


if __name__ == "__main__":
    # Command line arguments are automatically handled above
    main()
