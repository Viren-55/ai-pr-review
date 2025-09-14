"""Token management for secure storage and encryption of GitHub access tokens."""

import os
import json
import secrets
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import logging

logger = logging.getLogger(__name__)

class TokenManager:
    """Manages secure token storage with encryption."""
    
    def __init__(self, encryption_key: Optional[str] = None):
        """Initialize token manager with encryption.
        
        Args:
            encryption_key: Base64 encoded 256-bit key. If None, generates from environment.
        """
        if encryption_key is None:
            encryption_key = self._get_encryption_key_from_env()
        
        self.fernet = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)
    
    def _get_encryption_key_from_env(self) -> str:
        """Get or generate encryption key from environment."""
        key = os.getenv("TOKEN_ENCRYPTION_KEY")
        
        if not key:
            # Generate a new key for development
            key = Fernet.generate_key().decode()
            logger.warning(
                f"No TOKEN_ENCRYPTION_KEY found in environment. Generated temporary key: {key}\n"
                "For production, set TOKEN_ENCRYPTION_KEY environment variable with a secure 256-bit key."
            )
        
        return key
    
    def encrypt_token_data(self, token_data: dict) -> str:
        """Encrypt token data for secure storage.
        
        Args:
            token_data: Dictionary containing token information
            
        Returns:
            str: Encrypted token data as base64 string
        """
        try:
            # Convert dict to JSON string
            json_data = json.dumps(token_data)
            
            # Encrypt the JSON data
            encrypted_data = self.fernet.encrypt(json_data.encode())
            
            # Return as base64 string for database storage
            return base64.b64encode(encrypted_data).decode()
            
        except Exception as e:
            logger.error(f"Token encryption failed: {e}")
            raise ValueError("Failed to encrypt token data")
    
    def decrypt_token_data(self, encrypted_data: str) -> dict:
        """Decrypt token data from storage.
        
        Args:
            encrypted_data: Base64 encoded encrypted token data
            
        Returns:
            dict: Decrypted token information
        """
        try:
            # Decode from base64
            encrypted_bytes = base64.b64decode(encrypted_data.encode())
            
            # Decrypt the data
            decrypted_bytes = self.fernet.decrypt(encrypted_bytes)
            
            # Parse JSON
            token_data = json.loads(decrypted_bytes.decode())
            
            return token_data
            
        except Exception as e:
            logger.error(f"Token decryption failed: {e}")
            raise ValueError("Failed to decrypt token data")
    
    def extract_access_token(self, encrypted_data: str) -> str:
        """Extract access token from encrypted data.
        
        Args:
            encrypted_data: Encrypted token data from database
            
        Returns:
            str: GitHub access token
        """
        token_data = self.decrypt_token_data(encrypted_data)
        access_token = token_data.get("access_token")
        
        if not access_token:
            raise ValueError("No access token found in encrypted data")
        
        return access_token
    
    def is_token_expired(self, encrypted_data: str) -> bool:
        """Check if token is expired (if expiration info available).
        
        Args:
            encrypted_data: Encrypted token data
            
        Returns:
            bool: True if token is expired, False otherwise
        """
        try:
            token_data = self.decrypt_token_data(encrypted_data)
            
            # GitHub tokens don't typically have expiration info in the response
            # but we can check if expires_in field exists and calculate
            expires_in = token_data.get("expires_in")
            created_at = token_data.get("created_at")
            
            if expires_in and created_at:
                import time
                current_time = time.time()
                expiration_time = created_at + expires_in
                return current_time >= expiration_time
            
            # If no expiration info, assume token is valid
            return False
            
        except Exception as e:
            logger.warning(f"Could not check token expiration: {e}")
            return True  # Assume expired if we can't check
    
    def create_token_record(self, token_response: dict) -> str:
        """Create encrypted token record for database storage.
        
        Args:
            token_response: GitHub token response
            
        Returns:
            str: Encrypted token data for storage
        """
        import time
        
        # Add timestamp for expiration tracking
        token_data = {
            **token_response,
            "created_at": time.time()
        }
        
        return self.encrypt_token_data(token_data)
    
    @staticmethod
    def generate_state_token() -> str:
        """Generate cryptographically secure state token for OAuth flow.
        
        Returns:
            str: Random state token
        """
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def generate_encryption_key() -> str:
        """Generate a new encryption key for TOKEN_ENCRYPTION_KEY.
        
        Returns:
            str: Base64 encoded encryption key
        """
        return Fernet.generate_key().decode()

# Global token manager instance
_token_manager = None

def get_token_manager() -> TokenManager:
    """Get global token manager instance."""
    global _token_manager
    if _token_manager is None:
        _token_manager = TokenManager()
    return _token_manager