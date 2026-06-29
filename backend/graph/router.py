"""
Conditional edges for the LangGraph workflow.
"""

from typing import Literal
from graph.state import GraphState

def should_continue(state: GraphState) -> Literal["architect", "END"]:
    """
    Decide whether to loop back to the Architect or end the debate.
    """
    status = state.get("status", "running")
    if status == "approved" or status == "max_iterations" or status == "error":
        return "END"
    
    return "architect"
