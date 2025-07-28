"""
Capacity chart visualization module for roadmap analyzer.
Handles the creation and formatting of bar chart visualization for capacity data.
"""

import plotly.express as px
import plotly.graph_objects as go


def create_capacity_chart(capacity_df):
    """
    Create a bar chart visualization for capacity data.

    Args:
        capacity_df: DataFrame with capacity data

    Returns:
        Plotly figure object
    """
    if capacity_df.empty:
        # Create an empty figure with a message if no data
        fig = go.Figure()
        fig.update_layout(
            title="No capacity data available",
            xaxis_title="Period",
            yaxis_title="Capacity (PD)",
            height=400,
            width=800,
        )
        fig.add_annotation(
            text="No capacity data available. Upload a file with a 'Capacity' sheet to view capacity planning.",
            showarrow=False,
            font=dict(size=14),
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
        )
        return fig

    # Create bar chart
    fig = px.bar(
        capacity_df,
        x="DisplayPeriod",
        y="Capacity",
        color="Capacity",
        labels={"DisplayPeriod": "Period", "Capacity": "Capacity (PD)"},
        color_continuous_scale=["#FF7F7F", "#FFA500", "#4CAF50"],  # Red to orange to green
        title="Capacity Planning",
    )

    # Format the figure
    fig.update_layout(
        xaxis_title="Period",
        yaxis_title="Capacity (Person Days)",
        height=400,
        width=800,
        coloraxis_showscale=False,  # Hide the color scale
    )

    # Add average line
    avg_capacity = capacity_df["Capacity"].mean()
    fig.add_shape(
        type="line",
        x0=-0.5,
        x1=len(capacity_df) - 0.5,
        y0=avg_capacity,
        y1=avg_capacity,
        line=dict(color="black", width=1, dash="dash"),
    )

    # Add annotation for average
    fig.add_annotation(
        x=len(capacity_df) - 1,
        y=avg_capacity,
        text=f"Avg: {avg_capacity:.1f} PD",
        showarrow=False,
        yshift=10,
        font=dict(size=10),
    )

    return fig
