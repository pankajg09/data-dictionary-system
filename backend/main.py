from fastapi import FastAPI, UploadFile, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict
from openai import OpenAI, OpenAIError
import google.generativeai as genai
import os
from dotenv import load_dotenv
import json
import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, text

from core.database import get_db, init_db
from models.base import Base, Analysis, QueryExecution
from services.ai.analysis_service import AnalysisService
from api.routes import analysis, dictionary, databases, auth as api_auth
from routes.config import router as config_router
from routes.auth import router as auth_router
from routes.dashboard import router as dashboard_router

load_dotenv()

# Initialize database tables
try:
    init_db()
except Exception as e:
    print(f"Failed to initialize database: {str(e)}")
    raise

app = FastAPI(
    title="Data Dictionary System",
    description="A system for managing data dictionaries and code analysis",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600
)

# Mount the routers
app.include_router(analysis.router, prefix="/api")
app.include_router(dictionary.router, prefix="/api")
app.include_router(databases.router)
app.include_router(config_router, prefix="/api")
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(api_auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["dashboard"])

# Configure OpenAI client
openai_api_key = os.getenv("OPENAI_API_KEY")
openai_client = None
if openai_api_key:
    try:
        openai_client = OpenAI(api_key=openai_api_key)
        print(f"OpenAI client initialized successfully")
    except Exception as e:
        print(f"Failed to initialize OpenAI client: {str(e)}")
else:
    print("OpenAI API key not found in environment variables")

# Configure Gemini client
google_api_key = os.getenv("GOOGLE_API_KEY")
if google_api_key:
    try:
        genai.configure(api_key=google_api_key)
    except Exception as e:
        print(f"Failed to initialize Gemini client: {str(e)}")

@app.get("/")
async def root():
    return {"message": "Welcome to Data Dictionary System API"}

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Check the health of the API and database connection"""
    try:
        # Test database connection
        db.execute(text("SELECT 1")).scalar()
        
        # Check OpenAI client
        openai_status = "available" if openai_client else "not configured"
        
        # Check Gemini client
        gemini_status = "available" if google_api_key else "not configured"
        
        return {
            "status": "healthy",
            "database": "connected",
            "openai": openai_status,
            "gemini": gemini_status,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Health check failed: {str(e)}"
        ) 