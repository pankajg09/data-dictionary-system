from fastapi import APIRouter, UploadFile, Form, HTTPException, Depends, Body
from typing import Optional, Dict
import openai
from sqlalchemy.orm import Session
from core.database import get_db
from services.ai.analysis_service import AnalysisService
import os
from dotenv import load_dotenv
import json
from datetime import datetime
from sqlalchemy.sql import func

load_dotenv()

router = APIRouter()

# Configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

def analyze_code_with_llm(code: str) -> dict:
    """Analyze code using OpenAI's GPT model."""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a code analysis expert. Analyze the provided code and extract information about database tables, relationships, and important code snippets. Format your response as JSON with the following structure: {tables: [{name: string, fields: [{name: string, type: string, description: string}]}], relationships: [{from_table: string, to_table: string, type: string}], code_snippets: [{file: string, line: number, code: string, description: string}]}"},
                {"role": "user", "content": f"Analyze this code:\n\n{code}"}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        # Parse the response
        analysis = json.loads(response.choices[0].message.content)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Analysis failed: {str(e)}")

@router.post("/analyze")
async def analyze_code(
    file: Optional[UploadFile] = None,
    code: Optional[str] = Form(None),
    analysis_id: Optional[int] = Form(None),
    user_id: int = Form(...),  # Required user_id
    db: Session = Depends(get_db)
):
    try:
        if file:
            content = await file.read()
            code_to_analyze = content.decode()
        elif code:
            code_to_analyze = code
        else:
            raise HTTPException(status_code=400, detail="No code provided")

        analysis_service = AnalysisService(db, openai)
        analysis_result = await analysis_service.analyze_code(
            code_to_analyze, 
            analysis_id=analysis_id,
            user_id=user_id
        )
        
        return analysis_result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analysis/{analysis_id}/submit-for-review")
async def submit_for_review(
    analysis_id: int,
    reviewer_id: int = Body(...),
    db: Session = Depends(get_db)
):
    try:
        analysis_service = AnalysisService(db, openai)
        await analysis_service.submit_for_review(analysis_id, reviewer_id)
        return {"message": "Analysis submitted for review successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analysis/{analysis_id}/review")
async def submit_review(
    analysis_id: int,
    reviewer_id: int = Body(...),
    comments: Dict = Body(...),
    approved: bool = Body(...),
    db: Session = Depends(get_db)
):
    try:
        analysis_service = AnalysisService(db, openai)
        await analysis_service.submit_review(analysis_id, reviewer_id, comments, approved)
        return {"message": "Review submitted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis/{analysis_id}")
async def get_analysis(
    analysis_id: int,
    db: Session = Depends(get_db)
):
    try:
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        return {
            "id": analysis.id,
            "title": analysis.title,
            "description": analysis.description,
            "status": analysis.status,
            "review_status": analysis.review_status,
            "analysis_results": analysis.analysis_results,
            "review_comments": analysis.review_comments,
            "created_at": analysis.created_at,
            "updated_at": analysis.updated_at,
            "review_date": analysis.review_date
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/query-executions")
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

@router.get("/user/{user_id}/query-stats")
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