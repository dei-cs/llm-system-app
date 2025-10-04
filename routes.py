from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from auth import verify_frontend_api_key
from llm_client import llm_client


# Pydantic models for request/response validation
class Message(BaseModel):
    """Chat message model."""
    role: str = Field(..., description="Role of the message sender (user, assistant, system)")
    content: str = Field(..., description="Content of the message")


# Chat request model, used to validate incoming requests are in expected format
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
    Middleware in the downstream direction
    - Forwards chat request directly to the LLM service
    - Streaming is done in llm_client.stream_chat_request function
    - Response moves back upstream through same nodes as the downstream request
    """
    # Convert Pydantic models to dicts for the LLM client (tokens which are more readable by LLM)
    # This converts: [Message(role="user", content="Hello!")]
    # Into: [{"role": "user", "content": "Hello!"}]
    messages = [msg.dict() for msg in request.messages]
    
    # Stream from LLM service
    return StreamingResponse(
        llm_client.stream_chat_request(
            messages=messages,
            model=request.model,
            **(request.metadata or {})
        ),
        media_type="application/x-ndjson"
    )
