"""
Command Safety Verification Module

Provides two-tier safety verification for shell commands:
1. Whitelist for known safe commands (fast path)
2. LLM verification for complex commands

Supports pipelines (|) and redirections (>, <) with validation.
"""

from typing import Dict, Any, Tuple
import json
import re
from langchain_core.output_parsers import StrOutputParser
from src.llm.factory import llm_factory
from src.agent.prompts.safety import safety_prompt


# =============================================================================
# Configuration
# =============================================================================

# Simple allowlist for common, low-risk commands
# Only applied if no complex shell operators are present
SAFE_PREFIXES = [
    "ls", "pwd", "echo", "cat", "grep", "find",
    "git status", "git log", "git diff", "git show",
    "npm list", "pip list", "head", "tail", "wc",
    "sort", "uniq", "cut", "awk", "sed", "tr",
    "which", "whoami", "date", "uname", "hostname",
]

# Allowed pipeline commands (read-only, non-destructive)
ALLOWED_PIPELINE_COMMANDS = frozenset([
    "grep", "egrep", "fgrep", "rg",
    "sed", "awk", "cut", "sort", "uniq",
    "head", "tail", "wc", "tr", "column",
    "jq", "yq", "xq", "tomlq",
    "less", "more", "cat", "bat",
    "tee", "xargs",
])

# Dangerous characters that indicate command substitution or chaining
# Note: | > < are handled separately with validation
DANGEROUS_CHARS_REGEX = re.compile(r"[;&`]|\$\(")

# Pattern for command substitution variants
COMMAND_SUBSTITUTION_REGEX = re.compile(r"\$\(|`")

# Pattern for dangerous variable expansions
DANGEROUS_VARIABLE_REGEX = re.compile(r"\$\({[^}]+}\)|\$\([^(]+\)")

# Maximum pipeline length to prevent abuse
MAX_PIPELINE_LENGTH = 5


# =============================================================================
# Safety Validation Functions
# =============================================================================

def _validate_pipeline_component(cmd: str) -> Tuple[bool, str]:
    """
    Validate a single component in a pipeline.

    Args:
        cmd: Single command (no pipes)

    Returns:
        (is_safe, reason) tuple
    """
    cmd = cmd.strip()
    if not cmd:
        return False, "Empty pipeline component"

    # Get the base command (first word)
    parts = cmd.split()
    if not parts:
        return False, "Empty command"

    base_cmd = parts[0]

    # Check if command is in allowed list
    if base_cmd in ALLOWED_PIPELINE_COMMANDS:
        return True, "Allowed pipeline command"

    # Check safe prefixes
    for prefix in SAFE_PREFIXES:
        if base_cmd == prefix or cmd.startswith(prefix + " "):
            return True, "Whitelisted safe command"

    # Check for any remaining dangerous characters in this component
    if DANGEROUS_CHARS_REGEX.search(cmd):
        return False, f"Dangerous characters in pipeline component: {cmd}"

    return True, "Pipeline component passed validation"


def _validate_redirection(command: str) -> Tuple[bool, str]:
    """
    Validate file redirections in a command.

    Args:
        command: Command string with potential redirections

    Returns:
        (is_safe, reason) tuple
    """
    # Check for output redirection
    if ">>" in command:
        # Append redirection - generally safe
        pass
    elif ">" in command:
        # Overwrite redirection - check for dangerous paths
        match = re.search(r">\s*([^\s&|;]+)", command)
        if match:
            target = match.group(1)
            # Block redirection to sensitive paths
            dangerous_paths = ["/etc/", "/dev/", "/proc/", "/sys/", "/root/"]
            for path in dangerous_paths:
                if target.startswith(path):
                    return False, f"Redirection to sensitive path blocked: {target}"
            # Block hidden files that might be sensitive
            if target.startswith("/."):
                return False, f"Redirection to hidden system path blocked: {target}"

    # Check for input redirection
    if "<" in command:
        match = re.search(r"<\s*([^\s&|;>]+)", command)
        if match:
            source = match.group(1)
            # Block reading from dangerous paths
            dangerous_paths = ["/etc/shadow", "/etc/passwd", "/root/"]
            for path in dangerous_paths:
                if source.startswith(path):
                    return False, f"Reading from sensitive path blocked: {source}"

    return True, "Redirection validated"


def _validate_pipeline(command: str) -> Tuple[bool, str]:
    """
    Validate a command containing pipelines.

    Args:
        command: Command string with potential pipes

    Returns:
        (is_safe, reason) tuple
    """
    # Split by pipe character
    components = command.split("|")

    if len(components) > MAX_PIPELINE_LENGTH:
        return False, f"Pipeline too long (max {MAX_PIPELINE_LENGTH} components)"

    for i, component in enumerate(components):
        # Handle redirections within pipeline components
        component_clean = re.sub(r"[<>]\s*[^\s&|;]*", "", component).strip()

        is_safe, reason = _validate_pipeline_component(component_clean)
        if not is_safe:
            return False, f"Pipeline component {i+1} unsafe: {reason}"

    return True, "Pipeline validated"


