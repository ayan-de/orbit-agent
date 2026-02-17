from langgraph.graph import StateGraph, END, START
from src.agent.nodes.classifier import classify_intent
from src.agent.nodes.responder import respond
from src.agent.state import AgentState

workflow = StateGraph(AgentState)

workflow.add_node("classifier", classify_intent)
workflow.add_node("responder", respond)

workflow.add_edge(START, "classifier")
workflow.add_edge("classifier", "responder")
workflow.add_edge("responder", END)

# Create/Compile graph
app = workflow.compile()
