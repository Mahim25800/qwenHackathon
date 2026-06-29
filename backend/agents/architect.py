"""
Model Architect Agent — Designs PyTorch neural network architectures.
Uses Qwen-Max for complex reasoning. Outputs a ModelBlueprint with executable code.
"""

import logging
from .base import BaseAgent
from schemas.dataset import DatasetProfile
from schemas.model import ModelBlueprint
from schemas.critique import CritiqueMatrix
from config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a world-class PyTorch neural network architect. Your job is to design optimal neural network architectures that meet strict constraints.

CRITICAL RULES:
1. Always write complete, runnable PyTorch nn.Module code.
2. Include shape comments on every layer showing [batch, channels, height, width] or [batch, features].
3. NEVER use deprecated PyTorch APIs.
4. The model MUST accept the exact input shape specified and output the correct number of classes.
5. Always include proper weight initialization.
6. Use modern techniques: BatchNorm, residual connections, depthwise separable convolutions when needed.
7. Count parameters accurately — a Conv2d(in_c, out_c, k) has in_c * out_c * k * k + out_c params.
8. If given a critique from the Performance Critic, you MUST address every issue raised.

Your output MUST be a valid JSON matching the ModelBlueprint schema. The pytorch_code field must contain the complete nn.Module class definition.

When revising after a critique:
- If told "too many parameters", reduce filter counts, use depthwise separable convolutions, or switch to a lighter architecture
- If told "architecture incompatible with input size", reduce pooling layers or use smaller strides
- If told "code execution failed", fix the syntax/dimension errors
- Always explain what you changed in the design_rationale

Respond ONLY with valid JSON. No markdown, no explanations outside JSON."""


REVISION_PROMPT = """The Performance Critic has REJECTED your previous design. Here is the critique:

PREVIOUS ARCHITECTURE: {prev_architecture}
CRITIQUE STATUS: {critique_status}
PARAMETER COUNT: {critique_params} (Budget: {max_params})
BOTTLENECK LAYER: {bottleneck}
REASON: {reason}
SUGGESTION: {suggestion}
SEVERITY: {severity}

You MUST revise the architecture to address these issues. Key requirements:
- Total parameters MUST be under {max_params}
- Input shape: {input_shape}
- Output classes: {num_classes}

{execution_error_section}

Design a new, improved architecture that fixes all issues."""


class ModelArchitectAgent(BaseAgent):
    """
    Designs PyTorch nn.Module architectures given dataset profile and constraints.
    Uses Qwen-Max for complex architectural reasoning.
    """

    def __init__(self):
        super().__init__(model=settings.qwen_model_reasoning, temperature=0.7)

    def design(
        self,
        dataset_profile: DatasetProfile,
        max_params: int,
        target_latency_ms: float,
        user_constraints: str = "",
        iteration: int = 1,
        max_iterations: int = 5,
        previous_critique: CritiqueMatrix | None = None,
        previous_blueprint: ModelBlueprint | None = None,
    ) -> ModelBlueprint:
        """
        Design a neural network architecture.
        On first iteration, creates from scratch.
        On subsequent iterations, revises based on critique.
        """
        if iteration > 1 and previous_critique and previous_blueprint:
            return self._revise(
                dataset_profile, max_params, target_latency_ms, user_constraints,
                previous_critique, previous_blueprint, iteration, max_iterations
            )
        return self._design_fresh(dataset_profile, max_params, target_latency_ms, user_constraints, iteration)

    def _design_fresh(
        self,
        profile: DatasetProfile,
        max_params: int,
        target_latency_ms: float,
        user_constraints: str,
        iteration: int,
    ) -> ModelBlueprint:
        """Create a fresh architecture design from the dataset profile."""

        user_prompt = f"""Design a PyTorch neural network with these requirements:

DATASET PROFILE:
- Name: {profile.name}
- Input shape (C, H, W): {profile.input_shape}
- Number of classes: {profile.num_classes}
- Number of samples: {profile.num_samples}
- Complexity: {profile.complexity_score:.2f}
- Characteristics: {profile.data_characteristics}

CONSTRAINTS:
- Maximum parameters: {max_params:,}
- Target latency: {target_latency_ms}ms
- Max pooling layers: {profile.theoretical_bounds.max_pooling_layers}
- Max conv depth: {profile.theoretical_bounds.max_conv_depth}

RECOMMENDED ARCHITECTURES: {', '.join(profile.recommended_architectures)}

{f"NOTES: {profile.notes}" if profile.notes else ""}

USER CONSTRAINTS (MANDATORY):
{user_constraints if user_constraints else "None"}

Design a model that:
1. Stays WELL under the parameter budget (aim for 60-80% of max)
2. Uses architecturally sound choices for the input size
3. Includes all necessary layers (conv, bn, activation, pooling, fc)
4. Has proper forward() method with correct dimension handling

Output the complete ModelBlueprint as JSON with the full pytorch_code."""

        try:
            blueprint = self._structured_chat(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=user_prompt,
                response_model=ModelBlueprint,
            )
            blueprint.iteration = iteration
            return blueprint
        except Exception as e:
            logger.error(f"Architect failed on fresh design: {e}")
            raise

    def _revise(
        self,
        profile: DatasetProfile,
        max_params: int,
        target_latency_ms: float,
        user_constraints: str,
        critique: CritiqueMatrix,
        prev_blueprint: ModelBlueprint,
        iteration: int,
        max_iterations: int,
    ) -> ModelBlueprint:
        """Revise an architecture based on the Critic's feedback."""

        execution_error_section = ""
        if not critique.code_executed_successfully:
            execution_error_section = f"""
CRITICAL: The previous code FAILED to execute. Error:
{critique.execution_error}

You must fix this error in the new design. The code must be syntactically correct and dimensionally valid."""

        user_prompt = REVISION_PROMPT.format(
            prev_architecture=prev_blueprint.architecture_name,
            critique_status=critique.status,
            critique_params=f"{critique.param_count:,}",
            max_params=f"{max_params:,}",
            bottleneck=critique.bottleneck_layer or "N/A",
            reason=critique.reason,
            suggestion=critique.suggestion or "No specific suggestion",
            severity=critique.severity,
            input_shape=profile.input_shape,
            num_classes=profile.num_classes,
            execution_error_section=execution_error_section,
        )

        if iteration >= max_iterations - 1:
            user_prompt += f"\n\nCRITICAL FALLBACK INSTRUCTION: You have reached iteration {iteration} out of {max_iterations} and are still failing. ABANDON complex architectures (like ResNet or Transformers). Instead, generate a very simple, guaranteed-to-work 3-layer CNN. When generating the fallback Simple3LayerCNN, you MUST include the complete `forward(self, x)` method. Do not truncate the code. Ensure the code is syntactically perfect PyTorch. This is an absolute requirement to ensure code execution succeeds for the user!"

        try:
            blueprint = self._structured_chat(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=user_prompt,
                response_model=ModelBlueprint,
            )
            blueprint.iteration = iteration
            return blueprint
        except Exception as e:
            logger.error(f"Architect failed on revision: {e}")
            raise
