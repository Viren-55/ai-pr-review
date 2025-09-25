"""Security vulnerability detection agent using Pydantic AI."""

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


class SecurityAnalysisAgent(BaseCodeAgent):
    """Agent specialized in security vulnerability detection."""
    
    def __init__(self, async_azure_client=None, model_name=None):
        """Initialize security analysis agent."""
        super().__init__(
            name="Security Vulnerability Scanner",
            description="Detects security vulnerabilities, injection risks, and unsafe patterns",
            async_azure_client=async_azure_client,
            model_name=model_name
        )
        
    def _register_tools(self):
        """Register security analysis specific tools."""
        super()._register_tools()
        
        @self.agent.tool
        async def detect_sql_injection(ctx: RunContext[Any], code: str) -> List[Dict[str, Any]]:
            """Detect potential SQL injection vulnerabilities.
            
            Args:
                ctx: Run context
                code: Code to analyze
                
            Returns:
                List of SQL injection risks
            """
            vulnerabilities = []
            lines = code.split('\n')
            
            # Patterns that indicate SQL injection risk
            sql_patterns = [
                (r'SELECT.*\+.*(?:request|input|param|args|data)', "String concatenation in SQL query"),
                (r'WHERE.*%s|WHERE.*\?.*format|WHERE.*f["\']', "Unsafe string formatting in SQL"),
                (r'execute\([^)]*\+[^)]*\)', "Dynamic SQL execution with concatenation"),
                (r'query\s*=\s*["\'].*["\'].*\+', "SQL query built with string concatenation"),
            ]
            
            for line_num, line in enumerate(lines, 1):
                for pattern, description in sql_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        vulnerabilities.append({
                            "line": line_num,
                            "type": "sql_injection",
                            "description": description,
                            "code": line.strip(),
                            "severity": "critical"
                        })
            
            return vulnerabilities
        
        @self.agent.tool
        async def detect_xss_vulnerabilities(ctx: RunContext[Any], code: str) -> List[Dict[str, Any]]:
            """Detect potential XSS vulnerabilities.
            
            Args:
                ctx: Run context
                code: Code to analyze
                
            Returns:
                List of XSS risks
            """
            vulnerabilities = []
            lines = code.split('\n')
            
            # XSS patterns
            xss_patterns = [
                (r'innerHTML\s*=.*(?:request|input|param)', "Direct innerHTML assignment with user input"),
                (r'document\.write\(.*(?:request|input|param)', "document.write with user input"),
                (r'eval\(.*(?:request|input|param)', "eval() with user input"),
                (r'render_template.*\|safe', "Unsafe template rendering"),
                (r'dangerouslySetInnerHTML', "React dangerouslySetInnerHTML usage"),
            ]
            
            for line_num, line in enumerate(lines, 1):
                for pattern, description in xss_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        vulnerabilities.append({
                            "line": line_num,
                            "type": "xss",
                            "description": description,
                            "code": line.strip(),
                            "severity": "high"
                        })
            
            return vulnerabilities
        
        @self.agent.tool
        async def detect_hardcoded_secrets(ctx: RunContext[Any], code: str) -> List[Dict[str, Any]]:
            """Detect hardcoded secrets and credentials.
            
            Args:
                ctx: Run context
                code: Code to analyze
                
            Returns:
                List of hardcoded secrets
            """
            secrets = []
            lines = code.split('\n')
            
            # Patterns for detecting secrets
            secret_patterns = [
                (r'(?:api[_-]?key|apikey)\s*=\s*["\'][a-zA-Z0-9_\-]{20,}["\']', "Hardcoded API key"),
                (r'(?:password|passwd|pwd)\s*=\s*["\'][^"\']+["\']', "Hardcoded password"),
                (r'(?:secret|token)\s*=\s*["\'][a-zA-Z0-9_\-]{20,}["\']', "Hardcoded secret/token"),
                (r'Bearer\s+[a-zA-Z0-9_\-\.]+', "Hardcoded bearer token"),
                (r'aws_access_key_id\s*=\s*["\'][A-Z0-9]{20}["\']', "AWS access key"),
                (r'aws_secret_access_key\s*=\s*["\'][a-zA-Z0-9/+=]{40}["\']', "AWS secret key"),
            ]
            
            for line_num, line in enumerate(lines, 1):
                # Skip comments
                if line.strip().startswith('#') or line.strip().startswith('//'):
                    continue
                    
                for pattern, description in secret_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        # Check if it's likely a placeholder
                        if not re.search(r'(example|placeholder|your[_-]|xxx|<.*>)', line, re.IGNORECASE):
                            secrets.append({
                                "line": line_num,
                                "type": "hardcoded_secret",
                                "description": description,
                                "code": line.strip()[:50] + "...",  # Truncate for safety
                                "severity": "critical"
                            })
            
            return secrets
        
        @self.agent.tool
        async def detect_insecure_operations(ctx: RunContext[Any], code: str) -> List[Dict[str, Any]]:
            """Detect insecure operations and unsafe patterns.
            
            Args:
                ctx: Run context
                code: Code to analyze
                
            Returns:
                List of insecure operations
            """
            issues = []
            lines = code.split('\n')
            
            # Insecure operation patterns
            insecure_patterns = [
                (r'pickle\.loads?\(', "Unsafe deserialization with pickle", "high"),
                (r'exec\(|eval\(', "Dynamic code execution", "critical"),
                (r'os\.system\(|subprocess\..*shell=True', "Shell injection risk", "high"),
                (r'verify\s*=\s*False|ssl\._create_unverified_context', "SSL verification disabled", "high"),
                (r'except\s*:', "Broad exception handling", "low"),
                (r'md5\(|sha1\(', "Weak cryptographic hash", "medium"),
                (r'Random\(\)|random\.\w+', "Insecure random number generation", "medium"),
                (r'chmod.*777|chmod.*666', "Overly permissive file permissions", "high"),
            ]
            
            for line_num, line in enumerate(lines, 1):
                for pattern, description, severity in insecure_patterns:
                    if re.search(pattern, line):
                        issues.append({
                            "line": line_num,
                            "type": "insecure_operation",
                            "description": description,
                            "code": line.strip(),
                            "severity": severity
                        })
            
            return issues
    
    async def _perform_analysis(self, context: CodeContext) -> List[CodeIssue]:
        """Perform security analysis.
        
        Args:
            context: Code context to analyze
            
        Returns:
            List of security issues
        """
        issues = []
        
        # Use Pydantic AI agent to analyze code - simplified prompt for faster response
        prompt = f"""Analyze this {context.language} code for security issues:

```{context.language}
{context.code}
```

List each security issue in this format:
ISSUE:
- Line: [number]
- Type: [issue type]
- Description: [brief description]
- Severity: [critical/high/medium/low]
- Suggestion: [fix]"""

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
                issue_type = "Security Issue"
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
                    description=description or f"Security issue detected at line {line_num}",
                    severity=SeverityLevel(severity),
                    category=IssueCategory.SECURITY,
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
        
        return issues