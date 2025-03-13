from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from models.config import Configuration
from core.database import get_db
from core.auth import get_current_user

router = APIRouter(tags=["config"])

class ConfigurationCreate(BaseModel):
    key: str
    value: str
    description: Optional[str] = None

class ConfigurationResponse(BaseModel):
    key: str
    description: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

@router.get("/api/config/public/google-client-id")
async def get_google_client_id(db: Session = Depends(get_db)):
    """Get Google Client ID - public endpoint"""
    client_id = Configuration.get_value(db, "GOOGLE_CLIENT_ID")
    if client_id is None:
        raise HTTPException(status_code=404, detail="Google Client ID not configured")
    return {"value": client_id}

@router.get("/api/config", response_model=List[ConfigurationResponse])
async def get_configurations(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """Get all configuration keys (without values for security)"""
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized to view configurations")
    configs = db.query(Configuration).all()
    return configs

@router.get("/api/config/{key}")
async def get_configuration(key: str, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """Get a specific configuration value"""
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized to view configurations")
    config = Configuration.get_value(db, key)
    if config is None:
        raise HTTPException(status_code=404, detail="Configuration not found")
    return {"key": key, "value": config}

@router.post("/api/config")
async def create_configuration(
    config: ConfigurationCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create or update a configuration"""
    if not current_user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Not authorized to modify configurations")
    
    Configuration.set_value(db, config.key, config.value, config.description)
    return {"message": "Configuration updated successfully"} 