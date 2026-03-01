"""
Memory Compaction Module

Handles memory consolidation and archiving to prevent memory bloat.
Compacts episodic memory when it exceeds context window threshold.
"""

import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from src.llm.factory import llm_factory

from .reader import (
    read_memory_file,
    read_recent_sessions,
    read_session,
    read_user_profile,
)
from .writer import (
    archive_session,
    save_workflow,
    update_user_profile,
    write_to_memory,
)
from .structure import (
    ARCHIVE_DIR,
    EPISODIC_DIR,
    MEMORY_ROOT,
    PROCEDURAL_DIR,
    SESSIONS_DIR,
    USER_PROFILE_FILE,
    WORKFLOWS_FILE,
)


# ============================================================================
# Configuration
# ============================================================================

# Default context window sizes for common models (in tokens)
DEFAULT_CONTEXT_WINDOW = 128000  # GPT-4o / Claude 3.5 default
COMPACTON_THRESHOLD_RATIO = 0.8  # Compact at 80% of context window
SAFE_TOKEN_RATIO = 4  # Approximate tokens per character estimate

# Calculated thresholds
COMPACTION_THRESHOLD_CHARS = int(DEFAULT_CONTEXT_WINDOW / SAFE_TOKEN_RATIO * COMPACTON_THRESHOLD_RATIO)


# ============================================================================
# Compaction Detection
# ============================================================================

def get_total_memory_size() -> int:
    """
    Calculate total memory size in characters.

    Returns:
        Total size of all memory files in characters
    """
    total_size = 0

    for directory in [EPISODIC_DIR, PROCEDURAL_DIR]:
        if directory.exists():
            for file_path in directory.rglob("*.md"):
                total_size += file_path.stat().st_size

    return total_size


def check_compaction_needed(
    context_window: int = DEFAULT_CONTEXT_WINDOW,
    threshold_ratio: float = COMPACTON_THRESHOLD_RATIO,
) -> bool:
    """
    Check if memory compaction is needed based on context window usage.

    Args:
        context_window: Model's context window size in tokens
        threshold_ratio: Ratio of context window that triggers compaction

    Returns:
        True if compaction is needed, False otherwise
    """
    # Calculate threshold in characters
    threshold_chars = int(context_window / SAFE_TOKEN_RATIO * threshold_ratio)

    # Get current memory size
    current_size = get_total_memory_size()

    # Check if we've exceeded threshold
    return current_size > threshold_chars


def get_memory_usage_stats(
    context_window: int = DEFAULT_CONTEXT_WINDOW,
) -> Dict[str, any]:
    """
    Get detailed memory usage statistics.

    Args:
        context_window: Model's context window size in tokens

    Returns:
        Dictionary with memory usage statistics
    """
    total_chars = get_total_memory_size()
    estimated_tokens = total_chars / SAFE_TOKEN_RATIO
    usage_ratio = estimated_tokens / context_window
    threshold_chars = int(context_window / SAFE_TOKEN_RATIO * COMPACTON_THRESHOLD_RATIO)

    return {
        "total_chars": total_chars,
        "estimated_tokens": int(estimated_tokens),
        "context_window": context_window,
        "usage_ratio": round(usage_ratio, 3),
        "usage_percent": round(usage_ratio * 100, 1),
        "compaction_needed": check_compaction_needed(context_window),
        "threshold_chars": threshold_chars,
        "threshold_tokens": int(threshold_chars / SAFE_TOKEN_RATIO),
    }


# ============================================================================
# Fact Extraction (LLM-based)
# ============================================================================

