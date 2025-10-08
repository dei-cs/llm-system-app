import httpx
from typing import Dict, Any, Optional, AsyncIterator
from fastapi import HTTPException, status
from .config import settings

# Simple LLM client interface, holds functions to interact with LLM service
class LLMServiceClient:
    
    def __init__(self):
        self.llm_base_url = settings.llm_service_url
        self.llm_api_key = settings.llm_service_api_key
        self.timeout = 120.0  # > 2 minutes response time -> timeout for LLM operation
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with authentication for LLM service."""
        return {
            "Authorization": f"Bearer {self.llm_api_key}",
            "Content-Type": "application/json"
        }
    
    async def stream_chat_request(
        self,
        messages: list[Dict[str, str]],
        model: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[bytes]:
        """
        - The chat prompt lands at this endpoint first, comming from the frontend
        - This functions then starts a stream, streaming the prompt to the LLM service
        
        - Simple authorization happens here, with the simple API key we implement
        - Route to the next service in the stream is also configured here
        """
        payload = {
            "messages": messages,
            "stream": True,
            **kwargs
        }
        
        if model is not None:
            payload["model"] = model
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST",
                    f"{self.llm_base_url}/v1/chat",
                    json=payload,
                    headers=self._get_headers()
                ) as response:
                    
                    if response.status_code != 200:
                        error_text = await response.aread()
                        print(f"LLM service error ({response.status_code}): {error_text.decode()}")
                        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="LLM service error")
                    
                    # Stream NDJSON lines directly from LLM service
                    async for line in response.aiter_lines():
                        if line.strip():  # Only yield non-empty lines
                            yield line.encode("utf-8") + b"\n"
                    
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="LLM service request timed out"
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to connect to LLM service: {str(e)}"
            )

# Global client instance
llm_client = LLMServiceClient()
