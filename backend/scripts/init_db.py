import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import engine, SessionLocal
from models.base import Base, User
from datetime import datetime
import bcrypt

def init_database():
    """Initialize the database by creating all tables and adding a test user."""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create a session
    db = SessionLocal()
    
    try:
        # Check if test user exists
        test_user = db.query(User).filter(User.username == "test_user").first()
        
        if not test_user:
            # Create test user
            password = "test123"
            salt = bcrypt.gensalt()
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
            
            test_user = User(
                username="test_user",
                email="test@example.com",
                password_hash=hashed_password.decode('utf-8'),
                role="analyst",
                qualifications={"languages": ["Python", "JavaScript"], "experience": "5 years"}
            )
            db.add(test_user)
            db.commit()
            print("Test user created successfully!")
        else:
            print("Test user already exists.")
            
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Initializing database...")
    init_database()
    print("Database initialization completed!") 