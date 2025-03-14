from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
import sys
import os

# Add the project root to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)

# Import Base and models
from models.base import (
    Base, User, Analysis, DataDictionary, Review,
    CodeSnippet, QueryExecution, Database,
    Table, Column
)

# Set up database path
db_path = os.path.join(backend_dir, "data_dictionary.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def backup_users():
    """Backup users table data before dropping tables."""
    db = SessionLocal()
    try:
        inspector = inspect(engine)
        if 'users' in inspector.get_table_names():
            users = db.query(User).all()
            return [
                {
                    'email': user.email,
                    'name': user.name,
                    'picture': user.picture,
                    'role': user.role,
                    'google_id': user.google_id,
                    'login_count': user.login_count,
                    'first_login_at': user.first_login_at,
                    'last_login_at': user.last_login_at,
                    'created_at': user.created_at,
                    'updated_at': user.updated_at
                }
                for user in users
            ]
        return []
    finally:
        db.close()

def restore_users(users_data):
    """Restore users from backup data."""
    db = SessionLocal()
    try:
        for user_data in users_data:
            existing_user = db.query(User).filter_by(email=user_data['email']).first()
            if not existing_user:
                user = User(**user_data)
                db.add(user)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error restoring users: {str(e)}")
        raise
    finally:
        db.close()

def init_db():
    try:
        # Backup existing users
        users_backup = backup_users()
        print(f"Backed up {len(users_backup)} users")
        
        # Drop all tables
        Base.metadata.drop_all(bind=engine)
        print("Existing tables dropped successfully!")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully!")
        
        # Restore users if any were backed up
        if users_backup:
            restore_users(users_backup)
            print(f"Restored {len(users_backup)} users successfully!")
            
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        raise

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 