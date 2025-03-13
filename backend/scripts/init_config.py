from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

# Add the project root to Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)

from core.database import init_db, SessionLocal
from models.config import Configuration

def initialize_config():
    print("Initializing database...")
    try:
        # Initialize database and create tables
        init_db()
        print("Database initialized successfully!")
        
        # Get database session
        db = SessionLocal()
        
        try:
            # Add Google Client ID configuration
            google_client_id = input("Enter your Google Client ID: ")
            
            Configuration.set_value(
                db,
                "GOOGLE_CLIENT_ID",
                google_client_id,
                "Google OAuth Client ID for authentication"
            )
            print("Configuration saved successfully!")
            
            # Verify the configuration was saved
            saved_id = Configuration.get_value(db, "GOOGLE_CLIENT_ID")
            if saved_id == google_client_id:
                print("Configuration verified successfully!")
            else:
                print("Warning: Configuration verification failed!")
            
        except Exception as e:
            print(f"Error saving configuration: {str(e)}")
            db.rollback()
        finally:
            db.close()
            
    except Exception as e:
        print(f"Database initialization error: {str(e)}")
        raise

if __name__ == "__main__":
    initialize_config() 