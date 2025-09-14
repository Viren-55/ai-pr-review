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