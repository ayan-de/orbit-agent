from langgraph.graph import StateGraph, END, START
from .state import AgentState

def build_agent_graph():
    """Build a minimal Orbit AI agent graph."""
    
    workflow = StateGraph(AgentState)
    
    # Placeholder for nodes
    # workflow.add_node("classifier", ...)
    
    # Simple flow for now
    workflow.add_edge(START, END)
    
    return workflow.compile()
