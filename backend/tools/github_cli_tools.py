"""GitHub CLI tools for AI agents to use for data fetching and operations."""

import subprocess
import json
import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class GitHubCLIResult:
    """Result from GitHub CLI command execution."""
    success: bool
    data: Optional[Union[Dict, List, str]] = None
    error: Optional[str] = None
    raw_output: str = ""

class GitHubCLITools:
    """GitHub CLI tools that AI agents can use to fetch data and perform operations."""
    
    def __init__(self, token: Optional[str] = None):
        """Initialize GitHub CLI tools.
        
        Args:
            token: GitHub personal access token
        """
        self.token = token
        self._setup_auth()
    
    def _setup_auth(self):
        """Setup GitHub CLI authentication."""
        if self.token:
            try:
                # Set auth token for gh CLI
                result = subprocess.run(
                    ["gh", "auth", "login", "--with-token"],
                    input=self.token,
                    text=True,
                    capture_output=True,
                    timeout=30
                )
                if result.returncode != 0:
                    logger.warning(f"Failed to authenticate with gh CLI: {result.stderr}")
            except Exception as e:
                logger.warning(f"Failed to setup gh CLI auth: {e}")
    
    def _run_gh_command(self, command: List[str], json_output: bool = True) -> GitHubCLIResult:
        """Run a GitHub CLI command and return the result.
        
        Args:
            command: GitHub CLI command parts
            json_output: Whether to request JSON output
            
        Returns:
            GitHubCLIResult: Command execution result
        """
        try:
            # Add JSON format if requested
            if json_output and "--json" not in command:
                command.extend(["--json", "url,title,body,user,createdAt,updatedAt,state,merged,mergeable,baseRefName,headRefName,additions,deletions,changedFiles"])
            
            # Run the command
            result = subprocess.run(
                ["gh"] + command,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                # Success
                raw_output = result.stdout.strip()
                
                if json_output and raw_output:
                    try:
                        data = json.loads(raw_output)
                        return GitHubCLIResult(success=True, data=data, raw_output=raw_output)
                    except json.JSONDecodeError:
                        return GitHubCLIResult(success=True, data=raw_output, raw_output=raw_output)
                else:
                    return GitHubCLIResult(success=True, data=raw_output, raw_output=raw_output)
            else:
                # Command failed
                error_msg = result.stderr.strip()
                logger.error(f"GitHub CLI command failed: {' '.join(command)}, error: {error_msg}")
                return GitHubCLIResult(success=False, error=error_msg, raw_output=result.stdout)
                
        except subprocess.TimeoutExpired:
            logger.error(f"GitHub CLI command timed out: {' '.join(command)}")
            return GitHubCLIResult(success=False, error="Command timed out")
        except Exception as e:
            logger.error(f"Failed to run GitHub CLI command: {e}")
            return GitHubCLIResult(success=False, error=str(e))
    
    def get_pr_info(self, repo: str, pr_number: int) -> GitHubCLIResult:
        """Get detailed PR information using GitHub CLI.
        
        Args:
            repo: Repository in format "owner/repo"
            pr_number: Pull request number
            
        Returns:
            GitHubCLIResult: PR information
        """
        command = ["pr", "view", str(pr_number), "--repo", repo]
        return self._run_gh_command(command, json_output=True)
    
    def get_pr_diff(self, repo: str, pr_number: int) -> GitHubCLIResult:
        """Get PR diff using GitHub CLI.
        
        Args:
            repo: Repository in format "owner/repo"
            pr_number: Pull request number
            
        Returns:
            GitHubCLIResult: PR diff content
        """
        command = ["pr", "diff", str(pr_number), "--repo", repo]
        return self._run_gh_command(command, json_output=False)
    
    def get_pr_files(self, repo: str, pr_number: int) -> GitHubCLIResult:
        """Get list of changed files in PR using GitHub CLI.
        
        Args:
            repo: Repository in format "owner/repo"
            pr_number: Pull request number
            
        Returns:
            GitHubCLIResult: List of changed files
        """
        command = ["pr", "view", str(pr_number), "--repo", repo, "--json", "files"]
        return self._run_gh_command(command, json_output=True)
    
    def get_repo_info(self, repo: str) -> GitHubCLIResult:
        """Get repository information using GitHub CLI.
        
        Args:
            repo: Repository in format "owner/repo"
            
        Returns:
            GitHubCLIResult: Repository information
        """
        command = ["repo", "view", repo]
        return self._run_gh_command(command, json_output=True)
    
    def get_file_content(self, repo: str, file_path: str, ref: str = "HEAD") -> GitHubCLIResult:
        """Get file content from repository.
        
        Args:
            repo: Repository in format "owner/repo"
            file_path: Path to file in repository
            ref: Git reference (branch, commit, tag)
            
        Returns:
            GitHubCLIResult: File content
        """
        command = ["api", f"/repos/{repo}/contents/{file_path}", "--jq", ".content", "-q", f"ref={ref}"]
        result = self._run_gh_command(command, json_output=False)
        
        if result.success and result.data:
            try:
                # Decode base64 content
                import base64
                decoded_content = base64.b64decode(result.data).decode('utf-8')
                result.data = decoded_content
            except Exception as e:
                logger.warning(f"Failed to decode file content: {e}")
        
        return result
    
    def search_issues(self, repo: str, query: str, limit: int = 10) -> GitHubCLIResult:
        """Search issues in repository.
        
        Args:
            repo: Repository in format "owner/repo"
            query: Search query
            limit: Maximum number of results
            
        Returns:
            GitHubCLIResult: Search results
        """
        command = ["issue", "list", "--repo", repo, "--search", query, "--limit", str(limit)]
        return self._run_gh_command(command, json_output=True)
    
    def get_repo_languages(self, repo: str) -> GitHubCLIResult:
        """Get programming languages used in repository.
        
        Args:
            repo: Repository in format "owner/repo"
            
        Returns:
            GitHubCLIResult: Language statistics
        """
        command = ["api", f"/repos/{repo}/languages"]
        return self._run_gh_command(command, json_output=True)
    
    def get_recent_commits(self, repo: str, limit: int = 10, author: Optional[str] = None) -> GitHubCLIResult:
        """Get recent commits from repository.
        
        Args:
            repo: Repository in format "owner/repo"
            limit: Maximum number of commits
            author: Filter by author
            
        Returns:
            GitHubCLIResult: Recent commits
        """
        command = ["api", f"/repos/{repo}/commits", "--jq", ".[0:{}]".format(limit)]
        if author:
            command.extend(["-F", f"author={author}"])
        
        return self._run_gh_command(command, json_output=True)
    
    def get_pr_reviews(self, repo: str, pr_number: int) -> GitHubCLIResult:
        """Get reviews for a pull request.
        
        Args:
            repo: Repository in format "owner/repo"
            pr_number: Pull request number
            
        Returns:
            GitHubCLIResult: PR reviews
        """
        command = ["api", f"/repos/{repo}/pulls/{pr_number}/reviews"]
        return self._run_gh_command(command, json_output=True)
    
    def get_pr_comments(self, repo: str, pr_number: int) -> GitHubCLIResult:
        """Get comments for a pull request.
        
        Args:
            repo: Repository in format "owner/repo"
            pr_number: Pull request number
            
        Returns:
            GitHubCLIResult: PR comments
        """
        command = ["api", f"/repos/{repo}/pulls/{pr_number}/comments"]
        return self._run_gh_command(command, json_output=True)
    
    def create_pr_comment(self, repo: str, pr_number: int, body: str) -> GitHubCLIResult:
        """Create a comment on a pull request.
        
        Args:
            repo: Repository in format "owner/repo"  
            pr_number: Pull request number
            body: Comment body
            
        Returns:
            GitHubCLIResult: Created comment
        """
        command = ["pr", "comment", str(pr_number), "--repo", repo, "--body", body]
        return self._run_gh_command(command, json_output=True)
    
    def create_pr_review(self, repo: str, pr_number: int, body: str, event: str = "COMMENT") -> GitHubCLIResult:
        """Create a review for a pull request.
        
        Args:
            repo: Repository in format "owner/repo"
            pr_number: Pull request number
            body: Review body
            event: Review event (APPROVE, REQUEST_CHANGES, COMMENT)
            
        Returns:
            GitHubCLIResult: Created review
        """
        command = ["pr", "review", str(pr_number), "--repo", repo, "--body", body]
        
        if event == "APPROVE":
            command.append("--approve")
        elif event == "REQUEST_CHANGES":
            command.append("--request-changes")
        # COMMENT is default, no additional flag needed
        
        return self._run_gh_command(command, json_output=True)
    
    def check_cli_available(self) -> bool:
        """Check if GitHub CLI is available and authenticated.
        
        Returns:
            bool: True if CLI is available and authenticated
        """
        try:
            result = subprocess.run(
                ["gh", "auth", "status"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False

class AIGitHubToolkit:
    """High-level toolkit that provides GitHub operations for AI agents."""
    
    def __init__(self, token: Optional[str] = None):
        """Initialize GitHub toolkit for AI agents.
        
        Args:
            token: GitHub personal access token
        """
        self.cli = GitHubCLITools(token)
        self.is_available = self.cli.check_cli_available()
        
        if not self.is_available:
            logger.warning("GitHub CLI not available or not authenticated. Some features may not work.")
    
    def analyze_pr_context(self, repo: str, pr_number: int) -> Dict[str, Any]:
        """Analyze PR context for AI agents - comprehensive PR data gathering.
        
        Args:
            repo: Repository in format "owner/repo"
            pr_number: Pull request number
            
        Returns:
            dict: Comprehensive PR context for AI analysis
        """
        if not self.is_available:
            return {"error": "GitHub CLI not available"}
        
        context = {
            "repository": repo,
            "pr_number": pr_number,
            "gathered_at": logger.info("Gathering comprehensive PR context..."),
            "data": {},
            "analysis_ready": False
        }
        
        try:
            # Gather all PR-related data
            pr_info = self.cli.get_pr_info(repo, pr_number)
            if pr_info.success:
                context["data"]["pr_info"] = pr_info.data
            
            pr_diff = self.cli.get_pr_diff(repo, pr_number)
            if pr_diff.success:
                context["data"]["diff"] = pr_diff.data
            
            pr_files = self.cli.get_pr_files(repo, pr_number)
            if pr_files.success:
                context["data"]["files"] = pr_files.data
            
            # Get repository context
            repo_info = self.cli.get_repo_info(repo)
            if repo_info.success:
                context["data"]["repository_info"] = repo_info.data
            
            # Get language information
            languages = self.cli.get_repo_languages(repo)
            if languages.success:
                context["data"]["languages"] = languages.data
            
            # Get existing reviews and comments
            reviews = self.cli.get_pr_reviews(repo, pr_number)
            if reviews.success:
                context["data"]["reviews"] = reviews.data
            
            comments = self.cli.get_pr_comments(repo, pr_number)
            if comments.success:
                context["data"]["comments"] = comments.data
            
            # Get recent commits context
            recent_commits = self.cli.get_recent_commits(repo, limit=5)
            if recent_commits.success:
                context["data"]["recent_commits"] = recent_commits.data
            
            context["analysis_ready"] = True
            logger.info(f"Successfully gathered PR context for {repo}#{pr_number}")
            
        except Exception as e:
            logger.error(f"Failed to gather PR context: {e}")
            context["error"] = str(e)
        
        return context
    
    def provide_pr_feedback(self, repo: str, pr_number: int, analysis_results: Dict[str, Any], 
                           create_review: bool = False) -> Dict[str, Any]:
        """Provide feedback on PR based on analysis results.
        
        Args:
            repo: Repository in format "owner/repo"
            pr_number: Pull request number
            analysis_results: Results from AI analysis
            create_review: Whether to create an actual GitHub review
            
        Returns:
            dict: Feedback operation result
        """
        if not self.is_available:
            return {"error": "GitHub CLI not available"}
        
        try:
            # Format analysis results into review comment
            review_body = self._format_analysis_as_review(analysis_results)
            
            if create_review:
                # Create actual GitHub review
                result = self.cli.create_pr_review(repo, pr_number, review_body)
                return {
                    "success": result.success,
                    "review_created": result.success,
                    "review_body": review_body,
                    "error": result.error if not result.success else None
                }
            else:
                # Just return formatted review for preview
                return {
                    "success": True,
                    "review_created": False,
                    "review_body": review_body,
                    "preview_only": True
                }
                
        except Exception as e:
            logger.error(f"Failed to provide PR feedback: {e}")
            return {"error": str(e), "success": False}
    
    def _format_analysis_as_review(self, analysis: Dict[str, Any]) -> str:
        """Format AI analysis results as GitHub review comment.
        
        Args:
            analysis: AI analysis results
            
        Returns:
            str: Formatted review comment
        """
        lines = []
        lines.append("## 🤖 AI Code Review")
        lines.append("")
        
        # Overall score
        if "analysis" in analysis and "overall_score" in analysis["analysis"]:
            score = analysis["analysis"]["overall_score"]
            if score >= 90:
                emoji = "🟢"
            elif score >= 70:
                emoji = "🟡"
            else:
                emoji = "🔴"
            lines.append(f"**Overall Score:** {emoji} {score}/100")
            lines.append("")
        
        # Summary
        if "analysis" in analysis and "analysis_summary" in analysis["analysis"]:
            lines.append("### Summary")
            lines.append(analysis["analysis"]["analysis_summary"])
            lines.append("")
        
        # Issues found
        if "analysis" in analysis and "issues" in analysis["analysis"] and analysis["analysis"]["issues"]:
            lines.append("### Issues Found")
            lines.append("")
            
            # Group issues by severity
            issues_by_severity = {}
            for issue in analysis["analysis"]["issues"]:
                severity = issue.get("severity", "unknown")
                if severity not in issues_by_severity:
                    issues_by_severity[severity] = []
                issues_by_severity[severity].append(issue)
            
            # Display issues by severity (critical first)
            for severity in ["critical", "high", "medium", "low"]:
                if severity in issues_by_severity:
                    severity_emoji = {
                        "critical": "🚨",
                        "high": "⚠️",
                        "medium": "💡",
                        "low": "ℹ️"
                    }
                    
                    lines.append(f"#### {severity_emoji.get(severity, '•')} {severity.title()} Priority")
                    lines.append("")
                    
                    for issue in issues_by_severity[severity]:
                        lines.append(f"**{issue.get('title', 'Issue')}**")
                        if issue.get('file_path'):
                            lines.append(f"*File: `{issue['file_path']}`*")
                        if issue.get('line_number'):
                            lines.append(f"*Line: {issue['line_number']}*")
                        lines.append("")
                        lines.append(issue.get('description', 'No description'))
                        
                        if issue.get('suggested_fix'):
                            lines.append("")
                            lines.append("**Suggested Fix:**")
                            lines.append(f"```")
                            lines.append(issue['suggested_fix'])
                            lines.append("```")
                        
                        lines.append("")
                        lines.append("---")
                        lines.append("")
            
        else:
            lines.append("### ✅ No Issues Found")
            lines.append("Great job! No significant issues detected in this PR.")
            lines.append("")
        
        # Metadata
        if "metadata" in analysis:
            lines.append("<details>")
            lines.append("<summary>Analysis Details</summary>")
            lines.append("")
            lines.append("- **Analysis Time:** {:.2f}s".format(analysis["metadata"].get("analysis_time_seconds", 0)))
            lines.append("- **Language:** {}".format(analysis["metadata"].get("language", "Unknown")))
            lines.append("- **Files Analyzed:** {}".format(analysis["analysis"].get("files_analyzed", 0)))
            lines.append("- **Generated:** {}".format(analysis["metadata"].get("analyzed_at", "Unknown")))
            lines.append("")
            lines.append("</details>")
        
        lines.append("")
        lines.append("*This review was generated by AI. Please review the suggestions and use your judgment.*")
        
        return "\n".join(lines)