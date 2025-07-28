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
                "Start P10": format_date(project_stats.start_p10),
                "P10 (Best Case)": format_date(project_stats.p10),
                "Start P50": format_date(project_stats.start_p50),
                "P50 (Most Likely)": format_date(project_stats.p50),
                "Start P90": format_date(project_stats.start_p90),
                "P90 (Worst Case)": format_date(project_stats.p90),
                "On-Time Probability": format_percentage(project_stats.on_time_probability),
            }
        )

    return pd.DataFrame(data)


def _create_stats_dataframe(stats):
    """Create a DataFrame from project statistics."""
    return pd.DataFrame(
        [
            {
                "Project": project,
                "Due Date": stats[project].due_date.strftime("%b %d, %Y"),
                "Start P10": stats[project].start_p10.strftime("%b %d, %Y") if stats[project].start_p10 else "N/A",
                "P10 (Best Case)": stats[project].p10.strftime("%b %d, %Y"),
                "Start P50": stats[project].start_p50.strftime("%b %d, %Y") if stats[project].start_p50 else "N/A",
                "P50 (Most Likely)": stats[project].p50.strftime("%b %d, %Y"),
                "Start P90": stats[project].start_p90.strftime("%b %d, %Y") if stats[project].start_p90 else "N/A",
                "P90 (Worst Case)": stats[project].p90.strftime("%b %d, %Y"),
                "On-Time Probability": f"{stats[project].on_time_probability:.1f}%",
            }
            for project in stats
        ]
    )


def _style_completion_date(val, date_val, due_date):
    """Style completion date based on whether it's on time."""
    on_time = date_val <= due_date
    color = "#4CAF50" if on_time else "#FF7F7F"  # Green if on time, red if late
    return f'<span style="color: {color}; font-weight: bold;">{val}</span>'


def _style_start_date(val, on_time):
    """Style start date based on whether the completion is on time."""
    if val == "N/A":
        return val
    color = "#4CAF50" if on_time else "#FF7F7F"  # Green if on time, red if late
    return f'<span style="color: {color}; font-style: italic;">{val}</span>'


def _style_probability(val):
    """Style probability based on value."""
    prob_value = float(val.strip("%"))
    if prob_value >= 90:
        return f'<span style="color: #4CAF50; font-weight: bold;">{val}</span>'  # Green and bold
    elif prob_value >= 40:
        return f'<span style="color: #FFA500; font-weight: bold;">{val}</span>'  # Orange and bold
    else:
        return f'<span style="color: #FF7F7F; font-weight: bold;">{val}</span>'  # Red and bold


def _apply_styling(stats_df, stats):
    """Apply styling to the statistics DataFrame."""
    styled_df = stats_df.copy()

    for idx, row in styled_df.iterrows():
        project = row["Project"]
        due_date = stats[project].due_date

        # Check if completion dates are on time
        p10_on_time = stats[project].p10 <= due_date
        p50_on_time = stats[project].p50 <= due_date
        p90_on_time = stats[project].p90 <= due_date

        # Style completion dates
        styled_df.at[idx, "P10 (Best Case)"] = _style_completion_date(row["P10 (Best Case)"], stats[project].p10, due_date)
        styled_df.at[idx, "P50 (Most Likely)"] = _style_completion_date(row["P50 (Most Likely)"], stats[project].p50, due_date)
        styled_df.at[idx, "P90 (Worst Case)"] = _style_completion_date(row["P90 (Worst Case)"], stats[project].p90, due_date)

        # Style start dates
        styled_df.at[idx, "Start P10"] = _style_start_date(row["Start P10"], p10_on_time)
        styled_df.at[idx, "Start P50"] = _style_start_date(row["Start P50"], p50_on_time)
        styled_df.at[idx, "Start P90"] = _style_start_date(row["Start P90"], p90_on_time)

        # Style probability
        styled_df.at[idx, "On-Time Probability"] = _style_probability(row["On-Time Probability"])

    return styled_df


def _add_table_css():
    """Add CSS styling for the statistics table."""
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


def display_detailed_statistics(stats):
    """Display detailed statistics table with styling."""
    st.subheader("📈 Detailed Statistics")

    # Create and style the dataframe
    stats_df = _create_stats_dataframe(stats)
    styled_df = _apply_styling(stats_df, stats)

    # Display the styled dataframe
    st.markdown(styled_df.to_html(escape=False, index=False), unsafe_allow_html=True)

    # Add CSS styling
    _add_table_css()

    # Add download button for CSV
    csv = stats_df.to_csv(index=False)
    st.download_button(
        label="Download Statistics as CSV",
        data=csv,
        file_name=f"project_statistics_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )
