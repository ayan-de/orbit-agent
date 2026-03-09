"""
Integration classifier for intelligent request routing.

Classifies which integrations are needed based on user request,
using regex patterns first with LLM fallback.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from langchain_core.messages import HumanMessage

from src.config import settings
from src.integrations.config import IntegrationConfig, load_integration_configs
from src.llm.gemini import get_gemini_model

logger = logging.getLogger(__name__)


class ClassificationMethod(str, Enum):
    """Method used for classification."""
    REGEX = "regex"
    LLM = "llm"
    FALLBACK = "fallback"


@dataclass
class IntegrationIndex:
    """Metadata index for an integration used in classification."""
    name: str
    display_name: str
    description: str
    identity_keywords: list[str] = field(default_factory=list)
    request_patterns: list[str] = field(default_factory=list)


@dataclass
class ClassificationResult:
    """Result of classification with confidence score."""
    integrations: list[str] = field(default_factory=list)
    scores: dict[str, float] = field(default_factory=dict)
    method: str = field(default="llm")
    confidence: float = 0.0


class IntegrationClassifier:
    """
    Classifies which integrations are needed for a user request.

    Uses a tiered approach:
    1. Regex pattern matching (fast)
    2. LLM classification (Gemini Flash - fast and cheap)
    3. Fallback to web_search
    """

    def __init__(self, config_path: Optional[str] = None):
        self._configs: dict[str, IntegrationConfig] = {}
        self._indexes: dict[str, IntegrationIndex] = {}
        self._llm = None
        self._initialized = False

        if config_path:
            self.load_configs(config_path)

    def load_configs(self, config_path: Optional[str] = None) -> None:
        """Load integration configurations and build index."""
        from pathlib import Path
        path = Path(config_path) if config_path else None
        self._configs = load_integration_configs(path)
        self._build_indexes()
        self._initialized = True
        logger.info(f"Loaded {len(self._configs)} integration configs")

    def _build_indexes(self) -> None:
        """Build search indexes from configs for fast classification."""
        for name, config in self._configs.items():
            self._indexes[name] = IntegrationIndex(
                name=name,
                display_name=config.display_name,
                description=f"{config.display_name} integration with tools: {', '.join(config.tool_names[:3])}",
                identity_keywords=config.keywords.copy(),
                request_patterns=config.request_patterns.copy(),
            )

    def _get_llm(self):
        """Get LLM instance lazily (Gemini Flash for speed and cost)."""
        if self._llm is None:
            self._llm = get_gemini_model(model_name="gemini-2.5-flash", temperature=0)
        return self._llm

    async def classify(self, request: str) -> ClassificationResult:
        """
        Classify which integrations are needed for a request.

        Args:
            request: User request string

        Returns:
            ClassificationResult with integrations list and confidence
        """
        if not self._initialized:
            self.load_configs()

        # Phase 1: Try regex patterns first (fast)
        regex_result = self._regex_classify(request)
        if regex_result and regex_result.confidence >= 0.8:
            logger.info(f"Regex classification: {regex_result.integrations} (confidence: {regex_result.confidence})")
            return regex_result

        # Phase 2: LLM classification for ambiguous cases
        llm_result = await self._llm_classify(request)
        if llm_result:
            logger.info(f"LLM classification: {llm_result.integrations} (confidence: {llm_result.confidence})")
            return llm_result

        # Phase 3: Fallback to web_search
        logger.info("Using fallback classification: web_search")
        return ClassificationResult(
            integrations=["web_search"],
            method=ClassificationMethod.FALLBACK.value,
            confidence=0.1,
        )

    def _regex_classify(self, request: str) -> Optional[ClassificationResult]:
        """
        Try fast regex-based classification.

        Returns None if no clear match found.
        """
        request_lower = request.lower()
        matches: dict[str, float] = {}

        for name, config in self._configs.items():
            score = 0.0

            # Check regex patterns
            for pattern in config.request_patterns:
                try:
                    if re.search(pattern, request_lower, re.IGNORECASE):
                        score += 0.5
                except re.error as e:
                    logger.warning(f"Invalid regex pattern '{pattern}': {e}")

            # Check keywords
            keyword_matches = sum(
                1 for kw in config.keywords
                if kw.lower() in request_lower
            )
            score += min(keyword_matches * 0.2, 0.5)

            if score > 0:
                matches[name] = min(score, 1.0)

        if not matches:
            return None

        # Sort by score and take top matches
        sorted_matches = sorted(matches.items(), key=lambda x: x[1], reverse=True)
        top_integrations = [name for name, score in sorted_matches[:3]]
        top_score = sorted_matches[0][1] if sorted_matches else 0.0

        return ClassificationResult(
            integrations=top_integrations,
            scores=dict(sorted_matches),
            method=ClassificationMethod.REGEX.value,
            confidence=top_score,
        )

    async def _llm_classify(self, request: str) -> Optional[ClassificationResult]:
        """
        Use LLM for classification when regex is uncertain.

        Uses Gemini Flash for fast, cheap classification.
        """
        try:
            llm = self._get_llm()

            # Build integration descriptions for prompt
            integration_list = []
            for name, config in self._configs.items():
                integration_list.append(
                    f"- {name}: {config.display_name} (keywords: {', '.join(config.keywords[:5])})"
                )

            prompt = f"""You are a request classifier. Analyze the user request and determine which integrations are needed.

Available integrations:
{chr(10).join(integration_list)}

User request: "{request}"

Respond with ONLY a JSON object (no markdown, no explanation):
{{
  "integrations": ["integration_name1", "integration_name2"],
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation"
}}

Rules:
- Include only integrations that are clearly needed
- If uncertain, include fewer integrations with lower confidence
- Always include at least one integration
- Use exact integration names from the list above"""

            response = await llm.ainvoke([HumanMessage(content=prompt)])
            content = response.content.strip()

            # Parse JSON response
            # Handle potential markdown code blocks
            if "```" in content:
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]

            result = json.loads(content)

            # Validate integrations exist
            valid_integrations = [
                name for name in result.get("integrations", [])
                if name in self._configs
            ]

            if not valid_integrations:
                valid_integrations = ["web_search"]

            return ClassificationResult(
                integrations=valid_integrations,
                method=ClassificationMethod.LLM.value,
                confidence=result.get("confidence", 0.5),
            )

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM classification response: {e}")
            return None
        except Exception as e:
            logger.error(f"LLM classification failed: {e}")
            return None

    def get_config(self, integration_name: str) -> Optional[IntegrationConfig]:
        """Get integration config by name."""
        return self._configs.get(integration_name)

    def get_all_configs(self) -> dict[str, IntegrationConfig]:
        """Get all loaded integration configs."""
        return self._configs.copy()


# Singleton instance
_classifier_instance: Optional[IntegrationClassifier] = None


def get_classifier(config_path: Optional[str] = None) -> IntegrationClassifier:
    """
    Get or create the global classifier instance.

    Args:
        config_path: Optional path to config file (only used on first call)

    Returns:
        IntegrationClassifier singleton
    """
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = IntegrationClassifier(config_path)
    return _classifier_instance


def reset_classifier() -> None:
    """Reset the classifier singleton (useful for testing)."""
    global _classifier_instance
    _classifier_instance = None
