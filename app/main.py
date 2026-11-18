import time
import uuid
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from app.config import settings
from app.api.v1 import router as api_router
from app.api.connectors import router as connector_router

# Configure logging
logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger("incubrix")

# Modern lifespan event handler (replaces deprecated @app.on_event)
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n" + "="*50)
    print("🚀 FastAPI Server Successfully Started!")
    print("👉 Documentation (Swagger UI): http://127.0.0.1:8000/docs")
    print("👉 ReDoc Documentation:         http://127.0.0.1:8000/redoc")
    print("👉 Health Check Endpoint:     http://127.0.0.1:8000/health")
    print("👉 Readiness Check Endpoint:  http://127.0.0.1:8000/ready")
    print("="*50 + "\n")
    yield

# Initialize FastAPI app with lifespan
app = FastAPI(
    title=settings.APP_NAME, 
    version="1.0.0",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan
)

# Request logging and correlation ID middleware
@app.middleware("http")
async def add_correlation_id_and_logging(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-Id", str(uuid.uuid4()))
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    response.headers["X-Correlation-Id"] = correlation_id
    
    logger.info(
        f"HTTP Request processed | Method: {request.method} | Path: {request.url.path} | "
        f"Status: {response.status_code} | Duration: {round(duration, 4)}s | Correlation-ID: {correlation_id}"
    )
    return response

# Health and readiness check endpoints
@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": time.time()}

@app.get("/ready")
def readiness_check():
    return {"status": "ready", "simulation_mode": settings.SIMULATION_MODE}

# Root endpoint
@app.get("/")
def read_root():
    return {
        "message": "Welcome to the IncuBrix Long-Tail Distribution Service",
        "docs": "/docs",
        "health": "/health"
    }

# Include API v1 and Connector Contract routers
app.include_router(api_router, prefix=settings.API_V1_PREFIX)
app.include_router(connector_router, prefix=settings.CONNECTOR_PREFIX)