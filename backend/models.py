"""Database models for the code review system."""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

Base = declarative_base()

class CodeSubmission(Base):
    """Model for storing code submissions."""
    __tablename__ = "code_submissions"
    
    id = Column(Integer, primary_key=True, index=True)
    original_code = Column(Text, nullable=False)
    language = Column(String(50), nullable=False)
    filename = Column(String(255), nullable=True)
    submission_type = Column(String(20), nullable=False)  # paste, upload, github
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    analysis = relationship("CodeAnalysis", back_populates="submission", uselist=False)
    issues = relationship("CodeIssue", back_populates="submission")

class CodeAnalysis(Base):
    """Model for storing AI analysis results."""
    __tablename__ = "code_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("code_submissions.id"), unique=True)
    overall_score = Column(Integer, nullable=False)
    analysis_summary = Column(Text, nullable=False)
    model_used = Column(String(100), nullable=False)
    analysis_time_seconds = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    submission = relationship("CodeSubmission", back_populates="analysis")

class CodeIssue(Base):
    """Model for storing individual code issues found by AI."""
    __tablename__ = "code_issues"
    
    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("code_submissions.id"))
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(20), nullable=False)  # critical, high, medium, low
    category = Column(String(50), nullable=False)  # security, performance, quality, practices, maintainability
    line_number = Column(Integer, nullable=True)
    code_snippet = Column(Text, nullable=True)
    suggested_fix = Column(Text, nullable=True)
    fix_explanation = Column(Text, nullable=True)
    is_fixed = Column(Boolean, default=False)
    fixed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    submission = relationship("CodeSubmission", back_populates="issues")

# GitHub Authentication Models
class GitHubUser(Base):
    """Model for storing GitHub authenticated users."""
    __tablename__ = "github_users"
    
    id = Column(Integer, primary_key=True, index=True)
    github_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    avatar_url = Column(Text, nullable=True)
    encrypted_token_data = Column(Text, nullable=False)  # Encrypted GitHub token
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    pr_analyses = relationship("PRAnalysis", back_populates="user")

class PRAnalysis(Base):
    """Model for storing GitHub Pull Request analysis results."""
    __tablename__ = "pr_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("github_users.id"), nullable=False)
    pr_url = Column(String(500), nullable=False)
    repository = Column(String(255), nullable=False)  # owner/repo format
    pr_number = Column(Integer, nullable=False)
    pr_title = Column(String(500), nullable=True)
    pr_description = Column(Text, nullable=True)
    
    # Analysis results
    overall_score = Column(Integer, nullable=True)
    analysis_summary = Column(Text, nullable=True)
    model_used = Column(String(100), nullable=True)
    analysis_time_seconds = Column(Integer, nullable=True)
    
    # PR metadata
    files_changed = Column(JSON, nullable=True)  # List of changed files
    additions = Column(Integer, nullable=True)
    deletions = Column(Integer, nullable=True)
    
    # Status tracking
    analysis_status = Column(String(20), default="pending")  # pending, completed, failed
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("GitHubUser", back_populates="pr_analyses")
    pr_issues = relationship("PRIssue", back_populates="pr_analysis")

class PRIssue(Base):
    """Model for storing issues found in PR analysis."""
    __tablename__ = "pr_issues"
    
    id = Column(Integer, primary_key=True, index=True)
    pr_analysis_id = Column(Integer, ForeignKey("pr_analyses.id"), nullable=False)
    
    # Issue details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(20), nullable=False)  # critical, high, medium, low
    category = Column(String(50), nullable=False)  # security, performance, quality, practices, maintainability
    
    # Location in PR
    file_path = Column(String(500), nullable=True)
    line_number = Column(Integer, nullable=True)
    code_snippet = Column(Text, nullable=True)
    
    # Fix suggestions
    suggested_fix = Column(Text, nullable=True)
    fix_explanation = Column(Text, nullable=True)
    
    # Status tracking
    is_fixed = Column(Boolean, default=False)
    fixed_at = Column(DateTime, nullable=True)
    pr_comment_id = Column(Integer, nullable=True)  # GitHub comment ID if posted
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    pr_analysis = relationship("PRAnalysis", back_populates="pr_issues")

# Pydantic models for API
class CodeSubmissionCreate(BaseModel):
    code: str
    language: str
    filename: Optional[str] = None
    submission_type: str = "paste"

class CodeIssueResponse(BaseModel):
    id: int
    title: str
    description: str
    severity: str
    category: str
    line_number: Optional[int]
    code_snippet: Optional[str]
    suggested_fix: Optional[str]
    fix_explanation: Optional[str]
    is_fixed: bool
    
    class Config:
        from_attributes = True

class CodeAnalysisResponse(BaseModel):
    model_config = {"from_attributes": True, "protected_namespaces": ()}
    
    id: int
    overall_score: int
    analysis_summary: str
    model_used: str
    analysis_time_seconds: int
    issues: List[CodeIssueResponse]

class CodeSubmissionResponse(BaseModel):
    id: int
    original_code: str
    language: str
    filename: Optional[str]
    submission_type: str
    created_at: datetime
    analysis: Optional[CodeAnalysisResponse]
    
    class Config:
        from_attributes = True

class FixIssueRequest(BaseModel):
    issue_id: int
    apply_fix: bool = True

class FixIssueResponse(BaseModel):
    success: bool
    issue_id: int
    updated_code: Optional[str]
    message: str

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    azure_connected: bool
    database_connected: bool

# GitHub Authentication API Models
class GitHubUserResponse(BaseModel):
    id: int
    github_id: int
    username: str
    email: Optional[str]
    avatar_url: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class GitHubPRRequest(BaseModel):
    github_url: str              # PR URL from frontend
    language: str                # Programming language
    apply_fixes: bool = False    # Whether to apply AI suggestions
    create_review: bool = False  # Whether to post review comments

class PRIssueResponse(BaseModel):
    id: int
    title: str
    description: str
    severity: str
    category: str
    file_path: Optional[str]
    line_number: Optional[int]
    code_snippet: Optional[str]
    suggested_fix: Optional[str]
    fix_explanation: Optional[str]
    is_fixed: bool
    pr_comment_id: Optional[int]
    
    class Config:
        from_attributes = True

class PRAnalysisResponse(BaseModel):
    model_config = {"from_attributes": True, "protected_namespaces": ()}
    
    id: int
    pr_url: str
    repository: str
    pr_number: int
    pr_title: Optional[str]
    pr_description: Optional[str]
    overall_score: Optional[int]
    analysis_summary: Optional[str]
    model_used: Optional[str]
    analysis_time_seconds: Optional[int]
    files_changed: Optional[List[str]]
    additions: Optional[int]
    deletions: Optional[int]
    analysis_status: str
    error_message: Optional[str]
    created_at: datetime
    pr_issues: List[PRIssueResponse]

class AuthCallbackRequest(BaseModel):
    code: str
    state: str

class AuthResponse(BaseModel):
    success: bool
    user: Optional[GitHubUserResponse]
    session_token: Optional[str]
    message: str