async def extract_important_facts(
    session_content: str,
    max_facts: int = 10,
) -> List[str]:
    """
    Extract important facts from a session using LLM.

    Args:
        session_content: The session content to analyze
        max_facts: Maximum number of facts to extract

    Returns:
        List of important facts extracted from the session
    """
    if not session_content or len(session_content) < 100:
        return []

    # Create prompt for fact extraction
    prompt = f"""Extract the {max_facts} most important facts from this session.
Focus on:
1. User preferences
2. Repeated patterns
3. Important decisions
4. Technical details worth remembering

Format each fact on a new line, starting with "- ".

Session content:
{session_content[:3000]}..."""

    try:
        # Use LLM to extract facts
        llm = llm_factory(temperature=0.0)  # Low temperature for deterministic extraction

        response = await llm.ainvoke(prompt)

        # Normalize response if it's a list (Gemini)
        if isinstance(response.content, list):
            text_parts = [part["text"] for part in response.content if "text" in part]
            response_content = "\n".join(text_parts)
        else:
            response_content = response.content

        # Parse facts from response
        facts = []
        for line in response_content.split("\n"):
            line = line.strip()
            if line.startswith("- ") or line.startswith("* "):
                facts.append(line[2:].strip())

        return facts[:max_facts]

    except Exception:
        # Return empty list on error (fail gracefully)
        return []


# ============================================================================
# Session Summarization
# ============================================================================

async def generate_summary(
    session_id: str,
    max_chars: int = 500,
) -> Optional[str]:
    """
    Generate a concise summary of a session using LLM.

    Args:
        session_id: The session ID to summarize
        max_chars: Maximum characters for the summary

    Returns:
        Concise summary of the session, or None if session not found
    """
    session_content = read_session(session_id)
    if not session_content:
        return None

    # Truncate if too long for prompt
    if len(session_content) > 2000:
        session_content = session_content[:2000] + "..."

    prompt = f"""Generate a concise summary (max {max_chars} characters) of this session.
Focus on:
1. What the user asked about
2. What was accomplished
3. Any important decisions or outcomes

Session content:
{session_content}

Summary:"""

    try:
        # Use LLM to generate summary
        llm = llm_factory(temperature=0.3)

        response = await llm.ainvoke(prompt)

        # Normalize response
        if isinstance(response.content, list):
            text_parts = [part["text"] for part in response.content if "text" in part]
            response_content = "\n".join(text_parts)
        else:
            response_content = response.content

        # Ensure max length
        summary = response_content.strip()
        if len(summary) > max_chars:
            summary = summary[:max_chars-3] + "..."

        return summary

    except Exception:
        # Return simple summary on error
        return f"Session {session_id} summary unavailable"


# ============================================================================
# Consolidation to Procedural Memory
# ============================================================================

async def consolidate_to_procedural(
    facts: List[str],
    session_summaries: List[Dict[str, str]],
) -> int:
    """
    Consolidate facts and summaries into procedural memory (workflows).

    Args:
        facts: List of important facts extracted from sessions
        session_summaries: List of dicts with session_id and summary

    Returns:
        Number of workflows consolidated
    """
    consolidated_count = 0

    # 1. Convert facts to preferences in user profile
    preferences = []
    for fact in facts:
        if any(keyword in fact.lower() for keyword in ["prefer", "like", "want", "use", "choose"]):
            preferences.append(fact)

    if preferences:
        update_user_profile(
            {"consolidated_preferences": "\n".join(f"- {p}" for p in preferences)},
            append=True,
        )

    # 2. Create workflows from session patterns
    # Group summaries by common themes
    if len(session_summaries) >= 2:
        # Combine recent summaries for analysis
        combined_content = "\n\n".join(
            f"{s['session_id']}: {s['summary']}" for s in session_summaries
        )

        # Use LLM to detect patterns
        try:
            llm = llm_factory(temperature=0.2)

            prompt = f"""Analyze these session summaries and identify any recurring patterns or workflows.
For each pattern found, provide:
1. A name for the workflow
2. A brief description
3. Key steps (numbered list)

Session summaries:
{combined_content}

If no clear patterns exist, respond with "NO PATTERNS FOUND"."""

            response = await llm.ainvoke(prompt)

            if isinstance(response.content, list):
                text_parts = [part["text"] for part in response.content if "text" in part]
                response_content = "\n".join(text_parts)
            else:
                response_content = response.content

            # Check if patterns were found
            if "NO PATTERNS FOUND" not in response_content.upper():
                # Parse workflow from response
                # This is a simple parser - could be enhanced
                lines = response_content.split("\n")
                current_workflow = {"name": "", "description": "", "steps": []}

                for line in lines:
                    line = line.strip()
                    if not line:
                        continue

                    if line.startswith("Name:") or line.startswith("Workflow:"):
                        if current_workflow["name"]:  # Save previous workflow
                            if current_workflow["steps"]:
                                save_workflow(
                                    current_workflow["name"],
                                    current_workflow["description"],
                                    current_workflow["steps"],
                                )
                                consolidated_count += 1
                        current_workflow = {"name": "", "description": "", "steps": []}
                        current_workflow["name"] = line.split(":", 1)[1].strip()
                    elif line.startswith("Description:"):
                        current_workflow["description"] = line.split(":", 1)[1].strip()
                    elif re.match(r"^\d+\.", line):
                        step = re.sub(r"^\d+\.\s*", "", line)
                        current_workflow["steps"].append(step)

                # Save last workflow
                if current_workflow["name"] and current_workflow["steps"]:
                    save_workflow(
                        current_workflow["name"],
                        current_workflow["description"],
                        current_workflow["steps"],
                    )
                    consolidated_count += 1

        except Exception:
            # Fail gracefully on LLM errors
            pass

    return consolidated_count


