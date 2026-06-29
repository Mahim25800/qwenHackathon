"""
Graph Node Functions — Each function is a node in the LangGraph StateGraph.
Nodes transform the GraphState by calling the appropriate agent.
"""

import logging
from datetime import datetime
from graph.state import GraphState
from agents.data_explorer import DataExplorerAgent
from agents.architect import ModelArchitectAgent
from agents.critic import PerformanceCriticAgent
from schemas.dataset import DatasetProfile
from schemas.model import ModelBlueprint
from schemas.critique import CritiqueMatrix

logger = logging.getLogger(__name__)

# Agent instances (created once, reused across invocations)
_explorer = None
_architect = None
_critic = None


def _get_explorer():
    global _explorer
    if _explorer is None:
        _explorer = DataExplorerAgent()
    return _explorer


def _get_architect():
    global _architect
    if _architect is None:
        _architect = ModelArchitectAgent()
    return _architect


def _get_critic():
    global _critic
    if _critic is None:
        _critic = PerformanceCriticAgent()
    return _critic


def data_explorer_node(state: GraphState) -> dict:
    """
    Node 1: Data Explorer.
    Analyzes the dataset and produces a DatasetProfile.
    """
    logger.info(f"[Explorer] Analyzing dataset: {state['dataset_name']}")

    explorer = _get_explorer()
    profile = explorer.explore(
        dataset_name=state["dataset_name"],
        input_shape=state["input_shape"],
        num_classes=state["num_classes"],
        num_samples=state.get("num_samples", 50000),
    )

    profile_dict = profile.model_dump()

    # Build debate log entry
    log_entry = {
        "agent": "explorer",
        "action": "analyze_dataset",
        "data": profile_dict,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "iteration": 0,
        "message": f"Analyzed {state['dataset_name']}: {profile.data_characteristics[:100]}",
    }

    return {
        "dataset_profile": profile_dict,
        "iteration": 1,
        "status": "running",
        "debate_log": state.get("debate_log", []) + [log_entry],
    }


def architect_node(state: GraphState) -> dict:
    """
    Node 2: Model Architect.
    Designs (or revises) a PyTorch model based on the dataset profile and any previous critique.
    """
    iteration = state.get("iteration", 1)
    logger.info(f"[Architect] Designing model (iteration {iteration})")

    architect = _get_architect()
    profile = DatasetProfile(**state["dataset_profile"])

    # Reconstruct previous critique and blueprint if revising
    prev_critique = None
    prev_blueprint = None
    if iteration > 1 and state.get("critique"):
        prev_critique = CritiqueMatrix(**state["critique"])
    if state.get("model_blueprint"):
        prev_blueprint = ModelBlueprint(**state["model_blueprint"])

    blueprint = architect.design(
        dataset_profile=profile,
        max_params=state["max_params"],
        target_latency_ms=state["target_latency_ms"],
        user_constraints=state.get("user_constraints", ""),
        iteration=iteration,
        max_iterations=state["max_iterations"],
        previous_critique=prev_critique,
        previous_blueprint=prev_blueprint,
    )

    blueprint_dict = blueprint.model_dump()

    log_entry = {
        "agent": "architect",
        "action": "design_model" if iteration == 1 else "revise_model",
        "data": {
            "architecture_name": blueprint.architecture_name,
            "total_params": blueprint.total_params,
            "design_rationale": blueprint.design_rationale,
            "pytorch_code": blueprint.pytorch_code,
            "iteration": iteration,
        },
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "iteration": iteration,
        "message": f"{'Designed' if iteration == 1 else 'Revised'} {blueprint.architecture_name} ({blueprint.total_params:,} estimated params)",
    }

    return {
        "model_blueprint": blueprint_dict,
        "debate_log": state.get("debate_log", []) + [log_entry],
        "all_blueprints": state.get("all_blueprints", []) + [blueprint_dict],
    }


def critic_node(state: GraphState) -> dict:
    """
    Node 3: Performance Critic.
    Executes the model in the sandbox and generates a structured critique.
    """
    iteration = state.get("iteration", 1)
    logger.info(f"[Critic] Evaluating model (iteration {iteration})")

    critic = _get_critic()
    blueprint = ModelBlueprint(**state["model_blueprint"])

    critique = critic.critique(
        blueprint=blueprint,
        max_params=state["max_params"],
        target_latency_ms=state["target_latency_ms"],
        input_shape=state["input_shape"],
    )

    critique_dict = critique.model_dump()

    status_emoji = "✅" if critique.status == "APPROVE" else "❌"
    log_entry = {
        "agent": "critic",
        "action": "evaluate_model",
        "data": {
            "status": critique.status,
            "param_count": critique.param_count,
            "params_within_budget": critique.params_within_budget,
            "reason": critique.reason,
            "suggestion": critique.suggestion,
            "severity": critique.severity,
            "bottleneck_layer": critique.bottleneck_layer,
        },
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "iteration": iteration,
        "message": f"{status_emoji} {critique.status}: {critique.reason[:100]}",
    }

    # Determine new status
    new_status = "running"
    if critique.status == "APPROVE" and critique.code_executed_successfully and critique.params_within_budget:
        new_status = "approved"
    elif iteration >= state["max_iterations"]:
        new_status = "max_iterations"

    # Increment iteration for next loop
    new_iteration = iteration + 1 if critique.status == "REJECT" else iteration

    return {
        "critique": critique_dict,
        "status": new_status,
        "iteration": new_iteration,
        "debate_log": state.get("debate_log", []) + [log_entry],
        "all_critiques": state.get("all_critiques", []) + [critique_dict],
    }
