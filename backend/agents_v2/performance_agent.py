"""Performance optimization agent using Pydantic AI."""

import re
import uuid
from typing import List, Dict, Any

from pydantic_ai import RunContext
from typing import Any

from .base_agent import BaseCodeAgent
from .models import (
    CodeContext,
    CodeIssue,
    CodeLocation,
    SeverityLevel,
    IssueCategory
)


class PerformanceAnalysisAgent(BaseCodeAgent):
    """Agent specialized in performance optimization."""
    
    def __init__(self, async_azure_client=None, model_name=None):
        """Initialize performance analysis agent."""
        super().__init__(
            name="Performance Optimizer",
            description="Identifies performance bottlenecks, inefficient algorithms, and optimization opportunities",
            async_azure_client=async_azure_client,
            model_name=model_name
        )
        
    def _register_tools(self):
        """Register performance analysis specific tools."""
        super()._register_tools()
        
        @self.agent.tool
        async def detect_inefficient_loops(ctx: RunContext[Any], code: str) -> List[Dict[str, Any]]:
            """Detect inefficient loop patterns.
            
            Args:
                code: Code to analyze
                
            Returns:
                List of inefficient loops
            """
            issues = []
            lines = code.split('\n')
            
            # Patterns for inefficient loops
            patterns = [
                (r'for.*in.*range\(len\(', "Using range(len()) instead of enumerate()", "medium"),
                (r'\.append\(.*\).*for.*in', "List append in loop instead of list comprehension", "low"),
                (r'for.*in.*\.keys\(\)', "Iterating over .keys() unnecessarily", "low"),
                (r'for.*in.*\.items\(\).*\[0\]|\[1\]', "Unpacking items inefficiently", "low"),
                (r'while.*len\(.*\).*>', "Inefficient while loop with len() check", "medium"),
            ]
            
            for line_num, line in enumerate(lines, 1):
                for pattern, description, severity in patterns:
                    if re.search(pattern, line):
                        issues.append({
                            "line": line_num,
                            "description": description,
                            "code": line.strip(),
                            "severity": severity
                        })
            
            # Check for nested loops (O(n²) or worse)
            indent_stack = []
            for line_num, line in enumerate(lines, 1):
                if 'for ' in line or 'while ' in line:
                    indent = len(line) - len(line.lstrip())
                    # Check if this is a nested loop
                    if indent_stack and indent > indent_stack[-1]:
                        issues.append({
                            "line": line_num,
                            "description": "Nested loop detected - potential O(n²) complexity",
                            "code": line.strip(),
                            "severity": "high"
                        })
                    indent_stack.append(indent)
                elif not line.strip():
                    indent_stack = []
            
            return issues
        
        @self.agent.tool
        async def detect_database_issues(ctx: RunContext[Any], code: str) -> List[Dict[str, Any]]:
            """Detect database performance issues.
            
            Args:
                code: Code to analyze
                
            Returns:
                List of database performance issues
            """
            issues = []
            lines = code.split('\n')
            
            # N+1 query pattern detection
            in_loop = False
            loop_indent = 0
            
            for line_num, line in enumerate(lines, 1):
                current_indent = len(line) - len(line.lstrip())
                
                # Check if we're entering a loop
                if 'for ' in line or 'while ' in line:
                    in_loop = True
                    loop_indent = current_indent
                elif in_loop and current_indent <= loop_indent:
                    in_loop = False
                
                # Check for queries inside loops
                if in_loop and any(keyword in line for keyword in ['SELECT', 'query', 'execute', 'fetch', 'find', 'get']):
                    issues.append({
                        "line": line_num,
                        "type": "n_plus_one",
                        "description": "Database query inside loop - potential N+1 problem",
                        "severity": "high"
                    })
                
                # Check for missing indexes
                if 'WHERE' in line and not any(idx in line for idx in ['id', 'pk', 'primary']):
                    issues.append({
                        "line": line_num,
                        "type": "missing_index",
                        "description": "Query without apparent index usage",
                        "severity": "medium"
                    })
                
                # Check for SELECT *
                if re.search(r'SELECT\s+\*', line, re.IGNORECASE):
                    issues.append({
                        "line": line_num,
                        "type": "select_all",
                        "description": "SELECT * can fetch unnecessary data",
                        "severity": "low"
                    })
            
            return issues
        
        @self.agent.tool
        async def detect_memory_issues(ctx: RunContext[Any], code: str) -> List[Dict[str, Any]]:
            """Detect potential memory issues.
            
            Args:
                code: Code to analyze
                
            Returns:
                List of memory-related issues
            """
            issues = []
            lines = code.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                # Large data structure creation
                if re.search(r'=\s*\[\s*\].*for.*in.*range\([0-9]{4,}', line):
                    issues.append({
                        "line": line_num,
                        "description": "Creating large list - consider generator",
                        "severity": "high"
                    })
                
                # Reading entire file into memory
                if re.search(r'\.read\(\)|\.readlines\(\)', line):
                    issues.append({
                        "line": line_num,
                        "description": "Reading entire file into memory - consider streaming",
                        "severity": "medium"
                    })
                
                # String concatenation in loops
                if '+=' in line and ('"' in line or "'" in line):
                    # Check if in loop context
                    if line_num > 1 and any(keyword in lines[line_num-2] for keyword in ['for', 'while']):
                        issues.append({
                            "line": line_num,
                            "description": "String concatenation in loop - use join() or list",
                            "severity": "medium"
                        })
                
                # Global variables that could be large
                if re.match(r'^[A-Z_]+\s*=.*\[\]|\{\}', line.strip()):
                    issues.append({
                        "line": line_num,
                        "description": "Global mutable state - potential memory leak",
                        "severity": "low"
                    })
            
            return issues
        
        @self.agent.tool
        async def detect_algorithm_issues(ctx: RunContext[Any], code: str) -> List[Dict[str, Any]]:
            """Detect inefficient algorithms.
            
            Args:
                code: Code to analyze
                
            Returns:
                List of algorithmic inefficiencies
            """
            issues = []
            lines = code.split('\n')
            
            # Check for inefficient operations
            patterns = [
                (r'if.*in.*list\(|if.*in.*\[', "Using 'in' with list - O(n) operation", "medium"),
                (r'\.sort\(\).*\.sort\(\)', "Multiple sorts - combine operations", "medium"),
                (r'sorted\(.*reverse.*sorted\(', "Multiple sorting operations", "medium"),
                (r'len\(.*\)\s*==\s*0|len\(.*\)\s*!=\s*0', "Use boolean evaluation instead of len()", "low"),
                (r'sum\(\[.*for.*in.*\]\)', "sum() with list comprehension - use generator", "low"),
            ]
            
            for line_num, line in enumerate(lines, 1):
                for pattern, description, severity in patterns:
                    if re.search(pattern, line):
                        issues.append({
                            "line": line_num,
                            "description": description,
                            "severity": severity
                        })
            
            return issues
    
    async def _perform_analysis(self, context: CodeContext) -> List[CodeIssue]:
        """Perform performance analysis.
        
        Args:
            context: Code context to analyze
            
        Returns:
            List of performance issues
        """
        issues = []
        lines = context.code.split('\n')
        
        # Detect inefficient loops directly
        loop_issues = []
        patterns = [
            (r'for.*in.*range\(len\(', "Using range(len()) instead of enumerate()", "medium"),
            (r'\.append\(.*\).*for.*in', "List append in loop instead of list comprehension", "low"),
            (r'for.*in.*\.keys\(\)', "Iterating over .keys() unnecessarily", "low"),
        ]
        
        for line_num, line in enumerate(lines, 1):
            for pattern, description, severity in patterns:
                if re.search(pattern, line):
                    loop_issues.append({
                        "line": line_num,
                        "description": description,
                        "code": line.strip(),
                        "severity": severity
                    })
        for issue in loop_issues:
            issues.append(CodeIssue(
                id=str(uuid.uuid4()),
                title="Inefficient Loop Pattern",
                description=issue["description"],
                severity=SeverityLevel(issue["severity"]),
                category=IssueCategory.PERFORMANCE,
                location=CodeLocation(
                    file_path=context.file_path or "unknown",
                    line_start=issue["line"],
                    line_end=issue["line"]
                ),
                code_snippet=issue["code"],
                confidence=0.8,
                detected_by=self.name
            ))
        
        # Detect database issues directly
        db_issues = []
        for line_num, line in enumerate(lines, 1):
            if re.search(r'SELECT\s+\*', line, re.IGNORECASE):
                db_issues.append({
                    "line": line_num,
                    "type": "select_all",
                    "description": "SELECT * can fetch unnecessary data",
                    "severity": "low"
                })
        for issue in db_issues:
            title_map = {
                "n_plus_one": "N+1 Query Problem",
                "missing_index": "Potential Missing Index",
                "select_all": "Inefficient SELECT Query"
            }
            issues.append(CodeIssue(
                id=str(uuid.uuid4()),
                title=title_map.get(issue.get("type", ""), "Database Performance Issue"),
                description=issue["description"],
                severity=SeverityLevel(issue["severity"]),
                category=IssueCategory.PERFORMANCE,
                location=CodeLocation(
                    file_path=context.file_path or "unknown",
                    line_start=issue["line"],
                    line_end=issue["line"]
                ),
                confidence=0.75,
                detected_by=self.name
            ))
        
        # Detect memory issues directly
        memory_issues = []
        for line_num, line in enumerate(lines, 1):
            if re.search(r'\.read\(\)|\.readlines\(\)', line):
                memory_issues.append({
                    "line": line_num,
                    "description": "Reading entire file into memory - consider streaming",
                    "severity": "medium"
                })
        for issue in memory_issues:
            issues.append(CodeIssue(
                id=str(uuid.uuid4()),
                title="Memory Efficiency Issue",
                description=issue["description"],
                severity=SeverityLevel(issue["severity"]),
                category=IssueCategory.PERFORMANCE,
                location=CodeLocation(
                    file_path=context.file_path or "unknown",
                    line_start=issue["line"],
                    line_end=issue["line"]
                ),
                confidence=0.7,
                detected_by=self.name
            ))
        
        # Detect algorithm issues directly
        algo_issues = []
        algo_patterns = [
            (r'if.*in.*list\(|if.*in.*\[', "Using 'in' with list - O(n) operation", "medium"),
            (r'len\(.*\)\s*==\s*0|len\(.*\)\s*!=\s*0', "Use boolean evaluation instead of len()", "low"),
        ]
        
        for line_num, line in enumerate(lines, 1):
            for pattern, description, severity in algo_patterns:
                if re.search(pattern, line):
                    algo_issues.append({
                        "line": line_num,
                        "description": description,
                        "severity": severity
                    })
        for issue in algo_issues:
            issues.append(CodeIssue(
                id=str(uuid.uuid4()),
                title="Inefficient Algorithm",
                description=issue["description"],
                severity=SeverityLevel(issue["severity"]),
                category=IssueCategory.PERFORMANCE,
                location=CodeLocation(
                    file_path=context.file_path or "unknown",
                    line_start=issue["line"],
                    line_end=issue["line"]
                ),
                confidence=0.85,
                detected_by=self.name
            ))
        
        return issues