# ============================================================================
# Archiving
# ============================================================================

def archive_old_sessions(
    keep_recent: int = 10,
    max_age_days: int = 30,
) -> int:
    """
    Archive old sessions to the archive directory.

    Args:
        keep_recent: Number of most recent sessions to keep active
        max_age_days: Maximum age in days before archiving

    Returns:
        Number of sessions archived
    """
    if not SESSIONS_DIR.exists():
        return 0

    archived_count = 0
    now = datetime.now()

    # Get all sessions with their modification times
    sessions = []
    for session_file in SESSIONS_DIR.glob("*.md"):
        mtime = datetime.fromtimestamp(session_file.stat().st_mtime)
        age_days = (now - mtime).days
        sessions.append((session_file, age_days))

    # Sort by age (oldest first)
    sessions.sort(key=lambda x: x[1], reverse=True)

    # Archive sessions that are either:
    # 1. Older than max_age_days, OR
    # 2. Beyond the keep_recent limit
    for session_file, age_days in sessions:
        should_archive = age_days > max_age_days or archived_count >= len(sessions) - keep_recent

        if should_archive:
            try:
                archive_session(session_file.stem)
                archived_count += 1
            except Exception:
                # Fail gracefully if archive fails
                pass

    return archived_count


# ============================================================================
# Manual Compaction
# ============================================================================

