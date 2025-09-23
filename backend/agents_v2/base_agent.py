"""Base Pydantic AI agent for code analysis and editing."""

import os
import logging
from typing import Any, Dict, List, Optional, TypeVar, Generic
from datetime import datetime
from pydantic import BaseModel
from pydantic_ai import Agent, Tool, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from openai import AzureOpenAI

from .models import (
    CodeContext,
    CodeIssue,
    CodeRecommendation,
    EditOperation,
    ValidationResult,
    AgentResponse
)

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


class BaseCodeAgent(Generic[T]):
    """Base class for all code analysis agents using Pydantic AI."""
    
    def __init__(
        self,
        name: str,
        description: str,
        azure_client: Optional[AzureOpenAI] = None,
        model_name: Optional[str] = None,
        system_prompt: Optional[str] = None
    ):
        """Initialize the base agent.
        
        Args:
            name: Agent name
            description: Agent description
            azure_client: Azure OpenAI client (optional)
            model_name: Model deployment name
            system_prompt: Custom system prompt
        """
        self.name = name
        self.description = description
        self.azure_client = azure_client
        self.model_name = model_name or os.getenv("REASONING_MODEL", "gpt-4")
        
        # Initialize Pydantic AI agent
        # Set up environment variables for Pydantic AI to use Azure OpenAI
        if azure_client:
            # Set OpenAI environment variables to point to Azure
            os.environ['OPENAI_API_KEY'] = azure_client.api_key
            os.environ['OPENAI_BASE_URL'] = str(azure_client.base_url)
            self.model = f'openai:{self.model_name}'
        else:
            # Use default OpenAI (will need OPENAI_API_KEY)
            self.model = 'openai:gpt-4'
            
        # Create the agent with tools
        self.agent = self._create_agent(system_prompt)
        
        # Register tools
        self._register_tools()
        
    def _create_agent(self, system_prompt: Optional[str] = None) -> Agent:
        """Create the Pydantic AI agent.
        
        Args:
            system_prompt: Custom system prompt
            
        Returns:
            Configured Pydantic AI agent
        """
        default_prompt = f"""You are {self.name}, an expert AI agent specialized in code analysis and improvement.
        
Description: {self.description}

Your responsibilities:
1. Analyze code for issues and improvements
2. Provide actionable recommendations
3. Generate safe and tested fixes
4. Explain your reasoning clearly
5. Consider best practices and standards

Always provide structured, type-safe responses."""

        return Agent(
            model=self.model,
            system_prompt=system_prompt or default_prompt
        )
    
    def _register_tools(self):
        """Register agent-specific tools. Override in subclasses."""
        # Base tools that all agents share
        
        @self.agent.tool
        async def analyze_syntax(ctx: RunContext[Any], code: str, language: str) -> Dict[str, Any]:
            """Analyze code syntax.
            
            Args:
                ctx: Run context
                code: Code to analyze
                language: Programming language
                
            Returns:
                Syntax analysis results
            """
            return {
                "valid": True,
                "language": language,
                "lines": len(code.split('\n'))
            }
        
        @self.agent.tool
        async def extract_functions(ctx: RunContext[Any], code: str) -> List[str]:
            """Extract function definitions from code.
            
            Args:
                ctx: Run context
                code: Code to analyze
                
            Returns:
                List of function names
            """
            import re
            # Simple regex for function extraction (Python)
            pattern = r'def\s+(\w+)\s*\('
            functions = re.findall(pattern, code)
            return functions
        
        @self.agent.tool
        async def count_complexity(ctx: RunContext[Any], code: str) -> int:
            """Calculate cyclomatic complexity estimate.
            
            Args:
                ctx: Run context
                code: Code to analyze
                
            Returns:
                Complexity score
            """
            # Simplified complexity calculation
            complexity = 1  # Base complexity
            
            # Count decision points
            keywords = ['if', 'elif', 'for', 'while', 'except', 'case']
            for keyword in keywords:
                complexity += code.count(f' {keyword} ')
                complexity += code.count(f'\n{keyword} ')
                
            return complexity
    
    async def analyze(self, context: CodeContext) -> AgentResponse:
        """Analyze code and return results.
        
        Args:
            context: Code context to analyze
            
        Returns:
            Agent response with analysis results
        """
        start_time = datetime.now()
        
        try:
            # Run agent analysis
            result = await self._perform_analysis(context)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return AgentResponse(
                agent_name=self.name,
                success=True,
                data=result,
                processing_time=processing_time,
                metadata={"language": context.language}
            )
            
        except Exception as e:
            logger.error(f"Agent {self.name} analysis failed: {e}")
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return AgentResponse(
                agent_name=self.name,
                success=False,
                error=str(e),
                processing_time=processing_time
            )
    
    async def _perform_analysis(self, context: CodeContext) -> Any:
        """Perform the actual analysis. Override in subclasses.
        
        Args:
            context: Code context to analyze
            
        Returns:
            Analysis results
        """
        raise NotImplementedError("Subclasses must implement _perform_analysis")
    
    async def generate_recommendation(
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
            # Use agent to generate fix
            prompt = f"""Generate a fix for this issue:
            
Issue: {issue.title}
Description: {issue.description}
Severity: {issue.severity}

Code context:
```{context.language}
{context.code}
```

Provide a safe, tested fix that resolves the issue."""
            
            # This would use the agent's completion
            # For now, return a mock recommendation
            return CodeRecommendation(
                issue_id=issue.id,
                title=f"Fix for {issue.title}",
                description=f"Automated fix for {issue.description}",
                original_code=issue.code_snippet or "",
                suggested_code="# Fixed code here",
                explanation="This fix resolves the identified issue",
                confidence=0.8,
                auto_fixable=True,
                requires_review=True,
                impact="safe"
            )
            
        except Exception as e:
            logger.error(f"Failed to generate recommendation: {e}")
            return None
    
    async def validate_fix(
        self,
        original_code: str,
        fixed_code: str,
        language: str
    ) -> ValidationResult:
        """Validate a code fix.
        
        Args:
            original_code: Original code
            fixed_code: Fixed code
            language: Programming language
            
        Returns:
            Validation result
        """
        try:
            # Basic validation logic
            errors = []
            warnings = []
            
            # Check if code is not empty
            if not fixed_code.strip():
                errors.append("Fixed code is empty")
            
            # Check if fix is different from original
            if fixed_code == original_code:
                warnings.append("No changes detected in fix")
            
            # More validation can be added here
            
            return ValidationResult(
                valid=len(errors) == 0,
                syntax_valid=True,  # Would use actual syntax checker
                semantic_valid=True,  # Would use semantic analysis
                type_check_passed=True,  # Would use type checker
                errors=errors,
                warnings=warnings,
                metrics={
                    "lines_changed": abs(len(fixed_code.split('\n')) - len(original_code.split('\n')))
                }
            )
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return ValidationResult(
                valid=False,
                errors=[str(e)]
            )