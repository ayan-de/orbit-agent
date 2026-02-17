from typing import Dict, Any, Tuple
import json
import re
from langchain_core.output_parsers import StrOutputParser
from src.llm.factory import llm_factory
from src.agent.prompts.safety import safety_prompt

# Simple allowlist for common, low-risk commands
# Only applied if no complex shell operators are present
SAFE_PREFIXES = [
    "ls", "pwd", "echo", "cat", "grep", "find", 
    "git status", "git log", "git diff", "git show",
    "npm list", "pip list"
]

DANGEROUS_CHARS_REGEX = re.compile(r"[;&|><`$]")

async def is_safe_command(command: str) -> Tuple[bool, str]:
    """
    Analyzes a shell command to determine if it is safe to execute.
    Returns (is_safe: bool, reason: str).
    """
    print(f"DEBUG: Checking safety for '{command}'")
    
    if not command or not command.strip():
        return False, "Empty command"

    clean_cmd = command.strip()
    
    # 1. heuristic check: If simple command in whitelist, allow it.
    # Check for dangerous characters that imply chaining or redirection
    if not DANGEROUS_CHARS_REGEX.search(clean_cmd):
        for prefix in SAFE_PREFIXES:
            if clean_cmd.startswith(prefix):
                 if clean_cmd == prefix or clean_cmd.startswith(prefix + " "):
                     print(f"DEBUG: Allowed by whitelist: {prefix}")
                     return True, "Whitelisted safe command"
    
    # 2. LLM check for everything else
    # Initialize LLM (use low temp for deterministic safety checks)
    llm = llm_factory(temperature=0)
    
    # Create the chain
    chain = safety_prompt | llm | StrOutputParser()

    try:
        # Execute the chain
        result_text = await chain.ainvoke({"command": command})
        print(f"DEBUG: LLM Output for '{command}': {result_text}")
        
        # Clean up Markdown code blocks if present
        json_str = result_text.strip()
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif "```" in json_str:
             json_str = json_str.split("```")[1].split("```")[0].strip()
             
        data = json.loads(json_str)
        
        is_safe = data.get("safe", False)
        reason = data.get("reason", "Unknown risk")
        
        return is_safe, reason
        
    except json.JSONDecodeError:
        print(f"ERROR: Failed to parse JSON: {result_text}")
        return False, "Safety check failed: Invalid JSON response from LLM"
    except Exception as e:
        print(f"ERROR: Safety check exception: {e}")
        # Default to unsafe if we can't be sure
        return False, f"Safety check failed: {str(e)}"