async def manual_compaction(
    context_window: int = DEFAULT_CONTEXT_WINDOW,
    keep_recent: int = 5,
    archive_sessions: bool = True,
) -> Dict[str, any]:
    """
    Perform manual memory compaction on demand.

    This function:
    1. Extracts important facts from recent sessions
    2. Generates summaries of old sessions
    3. Consolidates facts into procedural memory
    4. Archives old sessions

    Args:
        context_window: Model's context window size
        keep_recent: Number of recent sessions to keep active
        archive_sessions: Whether to archive old sessions

    Returns:
        Dictionary with compaction results and statistics
    """
    results = {
        "facts_extracted": 0,
        "workflows_created": 0,
        "sessions_archived": 0,
        "sessions_summarized": 0,
        "memory_before": get_memory_usage_stats(context_window),
        "timestamp": datetime.now().isoformat(),
    }

    # Get recent sessions
    recent_sessions = read_recent_sessions(limit=20)

    if not recent_sessions:
        return results

    # 1. Extract facts from recent sessions
    all_facts = []
    for session in recent_sessions[:keep_recent * 2]:  # Check more for facts
        facts = await extract_important_facts(session["content"])
        all_facts.extend(facts)

    results["facts_extracted"] = len(all_facts)

    # 2. Generate summaries
    session_summaries = []
    for session in recent_sessions[keep_recent:]:  # Summarize older ones
        summary = await generate_summary(session["id"])
        if summary:
            session_summaries.append({
                "session_id": session["id"],
                "summary": summary,
            })
            results["sessions_summarized"] += 1

    # 3. Consolidate to procedural memory
    workflows_created = await consolidate_to_procedural(all_facts, session_summaries)
    results["workflows_created"] = workflows_created

    # 4. Archive old sessions
    if archive_sessions:
        archived = archive_old_sessions(keep_recent=keep_recent)
        results["sessions_archived"] = archived

    # Get memory after compaction
    results["memory_after"] = get_memory_usage_stats(context_window)
    results["memory_reduced_bytes"] = (
        results["memory_before"]["total_chars"] - results["memory_after"]["total_chars"]
    )

    # Write compaction log
    compaction_log = f"""# Memory Compaction Log

**Timestamp:** {results['timestamp']}
**Triggered:** Manual

## Results

- Facts extracted: {results['facts_extracted']}
- Workflows created: {results['workflows_created']}
- Sessions summarized: {results['sessions_summarized']}
- Sessions archived: {results['sessions_archived']}
- Memory reduced: {results['memory_reduced_bytes']:,} characters

## Memory Before

- Total characters: {results['memory_before']['total_chars']:,}
- Usage ratio: {results['memory_before']['usage_percent']}%

## Memory After

- Total characters: {results['memory_after']['total_chars']:,}
- Usage ratio: {results['memory_after']['usage_percent']}%

---

"""
    write_to_memory(
        compaction_log,
        "episodic",
        "compaction-log.md",
        add_timestamp=True,
        mode="a",
    )

    return results


async def auto_compaction(
    context_window: int = DEFAULT_CONTEXT_WINDOW,
    keep_recent: int = 5,
) -> Dict[str, any]:
    """
    Perform automatic memory compaction when threshold is exceeded.

    Similar to manual_compaction but lighter weight for automated triggering.

    Args:
        context_window: Model's context window size
        keep_recent: Number of recent sessions to keep active

    Returns:
        Dictionary with compaction results
    """
    if not check_compaction_needed(context_window):
        return {
            "compaction_performed": False,
            "reason": "Memory below threshold",
            "timestamp": datetime.now().isoformat(),
        }

    # Run compaction
    results = await manual_compaction(
        context_window=context_window,
        keep_recent=keep_recent,
        archive_sessions=True,
    )
    results["compaction_performed"] = True
    results["trigger"] = "auto"

    return results


# ============================================================================
# Utility Functions
# ============================================================================

def get_compaction_status() -> Dict[str, any]:
    """
    Get current memory compaction status.

    Returns:
        Dictionary with memory and compaction status
    """
    return {
        "memory_stats": get_memory_usage_stats(),
        "can_compact": check_compaction_needed(),
        "sessions_count": len(list(SESSIONS_DIR.glob("*.md"))) if SESSIONS_DIR.exists() else 0,
        "archive_count": len(list(ARCHIVE_DIR.glob("*.md"))) if ARCHIVE_DIR.exists() else 0,
        "last_compaction": _get_last_compaction_time(),
    }


def _get_last_compaction_time() -> Optional[str]:
    """
    Get timestamp of last compaction from compaction log.

    Returns:
        ISO timestamp of last compaction, or None if never compacted
    """
    log_file = EPISODIC_DIR / "compaction-log.md"
    if not log_file.exists():
        return None

    content = read_memory_file(log_file)
    if not content:
        return None

    # Find most recent timestamp in log
    timestamps = re.findall(r"\*\*Timestamp:\*\*\s*([^\n]+)", content)
    if timestamps:
        return timestamps[-1].strip()

    return None
