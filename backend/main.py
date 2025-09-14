"""Enhanced FastAPI backend for code review using Azure OpenAI with AI agents."""

from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
import uvicorn
from openai import AzureOpenAI
from typing import List, Optional
import asyncio

# Import our modules
from database import get_db, create_tables, database
from models import (
    CodeSubmission, CodeAnalysis, CodeIssue as DBCodeIssue,
    CodeSubmissionCreate, CodeSubmissionResponse, CodeAnalysisResponse, 
    CodeIssueResponse, FixIssueRequest, FixIssueResponse, HealthResponse
)
from ai_agents import (
    create_ai_orchestrator, create_code_fixer, 
    AIAgentOrchestrator, CodeFixerAgent
)

# Load environment variables
load_dotenv("../.env")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Validate Azure OpenAI configuration
required_vars = [
    "REASONING_AZURE_OPENAI_API_KEY",
    "REASONING_AZURE_OPENAI_ENDPOINT", 
    "REASONING_AZURE_API_VERSION",
    "REASONING_MODEL"
]

for var in required_vars:
    if not os.getenv(var):
        logger.error(f"Missing required environment variable: {var}")
        exit(1)

# Initialize Azure OpenAI client
azure_client = AzureOpenAI(
    api_key=os.getenv("REASONING_AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("REASONING_AZURE_OPENAI_ENDPOINT"),
    api_version=os.getenv("REASONING_AZURE_API_VERSION")
)

# Initialize AI agents
ai_orchestrator = create_ai_orchestrator(azure_client, os.getenv("REASONING_MODEL"))
code_fixer = create_code_fixer(azure_client, os.getenv("REASONING_MODEL"))

app = FastAPI(
    title="Enhanced Code Review API",
    description="Advanced code review system with AI agents and database storage",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database and connect."""
    create_tables()
    await database.connect()
    logger.info("Database connected and tables created")

@app.on_event("shutdown")
async def shutdown_event():
    """Disconnect from database."""
    await database.disconnect()
    logger.info("Database disconnected")

# Legacy models for backward compatibility
class CodeReviewRequest(CodeSubmissionCreate):
    pass

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "message": "Enhanced Code Review API",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "features": [
            "AI Agent Analysis",
            "Code Storage",
            "Automatic Fixing",
            "Diff Generation",
            "Real-time Updates"
        ]
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Detailed health check including Azure OpenAI and database connectivity."""
    try:
        # Test Azure OpenAI connection
        model_name = os.getenv("REASONING_MODEL")
        
        if "o4" in model_name or "o1" in model_name:
            response = azure_client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": "Hello, respond with just 'OK'"}],
                temperature=1.0,
                max_completion_tokens=10
            )
        else:
            response = azure_client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": "Hello, respond with just 'OK'"}],
                max_tokens=10
            )
        
        azure_connected = True
        logger.info("Azure OpenAI connection successful")
        
    except Exception as e:
        azure_connected = False
        logger.error(f"Azure OpenAI connection failed: {e}")
    
    # Test database connection
    try:
        await database.execute("SELECT 1")
        database_connected = True
        logger.info("Database connection successful")
    except Exception as e:
        database_connected = False
        logger.error(f"Database connection failed: {e}")
    
    return HealthResponse(
        status="healthy" if (azure_connected and database_connected) else "degraded",
        timestamp=datetime.now().isoformat(),
        azure_connected=azure_connected,
        database_connected=database_connected
    )

# Enhanced API endpoints

