"""
Bridge client module for Orbit Agent.

Contains HTTP client for communicating with NestJS Bridge orchestrator.
"""

from .schemas import BridgeCommandRequest, BridgeCommandResponse
from .orchestrator_client import BridgeClient

__all__ = ['BridgeClient', 'BridgeCommandRequest', 'BridgeCommandResponse']
