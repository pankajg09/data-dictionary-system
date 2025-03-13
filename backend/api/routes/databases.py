from fastapi import APIRouter, HTTPException, Depends, Body
from sqlalchemy.orm import Session
from core.database import get_db
from models.base import Database, Table, Column
from typing import List, Dict, Any, Optional
import os
import sqlite3
import json
from openai import OpenAI
import re
from pydantic import BaseModel
from services.ai.analysis_service import AnalysisService

router = APIRouter()

# Configure OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class SQLAnalysisRequest(BaseModel):
    sql_code: str

def analyze_sql_with_llm(sql_code: str) -> Dict[str, Any]:
    """
    Use LLM to analyze SQL code and extract data dictionary information
    """
    # Check if OpenAI API key is available
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("OpenAI API key not found. Using mock response.")
        # Parse the SQL code manually to extract basic information
        return parse_sql_manually(sql_code)
        
    try:
        prompt = f"""
        Analyze the following SQL code and extract information about tables, columns, and their relationships.
        Return the response as a JSON object with the following structure:
        {{
            "tables": [
                {{
                    "name": "table_name",
                    "columns": [
                        {{
                            "name": "column_name",
                            "type": "data_type",
                            "description": "description based on column name and context",
                            "constraints": ["PRIMARY KEY", "NOT NULL", etc.]
                        }}
                    ]
                }}
            ],
            "relationships": [
                {{
                    "from_table": "source_table",
                    "from_column": "source_column",
                    "to_table": "target_table",
                    "to_column": "target_column",
                    "type": "relationship_type (e.g., one-to-many)"
                }}
            ]
        }}

        SQL Code:
        {sql_code}
        
        Important instructions:
        1. Identify all tables and their columns from CREATE TABLE statements
        2. Extract data types, constraints (PRIMARY KEY, FOREIGN KEY, NOT NULL, etc.)
        3. Infer relationships from FOREIGN KEY constraints
        4. Generate meaningful descriptions for columns based on their names and context
        5. Return only valid JSON without any additional text or explanations
        """

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a SQL expert that analyzes SQL code and extracts structured information."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        # Parse the response
        result = json.loads(response.choices[0].message.content)
        return result
    except Exception as e:
        print(f"Error analyzing SQL with LLM: {str(e)}")
        # Fallback to manual parsing if LLM fails
        return parse_sql_manually(sql_code)

def parse_sql_manually(sql_code: str) -> Dict[str, Any]:
    """
    Parse SQL code manually to extract basic information about tables and relationships
    """
    tables = []
    relationships = []
    
    # Regular expressions to match CREATE TABLE statements and column definitions
    create_table_pattern = r"CREATE\s+TABLE\s+(\w+)\s*\((.*?)\);"
    column_pattern = r"(\w+)\s+(\w+)(?:\s+(\w+))?"
    foreign_key_pattern = r"FOREIGN\s+KEY\s+\((\w+)\)\s+REFERENCES\s+(\w+)\((\w+)\)"
    
    # Find all CREATE TABLE statements
    for table_match in re.finditer(create_table_pattern, sql_code, re.DOTALL | re.IGNORECASE):
        table_name = table_match.group(1)
        columns_text = table_match.group(2)
        
        table = {
            "name": table_name,
            "columns": []
        }
        
        # Process each line in the columns text
        for line in columns_text.split(","):
            line = line.strip()
            
            # Check if this line defines a foreign key
            fk_match = re.search(foreign_key_pattern, line, re.IGNORECASE)
            if fk_match:
                from_column = fk_match.group(1)
                to_table = fk_match.group(2)
                to_column = fk_match.group(3)
                
                relationships.append({
                    "from_table": table_name,
                    "from_column": from_column,
                    "to_table": to_table,
                    "to_column": to_column,
                    "type": "many-to-one"  # Assuming most common relationship type
                })
                continue
            
            # Check if this line defines a column
            col_match = re.search(column_pattern, line, re.IGNORECASE)
            if col_match:
                col_name = col_match.group(1)
                col_type = col_match.group(2)
                
                constraints = []
                if "PRIMARY KEY" in line.upper():
                    constraints.append("PRIMARY KEY")
                if "NOT NULL" in line.upper():
                    constraints.append("NOT NULL")
                if "UNIQUE" in line.upper():
                    constraints.append("UNIQUE")
                
                # Generate a simple description based on column name
                description = f"{col_name.replace('_', ' ').title()} of the {table_name}"
                
                table["columns"].append({
                    "name": col_name,
                    "type": col_type,
                    "description": description,
                    "constraints": constraints
                })
        
        tables.append(table)
    
    return {
        "tables": tables,
        "relationships": relationships
    }

