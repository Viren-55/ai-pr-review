"""Enhanced FastAPI backend for code review using Azure OpenAI with AI agents."""

from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Form, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
import uvicorn
from openai import AzureOpenAI, AsyncAzureOpenAI
from typing import List, Optional
import asyncio
import httpx

# Import our modules
from database import get_db, create_tables, database
from models import (
    CodeSubmission, CodeAnalysis, CodeIssue as DBCodeIssue,
    CodeSubmissionCreate, CodeSubmissionResponse, CodeAnalysisResponse, 
    CodeIssueResponse, FixIssueRequest, FixIssueResponse, HealthResponse,
    # GitHub Authentication Models
    GitHubUser, PRAnalysis, PRIssue,
    GitHubUserResponse, GitHubPRRequest, PRAnalysisResponse, PRIssueResponse,
    AuthCallbackRequest, AuthResponse
)
# Legacy ai_agents.py removed - using agents_v2 (Pydantic AI)
# from ai_agents import (
#     create_ai_orchestrator, create_code_fixer, 
#     AIAgentOrchestrator, CodeFixerAgent
# )
# GitHub Integration
from auth import (
    GitHubOAuth, GitHubAuthConfig, TokenManager, get_current_user, 
    authenticate_github_user, create_session_token
)
from github_integration import GitHubClient, GitHubURLParser, PRAnalyzer

# Load environment variables
load_dotenv(".env")  # Load from current directory (backend/)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic AI v2 Integration
try:
    from agents_v2 import AgentOrchestrator as PydanticAgentOrchestrator
    from api_v2 import router as api_v2_router, set_orchestrator
    PYDANTIC_AI_AVAILABLE = True
    logger.info("Pydantic AI v2 integration available")
except ImportError as e:
    PYDANTIC_AI_AVAILABLE = False
    logger.warning(f"Pydantic AI v2 not available: {e}")

# Note: Environment variables are optional for demo mode
# In production, ensure proper Azure OpenAI credentials are configured

# Initialize Azure OpenAI clients (both sync and async)
api_key = os.getenv("REASONING_AZURE_OPENAI_API_KEY")
azure_endpoint = os.getenv("REASONING_AZURE_OPENAI_ENDPOINT")
api_version = os.getenv("REASONING_AZURE_API_VERSION")

if api_key and api_key not in ["your-api-key-here", "demo-mode"]:
    # Sync client for legacy code
    azure_client = AzureOpenAI(
        api_key=api_key,
        azure_endpoint=azure_endpoint,
        api_version=api_version
    )
    # Async client for Pydantic AI agents
    async_azure_client = AsyncAzureOpenAI(
        api_key=api_key,
        azure_endpoint=azure_endpoint,
        api_version=api_version
    )
    logger.info(f"Azure OpenAI clients initialized - Endpoint: {azure_endpoint}, Model: {os.getenv('REASONING_MODEL')}")
else:
    azure_client = None
    async_azure_client = None
    logger.info("Running in demo mode - using mock responses")

# Initialize AI agents (delayed to avoid startup blocking)
ai_orchestrator = None
code_fixer = None
pydantic_orchestrator = None

def get_ai_orchestrator():
    """Get AI orchestrator, creating it if needed."""
    global ai_orchestrator
    if ai_orchestrator is None and async_azure_client is not None:
        # Use Pydantic AI orchestrator (agents_v2) with async client
        from agents_v2 import AgentOrchestrator
        ai_orchestrator = AgentOrchestrator(
            async_azure_client=async_azure_client,
            model_name=os.getenv("REASONING_MODEL")
        )
        logger.info("Pydantic AI orchestrator initialized with AsyncAzureOpenAI")
    return ai_orchestrator

def get_pydantic_orchestrator():
    """Get Pydantic AI orchestrator, creating it if needed."""
    global pydantic_orchestrator
    if PYDANTIC_AI_AVAILABLE and pydantic_orchestrator is None:
        pydantic_orchestrator = PydanticAgentOrchestrator(
            azure_client=azure_client,
            model_name=os.getenv("REASONING_MODEL")
        )
        # Set the orchestrator for API v2
        set_orchestrator(pydantic_orchestrator)
        logger.info("Pydantic AI orchestrator initialized")
    return pydantic_orchestrator

def get_code_fixer():
    """Get code fixer, creating it if needed."""
    global code_fixer
    if code_fixer is None and azure_client is not None:
        # Use Pydantic AI fix agent (agents_v2)
        from agents_v2 import CodeFixAgent
        code_fixer = CodeFixAgent(
            azure_client=azure_client,
            model_name=os.getenv("REASONING_MODEL")
        )
        logger.info("Pydantic AI fix agent initialized")
    return code_fixer

def is_demo_mode():
    """Check if we're running in demo mode."""
    # Demo mode is disabled - always use real AI analysis
    return False

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
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "https://localhost:3000",
        "https://localhost:3001"
    ],  # Specific origins required when using credentials
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include API v2 router if available
if PYDANTIC_AI_AVAILABLE:
    app.include_router(api_v2_router)
    logger.info("Pydantic AI v2 API routes registered")

