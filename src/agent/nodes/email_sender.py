"""
Email sender node - sends email via Google Workspace MCP server.
"""
from typing import Dict, Any
from langchain_core.messages import AIMessage

from src.agent.state import AgentState


async def send_email(state: AgentState) -> Dict[str, Any]:
    """
    Send a drafted email via Google Workspace MCP server.

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

    try:
        # Import MCP client
        from src.mcp.client import get_mcp_client

        # Get MCP client manager
        mcp_client = get_mcp_client()

        # Ensure Google Workspace MCP server is connected
        if not mcp_client.is_server_connected("google_workspace"):
            await mcp_client.connect_server("google_workspace")

        # Prepare email parameters
        email_params = {
            "to": to_email,
            "subject": subject,
            "body": body,
        }

        # Add optional parameters
        if cc_emails:
            email_params["cc"] = cc_emails
        if attachments:
            email_params["attachments"] = attachments

        # Send email via MCP
        result = await mcp_client.execute_tool(
            server_name="google_workspace",
            tool_name="send_gmail_message",
            **email_params
        )

        # Log to file (optional - for history)
        _log_sent_email(user_id, to_email, subject, body)

        if result.get("success"):
            # Extract message ID from result if available
            message_id = None
            if "data" in result and isinstance(result["data"], dict):
                message_id = result["data"].get("message_id")

            success_msg = f"✓ Email sent successfully"
            if message_id:
                success_msg += f" (Message ID: {message_id})"

            return {
                "messages": [AIMessage(content=success_msg)],
                "email_needs_confirmation": False,
                "email_sent_message_id": message_id
            }
        else:
            error_msg = result.get("data", {}).get("error", "Failed to send email")
            return {
                "messages": [AIMessage(content=f"✗ {error_msg}")],
                "email_needs_confirmation": False
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
