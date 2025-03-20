import base64
from typing import Dict, List, Optional, Any

from celai_community_tools.auth import Gmail as GmailAuth
from celai_community_tools.errors import AuthorizationError, ToolExecutionError


def _import_httpx() -> Any:
    """Import httpx library."""
    try:
        import httpx
        return httpx
    except ImportError as e:
        raise ImportError(
            "Cannot import httpx, please install with `pip install httpx`."
        ) from e


async def get_gmail_service(context: Any) -> Any:
    """
    Get a configured Gmail API client with the appropriate authorization.
    
    Args:
        context: The function context containing authorization information.
        
    Returns:
        A configured httpx.AsyncClient for making Gmail API requests.
        
    Raises:
        AuthorizationError: If authorization fails.
    """
    httpx = _import_httpx()
    
    if not hasattr(context, "authorization") or not context.authorization or not context.authorization.token:
        raise AuthorizationError("No authorization token provided for Gmail API access")
    
    client = httpx.AsyncClient(
        base_url="https://gmail.googleapis.com/gmail/v1",
        headers={
            "Authorization": f"Bearer {context.authorization.token}",
            "Content-Type": "application/json",
        }
    )
    
    return client


def decode_message_part(part: Dict) -> Dict:
    """
    Decode a message part from Gmail API response.
    
    Args:
        part: The Gmail API message part to decode.
        
    Returns:
        The decoded message part.
    """
    body = part.get("body", {})
    
    if "attachmentId" in body:
        # This is an attachment
        return {
            "mimeType": part.get("mimeType", ""),
            "filename": part.get("filename", ""),
            "attachmentId": body.get("attachmentId", ""),
            "size": body.get("size", 0),
        }
    
    if "data" in body:
        # This is a text part
        data = body.get("data", "")
        if data:
            decoded_data = base64.urlsafe_b64decode(data.encode("UTF-8")).decode("UTF-8")
            return {
                "mimeType": part.get("mimeType", ""),
                "data": decoded_data,
            }
    
    # This part has no content or is a multipart container
    return {
        "mimeType": part.get("mimeType", ""),
        "parts": [decode_message_part(p) for p in part.get("parts", [])],
    }


def parse_gmail_message(message: Dict) -> Dict:
    """
    Parse a Gmail message into a simplified format.
    
    Args:
        message: The Gmail API message to parse.
        
    Returns:
        A simplified message representation.
    """
    headers = message.get("payload", {}).get("headers", [])
    header_dict = {header["name"].lower(): header["value"] for header in headers}
    
    # Process payload parts
    payload = message.get("payload", {})
    parts = payload.get("parts", [])
    
    # If no parts, the payload itself is the content
    if not parts and "body" in payload:
        parts = [payload]
    
    # Decode parts
    decoded_parts = [decode_message_part(part) for part in parts]
    
    # Extract text content from parts
    content = ""
    attachments = []
    
    for part in decoded_parts:
        if part.get("mimeType", "").startswith("text/plain") and "data" in part:
            content += part["data"]
        elif "attachmentId" in part:
            attachments.append({
                "filename": part.get("filename", ""),
                "mimeType": part.get("mimeType", ""),
                "attachmentId": part.get("attachmentId", ""),
                "size": part.get("size", 0),
            })
    
    return {
        "id": message.get("id", ""),
        "threadId": message.get("threadId", ""),
        "labelIds": message.get("labelIds", []),
        "snippet": message.get("snippet", ""),
        "historyId": message.get("historyId", ""),
        "internalDate": message.get("internalDate", ""),
        "from": header_dict.get("from", ""),
        "to": header_dict.get("to", ""),
        "subject": header_dict.get("subject", ""),
        "cc": header_dict.get("cc", ""),
        "bcc": header_dict.get("bcc", ""),
        "date": header_dict.get("date", ""),
        "content": content,
        "attachments": attachments,
    }