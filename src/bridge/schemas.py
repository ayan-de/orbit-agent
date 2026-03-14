from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from enum import Enum


class BridgeCommandRequest(BaseModel):
    command: str
    args: List[str] = []
    cwd: Optional[str] = None
    env: Optional[Dict[str, str]] = None
    timeout: int = 30000  # ms
    trusted: bool = False  # Skip injection check for internal tools


class BridgeCommandResponse(BaseModel):
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: int


class BridgeError(BaseModel):
    message: str
    code: str


# =============================================================================
# Human-in-Loop Confirmation Schemas
# =============================================================================

class ConfirmationType(str, Enum):
    """Types of confirmation requests."""
    TOOL_EXECUTION = "tool_execution"
    COMMAND_EXECUTION = "command_execution"
    PLAN_EXECUTION = "plan_execution"
    FILE_MODIFICATION = "file_modification"


class ConfirmationRequest(BaseModel):
    """Request for user confirmation sent to Bridge."""
    confirmation_id: str
    confirmation_type: ConfirmationType
    title: str
    message: str
    details: Dict[str, Any] = {}
    danger_level: int = 0  # 0=safe, 1=low, 2=medium, 3=high, 4=critical
    timeout_seconds: Optional[int] = None  # Auto-deny after timeout
    options: List[str] = ["approve", "deny"]  # Available options


class ConfirmationResponse(BaseModel):
    """Response from user confirmation."""
    confirmation_id: str
    approved: bool
    response: Optional[str] = None  # User's text response if any
    remember_decision: bool = False  # User wants to remember this decision
    timestamp: Optional[str] = None


class RememberedDecision(BaseModel):
    """Stored user decision for automatic approval/denial."""
    user_id: str
    decision_key: str  # e.g., "tool:shell_exec" or "command:rm"
    approved: bool
    created_at: str
    expires_at: Optional[str] = None  # Optional expiration
