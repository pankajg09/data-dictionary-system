from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    google_id = Column(String(255), unique=True, nullable=True)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    picture = Column(Text, nullable=True)  # Changed to match frontend
    role = Column(String(20), nullable=False, default='user')
    first_login_at = Column(DateTime, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    login_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Analysis(Base):
    __tablename__ = 'analyses'
    
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String)
    analyst_id = Column(Integer, ForeignKey('users.id'))
    status = Column(String)  # draft, pending_review, approved, rejected
    code_location = Column(String)  # Git repository URL
    documentation = Column(JSON)
    analysis_results = Column(JSON)  # Store the complete analysis results
    review_status = Column(String, default='pending')  # pending, in_review, reviewed
    reviewer_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    review_comments = Column(JSON)
    review_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    analyst = relationship("User", foreign_keys=[analyst_id], backref="analyses_created")
    reviewer = relationship("User", foreign_keys=[reviewer_id], backref="analyses_reviewed")
    data_dictionaries = relationship("DataDictionary", back_populates="analysis")
    reviews = relationship("Review", back_populates="analysis")

class DataDictionary(Base):
    __tablename__ = 'data_dictionaries'
    
    id = Column(Integer, primary_key=True)
    analysis_id = Column(Integer, ForeignKey('analyses.id'))
    table_name = Column(String, nullable=False)
    column_name = Column(String, nullable=False)
    data_type = Column(String, nullable=False)
    description = Column(String)
    valid_values = Column(JSON)
    relationships = Column(JSON)
    source = Column(String)
    version = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    updated_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    analysis = relationship("Analysis", back_populates="data_dictionaries")
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])

class Review(Base):
    __tablename__ = 'reviews'
    
    id = Column(Integer, primary_key=True)
    analysis_id = Column(Integer, ForeignKey('analyses.id'))
    reviewer_id = Column(Integer, ForeignKey('users.id'))
    status = Column(String)  # pending, in_progress, completed
    comments = Column(JSON)
    rating = Column(Integer)
    suggested_modifications = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    analysis = relationship("Analysis", back_populates="reviews")
    reviewer = relationship("User")

class CodeSnippet(Base):
    __tablename__ = 'code_snippets'
    
    id = Column(Integer, primary_key=True)
    analysis_id = Column(Integer, ForeignKey('analyses.id'))
    code = Column(String, nullable=False)
    language = Column(String)
    purpose = Column(String)
    dependencies = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    analysis = relationship("Analysis")

class QueryExecution(Base):
    __tablename__ = 'query_executions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    analysis_id = Column(Integer, ForeignKey('analyses.id'), nullable=False)
    query_content = Column(String, nullable=False)
    execution_time = Column(DateTime, default=datetime.utcnow)
    execution_status = Column(String)  # success, failed
    error_message = Column(String, nullable=True)
    execution_duration = Column(Integer)  # in milliseconds
    
    user = relationship("User", backref="query_executions")
    analysis = relationship("Analysis", backref="query_executions")

# Models for database management
class Database(Base):
    __tablename__ = 'databases'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String)
    connection_string = Column(String)
    db_type = Column(String)  # sqlite, mysql, postgresql, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    tables = relationship("Table", back_populates="database", cascade="all, delete-orphan")

class Table(Base):
    __tablename__ = 'db_tables'
    
    id = Column(Integer, primary_key=True)
    database_id = Column(Integer, ForeignKey('databases.id'), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String)
    row_count = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    database = relationship("Database", back_populates="tables")
    columns = relationship("Column", back_populates="table", cascade="all, delete-orphan")

class Column(Base):
    __tablename__ = 'db_columns'
    
    id = Column(Integer, primary_key=True)
    table_id = Column(Integer, ForeignKey('db_tables.id'), nullable=False)
    name = Column(String, nullable=False)
    data_type = Column(String, nullable=False)
    description = Column(String)
    is_primary_key = Column(Integer, default=0)
    is_nullable = Column(Integer, default=1)
    default_value = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    table = relationship("Table", back_populates="columns") 