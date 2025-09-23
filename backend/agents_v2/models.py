"""Pydantic models for type-safe agent operations."""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class SeverityLevel(str, Enum):
    """Issue severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IssueCategory(str, Enum):
    """Categories of code issues."""
    SECURITY = "security"
    PERFORMANCE = "performance"
    QUALITY = "quality"
    MAINTAINABILITY = "maintainability"
    BEST_PRACTICES = "best_practices"
    STYLE = "style"
    BUG = "bug"


class CodeLocation(BaseModel):
    """Represents a location in code."""
    file_path: str = Field(..., description="Path to the file")
    line_start: int = Field(..., description="Starting line number")
    line_end: Optional[int] = Field(None, description="Ending line number")
    column_start: Optional[int] = Field(None, description="Starting column")
    column_end: Optional[int] = Field(None, description="Ending column")


class CodeContext(BaseModel):
    """Context for code analysis."""
    code: str = Field(..., description="The code to analyze")
    language: str = Field(..., description="Programming language")
    file_path: Optional[str] = Field(None, description="File path if available")
    project_context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional project context")


class CodeIssue(BaseModel):
    """Represents a code issue detected by analysis."""
    id: str = Field(..., description="Unique issue identifier")
    title: str = Field(..., description="Brief issue title")
    description: str = Field(..., description="Detailed issue description")
    severity: SeverityLevel = Field(..., description="Issue severity")
    category: IssueCategory = Field(..., description="Issue category")
    location: Optional[CodeLocation] = Field(None, description="Code location")
    code_snippet: Optional[str] = Field(None, description="Relevant code snippet")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Confidence score")
    detected_by: str = Field(..., description="Agent that detected the issue")
    detected_at: datetime = Field(default_factory=datetime.now)


class CodeRecommendation(BaseModel):
    """Represents a fix recommendation for a code issue."""
    issue_id: str = Field(..., description="Related issue ID")
    title: str = Field(..., description="Recommendation title")
    description: str = Field(..., description="Detailed explanation")
    original_code: str = Field(..., description="Original problematic code")
    suggested_code: str = Field(..., description="Suggested fix code")
    explanation: str = Field(..., description="Why this fix works")
    confidence: float = Field(0.0, ge=0.0, le=1.0, description="Confidence score")
    auto_fixable: bool = Field(False, description="Can be automatically applied")
    requires_review: bool = Field(True, description="Requires user review")
    impact: Literal["safe", "moderate", "risky"] = Field("moderate", description="Impact level of the fix")
    alternative_fixes: List[str] = Field(default_factory=list, description="Alternative fix suggestions")


class EditOperation(BaseModel):
    """Represents a code edit operation."""
    id: str = Field(..., description="Operation ID")
    type: Literal["replace", "insert", "delete", "move"] = Field(..., description="Edit type")
    location: CodeLocation = Field(..., description="Edit location")
    original_content: Optional[str] = Field(None, description="Original content")
    new_content: Optional[str] = Field(None, description="New content")
    description: str = Field(..., description="What this edit does")
    recommendation_id: Optional[str] = Field(None, description="Related recommendation")
    applied: bool = Field(False, description="Whether the edit has been applied")
    applied_at: Optional[datetime] = Field(None)


class ValidationResult(BaseModel):
    """Result of code validation after applying fixes."""
    valid: bool = Field(..., description="Whether the code is valid")
    syntax_valid: bool = Field(True, description="Syntax validity")
    semantic_valid: bool = Field(True, description="Semantic validity")
    type_check_passed: bool = Field(True, description="Type checking result")
    tests_passed: Optional[bool] = Field(None, description="Test execution result")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Code metrics")


class AnalysisResult(BaseModel):
    """Complete analysis result from agent orchestration."""
    id: str = Field(..., description="Analysis ID")
    context: CodeContext = Field(..., description="Analyzed code context")
    issues: List[CodeIssue] = Field(default_factory=list, description="Detected issues")
    recommendations: List[CodeRecommendation] = Field(default_factory=list, description="Fix recommendations")
    overall_score: int = Field(100, ge=0, le=100, description="Overall code quality score")
    summary: str = Field(..., description="Analysis summary")
    analyzed_by: List[str] = Field(default_factory=list, description="Agents that participated")
    analysis_time_seconds: float = Field(0.0, description="Analysis duration")
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class AgentResponse(BaseModel):
    """Standard response from an agent."""
    agent_name: str = Field(..., description="Name of the responding agent")
    success: bool = Field(True, description="Whether the operation succeeded")
    data: Optional[Any] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message if failed")
    processing_time: float = Field(0.0, description="Processing time in seconds")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EditSession(BaseModel):
    """Represents an interactive editing session."""
    session_id: str = Field(..., description="Unique session ID")
    code_context: CodeContext = Field(..., description="Code being edited")
    applied_edits: List[EditOperation] = Field(default_factory=list, description="Applied edits")
    pending_edits: List[EditOperation] = Field(default_factory=list, description="Pending edits")
    undo_stack: List[EditOperation] = Field(default_factory=list, description="Undo history")
    redo_stack: List[EditOperation] = Field(default_factory=list, description="Redo history")
    current_code: str = Field(..., description="Current state of the code")
    validation_status: Optional[ValidationResult] = Field(None)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)