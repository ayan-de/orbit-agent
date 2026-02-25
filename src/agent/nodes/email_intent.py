"""
Email intent node - extracts email components from user request.
"""
import re
from typing import Dict, Any, Optional, List
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import JsonOutputParser

from src.agent.state import AgentState
from src.llm.factory import llm_factory


EMAIL_INTENT_PROMPT = """You are an email extraction assistant. Your job is to extract email components from the user's request.

Analyze the user's request and extract the following information:
- to_email: Recipient email address
- subject: Email subject (if provided or infer from content)
- body: Email body content (main message)
- cc_emails: List of CC recipients (if mentioned)
- is_email_request: true if this is an email sending request, false otherwise

If the user mentions needing to fetch data (e.g., "fetch jira tickets", "search web"), set needs_content_generation to true and note the source.

Return a JSON object with these fields.

Examples:

User: "email 'Happy birthday' to sakil@gmail.com"
Output: {{"to_email": "sakil@gmail.com", "subject": "Happy Birthday", "body": "Happy birthday!", "is_email_request": true}}

User: "fetch my jira tickets, summarize them, and email the summary to manager@gmail.com"
Output: {{"to_email": "manager@gmail.com", "subject": "Jira Tickets Summary", "body": "[Content from jira]", "is_email_request": true, "needs_content_generation": true, "content_source": "jira"}}

User: "list top 10 cars and mail it to sakil@gmail.com"
Output: {{"to_email": "sakil@gmail.com", "subject": "Top 10 Cars", "body": "[List of cars]", "is_email_request": true, "needs_content_generation": true, "content_source": "web_search"}}

User: "how does the ls command work?"
Output: {{"is_email_request": false}}

Return ONLY valid JSON, nothing else.
"""


async def classify_email_intent(state: AgentState) -> Dict[str, Any]:
    """
    Classify if the request is email-related and extract components.

    Args:
        state: Current agent state

    Returns:
        State updates with email fields
    """
    messages = state["messages"]
    if not messages:
        return {"email_to": None, "email_subject": None, "email_body": None}

    last_message = messages[-1]
    if isinstance(last_message, HumanMessage):
        user_input = last_message.content
    else:
        user_input = last_message.content

    # Use LLM to extract email components
    llm = llm_factory(temperature=0)

    from langchain_core.prompts import ChatPromptTemplate
    prompt = ChatPromptTemplate.from_messages([
        ("system", EMAIL_INTENT_PROMPT),
        ("user", "{input}")
    ])

    chain = prompt | llm | JsonOutputParser()

    try:
        result = await chain.ainvoke({"input": user_input})

        is_email_request = result.get("is_email_request", False)

        if not is_email_request:
            return {
                "email_to": None,
                "email_subject": None,
                "email_body": None
            }

        # Extract and validate email components
        to_email = result.get("to_email")
        subject = result.get("subject", "No Subject")
        body = result.get("body", user_input)
        cc_emails = result.get("cc_emails", [])
        needs_content_generation = result.get("needs_content_generation", False)
        content_source = result.get("content_source")

        return {
            "email_to": to_email,
            "email_subject": subject,
            "email_body": body,
            "email_cc": cc_emails if cc_emails else None,
            "email_attachments": None,
            "email_needs_confirmation": True,
            "email_refinement_iteration": 0,
            "needs_content_generation": needs_content_generation,
            "content_source": content_source
        }

    except Exception as e:
        # Fallback: simple regex extraction
        return _extract_email_fallback(user_input)


def _extract_email_fallback(user_input: str) -> Dict[str, Any]:
    """
    Fallback email extraction using regex.

    Args:
        user_input: User message

    Returns:
        Extracted email fields
    """
    # Extract email addresses
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, user_input)

    if not emails:
        return {
            "email_to": None,
            "email_subject": None,
            "email_body": None
        }

    to_email = emails[0]

    # Extract content in quotes (message body)
    quote_pattern = r'["\']([^"\']+)["\']'
    quotes = re.findall(quote_pattern, user_input)

    body = quotes[0] if quotes else user_input

    # Generate subject from body or input
    words = body.split()[:5]
    subject = " ".join(words)
    if len(subject) < len(body):
        subject += "..."

    return {
        "email_to": to_email,
        "email_subject": subject,
        "email_body": body,
        "email_cc": None,
        "email_attachments": None,
        "email_needs_confirmation": True,
        "email_refinement_iteration": 0
    }
