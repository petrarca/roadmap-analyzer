"""
UI Components module for roadmap analyzer.
Contains reusable Streamlit UI components.
"""

from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from roadmap_analyzer.utils import prepare_dataframe_for_display

# Global list to store notifications - moved to function to ensure proper initialization


def add_notification(message, notification_type="info", show_inline=False):
    """Add a notification to the status tab

    Args:
        message (str): The notification message
        notification_type (str): Type of notification (info, warning, error, success)
        show_inline (bool): Whether to also show the notification inline
    """
    # Ensure notifications list exists in session state
    if "notifications" not in st.session_state:
        st.session_state.notifications = []

    # Add timestamp to the notification
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.notifications.append({"message": message, "type": notification_type, "timestamp": timestamp})

    # Only show the notification inline if requested
    if show_inline:
        if notification_type == "info":
            st.info(message)
        elif notification_type == "warning":
            st.warning(message)
        elif notification_type == "error":
            st.error(message)
        elif notification_type == "success":
            st.success(message)


def display_status_tab():
    """Display the status tab with all notifications"""
    # Ensure notifications list exists in session state
    if "notifications" not in st.session_state:
        st.session_state.notifications = []

    if not st.session_state.notifications:
        st.info("No notifications yet. Status messages will appear here.")
        return

    # Add clear notifications button
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader(f"📝 Status Messages ({len(st.session_state.notifications)})")
    with col2:
        if st.button("Clear All"):
            st.session_state.notifications = []
            st.experimental_rerun()

    # Display all notifications in reverse chronological order (newest first)
    for notification in reversed(st.session_state.notifications):
        message = notification["message"]
        notification_type = notification["type"]
        timestamp = notification["timestamp"]

        # Format message with timestamp
        formatted_message = f"[{timestamp}] {message}"

        if notification_type == "info":
            st.info(formatted_message)
        elif notification_type == "warning":
            st.warning(formatted_message)
        elif notification_type == "error":
            st.error(formatted_message)
        elif notification_type == "success":
            st.success(formatted_message)


def show_welcome_screen():
    """Display welcome screen with instructions"""
    st.markdown(
        """
        ## 👋 Welcome to the Project Roadmap Analyzer!
        
        This tool helps you analyze project timelines using Monte Carlo simulation to assess on-time delivery probabilities.
        
        ### How to use:
        1. Upload an Excel file with your project data
        2. Configure simulation parameters in the sidebar
        3. Run the simulation to see results
        
        ### Need help?
        - Check the example template for the expected format
        - Adjust capacity and simulation parameters as needed
        """
    )

    # Show example template button
    if st.button("Show Example Template"):
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


def display_data_tab(work_items):
    """Display project data in a table format"""

    # Calculate summary metrics
    total_best = sum(item.best_estimate for item in work_items)
    total_likely = sum(item.most_likely_estimate for item in work_items)
    total_worst = sum(item.worst_estimate for item in work_items)

    # Calculate additional statistics
    avg_likely = total_likely / len(work_items) if work_items else 0
    uncertainty_ratio = total_worst / total_best if total_best > 0 else 0

    # Find largest and smallest work items
    largest_item = max(work_items, key=lambda x: x.most_likely_estimate) if work_items else None
    smallest_item = min(work_items, key=lambda x: x.most_likely_estimate) if work_items else None

    # Project summary section before the table

    # Create a container with a border and background for the summary
    with st.container():
        # Project name header removed

        # First row of metrics
        row1_col1, row1_col2, row1_col3 = st.columns(3)
        with row1_col1:
            st.metric("Work Items", len(work_items))
        with row1_col2:
            st.metric("Avg. per Item", f"{avg_likely:,.0f} PD")
        with row1_col3:
            st.metric("Uncertainty Ratio", f"{uncertainty_ratio:.2f}x")

        # Second row with estimates aligned
        row2_col1, row2_col2, row2_col3 = st.columns(3)
        with row2_col1:
            st.metric("Best Estimate", f"{total_best:,.0f} PD")
        with row2_col2:
            st.metric("Likely Estimate", f"{total_likely:,.0f} PD")
        with row2_col3:
            st.metric("Worst Estimate", f"{total_worst:,.0f} PD")

        # Third row with largest and smallest items
        if largest_item and smallest_item:
            row3_col1, row3_col2, row3_col3 = st.columns(3)
            with row3_col1:
                largest_name = largest_item.item
                if len(largest_name) > 20:  # Truncate long names
                    largest_name = largest_name[:17] + "..."
                st.metric("Largest Item", largest_name, f"{largest_item.most_likely_estimate:,.0f} PD")
            with row3_col2:
                smallest_name = smallest_item.item
                if len(smallest_name) > 20:  # Truncate long names
                    smallest_name = smallest_name[:17] + "..."
                st.metric("Smallest Item", smallest_name, f"{smallest_item.most_likely_estimate:,.0f} PD")
            # Empty third column for alignment
            with row3_col3:
                pass

    # Create DataFrame from work items
    data = []
    for item in work_items:
        data.append(
            {
                "Position": item.position,
                "Item": item.item,
                "Due Date": item.due_date.strftime("%d/%m/%Y") if item.due_date else "N/A",
                "Dependency": item.dependency,
                "Best (PD)": item.best_estimate,
                "Likely (PD)": item.most_likely_estimate,
                "Worst (PD)": item.worst_estimate,
            }
        )

    # Create and display DataFrame
    df = pd.DataFrame(data)
    df = prepare_dataframe_for_display(df)
    st.dataframe(df, use_container_width=True)

    # No duplicate summary stats at the bottom