@router.get("/databases")
async def get_databases(db: Session = Depends(get_db)):
    """
    Get a list of all databases with their tables and sample data
    """
    try:
        # For demonstration, we'll use SQLite database files in a 'databases' directory
        # In a real application, you would use your database connection configuration
        databases_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "databases")
        
        # Create the directory if it doesn't exist
        os.makedirs(databases_dir, exist_ok=True)
        
        # Get all .db files in the directory
        db_files = [f for f in os.listdir(databases_dir) if f.endswith('.db')]
        
        databases = []
        
        # If no database files found, return the main application database
        if not db_files:
            # Get the main database information
            main_db = {
                "name": "Main Database",
                "description": "Primary application database",
                "tables": []
            }
            
            # Get all table names from SQLAlchemy metadata
            from sqlalchemy import inspect
            inspector = inspect(db.bind)
            table_names = inspector.get_table_names()
            
            for table_name in table_names:
                # Get column information
                columns = []
                for column in inspector.get_columns(table_name):
                    columns.append({
                        "name": column["name"],
                        "type": str(column["type"]),
                        "description": ""
                    })
                
                # Get sample data (first 10 rows)
                rows = []
                try:
                    result = db.execute(f"SELECT * FROM {table_name} LIMIT 10")
                    rows = [dict(row) for row in result]
                except Exception as e:
                    print(f"Error fetching rows for table {table_name}: {str(e)}")
                
                # Get row count
                row_count = 0
                try:
                    result = db.execute(f"SELECT COUNT(*) FROM {table_name}")
                    row_count = result.scalar()
                except Exception as e:
                    print(f"Error getting row count for table {table_name}: {str(e)}")
                
                main_db["tables"].append({
                    "name": table_name,
                    "columns": columns,
                    "rows": rows,
                    "rowCount": row_count
                })
            
            databases.append(main_db)
            return databases
        
        # Process each database file
        for db_file in db_files:
            db_path = os.path.join(databases_dir, db_file)
            db_name = os.path.splitext(db_file)[0]
            
            database = {
                "name": db_name,
                "description": f"SQLite database: {db_file}",
                "tables": []
            }
            
            try:
                # Connect to the SQLite database
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get all table names
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                table_names = [row[0] for row in cursor.fetchall()]
                
                for table_name in table_names:
                    # Skip SQLite system tables
                    if table_name.startswith('sqlite_'):
                        continue
                    
                    # Get column information
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = []
                    for col in cursor.fetchall():
                        columns.append({
                            "name": col["name"],
                            "type": col["type"],
                            "description": ""
                        })
                    
                    # Get sample data (first 10 rows)
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 10")
                    rows = [dict(row) for row in cursor.fetchall()]
                    
                    # Get row count
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    row_count = cursor.fetchone()[0]
                    
                    database["tables"].append({
                        "name": table_name,
                        "columns": columns,
                        "rows": rows,
                        "rowCount": row_count
                    })
                
                conn.close()
            except Exception as e:
                print(f"Error processing database {db_file}: {str(e)}")
                database["description"] = f"Error: {str(e)}"
            
            databases.append(database)
        
        return databases
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching databases: {str(e)}")

