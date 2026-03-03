"""
Agent Prompts Module

Contains system prompts for various agent components.
"""

from .classifier import classifier_prompt
from .web_search import WEB_SEARCH_SYSTEM_PROMPT, web_search_prompt_template
from .responder import RESPONDER_SYSTEM_PROMPT
from .planner import PLANNER_SYSTEM_PROMPT
from .safety import SAFETY_SYSTEM_PROMPT

__all__ = [
    "classifier_prompt",
    "WEB_SEARCH_SYSTEM_PROMPT",
    "web_search_prompt_template",
    "RESPONDER_SYSTEM_PROMPT",
    "PLANNER_SYSTEM_PROMPT",
    "SAFETY_SYSTEM_PROMPT",
]
