"""
Gmail send email tool.
"""
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import Optional, List

from pydantic import BaseModel, Field

from src.tools.base import OrbitTool, ToolCategory, ToolInput
from src.storage.token_store import get_token_store
from src.config import settings


class SendEmailInput(ToolInput):
    """Input schema for sending email."""

    user_id: str = Field(..., description="User ID for authentication")
    to_email: str = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body (plain text)")
    cc_emails: Optional[List[str]] = Field(
        default=None,
        description="CC recipients (optional)"
    )
    attachments: Optional[List[dict]] = Field(
        default=None,
        description="List of attachments with 'filename', 'content' (base64), and 'mimetype'"
    )


class SendEmailTool(OrbitTool):
    """
    Send email via Gmail API.

    Uses stored OAuth tokens to authenticate and send emails.
    Supports CC recipients and file attachments.
    """

    name: str = "gmail_send"
    description: str = "Send an email via Gmail API using OAuth authentication. Supports CC recipients and file attachments."
    category: ToolCategory = ToolCategory.INTEGRATION
    danger_level: int = 3  # Moderate danger (sends email externally)
    requires_confirmation: bool = True  # Always require confirmation
    args_schema: type = SendEmailInput

    # In-memory rate limit tracker: {user_id: [timestamp, ...]}
    _rate_tracker: dict = {}

    def _check_rate_limit(self, user_id: str) -> None:
        """Check if user has exceeded the email rate limit."""
        from datetime import datetime, timedelta

        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)

        # Get user's send timestamps and filter to last hour
        if user_id not in self._rate_tracker:
            self._rate_tracker[user_id] = []

        self._rate_tracker[user_id] = [
            ts for ts in self._rate_tracker[user_id] if ts > one_hour_ago
        ]

        if len(self._rate_tracker[user_id]) >= settings.EMAIL_RATE_LIMIT:
            raise Exception(
                f"Rate limit exceeded. Maximum {settings.EMAIL_RATE_LIMIT} emails per hour. "
                f"Please wait before sending more."
            )

    def _record_send(self, user_id: str) -> None:
        """Record a successful send for rate tracking."""
        from datetime import datetime
        if user_id not in self._rate_tracker:
            self._rate_tracker[user_id] = []
        self._rate_tracker[user_id].append(datetime.now())

    async def _arun(
        self,
        user_id: str,
        to_email: str,
        subject: str,
        body: str,
        cc_emails: Optional[List[str]] = None,
        attachments: Optional[List[dict]] = None
    ) -> str:
        """
        Send email via Gmail API.

        Args:
            user_id: User ID for authentication
            to_email: Recipient email address
            subject: Email subject
            body: Email body
            cc_emails: Optional CC recipients
            attachments: Optional attachments

        Returns:
            Success message with Gmail message ID
        """
        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build

            # Check rate limit before proceeding
            self._check_rate_limit(user_id)

            # Get tokens from storage
            token_store = get_token_store()
            tokens = token_store.get_tokens(user_id)

            if not tokens:
                raise Exception(
                    "No Gmail connection found. Please connect your Gmail account first."
                )

            # Check if token needs refresh
            from datetime import datetime
            from datetime import timedelta

            now = datetime.now()
            expires_at = tokens["token_expires_at"]

            if expires_at <= now + timedelta(minutes=5):
                # Token needs refresh - attempt automatic refresh
                try:
                    from google.auth.transport.requests import Request

                    credentials = Credentials(
                        token=None,
                        refresh_token=tokens["refresh_token"],
                        token_uri="https://oauth2.googleapis.com/token",
                        client_id=settings.GMAIL_CLIENT_ID,
                        client_secret=settings.GMAIL_CLIENT_SECRET,
                        scopes=settings.GMAIL_SCOPES,
                    )
                    credentials.refresh(Request())

                    # Update token store with new access token
                    new_expires_at = credentials.expiry or (now + timedelta(hours=1))
                    token_store.update_access_token(
                        user_id=user_id,
                        access_token=credentials.token,
                        expires_at=new_expires_at,
                    )

                    # Use refreshed token
                    tokens["access_token"] = credentials.token
                except Exception as refresh_error:
                    raise Exception(
                        f"Gmail access token expired and refresh failed: {str(refresh_error)}. "
                        "Please reconnect your Gmail account."
                    )

            # Create credentials
            credentials = Credentials(
                token=tokens["access_token"],
                refresh_token=tokens["refresh_token"],
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.GMAIL_CLIENT_ID,
                client_secret=settings.GMAIL_CLIENT_SECRET,
                scopes=settings.GMAIL_SCOPES
            )

            # Build Gmail service
            service = build("gmail", "v1", credentials=credentials)

            # Create message
            message = self._create_message(
                from_email=tokens["email_address"],
                to_email=to_email,
                cc_emails=cc_emails,
                subject=subject,
                body=body,
                attachments=attachments
            )

            # Send message
            result = (
                service.users()
                .messages()
                .send(userId="me", body={"raw": base64.urlsafe_b64encode(message.as_bytes()).decode()})
                .execute()
            )

            # Record successful send for rate limiting
            self._record_send(user_id)

            return f"Email sent successfully! Message ID: {result.get('id')}"

        except Exception as e:
            raise Exception(f"Failed to send email: {str(e)}")

    def _create_message(
        self,
        from_email: str,
        to_email: str,
        subject: str,
        body: str,
        cc_emails: Optional[List[str]] = None,
        attachments: Optional[List[dict]] = None
    ) -> MIMEMultipart:
        """
        Create MIME message.

        Args:
            from_email: Sender email address
            to_email: Recipient email address
            subject: Email subject
            body: Email body
            cc_emails: CC recipients
            attachments: File attachments

        Returns:
            MIME message object
        """
        # Create multipart message
        message = MIMEMultipart()
        message["to"] = to_email
        message["from"] = from_email
        message["subject"] = subject

        if cc_emails:
            message["cc"] = ", ".join(cc_emails)

        # Attach body
        message.attach(MIMEText(body, "plain"))

        # Attach files if provided
        if attachments:
            for attachment in attachments:
                filename = attachment.get("filename", "attachment")
                content = attachment.get("content")
                mimetype = attachment.get("mimetype", "application/octet-stream")

                if content:
                    # Decode base64 content
                    file_data = base64.b64decode(content)

                    part = MIMEApplication(file_data, Name=filename)
                    part["Content-Disposition"] = f'attachment; filename="{filename}"'
                    message.attach(part)

        return message
