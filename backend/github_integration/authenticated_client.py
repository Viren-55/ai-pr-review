"""Authenticated GitHub API client for PR operations."""

import httpx
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from .url_parser import GitHubPRInfo

logger = logging.getLogger(__name__)

class GitHubAPIError(Exception):
    """Custom exception for GitHub API errors."""
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(message)

class GitHubClient:
    """Authenticated GitHub API client for fetching PR data."""
    
    BASE_URL = "https://api.github.com"
    API_VERSION = "2022-11-28"
    
    def __init__(self, access_token: Optional[str] = None):
        """Initialize GitHub client with optional access token.
        
        Args:
            access_token: GitHub personal access token (optional for public repos)
        """
        self.access_token = access_token
        
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": self.API_VERSION,
            "User-Agent": "CodeReview-Platform/1.0"
        }
        
        # Only add authorization header if token is provided
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        
        self._client = httpx.AsyncClient(
            headers=headers,
            timeout=30.0
        )
    
    async def get_pr_info(self, pr_info: GitHubPRInfo) -> Dict[str, Any]:
        """Get detailed PR information.
        
        Args:
            pr_info: Parsed PR information
            
        Returns:
            dict: PR information from GitHub API
        """
        try:
            response = await self._client.get(pr_info.api_url)
            
            if response.status_code == 404:
                raise GitHubAPIError("Pull request not found", 404)
            elif response.status_code == 403:
                raise GitHubAPIError("Access denied - repository may be private", 403)
            elif response.status_code != 200:
                raise GitHubAPIError(
                    f"GitHub API error: {response.status_code}",
                    response.status_code,
                    response.json() if response.content else None
                )
            
            pr_data = response.json()
            logger.info(f"Fetched PR #{pr_info.pr_number} from {pr_info.full_repo}")
            
            return pr_data
            
        except httpx.RequestError as e:
            logger.error(f"Network error fetching PR: {e}")
            raise GitHubAPIError(f"Network error: {str(e)}")
    
    async def get_pr_diff(self, pr_info: GitHubPRInfo) -> str:
        """Get the full diff for the PR.
        
        Args:
            pr_info: Parsed PR information
            
        Returns:
            str: Full diff content in unified format
        """
        try:
            # Get PR diff in unified format
            response = await self._client.get(
                f"{self.BASE_URL}/repos/{pr_info.full_repo}/pulls/{pr_info.pr_number}",
                headers={"Accept": "application/vnd.github.diff"}
            )
            
            if response.status_code != 200:
                raise GitHubAPIError(
                    f"Failed to fetch PR diff: {response.status_code}",
                    response.status_code
                )
            
            diff_content = response.text
            logger.info(f"Fetched diff for PR #{pr_info.pr_number} ({len(diff_content)} chars)")
            
            return diff_content
            
        except httpx.RequestError as e:
            logger.error(f"Network error fetching PR diff: {e}")
            raise GitHubAPIError(f"Network error: {str(e)}")
    
    async def get_pr_files(self, pr_info: GitHubPRInfo) -> List[Dict[str, Any]]:
        """Get list of files changed in the PR.
        
        Args:
            pr_info: Parsed PR information
            
        Returns:
            list: List of changed files with diff information
        """
        try:
            files_url = f"{pr_info.api_url}/files"
            response = await self._client.get(files_url)
            
            if response.status_code != 200:
                raise GitHubAPIError(
                    f"Failed to fetch PR files: {response.status_code}",
                    response.status_code
                )
            
            files_data = response.json()
            logger.info(f"Fetched {len(files_data)} changed files for PR #{pr_info.pr_number}")
            
            return files_data
            
        except httpx.RequestError as e:
            logger.error(f"Network error fetching PR files: {e}")
            raise GitHubAPIError(f"Network error: {str(e)}")
    
    
    async def get_file_content(self, owner: str, repo: str, file_path: str, ref: str = "main") -> str:
        """Get content of a specific file from repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            file_path: Path to file in repository
            ref: Git reference (branch, commit, tag)
            
        Returns:
            str: File content
        """
        try:
            # GitHub API endpoint for file content
            url = f"{self.BASE_URL}/repos/{owner}/{repo}/contents/{file_path}"
            params = {"ref": ref}
            
            response = await self._client.get(url, params=params)
            
            if response.status_code == 404:
                raise GitHubAPIError(f"File not found: {file_path}", 404)
            elif response.status_code != 200:
                raise GitHubAPIError(
                    f"Failed to fetch file content: {response.status_code}",
                    response.status_code
                )
            
            file_data = response.json()
            
            # File content is base64 encoded
            import base64
            content = base64.b64decode(file_data["content"]).decode("utf-8")
            
            return content
            
        except httpx.RequestError as e:
            logger.error(f"Network error fetching file content: {e}")
            raise GitHubAPIError(f"Network error: {str(e)}")
        except UnicodeDecodeError:
            raise GitHubAPIError("File content is not valid UTF-8 text")
    
    async def create_pr_review(self, pr_info: GitHubPRInfo, body: str, event: str = "COMMENT") -> Dict[str, Any]:
        """Create a review on the PR.
        
        Args:
            pr_info: PR information
            body: Review comment body
            event: Review event type ("APPROVE", "REQUEST_CHANGES", "COMMENT")
            
        Returns:
            dict: Created review information
        """
        try:
            reviews_url = f"{pr_info.api_url}/reviews"
            
            review_data = {
                "body": body,
                "event": event
            }
            
            response = await self._client.post(reviews_url, json=review_data)
            
            if response.status_code not in [200, 201]:
                raise GitHubAPIError(
                    f"Failed to create PR review: {response.status_code}",
                    response.status_code,
                    response.json() if response.content else None
                )
            
            review = response.json()
            logger.info(f"Created PR review #{review['id']} for PR #{pr_info.pr_number}")
            
            return review
            
        except httpx.RequestError as e:
            logger.error(f"Network error creating PR review: {e}")
            raise GitHubAPIError(f"Network error: {str(e)}")
    
    async def create_pr_comment(self, pr_info: GitHubPRInfo, body: str, 
                              file_path: Optional[str] = None, line: Optional[int] = None) -> Dict[str, Any]:
        """Create a comment on the PR.
        
        Args:
            pr_info: PR information
            body: Comment body
            file_path: File path for line comment (optional)
            line: Line number for line comment (optional)
            
        Returns:
            dict: Created comment information
        """
        try:
            if file_path and line:
                # Create review comment on specific line
                comments_url = f"{pr_info.api_url}/comments"
                comment_data = {
                    "body": body,
                    "path": file_path,
                    "line": line
                }
            else:
                # Create general PR comment
                comments_url = f"{self.BASE_URL}/repos/{pr_info.full_repo}/issues/{pr_info.pr_number}/comments"
                comment_data = {"body": body}
            
            response = await self._client.post(comments_url, json=comment_data)
            
            if response.status_code not in [200, 201]:
                raise GitHubAPIError(
                    f"Failed to create PR comment: {response.status_code}",
                    response.status_code,
                    response.json() if response.content else None
                )
            
            comment = response.json()
            logger.info(f"Created PR comment #{comment['id']} for PR #{pr_info.pr_number}")
            
            return comment
            
        except httpx.RequestError as e:
            logger.error(f"Network error creating PR comment: {e}")
            raise GitHubAPIError(f"Network error: {str(e)}")
    
    async def validate_access(self) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Validate GitHub access token and get user info.
        
        Returns:
            tuple: (is_valid, user_info)
        """
        try:
            response = await self._client.get(f"{self.BASE_URL}/user")
            
            if response.status_code == 200:
                return True, response.json()
            else:
                return False, None
                
        except Exception as e:
            logger.warning(f"Token validation failed: {e}")
            return False, None
    
    async def close(self):
        """Close HTTP client connection."""
        await self._client.aclose()