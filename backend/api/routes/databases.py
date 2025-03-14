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
from sqlalchemy import create_engine, text

router = APIRouter(prefix="/api/databases", tags=["databases"])

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

# Function to initialize sample databases
def init_sample_databases():
    try:
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        db_dir = os.path.join(backend_dir, "sample_dbs")
        os.makedirs(db_dir, exist_ok=True)
        
        # List of sample databases and their SQL files
        sample_dbs = {
            "inventory": "inventory.sql",
            "sample": "sample.sql",
            "users": "users.sql"
        }
        
        # Initialize each database
        for db_name, sql_file in sample_dbs.items():
            db_path = os.path.join(db_dir, f"{db_name}.db")
            sql_file_path = os.path.join(backend_dir, "databases", sql_file)
            
            if not os.path.exists(sql_file_path):
                print(f"SQL file not found: {sql_file_path}")
                continue
                
            if not os.path.exists(db_path):
                print(f"Creating database: {db_path}")
                conn = sqlite3.connect(db_path)
                with open(sql_file_path) as f:
                    sql_content = f.read()
                    try:
                        conn.executescript(sql_content)
                        conn.commit()
                        print(f"Successfully initialized {db_name} database schema")
                        
                        # Populate with sample data if it's not the users database
                        if db_name != "users":
                            populate_sql_path = os.path.join(backend_dir, "databases", "populate_data.sql")
                            if os.path.exists(populate_sql_path):
                                with open(populate_sql_path) as pf:
                                    populate_content = pf.read()
                                    try:
                                        conn.executescript(populate_content)
                                        conn.commit()
                                        print(f"Successfully populated {db_name} database with sample data")
                                    except sqlite3.Error as e:
                                        print(f"Error populating {db_name} database: {str(e)}")
                            else:
                                print(f"Sample data SQL file not found: {populate_sql_path}")
                    except sqlite3.Error as e:
                        print(f"Error initializing {db_name} database: {str(e)}")
                conn.close()
            else:
                print(f"Database already exists: {db_path}")
                
                # Repopulate existing databases with fresh data if they're not the users database
                if db_name != "users":
                    conn = sqlite3.connect(db_path)
                    populate_sql_path = os.path.join(backend_dir, "databases", "populate_data.sql")
                    if os.path.exists(populate_sql_path):
                        with open(populate_sql_path) as pf:
                            populate_content = pf.read()
                            try:
                                conn.executescript(populate_content)
                                conn.commit()
                                print(f"Successfully repopulated {db_name} database with fresh sample data")
                            except sqlite3.Error as e:
                                print(f"Error repopulating {db_name} database: {str(e)}")
                    conn.close()
    except Exception as e:
        print(f"Error in init_sample_databases: {str(e)}")

@router.get("")
def get_databases():
    # Initialize sample databases if they don't exist
    init_sample_databases()
    
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    db_dir = os.path.join(backend_dir, "sample_dbs")
    
    databases = []
    
    # Add sample databases
    sample_dbs = ["inventory", "sample", "users"]
    for db_name in sample_dbs:
        db_path = os.path.join(db_dir, f"{db_name}.db")
        if os.path.exists(db_path):
            engine = create_engine(f"sqlite:///{db_path}")
            with engine.connect() as conn:
                # Get all table names
                tables = []
                result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
                for row in result:
                    table_name = row[0]
                    # Get column information
                    columns = []
                    col_result = conn.execute(text(f"PRAGMA table_info({table_name})"))
                    for col in col_result:
                        columns.append({
                            "name": col[1],
                            "type": col[2],
                            "nullable": not col[3],
                            "primary_key": bool(col[5])
                        })
                    
                    # Get row count
                    count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    row_count = count_result.scalar()
                    
                    tables.append({
                        "name": table_name,
                        "columns": columns,
                        "row_count": row_count
                    })
            
            databases.append({
                "name": db_name,
                "tables": tables
            })
    
    return databases

@router.get("/{database_name}/tables/{table_name}")
def get_table_data(database_name: str, table_name: str, page: int = 1, page_size: int = 10):
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    db_path = os.path.join(backend_dir, "sample_dbs", f"{database_name}.db")
    
    if not os.path.exists(db_path):
        raise HTTPException(status_code=404, detail="Database not found")
    
    engine = create_engine(f"sqlite:///{db_path}")
    with engine.connect() as conn:
        # Get total count
        count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
        total_count = count_result.scalar()
        
        # Get paginated data
        offset = (page - 1) * page_size
        result = conn.execute(text(f"SELECT * FROM {table_name} LIMIT {page_size} OFFSET {offset}"))
        columns = result.keys()
        rows = [dict(zip(columns, row)) for row in result]
        
        return {
            "total": total_count,
            "page": page,
            "page_size": page_size,
            "data": rows
        }

@router.post("/analyze-sql")
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

@router.post("/{database_name}/execute-sql")
async def execute_sql(
    database_name: str,
    sql_query: str = Body(...),
    user_id: Optional[int] = Body(None),
    db: Session = Depends(get_db)
):
    """
    Execute a SQL query on a specific database and return the results
    """
    try:
        # For SQLite databases
        databases_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "sample_dbs")
        db_path = os.path.join(databases_dir, f"{database_name}.db")
        
        if not os.path.exists(db_path):
            raise HTTPException(status_code=404, detail=f"Database '{database_name}' not found")
        
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