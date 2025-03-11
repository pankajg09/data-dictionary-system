from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from .models.base import Base
from .core.database import engine, get_db
from .api.routes import analysis, auth, review, dictionary

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Data Dictionary System",
    description="A system for managing data dictionaries and code analysis",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["Analysis"])
app.include_router(review.router, prefix="/api/review", tags=["Review"])
app.include_router(dictionary.router, prefix="/api/dictionary", tags=["Dictionary"])

@app.get("/")
async def root():
    return {"message": "Welcome to Data Dictionary System API"} 