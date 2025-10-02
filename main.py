from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
import uvicorn

# Create FastAPI application
app = FastAPI(
    title="System Logic Service API",
    description="Middleware service between Next.js frontend and LLM Service",
    version="1.0.0"
)

# Configure CORS - Allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint - API information."""
    return {
        "service": "System Logic Service API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "system-logic-service"
    }


# Import and include routers
from routes import router as api_router
app.include_router(api_router)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True
    )
