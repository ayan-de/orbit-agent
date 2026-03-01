"""
Permission Checker Module

Handles tool permission checking and user confirmation logic.
Determines when tools require user confirmation based on danger levels.
"""

from typing import Optional, Dict, Any
from enum import Enum

from src.tools.base import OrbitTool, get_danger_category


class PermissionResult(Enum):
    """
    Result of a permission check.

    ALLOWED: Tool can execute without confirmation
    REQUIRES_CONFIRMATION: Tool requires user confirmation
    DENIED: Tool is not allowed (e.g., danger too high, wrong environment)
    """

    ALLOWED = "allowed"
    REQUIRES_CONFIRMATION = "requires_confirmation"
    DENIED = "denied"


class PermissionCheckResult:
    """
    Result of a tool permission check.

    Attributes:
        result: The permission outcome (ALLOWED, REQUIRES_CONFIRMATION, DENIED)
        reason: Human-readable explanation of why this result was returned
        tool_danger_level: The tool's danger level
        user_permission_level: The user's permission level used
    """

    def __init__(
        self,
        result: PermissionResult,
        reason: str,
        tool_danger_level: int,
        user_permission_level: int = 1,
    ):
        self.result = result
        self.reason = reason
        self.tool_danger_level = tool_danger_level
        self.user_permission_level = user_permission_level

    def is_allowed(self) -> bool:
        """Check if tool is allowed to execute."""
        return self.result == PermissionResult.ALLOWED

    def requires_confirmation(self) -> bool:
        """Check if tool requires user confirmation."""
        return self.result == PermissionResult.REQUIRES_CONFIRMATION

    def is_denied(self) -> bool:
        """Check if tool execution is denied."""
        return self.result == PermissionResult.DENIED

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "result": self.result.value,
            "reason": self.reason,
            "tool_danger_level": self.tool_danger_level,
            "user_permission_level": self.user_permission_level,
        }


def needs_confirmation(
    tool: OrbitTool,
    user_permission_level: int = 1,
    environment: str = "dev",
) -> PermissionCheckResult:
    """
    Check if a tool requires user confirmation.

    This function evaluates:
    1. Tool's explicit requires_confirmation flag
    2. Tool's danger level vs user permission level
    3. Tool's allowed environments vs current environment

    Args:
        tool: The OrbitTool instance to check
        user_permission_level: User's permission level (1-10, higher = more access)
        environment: Current environment (dev, staging, production)

    Returns:
        PermissionCheckResult with outcome and reasoning

    Example:
        >>> tool = ShellTool()
        >>> result = needs_confirmation(tool, user_permission_level=1)
        >>> if result.requires_confirmation():
        ...     # Ask user for confirmation
        ...     pass
    """
    # Get tool metadata
    danger_level = getattr(tool, "danger_level", 0)
    requires_conf = getattr(tool, "requires_confirmation", False)
    allowed_envs = getattr(tool, "allowed_environments", ["dev", "staging", "production"])

    # 1. Check if tool is allowed in this environment
    if environment not in allowed_envs:
        return PermissionCheckResult(
            result=PermissionResult.DENIED,
            reason=f"Tool not allowed in {environment} environment. Allowed: {', '.join(allowed_envs)}",
            tool_danger_level=danger_level,
            user_permission_level=user_permission_level,
        )

    # 2. Check if tool explicitly requires confirmation
    if requires_conf:
        return PermissionCheckResult(
            result=PermissionResult.REQUIRES_CONFIRMATION,
            reason=f"Tool '{tool.name}' explicitly requires confirmation (danger level: {danger_level})",
            tool_danger_level=danger_level,
            user_permission_level=user_permission_level,
        )

    # 3. Check danger level vs user permission
    # User can execute tools with danger_level <= their permission level
    if danger_level > user_permission_level:
        category = get_danger_category(danger_level)
        return PermissionCheckResult(
            result=PermissionResult.REQUIRES_CONFIRMATION,
            reason=(
                f"Tool '{tool.name}' has danger level {danger_level} ({category}), "
                f"which exceeds your permission level ({user_permission_level}). "
                "Confirmation required."
            ),
            tool_danger_level=danger_level,
            user_permission_level=user_permission_level,
        )

    # 4. Tool is safe to execute
    return PermissionCheckResult(
        result=PermissionResult.ALLOWED,
        reason=f"Tool '{tool.name}' is safe to execute (danger level: {danger_level})",
        tool_danger_level=danger_level,
        user_permission_level=user_permission_level,
    )


