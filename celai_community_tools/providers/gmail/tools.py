import base64
import email.mime.text
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List, Optional

from cel.assistants.function_context import FunctionContext
from celai_community_tools.auth import Gmail
from celai_community_tools.errors import RetryableToolError, ToolExecutionError
from celai_community_tools.providers.gmail.auth import (
    get_gmail_service,
    parse_gmail_message,
)
from celai_community_tools.tool import tool


@tool(
    name="ListGmailMessages",
    desc="List recent Gmail messages from a user's inbox",
    requires_auth=Gmail(),
)
async def list_messages(
    context: FunctionContext,
    max_results: int = 10,
    label_ids: List[str] = None,
    include_spam_trash: bool = False,
) -> str:
    """
    List recent Gmail messages from the user's mailbox.
    
    Args:
        context: The function context containing authorization.
        max_results: Maximum number of messages to return (default: 10).
        label_ids: Only return messages with these labels (default: None).
        include_spam_trash: Include messages from SPAM and TRASH (default: False).
        
    Returns:
        A JSON string containing the list of messages.
    """
    client = await get_gmail_service(context)
    
    params = {
        "maxResults": max_results,
        "includeSpamTrash": include_spam_trash,
    }
    
    if label_ids:
        params["labelIds"] = label_ids
    
    try:
        response = await client.get("users/me/messages", params=params)
        response.raise_for_status()
        data = response.json()
        
        messages = []
        for msg in data.get("messages", []):
            msg_response = await client.get(f"users/me/messages/{msg['id']}")
            msg_response.raise_for_status()
            msg_data = msg_response.json()
            
            messages.append(parse_gmail_message(msg_data))
        
        return json.dumps(messages)
    
    except Exception as e:
        raise ToolExecutionError(
            message=f"Failed to list Gmail messages: {str(e)}",
            developer_message=f"Gmail API error: {str(e)}",
        )
    finally:
        await client.aclose()


@tool(
    name="GetGmailMessage",
    desc="Get a specific Gmail message by ID",
    requires_auth=Gmail(),
)
async def get_message(
    context: FunctionContext,
    message_id: str,
) -> str:
    """
    Get a specific Gmail message by its ID.
    
    Args:
        context: The function context containing authorization.
        message_id: The ID of the message to retrieve.
        
    Returns:
        A JSON string containing the message details.
    """
    client = await get_gmail_service(context)
    
    try:
        response = await client.get(f"users/me/messages/{message_id}")
        response.raise_for_status()
        data = response.json()
        
        parsed_message = parse_gmail_message(data)
        return json.dumps(parsed_message)
    
    except Exception as e:
        raise ToolExecutionError(
            message=f"Failed to get Gmail message: {str(e)}",
            developer_message=f"Gmail API error: {str(e)}",
        )
    finally:
        await client.aclose()


@tool(
    name="SearchGmailMessages",
    desc="Search for Gmail messages using Gmail search syntax",
    requires_auth=Gmail(),
)
async def search_messages(
    context: FunctionContext,
    query: str,
    max_results: int = 10,
    include_spam_trash: bool = False,
) -> str:
    """
    Search for Gmail messages using Gmail search syntax.
    
    Args:
        context: The function context containing authorization.
        query: Gmail search query (e.g., "from:example@gmail.com after:2023/01/01").
        max_results: Maximum number of messages to return (default: 10).
        include_spam_trash: Include messages from SPAM and TRASH (default: False).
        
    Returns:
        A JSON string containing the list of matching messages.
    """
    client = await get_gmail_service(context)
    
    params = {
        "q": query,
        "maxResults": max_results,
        "includeSpamTrash": include_spam_trash,
    }
    
    try:
        response = await client.get("users/me/messages", params=params)
        response.raise_for_status()
        data = response.json()
        
        if "messages" not in data:
            return json.dumps({"messages": []})
        
        messages = []
        for msg in data.get("messages", []):
            msg_response = await client.get(f"users/me/messages/{msg['id']}")
            msg_response.raise_for_status()
            msg_data = msg_response.json()
            
            messages.append(parse_gmail_message(msg_data))
        
        return json.dumps({"messages": messages})
    
    except Exception as e:
        raise ToolExecutionError(
            message=f"Failed to search Gmail messages: {str(e)}",
            developer_message=f"Gmail API error: {str(e)}",
        )
    finally:
        await client.aclose()


