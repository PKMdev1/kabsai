from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine
from app.models import Base
from app.routers import files, chat, xml_processor

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="KABS Assistant API",
    description="AI-powered document management and chat system for Elite/KABS",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(files.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(xml_processor.router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "message": "KABS Assistant API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
