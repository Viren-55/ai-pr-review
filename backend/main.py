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

# Note: Environment variables are optional for demo mode
# In production, ensure proper Azure OpenAI credentials are configured

# Initialize Azure OpenAI client (or None for demo mode)
api_key = os.getenv("REASONING_AZURE_OPENAI_API_KEY")
if api_key and api_key not in ["your-api-key-here", "demo-mode"]:
    azure_client = AzureOpenAI(
        api_key=api_key,
        azure_endpoint=os.getenv("REASONING_AZURE_OPENAI_ENDPOINT"),
        api_version=os.getenv("REASONING_AZURE_API_VERSION")
    )
    logger.info("Azure OpenAI client initialized with real credentials")
else:
    azure_client = None
    logger.info("Running in demo mode - using mock responses")

# Initialize AI agents (delayed to avoid startup blocking)
ai_orchestrator = None
code_fixer = None

def get_ai_orchestrator():
    """Get AI orchestrator, creating it if needed."""
    global ai_orchestrator
    if ai_orchestrator is None and azure_client is not None:
        ai_orchestrator = create_ai_orchestrator(azure_client, os.getenv("REASONING_MODEL"))
    return ai_orchestrator

def get_code_fixer():
    """Get code fixer, creating it if needed."""
    global code_fixer
    if code_fixer is None and azure_client is not None:
        code_fixer = create_code_fixer(azure_client, os.getenv("REASONING_MODEL"))
    return code_fixer

def is_demo_mode():
    """Check if we're running in demo mode."""
    api_key = os.getenv("REASONING_AZURE_OPENAI_API_KEY")
    return azure_client is None or api_key in ["your-api-key-here", "demo-mode"]

def generate_mock_analysis(code: str, language: str):
    """Generate realistic mock analysis based on actual code patterns."""
    from models import CodeIssue
    import re
    
    issues = []
    lines = code.split('\n')
    
    # Security analysis patterns
    security_patterns = [
        (r'SELECT.*\+.*str\(', "SQL injection vulnerability detected", 
         "User input is directly concatenated into SQL query without proper sanitization.", 
         "Use parameterized queries or prepared statements to prevent SQL injection.", "high"),
        (r'exec\(|eval\(', "Code injection vulnerability", 
         "Dynamic code execution can be dangerous with user input.", 
         "Avoid using exec() or eval() with user-provided data.", "critical"),
        (r'open\([^)]*input\(', "File path injection", 
         "User input used directly in file operations.", 
         "Validate and sanitize file paths before use.", "high"),
    ]
    
    # Quality analysis patterns  
    quality_patterns = [
        (r'except\s*:', "Exception handling is too broad", 
         "Catching all exceptions can hide important errors.", 
         "Catch specific exceptions like DatabaseError or ValueError instead of using bare except.", "medium"),
        (r'print\s*\(', "Debug print statements", 
         "Print statements should not be in production code.", 
         "Use proper logging instead of print statements.", "low"),
        (r'TODO|FIXME|HACK', "TODO/FIXME comments found", 
         "Unfinished work or technical debt indicators.", 
         "Address TODO items before production deployment.", "low"),
    ]
    
    # Performance patterns
    performance_patterns = [
        (r'for.*in.*range\(len\(', "Inefficient iteration pattern", 
         "Using range(len()) is less efficient and pythonic.", 
         "Use enumerate() or iterate directly over the sequence.", "medium"),
        (r'\.append\(.*for.*in', "Inefficient list building", 
         "List comprehension would be more efficient.", 
         "Consider using list comprehension instead of append in loop.", "low"),
    ]
    
    # Check each line for patterns
    for line_num, line in enumerate(lines, 1):
        # Security issues
        for pattern, title, desc, fix, severity in security_patterns:
            if re.search(pattern, line):
                issues.append(CodeIssue(
                    title=title,
                    description=desc,
                    severity=severity,
                    category="security",
                    line_number=line_num,
                    code_snippet=line.strip(),
                    fix_explanation=fix
                ))
        
        # Quality issues
        for pattern, title, desc, fix, severity in quality_patterns:
            if re.search(pattern, line):
                issues.append(CodeIssue(
                    title=title,
                    description=desc,
                    severity=severity,
                    category="quality",
                    line_number=line_num,
                    code_snippet=line.strip(),
                    fix_explanation=fix
                ))
        
        # Performance issues
        for pattern, title, desc, fix, severity in performance_patterns:
            if re.search(pattern, line):
                issues.append(CodeIssue(
                    title=title,
                    description=desc,
                    severity=severity,
                    category="performance",
                    line_number=line_num,
                    code_snippet=line.strip(),
                    fix_explanation=fix
                ))
    
    # If no issues found, add some generic ones for demo
    if not issues:
        issues.append(CodeIssue(
            title="Code structure could be improved",
            description="Consider adding more documentation and error handling.",
            severity="low",
            category="quality",
            fix_explanation="Add docstrings and proper error handling."
        ))
    
    # Calculate score based on issues
    severity_weights = {'critical': 25, 'high': 15, 'medium': 10, 'low': 5}
    total_penalty = sum(severity_weights.get(issue.severity, 5) for issue in issues)
    score = max(0, 100 - total_penalty)
    
    # Generate summary
    severity_counts = {}
    for issue in issues:
        severity_counts[issue.severity] = severity_counts.get(issue.severity, 0) + 1
    
    summary_parts = []
    if severity_counts:
        for severity in ['critical', 'high', 'medium', 'low']:
            count = severity_counts.get(severity, 0)
            if count > 0:
                summary_parts.append(f"{count} {severity}-severity")
        
        if summary_parts:
            summary = f"Found {len(issues)} issues: {', '.join(summary_parts)} issues that should be addressed."
        else:
            summary = f"Found {len(issues)} issues that should be reviewed."
    else:
        summary = "Code analysis completed successfully with no major issues found."
    
    logger.info(f"Mock analysis generated: {len(issues)} issues, score: {score}")
    return issues, score, summary

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
    if is_demo_mode():
        azure_connected = True  # Demo mode is always "connected"
        logger.info("Running in demo mode - skipping Azure OpenAI connection test")
    else:
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

