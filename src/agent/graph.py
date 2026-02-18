from langgraph.graph import StateGraph, END, START
from src.agent.nodes.classifier import classify_intent
from src.agent.nodes.command_generator import generate_command
from src.agent.nodes.responder import respond
from src.agent.state import AgentState

workflow = StateGraph(AgentState)

workflow.add_node("classifier", classify_intent)
workflow.add_node("command_generator", generate_command)
workflow.add_node("responder", respond)

# Conditional routing: only generate command if intent is "command"
def should_generate_command(state: AgentState) -> str:
    intent = state.get("intent", "unknown")
    return "command_generator" if intent == "command" else "responder"

workflow.add_edge(START, "classifier")
workflow.add_conditional_edges(
    "classifier",
    should_generate_command,
    {
        "command_generator": "command_generator",
        "responder": "responder"
    }
)
workflow.add_edge("command_generator", "responder")
workflow.add_edge("responder", END)

# Create/Compile graph
app = workflow.compile()
