"""Interactive code editing agent using Pydantic AI."""

import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime

from .base_agent import BaseCodeAgent
from .models import (
    CodeContext,
    CodeRecommendation,
    EditOperation,
    EditSession,
    ValidationResult,
    CodeLocation
)


class CodeEditorAgent(BaseCodeAgent):
    """Agent specialized in interactive code editing and modification."""
    
    def __init__(self, azure_client=None, model_name=None):
        """Initialize code editor agent."""
        super().__init__(
            name="Interactive Code Editor",
            description="Handles interactive code editing, multi-file refactoring, and safe transformations",
            azure_client=azure_client,
            model_name=model_name
        )
        self.active_sessions: Dict[str, EditSession] = {}
        
    def _register_tools(self):
        """Register code editing specific tools."""
        super()._register_tools()
        
        @self.agent.tool
        async def create_edit_session(code: str, language: str, file_path: str = None) -> str:
            """Create a new editing session.
            
            Args:
                code: Initial code content
                language: Programming language
                file_path: File path (optional)
                
            Returns:
                Session ID
            """
            session_id = str(uuid.uuid4())
            
            session = EditSession(
                session_id=session_id,
                code_context=CodeContext(
                    code=code,
                    language=language,
                    file_path=file_path
                ),
                current_code=code
            )
            
            return session_id
        
        @self.agent.tool
        async def apply_edit_operation(
            session_id: str,
            operation: EditOperation
        ) -> Dict[str, Any]:
            """Apply an edit operation to a session.
            
            Args:
                session_id: Session ID
                operation: Edit operation to apply
                
            Returns:
                Result of the operation
            """
            if session_id not in self.active_sessions:
                return {"error": "Session not found"}
            
            session = self.active_sessions[session_id]
            
            try:
                # Apply the edit based on operation type
                if operation.type == "replace":
                    new_code = session.current_code.replace(
                        operation.original_content or "",
                        operation.new_content or ""
                    )
                elif operation.type == "insert":
                    lines = session.current_code.split('\n')
                    line_num = operation.location.line_start - 1
                    lines.insert(line_num, operation.new_content or "")
                    new_code = '\n'.join(lines)
                elif operation.type == "delete":
                    lines = session.current_code.split('\n')
                    start = operation.location.line_start - 1
                    end = operation.location.line_end or start
                    del lines[start:end + 1]
                    new_code = '\n'.join(lines)
                else:
                    return {"error": f"Unsupported operation type: {operation.type}"}
                
                # Store previous state for undo
                session.undo_stack.append(EditOperation(
                    id=str(uuid.uuid4()),
                    type="replace",
                    location=CodeLocation(
                        file_path=session.code_context.file_path or "unknown",
                        line_start=1,
                        line_end=len(session.current_code.split('\n'))
                    ),
                    original_content=new_code,
                    new_content=session.current_code,
                    description="Undo operation"
                ))
                
                # Update session
                session.current_code = new_code
                session.applied_edits.append(operation)
                session.updated_at = datetime.now()
                operation.applied = True
                operation.applied_at = datetime.now()
                
                # Clear redo stack
                session.redo_stack.clear()
                
                return {
                    "success": True,
                    "new_code": new_code,
                    "operation_id": operation.id
                }
                
            except Exception as e:
                return {"error": str(e)}
        
        @self.agent.tool
        async def undo_last_edit(session_id: str) -> Dict[str, Any]:
            """Undo the last edit operation.
            
            Args:
                session_id: Session ID
                
            Returns:
                Result of undo operation
            """
            if session_id not in self.active_sessions:
                return {"error": "Session not found"}
            
            session = self.active_sessions[session_id]
            
            if not session.undo_stack:
                return {"error": "Nothing to undo"}
            
            # Get last undo operation
            undo_op = session.undo_stack.pop()
            
            # Store current state for redo
            session.redo_stack.append(EditOperation(
                id=str(uuid.uuid4()),
                type="replace",
                location=CodeLocation(
                    file_path=session.code_context.file_path or "unknown",
                    line_start=1,
                    line_end=len(session.current_code.split('\n'))
                ),
                original_content=session.current_code,
                new_content=undo_op.original_content or "",
                description="Redo operation"
            ))
            
            # Apply undo
            session.current_code = undo_op.original_content or ""
            session.updated_at = datetime.now()
            
            return {
                "success": True,
                "new_code": session.current_code,
                "operation_id": undo_op.id
            }
        
        @self.agent.tool
        async def redo_last_edit(session_id: str) -> Dict[str, Any]:
            """Redo the last undone edit operation.
            
            Args:
                session_id: Session ID
                
            Returns:
                Result of redo operation
            """
            if session_id not in self.active_sessions:
                return {"error": "Session not found"}
            
            session = self.active_sessions[session_id]
            
            if not session.redo_stack:
                return {"error": "Nothing to redo"}
            
            # Get last redo operation
            redo_op = session.redo_stack.pop()
            
            # Store current state for undo
            session.undo_stack.append(EditOperation(
                id=str(uuid.uuid4()),
                type="replace",
                location=CodeLocation(
                    file_path=session.code_context.file_path or "unknown",
                    line_start=1,
                    line_end=len(session.current_code.split('\n'))
                ),
                original_content=session.current_code,
                new_content=redo_op.new_content or "",
                description="Undo operation"
            ))
            
            # Apply redo
            session.current_code = redo_op.new_content or ""
            session.updated_at = datetime.now()
            
            return {
                "success": True,
                "new_code": session.current_code,
                "operation_id": redo_op.id
            }
        
        @self.agent.tool
        async def validate_session_code(session_id: str) -> ValidationResult:
            """Validate the current code in a session.
            
            Args:
                session_id: Session ID
                
            Returns:
                Validation result
            """
            if session_id not in self.active_sessions:
                return ValidationResult(
                    valid=False,
                    errors=["Session not found"]
                )
            
            session = self.active_sessions[session_id]
            
            # Perform basic validation
            errors = []
            warnings = []
            
            # Check for basic syntax (simplified)
            code = session.current_code
            language = session.code_context.language
            
            if language == "python":
                # Check for basic Python syntax issues
                try:
                    compile(code, '<string>', 'exec')
                except SyntaxError as e:
                    errors.append(f"Syntax error: {e.msg} at line {e.lineno}")
                
                # Check for common issues
                if code.count('(') != code.count(')'):
                    errors.append("Mismatched parentheses")
                if code.count('[') != code.count(']'):
                    errors.append("Mismatched brackets")
                if code.count('{') != code.count('}'):
                    errors.append("Mismatched braces")
            
            return ValidationResult(
                valid=len(errors) == 0,
                syntax_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                metrics={
                    "lines": len(code.split('\n')),
                    "characters": len(code)
                }
            )
    
    async def create_session(self, context: CodeContext) -> str:
        """Create a new editing session.
        
        Args:
            context: Code context
            
        Returns:
            Session ID
        """
        session_id = await self.agent.tools.create_edit_session(
            context.code,
            context.language,
            context.file_path
        )
        
        session = EditSession(
            session_id=session_id,
            code_context=context,
            current_code=context.code
        )
        
        self.active_sessions[session_id] = session
        return session_id
    
    async def apply_recommendation(
        self,
        session_id: str,
        recommendation: CodeRecommendation
    ) -> Dict[str, Any]:
        """Apply a recommendation to an editing session.
        
        Args:
            session_id: Session ID
            recommendation: Recommendation to apply
            
        Returns:
            Result of applying the recommendation
        """
        if session_id not in self.active_sessions:
            return {"error": "Session not found"}
        
        # Create edit operation from recommendation
        operation = EditOperation(
            id=str(uuid.uuid4()),
            type="replace",
            location=CodeLocation(
                file_path=self.active_sessions[session_id].code_context.file_path or "unknown",
                line_start=1,
                line_end=1
            ),
            original_content=recommendation.original_code,
            new_content=recommendation.suggested_code,
            description=recommendation.description,
            recommendation_id=recommendation.issue_id
        )
        
        result = await self.agent.tools.apply_edit_operation(session_id, operation)
        
        if result.get("success"):
            # Validate the changes
            validation = await self.agent.tools.validate_session_code(session_id)
            self.active_sessions[session_id].validation_status = validation
            
            result["validation"] = validation.dict()
        
        return result
    
    async def get_session_diff(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get diff between original and current code.
        
        Args:
            session_id: Session ID
            
        Returns:
            Diff information
        """
        if session_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[session_id]
        original = session.code_context.code
        current = session.current_code
        
        # Simple diff calculation
        original_lines = original.split('\n')
        current_lines = current.split('\n')
        
        added_lines = []
        removed_lines = []
        modified_lines = []
        
        # Basic diff algorithm
        for i, (orig, curr) in enumerate(zip(original_lines, current_lines)):
            if orig != curr:
                modified_lines.append({
                    "line": i + 1,
                    "original": orig,
                    "current": curr
                })
        
        # Handle length differences
        if len(current_lines) > len(original_lines):
            for i in range(len(original_lines), len(current_lines)):
                added_lines.append({
                    "line": i + 1,
                    "content": current_lines[i]
                })
        elif len(original_lines) > len(current_lines):
            for i in range(len(current_lines), len(original_lines)):
                removed_lines.append({
                    "line": i + 1,
                    "content": original_lines[i]
                })
        
        return {
            "original_lines": len(original_lines),
            "current_lines": len(current_lines),
            "added_lines": added_lines,
            "removed_lines": removed_lines,
            "modified_lines": modified_lines,
            "total_changes": len(added_lines) + len(removed_lines) + len(modified_lines)
        }
    
    async def finalize_session(self, session_id: str) -> Optional[str]:
        """Finalize an editing session and return the final code.
        
        Args:
            session_id: Session ID
            
        Returns:
            Final code or None if session not found
        """
        if session_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[session_id]
        final_code = session.current_code
        
        # Clean up session
        del self.active_sessions[session_id]
        
        return final_code