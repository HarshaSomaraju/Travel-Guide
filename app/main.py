"""
FastAPI Travel Guide API
Main application entry point
"""
from dotenv import load_dotenv
load_dotenv()  # Load .env file before other imports

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api.routes import chat

settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="AI Travel Guide API with real-time streaming",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/api")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy"}