# Create database tables on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database and connect."""
    create_tables()
    await database.connect()
    logger.info("Database connected and tables created")
    
    # Initialize Pydantic AI orchestrator if available
    # TODO: Fix Pydantic AI tool annotations before enabling
    # if PYDANTIC_AI_AVAILABLE:
    #     try:
    #         get_pydantic_orchestrator()
    #         logger.info("Pydantic AI orchestrator initialized on startup")
    #     except Exception as e:
    #         logger.warning(f"Failed to initialize Pydantic AI orchestrator: {e}")
    #         logger.info("Continuing with legacy agents only")
    logger.info("Pydantic AI orchestrator temporarily disabled - using legacy agents")

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
            
            response = azure_client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": "Hello, respond with just 'OK'"}]
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

# GitHub OAuth and Integration setup
github_oauth_config = None
github_oauth_client = None

try:
    github_oauth_config = GitHubAuthConfig.from_env()
    github_oauth_client = GitHubOAuth(github_oauth_config)
    logger.info("GitHub OAuth configured successfully")
except ValueError as e:
    logger.warning(f"GitHub OAuth not configured: {e}")
except Exception as e:
    logger.error(f"Failed to initialize GitHub OAuth: {e}")

# Enhanced API endpoints

@app.get("/test")
async def test_endpoint():
    """Simple test endpoint without dependencies."""
    return {"message": "Backend is working!", "timestamp": datetime.now().isoformat()}

# GitHub Authentication Endpoints

@app.get("/auth/github/login")
async def github_login():
    """Initiate GitHub OAuth login flow."""
    if not github_oauth_client:
        raise HTTPException(
            status_code=503, 
            detail="GitHub OAuth not configured. Please set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET environment variables."
        )
    
    try:
        auth_url, state = github_oauth_client.generate_auth_url()
        
        # In a real application, you'd store the state in session/cache for CSRF protection
        # For now, we'll just return it to be handled by the frontend
        return {
            "auth_url": auth_url,
            "state": state
        }
        
    except Exception as e:
        logger.error(f"Failed to generate GitHub auth URL: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate GitHub authentication")

@app.post("/auth/github/callback", response_model=AuthResponse)
async def github_callback(request: AuthCallbackRequest, response: Response, db: Session = Depends(get_db)):
    """Handle GitHub OAuth callback."""
    if not github_oauth_client:
        raise HTTPException(status_code=503, detail="GitHub OAuth not configured")
    
    try:
        # Exchange code for token
        token_response = await github_oauth_client.exchange_code_for_token(
            request.code, request.state
        )
        
        access_token = token_response["access_token"]
        
        # Authenticate user and store in database
        user = await authenticate_github_user(access_token, db)
        
        # Create session token
        session_token = create_session_token(user.id, user.username)
        
        # Set session cookie
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax",
            max_age=86400  # 24 hours
        )
        
        return AuthResponse(
            success=True,
            user=GitHubUserResponse.from_orm(user),
            session_token=session_token,
            message=f"Successfully authenticated as {user.username}"
        )
        
    except Exception as e:
        logger.error(f"GitHub OAuth callback failed: {e}")
        return AuthResponse(
            success=False,
            user=None,
            session_token=None,
            message=f"Authentication failed: {str(e)}"
        )

@app.get("/auth/user", response_model=GitHubUserResponse)
async def get_current_authenticated_user(current_user: GitHubUser = Depends(get_current_user)):
    """Get current authenticated user information."""
    return GitHubUserResponse.from_orm(current_user)

@app.post("/auth/logout")
async def logout(response: Response):
    """Logout user by clearing session cookie."""
    response.delete_cookie("session_token")
    return {"message": "Successfully logged out"}

from pydantic import BaseModel

class TokenRequest(BaseModel):
    token: str

class PRReviewRequest(BaseModel):
    github_url: str
    language: str = "python"
    create_github_review: bool = False
    review_type: str = "COMMENT"  # APPROVE, REQUEST_CHANGES, COMMENT

@app.post("/auth/token/test")
async def test_token(request: TokenRequest):
    """Simple token test endpoint."""
    try:
        token = request.token
        logger.info(f"Received token: {token[:10]}...")
        
        # Test GitHub API directly
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                    "User-Agent": "CodeReview-Platform/1.0"
                }
            )
            
        logger.info(f"GitHub response: {response.status_code}")
        user_data = response.json() if response.status_code == 200 else None
        
        return {
            "status": response.status_code,
            "user": user_data.get("login") if user_data else None,
            "token_prefix": token[:10]
        }
        
    except Exception as e:
        logger.error(f"Test error: {e}")
        return {"error": str(e)}

