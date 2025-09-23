"""FastAPI v2 endpoints for Pydantic AI agent integration."""

import asyncio
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json

from agents_v2 import (
    AgentOrchestrator,
    CodeContext,
    CodeRecommendation,
    AnalysisResult
)

logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(prefix="/api/v2", tags=["Pydantic AI v2"])

# Initialize orchestrator (will be set by main app)
orchestrator: Optional[AgentOrchestrator] = None


def set_orchestrator(orch: AgentOrchestrator):
    """Set the global orchestrator instance."""
    global orchestrator
    orchestrator = orch


# Request/Response Models
class AnalyzeRequest(BaseModel):
    """Request for code analysis."""
    code: str
    language: str = "python"
    file_path: Optional[str] = None
    include_recommendations: bool = True
    project_context: Optional[Dict[str, Any]] = None


class StreamingAnalysisResponse(BaseModel):
    """Streaming analysis response."""
    type: str
    analysis_id: str
    data: Dict[str, Any]
    timestamp: str


class ApplyRecommendationsRequest(BaseModel):
    """Request to apply recommendations."""
    code: str
    language: str = "python"
    file_path: Optional[str] = None
    recommendations: List[Dict[str, Any]]  # CodeRecommendation dicts
    session_id: Optional[str] = None


class SessionRequest(BaseModel):
    """Request to create editing session."""
    code: str
    language: str = "python"
    file_path: Optional[str] = None


class ValidationRequest(BaseModel):
    """Request for code validation."""
    code: str
    language: str = "python"
    session_id: Optional[str] = None


# WebSocket connection manager
class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.analysis_subscribers: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        # Remove from analysis subscribers
        for analysis_id, subscribers in self.analysis_subscribers.items():
            if websocket in subscribers:
                subscribers.remove(websocket)
    
    async def subscribe_to_analysis(self, websocket: WebSocket, analysis_id: str):
        """Subscribe a WebSocket to analysis updates."""
        if analysis_id not in self.analysis_subscribers:
            self.analysis_subscribers[analysis_id] = []
        self.analysis_subscribers[analysis_id].append(websocket)
    
    async def broadcast_analysis_update(self, analysis_id: str, update: Dict[str, Any]):
        """Broadcast analysis update to subscribers."""
        if analysis_id in self.analysis_subscribers:
            disconnected = []
            for websocket in self.analysis_subscribers[analysis_id]:
                try:
                    await websocket.send_json(update)
                except:
                    disconnected.append(websocket)
            
            # Remove disconnected WebSockets
            for ws in disconnected:
                self.analysis_subscribers[analysis_id].remove(ws)


# Global connection manager
manager = ConnectionManager()


# API Endpoints