@app.post("/api/submissions", response_model=CodeSubmissionResponse)
async def create_submission(request: CodeSubmissionCreate, db: Session = Depends(get_db)):
    """Submit code for analysis."""
    try:
        # Validate input
        if not request.code.strip():
            raise HTTPException(status_code=400, detail="Code cannot be empty")
        
        # Create submission record
        submission = CodeSubmission(
            original_code=request.code,
            language=request.language,
            filename=request.filename,
            submission_type=request.submission_type
        )
        
        db.add(submission)
        db.commit()
        db.refresh(submission)
        
        # Run AI analysis
        logger.info(f"Starting analysis for submission {submission.id}")
        issues, score, summary = await ai_orchestrator.analyze_code(request.code, request.language)
        
        # Create analysis record
        analysis = CodeAnalysis(
            submission_id=submission.id,
            overall_score=score,
            analysis_summary=summary,
            model_used=os.getenv("REASONING_MODEL"),
            analysis_time_seconds=3  # This would be calculated in real implementation
        )
        
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        
        # Create issue records
        db_issues = []
        for issue in issues:
            db_issue = DBCodeIssue(
                submission_id=submission.id,
                title=issue.title,
                description=issue.description,
                severity=issue.severity,
                category=issue.category,
                line_number=issue.line_number,
                code_snippet=issue.code_snippet,
                suggested_fix=issue.suggested_fix,
                fix_explanation=issue.fix_explanation
            )
            db.add(db_issue)
            db_issues.append(db_issue)
        
        db.commit()
        
        # Refresh all objects to get IDs
        for db_issue in db_issues:
            db.refresh(db_issue)
        
        logger.info(f"Analysis complete for submission {submission.id}: {len(issues)} issues, score {score}")
        
        # Return full submission with analysis
        return CodeSubmissionResponse(
            id=submission.id,
            original_code=submission.original_code,
            language=submission.language,
            filename=submission.filename,
            submission_type=submission.submission_type,
            created_at=submission.created_at,
            analysis=CodeAnalysisResponse(
                id=analysis.id,
                overall_score=analysis.overall_score,
                analysis_summary=analysis.analysis_summary,
                model_used=analysis.model_used,
                analysis_time_seconds=analysis.analysis_time_seconds,
                issues=[CodeIssueResponse.from_orm(issue) for issue in db_issues]
            )
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Submission failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/api/upload", response_model=CodeSubmissionResponse)
async def upload_file(
    file: UploadFile = File(...),
    language: str = Form(...),
    db: Session = Depends(get_db)
):
    """Upload a code file for analysis."""
    try:
        # Read file content
        content = await file.read()
        code = content.decode('utf-8')
        
        # Create submission request
        request = CodeSubmissionCreate(
            code=code,
            language=language,
            filename=file.filename,
            submission_type="upload"
        )
        
        # Use the same logic as create_submission
        return await create_submission(request, db)
        
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be valid UTF-8 encoded text")
    except Exception as e:
        logger.error(f"File upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/api/submissions/{submission_id}", response_model=CodeSubmissionResponse)
async def get_submission(submission_id: int, db: Session = Depends(get_db)):
    """Get a specific code submission with analysis."""
    submission = db.query(CodeSubmission).filter(CodeSubmission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    return CodeSubmissionResponse.from_orm(submission)

@app.get("/api/submissions", response_model=List[CodeSubmissionResponse])
async def list_submissions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all code submissions."""
    submissions = db.query(CodeSubmission).offset(skip).limit(limit).all()
    return [CodeSubmissionResponse.from_orm(submission) for submission in submissions]

@app.post("/api/issues/{issue_id}/fix", response_model=FixIssueResponse)
async def fix_issue(issue_id: int, request: FixIssueRequest, db: Session = Depends(get_db)):
    """Apply a fix to a specific issue."""
    try:
        # Get the issue
        issue = db.query(DBCodeIssue).filter(DBCodeIssue.id == issue_id).first()
        if not issue:
            raise HTTPException(status_code=404, detail="Issue not found")
        
        if not request.apply_fix:
            # Just mark as fixed without applying
            issue.is_fixed = True
            issue.fixed_at = datetime.utcnow()
            db.commit()
            
            return FixIssueResponse(
                success=True,
                issue_id=issue_id,
                updated_code=None,
                message="Issue marked as fixed"
            )
        
        # Get the original submission
        submission = db.query(CodeSubmission).filter(CodeSubmission.id == issue.submission_id).first()
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        # Create issue object for the fixer
        from ai_agents import CodeIssue as AICodeIssue
        ai_issue = AICodeIssue(
            title=issue.title,
            description=issue.description,
            severity=issue.severity,
            category=issue.category,
            line_number=issue.line_number,
            code_snippet=issue.code_snippet,
            suggested_fix=issue.suggested_fix,
            fix_explanation=issue.fix_explanation
        )
        
        # Apply the fix
        updated_code, success = await code_fixer.apply_fix(
            submission.original_code, 
            ai_issue, 
            submission.language
        )
        
        if success:
            # Update the submission with fixed code
            submission.original_code = updated_code
            submission.updated_at = datetime.utcnow()
            
            # Mark issue as fixed
            issue.is_fixed = True
            issue.fixed_at = datetime.utcnow()
            
            db.commit()
            
            return FixIssueResponse(
                success=True,
                issue_id=issue_id,
                updated_code=updated_code,
                message="Fix applied successfully"
            )
        else:
            return FixIssueResponse(
                success=False,
                issue_id=issue_id,
                updated_code=None,
                message="Failed to apply fix automatically"
            )
            
    except Exception as e:
        db.rollback()
        logger.error(f"Fix application failed: {e}")
        raise HTTPException(status_code=500, detail=f"Fix failed: {str(e)}")

@app.get("/api/submissions/{submission_id}/code")
async def get_current_code(submission_id: int, db: Session = Depends(get_db)):
    """Get the current code for a submission (with any applied fixes)."""
    submission = db.query(CodeSubmission).filter(CodeSubmission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    return {
        "submission_id": submission_id,
        "current_code": submission.original_code,
        "language": submission.language,
        "filename": submission.filename,
        "last_updated": submission.updated_at.isoformat()
    }

# Legacy endpoint for backward compatibility
@app.post("/review")
async def review_code_legacy(request: CodeReviewRequest, db: Session = Depends(get_db)):
    """Legacy endpoint - redirects to new submission API."""
    submission = await create_submission(request, db)
    
    # Format response to match old API
    if submission.analysis:
        issues_text = "\n".join([
            f"**{issue.title}** ({issue.severity.upper()})\n{issue.description}\n"
            for issue in submission.analysis.issues
        ])
        
        review_text = f"""
        Overall Score: {submission.analysis.overall_score}/100
        
        Issues Found:
        {issues_text}
        
        {submission.analysis.analysis_summary}
        """
    else:
        review_text = "Analysis pending..."
    
    return {
        "status": "success",
        "language": submission.language,
        "review": review_text,
        "timestamp": submission.created_at.isoformat(),
        "model_used": submission.analysis.model_used if submission.analysis else "unknown",
        "submission_id": submission.id
    }

@app.get("/languages")
async def get_supported_languages():
    """Get list of supported programming languages."""
    return {
        "languages": [
            {"name": "Python", "value": "python"},
            {"name": "JavaScript", "value": "javascript"},
            {"name": "TypeScript", "value": "typescript"},
            {"name": "Java", "value": "java"},
            {"name": "C++", "value": "cpp"},
            {"name": "C#", "value": "csharp"},
            {"name": "Go", "value": "go"},
            {"name": "Rust", "value": "rust"},
            {"name": "PHP", "value": "php"},
            {"name": "Ruby", "value": "ruby"}
        ]
    }

if __name__ == "__main__":
    logger.info("Starting Enhanced Code Review API server...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )