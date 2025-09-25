"""Performance optimization agent using Pydantic AI."""

import re
import uuid
import asyncio
from typing import List, Dict, Any

from pydantic_ai import RunContext

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
        
        # Use Pydantic AI agent to analyze code for performance issues - simplified for speed
        prompt = f"""Analyze this {context.language} code for performance issues:

```{context.language}
{context.code}
```

List each performance issue in this format:
ISSUE:
- Line: [number]
- Type: [issue type]
- Description: [brief description]
- Severity: [critical/high/medium/low]
- Suggestion: [optimization]"""

        try:
            # Run agent to get AI analysis with timeout
            result = await asyncio.wait_for(
                self.agent.run(prompt),
                timeout=20.0  # 20-second timeout per agent
            )
            ai_response = result.output
            
            # Parse AI response to extract structured issues
            lines = context.code.split('\n')
            
            # Split response into individual issues
            issue_blocks = ai_response.split('ISSUE:')
            
            for block in issue_blocks[1:]:  # Skip first empty split
                if not block.strip():
                    continue
                
                # Parse each field from the structured response
                line_num = None
                issue_type = "Performance Issue"
                description = ""
                severity = "medium"
                suggestion = ""
                fixed_code = ""
                
                for line in block.split('\n'):
                    line = line.strip()
                    if line.startswith('- Line:'):
                        line_match = re.search(r'Line:\s*(\d+)', line)
                        if line_match:
                            line_num = int(line_match.group(1))
                    elif line.startswith('- Type:'):
                        issue_type = line.replace('- Type:', '').strip()
                    elif line.startswith('- Description:'):
                        description = line.replace('- Description:', '').strip()
                    elif line.startswith('- Severity:'):
                        sev = line.replace('- Severity:', '').strip().lower()
                        if sev in ['critical', 'high', 'medium', 'low']:
                            severity = sev
                    elif line.startswith('- Suggestion:'):
                        suggestion = line.replace('- Suggestion:', '').strip()
                    elif line.startswith('- Fixed Code:'):
                        fixed_code = line.replace('- Fixed Code:', '').strip()
                
                # If we couldn't parse line number, try alternative formats
                if not line_num:
                    # Try to find line number in the whole block
                    line_match = re.search(r'(?:Line|line)[\s:]+(\d+)', block, re.IGNORECASE)
                    if line_match:
                        line_num = int(line_match.group(1))
                    else:
                        line_num = 1  # Default to line 1 if not found
                
                # Get code snippet from actual code
                code_snippet = ""
                if 0 < line_num <= len(lines):
                    code_snippet = lines[line_num - 1].strip()
                
                # Create issue with all extracted information
                issues.append(CodeIssue(
                    id=str(uuid.uuid4()),
                    title=issue_type,
                    description=description or f"Performance issue detected at line {line_num}",
                    severity=SeverityLevel(severity),
                    category=IssueCategory.PERFORMANCE,
                    location=CodeLocation(
                        file_path=context.file_path or "unknown",
                        line_start=line_num,
                        line_end=line_num
                    ),
                    code_snippet=code_snippet,
                    suggested_fix=fixed_code if fixed_code else None,
                    fix_explanation=suggestion if suggestion else None,
                    confidence=0.9,
                    detected_by=self.name
                ))
            
            # If AI found issues, return them
            if issues:
                return issues
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"AI analysis failed: {e}, using fallback")
        
        # Minimal fallback only if AI completely fails
        return issues
        
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