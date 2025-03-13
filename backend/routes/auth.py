from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from google.oauth2 import id_token
from google.auth.transport import requests
from typing import Optional
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from core.database import get_db
from models.base import User
from core.config import settings

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Secret key for JWT
SECRET_KEY = "your-secret-key"  # In production, use environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    picture: Optional[str] = None
    role: str
    login_count: int
    
    class Config:
        from_attributes = True

class GoogleLoginRequest(BaseModel):
    token: str
    email: str
    name: str
    picture: Optional[str] = None

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@router.post("/google-login", response_model=dict)
async def google_login(
    request: GoogleLoginRequest,
    db: Session = Depends(get_db)
):
    try:
        now = datetime.utcnow()
        # Check if user exists
        user = db.query(User).filter(User.email == request.email).first()
        
        if not user:
            # Create new user
            user = User(
                email=request.email,
                name=request.name,
                picture=request.picture,
                role="user",
                google_id=request.token,
                first_login_at=now,
                last_login_at=now,
                login_count=1,
                created_at=now,
                updated_at=now
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            # Update existing user
            user.last_login_at = now
            user.login_count += 1
            user.updated_at = now
            if request.picture:
                user.picture = request.picture
            if user.first_login_at is None:
                user.first_login_at = now
            db.commit()
            db.refresh(user)
        
        # Create access token
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=timedelta(minutes=1440)  # 24 hours
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "picture": user.picture,
                "role": user.role,
                "login_count": user.login_count
            }
        }
    except Exception as e:
        print(f"Error in google_login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process login: {str(e)}"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return user 