@app.post("/auth/token/validate", response_model=AuthResponse)
async def validate_github_token(request: TokenRequest, http_response: Response, db: Session = Depends(get_db)):
    """Validate GitHub token and create session."""
    try:
        token = request.token
        if not token:
            return AuthResponse(
                success=False,
                user=None,
                session_token=None,
                message="Token is required"
            )

        # Create a simple GitHub client to validate token
        github_client = GitHubClient(token)
        
        try:
            # Get user info from GitHub
            async with httpx.AsyncClient() as client:
                github_response = await client.get(
                    "https://api.github.com/user",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Accept": "application/vnd.github+json",
                        "User-Agent": "CodeReview-Platform/1.0"
                    }
                )
                
            logger.info(f"GitHub API response status: {github_response.status_code}")
            
            if github_response.status_code != 200:
                logger.error(f"GitHub API error: {github_response.text}")
                return AuthResponse(
                    success=False,
                    user=None,
                    session_token=None,
                    message=f"Invalid GitHub token: {github_response.status_code}"
                )
                
            user_data = github_response.json()
            logger.info(f"GitHub user data: {user_data.get('login', 'unknown')}")
            
            # Check if user exists or create new user
            existing_user = db.query(GitHubUser).filter(
                GitHubUser.github_id == user_data["id"]
            ).first()
            
            if existing_user:
                user = existing_user
                # Update token
                token_manager = TokenManager()
                user.encrypted_token_data = token_manager.encrypt_token_data({"access_token": token})
                db.commit()
            else:
                # Create new user
                token_manager = TokenManager()
                user = GitHubUser(
                    github_id=user_data["id"],
                    username=user_data["login"],
                    email=user_data.get("email"),
                    avatar_url=user_data.get("avatar_url"),
                    encrypted_token_data=token_manager.encrypt_token_data({"access_token": token})
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            
            # Create session token
            session_token = create_session_token(user.id, user.username)
            
            # Set session cookie
            http_response.set_cookie(
                key="session_token",
                value=session_token,
                httponly=True,
                secure=False,
                samesite="lax",
                max_age=86400
            )
            
            return AuthResponse(
                success=True,
                user=GitHubUserResponse.from_orm(user),
                session_token=session_token,
                message=f"Successfully authenticated as {user.username}"
            )
            
        except Exception as e:
            logger.error(f"GitHub API error: {e}")
            return AuthResponse(
                success=False,
                user=None,
                session_token=None,
                message=f"GitHub API error: {str(e)}"
            )
            
    except Exception as e:
        logger.error(f"Token validation failed: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return AuthResponse(
            success=False,
            user=None,
            session_token=None,
            message=f"Authentication failed: {str(e)}"
        )

# GitHub PR Analysis Endpoints

@app.post("/api/github/pr/analyze", response_model=PRAnalysisResponse)
async def analyze_github_pr(
    request: GitHubPRRequest, 
    current_user: GitHubUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Analyze a GitHub Pull Request."""
    try:
        # Parse and validate PR URL
        pr_info = GitHubURLParser.parse_pr_url(request.github_url)
        if not pr_info:
            raise HTTPException(status_code=400, detail="Invalid GitHub PR URL")
        
        # Check if we already have this PR analysis
        existing_analysis = db.query(PRAnalysis).filter(
            PRAnalysis.user_id == current_user.id,
            PRAnalysis.pr_url == request.github_url
        ).first()
        
        if existing_analysis and existing_analysis.analysis_status == "completed":
            logger.info(f"Returning existing analysis for PR {pr_info.full_repo}#{pr_info.pr_number}")
            return PRAnalysisResponse.from_orm(existing_analysis)
        
        # Create new analysis record
        if not existing_analysis:
            pr_analysis = PRAnalysis(
                user_id=current_user.id,
                pr_url=request.github_url,
                repository=pr_info.full_repo,
                pr_number=pr_info.pr_number,
                analysis_status="pending"
            )
            db.add(pr_analysis)
            db.commit()
            db.refresh(pr_analysis)
        else:
            pr_analysis = existing_analysis
            pr_analysis.analysis_status = "pending"
            pr_analysis.error_message = None
            db.commit()
        
        # Get user's GitHub token
        token_manager = TokenManager()
        github_token = token_manager.extract_access_token(current_user.encrypted_token_data)
        
        # Initialize GitHub client and PR analyzer
        github_client = GitHubClient(github_token)
        
        # Also initialize CLI tools for comprehensive analysis
        try:
            from tools import AIGitHubToolkit
            github_toolkit = AIGitHubToolkit(github_token)
        except ImportError as e:
            logger.warning(f"GitHub CLI tools not available: {e}")
            github_toolkit = None
        
        if is_demo_mode():
            # Use real GitHub data but mock AI analysis for demo mode
            logger.info("Running PR analysis in demo mode - fetching real PR data")
            
            try:
                # Fetch real PR data even in demo mode
                pr_data = await github_client.get_pr_info(pr_info)
                files_data = await github_client.get_pr_files(pr_info)
                
                # Use real PR metadata but mock analysis
                mock_analysis = {
                    "pr_info": {
                        "url": request.github_url,
                        "repository": pr_info.full_repo,
                        "pr_number": pr_info.pr_number,
                        "title": pr_data.get("title", "Untitled PR"),
                        "description": pr_data.get("body", "No description"),
                        "author": pr_data.get("user", {}).get("login", "unknown"),
                        "created_at": pr_data.get("created_at", ""),
                        "state": pr_data.get("state", "unknown")
                    },
                    "changes_summary": {
                        "files_changed": len(files_data),
                        "additions": pr_data.get("additions", 0),
                        "deletions": pr_data.get("deletions", 0),
                        "changed_files": [f["filename"] for f in files_data]
                    },
                    "analysis": {
                        "overall_score": 85,
                        "issues": [
                            {
                                "title": "Demo analysis result",
                                "description": "This is a demo analysis. In production, AI agents would analyze the actual code changes.",
                                "severity": "low",
                                "category": "demo",
                                "file_path": files_data[0]["filename"] if files_data else "demo.html",
                                "line_number": 1,
                                "suggested_fix": "This is demo mode - no real issues detected",
                                "fix_explanation": "Enable Azure OpenAI for real analysis"
                            }
                        ],
                        "analysis_summary": f"Demo analysis of PR with {len(files_data)} files changed. Real AI analysis available with Azure OpenAI configuration.",
                        "files_analyzed": len(files_data)
                    },
                    "metadata": {
                        "analysis_time_seconds": 1.5,
                        "analyzed_at": datetime.now().isoformat(),
                        "language": request.language,
                        "demo_mode": True
                    }
                }
                
                analysis_results = mock_analysis
                
            except Exception as e:
                logger.error(f"Failed to fetch real PR data in demo mode: {e}")
                # Fallback to completely mock data
                mock_analysis = {
                    "pr_info": {
                        "url": request.github_url,
                        "repository": pr_info.full_repo,
                        "pr_number": pr_info.pr_number,
                        "title": "Demo PR Analysis (API Error)",
                        "description": "Could not fetch real PR data",
                        "author": "demo-user",
                        "created_at": datetime.now().isoformat(),
                        "state": "open"
                    },
                    "changes_summary": {
                        "files_changed": 1,
                        "additions": 0,
                        "deletions": 1,
                        "changed_files": ["demo.html"]
                    },
                    "analysis": {
                        "overall_score": 75,
                        "issues": [
                            {
                                "title": "Demo mode - API error",
                                "description": "Could not fetch real PR data. This is a demo response.",
                                "severity": "low",
                                "category": "demo",
                                "file_path": "demo.html",
                                "line_number": 1,
                                "suggested_fix": "Check GitHub API access",
                                "fix_explanation": "Ensure GitHub token has proper permissions"
                            }
                        ],
                        "analysis_summary": f"Demo mode with API error: {str(e)}",
                        "files_analyzed": 1
                    },
                    "metadata": {
                        "analysis_time_seconds": 1.0,
                        "analyzed_at": datetime.now().isoformat(),
                        "language": request.language,
                        "demo_mode": True
                    }
                }
                
                analysis_results = mock_analysis
            
        else:
            # Get AI orchestrator
            orchestrator = get_ai_orchestrator()
            if not orchestrator:
                await github_client.close()
                raise HTTPException(status_code=503, detail="AI analysis service not available")
            
            # Gather comprehensive PR context using CLI tools
            pr_info_parsed = GitHubURLParser.parse_pr_url(request.github_url)
            if pr_info_parsed and github_toolkit and github_toolkit.is_available:
                logger.info("Using GitHub CLI for comprehensive PR analysis")
                pr_context = github_toolkit.analyze_pr_context(pr_info_parsed.full_repo, pr_info_parsed.pr_number)
                
                # Use both API and CLI data for analysis
                pr_analyzer = PRAnalyzer(github_client, orchestrator)
                analysis_results = await pr_analyzer.analyze_pr(request.github_url, request.language)
                
                # Enhance with CLI data
                if pr_context.get("analysis_ready"):
                    analysis_results["metadata"]["cli_enhanced"] = True
                    analysis_results["metadata"]["cli_context"] = {
                        "reviews_count": len(pr_context["data"].get("reviews", [])),
                        "comments_count": len(pr_context["data"].get("comments", [])),
                        "languages": pr_context["data"].get("languages", {})
                    }
            else:
                # Fallback to API-only analysis
                logger.info("Using API-only PR analysis")
                pr_analyzer = PRAnalyzer(github_client, orchestrator)
                analysis_results = await pr_analyzer.analyze_pr(request.github_url, request.language)
        
        # Update PR analysis record with results
        pr_data = analysis_results["pr_info"]
        changes_data = analysis_results["changes_summary"]
        ai_analysis = analysis_results["analysis"]
        
        pr_analysis.pr_title = pr_data["title"]
        pr_analysis.pr_description = pr_data.get("description")
        pr_analysis.overall_score = ai_analysis["overall_score"]
        pr_analysis.analysis_summary = ai_analysis["analysis_summary"]
        pr_analysis.model_used = os.getenv("REASONING_MODEL", "demo")
        pr_analysis.analysis_time_seconds = analysis_results.get("metadata", {}).get("analysis_time_seconds", 2.0)
        pr_analysis.files_changed = changes_data["changed_files"]
        pr_analysis.additions = changes_data["additions"]
        pr_analysis.deletions = changes_data["deletions"]
        pr_analysis.analysis_status = "completed"
        
        db.commit()
        
        # Create PR issues
        db_issues = []
        for issue_data in ai_analysis["issues"]:
            pr_issue = PRIssue(
                pr_analysis_id=pr_analysis.id,
                title=issue_data["title"],
                description=issue_data["description"],
                severity=issue_data["severity"],
                category=issue_data["category"],
                file_path=issue_data.get("file_path"),
                line_number=issue_data.get("line_number"),
                code_snippet=issue_data.get("code_snippet"),
                suggested_fix=issue_data.get("suggested_fix"),
                fix_explanation=issue_data.get("fix_explanation")
            )
            db.add(pr_issue)
            db_issues.append(pr_issue)
        
        db.commit()
        
        # Refresh all objects
        db.refresh(pr_analysis)
        for issue in db_issues:
            db.refresh(issue)
        
        await github_client.close()
        
        logger.info(f"PR analysis completed for {pr_info.full_repo}#{pr_info.pr_number}")
        return PRAnalysisResponse.from_orm(pr_analysis)
        
    except Exception as e:
        # Update analysis record with error
        if 'pr_analysis' in locals():
            pr_analysis.analysis_status = "failed"
            pr_analysis.error_message = str(e)
            db.commit()
        
        logger.error(f"PR analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"PR analysis failed: {str(e)}")

@app.get("/api/github/pr/{analysis_id}", response_model=PRAnalysisResponse) 
async def get_pr_analysis(
    analysis_id: int,
    current_user: GitHubUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific PR analysis."""
    analysis = db.query(PRAnalysis).filter(
        PRAnalysis.id == analysis_id,
        PRAnalysis.user_id == current_user.id
    ).first()
    
    if not analysis:
        raise HTTPException(status_code=404, detail="PR analysis not found")
    
    return PRAnalysisResponse.from_orm(analysis)

@app.get("/api/github/pr/analyses", response_model=List[PRAnalysisResponse])
async def list_pr_analyses(
    current_user: GitHubUser = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List user's PR analyses."""
    analyses = db.query(PRAnalysis).filter(
        PRAnalysis.user_id == current_user.id
    ).offset(skip).limit(limit).order_by(PRAnalysis.created_at.desc()).all()
    
    return [PRAnalysisResponse.from_orm(analysis) for analysis in analyses]

@app.post("/api/github/pr/review")
async def create_comprehensive_pr_review(
    request: PRReviewRequest,
    current_user: GitHubUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a comprehensive PR review using AI analysis and GitHub CLI tools.
    
    This endpoint:
    1. Analyzes the PR using AI agents
    2. Formats the analysis as a professional review
    3. Optionally posts the review to GitHub
    """
    try:
        # Parse PR URL
        pr_info = GitHubURLParser.parse_pr_url(request.github_url)
        if not pr_info:
            raise HTTPException(status_code=400, detail="Invalid GitHub PR URL")
        
        # Get user's GitHub token
        token_manager = TokenManager()
        github_token = token_manager.extract_access_token(current_user.encrypted_token_data)
        
        # Initialize tools
        github_client = GitHubClient(github_token)
        try:
            from tools import AIGitHubToolkit
            github_toolkit = AIGitHubToolkit(github_token)
        except ImportError as e:
            logger.warning(f"GitHub CLI tools not available: {e}")
            github_toolkit = None
        
        logger.info(f"Creating comprehensive review for PR {pr_info.full_repo}#{pr_info.pr_number}")
        
        if is_demo_mode():
            # Demo mode - create mock review
            mock_analysis = {
                "pr_info": {
                    "url": request.github_url,
                    "repository": pr_info.full_repo,
                    "pr_number": pr_info.pr_number,
                    "title": "Demo PR Review",
                    "author": "demo-user"
                },
                "analysis": {
                    "overall_score": 85,
                    "issues": [
                        {
                            "title": "Code structure could be improved",
                            "description": "Consider breaking down this large function into smaller, more focused functions",
                            "severity": "medium",
                            "category": "quality",
                            "file_path": "src/main.py",
                            "line_number": 42,
                            "suggested_fix": "Extract logic into separate helper functions"
                        }
                    ],
                    "analysis_summary": "Overall good code quality with minor improvements needed.",
                    "files_analyzed": 3
                },
                "metadata": {
                    "analysis_time_seconds": 2.5,
                    "analyzed_at": datetime.now().isoformat(),
                    "language": request.language
                }
            }
            
            # Format as review
            if github_toolkit:
                review_feedback = github_toolkit.provide_pr_feedback(
                    pr_info.full_repo, 
                    pr_info.pr_number, 
                    mock_analysis,
                    create_review=request.create_github_review
                )
            else:
                # Fallback formatting without CLI tools
                review_feedback = {
                    "success": True,
                    "review_body": f"## AI Code Review\n\n**Overall Score:** 85/100\n\n{mock_analysis['analysis']['analysis_summary']}\n\n*Note: Limited functionality - GitHub CLI tools not available*",
                    "review_created": False
                }
            
            return {
                "success": True,
                "repository": pr_info.full_repo,
                "pr_number": pr_info.pr_number,
                "review_body": review_feedback.get("review_body"),
                "review_created": review_feedback.get("review_created", False),
                "github_review_url": None,
                "analysis_summary": mock_analysis["analysis"]["analysis_summary"],
                "demo_mode": True
            }
        
        else:
            # Real analysis mode
            orchestrator = get_ai_orchestrator()
            if not orchestrator:
                raise HTTPException(status_code=503, detail="AI analysis service not available")
            
            # Run comprehensive analysis
            pr_analyzer = PRAnalyzer(github_client, orchestrator)
            analysis_results = await pr_analyzer.analyze_pr(request.github_url, request.language)
            
            # Enhance with CLI context if available
            if github_toolkit and github_toolkit.is_available:
                pr_context = github_toolkit.analyze_pr_context(pr_info.full_repo, pr_info.pr_number)
                if pr_context.get("analysis_ready"):
                    analysis_results["metadata"]["cli_enhanced"] = True
                    logger.info("Enhanced analysis with GitHub CLI context")
            
            # Create formatted review
            if github_toolkit:
                review_feedback = github_toolkit.provide_pr_feedback(
                    pr_info.full_repo,
                    pr_info.pr_number,
                    analysis_results,
                    create_review=request.create_github_review
                )
            else:
                # Fallback formatting
                score = analysis_results["analysis"]["overall_score"]
                review_feedback = {
                    "success": True,
                    "review_body": f"## AI Code Review\n\n**Overall Score:** {score}/100\n\n{analysis_results['analysis']['analysis_summary']}\n\n*Note: Limited functionality - GitHub CLI tools not available*",
                    "review_created": False
                }
            
            # Store review in database if created
            review_url = None
            if review_feedback.get("review_created"):
                review_url = f"https://github.com/{pr_info.full_repo}/pull/{pr_info.pr_number}"
                logger.info(f"Successfully created GitHub review for PR {pr_info.full_repo}#{pr_info.pr_number}")
            
            await github_client.close()
            
            return {
                "success": True,
                "repository": pr_info.full_repo,
                "pr_number": pr_info.pr_number,
                "review_body": review_feedback.get("review_body"),
                "review_created": review_feedback.get("review_created", False),
                "github_review_url": review_url,
                "analysis_summary": analysis_results["analysis"]["analysis_summary"],
                "overall_score": analysis_results["analysis"]["overall_score"],
                "issues_found": len(analysis_results["analysis"]["issues"]),
                "files_analyzed": analysis_results["analysis"]["files_analyzed"],
                "demo_mode": False
            }
            
    except Exception as e:
        logger.error(f"PR review creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create PR review: {str(e)}")

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

@app.post("/api/submissions")  # Removed response_model to allow extra fields like timing
async def create_submission(request: CodeSubmissionCreate, db: Session = Depends(get_db)):
    """Submit code for analysis."""
    import time
    start_time = time.time()
    logger.info(f"[TIMING] Starting code submission analysis")
    
    try:
        # Validate input
        t_validation_start = time.time()
        if not request.code.strip():
            raise HTTPException(status_code=400, detail="Code cannot be empty")
        t_validation_end = time.time()
        validation_time_ms = (t_validation_end - t_validation_start) * 1000
        logger.info(f"[TIMING] Input validation: {validation_time_ms:.2f}ms")
        
        # Create submission record
        t_db_submission_start = time.time()
        submission = CodeSubmission(
            original_code=request.code,
            language=request.language,
            filename=request.filename,
            submission_type=request.submission_type
        )
        
        db.add(submission)
        db.commit()
        db.refresh(submission)
        t_db_submission_end = time.time()
        db_submission_time_ms = (t_db_submission_end - t_db_submission_start) * 1000
        logger.info(f"[TIMING] Database submission record: {db_submission_time_ms:.2f}ms")
        
        # Run AI analysis with timeout and fallback
        t_ai_analysis_start = time.time()
        logger.info(f"[TIMING] Starting AI analysis for submission {submission.id}")
        
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
                    
                # Use Pydantic AI orchestrator with proper context
                t_context_start = time.time()
                from agents_v2 import CodeContext
                context = CodeContext(
                    code=request.code,
                    language=request.language,
                    file_path=request.filename
                )
                logger.info(f"[TIMING] Context creation: {(time.time() - t_context_start)*1000:.2f}ms")
                
                t_orchestrator_start = time.time()
                result = await asyncio.wait_for(
                    orchestrator.analyze_code(context),
                    timeout=60.0  # 60 second timeout - increased for complex analysis
                )
                logger.info(f"[TIMING] AI orchestrator analysis: {(time.time() - t_orchestrator_start)*1000:.2f}ms")
                
                # Extract issues, score, and summary from AnalysisResult
                issues = result.issues if result else []
                score = result.overall_score if result else 50
                summary = result.summary if result else "Analysis completed"
                logger.info(f"[TIMING] AI analysis complete - found {len(issues)} issues, score: {score}")
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
                logger.error(f"[TIMING] AI analysis failed after {(time.time() - t_ai_analysis_start)*1000:.2f}ms: {e}")
                logger.info("[TIMING] Falling back to mock analysis")
                t_mock_start = time.time()
                issues, score, summary = generate_mock_analysis(request.code, request.language)
                logger.info(f"[TIMING] Mock analysis: {(time.time() - t_mock_start)*1000:.2f}ms")
        
        # Create analysis record
        t_db_storage_start = time.time()
        actual_analysis_time = time.time() - t_ai_analysis_start
        ai_analysis_time_ms = actual_analysis_time * 1000
        analysis = CodeAnalysis(
            submission_id=submission.id,
            overall_score=score,
            analysis_summary=summary,
            model_used=os.getenv("REASONING_MODEL"),
            analysis_time_seconds=int(actual_analysis_time)
        )
        
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        t_analysis_record_end = time.time()
        analysis_record_time_ms = (t_analysis_record_end - t_db_storage_start) * 1000
        logger.info(f"[TIMING] Database analysis record: {analysis_record_time_ms:.2f}ms")
        
        # Create issue records
        t_issues_start = time.time()
        db_issues = []
        for issue in issues:
            # Handle both Pydantic AI CodeIssue and legacy format
            line_num = None
            if hasattr(issue, 'location') and issue.location:
                line_num = issue.location.line_start
            elif hasattr(issue, 'line_number'):
                line_num = issue.line_number
            
            db_issue = DBCodeIssue(
                submission_id=submission.id,
                title=issue.title,
                description=issue.description,
                severity=issue.severity.value if hasattr(issue.severity, 'value') else issue.severity,
                category=issue.category.value if hasattr(issue.category, 'value') else issue.category,
                line_number=line_num,
                code_snippet=getattr(issue, 'code_snippet', None),
                suggested_fix=getattr(issue, 'suggested_fix', None),
                fix_explanation=getattr(issue, 'fix_explanation', None)
            )
            db.add(db_issue)
            db_issues.append(db_issue)
        
        db.commit()
        
        # Refresh all objects to get IDs
        for db_issue in db_issues:
            db.refresh(db_issue)
        t_issues_end = time.time()
        issues_storage_time_ms = (t_issues_end - t_issues_start) * 1000
        logger.info(f"[TIMING] Database issues ({len(issues)} records): {issues_storage_time_ms:.2f}ms")
        
        total_time = time.time() - start_time
        logger.info(f"[TIMING] ✅ TOTAL submission time: {total_time*1000:.2f}ms ({total_time:.2f}s)")
        logger.info(f"[TIMING] Analysis complete for submission {submission.id}: {len(issues)} issues, score {score}")
        
        # Calculate timing breakdown for frontend
        # Total database storage time = analysis record + issues records
        total_db_storage_time_ms = analysis_record_time_ms + issues_storage_time_ms
        
        timing_breakdown = {
            "total_time_ms": round(total_time * 1000, 2),
            "total_time_seconds": round(total_time, 2),
            "steps": {
                "validation": f"{validation_time_ms:.1f}ms" if validation_time_ms >= 0.1 else "< 0.1ms",
                "database_submission": f"{db_submission_time_ms:.1f}ms",
                "ai_analysis": f"{ai_analysis_time_ms:.1f}ms",
                "database_storage": f"{total_db_storage_time_ms:.1f}ms"
            },
            "agents_used": 3,
            "issues_found": len(issues)
        }
        
        # Return full submission with analysis and timing
        response_data = CodeSubmissionResponse(
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
        
        # Add timing metadata to response
        # Use model_dump for Pydantic v2 compatibility
        try:
            response_dict = response_data.model_dump() if hasattr(response_data, 'model_dump') else response_data.dict()
        except:
            response_dict = dict(response_data)
        
        response_dict['timing'] = timing_breakdown
        
        return response_dict
        
    except Exception as e:
        db.rollback()
        total_time = time.time() - start_time
        logger.error(f"[TIMING] ❌ Submission FAILED after {total_time*1000:.2f}ms: {e}")
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
        
        # Create recommendation for the fixer
        from agents_v2 import CodeRecommendation
        
        recommendation = CodeRecommendation(
            issue_id=str(issue.id),
            title=issue.title,
            description=issue.description,
            original_code=issue.code_snippet or "",
            suggested_code=issue.suggested_fix or "",
            confidence=0.8,
            impact="Fixes: " + issue.title
        )
        
        # Apply the fix
        fixer = get_code_fixer()
        updated_code, operation = await fixer.apply_fix(
            submission.original_code, 
            recommendation
        )
        
        success = updated_code != submission.original_code
        
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

# GitHub PR Review endpoint for frontend integration
@app.post("/review/github-pr")
async def analyze_pr_for_review(request: dict, db: Session = Depends(get_db)):
    """Analyze GitHub PR and return review results for frontend."""
    try:
        pr_url = request.get("pr_url")
        language = request.get("language", "javascript")
        
        if not pr_url:
            raise HTTPException(status_code=400, detail="PR URL is required")
        
        # Parse PR URL
        pr_info = GitHubURLParser.parse_pr_url(pr_url)
        if not pr_info:
            raise HTTPException(status_code=400, detail="Invalid GitHub PR URL")
        
        logger.info(f"Analyzing PR: {pr_info.full_repo}#{pr_info.pr_number}")
        
        # Create GitHub client with authentication token
        github_token = "${GITHUB_TOKEN:-GITHUB_TOKEN_NOT_SET}"
        github_client = GitHubClient(access_token=github_token)
        
        if is_demo_mode():
            # Use real GitHub data but mock AI analysis for demo mode
            logger.info("Running PR analysis in demo mode - fetching real PR data")
            
            # Fetch real PR data even in demo mode
            pr_data = await github_client.get_pr_info(pr_info)
            files_data = await github_client.get_pr_files(pr_info)
            
            # Also fetch the actual diff content for display
            try:
                diff_content = await github_client.get_pr_diff(pr_info)
            except Exception as e:
                logger.warning(f"Failed to fetch PR diff: {e}")
                diff_content = ""
            
            # Use real PR metadata but mock analysis
            mock_analysis = {
                "pr_info": {
                    "url": pr_url,
                    "repository": pr_info.full_repo,
                    "pr_number": pr_info.pr_number,
                    "title": pr_data.get("title", "Untitled PR"),
                    "description": pr_data.get("body", "No description"),
                    "author": pr_data.get("user", {}).get("login", "unknown"),
                    "created_at": pr_data.get("created_at", ""),
                    "updated_at": pr_data.get("updated_at", ""),
                    "state": pr_data.get("state", "open"),
                    "merged": pr_data.get("merged", False),
                    "mergeable": pr_data.get("mergeable"),
                    "base_branch": pr_data.get("base", {}).get("ref", "main"),
                    "head_branch": pr_data.get("head", {}).get("ref", "feature-branch")
                },
                "changes_summary": {
                    "files_changed": len(files_data) if files_data else 0,
                    "additions": pr_data.get("additions", 0),
                    "deletions": pr_data.get("deletions", 0),
                    "changed_files": [f.get("filename", "") for f in files_data] if files_data else [],
                    "file_types": {"source_code": len(files_data) if files_data else 0, "tests": 0, "documentation": 0, "configuration": 0, "other": 0}
                },
                "analysis": {
                    "overall_score": 85,
                    "issues": [
                        {
                            "title": "Documentation Update",
                            "description": "HTML file was modified - ensure content is valid and accessible",
                            "severity": "low",
                            "category": "documentation",
                            "line_number": None,
                            "code_snippet": "",
                            "suggested_fix": "Review the HTML changes for proper structure and accessibility",
                            "fix_explanation": "Ensure HTML modifications follow web standards",
                            "file_path": next(iter([f.get("filename", "") for f in files_data] if files_data else [""]), "")
                        }
                    ] if files_data else [],
                    "analysis_summary": f"Analyzed {len(files_data) if files_data else 0} changed files. This appears to be a documentation or HTML update. No critical issues detected." if files_data else "No files to analyze.",
                    "files_analyzed": len(files_data) if files_data else 0,
                    "total_lines_analyzed": pr_data.get("additions", 0) + pr_data.get("deletions", 0)
                },
                "metadata": {
                    "analysis_time_seconds": 2.0,
                    "analyzed_at": datetime.now().isoformat(),
                    "language": language,
                    "diff_size": 1024
                }
            }
            
            return {
                "status": "success",
                "analysis": mock_analysis,
                "timestamp": datetime.now().isoformat(),
                "demo_mode": True
            }
        else:
            # Production mode with real AI analysis
            orchestrator = get_ai_orchestrator()
            if not orchestrator:
                raise HTTPException(status_code=500, detail="AI orchestrator not available")
            
            # Create PR analyzer
            pr_analyzer = PRAnalyzer(github_client, orchestrator)
            
            # Run analysis
            analysis_results = await pr_analyzer.analyze_pr(pr_url, language)
            
            return {
                "status": "success", 
                "analysis": analysis_results,
                "timestamp": datetime.now().isoformat(),
                "demo_mode": False
            }
            
    except Exception as e:
        logger.error(f"PR analysis failed: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

# Legacy endpoint for backward compatibility
@app.post("/review")
async def review_code_legacy(request: CodeReviewRequest, db: Session = Depends(get_db)):
    """Legacy endpoint - redirects to new submission API."""
    submission = await create_submission(request, db)
    
    # Format response to match old API
    if submission.get('analysis'):
        analysis = submission['analysis']
        issues_text = "\n".join([
            f"**{issue['title']}** ({issue['severity'].upper()})\n{issue['description']}\n"
            for issue in analysis.get('issues', [])
        ])
        
        review_text = f"""
        Overall Score: {analysis.get('overall_score', 0)}/100
        
        Issues Found:
        {issues_text}
        
        {analysis.get('analysis_summary', '')}
        """
    else:
        review_text = "Analysis pending..."
    
    analysis = submission.get('analysis', {})
    return {
        "status": "success",
        "language": submission.get('language', 'unknown'),
        "review": review_text,
        "timestamp": submission.get('created_at'),
        "model_used": analysis.get('model_used', 'unknown') if analysis else "unknown",
        "submission_id": submission.get('id'),
        "timing": submission.get('timing', {})
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