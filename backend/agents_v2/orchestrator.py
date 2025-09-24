"""Agent orchestrator for coordinating multiple AI agents with streaming support."""

import asyncio
import logging
from typing import List, Dict, Any, AsyncGenerator, Optional
from datetime import datetime

from .models import (
    CodeContext,
    AnalysisResult,
    CodeIssue,
    CodeRecommendation,
    AgentResponse
)
from .code_analyzer_agent import CodeAnalyzerAgent
from .security_agent import SecurityAnalysisAgent
from .performance_agent import PerformanceAnalysisAgent
from .fix_agent import CodeFixAgent
from .editor_agent import CodeEditorAgent

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Orchestrates multiple AI agents for comprehensive code analysis."""
    
    def __init__(self, async_azure_client=None, model_name=None):
        """Initialize the orchestrator with all agents.
        
        Args:
            async_azure_client: Async Azure OpenAI client
            model_name: Model deployment name
        """
        self.async_azure_client = async_azure_client
        self.model_name = model_name
        
        # Initialize all analysis agents with async Azure client
        self.agents = {
            'code_analyzer': CodeAnalyzerAgent(async_azure_client, model_name),
            'security_agent': SecurityAnalysisAgent(async_azure_client, model_name),
            'performance_agent': PerformanceAnalysisAgent(async_azure_client, model_name),
            'fix_agent': CodeFixAgent(async_azure_client, model_name),
            'editor_agent': CodeEditorAgent(async_azure_client, model_name)
        }
        
        logger.info(f"Initialized orchestrator with {len(self.agents)} agents using AsyncAzureOpenAI")
    
    async def analyze_code_streaming(
        self,
        context: CodeContext,
        include_recommendations: bool = True
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Analyze code with streaming results.
        
        Args:
            context: Code context to analyze
            include_recommendations: Whether to generate fix recommendations
            
        Yields:
            Streaming analysis updates
        """
        start_time = datetime.now()
        analysis_id = f"analysis_{int(start_time.timestamp())}"
        
        # Send initial status
        yield {
            "type": "status",
            "analysis_id": analysis_id,
            "status": "started",
            "timestamp": start_time.isoformat(),
            "total_agents": len([a for a in self.agents.values() if a.name != "Interactive Code Editor"])
        }
        
        all_issues = []
        all_recommendations = []
        agent_results = {}
        
        # Run analysis agents concurrently with streaming updates
        analysis_agents = ['code_analyzer', 'security_agent', 'performance_agent']
        
        for i, agent_name in enumerate(analysis_agents):
            agent = self.agents[agent_name]
            
            yield {
                "type": "agent_start",
                "analysis_id": analysis_id,
                "agent": agent.name,
                "progress": (i / len(analysis_agents)) * 100
            }
            
            try:
                # Run agent analysis
                response = await agent.analyze(context)
                
                if response.success and response.data:
                    issues = response.data if isinstance(response.data, list) else []
                    all_issues.extend(issues)
                    agent_results[agent.name] = len(issues)
                    
                    # Stream individual issues as they're found
                    for issue in issues:
                        yield {
                            "type": "issue_found",
                            "analysis_id": analysis_id,
                            "agent": agent.name,
                            "issue": issue.dict()
                        }
                    
                    yield {
                        "type": "agent_complete",
                        "analysis_id": analysis_id,
                        "agent": agent.name,
                        "issues_found": len(issues),
                        "processing_time": response.processing_time,
                        "progress": ((i + 1) / len(analysis_agents)) * 100
                    }
                else:
                    yield {
                        "type": "agent_error",
                        "analysis_id": analysis_id,
                        "agent": agent.name,
                        "error": response.error,
                        "progress": ((i + 1) / len(analysis_agents)) * 100
                    }
                    
            except Exception as e:
                logger.error(f"Agent {agent.name} failed: {e}")
                yield {
                    "type": "agent_error",
                    "analysis_id": analysis_id,
                    "agent": agent.name,
                    "error": str(e),
                    "progress": ((i + 1) / len(analysis_agents)) * 100
                }
        
        # Generate recommendations if requested
        if include_recommendations and all_issues:
            yield {
                "type": "status",
                "analysis_id": analysis_id,
                "status": "generating_recommendations",
                "issues_found": len(all_issues)
            }
            
            fix_agent = self.agents['fix_agent']
            
            for i, issue in enumerate(all_issues):
                try:
                    recommendation = await fix_agent.generate_fix(issue, context)
                    if recommendation:
                        all_recommendations.append(recommendation)
                        
                        yield {
                            "type": "recommendation_generated",
                            "analysis_id": analysis_id,
                            "recommendation": recommendation.dict(),
                            "progress": ((i + 1) / len(all_issues)) * 100
                        }
                        
                except Exception as e:
                    logger.error(f"Failed to generate recommendation for issue {issue.id}: {e}")
        
        # Calculate overall score
        overall_score = self._calculate_score(all_issues)
        
        # Generate summary
        analysis_time = (datetime.now() - start_time).total_seconds()
        summary = self._generate_summary(all_issues, agent_results, analysis_time)
        
        # Create final result
        result = AnalysisResult(
            id=analysis_id,
            context=context,
            issues=all_issues,
            recommendations=all_recommendations,
            overall_score=overall_score,
            summary=summary,
            analyzed_by=list(agent_results.keys()),
            analysis_time_seconds=analysis_time,
            metadata={
                "streaming": True,
                "agent_count": len(analysis_agents),
                "recommendation_count": len(all_recommendations)
            }
        )
        
        # Send final result
        yield {
            "type": "analysis_complete",
            "analysis_id": analysis_id,
            "result": result.dict(),
            "total_time": analysis_time
        }
    
    async def analyze_code(
        self,
        context: CodeContext,
        include_recommendations: bool = True
    ) -> AnalysisResult:
        """Analyze code and return complete results.
        
        Args:
            context: Code context to analyze
            include_recommendations: Whether to generate fix recommendations
            
        Returns:
            Complete analysis result
        """
        import time
        start_time = time.time()
        logger.info(f"[ORCHESTRATOR] Starting code analysis for {context.language} code ({len(context.code)} chars)")
        
        # Collect all streaming results
        final_result = None
        
        async for update in self.analyze_code_streaming(context, include_recommendations):
            if update["type"] == "agent_start":
                logger.info(f"[ORCHESTRATOR] Agent '{update['agent']}' starting...")
            elif update["type"] == "agent_complete":
                logger.info(f"[ORCHESTRATOR] Agent '{update['agent']}' completed: {update['issues_found']} issues in {update['processing_time']:.2f}s")
            elif update["type"] == "analysis_complete":
                final_result = AnalysisResult(**update["result"])
                break
        
        total_time = time.time() - start_time
        logger.info(f"[ORCHESTRATOR] ✅ Analysis complete in {total_time*1000:.2f}ms")
        
        return final_result or AnalysisResult(
            id="error",
            context=context,
            summary="Analysis failed",
            analyzed_by=[],
            analysis_time_seconds=0
        )
    
    async def apply_recommendations(
        self,
        context: CodeContext,
        recommendations: List[CodeRecommendation],
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Apply multiple recommendations to code.
        
        Args:
            context: Code context
            recommendations: Recommendations to apply
            session_id: Existing session ID (optional)
            
        Returns:
            Application results
        """
        editor_agent = self.agents['editor_agent']
        
        # Create or use existing session
        if not session_id:
            session_id = await editor_agent.create_session(context)
        
        results = []
        applied_count = 0
        
        for recommendation in recommendations:
            try:
                result = await editor_agent.apply_recommendation(session_id, recommendation)
                results.append({
                    "recommendation_id": recommendation.issue_id,
                    "success": result.get("success", False),
                    "error": result.get("error")
                })
                
                if result.get("success"):
                    applied_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to apply recommendation {recommendation.issue_id}: {e}")
                results.append({
                    "recommendation_id": recommendation.issue_id,
                    "success": False,
                    "error": str(e)
                })
        
        # Get final code and diff
        final_code = None
        diff = None
        
        if session_id in editor_agent.active_sessions:
            final_code = editor_agent.active_sessions[session_id].current_code
            diff = await editor_agent.get_session_diff(session_id)
        
        return {
            "session_id": session_id,
            "total_recommendations": len(recommendations),
            "applied_count": applied_count,
            "failed_count": len(recommendations) - applied_count,
            "results": results,
            "final_code": final_code,
            "diff": diff
        }
    
    async def create_editing_session(self, context: CodeContext) -> str:
        """Create a new interactive editing session.
        
        Args:
            context: Code context
            
        Returns:
            Session ID
        """
        editor_agent = self.agents['editor_agent']
        return await editor_agent.create_session(context)
    
    async def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get status of an editing session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session status or None if not found
        """
        editor_agent = self.agents['editor_agent']
        
        if session_id not in editor_agent.active_sessions:
            return None
        
        session = editor_agent.active_sessions[session_id]
        diff = await editor_agent.get_session_diff(session_id)
        
        return {
            "session_id": session_id,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "current_code": session.current_code,
            "applied_edits": len(session.applied_edits),
            "pending_edits": len(session.pending_edits),
            "can_undo": len(session.undo_stack) > 0,
            "can_redo": len(session.redo_stack) > 0,
            "validation_status": session.validation_status.dict() if session.validation_status else None,
            "diff": diff
        }
    
    def _calculate_score(self, issues: List[CodeIssue]) -> int:
        """Calculate overall code quality score.
        
        Args:
            issues: List of issues found
            
        Returns:
            Score from 0-100
        """
        if not issues:
            return 100
        
        # Penalty weights by severity
        penalties = {
            'critical': 25,
            'high': 15,
            'medium': 10,
            'low': 5,
            'info': 2
        }
        
        total_penalty = 0
        for issue in issues:
            total_penalty += penalties.get(issue.severity.value, 5)
        
        # Cap the penalty to ensure score doesn't go below 0
        score = max(0, 100 - total_penalty)
        return score
    
    def _generate_summary(
        self,
        issues: List[CodeIssue],
        agent_results: Dict[str, int],
        analysis_time: float
    ) -> str:
        """Generate human-readable analysis summary.
        
        Args:
            issues: List of issues found
            agent_results: Results by agent
            analysis_time: Analysis duration
            
        Returns:
            Summary text
        """
        if not issues:
            return f"Code analysis completed in {analysis_time:.1f}s. No issues found - excellent code quality!"
        
        severity_counts = {}
        category_counts = {}
        
        for issue in issues:
            severity = issue.severity.value
            category = issue.category.value
            
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Build summary
        summary_parts = []
        
        # Overall stats
        summary_parts.append(f"Analysis completed in {analysis_time:.1f}s")
        summary_parts.append(f"Found {len(issues)} issues across {len(category_counts)} categories")
        
        # Severity breakdown
        if severity_counts:
            severity_text = []
            for severity in ['critical', 'high', 'medium', 'low']:
                count = severity_counts.get(severity, 0)
                if count > 0:
                    severity_text.append(f"{count} {severity}")
            
            if severity_text:
                summary_parts.append(f"Severity: {', '.join(severity_text)}")
        
        # Top categories
        if category_counts:
            top_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            cat_text = [f"{count} {cat.replace('_', ' ')}" for cat, count in top_categories]
            summary_parts.append(f"Main areas: {', '.join(cat_text)}")
        
        return ". ".join(summary_parts) + "."