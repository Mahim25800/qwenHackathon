"""
Streaming utilities for SSE.
"""

import json
import asyncio
from datetime import datetime
from typing import AsyncGenerator
import logging
from graph.workflow import graph
from graph.state import GraphState
from schemas.swarm import SwarmConfig, SwarmEvent
from db.debate_log import save_log_entry, update_session_status

logger = logging.getLogger(__name__)

async def stream_debate(session_id: str, config: SwarmConfig) -> AsyncGenerator[str, None]:
    """
    Execute the LangGraph workflow and yield SSE events as JSON strings.
    """
    logger.info(f"Starting swarm debate for session: {session_id}")
    
    # Initialize state
    state: GraphState = {
        "session_id": session_id,
        "dataset_name": config.dataset_name,
        "input_shape": config.input_shape,
        "num_classes": config.num_classes,
        "max_params": config.max_params,
        "target_latency_ms": config.target_latency_ms,
        "max_iterations": config.max_iterations,
        "num_samples": 50000, # default
        
        "dataset_profile": None,
        "model_blueprint": None,
        "critique": None,
        
        "iteration": 0,
        "status": "running",
        
        "debate_log": [],
        "all_blueprints": [],
        "all_critiques": [],
        "error_message": None,
    }

    # Emit start event
    start_event = SwarmEvent(
        type="swarm_started",
        iteration=0,
        message=f"Started debate for {config.dataset_name}"
    )
    yield f"data: {start_event.model_dump_json()}\n\n"

    latest_blueprint = None

    try:
        # Use graph.astream with stream_mode="updates"
        async for event in graph.astream(state, stream_mode="updates"):
            # 'event' is a dict containing the node that ran and the state updates
            # Example: {"data_explorer": {"dataset_profile": {...}, "debate_log": [...]}}
            
            for node_name, updates in event.items():
                logger.info(f"Node completed: {node_name}")
                
                if "model_blueprint" in updates:
                    latest_blueprint = updates["model_blueprint"]
                
                # Extract the latest debate log entry
                if "debate_log" in updates and len(updates["debate_log"]) > 0:
                    latest_log = updates["debate_log"][-1]
                    
                    # Save to DB
                    save_log_entry(session_id, latest_log)
                    
                    # Emit event to frontend
                    agent_event = SwarmEvent(
                        type="agent_result",
                        agent=node_name.replace("_node", ""),
                        iteration=updates.get("iteration", 0),
                        data=latest_log["data"],
                        message=latest_log["message"]
                    )
                    yield f"data: {agent_event.model_dump_json()}\n\n"
                    
                # If Critic just ran, it might be the end of an iteration
                if node_name == "critic":
                    status = updates.get("status", "running")
                    critique = updates.get("critique", {})
                    
                    iter_event = SwarmEvent(
                        type="iteration_complete",
                        iteration=updates.get("iteration", 0),
                        data={"status": status, "critique_status": critique.get("status")},
                        message=f"Iteration complete. Status: {status}"
                    )
                    yield f"data: {iter_event.model_dump_json()}\n\n"
                    
                    if status in ["approved", "max_iterations"]:
                        update_session_status(session_id, status)
                        # Emit final completion
                        comp_event = SwarmEvent(
                            type="swarm_complete",
                            iteration=updates.get("iteration", 0),
                            data={
                                "final_status": status,
                                "final_blueprint": latest_blueprint,
                                "final_critique": critique
                            },
                            message=f"Swarm debate finished with status: {status}"
                        )
                        yield f"data: {comp_event.model_dump_json()}\n\n"

    except Exception as e:
        logger.error(f"Graph execution failed: {e}")
        update_session_status(session_id, "error")
        err_event = SwarmEvent(
            type="error",
            message=f"Error executing swarm: {str(e)}"
        )
        yield f"data: {err_event.model_dump_json()}\n\n"
        
    yield "data: [DONE]\n\n"
