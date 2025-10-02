# System Logic Service API

A FastAPI-based middleware service that sits between a Next.js frontend and an LLM Service, providing authentication, request routing, and response handling.

## Architecture

```
Frontend (Next.js) 
    ↓ HTTPS + API Key
System Logic Service (FastAPI) 
    ↓ HTTPS + API Key
LLM Service
```

## Features

- **API Key Authentication**: Secure communication between frontend and system service
- **Request Forwarding**: Routes authenticated requests to the LLM service
- **CORS Support**: Configurable CORS for frontend communication
- **Health Checks**: Monitor service and LLM service health
- **Error Handling**: Comprehensive error handling and status codes

## Project Structure

```
llm-system-app/
├── main.py              # FastAPI application entry point
├── config.py            # Configuration management
├── auth.py              # Authentication middleware
├── llm_client.py        # LLM service client
├── routes.py            # API routes and endpoints
├── requirements.txt     # Python dependencies
├── Dockerfile           # Docker image configuration
├── docker-compose.yml   # Docker Compose configuration
├── .dockerignore        # Docker ignore rules
├── .env.example         # Environment variables template
├── .gitignore          # Git ignore rules
└── README.md           # This file
```

## Setup

### 1. Clone and Navigate to Project

```bash
cd /Users/danieliversen/Documents/python-projects/llm-system-app
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` with your actual configuration:

```env
# API Key for frontend to authenticate with System Logic Service
FRONTEND_API_KEY=your-secure-frontend-key

# API Key for System Logic Service to authenticate with LLM Service
LLM_SERVICE_API_KEY=your-llm-service-key

# LLM Service Configuration
LLM_SERVICE_URL=http://localhost:8001

# Server Configuration
HOST=0.0.0.0
PORT=8000
```

## Running the Service

### Option 1: Docker (Recommended)

#### Using Docker Compose

```bash
# Build and start the service
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the service
docker-compose down
```

#### Using Docker directly

```bash
# Build the image
docker build -t system-logic-service .

# Run the container
docker run -d \
  --name system-logic-service \
  -p 8000:8000 \
  --env-file .env \
  system-logic-service

# View logs
docker logs -f system-logic-service

# Stop and remove container
docker stop system-logic-service
docker rm system-logic-service
```

The service will be available at `http://localhost:8000`

### Option 2: Local Development (without Docker)

#### Development Mode (with auto-reload)

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Production Mode

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Documentation

Once running, access the interactive API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Root & Health

- `GET /` - Service information
- `GET /health` - Basic health check
- `GET /api/status` - Status of this service and LLM service (requires API key)

### Chat Completions

- `POST /api/chat/completions` - Forward chat requests to LLM service (requires API key)

**Request Headers:**
```
X-API-Key: your-frontend-api-key
Content-Type: application/json
```

**Request Body:**
```json
{
  "messages": [
    {
      "role": "user",
      "content": "Hello, how are you?"
    }
  ],
  "model": "gpt-4",
  "temperature": 0.7,
  "max_tokens": 1000
}
```

**Response:**
```json
{
  "response": {
    // LLM service response
  },
  "status": "success"
}
```

## Frontend Integration (Next.js)

Example fetch request from Next.js:

```typescript
const response = await fetch('http://localhost:8000/api/chat/completions', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': process.env.NEXT_PUBLIC_SYSTEM_API_KEY
  },
  body: JSON.stringify({
    messages: [
      { role: 'user', content: 'Hello!' }
    ]
  })
});

const data = await response.json();
```

## Security Considerations

1. **API Keys**: Store API keys securely, never commit `.env` to version control
2. **HTTPS**: Use HTTPS in production
3. **CORS**: Configure `ALLOWED_ORIGINS` to only include trusted domains
4. **Rate Limiting**: Consider adding rate limiting for production use
5. **Environment Variables**: Keep separate `.env` files for dev/staging/production

## Error Handling

The service returns appropriate HTTP status codes:

- `200` - Success
- `401` - Invalid API key
- `502` - LLM service error or authentication failure
- `503` - LLM service unavailable
- `504` - LLM service timeout

## Docker Details

### Container Features
- **Base Image**: Python 3.11 slim
- **Non-root User**: Runs as user `appuser` (UID 1000) for security
- **Health Check**: Automatic health monitoring every 30 seconds
- **Auto-restart**: Container restarts automatically unless stopped
- **Port**: Exposes port 8000

### Docker Environment Variables

When running with Docker, ensure your `.env` file includes:

```env
# Use host.docker.internal to access services on host machine from container
LLM_SERVICE_URL=http://host.docker.internal:8001

# Or use container name if LLM service is also in Docker
# LLM_SERVICE_URL=http://llm-service:8001
```

### Docker Networking

If your LLM service is also running in Docker, you can connect them:

```yaml
# docker-compose.yml with both services
version: '3.8'

services:
  system-logic-service:
    build: .
    ports:
      - "8000:8000"
    environment:
      - LLM_SERVICE_URL=http://llm-service:8001
    networks:
      - app-network
    depends_on:
      - llm-service

  llm-service:
    image: your-llm-service:latest
    ports:
      - "8001:8001"
    networks:
      - app-network

networks:
  app-network:
    driver: bridge
```

## Testing

Test the API using curl:

```bash
# Health check (no authentication required)
curl http://localhost:8000/health

# Status check (requires API key)
curl -H "X-API-Key: your-frontend-api-key" \
     http://localhost:8000/api/status

# Chat completion (requires API key)
curl -X POST http://localhost:8000/api/chat/completions \
     -H "Content-Type: application/json" \
     -H "X-API-Key: your-frontend-api-key" \
     -d '{
       "messages": [
         {"role": "user", "content": "Hello!"}
       ]
     }'
```

## Development

### Adding New Endpoints

1. Define Pydantic models in `routes.py`
2. Create route handlers with proper authentication
3. Use `llm_client` to communicate with LLM service
4. Handle errors appropriately

### Modifying LLM Client

Edit `llm_client.py` to:
- Add new LLM service endpoints
- Modify request/response handling
- Adjust timeout settings
- Add retry logic

## License

MIT

## Support

For issues or questions, please create an issue in the project repository.
