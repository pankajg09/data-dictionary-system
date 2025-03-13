import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import SessionLocal
from models.base import User, Analysis, QueryExecution
from datetime import datetime

def test_database():
    """Test database functionality by performing basic operations."""
    db = SessionLocal()
    
    try:
        # 1. Check if test user exists
        test_user = db.query(User).filter(User.username == "test_user").first()
        if test_user:
            print(f"Found test user: {test_user.username} (ID: {test_user.id})")
        else:
            print("Test user not found!")
            return
        
        # 2. Create a test analysis
        test_analysis = Analysis(
            title="Test Analysis",
            description="Testing database functionality",
            analyst_id=test_user.id,
            status="draft",
            analysis_results={
                "tables": [
                    {
                        "name": "TestTable",
                        "fields": [
                            {"name": "id", "type": "integer", "description": "Primary key"}
                        ]
                    }
                ]
            }
        )
        db.add(test_analysis)
        db.commit()
        db.refresh(test_analysis)
        print(f"\nCreated test analysis with ID: {test_analysis.id}")
        
        # 3. Create a test query execution
        test_execution = QueryExecution(
            user_id=test_user.id,
            analysis_id=test_analysis.id,
            query_content="SELECT * FROM test",
            execution_status="success",
            execution_duration=100
        )
        db.add(test_execution)
        db.commit()
        print("\nCreated test query execution")
        
        # 4. Verify data
        print("\nVerifying stored data:")
        
        # Check analyses
        analyses = db.query(Analysis).filter(Analysis.analyst_id == test_user.id).all()
        print(f"\nFound {len(analyses)} analyses for test user")
        for analysis in analyses:
            print(f"- Analysis {analysis.id}: {analysis.title} ({analysis.status})")
        
        # Check query executions
        executions = db.query(QueryExecution).filter(QueryExecution.user_id == test_user.id).all()
        print(f"\nFound {len(executions)} query executions for test user")
        for execution in executions:
            print(f"- Execution {execution.id}: {execution.execution_status} ({execution.execution_duration}ms)")
        
    except Exception as e:
        print(f"Error during testing: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Testing database functionality...")
    test_database()
    print("\nDatabase testing completed!") 