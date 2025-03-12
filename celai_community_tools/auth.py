from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List


@dataclass
class ToolAuthorization(ABC):
    """Base class for tool authorization requirements."""
    
    @abstractmethod
    def validate(self, token: str) -> bool:
        """
        Validate the given token.
        
        Args:
            token: The token to validate.
            
        Returns:
            True if the token is valid, False otherwise.
        """
        pass


@dataclass
class OAuth2(ToolAuthorization):
    """OAuth2 authorization."""
    
    scopes: List[str]
    
    def validate(self, token: str) -> bool:
        # In a real implementation, this would validate the token and its scopes
        return bool(token)


@dataclass
class APIKey(ToolAuthorization):
    """API key authorization."""
    
    def validate(self, token: str) -> bool:
        # In a real implementation, this would validate the API key
        return bool(token)


@dataclass
class BearerToken(ToolAuthorization):
    """Bearer token authorization."""
    
    def validate(self, token: str) -> bool:
        # In a real implementation, this would validate the token
        return bool(token)


class Gmail(OAuth2):
    """Gmail-specific OAuth2 authorization."""
    
    def __init__(self, scopes: List[str] = None):
        default_scopes = [
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/gmail.compose",
            "https://www.googleapis.com/auth/gmail.modify",
        ]
        super().__init__(scopes or default_scopes)


class GitHub(OAuth2):
    """GitHub-specific OAuth2 authorization."""
    
    def __init__(self, scopes: List[str] = None):
        default_scopes = [
            "repo",
            "user",
        ]
        super().__init__(scopes or default_scopes)


class OpenWeatherMap(APIKey):
    """OpenWeatherMap-specific API key authorization."""
    pass