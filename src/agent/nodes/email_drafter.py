"""
Email drafter node - creates and refines email drafts.
"""
import json
from typing import Dict, Any, Optional
from datetime import datetime

from src.agent.state import AgentState
from src.llm.factory import llm_factory
from src.storage.token_store import get_token_store


EMAIL_DRAFTER_PROMPT = """You are an email drafter. Your job is to create or refine an email draft based on the user's request.

Context:
- User ID: {user_id}
- Recipient: {to_email}
- Subject: {subject}
- Current Body: {current_body}
- User Request: {user_request}
- Iteration: {iteration}

If the user is asking to modify the email (iteration > 0), apply their changes to the existing draft.
If this is a new draft (iteration 0), create the email body based on their request.

IMPORTANT Guidelines:
1. If the user provides a short, simple message (e.g. "hi", "hello world", "thanks for the meeting"), use their exact words as the email body. Do NOT add greetings, closings, filler text, or formatting they didn't ask for.
2. Only add professional formatting (greetings, closings, structure) if the user explicitly asks for a formal/professional email OR if the content is clearly meant to be a longer, structured email (e.g. "write a formal email about the project update").
3. Preserve the user's tone and intent exactly.
4. If content needs to be generated from a source (Jira, web search, etc.), include a placeholder.

Return the updated email body only, nothing else.
"""


async def draft_email(state: AgentState) -> Dict[str, Any]:
    """
    Draft or refine an email based on user request.

    Args:
        state: Current agent state

    Returns:
        State updates with drafted email
    """
    user_id = state.get("user_id", "")
    to_email = state.get("email_to")
    subject = state.get("email_subject")
    current_body = state.get("email_body", "")
    iteration = state.get("email_refinement_iteration", 0)

    # Get user's latest message
    messages = state["messages"]
    user_request = messages[-1].content if messages else ""

    # Check if email address is provided
    if not to_email:
        from langchain_core.messages import AIMessage
        return {
            "messages": [AIMessage(content="I need a recipient email address to send an email. Please provide the recipient's email address.")],
            "email_needs_confirmation": False
        }

    # Get user email for "from" field
    token_store = get_token_store()
    connection = token_store.get_connection_status(user_id)

    print(f"DEBUG email_drafter: user_id={repr(user_id)}, connection={connection}, all_keys={list(token_store._tokens.keys())}")

    if not connection["is_connected"]:
        from langchain_core.messages import AIMessage
        return {
            "messages": [AIMessage(content="Please connect your Gmail account first. Use the 'Connect Gmail' option in your profile.")],
            "email_needs_confirmation": False
        }

    from_email = connection["email_address"]

    # Generate/refine email body
    if iteration == 0:
        # First draft - use user's exact text as-is
        body = current_body
    else:
        # Refinement - apply user changes via LLM
        llm = llm_factory(temperature=0.3)
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser

        prompt = ChatPromptTemplate.from_messages([
            ("system", EMAIL_DRAFTER_PROMPT),
            ("user", "{user_request}")
        ])

        chain = prompt | llm | StrOutputParser()

        body = await chain.ainvoke({
            "user_id": user_id,
            "to_email": to_email,
            "subject": subject,
            "current_body": current_body,
            "user_request": user_request,
            "iteration": iteration
        })

    # Create preview message
    preview = _format_email_preview(
        from_email=from_email,
        to_email=to_email,
        subject=subject,
        body=body,
        cc=state.get("email_cc"),
        iteration=iteration
    )

    return {
        "email_body": body,
        "email_confirmation_prompt": preview
    }


def _format_email_preview(
    from_email: str,
    to_email: str,
    subject: str,
    body: str,
    cc: Optional[list] = None,
    iteration: int = 0
) -> str:
    """
    Format email preview for user.

    Args:
        from_email: Sender email
        to_email: Recipient email
        subject: Email subject
        body: Email body
        cc: CC recipients
        iteration: Draft iteration number

    Returns:
        Formatted preview string
    """
    preview = "📧 Email Preview\n"
    preview += "═" * 50 + "\n\n"
    preview += f"From: {from_email}\n"
    preview += f"To: {to_email}\n"
    if cc:
        preview += f"CC: {', '.join(cc)}\n"
    preview += f"Subject: {subject}\n\n"
    preview += "─" * 50 + "\n\n"
    preview += body + "\n\n"
    preview += "═" * 50 + "\n\n"
    preview += "Reply:\n"
    if iteration == 0:
        preview += "  • 'yes' to send this email\n"
        preview += "  • Provide changes to modify the email\n"
        preview += "  • 'cancel' to abort\n"
    else:
        preview += f"  • 'yes' to send this email (refinement #{iteration})\n"
        preview += "  • Provide more changes to modify further\n"
        preview += "  • 'cancel' to abort\n"

    return preview
