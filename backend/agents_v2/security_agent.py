"""Security vulnerability detection agent using Pydantic AI."""

import re
import uuid
from typing import List, Dict, Any

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
    
    def __init__(self, azure_client=None, model_name=None):
        """Initialize security analysis agent."""
        super().__init__(
            name="Security Vulnerability Scanner",
            description="Detects security vulnerabilities, injection risks, and unsafe patterns",
            azure_client=azure_client,
            model_name=model_name
        )
        
    def _register_tools(self):
        """Register security analysis specific tools."""
        super()._register_tools()
        
        @self.agent.tool
        async def detect_sql_injection(code: str) -> List[Dict[str, Any]]:
            """Detect potential SQL injection vulnerabilities.
            
            Args:
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
        async def detect_xss_vulnerabilities(code: str) -> List[Dict[str, Any]]:
            """Detect potential XSS vulnerabilities.
            
            Args:
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
        async def detect_hardcoded_secrets(code: str) -> List[Dict[str, Any]]:
            """Detect hardcoded secrets and credentials.
            
            Args:
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
        async def detect_insecure_operations(code: str) -> List[Dict[str, Any]]:
            """Detect insecure operations and unsafe patterns.
            
            Args:
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
        
        # Detect SQL injection
        sql_vulns = await self.agent.tools.detect_sql_injection(context.code)
        for vuln in sql_vulns:
            issues.append(CodeIssue(
                id=str(uuid.uuid4()),
                title="SQL Injection Vulnerability",
                description=vuln["description"],
                severity=SeverityLevel(vuln["severity"]),
                category=IssueCategory.SECURITY,
                location=CodeLocation(
                    file_path=context.file_path or "unknown",
                    line_start=vuln["line"],
                    line_end=vuln["line"]
                ),
                code_snippet=vuln["code"],
                confidence=0.95,
                detected_by=self.name
            ))
        
        # Detect XSS vulnerabilities
        xss_vulns = await self.agent.tools.detect_xss_vulnerabilities(context.code)
        for vuln in xss_vulns:
            issues.append(CodeIssue(
                id=str(uuid.uuid4()),
                title="Cross-Site Scripting (XSS) Risk",
                description=vuln["description"],
                severity=SeverityLevel(vuln["severity"]),
                category=IssueCategory.SECURITY,
                location=CodeLocation(
                    file_path=context.file_path or "unknown",
                    line_start=vuln["line"],
                    line_end=vuln["line"]
                ),
                code_snippet=vuln["code"],
                confidence=0.9,
                detected_by=self.name
            ))
        
        # Detect hardcoded secrets
        secrets = await self.agent.tools.detect_hardcoded_secrets(context.code)
        for secret in secrets:
            issues.append(CodeIssue(
                id=str(uuid.uuid4()),
                title="Hardcoded Secret Detected",
                description=secret["description"],
                severity=SeverityLevel(secret["severity"]),
                category=IssueCategory.SECURITY,
                location=CodeLocation(
                    file_path=context.file_path or "unknown",
                    line_start=secret["line"],
                    line_end=secret["line"]
                ),
                code_snippet=secret["code"],
                confidence=0.85,
                detected_by=self.name
            ))
        
        # Detect insecure operations
        insecure_ops = await self.agent.tools.detect_insecure_operations(context.code)
        for op in insecure_ops:
            issues.append(CodeIssue(
                id=str(uuid.uuid4()),
                title="Insecure Operation Detected",
                description=op["description"],
                severity=SeverityLevel(op["severity"]),
                category=IssueCategory.SECURITY,
                location=CodeLocation(
                    file_path=context.file_path or "unknown",
                    line_start=op["line"],
                    line_end=op["line"]
                ),
                code_snippet=op["code"],
                confidence=0.8,
                detected_by=self.name
            ))
        
        return issues