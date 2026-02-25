from typing import Dict, Any
import re
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from src.agent.state import AgentState
from src.llm.factory import llm_factory

from src.agent.prompts.command_generator import command_generator_prompt


async def generate_command(state: AgentState) -> Dict[str, Any]:
    """
    Generates a shell command from the user's natural language request.
    Only runs when intent is 'command'.
    """
    messages = state["messages"]
    intent = state.get("intent", "unknown")

    # Only generate command for command intent
    if intent != "command":
        return {}

    # Get the user's request (last human message)
    user_request = ""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            user_request = msg.content
            break

    if not user_request:
        return {}

    # Initialize LLM with low temperature for deterministic output
    llm = llm_factory(temperature=0)

    # Create the chain
    chain = command_generator_prompt | llm | StrOutputParser()

    # Execute the chain
    try:
        command = await chain.ainvoke({"user_request": user_request})
        command = command.strip()

        # Clean up any markdown code blocks (```bash, ```sh, or just ```)
        # Match ```language\ncmd\n``` or ```\ncmd\n```
        code_block_pattern = r'```(?:bash|sh)?\s*\n(.*?)\n```'
        match = re.search(code_block_pattern, command, re.DOTALL)
        if match:
            command = match.group(1).strip()
        else:
            # Fallback: just strip backticks if they're at the edges
            command = command.strip('`')

        # Strip any remaining leading/trailing whitespace and quotes
        command = command.strip().strip('"').strip("'")

        # Create a message that clearly indicates the command
        response_message = f"Running: `{command}`"

        # Return the command and response message
        return {
            "messages": [AIMessage(content=response_message)],
            "command": command  # Store the command in state
        }
    except Exception as e:
        # If generation fails, return an error message
        error_msg = f"Failed to generate command: {str(e)}"
        return {
            "messages": [AIMessage(content=error_msg)],
            "command": ""
        }
