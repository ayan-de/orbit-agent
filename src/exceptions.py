"""
Custom Exception Hierarchy for Orbit Agent

Provides a structured exception system for better error handling,
debugging, and API error responses.

Exception Hierarchy:
    OrbitError (base)
    ├── ConfigurationError
    ├── LLMError
    │   ├── LLMConnectionError
    │   ├── LLMRateLimitError
    │   └── LLMResponseError
    ├── ToolError
    │   ├── ToolNotFoundError
    │   ├── ToolExecutionError
    │   └── ToolValidationError
    ├── SafetyError
    │   ├── CommandBlockedError
    │   └── DangerousPatternError
    ├── MemoryError
    │   ├── MemoryReadError
    │   ├── MemoryWriteError
    │   └── MemoryCompactionError
    ├── MCPError
    │   ├── MCPConnectionError
    │   ├── MCPToolError
    │   └── MCPAuthError
    ├── BridgeError
    │   ├── BridgeConnectionError
    │   ├── BridgeTimeoutError
    │   └── BridgeAuthError
    ├── IntegrationError
    │   ├── IntegrationNotFoundError
    │   ├── IntegrationAuthError
    │   └── IntegrationConfigError
    └── AgentError
        ├── AgentStateError
        ├── AgentWorkflowError
        └── AgentTimeoutError
"""

from typing import Optional, Dict, Any


# =============================================================================
# Base Exception
# =============================================================================

