"""PR analyzer that integrates GitHub data with existing AI agents."""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from .authenticated_client import GitHubClient, GitHubAPIError
from .url_parser import GitHubURLParser, GitHubPRInfo
from ai_agents import AIAgentOrchestrator, CodeIssue

logger = logging.getLogger(__name__)

class PRAnalysisError(Exception):
    """Custom exception for PR analysis errors."""
    pass

class PRAnalyzer:
    """Analyzer that fetches GitHub PR data and runs AI analysis."""
    
    def __init__(self, github_client: GitHubClient, ai_orchestrator: AIAgentOrchestrator):
        """Initialize PR analyzer.
        
        Args:
            github_client: Authenticated GitHub client
            ai_orchestrator: AI agent orchestrator for code analysis
        """
        self.github_client = github_client
        self.ai_orchestrator = ai_orchestrator
    
    async def analyze_pr(self, pr_url: str, language: str) -> Dict[str, Any]:
        """Analyze a GitHub Pull Request.
        
        Args:
            pr_url: GitHub PR URL
            language: Programming language for analysis
            
        Returns:
            dict: Complete PR analysis results
        """
        start_time = datetime.now()
        
        try:
            # Parse PR URL
            pr_info = GitHubURLParser.parse_pr_url(pr_url)
            if not pr_info:
                raise PRAnalysisError(f"Invalid GitHub PR URL: {pr_url}")
            
            logger.info(f"Starting analysis for PR {pr_info.full_repo}#{pr_info.pr_number}")
            
            # Fetch PR data from GitHub
            pr_data = await self._fetch_pr_data(pr_info)
            
            # Extract and analyze code changes
            analysis_results = await self._analyze_pr_changes(pr_info, pr_data, language)
            
            # Calculate analysis time
            analysis_time = (datetime.now() - start_time).total_seconds()
            
            # Combine all results
            complete_analysis = {
                "pr_info": {
                    "url": pr_url,
                    "repository": pr_info.full_repo,
                    "pr_number": pr_info.pr_number,
                    "title": pr_data["title"],
                    "description": pr_data["body"],
                    "author": pr_data["user"]["login"],
                    "created_at": pr_data["created_at"],
                    "state": pr_data["state"]
                },
                "changes_summary": {
                    "files_changed": len(pr_data["files"]),
                    "additions": pr_data["additions"],
                    "deletions": pr_data["deletions"],
                    "changed_files": [f["filename"] for f in pr_data["files"]]
                },
                "analysis": analysis_results,
                "metadata": {
                    "analyzed_at": datetime.now().isoformat(),
                    "analysis_time_seconds": int(analysis_time),
                    "language": language
                }
            }
            
            logger.info(f"PR analysis completed in {analysis_time:.2f}s")
            return complete_analysis
            
        except GitHubAPIError as e:
            logger.error(f"GitHub API error during PR analysis: {e}")
            raise PRAnalysisError(f"GitHub API error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during PR analysis: {e}")
            raise PRAnalysisError(f"Analysis failed: {str(e)}")
    
    async def _fetch_pr_data(self, pr_info: GitHubPRInfo) -> Dict[str, Any]:
        """Fetch comprehensive PR data from GitHub.
        
        Args:
            pr_info: Parsed PR information
            
        Returns:
            dict: Combined PR data including files and metadata
        """
        # Fetch PR information and files in parallel
        import asyncio
        
        pr_data, files_data = await asyncio.gather(
            self.github_client.get_pr_info(pr_info),
            self.github_client.get_pr_files(pr_info)
        )
        
        # Add files data to PR data
        pr_data["files"] = files_data
        
        # Calculate total additions/deletions
        pr_data["additions"] = sum(file.get("additions", 0) for file in files_data)
        pr_data["deletions"] = sum(file.get("deletions", 0) for file in files_data)
        
        return pr_data
    
    async def _analyze_pr_changes(self, pr_info: GitHubPRInfo, pr_data: Dict[str, Any], language: str) -> Dict[str, Any]:
        """Analyze the code changes in the PR using AI agents.
        
        Args:
            pr_info: PR information
            pr_data: GitHub PR data including files
            language: Programming language
            
        Returns:
            dict: AI analysis results
        """
        # Filter files to analyze (exclude non-code files)
        analyzable_files = self._filter_analyzable_files(pr_data["files"], language)
        
        if not analyzable_files:
            logger.warning(f"No analyzable files found for language {language}")
            return {
                "overall_score": 100,
                "issues": [],
                "analysis_summary": f"No {language} files found to analyze in this PR.",
                "files_analyzed": 0
            }
        
        # Extract code changes for analysis
        code_changes = await self._extract_code_changes(pr_info, analyzable_files)
        
        # Run AI analysis on the combined changes
        all_issues = []
        total_score = 0
        files_analyzed = 0
        
        for file_path, file_content in code_changes.items():
            try:
                # Run AI orchestrator on this file's changes
                file_issues, file_score, file_summary = await self.ai_orchestrator.analyze_code(
                    file_content, language
                )
                
                # Add file path to each issue
                for issue in file_issues:
                    issue.file_path = file_path
                
                all_issues.extend(file_issues)
                total_score += file_score
                files_analyzed += 1
                
                logger.info(f"Analyzed {file_path}: {len(file_issues)} issues, score {file_score}")
                
            except Exception as e:
                logger.error(f"Failed to analyze {file_path}: {e}")
                # Continue with other files
                continue
        
        # Calculate overall score
        overall_score = total_score // max(files_analyzed, 1) if files_analyzed > 0 else 100
        
        # Generate summary
        analysis_summary = self._generate_pr_summary(all_issues, files_analyzed, pr_data)
        
        return {
            "overall_score": overall_score,
            "issues": [self._issue_to_dict(issue) for issue in all_issues],
            "analysis_summary": analysis_summary,
            "files_analyzed": files_analyzed
        }
    
    def _filter_analyzable_files(self, files: List[Dict[str, Any]], language: str) -> List[Dict[str, Any]]:
        """Filter files that can be analyzed for the given language.
        
        Args:
            files: List of changed files from GitHub
            language: Target programming language
            
        Returns:
            list: Filtered list of analyzable files
        """
        # Language file extensions mapping
        language_extensions = {
            "python": [".py", ".pyx", ".pyw"],
            "javascript": [".js", ".jsx", ".mjs"],
            "typescript": [".ts", ".tsx"],
            "java": [".java"],
            "cpp": [".cpp", ".cc", ".cxx", ".c++", ".h", ".hpp"],
            "c": [".c", ".h"],
            "csharp": [".cs"],
            "go": [".go"],
            "rust": [".rs"],
            "php": [".php"],
            "ruby": [".rb"]
        }
        
        extensions = language_extensions.get(language.lower(), [])
        if not extensions:
            logger.warning(f"No known extensions for language: {language}")
            return files  # Return all files if language not recognized
        
        analyzable_files = []
        for file in files:
            filename = file["filename"].lower()
            
            # Check if file has relevant extension
            if any(filename.endswith(ext) for ext in extensions):
                # Skip deleted files
                if file["status"] != "removed":
                    # Skip binary files and very large files
                    if file.get("changes", 0) <= 1000:  # Limit to reasonable size
                        analyzable_files.append(file)
        
        logger.info(f"Filtered {len(analyzable_files)} analyzable files from {len(files)} total files")
        return analyzable_files
    
    async def _extract_code_changes(self, pr_info: GitHubPRInfo, files: List[Dict[str, Any]]) -> Dict[str, str]:
        """Extract the actual code changes from files.
        
        Args:
            pr_info: PR information
            files: List of files to analyze
            
        Returns:
            dict: Mapping of file_path -> code_content
        """
        code_changes = {}
        
        for file in files:
            file_path = file["filename"]
            
            try:
                if file["status"] == "added":
                    # For new files, get the entire content
                    content = await self.github_client.get_file_content(
                        pr_info.owner, pr_info.repo, file_path, "HEAD"
                    )
                elif file["status"] == "modified":
                    # For modified files, we could get just the patch or the full content
                    # For simplicity, we'll analyze the current content
                    # In a more sophisticated implementation, we'd analyze just the changes
                    content = await self.github_client.get_file_content(
                        pr_info.owner, pr_info.repo, file_path, "HEAD"
                    )
                else:
                    # Skip renamed/deleted files for now
                    continue
                
                code_changes[file_path] = content
                
            except GitHubAPIError as e:
                logger.warning(f"Failed to fetch content for {file_path}: {e}")
                # Use patch content as fallback if available
                if "patch" in file and file["patch"]:
                    code_changes[file_path] = self._extract_code_from_patch(file["patch"])
        
        return code_changes
    
    def _extract_code_from_patch(self, patch: str) -> str:
        """Extract code lines from a git patch.
        
        Args:
            patch: Git patch content
            
        Returns:
            str: Extracted code content
        """
        lines = []
        for line in patch.split('\n'):
            # Extract lines that are added (start with +) or context (no prefix)
            if line.startswith('+') and not line.startswith('+++'):
                lines.append(line[1:])  # Remove + prefix
            elif not line.startswith('-') and not line.startswith('@@') and not line.startswith('+++') and not line.startswith('---'):
                lines.append(line)
        
        return '\n'.join(lines)
    
    def _generate_pr_summary(self, issues: List[CodeIssue], files_analyzed: int, pr_data: Dict[str, Any]) -> str:
        """Generate human-readable summary of PR analysis.
        
        Args:
            issues: List of found issues
            files_analyzed: Number of files analyzed
            pr_data: GitHub PR data
            
        Returns:
            str: Analysis summary
        """
        # Count issues by severity
        severity_counts = {
            'critical': len([i for i in issues if i.severity == 'critical']),
            'high': len([i for i in issues if i.severity == 'high']),
            'medium': len([i for i in issues if i.severity == 'medium']),
            'low': len([i for i in issues if i.severity == 'low'])
        }
        
        # Count issues by category
        category_counts = {}
        for issue in issues:
            category_counts[issue.category] = category_counts.get(issue.category, 0) + 1
        
        summary_lines = [
            f"Pull Request Analysis for #{pr_data.get('number', '?')}: {pr_data.get('title', 'Untitled')}",
            f"Files analyzed: {files_analyzed}/{len(pr_data.get('files', []))}",
            f"Total changes: +{pr_data.get('additions', 0)} -{pr_data.get('deletions', 0)}",
            "",
            f"Issues found: {len(issues)}"
        ]
        
        if severity_counts:
            severity_parts = []
            for severity in ['critical', 'high', 'medium', 'low']:
                count = severity_counts[severity]
                if count > 0:
                    severity_parts.append(f"{count} {severity}")
            
            if severity_parts:
                summary_lines.append(f"  By severity: {', '.join(severity_parts)}")
        
        if category_counts:
            category_parts = [f"{count} {category}" for category, count in category_counts.items()]
            summary_lines.append(f"  By category: {', '.join(category_parts)}")
        
        if not issues:
            summary_lines.append("No significant issues found. Code quality looks good!")
        elif severity_counts.get('critical', 0) > 0:
            summary_lines.append("⚠️ Critical issues found that should be addressed before merging.")
        elif severity_counts.get('high', 0) > 0:
            summary_lines.append("⚠️ High-priority issues found that should be reviewed.")
        else:
            summary_lines.append("Minor issues found. Consider addressing for better code quality.")
        
        return '\n'.join(summary_lines)
    
    def _issue_to_dict(self, issue: CodeIssue) -> Dict[str, Any]:
        """Convert CodeIssue to dictionary for API response.
        
        Args:
            issue: CodeIssue object
            
        Returns:
            dict: Issue data
        """
        return {
            "title": issue.title,
            "description": issue.description,
            "severity": issue.severity,
            "category": issue.category,
            "file_path": getattr(issue, 'file_path', None),
            "line_number": issue.line_number,
            "code_snippet": issue.code_snippet,
            "suggested_fix": issue.suggested_fix,
            "fix_explanation": issue.fix_explanation
        }