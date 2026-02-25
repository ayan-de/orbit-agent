"""
Email sender node - sends email via Gmail API.
"""
from typing import Dict, Any
from langchain_core.messages import AIMessage

from src.agent.state import AgentState
from src.tools.gmail.send import SendEmailTool


async def send_email(state: AgentState) -> Dict[str, Any]:
    """
    Send the drafted email via Gmail API.

    Args:
        state: Current agent state

    Returns:
        State updates with send result
    """
    user_id = state.get("user_id", "")
    to_email = state.get("email_to")
    subject = state.get("email_subject")
    body = state.get("email_body")
    cc_emails = state.get("email_cc")
    attachments = state.get("email_attachments")

    # Validate required fields
    if not to_email or not body:
        return {
            "messages": [AIMessage(content="Cannot send email: missing recipient or body.")],
            "email_needs_confirmation": False
        }

    # Create Gmail tool instance
    gmail_tool = SendEmailTool()

    try:
        # Send email
        result = await gmail_tool._arun(
            user_id=user_id,
            to_email=to_email,
            subject=subject,
            body=body,
            cc_emails=cc_emails,
            attachments=attachments
        )

        # Log to file (optional - for history)
        _log_sent_email(user_id, to_email, subject, body)

        return {
            "messages": [AIMessage(content=f"✓ {result}")],
            "email_needs_confirmation": False,
            "email_sent_message_id": result.split("Message ID: ")[1] if "Message ID: " in result else None
        }

    except Exception as e:
        error_msg = f"Failed to send email: {str(e)}"
        return {
            "messages": [AIMessage(content=error_msg)],
            "email_needs_confirmation": False
        }


def _log_sent_email(user_id: str, to_email: str, subject: str, body: str) -> None:
    """
    Log sent email to file for history (optional).

    Args:
        user_id: User ID
        to_email: Recipient email
        subject: Email subject
        body: Email body
    """
    try:
        import json
        from datetime import datetime
        from pathlib import Path

        # Create data directory if needed
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)

        # Log entry
        log_entry = {
            "user_id": user_id,
            "to_email": to_email,
            "subject": subject,
            "body": body,
            "sent_at": datetime.now().isoformat()
        }

        # Append to log file
        log_file = data_dir / "sent_emails.log"
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

    except Exception as e:
        # Logging failure shouldn't block email sending
        print(f"Warning: Failed to log sent email: {e}")