@router.post("/analyze", response_model=Dict[str, Any])
async def analyze_code(request: AnalyzeRequest, background_tasks: BackgroundTasks):
    """Analyze code with Pydantic AI agents.
    
    Args:
        request: Analysis request
        background_tasks: Background task manager
        
    Returns:
        Analysis result or streaming info
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent orchestrator not available")
    
    try:
        # Create code context
        context = CodeContext(
            code=request.code,
            language=request.language,
            file_path=request.file_path,
            project_context=request.project_context or {}
        )
        
        # Run analysis
        result = await orchestrator.analyze_code(context, request.include_recommendations)
        
        return {
            "status": "success",
            "analysis": result.dict(),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/analyze/stream/{analysis_id}")
async def stream_analysis_progress(analysis_id: str):
    """Stream analysis progress for a specific analysis ID."""
    
    async def generate_updates():
        """Generate streaming updates."""
        # This would connect to the actual streaming analysis
        # For now, return a simple stream
        for i in range(5):
            yield f"data: {json.dumps({'progress': i * 20, 'status': f'Step {i+1}'})}\n\n"
            await asyncio.sleep(0.5)
        
        yield f"data: {json.dumps({'progress': 100, 'status': 'Complete'})}\n\n"
    
    return StreamingResponse(
        generate_updates(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.post("/recommendations/apply")
async def apply_recommendations(request: ApplyRecommendationsRequest):
    """Apply code recommendations.
    
    Args:
        request: Apply recommendations request
        
    Returns:
        Application results
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent orchestrator not available")
    
    try:
        # Create code context
        context = CodeContext(
            code=request.code,
            language=request.language,
            file_path=request.file_path
        )
        
        # Convert recommendation dicts to objects
        recommendations = [
            CodeRecommendation(**rec_data) 
            for rec_data in request.recommendations
        ]
        
        # Apply recommendations
        result = await orchestrator.apply_recommendations(
            context, 
            recommendations, 
            request.session_id
        )
        
        return {
            "status": "success",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to apply recommendations: {e}")
        raise HTTPException(status_code=500, detail=f"Application failed: {str(e)}")


@router.post("/session/create")
async def create_editing_session(request: SessionRequest):
    """Create a new interactive editing session.
    
    Args:
        request: Session creation request
        
    Returns:
        Session ID and initial status
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent orchestrator not available")
    
    try:
        # Create code context
        context = CodeContext(
            code=request.code,
            language=request.language,
            file_path=request.file_path
        )
        
        # Create session
        session_id = await orchestrator.create_editing_session(context)
        
        return {
            "status": "success",
            "session_id": session_id,
            "created_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise HTTPException(status_code=500, detail=f"Session creation failed: {str(e)}")


@router.get("/session/{session_id}/status")
async def get_session_status(session_id: str):
    """Get editing session status.
    
    Args:
        session_id: Session ID
        
    Returns:
        Session status
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent orchestrator not available")
    
    try:
        status = await orchestrator.get_session_status(session_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            "status": "success",
            "session_status": status,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session status: {e}")
        raise HTTPException(status_code=500, detail=f"Status retrieval failed: {str(e)}")


@router.post("/validate")
async def validate_code(request: ValidationRequest):
    """Validate code syntax and semantics.
    
    Args:
        request: Validation request
        
    Returns:
        Validation results
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Agent orchestrator not available")
    
    try:
        # Get editor agent
        editor_agent = orchestrator.agents.get('editor_agent')
        if not editor_agent:
            raise HTTPException(status_code=503, detail="Editor agent not available")
        
        # Validate code
        if request.session_id:
            # Validate session code
            validation = await editor_agent.agent.tools.validate_session_code(request.session_id)
        else:
            # Validate provided code directly
            # Create temporary session for validation
            context = CodeContext(
                code=request.code,
                language=request.language
            )
            temp_session_id = await editor_agent.create_session(context)
            validation = await editor_agent.agent.tools.validate_session_code(temp_session_id)
            
            # Clean up temporary session
            if temp_session_id in editor_agent.active_sessions:
                del editor_agent.active_sessions[temp_session_id]
        
        return {
            "status": "success",
            "validation": validation.dict(),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check for v2 API."""
    
    status = "healthy" if orchestrator else "degraded"
    
    agent_status = {}
    if orchestrator:
        for name, agent in orchestrator.agents.items():
            agent_status[name] = {
                "name": agent.name,
                "available": agent.model is not None
            }
    
    return {
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "agents": agent_status,
        "features": [
            "Pydantic AI Integration",
            "Streaming Analysis",
            "Interactive Editing",
            "Real-time Validation",
            "WebSocket Support"
        ]
    }


# WebSocket Endpoints

@router.websocket("/ws/analysis")
async def websocket_analysis(websocket: WebSocket):
    """WebSocket endpoint for real-time analysis updates."""
    await manager.connect(websocket)
    
    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            if message_type == "start_analysis":
                # Start analysis and stream results
                code = data.get("code", "")
                language = data.get("language", "python")
                file_path = data.get("file_path")
                
                if not orchestrator:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Agent orchestrator not available"
                    })
                    continue
                
                # Create context
                context = CodeContext(
                    code=code,
                    language=language,
                    file_path=file_path
                )
                
                # Stream analysis results
                try:
                    async for update in orchestrator.analyze_code_streaming(context, True):
                        await websocket.send_json({
                            "type": "analysis_update",
                            "update": update
                        })
                        
                except Exception as e:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Analysis failed: {str(e)}"
                    })
            
            elif message_type == "subscribe":
                # Subscribe to analysis updates
                analysis_id = data.get("analysis_id")
                if analysis_id:
                    await manager.subscribe_to_analysis(websocket, analysis_id)
                    await websocket.send_json({
                        "type": "subscribed",
                        "analysis_id": analysis_id
                    })
            
            elif message_type == "ping":
                # Respond to ping
                await websocket.send_json({"type": "pong"})
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.send_json({
            "type": "error",
            "message": f"WebSocket error: {str(e)}"
        })
        manager.disconnect(websocket)


@router.websocket("/ws/session/{session_id}")
async def websocket_session(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for interactive editing session."""
    await manager.connect(websocket)
    
    try:
        # Verify session exists
        if not orchestrator:
            await websocket.send_json({
                "type": "error",
                "message": "Agent orchestrator not available"
            })
            return
        
        session_status = await orchestrator.get_session_status(session_id)
        if not session_status:
            await websocket.send_json({
                "type": "error",
                "message": "Session not found"
            })
            return
        
        # Send initial session status
        await websocket.send_json({
            "type": "session_status",
            "status": session_status
        })
        
        # Handle real-time editing
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            if message_type == "apply_recommendation":
                # Apply a recommendation
                rec_data = data.get("recommendation")
                if rec_data:
                    try:
                        recommendation = CodeRecommendation(**rec_data)
                        editor_agent = orchestrator.agents['editor_agent']
                        result = await editor_agent.apply_recommendation(session_id, recommendation)
                        
                        await websocket.send_json({
                            "type": "recommendation_applied",
                            "result": result
                        })
                        
                        # Send updated session status
                        updated_status = await orchestrator.get_session_status(session_id)
                        await websocket.send_json({
                            "type": "session_updated",
                            "status": updated_status
                        })
                        
                    except Exception as e:
                        await websocket.send_json({
                            "type": "error",
                            "message": f"Failed to apply recommendation: {str(e)}"
                        })
            
            elif message_type == "get_status":
                # Get current session status
                status = await orchestrator.get_session_status(session_id)
                await websocket.send_json({
                    "type": "session_status",
                    "status": status
                })
            
            elif message_type == "ping":
                await websocket.send_json({"type": "pong"})
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Session WebSocket error: {e}")
        manager.disconnect(websocket)