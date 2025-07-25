"""Configuration settings for the roadmap analyzer using Pydantic models."""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SimulationConfig(BaseModel):
    """Configuration for Monte Carlo simulation with validation."""

    default_capacity_per_quarter: int = Field(default=1300, ge=1, description="Default quarterly capacity in person-days")
    default_num_simulations: int = Field(default=20000, ge=100, le=100000, description="Default number of simulation runs")
    simulation_options: List[int] = Field(default=[5000, 10000, 20000], description="Available simulation count options")
    working_days_per_quarter: int = Field(default=65, ge=50, le=80, description="Approximate working days per quarter")
    progress_update_interval: int = Field(default=100, ge=1, description="How often to update progress (every N simulations)")

    @field_validator("simulation_options")
    @classmethod
    def validate_simulation_options(cls, v):
        if not v or len(v) == 0:
            raise ValueError("Must have at least one simulation option")
        if any(x < 100 for x in v):
            raise ValueError("All simulation options must be >= 100")
        return sorted(v)


class ColorScheme(BaseModel):
    """Color scheme configuration with validation."""

    high: str = Field(default="green", description="Color for high probability (>= 80%)")
    medium: str = Field(default="orange", description="Color for medium probability (>= 30%)")
    low: str = Field(default="red", description="Color for low probability (< 30%)")


class GanttColors(BaseModel):
    """Gantt chart color configuration."""

    p90: str = Field(default="lightcoral", description="Color for P90 (worst case) range")
    p50: str = Field(default="lightsalmon", description="Color for P50 (most likely) range")
    p10: str = Field(default="lightgreen", description="Color for P10 (best case) range")
    due_date: str = Field(default="blue", description="Color for due date markers")


class UIConfig(BaseModel):
    """Configuration for the user interface."""

    page_title: str = Field(default="Project Roadmap Monte Carlo Analysis", description="Application page title")
    page_icon: str = Field(default="📊", description="Page icon for browser tab")
    layout: str = Field(default="wide", description="Streamlit layout mode")
    probability_colors: ColorScheme = Field(default_factory=ColorScheme, description="Color scheme for probability visualization")
    gantt_colors: GanttColors = Field(default_factory=GanttColors, description="Color scheme for Gantt charts")

    @field_validator("layout")
    @classmethod
    def validate_layout(cls, v):
        if v not in ["wide", "centered"]:
            raise ValueError("Layout must be 'wide' or 'centered'")
        return v


class DataConfig(BaseModel):
    """Configuration for data processing."""

    required_columns: List[str] = Field(
        default=["Position", "Item", "Due date", "Dependency", "Best", "Likely", "Worst"], description="Required columns in Excel input"
    )
    date_format: Optional[str] = Field(default=None, description="Expected date format in Excel")
    max_work_items: int = Field(default=100, ge=1, le=1000, description="Maximum number of work items allowed")

    @field_validator("required_columns")
    @classmethod
    def validate_required_columns(cls, v):
        if len(v) < 3:
            raise ValueError("Must have at least 3 required columns")
        return v


class AppConfig(BaseModel):
    """Main application configuration combining all sub-configurations."""

    simulation: SimulationConfig = Field(default_factory=SimulationConfig, description="Simulation settings")
    ui: UIConfig = Field(default_factory=UIConfig, description="UI settings")
    data: DataConfig = Field(default_factory=DataConfig, description="Data processing settings")

    # Pydantic configuration
    model_config = ConfigDict(validate_assignment=True, extra="forbid")


# Global configuration instance
APP_CONFIG = AppConfig()
