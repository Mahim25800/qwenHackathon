"""
ModelBlueprint schema — output of the Model Architect Agent.
Contains the PyTorch code and a structured summary of the architecture.
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class LayerInfo(BaseModel):
    """Details about a single layer in the model."""

    name: str = Field(description="Layer identifier, e.g. 'conv1', 'bn2', 'fc_out'")
    type: str = Field(description="Layer type, e.g. 'Conv2d', 'BatchNorm2d', 'Linear'")
    params: int = Field(description="Number of trainable parameters in this layer")
    output_shape: Optional[str] = Field(
        default=None,
        description="Output tensor shape as string, e.g. '[B, 64, 16, 16]'"
    )
    config: Optional[str] = Field(
        default=None,
        description="Layer configuration summary, e.g. 'in=3, out=64, kernel=3x3, stride=1'"
    )


class ModelBlueprint(BaseModel):
    """
    Complete blueprint of a neural network designed by the Architect agent.
    Includes both the executable PyTorch code and a structured layer summary.
    """

    architecture_name: str = Field(
        description="Human-readable architecture name, e.g. 'Compact-ResNet-18'"
    )
    architecture_family: str = Field(
        description="Architecture family, e.g. 'ResNet', 'MobileNet', 'EfficientNet', 'Custom CNN'"
    )
    total_params: int = Field(
        description="Total number of trainable parameters"
    )
    total_macs: Optional[int] = Field(
        default=None,
        description="Total Multiply-Accumulate operations (MACs) for one forward pass"
    )
    pytorch_code: str = Field(
        description="Complete PyTorch nn.Module code with shape comments"
    )
    layers: List[LayerInfo] = Field(
        description="Ordered list of layer details"
    )
    design_rationale: str = Field(
        description="Brief explanation of why this architecture was chosen"
    )
    estimated_accuracy: Optional[float] = Field(
        default=None,
        description="Estimated accuracy on the target dataset (0.0-1.0)"
    )
    iteration: int = Field(
        default=1,
        description="Which iteration of the debate this design came from"
    )
