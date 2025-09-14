"""AI Agent system for code analysis and automatic fixing."""

import json
import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from openai import AzureOpenAI
import logging
from datetime import datetime
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import TerminalFormatter

logger = logging.getLogger(__name__)

@dataclass
class CodeIssue:
    """Represents a code issue found by AI analysis."""
    title: str
    description: str
    severity: str  # critical, high, medium, low
    category: str  # security, performance, quality, practices, maintainability
    line_number: Optional[int]
    code_snippet: Optional[str]
    suggested_fix: Optional[str]
    fix_explanation: Optional[str]

class AIAgent:
    """Base class for AI agents."""
    
    def __init__(self, name: str, description: str, azure_client: AzureOpenAI, model: str):
        self.name = name
        self.description = description
        self.azure_client = azure_client
        self.model = model
    
    async def analyze(self, code: str, language: str) -> List[CodeIssue]:
        """Analyze code and return issues. To be implemented by subclasses."""
        raise NotImplementedError
    
    async def _get_issues_from_ai(self, prompt: str) -> List[CodeIssue]:
        """Common method to get issues from AI and parse response."""
        try:
            # Call Azure OpenAI
            if "o4" in self.model or "o1" in self.model:
                response = self.azure_client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=1.0,
                    max_completion_tokens=2000
                )
            else:
                response = self.azure_client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=2000
                )
            
            ai_response = response.choices[0].message.content
            logger.info(f"AI response for {self.name}: {ai_response[:200]}...")
            
            # Parse JSON response
            issues_data = json.loads(ai_response)
            
            # Convert to CodeIssue objects
            issues = []
            for issue_data in issues_data:
                issue = CodeIssue(
                    title=issue_data.get("title", "Unknown Issue"),
                    description=issue_data.get("description", ""),
                    severity=issue_data.get("severity", "medium"),
                    category=issue_data.get("category", "quality"),
                    line_number=issue_data.get("line_number"),
                    code_snippet=issue_data.get("code_snippet"),
                    suggested_fix=issue_data.get("suggested_fix"),
                    fix_explanation=issue_data.get("fix_explanation")
                )
                issues.append(issue)
            
            return issues
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            return []
        except Exception as e:
            logger.error(f"Error in {self.name}: {e}")
            return []

class SecurityAgent(AIAgent):
    """Agent specialized in security vulnerability detection."""
    
    def __init__(self, azure_client: AzureOpenAI, model: str):
        super().__init__(
            "Security Analysis Agent",
            "Advanced vulnerability detection and security flaw identification",
            azure_client,
            model
        )
    
    async def analyze(self, code: str, language: str) -> List[CodeIssue]:
        """Analyze code for security issues."""
        prompt = f"""You are a cybersecurity expert analyzing {language} code for security vulnerabilities.

Analyze this code and identify security issues. For each issue found, provide EXACTLY this JSON format:

{{
    "title": "Brief issue title",
    "description": "Detailed description of the security vulnerability",
    "severity": "critical|high|medium|low",
    "category": "security",
    "line_number": line_number_or_null,
    "code_snippet": "problematic code snippet",
    "suggested_fix": "corrected code",
    "fix_explanation": "explanation of the fix"
}}

Return ONLY a JSON array of issues, no other text.

Code to analyze:
```{language}
{code}
```"""

        return await self._get_issues_from_ai(prompt)

class PerformanceAgent(AIAgent):
    """Agent specialized in performance optimization."""
    
    def __init__(self, azure_client: AzureOpenAI, model: str):
        super().__init__(
            "Performance Optimization Agent",
            "Intelligent bottleneck identification and algorithmic efficiency optimization",
            azure_client,
            model
        )
    
    async def analyze(self, code: str, language: str) -> List[CodeIssue]:
        """Analyze code for performance issues."""
        prompt = f"""You are a performance optimization expert analyzing {language} code.

Analyze this code for performance issues, bottlenecks, and optimization opportunities. For each issue found, provide EXACTLY this JSON format:

{{
    "title": "Brief issue title",
    "description": "Detailed description of the performance issue",
    "severity": "critical|high|medium|low",
    "category": "performance",
    "line_number": line_number_or_null,
    "code_snippet": "problematic code snippet",
    "suggested_fix": "optimized code",
    "fix_explanation": "explanation of the performance improvement"
}}

Return ONLY a JSON array of issues, no other text.

Code to analyze:
```{language}
{code}
```"""

        return await self._get_issues_from_ai(prompt)

