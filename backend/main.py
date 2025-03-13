from fastapi import FastAPI, UploadFile, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict
from openai import OpenAI, OpenAIError
import google.generativeai as genai
import os
from dotenv import load_dotenv
import json
import ast
import re
import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, text

from core.database import get_db, init_db
from models.base import Base, Analysis, QueryExecution
from services.ai.analysis_service import AnalysisService
from api.routes import analysis, dictionary, databases
from routes.config import router as config_router
from routes.auth import router as auth_router

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
app.include_router(dictionary.router, prefix="/api/dictionary")
app.include_router(databases.router, prefix="/api")
app.include_router(config_router, prefix="/api/config", tags=["config"])
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])

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

def extract_code_info(code: str) -> dict:
    """Extract basic information from code using AST."""
    try:
        tree = ast.parse(code)
        imports = []
        functions = []
        classes = []
        variables = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(n.name for n in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(f"{node.module}.{node.names[0].name}")
            elif isinstance(node, ast.FunctionDef):
                functions.append(node.name)
            elif isinstance(node, ast.ClassDef):
                classes.append(node.name)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        variables.append(target.id)
        
        return {
            "imports": imports,
            "functions": functions,
            "classes": classes,
            "variables": variables
        }
    except Exception as e:
        return {"error": f"Failed to parse code: {str(e)}"}

async def analyze_with_openai(code: str, code_info: dict) -> dict:
    """Analyze code using OpenAI's GPT model."""
    if not openai_client:
        raise ValueError("OpenAI client not configured")

    system_prompt = """You are an expert code analyst specializing in data dictionary creation and code analysis. 
    Analyze the provided code and extract the following information in JSON format:
    1. Tables and their structures (even if implied from code)
    2. Data relationships and dependencies
    3. Important code snippets with explanations
    4. Data sources and their descriptions
    5. Data transformations and cleaning steps
    6. Potential reuse opportunities
    7. Documentation summary"""

    context = f"""Code Analysis Context:
    - Imports: {', '.join(code_info['imports'])}
    - Functions: {', '.join(code_info['functions'])}
    - Classes: {', '.join(code_info['classes'])}
    
    Code to analyze:
    {code}
    """

    try:
        print("Attempting OpenAI API analysis...")
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo-16k",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": context}
            ],
            temperature=0.7,
            max_tokens=4000
        )
        
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"OpenAI API Error: {str(e)}")
        raise

async def analyze_with_gemini(code: str, code_info: dict) -> dict:
    """Analyze code using Google's Gemini model."""
    if not google_api_key:
        raise ValueError("Gemini API key not configured")

    prompt = f"""As an expert code analyst, analyze this code and provide information in JSON format about:
    1. Tables and their structures (even if implied from code)
    2. Data relationships and dependencies
    3. Important code snippets with explanations
    4. Data sources and their descriptions
    5. Data transformations and cleaning steps
    6. Potential reuse opportunities
    7. Documentation summary

    Code Analysis Context:
    - Imports: {', '.join(code_info['imports'])}
    - Functions: {', '.join(code_info['functions'])}
    - Classes: {', '.join(code_info['classes'])}
    
    Code to analyze:
    {code}

    IMPORTANT: Return ONLY the JSON object without any markdown formatting or code blocks.
    """

    try:
        print("Attempting Gemini API analysis...")
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        generation_config = {
            "temperature": 0.3,
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 4000,
        }
        
        response = model.generate_content(
            prompt,
            generation_config=generation_config
        )
        
        if not response.text:
            raise ValueError("Empty response from Gemini API")
            
        # Clean up the response text
        response_text = response.text
        # Remove markdown code block if present
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        response_text = response_text.strip()
        
        print("Raw response:", response_text)
            
        try:
            # Try to parse the response as JSON
            result = json.loads(response_text)
            return result
        except json.JSONDecodeError as je:
            print(f"Failed to parse Gemini response as JSON: {str(je)}")
            print(f"Raw response: {response_text}")
            raise ValueError(f"Invalid JSON response from Gemini API: {str(je)}")
            
    except Exception as e:
        print(f"Gemini API Error: {str(e)}")
        raise

async def analyze_code_with_llm(code: str, code_info: dict) -> dict:
    """Analyze code using available LLM services with fallback."""
    errors = []

    # Try OpenAI first if configured
    if openai_client:
        try:
            return await analyze_with_openai(code, code_info)
        except Exception as e:
            error_msg = str(e)
            print(f"OpenAI analysis failed: {error_msg}")
            errors.append(f"OpenAI Error: {error_msg}")

    # Try Gemini as fallback
    if google_api_key:
        try:
            return await analyze_with_gemini(code, code_info)
        except Exception as e:
            error_msg = str(e)
            print(f"Gemini analysis failed: {error_msg}")
            errors.append(f"Gemini Error: {error_msg}")

    # If both failed, raise error with details
    raise HTTPException(
        status_code=500,
        detail=f"LLM analysis failed with both services: {'; '.join(errors)}"
    )

@app.post("/analyze")
async def analyze_code(
    file: Optional[UploadFile] = None,
    code: Optional[str] = Form(None),
    user_id: int = Form(...),
    analysis_id: Optional[int] = Form(None),
    db: Session = Depends(get_db)
):
    try:
        if not openai_client:
            raise HTTPException(status_code=500, detail="OpenAI client not initialized")

        if file:
            content = await file.read()
            code_to_analyze = content.decode()
        elif code:
            code_to_analyze = code
        else:
            raise HTTPException(status_code=400, detail="No code provided")

        analysis_service = AnalysisService(db, openai_client)
        analysis_result = await analysis_service.analyze_code(
            code_to_analyze,
            analysis_id=analysis_id,
            user_id=user_id
        )
        
        return analysis_result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/query-executions")
async def get_query_executions(
    user_id: Optional[int] = None,
    analysis_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get query execution history with optional filters"""
    try:
        query = db.query(QueryExecution)
        
        if user_id:
            query = query.filter(QueryExecution.user_id == user_id)
        if analysis_id:
            query = query.filter(QueryExecution.analysis_id == analysis_id)
            
        executions = query.order_by(QueryExecution.execution_time.desc()).all()
        
        return [{
            "id": exe.id,
            "user_id": exe.user_id,
            "analysis_id": exe.analysis_id,
            "execution_time": exe.execution_time,
            "execution_status": exe.execution_status,
            "execution_duration": exe.execution_duration,
            "error_message": exe.error_message
        } for exe in executions]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/user/{user_id}/query-stats")
async def get_user_query_stats(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get query execution statistics for a user"""
    try:
        total_queries = db.query(QueryExecution).filter(QueryExecution.user_id == user_id).count()
        successful_queries = db.query(QueryExecution).filter(
            QueryExecution.user_id == user_id,
            QueryExecution.execution_status == "success"
        ).count()
        failed_queries = db.query(QueryExecution).filter(
            QueryExecution.user_id == user_id,
            QueryExecution.execution_status == "failed"
        ).count()
        
        avg_duration = db.query(func.avg(QueryExecution.execution_duration)).filter(
            QueryExecution.user_id == user_id,
            QueryExecution.execution_status == "success"
        ).scalar()
        
        return {
            "total_queries": total_queries,
            "successful_queries": successful_queries,
            "failed_queries": failed_queries,
            "average_duration_ms": round(float(avg_duration or 0), 2)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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