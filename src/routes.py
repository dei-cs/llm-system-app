from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from .auth import verify_frontend_api_key
from .llm_client import llm_client
from .mcp_client.academic_search.arxiv_search import arxiv_mcp
import re


# Pydantic models for request/response validation
class Message(BaseModel):
    """Chat message model."""
    role: str = Field(..., description="Role of the message sender (user, assistant, system)")
    content: str = Field(..., description="Content of the message")


class ChatRequest(BaseModel):
    """Request model for chat completion."""
    messages: List[Message] = Field(..., description="List of chat messages")
    model: Optional[str] = Field(None, description="Optional model name")
    stream: Optional[bool] = Field(True, description="Whether to stream the response")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata")


# Create router
router = APIRouter(
    tags=["LLM Operations"]
)


@router.post("/v1/chat")
async def chat(request: ChatRequest, req: Request, _: str = Depends(verify_frontend_api_key)):
    """
    Forward chat completion request to LLM gateway.
    Streams NDJSON responses from the LLM service.
    
    This endpoint matches the format expected by Next.js frontend:
    - Accepts messages array
    - Streams NDJSON lines (Ollama format)
    - Frontend converts to SSE
    - Detects 'academic_search' keyword and injects arXiv context
    
    Args:
        request: Chat completion request with messages and parameters
        
    Returns:
        StreamingResponse with NDJSON lines
    """
    # Convert Pydantic models to dicts for the LLM client
    messages = [msg.dict() for msg in request.messages]
    
    
    enable_academic_search = False  # Toggle for academic search feature
    
    if enable_academic_search:
        # Check for 'academic_search' keyword in the last user message
        if messages:
            last_message = messages[-1]
            if last_message.get('role') == 'user':
                content = last_message.get('content', '')
                
                # Check if 'academic_search' keyword is present
                if 'academic_search' in content.lower():
                    # Extract query after 'academic_search'
                    # Pattern: academic_search: query or academic_search query
                    pattern = r'academic_search[:\s]+(.+?)(?:\n|$)'
                    match = re.search(pattern, content, re.IGNORECASE)
                    
                    if match:
                        search_query = match.group(1).strip()
                    else:
                        # If no explicit query, use the rest of the message
                        search_query = re.sub(r'academic_search', '', content, flags=re.IGNORECASE).strip()
                    
                    # Perform arXiv search
                    search_results = arxiv_mcp.search(query=search_query, max_results=5)
                    
                    # Format results as context
                    context = arxiv_mcp.format_results_for_context(search_results)
                    
                    # Inject context into the user's message
                    # Add context before the user's original query
                    enhanced_content = f"{context}\n\nUser Query: {content}"
                    messages[-1]['content'] = enhanced_content
    
    
    # Stream from LLM service
    return StreamingResponse(
        llm_client.stream_chat_request(
            messages=messages,
            model=request.model,
            **(request.metadata or {})
        ),
        media_type="application/x-ndjson"
    )


@router.get("/status")
async def check_status(_: str = Depends(verify_frontend_api_key)):
    """
    Check the status of this service and the LLM service.
    
    Returns:
        Status information about both services
    """
    llm_service_healthy = await llm_client.check_health()
    
    return {
        "system_logic_service": "healthy",
        "llm_service": "healthy" if llm_service_healthy else "unhealthy",
        "overall_status": "operational" if llm_service_healthy else "degraded"
    }