class QualityAgent(AIAgent):
    """Agent specialized in code quality assessment."""
    
    def __init__(self, azure_client: AzureOpenAI, model: str):
        super().__init__(
            "Code Quality Agent",
            "Comprehensive structure analysis and coding standards adherence",
            azure_client,
            model
        )
    
    async def analyze(self, code: str, language: str) -> List[CodeIssue]:
        """Analyze code for quality issues."""
        prompt = f"""You are a code quality expert analyzing {language} code for quality issues.

Analyze this code for quality problems like code smells, poor structure, naming issues, complexity, etc. For each issue found, provide EXACTLY this JSON format:

{{
    "title": "Brief issue title",
    "description": "Detailed description of the quality issue",
    "severity": "critical|high|medium|low",
    "category": "quality",
    "line_number": line_number_or_null,
    "code_snippet": "problematic code snippet",
    "suggested_fix": "improved code",
    "fix_explanation": "explanation of the quality improvement"
}}

Return ONLY a JSON array of issues, no other text.

Code to analyze:
```{language}
{code}
```"""

        return await self._get_issues_from_ai(prompt)

class BestPracticesAgent(AIAgent):
    """Agent specialized in best practices compliance."""
    
    def __init__(self, azure_client: AzureOpenAI, model: str):
        super().__init__(
            "Best Practices Agent",
            "Industry-standard pattern recognition and architectural recommendations",
            azure_client,
            model
        )
    
    async def analyze(self, code: str, language: str) -> List[CodeIssue]:
        """Analyze code for best practices violations."""
        prompt = f"""You are a software architecture expert analyzing {language} code for best practices compliance.

Analyze this code for violations of {language} best practices, design patterns, and industry standards. For each issue found, provide EXACTLY this JSON format:

{{
    "title": "Brief issue title",
    "description": "Detailed description of the best practice violation",
    "severity": "critical|high|medium|low",
    "category": "practices",
    "line_number": line_number_or_null,
    "code_snippet": "problematic code snippet",
    "suggested_fix": "code following best practices",
    "fix_explanation": "explanation of the best practice"
}}

Return ONLY a JSON array of issues, no other text.

Code to analyze:
```{language}
{code}
```"""

        return await self._get_issues_from_ai(prompt)

class MaintainabilityAgent(AIAgent):
    """Agent specialized in maintainability assessment."""
    
    def __init__(self, azure_client: AzureOpenAI, model: str):
        super().__init__(
            "Maintainability Agent",
            "Long-term sustainability analysis and modular design assessment",
            azure_client,
            model
        )
    
    async def analyze(self, code: str, language: str) -> List[CodeIssue]:
        """Analyze code for maintainability issues."""
        prompt = f"""You are a software maintainability expert analyzing {language} code.

Analyze this code for maintainability issues like tight coupling, lack of documentation, hard-to-understand logic, etc. For each issue found, provide EXACTLY this JSON format:

{{
    "title": "Brief issue title",
    "description": "Detailed description of the maintainability issue",
    "severity": "critical|high|medium|low",
    "category": "maintainability",
    "line_number": line_number_or_null,
    "code_snippet": "problematic code snippet",
    "suggested_fix": "more maintainable code",
    "fix_explanation": "explanation of the maintainability improvement"
}}

Return ONLY a JSON array of issues, no other text.

Code to analyze:
```{language}
{code}
```"""

        return await self._get_issues_from_ai(prompt)

