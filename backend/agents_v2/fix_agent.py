"""Code fixing agent using Pydantic AI."""

import re
import uuid
from typing import List, Dict, Any, Optional, Tuple

from .base_agent import BaseCodeAgent
from .models import (
    CodeContext,
    CodeIssue,
    CodeRecommendation,
    EditOperation,
    ValidationResult,
    SeverityLevel,
    IssueCategory
)


class CodeFixAgent(BaseCodeAgent):
    """Agent specialized in generating and validating code fixes."""
    
    def __init__(self, azure_client=None, model_name=None):
        """Initialize code fix agent."""
        super().__init__(
            name="Code Fix Generator",
            description="Generates safe, tested fixes for identified code issues",
            azure_client=azure_client,
            model_name=model_name
        )
        
    def _register_tools(self):
        """Register code fixing specific tools."""
        super()._register_tools()
        
        @self.agent.tool
        async def generate_sql_injection_fix(code: str, issue_line: int) -> Dict[str, Any]:
            """Generate fix for SQL injection vulnerability.
            
            Args:
                code: Original code
                issue_line: Line with the issue
                
            Returns:
                Fix information
            """
            lines = code.split('\n')
            if issue_line <= 0 or issue_line > len(lines):
                return {"error": "Invalid line number"}
            
            original_line = lines[issue_line - 1]
            fixed_line = original_line
            
            # Fix string concatenation in SQL
            if '+' in original_line and any(sql in original_line.upper() for sql in ['SELECT', 'WHERE', 'INSERT', 'UPDATE']):
                # Replace string concatenation with parameterized query
                if 'str(' in original_line:
                    # Python example: "SELECT * FROM users WHERE id = " + str(user_id)
                    fixed_line = re.sub(
                        r'(["\'])([^"\']*)\1\s*\+\s*str\([^)]+\)',
                        r'\1\2\1, (\3,)',
                        original_line
                    )
                    fixed_line = re.sub(r'WHERE\s+(\w+)\s*=\s*["\']', r'WHERE \1 = ?', fixed_line)
                
                return {
                    "original": original_line,
                    "fixed": fixed_line,
                    "explanation": "Use parameterized queries to prevent SQL injection"
                }
            
            return {"error": "Could not generate fix"}
        
        @self.agent.tool
        async def fix_naming_convention(code: str, issue_line: int, convention: str) -> Dict[str, Any]:
            """Fix naming convention issues.
            
            Args:
                code: Original code
                issue_line: Line with the issue
                convention: Target naming convention
                
            Returns:
                Fix information
            """
            lines = code.split('\n')
            if issue_line <= 0 or issue_line > len(lines):
                return {"error": "Invalid line number"}
            
            original_line = lines[issue_line - 1]
            fixed_line = original_line
            
            if convention == "snake_case":
                # Convert camelCase to snake_case
                def camel_to_snake(name):
                    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
                    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
                
                # Fix function names
                if 'def ' in original_line:
                    func_match = re.search(r'def\s+([a-zA-Z_]\w*)', original_line)
                    if func_match:
                        old_name = func_match.group(1)
                        new_name = camel_to_snake(old_name)
                        fixed_line = original_line.replace(f'def {old_name}', f'def {new_name}')
            
            elif convention == "PascalCase":
                # Convert to PascalCase for classes
                if 'class ' in original_line:
                    class_match = re.search(r'class\s+([a-z_]\w*)', original_line)
                    if class_match:
                        old_name = class_match.group(1)
                        new_name = ''.join(word.capitalize() for word in old_name.split('_'))
                        fixed_line = original_line.replace(f'class {old_name}', f'class {new_name}')
            
            return {
                "original": original_line,
                "fixed": fixed_line,
                "explanation": f"Fixed naming to follow {convention} convention"
            }
        
        @self.agent.tool
        async def optimize_loop(code: str, issue_line: int) -> Dict[str, Any]:
            """Optimize inefficient loop patterns.
            
            Args:
                code: Original code
                issue_line: Line with the issue
                
            Returns:
                Optimized code
            """
            lines = code.split('\n')
            if issue_line <= 0 or issue_line > len(lines):
                return {"error": "Invalid line number"}
            
            original_line = lines[issue_line - 1]
            fixed_line = original_line
            
            # Fix range(len()) pattern
            if 'for' in original_line and 'range(len(' in original_line:
                # Extract variable names
                match = re.search(r'for\s+(\w+)\s+in\s+range\(len\((\w+)\)\)', original_line)
                if match:
                    index_var = match.group(1)
                    list_var = match.group(2)
                    # Check if index is used in the loop body
                    loop_body = []
                    indent = len(original_line) - len(original_line.lstrip())
                    for i in range(issue_line, min(issue_line + 10, len(lines))):
                        next_line = lines[i]
                        next_indent = len(next_line) - len(next_line.lstrip())
                        if next_indent <= indent and next_line.strip():
                            break
                        loop_body.append(next_line)
                    
                    # If index is used, use enumerate
                    if any(index_var in line for line in loop_body):
                        fixed_line = re.sub(
                            r'for\s+(\w+)\s+in\s+range\(len\((\w+)\)\)',
                            r'for \1, item in enumerate(\2)',
                            original_line
                        )
                    else:
                        # If index not used, iterate directly
                        fixed_line = re.sub(
                            r'for\s+\w+\s+in\s+range\(len\((\w+)\)\)',
                            r'for item in \1',
                            original_line
                        )
            
            # Fix .keys() iteration
            elif '.keys()' in original_line:
                fixed_line = original_line.replace('.keys()', '')
            
            return {
                "original": original_line,
                "fixed": fixed_line,
                "explanation": "Optimized loop pattern for better performance"
            }
        
        @self.agent.tool
        async def fix_exception_handling(code: str, issue_line: int) -> Dict[str, Any]:
            """Fix broad exception handling.
            
            Args:
                code: Original code
                issue_line: Line with the issue
                
            Returns:
                Fixed exception handling
            """
            lines = code.split('\n')
            if issue_line <= 0 or issue_line > len(lines):
                return {"error": "Invalid line number"}
            
            original_line = lines[issue_line - 1]
            
            # Fix bare except
            if re.search(r'except\s*:', original_line):
                # Look at the try block to determine likely exceptions
                try_line = -1
                for i in range(issue_line - 2, max(0, issue_line - 20), -1):
                    if 'try:' in lines[i]:
                        try_line = i
                        break
                
                # Analyze try block content
                exceptions = []
                if try_line >= 0:
                    try_block = '\n'.join(lines[try_line:issue_line-1])
                    
                    if 'open(' in try_block or 'file' in try_block:
                        exceptions.append('IOError')
                    if 'int(' in try_block or 'float(' in try_block:
                        exceptions.append('ValueError')
                    if '[' in try_block or 'dict' in try_block:
                        exceptions.append('KeyError')
                    if '/' in try_block:
                        exceptions.append('ZeroDivisionError')
                    
                    if not exceptions:
                        exceptions = ['Exception']  # At least use Exception instead of bare
                
                fixed_line = original_line.replace(
                    'except:',
                    f'except ({", ".join(exceptions)}):'
                )
                
                return {
                    "original": original_line,
                    "fixed": fixed_line,
                    "explanation": f"Catch specific exceptions: {', '.join(exceptions)}"
                }
            
            return {"error": "Could not generate fix"}
    
    async def generate_fix(
        self,
        issue: CodeIssue,
        context: CodeContext
    ) -> Optional[CodeRecommendation]:
        """Generate a fix recommendation for an issue.
        
        Args:
            issue: The issue to fix
            context: Code context
            
        Returns:
            Fix recommendation or None
        """
        try:
            lines = context.code.split('\n')
            
            # Determine fix strategy based on issue category
            fix_result = None
            
            if issue.category == IssueCategory.SECURITY:
                if "SQL" in issue.title.upper():
                    fix_result = await self.agent.tools.generate_sql_injection_fix(
                        context.code,
                        issue.location.line_start if issue.location else 1
                    )
            
            elif issue.category == IssueCategory.STYLE:
                if "naming" in issue.title.lower():
                    convention = "snake_case" if "snake" in issue.description.lower() else "PascalCase"
                    fix_result = await self.agent.tools.fix_naming_convention(
                        context.code,
                        issue.location.line_start if issue.location else 1,
                        convention
                    )
            
            elif issue.category == IssueCategory.PERFORMANCE:
                if "loop" in issue.title.lower():
                    fix_result = await self.agent.tools.optimize_loop(
                        context.code,
                        issue.location.line_start if issue.location else 1
                    )
            
            elif issue.category == IssueCategory.QUALITY:
                if "exception" in issue.title.lower():
                    fix_result = await self.agent.tools.fix_exception_handling(
                        context.code,
                        issue.location.line_start if issue.location else 1
                    )
            
            if fix_result and "error" not in fix_result:
                return CodeRecommendation(
                    issue_id=issue.id,
                    title=f"Fix for {issue.title}",
                    description=fix_result.get("explanation", "Automated fix"),
                    original_code=fix_result.get("original", ""),
                    suggested_code=fix_result.get("fixed", ""),
                    explanation=fix_result.get("explanation", ""),
                    confidence=0.8,
                    auto_fixable=True,
                    requires_review=True,
                    impact="safe" if issue.severity == SeverityLevel.LOW else "moderate"
                )
            
            # Fallback to generic fix suggestion
            return CodeRecommendation(
                issue_id=issue.id,
                title=f"Manual fix required for {issue.title}",
                description=issue.description,
                original_code=issue.code_snippet or "",
                suggested_code="# TODO: Manual fix required",
                explanation="This issue requires manual review and fixing",
                confidence=0.3,
                auto_fixable=False,
                requires_review=True,
                impact="moderate"
            )
            
        except Exception as e:
            logger.error(f"Failed to generate fix: {e}")
            return None
    
    async def apply_fix(
        self,
        code: str,
        recommendation: CodeRecommendation
    ) -> Tuple[str, EditOperation]:
        """Apply a fix recommendation to code.
        
        Args:
            code: Original code
            recommendation: Fix recommendation
            
        Returns:
            Tuple of (fixed code, edit operation)
        """
        try:
            # Simple replacement for now
            fixed_code = code.replace(
                recommendation.original_code,
                recommendation.suggested_code
            )
            
            # Create edit operation
            operation = EditOperation(
                id=str(uuid.uuid4()),
                type="replace",
                location=CodeLocation(
                    file_path="unknown",
                    line_start=1,
                    line_end=1
                ),
                original_content=recommendation.original_code,
                new_content=recommendation.suggested_code,
                description=recommendation.description,
                recommendation_id=recommendation.issue_id,
                applied=True
            )
            
            return fixed_code, operation
            
        except Exception as e:
            logger.error(f"Failed to apply fix: {e}")
            raise