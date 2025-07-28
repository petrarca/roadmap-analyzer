"""
UI Components module for roadmap analyzer.
Contains reusable Streamlit UI components.
"""

from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from roadmap_analyzer.utils import prepare_dataframe_for_display


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
    st.subheader("📋 Project Data")

    # Create DataFrame from work items
    data = []
    for item in work_items:
        data.append(
            {
                "Position": item.position,
                "Initiative": item.initiative,
                "Due Date": item.due_date.strftime("%d/%m/%Y") if item.due_date else "N/A",
                "Dependency": item.dependency,
                "Best (hrs)": item.best_estimate,
                "Likely (hrs)": item.most_likely_estimate,
                "Worst (hrs)": item.worst_estimate,
            }
        )

    # Create and display DataFrame
    df = pd.DataFrame(data)
    df = prepare_dataframe_for_display(df)
    st.dataframe(df, use_container_width=True)

    # Display summary stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Projects", len(work_items))
    with col2:
        total_effort = sum(item.most_likely_estimate for item in work_items)
        st.metric("Total Effort (hrs)", f"{total_effort:,.0f}")
    with col3:
        avg_effort = total_effort / len(work_items) if work_items else 0
        st.metric("Avg. Effort per Project (hrs)", f"{avg_effort:,.0f}")


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
        st.success("✅ All projects have a good probability of meeting their deadlines!")
    elif on_time_projects >= total_projects * 0.7:
        st.warning("⚠️ Some projects may face delays. Consider increasing capacity or adjusting timelines.")
    else:
        st.error("🚨 Many projects are at risk of delays. Review capacity allocation and dependencies.")


def display_sidebar_controls():
    """Display sidebar controls for simulation parameters"""
    with st.sidebar:
        st.header("⚙️ Simulation Settings")

        # File uploader
        uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx", "xls"])

        file_path = ""
        if uploaded_file:
            # Save the uploaded file to a temporary location and use that path
            import tempfile

            # Create a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                file_path = tmp_file.name

            st.success(f"File uploaded successfully: {uploaded_file.name}")

        # Simulation parameters
        st.subheader("Parameters")

        # Start date picker
        start_date = st.date_input(
            "Start Date",
            value=datetime.now().date(),
            min_value=datetime.now().date() - timedelta(days=365),
            max_value=datetime.now().date() + timedelta(days=365),
        )

        # Capacity per quarter slider
        capacity_per_quarter = st.slider(
            "Capacity per Quarter (hours)",
            min_value=500,
            max_value=5000,
            value=2000,
            step=100,
        )

        # Number of simulations slider
        num_simulations = st.slider(
            "Number of Simulations",
            min_value=100,
            max_value=10000,
            value=1000,
            step=100,
        )

        # Run simulation button
        run_simulation = st.button("🚀 Run Simulation", type="primary")

        return file_path, start_date, capacity_per_quarter, num_simulations, run_simulation