class AIAgentOrchestrator:
    """Orchestrates multiple AI agents for comprehensive code analysis."""
    
    def __init__(self, azure_client: AzureOpenAI, model: str):
        self.azure_client = azure_client
        self.model = model
        
        # Initialize all agents
        self.agents = [
            SecurityAgent(azure_client, model),
            PerformanceAgent(azure_client, model),
            QualityAgent(azure_client, model),
            BestPracticesAgent(azure_client, model),
            MaintainabilityAgent(azure_client, model)
        ]
    
    async def analyze_code(self, code: str, language: str) -> Tuple[List[CodeIssue], int, str]:
        """Run all agents and return comprehensive analysis."""
        start_time = datetime.now()
        
        logger.info(f"Starting comprehensive analysis with {len(self.agents)} agents")
        
        all_issues = []
        agent_results = {}
        
        # Run all agents
        for agent in self.agents:
            try:
                logger.info(f"Running {agent.name}")
                issues = await agent.analyze(code, language)
                all_issues.extend(issues)
                agent_results[agent.name] = len(issues)
                logger.info(f"{agent.name} found {len(issues)} issues")
            except Exception as e:
                logger.error(f"Error running {agent.name}: {e}")
                agent_results[agent.name] = 0
        
        # Calculate overall score
        overall_score = self._calculate_score(all_issues)
        
        # Generate summary
        analysis_time = (datetime.now() - start_time).seconds
        summary = self._generate_summary(all_issues, agent_results, analysis_time)
        
        logger.info(f"Analysis complete: {len(all_issues)} issues found, score: {overall_score}")
        
        return all_issues, overall_score, summary
    
    def _calculate_score(self, issues: List[CodeIssue]) -> int:
        """Calculate overall code quality score."""
        if not issues:
            return 100
        
        # Penalty weights by severity
        penalties = {
            'critical': 25,
            'high': 15,
            'medium': 10,
            'low': 5
        }
        
        total_penalty = 0
        for issue in issues:
            total_penalty += penalties.get(issue.severity, 5)
        
        # Cap the penalty to ensure score doesn't go below 0
        score = max(0, 100 - total_penalty)
        return score
    
    def _generate_summary(self, issues: List[CodeIssue], agent_results: Dict, analysis_time: int) -> str:
        """Generate human-readable analysis summary."""
        severity_counts = {
            'critical': len([i for i in issues if i.severity == 'critical']),
            'high': len([i for i in issues if i.severity == 'high']),
            'medium': len([i for i in issues if i.severity == 'medium']),
            'low': len([i for i in issues if i.severity == 'low'])
        }
        
        category_counts = {}
        for issue in issues:
            category_counts[issue.category] = category_counts.get(issue.category, 0) + 1
        
        summary = f"""
        Code Analysis Summary
        ====================
        
        Total Issues Found: {len(issues)}
        Analysis Time: {analysis_time} seconds
        
        Issues by Severity:
        - Critical: {severity_counts['critical']}
        - High: {severity_counts['high']}
        - Medium: {severity_counts['medium']}
        - Low: {severity_counts['low']}
        
        Issues by Category:
        """
        
        for category, count in category_counts.items():
            summary += f"- {category.title()}: {count}\n        "
        
        summary += f"""
        Agent Results:
        """
        
        for agent_name, count in agent_results.items():
            summary += f"- {agent_name}: {count} issues\n        "
        
        return summary.strip()

class CodeFixerAgent:
    """Agent responsible for applying fixes to code."""
    
    def __init__(self, azure_client: AzureOpenAI, model: str):
        self.azure_client = azure_client
        self.model = model
    
    async def apply_fix(self, original_code: str, issue: CodeIssue, language: str) -> Tuple[str, bool]:
        """Apply a fix to code and return the updated code."""
        if not issue.suggested_fix:
            return original_code, False
        
        try:
            # If we have a line number, try to replace specific lines
            if issue.line_number and issue.code_snippet:
                lines = original_code.split('\n')
                
                # Find the problematic line(s)
                for i, line in enumerate(lines):
                    if issue.code_snippet.strip() in line.strip():
                        # Apply the fix
                        lines[i] = issue.suggested_fix
                        return '\n'.join(lines), True
            
            # If no specific line match, use AI to apply the fix contextually
            prompt = f"""Apply the following fix to the {language} code:

Original Code:
```{language}
{original_code}
```

Issue: {issue.title}
Description: {issue.description}
Suggested Fix: {issue.suggested_fix}

Please return ONLY the complete corrected code, nothing else."""

            if "o4" in self.model or "o1" in self.model:
                response = self.azure_client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=1.0,
                    max_completion_tokens=4000
                )
            else:
                response = self.azure_client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=4000
                )
            
            fixed_code = response.choices[0].message.content
            
            # Clean up the response (remove code block markers if present)
            fixed_code = re.sub(r'^```\w*\n', '', fixed_code, flags=re.MULTILINE)
            fixed_code = re.sub(r'\n```$', '', fixed_code)
            
            return fixed_code.strip(), True
            
        except Exception as e:
            logger.error(f"Error applying fix: {e}")
            return original_code, False

def create_ai_orchestrator(azure_client: AzureOpenAI, model: str) -> AIAgentOrchestrator:
    """Factory function to create AI orchestrator."""
    return AIAgentOrchestrator(azure_client, model)

def create_code_fixer(azure_client: AzureOpenAI, model: str) -> CodeFixerAgent:
    """Factory function to create code fixer agent."""
    return CodeFixerAgent(azure_client, model)