from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from core.database import get_db
from models.base import Analysis, QueryExecution, User

router = APIRouter(tags=["dashboard"])

@router.get("/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics"""
    try:
        # Count total analyses
        total_analyses = db.query(func.count(Analysis.id)).scalar() or 0
        
        # Count analyses by status
        pending_analyses = db.query(func.count(Analysis.id)).filter(
            Analysis.status == "pending_review"
        ).scalar() or 0
        
        approved_analyses = db.query(func.count(Analysis.id)).filter(
            Analysis.status == "approved"
        ).scalar() or 0
        
        # Count total query executions
        total_queries = db.query(func.count(QueryExecution.id)).scalar() or 0
        
        # Count successful and failed queries
        successful_queries = db.query(func.count(QueryExecution.id)).filter(
            QueryExecution.execution_status == "success"
        ).scalar() or 0
        
        failed_queries = db.query(func.count(QueryExecution.id)).filter(
            QueryExecution.execution_status == "failed"
        ).scalar() or 0
        
        # Count active users (users who have logged in)
        active_users = db.query(func.count(User.id)).filter(
            User.login_count > 0
        ).scalar() or 0
        
        return {
            "total_analyses": total_analyses,
            "pending_analyses": pending_analyses,
            "approved_analyses": approved_analyses,
            "total_queries": total_queries,
            "successful_queries": successful_queries,
            "failed_queries": failed_queries,
            "active_users": active_users
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching dashboard stats: {str(e)}") 