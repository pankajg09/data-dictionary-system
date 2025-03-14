from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from core.database import get_db
from models.base import DataDictionary, User
from datetime import datetime

router = APIRouter(prefix="/dictionary", tags=["dictionary"])

def create_sample_entries(db: Session):
    """Create sample entries if none exist"""
    # Get the first user or create a system user if none exists
    system_user = db.query(User).first()
    if not system_user:
        system_user = User(
            email="system@example.com",
            name="System User",
            role="system",
            google_id="system",
            first_login_at=datetime.utcnow(),
            last_login_at=datetime.utcnow(),
            login_count=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(system_user)
        db.commit()
        db.refresh(system_user)
    
    sample_entries = [
        {
            "table_name": "users",
            "column_name": "id",
            "data_type": "INTEGER",
            "description": "Primary key for users table",
            "source": "manual",
            "version": "1.0",
            "created_by": system_user.id
        },
        {
            "table_name": "users",
            "column_name": "email",
            "data_type": "VARCHAR(255)",
            "description": "User's email address, must be unique",
            "source": "manual",
            "version": "1.0",
            "created_by": system_user.id
        },
        {
            "table_name": "orders",
            "column_name": "id",
            "data_type": "INTEGER",
            "description": "Primary key for orders table",
            "source": "manual",
            "version": "1.0",
            "created_by": system_user.id
        },
        {
            "table_name": "orders",
            "column_name": "user_id",
            "data_type": "INTEGER",
            "description": "Foreign key reference to users.id",
            "relationships": ["users.id"],
            "source": "manual",
            "version": "1.0",
            "created_by": system_user.id
        }
    ]
    
    try:
        for entry_data in sample_entries:
            entry = DataDictionary(**entry_data)
            db.add(entry)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error creating sample entries: {str(e)}")

@router.get("")
async def get_all_entries(
    db: Session = Depends(get_db),
    user_id: Optional[int] = None,
    table_name: Optional[str] = None
):
    """Get all dictionary entries with optional filters"""
    # Check if there are any entries, if not create sample entries
    count = db.query(DataDictionary).count()
    if count == 0:
        create_sample_entries(db)
        db.commit()
    
    query = db.query(DataDictionary)
    
    if user_id:
        query = query.filter(DataDictionary.created_by == user_id)
    
    if table_name:
        query = query.filter(DataDictionary.table_name == table_name)
    
    entries = query.all()
    
    return [
        {
            "id": entry.id,
            "table_name": entry.table_name,
            "column_name": entry.column_name,
            "data_type": entry.data_type,
            "description": entry.description,
            "valid_values": entry.valid_values,
            "relationships": entry.relationships,
            "source": entry.source,
            "version": entry.version,
            "created_at": entry.created_at.isoformat() if entry.created_at else None,
            "updated_at": entry.updated_at.isoformat() if entry.updated_at else None,
            "created_by": entry.created_by,
            "updated_by": entry.updated_by
        }
        for entry in entries
    ]

@router.get("/entries")
async def get_entries(
    db: Session = Depends(get_db),
    user_id: Optional[int] = None,
    table_name: Optional[str] = None
):
    """Get all dictionary entries with optional filters"""
    return await get_all_entries(db, user_id, table_name)

@router.post("/entries")
async def create_entry(
    entry_data: dict,
    current_user_id: int = Query(..., description="ID of the current user"),
    db: Session = Depends(get_db)
):
    """Create a new dictionary entry"""
    try:
        # Check if user exists
        user = db.query(User).filter(User.id == current_user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        new_entry = DataDictionary(
            table_name=entry_data["table_name"],
            column_name=entry_data["column_name"],
            data_type=entry_data["data_type"],
            description=entry_data["description"],
            valid_values=entry_data.get("valid_values"),
            relationships=entry_data.get("relationships"),
            source=entry_data.get("source", "manual"),
            version="1.0",
            analysis_id=entry_data.get("analysis_id"),
            created_by=current_user_id
        )
        db.add(new_entry)
        db.commit()
        db.refresh(new_entry)
        return new_entry
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/entries/{entry_id}")
async def update_entry(
    entry_id: int,
    entry_data: dict,
    current_user_id: int = Query(..., description="ID of the current user"),
    db: Session = Depends(get_db)
):
    """Update an existing dictionary entry"""
    try:
        entry = db.query(DataDictionary).filter(DataDictionary.id == entry_id).first()
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found")
        
        # Check if user has permission to edit
        if entry.analysis and entry.analysis.analyst_id != current_user_id:
            raise HTTPException(status_code=403, detail="Not authorized to edit this entry")
        
        # Update fields
        for key, value in entry_data.items():
            if hasattr(entry, key):
                setattr(entry, key, value)
        
        entry.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(entry)
        return entry
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/entries/{entry_id}")
async def delete_entry(
    entry_id: int,
    current_user_id: int = Query(..., description="ID of the current user"),
    db: Session = Depends(get_db)
):
    """Delete a dictionary entry"""
    try:
        entry = db.query(DataDictionary).filter(DataDictionary.id == entry_id).first()
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found")
        
        # Check if user has permission to delete
        if entry.analysis and entry.analysis.analyst_id != current_user_id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this entry")
        
        db.delete(entry)
        db.commit()
        return {"message": "Entry deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/entries/{entry_id}/history")
async def get_entry_history(
    entry_id: int,
    db: Session = Depends(get_db)
):
    """Get the history of changes for a dictionary entry"""
    entry = db.query(DataDictionary).filter(DataDictionary.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    # For now, return a simple history based on created and updated timestamps
    history = [
        {
            "id": 1,
            "timestamp": entry.created_at,
            "user": entry.analysis.analyst.username if entry.analysis and entry.analysis.analyst else "System",
            "changes": {"type": "created", "fields": ["all"]}
        }
    ]
    
    if entry.updated_at and entry.updated_at != entry.created_at:
        history.append({
            "id": 2,
            "timestamp": entry.updated_at,
            "user": entry.analysis.analyst.username if entry.analysis and entry.analysis.analyst else "System",
            "changes": {"type": "updated", "fields": ["unknown"]}
        })
    
    return history 