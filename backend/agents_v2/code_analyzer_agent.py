"""Code quality analysis agent using Pydantic AI."""

import re
import uuid
from typing import List, Dict, Any
from datetime import datetime

from .base_agent import BaseCodeAgent
from pydantic_ai import RunContext
from .models import (
    CodeContext,
    CodeIssue,
    CodeLocation,
    SeverityLevel,
    IssueCategory
)


class CodeAnalyzerAgent(BaseCodeAgent):
    """Agent specialized in code quality analysis."""
    
    def __init__(self, azure_client=None, model_name=None):
        """Initialize code analyzer agent."""
        super().__init__(
            name="Code Quality Analyzer",
            description="Analyzes code structure, naming conventions, complexity, and maintainability",
            azure_client=azure_client,
            model_name=model_name
        )
        
    def _register_tools(self):
        """Register code analysis specific tools."""
        super()._register_tools()
        
        @self.agent.tool
        async def check_naming_conventions(ctx: RunContext[Any], code: str, language: str) -> List[Dict[str, Any]]:
            """Check naming conventions in code.
            
            Args:
                code: Code to analyze
                language: Programming language
                
            Returns:
                List of naming issues
            """
            issues = []
            lines = code.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                # Check for Python naming conventions
                if language == "python":
                    # Check for camelCase in function names (should be snake_case)
                    if re.search(r'def\s+[a-z][a-zA-Z]+\(', line):
                        func_match = re.search(r'def\s+([a-z][a-zA-Z]+)\(', line)
                        if func_match:
                            issues.append({
                                "line": line_num,
                                "issue": f"Function '{func_match.group(1)}' should use snake_case",
                                "severity": "low"
                            })
                    
                    # Check for lowercase class names (should be PascalCase)
                    if re.search(r'class\s+[a-z][a-z_]*\s*[\(:]', line):
                        class_match = re.search(r'class\s+([a-z][a-z_]*)\s*[\(:]', line)
                        if class_match:
                            issues.append({
                                "line": line_num,
                                "issue": f"Class '{class_match.group(1)}' should use PascalCase",
                                "severity": "medium"
                            })
                    
                    # Check for UPPERCASE variables that aren't constants
                    if not line.strip().startswith('#') and '=' in line:
                        var_match = re.search(r'^([A-Z_]+)\s*=', line.strip())
                        if var_match and line_num > 10:  # Skip early constants
                            issues.append({
                                "line": line_num,
                                "issue": f"Variable '{var_match.group(1)}' appears to be a constant, consider moving to module level",
                                "severity": "low"
                            })
            
            return issues
        
        @self.agent.tool
        async def detect_code_smells(ctx: RunContext[Any], code: str) -> List[Dict[str, Any]]:
            """Detect common code smells.
            
            Args:
                code: Code to analyze
                
            Returns:
                List of code smells detected
            """
            smells = []
            lines = code.split('\n')
            
            # Check for long functions
            in_function = False
            function_start = 0
            function_name = ""
            
            for line_num, line in enumerate(lines, 1):
                if re.search(r'def\s+\w+\s*\(', line):
                    if in_function and line_num - function_start > 50:
                        smells.append({
                            "type": "long_function",
                            "function": function_name,
                            "lines": line_num - function_start,
                            "severity": "medium"
                        })
                    func_match = re.search(r'def\s+(\w+)\s*\(', line)
                    if func_match:
                        in_function = True
                        function_start = line_num
                        function_name = func_match.group(1)
            
            # Check for duplicate code patterns
            code_blocks = {}
            for i in range(len(lines) - 3):
                block = '\n'.join(lines[i:i+4])
                if len(block) > 50:  # Only consider substantial blocks
                    if block in code_blocks:
                        smells.append({
                            "type": "duplicate_code",
                            "lines": f"{code_blocks[block]} and {i+1}",
                            "severity": "medium"
                        })
                    else:
                        code_blocks[block] = i + 1
            
            # Check for deeply nested code
            for line_num, line in enumerate(lines, 1):
                indent_level = len(line) - len(line.lstrip())
                if indent_level > 16:  # More than 4 levels of indentation
                    smells.append({
                        "type": "deep_nesting",
                        "line": line_num,
                        "severity": "medium"
                    })
            
            return smells
        
        @self.agent.tool
        async def analyze_complexity(ctx: RunContext[Any], code: str) -> Dict[str, Any]:
            """Analyze code complexity metrics.
            
            Args:
                code: Code to analyze
                
            Returns:
                Complexity metrics
            """
            lines = code.split('\n')
            
            # Count various metrics
            metrics = {
                "total_lines": len(lines),
                "code_lines": len([l for l in lines if l.strip() and not l.strip().startswith('#')]),
                "comment_lines": len([l for l in lines if l.strip().startswith('#')]),
                "blank_lines": len([l for l in lines if not l.strip()]),
                "functions": len(re.findall(r'def\s+\w+\s*\(', code)),
                "classes": len(re.findall(r'class\s+\w+', code)),
                "imports": len(re.findall(r'^import\s+|^from\s+.*import', code, re.MULTILINE)),
                "complexity_score": 0
            }
            
            # Calculate complexity score
            complexity = 1
            for keyword in ['if', 'elif', 'else', 'for', 'while', 'except', 'with']:
                complexity += len(re.findall(f'\\b{keyword}\\b', code))
            
            metrics["complexity_score"] = complexity
            
            # Determine complexity level
            if complexity < 10:
                metrics["complexity_level"] = "simple"
            elif complexity < 20:
                metrics["complexity_level"] = "moderate"
            else:
                metrics["complexity_level"] = "complex"
            
            return metrics
    
    async def _perform_analysis(self, context: CodeContext) -> List[CodeIssue]:
        """Perform code quality analysis.
        
        Args:
            context: Code context to analyze
            
        Returns:
            List of code quality issues
        """
        issues = []
        
        # Check naming conventions
        naming_issues = await self.agent.tools.check_naming_conventions(
            context.code, context.language
        )
        
        for issue_data in naming_issues:
            issues.append(CodeIssue(
                id=str(uuid.uuid4()),
                title="Naming Convention Violation",
                description=issue_data["issue"],
                severity=SeverityLevel(issue_data["severity"]),
                category=IssueCategory.STYLE,
                location=CodeLocation(
                    file_path=context.file_path or "unknown",
                    line_start=issue_data["line"],
                    line_end=issue_data["line"]
                ),
                confidence=0.9,
                detected_by=self.name
            ))
        
        # Detect code smells
        code_smells = await self.agent.tools.detect_code_smells(context.code)
        
        for smell in code_smells:
            if smell["type"] == "long_function":
                issues.append(CodeIssue(
                    id=str(uuid.uuid4()),
                    title="Long Function Detected",
                    description=f"Function '{smell['function']}' is {smell['lines']} lines long. Consider breaking it into smaller functions.",
                    severity=SeverityLevel(smell["severity"]),
                    category=IssueCategory.MAINTAINABILITY,
                    confidence=0.8,
                    detected_by=self.name
                ))
            elif smell["type"] == "duplicate_code":
                issues.append(CodeIssue(
                    id=str(uuid.uuid4()),
                    title="Duplicate Code Detected",
                    description=f"Similar code blocks found at lines {smell['lines']}. Consider extracting to a function.",
                    severity=SeverityLevel(smell["severity"]),
                    category=IssueCategory.MAINTAINABILITY,
                    confidence=0.7,
                    detected_by=self.name
                ))
            elif smell["type"] == "deep_nesting":
                issues.append(CodeIssue(
                    id=str(uuid.uuid4()),
                    title="Deep Nesting",
                    description=f"Deeply nested code at line {smell['line']}. Consider refactoring to reduce complexity.",
                    severity=SeverityLevel(smell["severity"]),
                    category=IssueCategory.QUALITY,
                    location=CodeLocation(
                        file_path=context.file_path or "unknown",
                        line_start=smell["line"],
                        line_end=smell["line"]
                    ),
                    confidence=0.85,
                    detected_by=self.name
                ))
        
        # Analyze complexity
        complexity_metrics = await self.agent.tools.analyze_complexity(context.code)
        
        if complexity_metrics["complexity_level"] == "complex":
            issues.append(CodeIssue(
                id=str(uuid.uuid4()),
                title="High Code Complexity",
                description=f"Code has high cyclomatic complexity ({complexity_metrics['complexity_score']}). Consider simplifying logic.",
                severity=SeverityLevel.MEDIUM,
                category=IssueCategory.MAINTAINABILITY,
                confidence=0.75,
                detected_by=self.name
            ))
        
        # Check for missing documentation
        if complexity_metrics["functions"] > 0 and complexity_metrics["comment_lines"] < complexity_metrics["functions"]:
            issues.append(CodeIssue(
                id=str(uuid.uuid4()),
                title="Insufficient Documentation",
                description=f"Found {complexity_metrics['functions']} functions but only {complexity_metrics['comment_lines']} comment lines. Add docstrings.",
                severity=SeverityLevel.LOW,
                category=IssueCategory.BEST_PRACTICES,
                confidence=0.6,
                detected_by=self.name
            ))
        
        return issues