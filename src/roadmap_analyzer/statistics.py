"""
Statistics module for roadmap analyzer.
Contains functions for processing and displaying statistics.
"""

from datetime import datetime
from typing import Dict

import pandas as pd
import streamlit as st

from .models import SimulationStats


def _create_stats_dataframe(stats: Dict[str, SimulationStats]) -> pd.DataFrame:
    """Create a DataFrame from roadmap statistics."""
    return pd.DataFrame(
        [
            {
                "Work Item": work_item,
                "Start Date": stats[work_item].start_date.strftime("%b %d, %Y") if stats[work_item].start_date else "N/A",
                "Due Date": stats[work_item].due_date.strftime("%b %d, %Y"),
                "Start P10": stats[work_item].start_p10.strftime("%b %d, %Y") if stats[work_item].start_p10 else "N/A",
                "P10 (Best Case)": stats[work_item].p10.strftime("%b %d, %Y"),
                "Start P50": stats[work_item].start_p50.strftime("%b %d, %Y") if stats[work_item].start_p50 else "N/A",
                "P50 (Most Likely)": stats[work_item].p50.strftime("%b %d, %Y"),
                "Start P90": stats[work_item].start_p90.strftime("%b %d, %Y") if stats[work_item].start_p90 else "N/A",
                "P90 (Worst Case)": stats[work_item].p90.strftime("%b %d, %Y"),
                "On-Time Probability": f"{stats[work_item].on_time_probability:.1f}%",
            }
            for work_item in stats
        ]
    )


def _style_completion_date(val: str, date_val: datetime, due_date: datetime) -> str:
    """Style completion date based on whether it's on time."""
    on_time = date_val <= due_date
    color = "#4CAF50" if on_time else "#FF7F7F"  # Green if on time, red if late
    return f'<span style="color: {color}; font-weight: bold;">{val}</span>'


def _style_start_date(val: str, on_time: bool) -> str:
    """Style start date based on whether the completion is on time."""
    if val == "N/A":
        return val
    color = "#4CAF50" if on_time else "#FF7F7F"  # Green if on time, red if late
    return f'<span style="color: {color}; font-style: italic;">{val}</span>'


def _style_probability(val: str) -> str:
    """Style probability based on value."""
    prob_value = float(val.strip("%"))
    if prob_value >= 90:
        return f'<span style="color: #4CAF50; font-weight: bold;">{val}</span>'  # Green and bold
    elif prob_value >= 40:
        return f'<span style="color: #FFA500; font-weight: bold;">{val}</span>'  # Orange and bold
    else:
        return f'<span style="color: #FF7F7F; font-weight: bold;">{val}</span>'  # Red and bold


def _apply_styling(stats_df: pd.DataFrame, stats: Dict[str, SimulationStats]) -> pd.DataFrame:
    """Apply styling to the statistics DataFrame."""
    styled_df = stats_df.copy()

    for idx, row in styled_df.iterrows():
        work_item = row["Work Item"]
        due_date = stats[work_item].due_date

        # Check if completion dates are on time
        p10_on_time = stats[work_item].p10 <= due_date
        p50_on_time = stats[work_item].p50 <= due_date
        p90_on_time = stats[work_item].p90 <= due_date

        # Style completion dates
        styled_df.at[idx, "P10 (Best Case)"] = _style_completion_date(row["P10 (Best Case)"], stats[work_item].p10, due_date)
        styled_df.at[idx, "P50 (Most Likely)"] = _style_completion_date(row["P50 (Most Likely)"], stats[work_item].p50, due_date)
        styled_df.at[idx, "P90 (Worst Case)"] = _style_completion_date(row["P90 (Worst Case)"], stats[work_item].p90, due_date)

        # Style start date
        start_date_val = row["Start Date"]
        if start_date_val == "N/A":
            styled_df.at[idx, "Start Date"] = f'<span style="color: #888888; font-style: italic;">{start_date_val}</span>'
        else:
            styled_df.at[idx, "Start Date"] = f'<span style="color: #4CAF50; font-weight: bold;">{start_date_val}</span>'

        # Style start dates
        styled_df.at[idx, "Start P10"] = _style_start_date(row["Start P10"], p10_on_time)
        styled_df.at[idx, "Start P50"] = _style_start_date(row["Start P50"], p50_on_time)
        styled_df.at[idx, "Start P90"] = _style_start_date(row["Start P90"], p90_on_time)

        # Style probability
        styled_df.at[idx, "On-Time Probability"] = _style_probability(row["On-Time Probability"])

    return styled_df


def _add_table_css() -> None:
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


def display_detailed_statistics(stats: Dict[str, SimulationStats]) -> None:
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
        file_name=f"roadmap_statistics_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )
