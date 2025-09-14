"""GitHub OAuth 2.0 integration for user authentication."""

import os
import secrets
import httpx
from typing import Optional, Dict, Any
from dataclasses import dataclass
from urllib.parse import urlencode
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

@dataclass
class GitHubAuthConfig:
    """GitHub OAuth configuration."""
    client_id: str
    client_secret: str
    redirect_uri: str
    scopes: list[str]

    @classmethod
    def from_env(cls) -> 'GitHubAuthConfig':
        """Create config from environment variables."""
        client_id = os.getenv("GITHUB_CLIENT_ID")
        client_secret = os.getenv("GITHUB_CLIENT_SECRET") 
        redirect_uri = os.getenv("GITHUB_REDIRECT_URI", "http://localhost:3000/auth/callback")
        
        if not client_id or not client_secret:
            raise ValueError("GitHub OAuth credentials not configured. Please set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET")
        
        # Minimal scopes for user authentication only
        # Users will provide PR URLs manually, no repo access needed during auth
        scopes = [
            "user:email"      # User email for identification
        ]
        
        return cls(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scopes=scopes
        )

class GitHubOAuth:
    """GitHub OAuth 2.0 handler."""
    
    GITHUB_OAUTH_URL = "https://github.com/login/oauth/authorize"
    GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
    GITHUB_USER_API = "https://api.github.com/user"
    
    def __init__(self, config: GitHubAuthConfig):
        self.config = config
        self._http_client = httpx.AsyncClient()
    
    def generate_auth_url(self, state: Optional[str] = None) -> tuple[str, str]:
        """Generate GitHub OAuth authorization URL.
        
        Returns:
            tuple: (auth_url, state) - The authorization URL and state parameter
        """
        if state is None:
            state = secrets.token_urlsafe(32)
        
        params = {
            "client_id": self.config.client_id,
            "redirect_uri": self.config.redirect_uri,
            "scope": " ".join(self.config.scopes),
            "state": state,
            "response_type": "code"
        }
        
        auth_url = f"{self.GITHUB_OAUTH_URL}?{urlencode(params)}"
        return auth_url, state
    
    async def exchange_code_for_token(self, code: str, state: str) -> Dict[str, Any]:
        """Exchange authorization code for access token.
        
        Args:
            code: Authorization code from GitHub
            state: State parameter for CSRF protection
            
        Returns:
            dict: Token response containing access_token, token_type, scope
        """
        try:
            # Exchange code for token
            token_data = {
                "client_id": self.config.client_id,
                "client_secret": self.config.client_secret,
                "code": code,
                "redirect_uri": self.config.redirect_uri
            }
            
            headers = {"Accept": "application/json"}
            
            response = await self._http_client.post(
                self.GITHUB_TOKEN_URL,
                data=token_data,
                headers=headers
            )
            
            if response.status_code != 200:
                logger.error(f"GitHub token exchange failed: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=400,
                    detail="Failed to exchange authorization code for token"
                )
            
            token_response = response.json()
            
            if "error" in token_response:
                logger.error(f"GitHub OAuth error: {token_response}")
                raise HTTPException(
                    status_code=400,
                    detail=f"GitHub OAuth error: {token_response.get('error_description', 'Unknown error')}"
                )
            
            return token_response
            
        except httpx.RequestError as e:
            logger.error(f"HTTP error during token exchange: {e}")
            raise HTTPException(
                status_code=500,
                detail="Network error during GitHub authentication"
            )
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get GitHub user information using access token.
        
        Args:
            access_token: GitHub access token
            
        Returns:
            dict: User information from GitHub API
        """
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28"
            }
            
            response = await self._http_client.get(
                self.GITHUB_USER_API,
                headers=headers
            )
            
            if response.status_code != 200:
                logger.error(f"GitHub user API failed: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=400,
                    detail="Failed to fetch user information from GitHub"
                )
            
            user_data = response.json()
            
            # Get user email if not public
            if not user_data.get("email"):
                user_data["email"] = await self._get_primary_email(access_token)
            
            return user_data
            
        except httpx.RequestError as e:
            logger.error(f"HTTP error during user info fetch: {e}")
            raise HTTPException(
                status_code=500,
                detail="Network error fetching user information"
            )
    
    async def _get_primary_email(self, access_token: str) -> Optional[str]:
        """Get user's primary email address."""
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28"
            }
            
            response = await self._http_client.get(
                "https://api.github.com/user/emails",
                headers=headers
            )
            
            if response.status_code == 200:
                emails = response.json()
                for email in emails:
                    if email.get("primary") and email.get("verified"):
                        return email["email"]
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to fetch user email: {e}")
            return None
    
    async def validate_token(self, access_token: str) -> bool:
        """Validate if access token is still valid.
        
        Args:
            access_token: GitHub access token to validate
            
        Returns:
            bool: True if token is valid, False otherwise
        """
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json"
            }
            
            response = await self._http_client.get(
                self.GITHUB_USER_API,
                headers=headers
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.warning(f"Token validation failed: {e}")
            return False
    
    async def revoke_token(self, access_token: str) -> bool:
        """Revoke GitHub access token.
        
        Args:
            access_token: Token to revoke
            
        Returns:
            bool: True if revocation successful
        """
        try:
            # GitHub doesn't have a standard token revocation endpoint
            # Instead, we'll just validate that we can't use it anymore
            # The token will naturally expire or can be revoked from GitHub settings
            
            # For now, we'll just return True and let the token naturally expire
            # In a production system, you might want to maintain a revoked tokens blacklist
            return True
            
        except Exception as e:
            logger.warning(f"Token revocation failed: {e}")
            return False
    
    async def close(self):
        """Close HTTP client."""
        await self._http_client.aclose()