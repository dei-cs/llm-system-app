import httpx
from typing import Dict, Any, Optional, AsyncIterator
from fastapi import HTTPException, status
from config import settings


class LLMServiceClient:
    """Client for communicating with the LLM Service."""
    
    def __init__(self):
        self.base_url = settings.llm_service_url
        self.api_key = settings.llm_service_api_key
        self.timeout = 120.0  # 2 minutes timeout for LLM operations
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with authentication for LLM service."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def stream_chat_request(
        self,
        messages: list[Dict[str, str]],
        model: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[bytes]:
        """
        Stream chat completion request to the LLM service.
        Yields NDJSON lines from the LLM gateway.
        
        Args:
            messages: List of message objects with 'role' and 'content'
            model: Optional model name override
            **kwargs: Additional parameters to pass to the LLM service
            
        Yields:
            NDJSON lines as bytes from the LLM service
            
        Raises:
            HTTPException: If the LLM service request fails
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
                    f"{self.base_url}/v1/chat",
                    json=payload,
                    headers=self._get_headers()
                ) as response:
                    
                    if response.status_code == 401:
                        raise HTTPException(
                            status_code=status.HTTP_502_BAD_GATEWAY,
                            detail="Authentication failed with LLM service"
                        )
                    elif response.status_code != 200:
                        error_text = await response.aread()
                        raise HTTPException(
                            status_code=status.HTTP_502_BAD_GATEWAY,
                            detail=f"LLM service error: {error_text.decode()}"
                        )
                    
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
    
    async def check_health(self) -> bool:
        """
        Check if the LLM service is healthy.
        
        Returns:
            True if the service is healthy, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.base_url}/health",
                    headers=self._get_headers()
                )
                return response.status_code == 200
        except Exception:
            return False


# Global client instance
llm_client = LLMServiceClient()
