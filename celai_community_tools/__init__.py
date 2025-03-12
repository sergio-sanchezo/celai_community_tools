from celai_community_tools.tool import tool, deprecated
from celai_community_tools.auth import (
    ToolAuthorization,
    OAuth2,
    APIKey,
    BearerToken,
    Gmail,
    GitHub,
    OpenWeatherMap,
)
from celai_community_tools.errors import (
    ToolError,
    ToolExecutionError,
    RetryableToolError,
    AuthorizationError,
)

__version__ = "0.1.0"

__all__ = [
    # Tool decorator
    "tool",
    "deprecated",
    
    # Authentication
    "ToolAuthorization",
    "OAuth2",
    "APIKey",
    "BearerToken",
    "Gmail",
    "GitHub",
    "OpenWeatherMap",
    
    # Errors
    "ToolError",
    "ToolExecutionError",
    "RetryableToolError",
    "AuthorizationError",
]