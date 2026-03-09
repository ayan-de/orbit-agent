"""
Integration configuration models.

Defines the structure for MCP integration configurations.
"""

from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path

import yaml


@dataclass
class IntegrationConfig:
    """Configuration for a single integration (MCP server tools group)."""

    name: str
    tool_names: list[str]
    display_name: str
    icon: str
    requires_auth: bool
    mcp_server: Optional[str]
    request_patterns: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    planner_hints: str = ""
    executor_hints: str = ""

    def matches_pattern(self, text: str) -> bool:
        """Check if text matches any of the request patterns."""
        import re
        text_lower = text.lower()
        for pattern in self.request_patterns:
            try:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    return True
            except re.error:
                # If regex fails, try simple substring match
                if pattern.lower() in text_lower:
                    return True
        return False

    def matches_keywords(self, text: str) -> int:
        """Count keyword matches in text. Returns match count."""
        text_lower = text.lower()
        text_words = set(text_lower.split())
        return sum(1 for kw in self.keywords if kw.lower() in text_words)

    @classmethod
    def from_dict(cls, name: str, data: dict) -> "IntegrationConfig":
        """Create IntegrationConfig from dictionary."""
        return cls(
            name=name,
            tool_names=data.get("tool_names", []),
            display_name=data.get("display_name", name),
            icon=data.get("icon", "default"),
            requires_auth=data.get("requires_auth", False),
            mcp_server=data.get("mcp_server"),
            request_patterns=data.get("request_patterns", []),
            keywords=data.get("keywords", []),
            planner_hints=data.get("planner_hints", ""),
            executor_hints=data.get("executor_hints", ""),
        )


def load_integration_configs(config_path: Optional[Path] = None) -> dict[str, IntegrationConfig]:
    """
    Load integration configurations from YAML file.

    Args:
        config_path: Path to YAML config file. Defaults to integration_config.yaml

    Returns:
        Dictionary mapping integration names to IntegrationConfig
    """
    if config_path is None:
        config_path = Path(__file__).parent / "integration_config.yaml"

    if not config_path.exists():
        return {}

    with open(config_path, "r") as f:
        data = yaml.safe_load(f)

    if not data or "integrations" not in data:
        return {}

    configs = {}
    for name, integration_data in data["integrations"].items():
        configs[name] = IntegrationConfig.from_dict(name, integration_data)

    return configs
