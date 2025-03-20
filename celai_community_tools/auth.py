from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Union
import os


@dataclass
class ToolAuthorization(ABC):
    """Base class for tool authorization requirements."""
    @abstractmethod
    def validate(self) -> bool:
        """Validate the authorization credentials."""
        pass


@dataclass
class OAuth2(ToolAuthorization):
    """OAuth2 authorization."""
    
    scopes: List[str]
    
    def validate(self, token: str) -> bool:
        # In a real implementation, this would validate the token and its scopes
        return bool(token)


class APIKey(ToolAuthorization):
    """API Key authorization base class."""
    env_var: str  # Environment variable name for the API key

    def validate(self) -> bool:
        """Check if the API key is present in the environment."""
        return os.getenv(self.env_var) is not None

@dataclass
class BearerToken(ToolAuthorization):
    """Bearer token authorization."""
    
    def validate(self, token: str) -> bool:
        # In a real implementation, this would validate the token
        return bool(token)


def _import_google_auth() -> any:
    """Import Google Auth related dependencies."""
    try:
        import google.oauth2.credentials
        import google_auth_oauthlib.flow
        import googleapiclient.discovery
        return (google.oauth2.credentials, google_auth_oauthlib.flow, googleapiclient.discovery)
    except ImportError as e:
        raise ImportError(
            "Cannot import Google Auth libraries. Install with: "
            "`pip install google-auth google-auth-oauthlib google-api-python-client`."
        ) from e


def _import_github() -> any:
    """Import GitHub related dependencies."""
    try:
        from github import Github
        return Github
    except ImportError as e:
        raise ImportError(
            "Cannot import PyGithub. Install with: `pip install PyGithub`."
        ) from e


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
        
    def get_credentials(self, token: str):
        """
        Get Google credentials from the token.
        
        Args:
            token: The OAuth2 token.
            
        Returns:
            Google credentials object.
        """
        google_creds, _, _ = _import_google_auth()
        return google_creds.Credentials(token=token, scopes=self.scopes)


class GitHub(OAuth2):
    """GitHub-specific OAuth2 authorization."""
    
    def __init__(self, scopes: List[str] = None):
        default_scopes = [
            "repo",
            "user",
        ]
        super().__init__(scopes or default_scopes)
        
    def get_client(self, token: str):
        """
        Get GitHub client from the token.
        
        Args:
            token: The OAuth2 token.
            
        Returns:
            GitHub client object.
        """
        Github = _import_github()
        return Github(token)


class OpenWeatherMap(APIKey):
    """OpenWeatherMap-specific API key authorization."""
    env_var = "OPENWEATHERMAP_API_KEY"


class Firecrawl(APIKey):
    """Firecrawl-specific API key authorization."""
    env_var = "FIRECRAWL_API_KEY"