async def is_safe_command(command: str) -> Tuple[bool, str]:
    """
    Analyzes a shell command to determine if it is safe to execute.
    Returns (is_safe: bool, reason: str).

    Safety tiers:
    1. Whitelist check for simple commands
    2. Pipeline validation for piped commands
    3. Redirection validation for redirected commands
    4. LLM verification for everything else

    Args:
        command: Shell command to validate

    Returns:
        Tuple of (is_safe, reason)
    """
    print(f"DEBUG: Checking safety for '{command}'")

    if not command or not command.strip():
        return False, "Empty command"

    clean_cmd = command.strip()

    # ==========================================================================
    # Tier 1: Check for command substitution (always blocked)
    # ==========================================================================
    if COMMAND_SUBSTITUTION_REGEX.search(clean_cmd):
        return False, "Command substitution is not allowed for security reasons"

    # Check for dangerous variable expansions
    if DANGEROUS_VARIABLE_REGEX.search(clean_cmd):
        return False, "Dangerous variable expansion detected"

    # Check for chaining operators (always blocked)
    if DANGEROUS_CHARS_REGEX.search(clean_cmd):
        dangerous_matches = DANGEROUS_CHARS_REGEX.findall(clean_cmd)
        return False, f"Command chaining operators not allowed: {dangerous_matches}"

    # ==========================================================================
    # Tier 2: Simple whitelist check (no special operators)
    # ==========================================================================
    has_pipe = "|" in clean_cmd
    has_redirect = ">" in clean_cmd or "<" in clean_cmd

    if not has_pipe and not has_redirect:
        # Simple command - check whitelist
        for prefix in SAFE_PREFIXES:
            if clean_cmd == prefix or clean_cmd.startswith(prefix + " "):
                print(f"DEBUG: Allowed by whitelist: {prefix}")
                return True, "Whitelisted safe command"

    # ==========================================================================
    # Tier 3: Pipeline validation
    # ==========================================================================
    if has_pipe:
        is_safe, reason = _validate_pipeline(clean_cmd)
        if not is_safe:
            return False, reason

        # Also check for redirections in piped commands
        if has_redirect:
            is_safe, reason = _validate_redirection(clean_cmd)
            if not is_safe:
                return False, reason

        print(f"DEBUG: Pipeline validated: {clean_cmd}")
        return True, "Safe pipeline command"

    # ==========================================================================
    # Tier 4: Redirection validation
    # ==========================================================================
    if has_redirect:
        is_safe, reason = _validate_redirection(clean_cmd)
        if not is_safe:
            return False, reason

        # Validate the base command (without redirections)
        base_cmd = re.sub(r"[<>]\s*[^\s&|;]*", "", clean_cmd).strip()
        for prefix in SAFE_PREFIXES:
            if base_cmd == prefix or base_cmd.startswith(prefix + " "):
                print(f"DEBUG: Redirection with whitelisted command: {prefix}")
                return True, "Safe redirected command"

    # ==========================================================================
    # Tier 5: LLM check for everything else
    # ==========================================================================
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


# =============================================================================
# Utility Functions
# =============================================================================

def get_command_parts(command: str) -> list[str]:
    """
    Split a command into its constituent parts for analysis.

    Args:
        command: Shell command string

    Returns:
        List of command parts
    """
    # Simple split by spaces, respecting quotes
    parts = []
    current = ""
    in_quote = False
    quote_char = None

    for char in command:
        if char in '"\'':
            if not in_quote:
                in_quote = True
                quote_char = char
            elif char == quote_char:
                in_quote = False
                quote_char = None
            else:
                current += char
        elif char == ' ' and not in_quote:
            if current:
                parts.append(current)
                current = ""
        else:
            current += char

    if current:
        parts.append(current)

    return parts


def estimate_command_risk(command: str) -> Dict[str, Any]:
    """
    Estimate the risk level of a command without full LLM validation.

    This provides a quick heuristic for UI/UX purposes.

    Args:
        command: Shell command string

    Returns:
        Dict with risk_level (0-10), risk_factors list, and safe boolean
    """
    risk_factors = []
    risk_level = 0

    # Check for dangerous operators
    if COMMAND_SUBSTITUTION_REGEX.search(command):
        risk_factors.append("command_substitution")
        risk_level += 8

    if DANGEROUS_CHARS_REGEX.search(command):
        risk_factors.append("chaining_operators")
        risk_level += 5

    # Check for sensitive paths
    sensitive_paths = ["/etc/", "/root/", "/home/", "/dev/", "/proc/", "/sys/"]
    for path in sensitive_paths:
        if path in command:
            risk_factors.append(f"sensitive_path:{path}")
            risk_level += 3

    # Check for network operations
    if any(word in command for word in ["curl", "wget", "nc", "netcat", "ssh", "scp"]):
        risk_factors.append("network_operation")
        risk_level += 4

    # Check for file modification
    if any(word in command for word in ["rm", "rmdir", "mv", "cp", "chmod", "chown"]):
        risk_factors.append("file_modification")
        risk_level += 3

    # Check for package management
    if any(word in command for word in ["apt", "yum", "dnf", "pacman", "brew", "npm", "pip"]):
        risk_factors.append("package_management")
        risk_level += 2

    # Cap at 10
    risk_level = min(risk_level, 10)

    return {
        "risk_level": risk_level,
        "risk_factors": risk_factors,
        "safe": risk_level <= 3 and len(risk_factors) == 0,
    }