def can_auto_approve(
    tool: OrbitTool,
    user_permission_level: int = 1,
) -> bool:
    """
    Check if a tool can be auto-approved without asking user.

    Auto-approval criteria:
    - Tool does NOT explicitly require confirmation
    - Tool danger level <= user permission level
    - Danger level is in SAFE range (0-2)

    Args:
        tool: The OrbitTool instance to check
        user_permission_level: User's permission level

    Returns:
        True if tool can be auto-approved, False otherwise
    """
    result = needs_confirmation(tool, user_permission_level)
    return result.is_allowed() and tool.danger_level <= 2


def get_permission_prompt(
    tool: OrbitTool,
    check_result: PermissionCheckResult,
) -> str:
    """
    Generate a user-facing prompt for tool confirmation.

    Args:
        tool: The OrbitTool instance
        check_result: The permission check result

    Returns:
        User-friendly confirmation prompt string
    """
    danger_category = get_danger_category(tool.danger_level)

    prompt = f"⚠️  Tool '{tool.name}' requires confirmation\n\n"
    prompt += f"**Category:** {tool.category}\n"
    prompt += f"**Danger Level:** {tool.danger_level}/10 ({danger_category})\n"
    prompt += f"**Reason:** {check_result.reason}\n\n"
    prompt += "**Do you want to proceed?** (yes/no)\n"
    prompt += "- Type 'yes' or 'y' to approve\n"
    prompt += "- Type 'no' or 'n' to deny\n"
    prompt += "- Type 'always' to auto-approve this tool for this session"

    return prompt


def parse_confirmation_response(response: str) -> Optional[bool]:
    """
    Parse user's confirmation response.

    Args:
        response: User's response string

    Returns:
        True if approved, False if denied, None if unclear
    """
    response_clean = response.strip().lower()

    # Approvals
    if response_clean in ["yes", "y", "yeah", "yep", "sure", "ok"]:
        return True

    # Denials
    if response_clean in ["no", "n", "nope", "nah", "cancel"]:
        return False

    # Unclear
    return None


# ============================================================================
# Batch Permission Checking
# ============================================================================

def check_tools_permissions(
    tools: list[OrbitTool],
    user_permission_level: int = 1,
    environment: str = "dev",
) -> Dict[str, PermissionCheckResult]:
    """
    Check permissions for multiple tools.

    Args:
        tools: List of OrbitTool instances to check
        user_permission_level: User's permission level
        environment: Current environment

    Returns:
        Dictionary mapping tool names to permission check results
    """
    results = {}

    for tool in tools:
        result = needs_confirmation(tool, user_permission_level, environment)
        results[tool.name] = result

    return results


def get_tools_requiring_confirmation(
    tools: list[OrbitTool],
    user_permission_level: int = 1,
) -> list[OrbitTool]:
    """
    Get list of tools that require confirmation.

    Args:
        tools: List of OrbitTool instances to check
        user_permission_level: User's permission level

    Returns:
        List of tools that require confirmation
    """
    requiring = []

    for tool in tools:
        result = needs_confirmation(tool, user_permission_level)
        if result.requires_confirmation():
            requiring.append(tool)

    return requiring


def get_auto_approvable_tools(
    tools: list[OrbitTool],
    user_permission_level: int = 1,
) -> list[OrbitTool]:
    """
    Get list of tools that can be auto-approved.

    Args:
        tools: List of OrbitTool instances to check
        user_permission_level: User's permission level

    Returns:
        List of tools that can execute without confirmation
    """
    approvable = []

    for tool in tools:
        if can_auto_approve(tool, user_permission_level):
            approvable.append(tool)

    return approvable
