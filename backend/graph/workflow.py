"""
Main LangGraph workflow assembly.
"""

from langgraph.graph import StateGraph, END
from .state import GraphState
from .nodes import data_explorer_node, architect_node, critic_node
from .router import should_continue

def create_debate_graph():
    """
    Builds and compiles the NeuralSwarm LangGraph state machine.
    """
    builder = StateGraph(GraphState)

    # Add nodes
    builder.add_node("data_explorer", data_explorer_node)
    builder.add_node("architect", architect_node)
    builder.add_node("critic", critic_node)

    # Define edges
    builder.set_entry_point("data_explorer")
    builder.add_edge("data_explorer", "architect")
    builder.add_edge("architect", "critic")

    # Conditional logic after critic
    builder.add_conditional_edges(
        "critic",
        should_continue,
        {
            "architect": "architect",
            "END": END
        }
    )

    # Compile the graph
    return builder.compile()

# Global graph instance
graph = create_debate_graph()
