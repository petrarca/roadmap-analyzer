"""
Probability chart visualization module for roadmap analyzer.
Handles the creation and formatting of scatter plot visualization for project timelines.
"""

import pandas as pd
import plotly.express as px


def create_probability_chart(stats):
    """
    Create a scatter plot visualization for on-time completion probabilities.

    Args:
        stats: Dictionary of project statistics

    Returns:
        Plotly figure object
    """
    sorted_projects = sorted(stats.items(), key=lambda x: x[1].position)

    # Extract data
    project_names = [p[0] for p in sorted_projects]
    probabilities = [p[1].on_time_probability for p in sorted_projects]
    due_dates = [p[1].due_date for p in sorted_projects]
    efforts = [(p[1].best_effort + p[1].likely_effort + p[1].worst_effort) / 3 for p in sorted_projects]

    # Create a DataFrame for easier plotting
    df = pd.DataFrame(
        {
            "Project": project_names,
            "Probability": probabilities,
            "Due Date": due_dates,
            "Effort": efforts,
            "Risk Category": ["Low Risk" if p >= 80 else "Medium Risk" if p >= 50 else "High Risk" for p in probabilities],
        }
    )

    # Normalize efforts for bubble size (between 10 and 50)
    min_effort = min(efforts)
    max_effort = max(efforts) if max(efforts) > min_effort else min_effort + 1
    df["Size"] = 10 + 40 * (df["Effort"] - min_effort) / (max_effort - min_effort)

    # Create color mapping
    color_map = {"High Risk": "#FF7F7F", "Medium Risk": "#FFA500", "Low Risk": "#4CAF50"}

    # Create scatter plot
    fig = px.scatter(
        df,
        x="Due Date",
        y="Probability",
        size="Size",
        color="Risk Category",
        color_discrete_map=color_map,
        hover_name="Project",
        text="Project",
        size_max=50,
        labels={"Probability": "On-Time Probability (%)", "Due Date": "Due Date", "Size": "Relative Effort"},
    )

    # Customize the hover template
    fig.update_traces(
        hovertemplate="<b>%{hovertext}</b><br>Probability: %{y:.1f}%<br>Due Date: %{x|%Y-%m-%d}<br>Effort: %{marker.size:.1f}<extra></extra>"
    )

    # Add horizontal reference lines
    fig.add_shape(
        type="line",
        x0=df["Due Date"].min(),
        x1=df["Due Date"].max(),
        y0=50,
        y1=50,
        line=dict(color="orange", width=1, dash="dash"),
        name="Medium Risk Threshold",
    )

    fig.add_shape(
        type="line",
        x0=df["Due Date"].min(),
        x1=df["Due Date"].max(),
        y0=80,
        y1=80,
        line=dict(color="green", width=1, dash="dash"),
        name="Low Risk Threshold",
    )

    # Format the figure
    fig.update_layout(
        title="Project Completion Probability vs Due Date",
        xaxis=dict(
            title="Due Date",
            tickformat="%b %Y",  # Format as month and year (e.g., Jan 2025)
            dtick="M1",  # Display ticks every month
            ticklabelmode="period",  # Show labels at the period boundaries
        ),
        yaxis=dict(
            title="On-Time Probability (%)",
            range=[-5, 105],
            tickvals=[0, 20, 40, 50, 60, 80, 100],
            ticktext=["0%", "20%", "40%", "50%", "60%", "80%", "100%"],
        ),
        height=600,
        width=800,
        legend=dict(title="Risk Level", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    return fig