@router.get("/databases/{db_name}/tables/{table_name}")
async def get_table_data(db_name: str, table_name: str, limit: int = 100, offset: int = 0, db: Session = Depends(get_db)):
    """
    Get detailed data for a specific table
    """
    try:
        # For the main database
        if db_name == "main":
            # Get column information
            from sqlalchemy import inspect
            inspector = inspect(db.bind)
            
            if table_name not in inspector.get_table_names():
                raise HTTPException(status_code=404, detail=f"Table {table_name} not found")
            
            columns = []
            for column in inspector.get_columns(table_name):
                columns.append({
                    "name": column["name"],
                    "type": str(column["type"]),
                    "description": ""
                })
            
            # Get data with pagination
            result = db.execute(f"SELECT * FROM {table_name} LIMIT {limit} OFFSET {offset}")
            rows = [dict(row) for row in result]
            
            # Get total row count
            result = db.execute(f"SELECT COUNT(*) FROM {table_name}")
            total_rows = result.scalar()
            
            return {
                "name": table_name,
                "columns": columns,
                "rows": rows,
                "totalRows": total_rows,
                "limit": limit,
                "offset": offset
            }
        
        # For other SQLite databases
        databases_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "databases")
        db_path = os.path.join(databases_dir, f"{db_name}.db")
        
        if not os.path.exists(db_path):
            raise HTTPException(status_code=404, detail=f"Database {db_name} not found")
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail=f"Table {table_name} not found in database {db_name}")
        
        # Get column information
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = []
        for col in cursor.fetchall():
            columns.append({
                "name": col["name"],
                "type": col["type"],
                "description": ""
            })
        
        # Get data with pagination
        cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit} OFFSET {offset}")
        rows = [dict(row) for row in cursor.fetchall()]
        
        # Get total row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        total_rows = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "name": table_name,
            "columns": columns,
            "rows": rows,
            "totalRows": total_rows,
            "limit": limit,
            "offset": offset
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching table data: {str(e)}")

@router.post("/databases/analyze-sql")
async def analyze_sql(request: SQLAnalysisRequest, db: Session = Depends(get_db)):
    """
    Analyze SQL code using LLM to extract schema information
    """
    try:
        analysis_service = AnalysisService(db, client)
        result = await analysis_service.analyze_sql_with_llm(request.sql_code)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing code: {str(e)}")

@router.post("/databases/{db_name}/execute-sql")
async def execute_sql(
    db_name: str,
    sql_query: str = Body(...),
    user_id: Optional[int] = Body(None),
    db: Session = Depends(get_db)
):
    """
    Execute a SQL query on a specific database and return the results
    """
    try:
        # For SQLite databases
        databases_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "databases")
        db_path = os.path.join(databases_dir, f"{db_name}.db")
        
        if not os.path.exists(db_path):
            raise HTTPException(status_code=404, detail=f"Database {db_name} not found")
        
        # Connect to the database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Execute the query
        try:
            cursor.execute(sql_query)
            rows = [dict(row) for row in cursor.fetchall()]
            
            # Get column names and types
            columns = []
            if rows:
                for key in rows[0].keys():
                    columns.append({
                        "name": key,
                        "type": "unknown"  # SQLite doesn't provide type info easily
                    })
            
            # Record the query execution if user_id is provided
            if user_id:
                query_execution = QueryExecution(
                    user_id=user_id,
                    analysis_id=None,  # No analysis associated
                    query_content=sql_query,
                    execution_status="success",
                    execution_duration=0  # We're not measuring duration
                )
                db.add(query_execution)
                db.commit()
            
            conn.close()
            
            # Return the results
            return {
                "columns": columns,
                "rows": rows,
                "rowCount": len(rows)
            }
        except Exception as e:
            conn.close()
            
            # Record the failed query execution if user_id is provided
            if user_id:
                query_execution = QueryExecution(
                    user_id=user_id,
                    analysis_id=None,  # No analysis associated
                    query_content=sql_query,
                    execution_status="failed",
                    error_message=str(e),
                    execution_duration=0  # We're not measuring duration
                )
                db.add(query_execution)
                db.commit()
            
            raise HTTPException(status_code=400, detail=f"SQL execution error: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing SQL: {str(e)}") 