@tool(
    name="SendGmailMessage",
    desc="Send a new email message via Gmail",
    requires_auth=Gmail(),
)
async def send_message(
    context: FunctionContext,
    to: str,
    subject: str,
    body: str,
    cc: str = None,
    bcc: str = None,
    html_body: str = None,
) -> str:
    """
    Send a new email message via Gmail.
    
    Args:
        context: The function context containing authorization.
        to: Recipient email address or addresses (comma-separated).
        subject: Email subject.
        body: Plain text email body.
        cc: Carbon copy recipient(s) (comma-separated).
        bcc: Blind carbon copy recipient(s) (comma-separated).
        html_body: HTML email body (optional).
        
    Returns:
        A JSON string containing the message ID and thread ID.
    """
    client = await get_gmail_service(context)
    
    # Create message
    message = MIMEMultipart("alternative")
    message["To"] = to
    message["Subject"] = subject
    
    if cc:
        message["Cc"] = cc
    if bcc:
        message["Bcc"] = bcc
    
    # Attach plain text part
    plain_part = MIMEText(body, "plain")
    message.attach(plain_part)
    
    # Attach HTML part if provided
    if html_body:
        html_part = MIMEText(html_body, "html")
        message.attach(html_part)
    
    # Encode message
    encoded_message = base64.urlsafe_b64encode(message.as_string().encode()).decode()
    
    # Prepare API request
    request_body = {
        "raw": encoded_message,
    }
    
    try:
        response = await client.post("users/me/messages/send", json=request_body)
        response.raise_for_status()
        data = response.json()
        
        return json.dumps({
            "id": data.get("id", ""),
            "threadId": data.get("threadId", ""),
            "labelIds": data.get("labelIds", []),
        })
    
    except Exception as e:
        raise ToolExecutionError(
            message=f"Failed to send Gmail message: {str(e)}",
            developer_message=f"Gmail API error: {str(e)}",
        )
    finally:
        await client.aclose()


@tool(
    name="CreateGmailDraft",
    desc="Create a draft email message in Gmail",
    requires_auth=Gmail(),
)
async def create_draft(
    context: FunctionContext,
    to: str,
    subject: str,
    body: str,
    cc: str = None,
    bcc: str = None,
    html_body: str = None,
) -> str:
    """
    Create a draft email message in Gmail.
    
    Args:
        context: The function context containing authorization.
        to: Recipient email address or addresses (comma-separated).
        subject: Email subject.
        body: Plain text email body.
        cc: Carbon copy recipient(s) (comma-separated).
        bcc: Blind carbon copy recipient(s) (comma-separated).
        html_body: HTML email body (optional).
        
    Returns:
        A JSON string containing the draft message ID and thread ID.
    """
    client = await get_gmail_service(context)
    
    # Create message
    message = MIMEMultipart("alternative")
    message["To"] = to
    message["Subject"] = subject
    
    if cc:
        message["Cc"] = cc
    if bcc:
        message["Bcc"] = bcc
    
    # Attach plain text part
    plain_part = MIMEText(body, "plain")
    message.attach(plain_part)
    
    # Attach HTML part if provided
    if html_body:
        html_part = MIMEText(html_body, "html")
        message.attach(html_part)
    
    # Encode message
    encoded_message = base64.urlsafe_b64encode(message.as_string().encode()).decode()
    
    # Prepare API request
    request_body = {
        "message": {
            "raw": encoded_message,
        }
    }
    
    try:
        response = await client.post("users/me/drafts", json=request_body)
        response.raise_for_status()
        data = response.json()
        
        return json.dumps({
            "id": data.get("id", ""),
            "message": {
                "id": data.get("message", {}).get("id", ""),
                "threadId": data.get("message", {}).get("threadId", ""),
                "labelIds": data.get("message", {}).get("labelIds", []),
            }
        })
    
    except Exception as e:
        raise ToolExecutionError(
            message=f"Failed to create Gmail draft: {str(e)}",
            developer_message=f"Gmail API error: {str(e)}",
        )
    finally:
        await client.aclose()