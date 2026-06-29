"""
Performance Critic Agent — Evaluates model architectures using sandbox execution.
Uses Qwen-Max + tool calling. The "secret weapon" that makes the debate system work.
"""

import json
import logging
from .base import BaseAgent
from schemas.model import ModelBlueprint
from schemas.critique import CritiqueMatrix
from tools.sandbox import execute_model_code
from config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a ruthless but fair neural network performance critic. Your job is to evaluate proposed PyTorch model architectures against strict constraints.

You have access to ACTUAL execution metrics from a code sandbox. Do NOT guess parameter counts — use the real numbers provided.

Your evaluation criteria:
1. PARAMETER COUNT: Must be within the user's budget. If over, REJECT.
2. CODE CORRECTNESS: The code must execute without errors. If it fails, REJECT.
3. ARCHITECTURAL SOUNDNESS: Check for dimension mismatches, missing layers, bad practices.
4. EFFICIENCY: Identify bottleneck layers that contribute most to parameter count or compute.

When REJECTING, you MUST provide:
- The specific bottleneck layer causing the issue
- A concrete, hyper-specific actionable suggestion for the Architect to fix it (e.g., "Change out_channels of Conv2d from 128 to 64 to save 200k params" or "Add a 2x2 MaxPool2d after the first conv layer to fix the 32x32 to 16x16 dimension mismatch").
- The severity level (LOW, MEDIUM, HIGH, CRITICAL)

When APPROVING, still provide feedback on potential improvements.

Respond ONLY with valid JSON matching the CritiqueMatrix schema."""


class PerformanceCriticAgent(BaseAgent):
    """
    Evaluates model architectures by running them in a sandbox
    and critiquing the results against user constraints.
    """

    def __init__(self):
        super().__init__(model=settings.qwen_model_reasoning, temperature=0.3)

    def critique(
        self,
        blueprint: ModelBlueprint,
        max_params: int,
        target_latency_ms: float,
        input_shape: list[int],
    ) -> CritiqueMatrix:
        """
        Run the model code in the sandbox, get real metrics,
        then use Qwen-Max to generate a structured critique.
        """
        # Step 1: Execute in sandbox to get real metrics
        sandbox_result = execute_model_code(
            code=blueprint.pytorch_code,
            input_shape=input_shape,
        )

        # Step 2: Build the critique prompt with real data
        if sandbox_result["success"]:
            actual_params = sandbox_result["total_params"]
            params_within_budget = actual_params <= max_params

            user_prompt = f"""Evaluate this model architecture against the constraints.

ARCHITECTURE: {blueprint.architecture_name}
DESIGN RATIONALE: {blueprint.design_rationale}

SANDBOX EXECUTION RESULTS (these are REAL, not estimated):
- Code executed: SUCCESS
- Total parameters: {actual_params:,}
- Parameter budget: {max_params:,}
- Parameters within budget: {params_within_budget}
- Layer breakdown:
{sandbox_result.get("layer_summary", "Not available")}

CONSTRAINTS:
- Max parameters: {max_params:,}
- Target latency: {target_latency_ms}ms

PYTORCH CODE:
```python
{blueprint.pytorch_code}
```

Provide your verdict as a CritiqueMatrix JSON.
If parameters exceed budget, status MUST be "REJECT".
If code had issues, status MUST be "REJECT".
Identify the biggest bottleneck layer and suggest specific fixes."""

        else:
            # Code failed to execute
            user_prompt = f"""The Architect's PyTorch code FAILED to execute in the sandbox.

ARCHITECTURE: {blueprint.architecture_name}
ERROR: {sandbox_result.get("error", "Unknown error")}
STDERR: {sandbox_result.get("stderr", "")[:500]}

PYTORCH CODE:
```python
{blueprint.pytorch_code}
```

Status MUST be "REJECT" with severity "CRITICAL".
Explain EXACTLY what line/layer caused the error and write out the EXACT code correction needed.
Set code_executed_successfully to false."""

        try:
            critique = self._structured_chat(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=user_prompt,
                response_model=CritiqueMatrix,
            )

            # Override with sandbox ground truth
            if sandbox_result["success"]:
                critique.param_count = sandbox_result["total_params"]
                critique.params_within_budget = sandbox_result["total_params"] <= max_params
                critique.code_executed_successfully = True
                critique.sandbox_output = sandbox_result.get("stdout", "")
                # Force REJECT if params over budget (don't trust LLM verdict alone)
                if not critique.params_within_budget:
                    critique.status = "REJECT"
            else:
                critique.code_executed_successfully = False
                critique.execution_error = sandbox_result.get("error", "Unknown error")
                critique.status = "REJECT"
                critique.severity = "CRITICAL"
                critique.param_count = 0
                critique.params_within_budget = False

            return critique

        except Exception as e:
            logger.error(f"Critic failed: {e}")
            # Return a hard rejection on LLM failure
            return CritiqueMatrix(
                status="REJECT",
                param_count=sandbox_result.get("total_params", 0),
                params_within_budget=False,
                reason=f"Critic agent encountered an error: {str(e)}",
                suggestion="Retry with a simpler architecture",
                severity="HIGH",
                code_executed_successfully=sandbox_result.get("success", False),
                execution_error=str(e),
            )
