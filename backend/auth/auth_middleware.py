"""Authentication middleware for FastAPI endpoints."""

from typing import Optional, Annotated
from fastapi import Depends, HTTPException, status, Cookie, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import jwt
import os
from datetime import datetime, timedelta
import logging

from database import get_db
from .token_manager import get_token_manager
from .github_oauth import GitHubOAuth, GitHubAuthConfig

logger = logging.getLogger(__name__)

# JWT configuration for session tokens
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

security = HTTPBearer(auto_error=False)

class AuthenticationError(Exception):
    """Custom authentication error."""
    pass

def create_session_token(user_id: int, github_username: str) -> str:
    """Create JWT session token for authenticated user.
    
    Args:
        user_id: Database user ID
        github_username: GitHub username
        
    Returns:
        str: JWT token
    """
    payload = {
        "user_id": user_id,
        "github_username": github_username,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.utcnow(),
        "type": "session"
    }
    
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def verify_session_token(token: str) -> dict:
    """Verify JWT session token.
    
    Args:
        token: JWT token to verify
        
    Returns:
        dict: Decoded token payload
        
    Raises:
        AuthenticationError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        # Verify token type
        if payload.get("type") != "session":
            raise AuthenticationError("Invalid token type")
        
        return payload
        
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Session token has expired")
    except jwt.InvalidTokenError as e:
        raise AuthenticationError(f"Invalid session token: {str(e)}")

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    session_token: Optional[str] = Cookie(None, alias="session_token"),
    db: Session = Depends(get_db)
):
    """Get current authenticated user from request.
    
    Checks for authentication in the following order:
    1. Bearer token in Authorization header
    2. Session cookie
    
    Args:
        credentials: HTTP Bearer credentials
        session_token: Session token from cookie
        db: Database session
        
    Returns:
        GitHubUser: Authenticated user object
        
    Raises:
        HTTPException: If authentication fails
    """
    from models import GitHubUser  # Import here to avoid circular imports
    
    token = None
    
    # Try Bearer token first
    if credentials:
        token = credentials.credentials
    # Fall back to session cookie
    elif session_token:
        token = session_token
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        # Verify session token
        payload = verify_session_token(token)
        user_id = payload.get("user_id")
        
        if not user_id:
            raise AuthenticationError("Invalid token payload")
        
        # Get user from database
        user = db.query(GitHubUser).filter(GitHubUser.id == user_id).first()
        
        if not user:
            raise AuthenticationError("User not found")
        
        # Validate GitHub token is still valid
        token_manager = get_token_manager()
        github_token = token_manager.extract_access_token(user.encrypted_token_data)
        
        # Create GitHub OAuth client to validate token
        try:
            github_config = GitHubAuthConfig.from_env()
            github_oauth = GitHubOAuth(github_config)
            
            is_valid = await github_oauth.validate_token(github_token)
            await github_oauth.close()
            
            if not is_valid:
                # GitHub token is invalid, user needs to re-authenticate
                raise AuthenticationError("GitHub token expired or revoked")
                
        except Exception as e:
            logger.warning(f"GitHub token validation failed: {e}")
            # Continue with session - token validation is optional for some operations
        
        return user
        
    except AuthenticationError as e:
        logger.warning(f"Authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        logger.error(f"Unexpected authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error"
        )

async def authenticate_github_user(
    token: str,
    db: Session = Depends(get_db)
) -> 'GitHubUser':
    """Authenticate user with GitHub access token directly.
    
    This is used during the OAuth callback process.
    
    Args:
        token: GitHub access token
        db: Database session
        
    Returns:
        GitHubUser: Authenticated user
    """
    from models import GitHubUser
    
    try:
        # Get GitHub user info
        github_config = GitHubAuthConfig.from_env()
        github_oauth = GitHubOAuth(github_config)
        
        user_info = await github_oauth.get_user_info(token)
        await github_oauth.close()
        
        # Check if user exists
        github_id = user_info["id"]
        user = db.query(GitHubUser).filter(GitHubUser.github_id == github_id).first()
        
        if not user:
            # Create new user
            token_manager = get_token_manager()
            encrypted_token = token_manager.create_token_record({"access_token": token})
            
            user = GitHubUser(
                github_id=github_id,
                username=user_info["login"],
                email=user_info.get("email"),
                avatar_url=user_info.get("avatar_url"),
                encrypted_token_data=encrypted_token
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            logger.info(f"Created new GitHub user: {user.username}")
        else:
            # Update existing user info and token
            token_manager = get_token_manager()
            encrypted_token = token_manager.create_token_record({"access_token": token})
            
            user.username = user_info["login"]
            user.email = user_info.get("email")
            user.avatar_url = user_info.get("avatar_url")
            user.encrypted_token_data = encrypted_token
            user.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(user)
            
            logger.info(f"Updated GitHub user: {user.username}")
        
        return user
        
    except Exception as e:
        logger.error(f"GitHub user authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to authenticate with GitHub: {str(e)}"
        )

# Optional: Create dependency for endpoints that require GitHub operations
async def get_github_authenticated_user(
    current_user: 'GitHubUser' = Depends(get_current_user)
) -> 'GitHubUser':
    """Get user specifically for GitHub operations.
    
    This ensures the user has valid GitHub credentials.
    """
    # Additional GitHub-specific validation could be added here
    return current_user