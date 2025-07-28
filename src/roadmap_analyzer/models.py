"""Data models for the roadmap analyzer."""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class WorkItem(BaseModel):
    """Represents a work item loaded from Excel data.

    This model defines the structure of work items that are read from Excel files,
    including effort estimates, dependencies, and due dates for Monte Carlo analysis.
    """

    position: int = Field(..., description="Position/order of the work item in the roadmap", ge=1)

    item: str = Field(..., alias="Item", description="Name or title of the work item", min_length=1)

    due_date: datetime = Field(..., description="Target due date for the work item")

    start_date: Optional[datetime] = Field(None, alias="Start date", description="Planned start date for the work item")

    priority: Optional[str] = Field(None, alias="Priority", description="Priority level of the work item")

    dependency: Optional[int] = Field(None, description="Position number of the work item this depends on", ge=1)

    best_estimate: float = Field(..., alias="Best", description="Best case effort estimate in person days", gt=0)

    most_likely_estimate: float = Field(..., alias="Likely", description="Most likely effort estimate in person days", gt=0)

    worst_estimate: float = Field(..., alias="Worst", description="Worst case effort estimate in person days", gt=0)

    @field_validator("most_likely_estimate")
    @classmethod
    def validate_most_likely(cls, v, info):
        """Ensure likely estimate is >= best estimate."""
        if "best_estimate" in info.data and v < info.data["best_estimate"]:
            raise ValueError("Likely estimate must be >= best estimate")
        return v

    @field_validator("worst_estimate")
    @classmethod
    def validate_worst(cls, v, info):
        """Ensure worst estimate is >= likely estimate."""
        if "most_likely_estimate" in info.data and v < info.data["most_likely_estimate"]:
            raise ValueError("Worst estimate must be >= likely estimate")
        if "best_estimate" in info.data and v < info.data["best_estimate"]:
            raise ValueError("Worst estimate must be >= best estimate")
        return v

    @field_validator("dependency")
    def validate_dependency(cls, v, info):
        """Ensure dependency doesn't reference itself."""
        if v is not None and "position" in info.data and v == info.data["position"]:
            raise ValueError("Work item cannot depend on itself")
        return v

    # Pydantic configuration
    model_config = ConfigDict(
        populate_by_name=True,  # Allow field aliases for Excel column names
        use_enum_values=True,  # Use enum values for serialization
        validate_assignment=True,  # Validate assignments
    )

    def __str__(self) -> str:
        """String representation of the work item."""
        return f"WorkItem({self.position}: {self.item})"

    def __repr__(self) -> str:
        """Detailed string representation."""
        # Format dates safely with proper null checking
        due_date_str = self.due_date.strftime("%Y-%m-%d") if hasattr(self.due_date, "strftime") else str(self.due_date)
        start_date_str = self.start_date.strftime("%Y-%m-%d") if self.start_date and hasattr(self.start_date, "strftime") else None

        return (
            f"WorkItem(position={self.position}, item='{self.item}', "
            f"estimates=({self.best_estimate}, {self.most_likely_estimate}, {self.worst_estimate}), "
            f"due_date={due_date_str}, start_date={start_date_str}, "
            f"priority={self.priority}, dependency={self.dependency})"
        )

    @property
    def has_dependency(self) -> bool:
        """Check if this work item has a dependency."""
        return self.dependency is not None

    @property
    def estimate_range(self) -> tuple[float, float, float]:
        """Get the effort estimates as a tuple (best, most_likely, worst)."""
        return (self.best_estimate, self.most_likely_estimate, self.worst_estimate)

    @property
    def expected_effort(self) -> float:
        """Calculate expected effort using triangular distribution formula."""
        # Expected value of triangular distribution: (a + b + c) / 3
        return (self.best_estimate + self.most_likely_estimate + self.worst_estimate) / 3


# Simulation Result Models
class SimulationResult(BaseModel):
    """Represents a single project result from a simulation run."""

    name: str = Field(..., description="Name of the work item")
    position: int = Field(..., description="Position/ID of the work item")
    effort: float = Field(..., description="Sampled effort for this simulation run")
    start_date: datetime = Field(..., description="Start date for the work item")
    completion_date: datetime = Field(..., description="Calculated completion date")
    due_date: datetime = Field(..., description="Target due date")
    on_time: bool = Field(..., description="Whether the work item completes on time")


class SimulationRun(BaseModel):
    """Represents a complete simulation run with results for all work items."""

    results: List[SimulationResult] = Field(..., description="Results for all work items in this simulation run")


class SimulationStats(BaseModel):
    """Statistics for a single work item across all simulation runs."""

    position: int = Field(..., description="Position/ID of the work item")
    due_date: datetime = Field(..., description="Target due date")
    on_time_probability: float = Field(..., description="Probability of on-time completion (percentage)")
    p10: datetime = Field(..., description="P10 (optimistic) completion date")
    p50: datetime = Field(..., description="P50 (median) completion date")
    p90: datetime = Field(..., description="P90 (pessimistic) completion date")
    best_effort: float = Field(..., description="Best case effort estimate")
    likely_effort: float = Field(..., description="Most likely effort estimate")
    worst_effort: float = Field(..., description="Worst case effort estimate")
    start_p10: Optional[datetime] = Field(None, description="P10 start date (considering dependencies)")
    start_p50: Optional[datetime] = Field(None, description="P50 start date (considering dependencies)")
    start_p90: Optional[datetime] = Field(None, description="P90 start date (considering dependencies)")


class SimulationResults(BaseModel):
    """Complete simulation results for all work items."""

    runs: List[SimulationRun] = Field(..., description="All simulation runs")
    stats: Dict[str, SimulationStats] = Field(..., description="Statistics by work item name")
