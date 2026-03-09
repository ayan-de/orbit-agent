"""
Integrations package for Orbit AI Agent.

Provides unified MCP tool integration with:
- YAML-based integration definitions
- Intelligent request classification
- Pre-warmed tool registry for performance
- Dynamic tool loading from MCP servers
"""

from src.integrations.config import IntegrationConfig
from src.integrations.registry import (
    IntegrationRegistry,
    get_registry,
    reset_registry,
)
from src.integrations.classifier import (
    IntegrationClassifier,
    ClassificationResult,
    get_classifier,
)

__all__ = [
    "IntegrationConfig",
    "IntegrationRegistry",
    "get_registry",
    "reset_registry",
    "IntegrationClassifier",
    "ClassificationResult",
    "get_classifier",
]
