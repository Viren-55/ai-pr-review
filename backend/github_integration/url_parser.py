"""GitHub URL parser for extracting repository and PR information."""

import re
from typing import Optional, Tuple
from urllib.parse import urlparse
from dataclasses import dataclass

@dataclass
class GitHubPRInfo:
    """Information extracted from GitHub PR URL."""
    owner: str
    repo: str
    pr_number: int
    full_repo: str  # owner/repo format
    
    @property
    def api_url(self) -> str:
        """Get GitHub API URL for this PR."""
        return f"https://api.github.com/repos/{self.full_repo}/pulls/{self.pr_number}"
    
    @property
    def web_url(self) -> str:
        """Get GitHub web URL for this PR."""
        return f"https://github.com/{self.full_repo}/pull/{self.pr_number}"

class GitHubURLParser:
    """Parser for GitHub URLs to extract repository and PR information."""
    
    # Regex patterns for different GitHub URL formats
    PR_URL_PATTERNS = [
        # https://github.com/owner/repo/pull/123
        r'^https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)(?:/.*)?$',
        # https://github.com/owner/repo/pulls/123 (sometimes used)
        r'^https?://github\.com/([^/]+)/([^/]+)/pulls/(\d+)(?:/.*)?$',
    ]
    
    @staticmethod
    def parse_pr_url(url: str) -> Optional[GitHubPRInfo]:
        """Parse GitHub PR URL and extract information.
        
        Args:
            url: GitHub PR URL to parse
            
        Returns:
            GitHubPRInfo: Parsed PR information, or None if invalid
        """
        if not url or not isinstance(url, str):
            return None
        
        # Clean up the URL
        url = url.strip()
        
        # Try each pattern
        for pattern in GitHubURLParser.PR_URL_PATTERNS:
            match = re.match(pattern, url, re.IGNORECASE)
            if match:
                owner, repo, pr_number_str = match.groups()
                
                try:
                    pr_number = int(pr_number_str)
                    
                    # Validate owner and repo names (GitHub requirements)
                    if not GitHubURLParser._is_valid_github_name(owner):
                        return None
                    if not GitHubURLParser._is_valid_github_name(repo):
                        return None
                    
                    return GitHubPRInfo(
                        owner=owner,
                        repo=repo,
                        pr_number=pr_number,
                        full_repo=f"{owner}/{repo}"
                    )
                    
                except ValueError:
                    # Invalid PR number
                    continue
        
        return None
    
    @staticmethod
    def _is_valid_github_name(name: str) -> bool:
        """Validate GitHub username/repository name.
        
        GitHub names can contain alphanumeric characters and hyphens,
        but cannot start or end with hyphens.
        """
        if not name or len(name) > 39:  # GitHub max length is 39
            return False
        
        # Check for valid characters and format
        if not re.match(r'^[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?$', name):
            return False
        
        return True
    
    @staticmethod
    def extract_repo_info(url: str) -> Optional[Tuple[str, str]]:
        """Extract just owner and repo from any GitHub URL.
        
        Args:
            url: GitHub URL (can be PR, issue, or repo URL)
            
        Returns:
            Tuple[str, str]: (owner, repo) or None if invalid
        """
        if not url:
            return None
        
        try:
            parsed = urlparse(url.strip())
            
            if parsed.netloc.lower() != 'github.com':
                return None
            
            # Split path and extract owner/repo
            path_parts = [p for p in parsed.path.split('/') if p]
            
            if len(path_parts) >= 2:
                owner, repo = path_parts[0], path_parts[1]
                
                if (GitHubURLParser._is_valid_github_name(owner) and 
                    GitHubURLParser._is_valid_github_name(repo)):
                    return owner, repo
            
            return None
            
        except Exception:
            return None
    
    @staticmethod
    def is_github_url(url: str) -> bool:
        """Check if URL is a valid GitHub URL.
        
        Args:
            url: URL to check
            
        Returns:
            bool: True if valid GitHub URL
        """
        if not url:
            return False
        
        try:
            parsed = urlparse(url.strip())
            return parsed.netloc.lower() == 'github.com'
        except Exception:
            return False
    
    @staticmethod
    def normalize_pr_url(url: str) -> Optional[str]:
        """Normalize PR URL to standard format.
        
        Args:
            url: GitHub PR URL to normalize
            
        Returns:
            str: Normalized URL or None if invalid
        """
        pr_info = GitHubURLParser.parse_pr_url(url)
        if pr_info:
            return pr_info.web_url
        return None