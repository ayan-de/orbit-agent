from typing import Dict, Any
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from src.agent.state import AgentState
from src.llm.factory import llm_factory

# System prompt for generating shell commands from natural language
COMMAND_GENERATOR_SYSTEM_PROMPT = """You are an expert shell command generator for an AI coding agent named Orbit.

Your job is to translate the user's natural language request into a precise, safe shell command.

Guidelines:
1. Generate ONLY the shell command, nothing else. No explanations, no backticks.
2. Use safe, standard commands. Avoid dangerous commands (rm -rf, sudo reboot, etc.).
3. For file operations, use relative paths where possible.
4. Use proper flags for better output (e.g., `ls -la`, `git status`).
5. If the request is ambiguous, generate the most reasonable interpretation.

Examples:
- "what directory am I in?" → `pwd`
- "list files in current directory" → `ls -la`
- "show git status" → `git status`
- "create a folder named test" → `mkdir test`
- "read contents of file.txt" → `cat file.txt`
- "find all Python files" → `find . -name "*.py" -type f`

Return ONLY the shell command as a plain string.
"""

command_generator_prompt = ChatPromptTemplate.from_messages([
    ("system", COMMAND_GENERATOR_SYSTEM_PROMPT),
    ("user", "{user_request}")
])


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

        # Clean up any markdown code blocks
        if command.startswith("```"):
            command = command.split("\n")[1]  # Remove ``` at start
        if command.endswith("```"):
            command = command.rsplit("\n", 1)[0]  # Remove ``` at end

        command = command.strip()

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