def display_simulation_metrics(stats):
    """Display summary metrics from simulation results"""
    st.subheader("🎯 Simulation Summary")

    # Calculate metrics
    total_projects = len(stats)
    on_time_projects = sum(1 for p in stats.values() if p.on_time_probability >= 0.8)
    at_risk_projects = sum(1 for p in stats.values() if 0.4 <= p.on_time_probability < 0.8)
    late_projects = sum(1 for p in stats.values() if p.on_time_probability < 0.4)

    # Display metrics in columns
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "On Track",
            f"{on_time_projects}/{total_projects}",
            delta=f"{on_time_projects / total_projects:.0%}" if total_projects > 0 else "N/A",
            delta_color="normal",
        )

    with col2:
        st.metric(
            "At Risk",
            f"{at_risk_projects}/{total_projects}",
            delta=f"{at_risk_projects / total_projects:.0%}" if total_projects > 0 else "N/A",
            delta_color="off",
        )

    with col3:
        st.metric(
            "Likely Late",
            f"{late_projects}/{total_projects}",
            delta=f"{late_projects / total_projects:.0%}" if total_projects > 0 else "N/A",
            delta_color="inverse",
        )

    # Alert box
    if on_time_projects == total_projects:
        add_notification("✅ All projects have a good probability of meeting their deadlines!", "success")
    elif on_time_projects >= total_projects * 0.7:
        add_notification("⚠️ Some projects may face delays. Consider increasing capacity or adjusting timelines.", "warning")
    else:
        add_notification("🚫 Many work items are at risk of delays. Review capacity allocation and dependencies.", "error")


def display_sidebar_controls(file_path=""):
    """Display sidebar controls for simulation parameters

    Args:
        file_path (str): Path to the Excel file (if already loaded)

    Returns:
        tuple: (file_path, start_date, capacity_value, time_period_type, num_simulations, run_simulation)
    """
    with st.sidebar:
        st.header("⚙️ Simulation Settings")

        # Simulation parameters
        st.subheader("Parameters")

        # Get default values from session state if available (loaded from Excel)
        # Otherwise use current date and default values from config
        from roadmap_analyzer.config import APP_CONFIG

        # Start date picker - use value from Excel if available
        default_start_date = datetime.now().date()
        if "start_date" in st.session_state:
            try:
                # Try to parse the date from session state
                default_start_date = pd.to_datetime(st.session_state["start_date"]).date()
            except (ValueError, TypeError):
                # If parsing fails, use current date
                pass

        start_date = st.date_input(
            "Start Date",
            value=default_start_date,
            min_value=datetime.now().date() - timedelta(days=365 * 5),  # Allow dates up to 5 years in the past
            max_value=datetime.now().date() + timedelta(days=365 * 5),  # Allow dates up to 5 years in the future
        )

        # Time period selection (quarter/month)

        # Get default time period from session state if available
        default_period_type = "quarterly"
        if "time_period_type" in st.session_state:
            default_period_type = st.session_state["time_period_type"]

        time_period_options = ["quarterly", "monthly"]
        time_period_type = st.selectbox(
            "Time Period",
            options=time_period_options,
            index=time_period_options.index(default_period_type),
            format_func=lambda x: "Quarterly" if x == "quarterly" else "Monthly",
        )

        # Store selected time period in session state
        st.session_state["time_period_type"] = time_period_type

        # Capacity input - label changes based on selected time period
        default_capacity = APP_CONFIG.simulation.default_capacity_per_quarter
        if time_period_type == "monthly":
            # If no session state value exists, convert quarterly to monthly
            if "capacity_value" not in st.session_state:
                default_capacity = default_capacity / 3
            capacity_label = "Capacity per Month (PD)"
        else:
            capacity_label = "Capacity per Quarter (PD)"

        # Use value from session state if available
        if "capacity_value" in st.session_state:
            default_capacity = st.session_state["capacity_value"]

        capacity_value = st.number_input(capacity_label, min_value=0.1, value=float(default_capacity), step=50.0, format="%.1f")

        # Store capacity value in session state
        st.session_state["capacity_value"] = capacity_value

        # Number of simulations slider - use value from session state if available
        default_simulations = APP_CONFIG.simulation.default_num_simulations
        if "num_simulations" in st.session_state:
            default_simulations = st.session_state["num_simulations"]
        max_simulations = max(APP_CONFIG.simulation.simulation_options)
        num_simulations = st.slider(
            "Number of Simulations",
            min_value=100,
            max_value=max_simulations,
            value=default_simulations,
            step=100,
        )

        # Configuration values loaded from Excel are shown silently without notification

        # Run simulation button - enabled only when data is loaded
        run_simulation = st.button("🚀 Run Simulation", type="primary", disabled=not file_path)

        return file_path, start_date, capacity_value, time_period_type, num_simulations, run_simulation
