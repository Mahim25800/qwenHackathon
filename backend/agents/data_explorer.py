"""
Data Explorer Agent — Analyzes dataset characteristics and computes theoretical bounds.
Uses Qwen-Plus for speed. Outputs a structured DatasetProfile.
"""

import math
import logging
from .base import BaseAgent
from schemas.dataset import DatasetProfile, TheoreticalBounds
from config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a senior ML research scientist specializing in dataset analysis and neural architecture search.

Your task is to analyze a dataset specification and produce a comprehensive DatasetProfile in JSON format.

You MUST:
1. Calculate the theoretical bounds for the architecture based on input dimensions.
2. Determine how many pooling layers (2x2, stride 2) can be applied before spatial dimensions reach 1.
3. Recommend architecture families that are appropriate for the input size and task complexity.
4. Assess the task complexity based on the number of classes, input resolution, and data characteristics.
5. Include any warnings about impossible or problematic configurations.

Always respond in valid JSON matching the DatasetProfile schema. Do not include any text outside the JSON."""


class DataExplorerAgent(BaseAgent):
    """
    Explores the dataset specification and produces a DatasetProfile.
    Computes theoretical bounds to guide the Model Architect.
    """

    def __init__(self):
        super().__init__(model=settings.qwen_model_fast, temperature=0.3)

    def _compute_theoretical_bounds(
        self, input_shape: list[int]
    ) -> TheoreticalBounds:
        """
        Compute architectural constraints based on input spatial dimensions.
        This is done deterministically (no LLM needed).
        """
        channels, height, width = input_shape
        spatial = min(height, width)

        # Calculate max pooling layers (each halves spatial dims)
        max_pools = 0
        dims_after_pools = []
        current = spatial
        while current > 1:
            current = current // 2
            if current >= 1:
                max_pools += 1
                dims_after_pools.append(current)

        # Max reasonable conv depth (heuristic)
        max_conv_depth = min(max_pools * 4, 50)

        # Minimum receptive field (should cover ~25% of input)
        min_rf = max(3, spatial // 4)

        return TheoreticalBounds(
            max_pooling_layers=max_pools,
            min_receptive_field=min_rf,
            max_conv_depth=max_conv_depth,
            spatial_dims_after_pools=dims_after_pools,
        )

    def explore(
        self,
        dataset_name: str,
        input_shape: list[int],
        num_classes: int,
        num_samples: int = 50000,
    ) -> DatasetProfile:
        """
        Analyze the dataset and produce a DatasetProfile.
        Combines deterministic computation with LLM analysis.
        """
        # Compute bounds deterministically
        bounds = self._compute_theoretical_bounds(input_shape)

        user_prompt = f"""Analyze this dataset and produce a DatasetProfile:

Dataset: {dataset_name}
Input shape (C, H, W): {input_shape}
Number of classes: {num_classes}
Number of training samples: {num_samples}

Pre-computed theoretical bounds:
- Max pooling layers (2x2, stride 2): {bounds.max_pooling_layers}
- Spatial dims after each pool: {bounds.spatial_dims_after_pools}
- Min receptive field: {bounds.min_receptive_field}
- Max conv depth: {bounds.max_conv_depth}

Based on these bounds, provide:
1. A description of the data characteristics
2. A complexity score (0.0-1.0)
3. A ranked list of recommended architecture families (best first)
4. Any important notes or warnings

Consider:
- If spatial size is very small (< 32), avoid architectures with too many pooling layers
- For many classes (> 100), favor deeper architectures
- For few samples (< 10000), favor smaller architectures to avoid overfitting
- If the input is grayscale (1 channel), note this for architecture design"""

        try:
            profile = self._structured_chat(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=user_prompt,
                response_model=DatasetProfile,
            )
            # Override with our deterministic bounds (more reliable than LLM)
            profile.theoretical_bounds = bounds
            profile.name = dataset_name
            profile.input_shape = input_shape
            profile.num_classes = num_classes
            profile.num_samples = num_samples
            return profile

        except Exception as e:
            logger.error(f"Data Explorer failed: {e}")
            # Fallback: return a basic profile with computed bounds
            return DatasetProfile(
                name=dataset_name,
                input_shape=input_shape,
                num_classes=num_classes,
                num_samples=num_samples,
                data_characteristics=f"Standard image classification dataset with {num_classes} classes",
                theoretical_bounds=bounds,
                recommended_architectures=["MobileNetV3", "EfficientNet-B0", "ResNet-18"],
                complexity_score=min(1.0, num_classes / 100),
                notes="Fallback profile — LLM analysis failed",
            )