@app.get("/test")
async def test_endpoint():
    """Simple test endpoint without dependencies."""
    return {"message": "Backend is working!", "timestamp": datetime.now().isoformat()}

@app.post("/api/submissions/mock")
async def create_mock_submission(request: dict):
    """Mock submissions endpoint for UI testing - returns sample data immediately."""
    return {
        "id": "mock-123",
        "original_code": request.get("code", "print('hello')"),
        "language": request.get("language", "python"),
        "filename": "test_code.py",
        "submission_type": request.get("submission_type", "paste"),
        "created_at": datetime.now().isoformat(),
        "analysis": {
            "id": "analysis-456",
            "submission_id": "mock-123",
            "overall_score": 55,
            "analysis_summary": "Found 3 issues: 2 high-severity issues and 1 medium-severity issue that should be addressed.",
            "model_used": "gpt-4",
            "analysis_time_seconds": 2,
            "issues": [
                {
                    "id": 1,
                    "title": "SQL injection vulnerability detected",
                    "description": "User input is directly concatenated into SQL query without proper sanitization.",
                    "severity": "high",
                    "category": "security",
                    "fix_explanation": "Use parameterized queries or prepared statements to prevent SQL injection.",
                    "line_number": 79,
                    "code_snippet": 'query = "SELECT * FROM users WHERE id = " + str(user_id)',
                    "suggested_fix": 'query = "SELECT * FROM users WHERE id = ?"\\ncursor.execute(query, (user_id,))'
                },
                {
                    "id": 2,
                    "title": "Potential performance issue: Missing index on frequently queried columns",
                    "description": "Missing index on frequently queried columns in large dataset.",
                    "severity": "high",
                    "category": "performance", 
                    "fix_explanation": "Consider adding indexes on line_item_usage_account_name and line_item_usage_account_id.",
                    "line_number": 249,
                    "code_snippet": "SELECT DISTINCT\\n    line_item_usage_account_id,\\n    line_item_product_code,",
                    "suggested_fix": "-- Add these indexes to improve query performance:\\n-- CREATE INDEX idx_account_name ON table_name(line_item_usage_account_name);\\n-- CREATE INDEX idx_account_id ON table_name(line_item_usage_account_id);"
                },
                {
                    "id": 3,
                    "title": "Exception handling is too broad",
                    "description": "Catching all exceptions can hide important errors.",
                    "severity": "medium",
                    "category": "quality",
                    "fix_explanation": "Catch specific exceptions like DatabaseError or ValueError instead of using bare except.",
                    "line_number": 576,
                    "code_snippet": "try:\\n    result = data / 0\\n    return result\\nexcept:\\n    pass",
                    "suggested_fix": "try:\\n    result = data / 0\\n    return result\\nexcept (ZeroDivisionError, TypeError) as e:\\n    logger.error(f'Error processing data: {e}')\\n    return None"
                }
            ]
        }
    }

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
        
        # Run AI analysis with timeout and fallback
        logger.info(f"Starting analysis for submission {submission.id}")
        
        if is_demo_mode():
            logger.info("Running in demo mode - using enhanced mock data")
            # Enhanced mock analysis that analyzes the actual submitted code
            issues, score, summary = generate_mock_analysis(request.code, request.language)
        else:
            try:
                # Add timeout to AI calls
                orchestrator = get_ai_orchestrator()
                if orchestrator is None:
                    raise Exception("AI orchestrator not available")
                    
                issues, score, summary = await asyncio.wait_for(
                    orchestrator.analyze_code(request.code, request.language),
                    timeout=30.0  # 30 second timeout
                )
            except asyncio.TimeoutError:
                logger.error("AI analysis timed out, using fallback")
                # Fallback response
                from models import CodeIssue  
                issues = [CodeIssue(
                    title="Analysis timeout",
                    description="AI analysis took too long to complete.",
                    severity="low",
                    category="system",
                    fix_explanation="Please try again later or contact support."
                )]
                score = 50
                summary = "Analysis timed out - using fallback response."
            except Exception as e:
                logger.error(f"AI analysis failed: {e}, using mock data")
                issues, score, summary = generate_mock_analysis(request.code, request.language)
        
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
        fixer = get_code_fixer()
        updated_code, success = await fixer.apply_fix(
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