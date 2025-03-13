import re
import json
from typing import Dict, Any

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

# Test the function with a sample SQL code
sql_code = """
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL,
    email TEXT UNIQUE,
    created_at TIMESTAMP
);

CREATE TABLE posts (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    title TEXT NOT NULL,
    content TEXT,
    created_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
"""

result = parse_sql_manually(sql_code)
print(json.dumps(result, indent=2)) 