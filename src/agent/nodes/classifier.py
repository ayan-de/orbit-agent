from typing import Dict, Any, Literal
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser

from src.agent.state import AgentState
from src.llm.factory import llm_factory
from src.agent.prompts.classifier import classifier_prompt

async def classify_intent(state: AgentState) -> Dict[str, Any]:
    """
    Analyzes the user's input and classifies the intent into one of the known categories.
    Updates the state with the determined intent.
    """
    messages = state["messages"]
    if not messages:
        # Default fallback if no messages exist (should rarely happen in a real flow)
        return {"intent": "unknown"}
    
    last_message = messages[-1]
    
    # Only process if the last message is from a human or AI (in a multi-turn conversation)
    # Typically we classify the USER'S intent based on their latest input.
    if isinstance(last_message, HumanMessage):
        user_input = last_message.content
    else:
        # If the last message was AI, look back for the last human message or fail
        # For simplicity, let's assume valid state has user input last or near last.
        # But in a graph loop, the last message might be tool output.
        # We need to find the last user message to classify intent if we are re-evaluating.
        # However, typically the classifier runs at the START of a turn.
        # If the graph is cycling, we might not need to re-classify unless it's a new turn.
        # For Phase 1, we assume a simple Linear flow: User -> Classify -> Act -> Respond.
        # So messages[-1] should be the user's input.
        user_input = last_message.content

    # Initialize LLM
    # We use a lower temperature for classification to be deterministic
    llm = llm_factory(temperature=0)
    
    # Create the chain
    chain = classifier_prompt | llm | StrOutputParser()
    
    # Execute the chain
    intent_str = await chain.ainvoke({"input": user_input})
    
    # Normalize and validate the output
    intent = intent_str.strip().lower()
    valid_intents = ["command", "question", "workflow", "confirmation"]
    
    if intent not in valid_intents:
        # Fallback for unexpected LLM output
        # If it looks like code, maybe command?
        # For now, default to 'question' or 'unknown'
        intent = "question"

    return {"intent": intent}
