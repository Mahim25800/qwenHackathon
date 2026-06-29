"""
SwarmState, SwarmConfig, and SwarmEvent schemas.
These define the orchestration state, user configuration, and real-time events.
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal, Any, List
from datetime import datetime

from .dataset import DatasetProfile
from .model import ModelBlueprint
from .critique import CritiqueMatrix


class SwarmConfig(BaseModel):
    """User-provided configuration for a swarm run."""

    dataset_name: str = Field(
        default="CIFAR-10",
        description="Name of the target dataset"
    )
    input_shape: List[int] = Field(
        default=[3, 32, 32],
        description="Input tensor shape [channels, height, width]"
    )
    num_classes: int = Field(
        default=10,
        description="Number of output classes"
    )
    max_params: int = Field(
        default=10_000_000,
        description="Maximum allowed trainable parameters"
    )
    target_latency_ms: float = Field(
        default=20.0,
        description="Target inference latency in milliseconds"
    )
    max_iterations: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Maximum debate iterations before forcing consensus"
    )
    user_constraints: Optional[str] = Field(
        default="",
        description="Optional additional architectural constraints from the user"
    )


class SwarmEvent(BaseModel):
    """Real-time event emitted during swarm execution, sent via SSE."""

    type: Literal[
        "swarm_started",
        "agent_thinking",
        "agent_result",
        "iteration_complete",
        "swarm_complete",
        "error",
    ] = Field(description="Event type for frontend routing")

    agent: Optional[str] = Field(
        default=None,
        description="Agent name: 'explorer', 'architect', 'critic'"
    )
    data: Any = Field(
        default=None,
        description="Event payload — type depends on event type"
    )
    message: Optional[str] = Field(
        default=None,
        description="Human-readable event description"
    )
    iteration: Optional[int] = Field(
        default=None,
        description="Current debate iteration number"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z"
    )


class SwarmState(BaseModel):
    """
    Complete state of a swarm session.
    This is the main state object passed through the LangGraph workflow.
    """

    session_id: str = Field(description="Unique session identifier")
    config: SwarmConfig = Field(description="User-provided configuration")

    # Agent outputs
    dataset_profile: Optional[DatasetProfile] = Field(
        default=None,
        description="Output from the Data Explorer agent"
    )
    model_blueprint: Optional[ModelBlueprint] = Field(
        default=None,
        description="Current model design from the Architect agent"
    )
    critique: Optional[CritiqueMatrix] = Field(
        default=None,
        description="Latest critique from the Critic agent"
    )

    # Iteration tracking
    iteration: int = Field(default=0, description="Current debate iteration")
    status: Literal["pending", "running", "completed", "error"] = Field(
        default="pending"
    )

    # History
    debate_log: List[dict] = Field(
        default_factory=list,
        description="Chronological log of all agent actions and outputs"
    )
    all_blueprints: List[ModelBlueprint] = Field(
        default_factory=list,
        description="All model blueprints from every iteration"
    )
    all_critiques: List[CritiqueMatrix] = Field(
        default_factory=list,
        description="All critiques from every iteration"
    )

    # Error tracking
    error_message: Optional[str] = Field(default=None)
