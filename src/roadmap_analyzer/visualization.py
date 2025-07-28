"""
Visualization module for roadmap analyzer.
Contains all visualization components and charts.
"""

import plotly.graph_objects as go


def create_gantt_chart(stats, project_start_date, work_items):
    """
    Create Gantt chart visualization with confidence intervals.

    Args:
        stats: Dictionary of project statistics
        project_start_date: Start date of the project
        work_items: List of work items

    Returns:
        Plotly figure object
    """
    # Create figure
    fig = go.Figure()

    # Sort projects by position
    project_order = {item.item: item.position for item in work_items}
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
        title="Project timeline with confidence intervals",
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


def create_probability_chart(stats):
    """
    Create probability chart for on-time completion.

    Args:
        stats: Dictionary of project statistics

    Returns:
        Plotly figure object
    """
    # Extract project names and on-time probabilities
    projects = list(stats.keys())
    probabilities = [stats[p].on_time_probability * 100 for p in projects]

    # Create horizontal bar chart
    fig = go.Figure()

    # Add bars
    fig.add_trace(
        go.Bar(
            y=projects,
            x=probabilities,
            orientation="h",
            marker=dict(
                color=["#4CAF50" if p >= 80 else "#FFA500" if p >= 50 else "#FF7F7F" for p in probabilities],
                line=dict(color="rgb(8,48,107)", width=1.5),
            ),
            text=[f"{p:.1f}%" for p in probabilities],
            textposition="auto",
        )
    )

    # Update layout
    fig.update_layout(
        title="On-Time Completion Probability",
        xaxis=dict(
            title="Probability (%)",
            range=[0, 100],
        ),
        yaxis=dict(
            title="Project",
        ),
        height=100 + len(projects) * 40,
    )

    return fig
