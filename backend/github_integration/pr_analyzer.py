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
            
            # Fetch PR information
            pr_data = await self.github_client.get_pr_info(pr_info)
            
            # Fetch PR diff
            diff_content = await self.github_client.get_pr_diff(pr_info)
            
            # Fetch changed files
            files_data = await self.github_client.get_pr_files(pr_info)
            
            # Extract meaningful code changes for analysis
            analyzable_content = self._extract_code_changes(diff_content, files_data, language)
            
            # Run AI analysis on the changes
            if analyzable_content:
                issues, score, summary = await self.ai_orchestrator.analyze_code(
                    analyzable_content, 
                    language
                )
            else:
                # No analyzable code found
                issues = []
                score = 100
                summary = "No significant code changes found for analysis"
            
            # Calculate analysis time
            analysis_time = (datetime.now() - start_time).total_seconds()
            
            # Build comprehensive analysis result
            result = {
                "pr_info": {
                    "url": pr_url,
                    "repository": pr_info.full_repo,
                    "pr_number": pr_info.pr_number,
                    "title": pr_data.get("title", ""),
                    "description": pr_data.get("body", ""),
                    "author": pr_data.get("user", {}).get("login", ""),
                    "created_at": pr_data.get("created_at", ""),
                    "updated_at": pr_data.get("updated_at", ""),
                    "state": pr_data.get("state", ""),
                    "merged": pr_data.get("merged", False),
                    "mergeable": pr_data.get("mergeable"),
                    "base_branch": pr_data.get("base", {}).get("ref", ""),
                    "head_branch": pr_data.get("head", {}).get("ref", "")
                },
                "changes_summary": {
                    "files_changed": len(files_data),
                    "additions": pr_data.get("additions", 0),
                    "deletions": pr_data.get("deletions", 0),
                    "changed_files": [f["filename"] for f in files_data],
                    "file_types": self._categorize_file_changes(files_data)
                },
                "code_content": {
                    "diff": diff_content,
                    "extracted_code": analyzable_content,
                    "files_data": files_data
                },
                "analysis": {
                    "overall_score": score,
                    "issues": [self._format_issue(issue, file_data) for issue in issues],
                    "analysis_summary": summary,
                    "files_analyzed": len([f for f in files_data if self._should_analyze_file(f["filename"], language)]),
                    "total_lines_analyzed": len(analyzable_content.split('\n')) if analyzable_content else 0
                },
                "metadata": {
                    "analysis_time_seconds": analysis_time,
                    "analyzed_at": datetime.now().isoformat(),
                    "language": language,
                    "diff_size": len(diff_content)
                }
            }
            
            logger.info(
                f"Completed PR analysis: {len(issues)} issues found, "
                f"score: {score}, time: {analysis_time:.2f}s"
            )
            
            return result
            
        except GitHubAPIError as e:
            logger.error(f"GitHub API error during PR analysis: {e}")
            raise PRAnalysisError(f"Failed to fetch PR data: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during PR analysis: {e}")
            raise PRAnalysisError(f"Analysis failed: {str(e)}")
    
    def _extract_code_changes(self, diff_content: str, files_data: List[Dict], language: str) -> str:
        """Extract meaningful code changes from diff for AI analysis.
        
        Args:
            diff_content: Full PR diff content
            files_data: List of changed files
            language: Target programming language
            
        Returns:
            str: Extracted code content for analysis
        """
        # Filter files by language and relevance
        relevant_files = [f for f in files_data if self._should_analyze_file(f["filename"], language)]
        
        if not relevant_files:
            return ""
        
        # Extract added/modified lines from diff
        code_lines = []
        current_file = None
        
        for line in diff_content.split('\n'):
            # Track current file
            if line.startswith('diff --git'):
                current_file = line.split(' b/')[-1] if ' b/' in line else None
                continue
            
            # Skip if not a relevant file
            if current_file and not any(f["filename"] == current_file for f in relevant_files):
                continue
                
            # Extract added lines (starting with +) but skip diff metadata
            if line.startswith('+') and not line.startswith('+++'):
                code_lines.append(line[1:])  # Remove + prefix
            # Also include context lines for better analysis
            elif line.startswith(' '):
                code_lines.append(line[1:])  # Remove space prefix
        
        return '\n'.join(code_lines)
    
    def _should_analyze_file(self, filename: str, target_language: str) -> bool:
        """Check if file should be analyzed based on language and type.
        
        Args:
            filename: Name of the file
            target_language: Target programming language
            
        Returns:
            bool: True if file should be analyzed
        """
        # Language-specific file extensions
        language_extensions = {
            'python': ['.py', '.pyx', '.pyi'],
            'javascript': ['.js', '.jsx', '.mjs'],
            'typescript': ['.ts', '.tsx'],
            'java': ['.java'],
            'cpp': ['.cpp', '.cxx', '.cc', '.c++', '.c', '.h', '.hpp'],
            'csharp': ['.cs'],
            'go': ['.go'],
            'rust': ['.rs'],
            'php': ['.php', '.php3', '.php4', '.php5'],
            'ruby': ['.rb', '.rake']
        }
        
        # Skip non-code files
        skip_patterns = [
            r'\.md$', r'\.txt$', r'\.json$', r'\.xml$', r'\.yml$', r'\.yaml$',
            r'\.lock$', r'package-lock\.json$', r'yarn\.lock$', r'Pipfile\.lock$',
            r'\.gitignore$', r'\.dockerignore$', r'Dockerfile$', r'README',
            r'\.png$', r'\.jpg$', r'\.jpeg$', r'\.gif$', r'\.svg$', r'\.ico$'
        ]
        
        # Skip if matches skip patterns
        for pattern in skip_patterns:
            if re.search(pattern, filename, re.IGNORECASE):
                return False
        
        # Check for target language extensions
        target_exts = language_extensions.get(target_language, [])
        if target_exts:
            return any(filename.lower().endswith(ext) for ext in target_exts)
        
        # If no specific language, analyze common code files
        all_code_exts = [ext for exts in language_extensions.values() for ext in exts]
        return any(filename.lower().endswith(ext) for ext in all_code_exts)
    
    def _categorize_file_changes(self, files_data: List[Dict]) -> Dict[str, int]:
        """Categorize file changes by type.
        
        Args:
            files_data: List of changed files
            
        Returns:
            dict: Count of changes by file category
        """
        categories = {
            'source_code': 0,
            'tests': 0,
            'documentation': 0,
            'configuration': 0,
            'other': 0
        }
        
        for file_data in files_data:
            filename = file_data["filename"].lower()
            
            # Categorize files
            if any(test_pattern in filename for test_pattern in ['test', 'spec', '__test__']):
                categories['tests'] += 1
            elif filename.endswith(('.md', '.rst', '.txt', '.doc')):
                categories['documentation'] += 1
            elif filename.endswith(('.json', '.yml', '.yaml', '.toml', '.ini', '.cfg', '.conf')):
                categories['configuration'] += 1
            elif any(filename.endswith(ext) for ext in ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs', '.php', '.rb', '.cs']):
                categories['source_code'] += 1
            else:
                categories['other'] += 1
        
        return categories
    
    def _format_issue(self, issue: CodeIssue, file_context: Optional[Dict] = None) -> Dict[str, Any]:
        """Format an AI-generated issue for PR analysis output.
        
        Args:
            issue: Code issue from AI analysis
            file_context: Optional file context information
            
        Returns:
            dict: Formatted issue data
        """
        return {
            "title": issue.title,
            "description": issue.description,
            "severity": issue.severity,
            "category": issue.category,
            "line_number": issue.line_number,
            "code_snippet": issue.code_snippet,
            "suggested_fix": issue.suggested_fix,
            "fix_explanation": issue.fix_explanation,
            "file_path": file_context.get("filename") if file_context else None
        }