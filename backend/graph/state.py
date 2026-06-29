"""
LangGraph State Definition for NeuralSwarm.
Defines the TypedDict state that flows through the debate graph.
"""

from typing import TypedDict, Optional, Literal, Any


class GraphState(TypedDict):
    """
    The state object that flows through the LangGraph debate loop.
    Each node reads from and writes to specific fields.
    """

    # Configuration (set once at entry)
    session_id: str
    dataset_name: str
    input_shape: list[int]
    num_classes: int
    num_samples: int
    max_params: int
    target_latency_ms: float
    max_iterations: int
    user_constraints: str

    # Agent outputs (updated at each step)
    dataset_profile: Optional[dict]       # DatasetProfile.model_dump()
    model_blueprint: Optional[dict]       # ModelBlueprint.model_dump()
    critique: Optional[dict]              # CritiqueMatrix.model_dump()

    # Iteration tracking
    iteration: int
    status: str   # "running", "approved", "max_iterations", "error"

    # History
    debate_log: list[dict]
    all_blueprints: list[dict]
    all_critiques: list[dict]

    # Error
    error_message: Optional[str]
