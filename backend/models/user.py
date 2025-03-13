from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr
from sqlalchemy import Column, Integer, String, DateTime, func, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    google_id = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    picture = Column(Text, nullable=True)
    role = Column(String(20), default='user')
    first_login_at = Column(DateTime, default=func.current_timestamp())
    last_login_at = Column(DateTime, default=func.current_timestamp())
    login_count = Column(Integer, default=1)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())

    def update_login(self):
        """Update login information when user logs in"""
        self.last_login_at = datetime.utcnow()
        self.login_count += 1

    @classmethod
    def create_from_google(cls, google_data: dict) -> 'User':
        """Create a new user from Google OAuth data"""
        return cls(
            google_id=google_data['sub'],
            email=google_data['email'],
            name=google_data['name'],
            picture=google_data.get('picture'),
            first_login_at=datetime.utcnow(),
            last_login_at=datetime.utcnow()
        )

# Pydantic models for API requests/responses
class UserBase(BaseModel):
    email: EmailStr
    name: str
    picture: Optional[str] = None
    role: str = 'user'

class UserCreate(UserBase):
    google_id: str

class UserResponse(UserBase):
    id: int
    google_id: str
    first_login_at: datetime
    last_login_at: datetime
    login_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class UserUpdate(BaseModel):
    email: Optional[str] = None
    name: Optional[str] = None
    picture: Optional[str] = None
    role: Optional[str] = None 