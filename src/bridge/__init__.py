"""
Bridge client module for Orbit Agent.

Contains HTTP client for communicating with NestJS Bridge orchestrator.

NOTE: The class is named OrchestratorClient (not BridgeClient) to avoid
confusion with the DesktopClient in TypeScript. Both connect to the Bridge,
but from different contexts:
- OrchestratorClient: Python Agent → NestJS Bridge (for command execution)
- DesktopClient: Desktop TUI → NestJS Bridge (for WebSocket connection)
"""

from .schemas import BridgeCommandRequest, BridgeCommandResponse
from .orchestrator_client import OrchestratorClient

__all__ = ['OrchestratorClient', 'BridgeCommandRequest', 'BridgeCommandResponse']
