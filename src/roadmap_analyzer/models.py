"""Data models for the roadmap analyzer."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class WorkItem(BaseModel):
    """Represents a work item loaded from Excel data.

    This model defines the structure of work items that are read from Excel files,
    including effort estimates, dependencies, and due dates for Monte Carlo analysis.
    """

    position: int = Field(..., description="Position/order of the work item in the roadmap", ge=1)

    initiative: str = Field(..., description="Name or title of the work item/initiative", min_length=1)

    due_date: datetime = Field(..., description="Target due date for the work item")

    dependency: Optional[int] = Field(None, description="Position number of the work item this depends on", ge=1)

    best_estimate: float = Field(..., alias="Best", description="Best case effort estimate in person days", gt=0)

    most_likely_estimate: float = Field(..., alias="Most likely", description="Most likely effort estimate in person days", gt=0)

    worst_estimate: float = Field(..., alias="Worst", description="Worst case effort estimate in person days", gt=0)

    @field_validator("most_likely_estimate")
    @classmethod
    def validate_most_likely(cls, v, info):
        """Ensure most likely estimate is >= best estimate."""
        if "best_estimate" in info.data and v < info.data["best_estimate"]:
            raise ValueError("Most likely estimate must be >= best estimate")
        return v

    @field_validator("worst_estimate")
    @classmethod
    def validate_worst(cls, v, info):
        """Ensure worst estimate is >= most likely estimate."""
        if "most_likely_estimate" in info.data and v < info.data["most_likely_estimate"]:
            raise ValueError("Worst estimate must be >= most likely estimate")
        if "best_estimate" in info.data and v < info.data["best_estimate"]:
            raise ValueError("Worst estimate must be >= best estimate")
        return v

    @field_validator("dependency")
    @classmethod
    def validate_dependency(cls, v, info):
        """Ensure dependency doesn't reference itself."""
        if v is not None and "position" in info.data and v == info.data["position"]:
            raise ValueError("Work item cannot depend on itself")
        return v

    class Config:
        """Pydantic configuration."""

        # Allow field aliases for Excel column names
        populate_by_name = True
        # Use enum values for serialization
        use_enum_values = True
        # Validate assignments
        validate_assignment = True

    def __str__(self) -> str:
        """String representation of the work item."""
        return f"WorkItem({self.position}: {self.initiative})"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return (
            f"WorkItem(position={self.position}, initiative='{self.initiative}', "
            f"estimates=({self.best_estimate}, {self.most_likely_estimate}, {self.worst_estimate}), "
            f"due_date={self.due_date.date()}, dependency={self.dependency})"
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