class OrbitError(Exception):
    """
    Base exception for all Orbit Agent errors.

    All custom exceptions should inherit from this class.
    Provides common functionality for error codes, details, and HTTP status.
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        http_status: int = 500,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.http_status = http_status

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details,
        }

    def __str__(self) -> str:
        if self.details:
            return f"[{self.error_code}] {self.message} - {self.details}"
        return f"[{self.error_code}] {self.message}"


# =============================================================================
# Configuration Errors
# =============================================================================

class ConfigurationError(OrbitError):
    """Raised when configuration is missing or invalid."""

    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code="CONFIG_ERROR",
            details={"config_key": config_key, **(details or {})},
            http_status=500,
        )


# =============================================================================
# LLM Errors
# =============================================================================

class LLMError(OrbitError):
    """Base exception for LLM-related errors."""

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        http_status: int = 502,
    ):
        super().__init__(
            message=message,
            error_code="LLM_ERROR",
            details={"provider": provider, "model": model, **(details or {})},
            http_status=http_status,
        )


class LLMConnectionError(LLMError):
    """Raised when connection to LLM provider fails."""

    def __init__(
        self,
        message: str = "Failed to connect to LLM provider",
        provider: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            provider=provider,
            details=details,
            http_status=503,
        )
        self.error_code = "LLM_CONNECTION_ERROR"


class LLMRateLimitError(LLMError):
    """Raised when LLM rate limit is exceeded."""

    def __init__(
        self,
        message: str = "LLM rate limit exceeded",
        provider: Optional[str] = None,
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            provider=provider,
            details={"retry_after": retry_after, **(details or {})},
            http_status=429,
        )
        self.error_code = "LLM_RATE_LIMIT_ERROR"
        self.retry_after = retry_after


class LLMResponseError(LLMError):
    """Raised when LLM response is invalid or cannot be parsed."""

    def __init__(
        self,
        message: str = "Invalid LLM response",
        provider: Optional[str] = None,
        raw_response: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            provider=provider,
            details={"raw_response": raw_response[:500] if raw_response else None, **(details or {})},
            http_status=502,
        )
        self.error_code = "LLM_RESPONSE_ERROR"


# =============================================================================
# Tool Errors
# =============================================================================

class ToolError(OrbitError):
    """Base exception for tool-related errors."""

    def __init__(
        self,
        message: str,
        tool_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        http_status: int = 500,
    ):
        super().__init__(
            message=message,
            error_code="TOOL_ERROR",
            details={"tool_name": tool_name, **(details or {})},
            http_status=http_status,
        )


class ToolNotFoundError(ToolError):
    """Raised when a requested tool is not found."""

    def __init__(
        self,
        tool_name: str,
        available_tools: Optional[list] = None,
    ):
        super().__init__(
            message=f"Tool not found: {tool_name}",
            tool_name=tool_name,
            details={"available_tools": available_tools[:10] if available_tools else None},
            http_status=404,
        )
        self.error_code = "TOOL_NOT_FOUND"


class ToolExecutionError(ToolError):
    """Raised when tool execution fails."""

    def __init__(
        self,
        message: str,
        tool_name: str,
        original_error: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            tool_name=tool_name,
            details={"original_error": original_error, **(details or {})},
            http_status=500,
        )
        self.error_code = "TOOL_EXECUTION_ERROR"


class ToolValidationError(ToolError):
    """Raised when tool input validation fails."""

    def __init__(
        self,
        message: str,
        tool_name: str,
        validation_errors: Optional[Dict[str, str]] = None,
    ):
        super().__init__(
            message=message,
            tool_name=tool_name,
            details={"validation_errors": validation_errors},
            http_status=400,
        )
        self.error_code = "TOOL_VALIDATION_ERROR"


# =============================================================================
# Safety Errors
# =============================================================================

class SafetyError(OrbitError):
    """Base exception for safety-related errors."""

    def __init__(
        self,
        message: str,
        command: Optional[str] = None,
        reason: Optional[str] = None,
        http_status: int = 400,
    ):
        super().__init__(
            message=message,
            error_code="SAFETY_ERROR",
            details={"command": command, "reason": reason},
            http_status=http_status,
        )


class CommandBlockedError(SafetyError):
    """Raised when a command is blocked by safety rules."""

    def __init__(
        self,
        command: str,
        reason: str,
        risk_level: Optional[int] = None,
    ):
        super().__init__(
            message=f"Command blocked: {reason}",
            command=command,
            reason=reason,
            http_status=403,
        )
        self.error_code = "COMMAND_BLOCKED"
        self.details["risk_level"] = risk_level


class DangerousPatternError(SafetyError):
    """Raised when a dangerous pattern is detected in input."""

    def __init__(
        self,
        pattern: str,
        context: Optional[str] = None,
    ):
        super().__init__(
            message=f"Dangerous pattern detected: {pattern}",
            command=context,
            reason="Input contains potentially dangerous pattern",
            http_status=400,
        )
        self.error_code = "DANGEROUS_PATTERN"
        self.details["pattern"] = pattern


# =============================================================================
# Memory Errors
# =============================================================================

class MemoryError(OrbitError):
    """Base exception for memory-related errors."""

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            error_code="MEMORY_ERROR",
            details={"operation": operation, **(details or {})},
            http_status=500,
        )


class MemoryReadError(MemoryError):
    """Raised when reading from memory fails."""

    def __init__(
        self,
        message: str = "Failed to read from memory",
        file_path: Optional[str] = None,
    ):
        super().__init__(
            message=message,
            operation="read",
            details={"file_path": file_path},
        )
        self.error_code = "MEMORY_READ_ERROR"


class MemoryWriteError(MemoryError):
    """Raised when writing to memory fails."""

    def __init__(
        self,
        message: str = "Failed to write to memory",
        file_path: Optional[str] = None,
    ):
        super().__init__(
            message=message,
            operation="write",
            details={"file_path": file_path},
        )
        self.error_code = "MEMORY_WRITE_ERROR"


class MemoryCompactionError(MemoryError):
    """Raised when memory compaction fails."""

    def __init__(
        self,
        message: str = "Memory compaction failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            operation="compaction",
            details=details,
        )
        self.error_code = "MEMORY_COMPACTION_ERROR"


# =============================================================================
# MCP Errors
# =============================================================================

class MCPError(OrbitError):
    """Base exception for MCP-related errors."""

    def __init__(
        self,
        message: str,
        server_name: Optional[str] = None,
        tool_name: Optional[str] = None,
        http_status: int = 502,
    ):
        super().__init__(
            message=message,
            error_code="MCP_ERROR",
            details={"server_name": server_name, "tool_name": tool_name},
            http_status=http_status,
        )


class MCPConnectionError(MCPError):
    """Raised when MCP server connection fails."""

    def __init__(
        self,
        server_name: str,
        original_error: Optional[str] = None,
    ):
        super().__init__(
            message=f"Failed to connect to MCP server: {server_name}",
            server_name=server_name,
            http_status=503,
        )
        self.error_code = "MCP_CONNECTION_ERROR"
        self.details["original_error"] = original_error


class MCPToolError(MCPError):
    """Raised when MCP tool execution fails."""

    def __init__(
        self,
        message: str,
        server_name: str,
        tool_name: str,
    ):
        super().__init__(
            message=message,
            server_name=server_name,
            tool_name=tool_name,
        )
        self.error_code = "MCP_TOOL_ERROR"


class MCPAuthError(MCPError):
    """Raised when MCP authentication fails."""

    def __init__(
        self,
        server_name: str,
        auth_url: Optional[str] = None,
    ):
        super().__init__(
            message=f"Authentication required for MCP server: {server_name}",
            server_name=server_name,
            http_status=401,
        )
        self.error_code = "MCP_AUTH_ERROR"
        self.details["auth_url"] = auth_url


# =============================================================================
# Bridge Errors
# =============================================================================

class BridgeError(OrbitError):
    """Base exception for Bridge communication errors."""

    def __init__(
        self,
        message: str,
        endpoint: Optional[str] = None,
        http_status: int = 502,
    ):
        super().__init__(
            message=message,
            error_code="BRIDGE_ERROR",
            details={"endpoint": endpoint},
            http_status=http_status,
        )


class BridgeConnectionError(BridgeError):
    """Raised when connection to Bridge fails."""

    def __init__(
        self,
        message: str = "Failed to connect to Bridge service",
        endpoint: Optional[str] = None,
    ):
        super().__init__(
            message=message,
            endpoint=endpoint,
            http_status=503,
        )
        self.error_code = "BRIDGE_CONNECTION_ERROR"


class BridgeTimeoutError(BridgeError):
    """Raised when Bridge request times out."""

    def __init__(
        self,
        endpoint: str,
        timeout: Optional[float] = None,
    ):
        super().__init__(
            message=f"Bridge request timed out: {endpoint}",
            endpoint=endpoint,
            http_status=504,
        )
        self.error_code = "BRIDGE_TIMEOUT_ERROR"
        self.details["timeout"] = timeout


class BridgeAuthError(BridgeError):
    """Raised when Bridge authentication fails."""

    def __init__(
        self,
        message: str = "Bridge authentication failed",
    ):
        super().__init__(
            message=message,
            http_status=401,
        )
        self.error_code = "BRIDGE_AUTH_ERROR"


# =============================================================================
# Integration Errors
# =============================================================================

class IntegrationError(OrbitError):
    """Base exception for integration errors."""

    def __init__(
        self,
        message: str,
        integration_name: Optional[str] = None,
        http_status: int = 500,
    ):
        super().__init__(
            message=message,
            error_code="INTEGRATION_ERROR",
            details={"integration_name": integration_name},
            http_status=http_status,
        )


class IntegrationNotFoundError(IntegrationError):
    """Raised when an integration is not found."""

    def __init__(
        self,
        integration_name: str,
    ):
        super().__init__(
            message=f"Integration not found: {integration_name}",
            integration_name=integration_name,
            http_status=404,
        )
        self.error_code = "INTEGRATION_NOT_FOUND"


class IntegrationAuthError(IntegrationError):
    """Raised when integration authentication fails or is missing."""

    def __init__(
        self,
        integration_name: str,
        auth_required: bool = True,
    ):
        super().__init__(
            message=f"Authentication required for integration: {integration_name}",
            integration_name=integration_name,
            http_status=401,
        )
        self.error_code = "INTEGRATION_AUTH_ERROR"
        self.details["auth_required"] = auth_required


class IntegrationConfigError(IntegrationError):
    """Raised when integration configuration is invalid."""

    def __init__(
        self,
        integration_name: str,
        config_issue: str,
    ):
        super().__init__(
            message=f"Invalid configuration for {integration_name}: {config_issue}",
            integration_name=integration_name,
            http_status=500,
        )
        self.error_code = "INTEGRATION_CONFIG_ERROR"


# =============================================================================
# Agent Errors
# =============================================================================

class AgentError(OrbitError):
    """Base exception for agent workflow errors."""

    def __init__(
        self,
        message: str,
        node_name: Optional[str] = None,
        state_key: Optional[str] = None,
        http_status: int = 500,
    ):
        super().__init__(
            message=message,
            error_code="AGENT_ERROR",
            details={"node_name": node_name, "state_key": state_key},
            http_status=http_status,
        )


class AgentStateError(AgentError):
    """Raised when agent state is invalid."""

    def __init__(
        self,
        message: str,
        state_key: str,
        expected_type: Optional[str] = None,
        actual_value: Optional[Any] = None,
    ):
        super().__init__(
            message=message,
            state_key=state_key,
        )
        self.error_code = "AGENT_STATE_ERROR"
        self.details["expected_type"] = expected_type
        self.details["actual_value"] = str(actual_value)[:100] if actual_value else None


class AgentWorkflowError(AgentError):
    """Raised when agent workflow execution fails."""

    def __init__(
        self,
        message: str,
        node_name: str,
        step: Optional[int] = None,
    ):
        super().__init__(
            message=message,
            node_name=node_name,
        )
        self.error_code = "AGENT_WORKFLOW_ERROR"
        self.details["step"] = step


class AgentTimeoutError(AgentError):
    """Raised when agent execution times out."""

    def __init__(
        self,
        message: str = "Agent execution timed out",
        timeout: Optional[float] = None,
    ):
        super().__init__(
            message=message,
        )
        self.error_code = "AGENT_TIMEOUT_ERROR"
        self.details["timeout"] = timeout
        self.http_status = 504
