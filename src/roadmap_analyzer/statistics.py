"""
Statistics module for roadmap analyzer.
Contains functions for processing and displaying statistics.
"""

from datetime import datetime

import pandas as pd
import streamlit as st


def format_date(date):
    """Format date for display"""
    if date is None:
        return "N/A"
    return date.strftime("%b %d, %Y")


def format_percentage(value):
    """Format percentage for display"""
    if value is None:
        return "N/A"
    return f"{value * 100:.1f}%"


def create_statistics_dataframe(stats):
    """
    Create a pandas DataFrame from project statistics.

    Args:
        stats: Dictionary of project statistics

    Returns:
        Pandas DataFrame with formatted statistics
    """
    data = []

    for project_name, project_stats in stats.items():
        data.append(
            {
                "Project": project_name,
                "Due Date": format_date(project_stats.due_date),
                "P10 (Best Case)": format_date(project_stats.p10),
                "P50 (Most Likely)": format_date(project_stats.p50),
                "P90 (Worst Case)": format_date(project_stats.p90),
                "On-Time Probability": format_percentage(project_stats.on_time_probability),
            }
        )

    return pd.DataFrame(data)


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
        due_date = stats[project].due_date

        if col == "P10 (Best Case)":
            date_val = stats[project].p10
            on_time = date_val <= due_date
        elif col == "P50 (Most Likely)":
            date_val = stats[project].p50
            on_time = date_val <= due_date
        elif col == "P90 (Worst Case)":
            date_val = stats[project].p90
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

    # Add download button for CSV
    csv = stats_df.to_csv(index=False)
    st.download_button(
        label="Download Statistics as CSV",
        data=csv,
        file_name=f"project_statistics_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )
