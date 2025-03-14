import os
import json
import re
import ast
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session
from openai import OpenAI
import google.generativeai as genai
from models.base import Analysis, DataDictionary, CodeSnippet, QueryExecution

class AnalysisService:
    def __init__(self, db_session: Session, openai_client: OpenAI):
        self.db = db_session
        self.ai = openai_client
        
        # Configure Gemini client if available
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        if self.google_api_key:
            try:
                genai.configure(api_key=self.google_api_key)
            except Exception as e:
                print(f"Failed to initialize Gemini client: {str(e)}")
        
    def parse_sql(self, sql_code: str) -> Dict:
        """Parse SQL code to extract table and column information"""
        tables = []
        
        # Pattern for CREATE TABLE statements
        create_table_pattern = r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([`\"]?\w+[`\"]?)?\s*\(([\s\S]*?)\)(?:\s*;)?"
        
        # Find all CREATE TABLE statements
        for match in re.finditer(create_table_pattern, sql_code, re.IGNORECASE):
            table_name = match.group(1)
            if table_name:
                table_name = table_name.strip('`"')
                
            columns_text = match.group(2)
            columns = []
            relationships = []
            
            # Split column definitions, handling commas inside parentheses
            col_defs = []
            paren_count = 0
            current_def = []
            in_string = False
            string_char = None
            
            for char in columns_text:
                # Handle string literals
                if char in ["'", '"'] and not in_string:
                    in_string = True
                    string_char = char
                elif char == string_char and in_string:
                    in_string = False
                    string_char = None
                # Handle parentheses only if not in string
                elif not in_string:
                    if char == '(':
                        paren_count += 1
                    elif char == ')':
                        paren_count -= 1
                    elif char == ',' and paren_count == 0:
                        col_defs.append(''.join(current_def).strip())
                        current_def = []
                        continue
                current_def.append(char)
            
            if current_def:
                col_defs.append(''.join(current_def).strip())
            
            # Process each column definition
            for col_def in col_defs:
                # Skip empty definitions
                if not col_def.strip():
                    continue
                    
                # Handle foreign key constraints
                if re.match(r"\s*FOREIGN\s+KEY\b", col_def, re.IGNORECASE):
                    fk_match = re.search(r"FOREIGN\s+KEY\s*\(([^)]+)\)\s*REFERENCES\s+([`\"]?\w+[`\"]?)\s*(?:\(([^)]+)\))?", col_def, re.IGNORECASE)
                    if fk_match:
                        source_cols = [col.strip('`" ') for col in fk_match.group(1).split(',')]
                        target_table = fk_match.group(2).strip('`"')
                        target_cols = []
                        if fk_match.group(3):
                            target_cols = [col.strip('`" ') for col in fk_match.group(3).split(',')]
                        else:
                            target_cols = ['id']  # Default to 'id' if not specified
                        
                        relationships.append({
                            "type": "foreign_key",
                            "from_table": table_name,
                            "from_fields": source_cols,
                            "to_table": target_table,
                            "to_fields": target_cols
                        })
                    continue
                
                # Extract column name
                name_match = re.match(r"([`\"]?\w+[`\"]?)\s+", col_def)
                if not name_match:
                    continue
                
                column_name = name_match.group(1).strip('`"')
                remaining_def = col_def[len(name_match.group(0)):].strip()
                
                # Extract data type
                type_match = re.match(r"(\w+(?:\s*\([^)]*\))?)", remaining_def)
                if not type_match:
                    continue
                
                data_type = type_match.group(1).strip()
                remaining_def = remaining_def[len(type_match.group(0)):].strip()
                
                # Extract comment if present
                comment_match = re.search(r"COMMENT\s+['\"]((?:[^'\"\\]|\\.)*)['\"]", remaining_def, re.IGNORECASE)
                comment = comment_match.group(1) if comment_match else ""
                
                # Extract constraints
                constraints = []
                constraint_patterns = [
                    (r"\bPRIMARY\s+KEY\b", "PRIMARY KEY"),
                    (r"\bUNIQUE\b", "UNIQUE"),
                    (r"\bNOT\s+NULL\b", "NOT NULL"),
                    (r"\bDEFAULT\s+(?:[^,\s]+|\([^)]+\))", "DEFAULT"),
                    (r"\bCHECK\s*\([^)]+\)", "CHECK"),
                    (r"\bAUTO_INCREMENT\b", "AUTO_INCREMENT")
                ]
                
                for pattern, constraint_name in constraint_patterns:
                    constraint_match = re.search(pattern, remaining_def, re.IGNORECASE)
                    if constraint_match:
                        if constraint_name == "DEFAULT":
                            default_value = constraint_match.group(0).split(None, 1)[1]
                            constraints.append(f"DEFAULT {default_value}")
                        else:
                            constraints.append(constraint_name)
                
                columns.append({
                    "name": column_name,
                    "type": data_type,
                    "description": comment,
                    "constraints": constraints
                })
            
            tables.append({
                "name": table_name,
                "fields": columns,
                "relationships": relationships
            })
        
        return {
            "tables": tables,
            "type": "sql_analysis"
        }

    async def analyze_code(self, code: str, analysis_id: Optional[int] = None, user_id: Optional[int] = None) -> Dict:
        """
        Analyze code using OpenAI or Gemini to extract data dictionary information and optionally store results
        """
        start_time = datetime.utcnow()
        execution_status = "success"
        error_message = None
        
        model_used = "OpenAI GPT-3.5 Turbo"
        try:
            # First try to parse as SQL if it looks like SQL code
            if re.search(r"CREATE\s+TABLE|ALTER\s+TABLE|SELECT\s+.*\s+FROM", code, re.IGNORECASE):
                analysis_result = self.parse_sql(code)
                if analysis_result["tables"]:  # If SQL parsing found tables
                    model_used = "SQL Parser"
                    return {
                        "analysis_id": analysis_id,
                        "results": {
                            **analysis_result,
                            "model_used": model_used,
                            "documentation_summary": "SQL schema analysis"
                        }
                    }
            
            # Try OpenAI first
            try:
                response = await self.ai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a code analysis expert. Extract data-related information from the code."},
                        {"role": "user", "content": f"""Analyze this code and extract information about data structures, types, and relationships.
                        Return the response in the following JSON format:
                        {{
                            "tables": [
                                {{
                                    "name": "table_name",
                                    "fields": [
                                        {{
                                            "name": "field_name",
                                            "type": "field_type",
                                            "description": "field_description"
                                        }}
                                    ]
                                }}
                            ],
                            "relationships": [
                                {{
                                    "from_table": "source",
                                    "to_table": "target",
                                    "type": "relationship_type",
                                    "from_field": "source_field",
                                    "to_field": "target_field"
                                }}
                            ],
                            "code_snippets": [
                                {{
                                    "code": "code_here",
                                    "language": "language_name",
                                    "description": "description"
                                }}
                            ],
                            "data_sources": ["list_of_data_sources"],
                            "data_transformations": ["list_of_transformations"],
                            "potential_reuse_opportunities": ["list_of_opportunities"],
                            "documentation_summary": "summary_text"
                        }}

                        Here's the code to analyze:

                        {code}"""}
                    ]
                )
                analysis_result = self._parse_ai_response(response.choices[0].message.content)
            except Exception as openai_error:
                print(f"OpenAI analysis failed: {str(openai_error)}, trying Gemini...")
                # Try Gemini as fallback
                try:
                    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
                    model = genai.GenerativeModel('gemini-1.5-pro')
                    response = model.generate_content(
                        f"""You are a code analysis expert. Analyze this code and extract information about data structures, types, and relationships.
                        Return the response in the following JSON format:
                        {{
                            "tables": [
                                {{
                                    "name": "table_name",
                                    "fields": [
                                        {{
                                            "name": "field_name",
                                            "type": "field_type",
                                            "description": "field_description"
                                        }}
                                    ]
                                }}
                            ],
                            "relationships": [
                                {{
                                    "from_table": "source",
                                    "to_table": "target",
                                    "type": "relationship_type",
                                    "from_field": "source_field",
                                    "to_field": "target_field"
                                }}
                            ],
                            "code_snippets": [
                                {{
                                    "code": "code_here",
                                    "language": "language_name",
                                    "description": "description"
                                }}
                            ],
                            "data_sources": ["list_of_data_sources"],
                            "data_transformations": ["list_of_transformations"],
                            "potential_reuse_opportunities": ["list_of_opportunities"],
                            "documentation_summary": "summary_text"
                        }}

                        Here's the code to analyze:

                        {code}

                        Remember to:
                        1. Always return valid JSON
                        2. Include all fields even if empty
                        3. For each class, create a table entry with its fields
                        4. Identify relationships between classes (e.g., foreign keys)
                        5. Extract meaningful code snippets with descriptions
                        6. Provide a comprehensive documentation summary"""
                    )
                    # Ensure we get the text content from the response
                    analysis_result = self._parse_ai_response(response.text)
                    model_used = "Gemini 1.5 Pro"
                except Exception as gemini_error:
                    raise Exception(f"Both OpenAI and Gemini analysis failed. OpenAI error: {str(openai_error)}, Gemini error: {str(gemini_error)}")
            
            # Store the model used in the analysis result
            analysis_result['model_used'] = model_used
            
            # Create a new analysis if analysis_id is not provided
            if not analysis_id and user_id:
                new_analysis = Analysis(
                    title=f"Code Analysis {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}",
                    description="Automated code analysis",
                    analyst_id=user_id,
                    status="draft",
                    analysis_results=analysis_result
                )
                self.db.add(new_analysis)
                try:
                    self.db.commit()
                    self.db.refresh(new_analysis)
                    analysis_id = new_analysis.id
                except Exception as e:
                    self.db.rollback()
                    raise Exception(f"Error creating new analysis: {str(e)}")
            # If analysis_id is provided, update existing analysis
            elif analysis_id:
                await self.store_analysis_results(analysis_id, analysis_result)
            
            return {
                "analysis_id": analysis_id,
                "results": analysis_result
            }
        except Exception as e:
            execution_status = "failed"
            error_message = str(e)
            raise Exception(f"Error analyzing code: {str(e)}")
        finally:
            if user_id:
                end_time = datetime.utcnow()
                duration = int((end_time - start_time).total_seconds() * 1000)  # Convert to milliseconds
                
                # Record query execution
                query_execution = QueryExecution(
                    user_id=user_id,
                    analysis_id=analysis_id if analysis_id else None,
                    query_content=code[:1000],  # Store first 1000 characters of the query
                    execution_status=execution_status,
                    error_message=error_message,
                    execution_duration=duration
                )
                self.db.add(query_execution)
                try:
                    self.db.commit()
                except Exception:
                    self.db.rollback()
    
    async def store_analysis_results(self, analysis_id: int, results: Dict) -> None:
        """
        Store analysis results in the database
        """
        try:
            analysis = self.db.query(Analysis).filter(Analysis.id == analysis_id).first()
            if not analysis:
                raise Exception(f"Analysis with id {analysis_id} not found")
            
            analysis.analysis_results = results
            analysis.status = 'pending_review'
            analysis.review_status = 'pending'
            
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Error storing analysis results: {str(e)}")
    
    async def submit_for_review(self, analysis_id: int, reviewer_id: int) -> None:
        """
        Submit analysis for review
        """
        try:
            analysis = self.db.query(Analysis).filter(Analysis.id == analysis_id).first()
            if not analysis:
                raise Exception(f"Analysis with id {analysis_id} not found")
            
            analysis.reviewer_id = reviewer_id
            analysis.review_status = 'in_review'
            analysis.status = 'pending_review'
            
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Error submitting for review: {str(e)}")
    
    async def submit_review(self, analysis_id: int, reviewer_id: int, comments: Dict, approved: bool) -> None:
        """
        Submit review for an analysis
        """
        try:
            analysis = self.db.query(Analysis).filter(
                Analysis.id == analysis_id,
                Analysis.reviewer_id == reviewer_id
            ).first()
            
            if not analysis:
                raise Exception(f"Analysis with id {analysis_id} not found or not assigned to reviewer {reviewer_id}")
            
            analysis.review_comments = comments
            analysis.review_status = 'reviewed'
            analysis.status = 'approved' if approved else 'rejected'
            analysis.review_date = datetime.utcnow()
            
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Error submitting review: {str(e)}")
    
    def _parse_ai_response(self, response: str) -> Dict:
        """
        Parse the AI response into structured data dictionary information
        """
        try:
            # Clean up the response text
            response = response.strip()
            
            # Extract JSON from markdown code blocks if present
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            
            response = response.strip()
            
            # Try to parse the response as JSON
            try:
                parsed_data = json.loads(response)
                if isinstance(parsed_data, dict):
                    # Ensure all required fields are present with default values
                    return {
                        "tables": parsed_data.get("tables", []),
                        "relationships": parsed_data.get("relationships", []),
                        "code_snippets": parsed_data.get("code_snippets", []),
                        "data_sources": parsed_data.get("data_sources", []),
                        "data_transformations": parsed_data.get("data_transformations", []),
                        "potential_reuse_opportunities": parsed_data.get("potential_reuse_opportunities", []),
                        "documentation_summary": parsed_data.get("documentation_summary", "")
                    }
            except json.JSONDecodeError as e:
                print(f"JSON parsing error: {str(e)}")
                print(f"Raw response: {response}")

            # If JSON parsing fails, try to extract information using regex
            analysis_data = {
                "tables": [],
                "relationships": [],
                "code_snippets": [],
                "data_sources": [],
                "data_transformations": [],
                "potential_reuse_opportunities": [],
                "documentation_summary": ""
            }

            # Extract tables and their fields using improved regex
            table_pattern = r"(?:class|table)\s+(\w+)(?:\(.*?\))?[\s\n]*{([^}]+)}"
            for match in re.finditer(table_pattern, response, re.MULTILINE | re.IGNORECASE):
                table_name = match.group(1)
                fields_text = match.group(2)
                fields = []
                
                # Look for field definitions in various formats
                field_patterns = [
                    r"(\w+)\s*:\s*([\w\[\]\.]+)(?:\s*=\s*[^,\n]+)?(?:\s*#\s*(.+))?",  # Type hints
                    r"self\.(\w+)\s*=\s*([^#\n]+)(?:\s*#\s*(.+))?",  # Instance variables with comments
                    r"(\w+)\s*=\s*([^#\n]+)(?:\s*#\s*(.+))?"  # Assignments with comments
                ]
                
                for pattern in field_patterns:
                    for field_match in re.finditer(pattern, fields_text):
                        field_name = field_match.group(1)
                        field_type = field_match.group(2) if len(field_match.groups()) > 1 else "any"
                        description = field_match.group(3) if len(field_match.groups()) > 2 else ""
                        
                        # Clean up the type if it's a value rather than a type
                        if field_type and not any(type_word in field_type.lower() for type_word in ["str", "int", "float", "bool", "list", "dict", "any"]):
                            # Try to infer type from the value
                            if field_type.startswith('"') or field_type.startswith("'"):
                                field_type = "str"
                            elif field_type.replace(".", "").isdigit():
                                field_type = "float" if "." in field_type else "int"
                            elif field_type.lower() in ["true", "false"]:
                                field_type = "bool"
                            else:
                                field_type = "any"
                        
                        fields.append({
                            "name": field_name.strip(),
                            "type": field_type.strip() if field_type else "any",
                            "description": description.strip() if description else ""
                        })
                
                if fields:  # Only add tables that have fields
                    analysis_data["tables"].append({
                        "name": table_name,
                        "fields": fields
                    })

            # Extract relationships with improved pattern
            rel_patterns = [
                r"(?:relationship|foreign[\s_]key):\s*(\w+)\.(\w+)\s*->\s*(\w+)\.(\w+)",
                r"(\w+)\s+references\s+(\w+)(?:\((\w+)\))?",
                r"(?:self\.)?(\w+)(?:\s*=\s*|\s*:\s*).*?(?:id|ID|Id).*?#.*?(?:References|references|REFERENCES)\s+(\w+)"
            ]
            
            for pattern in rel_patterns:
                for match in re.finditer(pattern, response, re.MULTILINE | re.IGNORECASE):
                    if len(match.groups()) == 4:  # First pattern
                        analysis_data["relationships"].append({
                            "from_table": match.group(1),
                            "from_field": match.group(2),
                            "to_table": match.group(3),
                            "to_field": match.group(4),
                            "type": "foreign_key"
                        })
                    elif len(match.groups()) == 2:  # Third pattern (comment-based)
                        analysis_data["relationships"].append({
                            "from_table": match.group(1),
                            "to_table": match.group(2),
                            "type": "foreign_key"
                        })
                    else:  # Second pattern
                        analysis_data["relationships"].append({
                            "from_table": match.group(1),
                            "to_table": match.group(2),
                            "to_field": match.group(3) if len(match.groups()) > 2 else "id",
                            "type": "foreign_key"
                        })

            # Extract code snippets with language detection
            code_pattern = r"```(\w+)?\n(.*?)```"
            for match in re.finditer(code_pattern, response, re.DOTALL):
                language = match.group(1) or "python"
                code = match.group(2).strip()
                analysis_data["code_snippets"].append({
                    "code": code,
                    "language": language.lower(),
                    "description": ""
                })

            # Extract documentation summary
            summary_patterns = [
                r"(?:summary|documentation):\s*(.+?)(?=\n\n|\Z)",
                r"\/\*\*\s*\n\s*\*\s*(.+?)\s*\n\s*\*\/",
                r"#\s*(.+?)(?=\n\n|\Z)"  # Simple comment-based summary
            ]
            
            for pattern in summary_patterns:
                summary_match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
                if summary_match:
                    analysis_data["documentation_summary"] = summary_match.group(1).strip()
                    break

            # If no summary was found, generate one based on the tables and relationships
            if not analysis_data["documentation_summary"]:
                table_names = [table["name"] for table in analysis_data["tables"]]
                if table_names:
                    analysis_data["documentation_summary"] = f"Code defines {len(table_names)} main data structures: {', '.join(table_names)}."
                    if analysis_data["relationships"]:
                        analysis_data["documentation_summary"] += f" Contains {len(analysis_data['relationships'])} relationships between entities."

            return analysis_data

        except Exception as e:
            print(f"Error parsing AI response: {str(e)}")
            print(f"Raw response: {response}")
            # Return a basic structure if parsing fails
            return {
                "tables": [],
                "relationships": [],
                "code_snippets": [],
                "data_sources": [],
                "data_transformations": [],
                "potential_reuse_opportunities": [],
                "documentation_summary": f"Error parsing response: {str(e)}"
            }
    
    def extract_code_structure(self, code: str) -> Dict:
        """
        Extract code structure using AST
        """
        try:
            tree = ast.parse(code)
            return self._analyze_ast(tree)
        except Exception as e:
            raise Exception(f"Error parsing code: {str(e)}")
    
    def _analyze_ast(self, tree: ast.AST) -> Dict:
        """
        Analyze the AST to extract relevant information
        """
        data_structures = []
        functions = []
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                data_structures.append(self._analyze_class(node))
            elif isinstance(node, ast.FunctionDef):
                functions.append(self._analyze_function(node))
            elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                imports.extend(self._analyze_import(node))
                
        return {
            "data_structures": data_structures,
            "functions": functions,
            "imports": imports
        }
    
    def _analyze_class(self, node: ast.ClassDef) -> Dict:
        """
        Analyze a class definition
        """
        return {
            "name": node.name,
            "fields": self._extract_class_fields(node),
            "methods": [m.name for m in node.body if isinstance(m, ast.FunctionDef)]
        }
    
    def _extract_class_fields(self, node: ast.ClassDef) -> List[Dict]:
        """
        Extract fields from a class definition
        """
        fields = []
        for item in node.body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                fields.append({
                    "name": item.target.id,
                    "type": self._get_type_annotation(item.annotation)
                })
        return fields
    
    def _analyze_function(self, node: ast.FunctionDef) -> Dict:
        """
        Analyze a function definition
        """
        return {
            "name": node.name,
            "args": self._extract_function_args(node),
            "returns": self._get_type_annotation(node.returns) if hasattr(node, "returns") else None
        }
    
    def _extract_function_args(self, node: ast.FunctionDef) -> List[Dict]:
        """
        Extract function arguments and their types
        """
        args = []
        for arg in node.args.args:
            args.append({
                "name": arg.arg,
                "type": self._get_type_annotation(arg.annotation) if hasattr(arg, "annotation") else None
            })
        return args
    
    def _analyze_import(self, node: ast.AST) -> List[str]:
        """
        Analyze import statements
        """
        if isinstance(node, ast.Import):
            return [n.name for n in node.names]
        elif isinstance(node, ast.ImportFrom):
            return [f"{node.module}.{n.name}" for n in node.names]
        return []
    
    def _get_type_annotation(self, node: Optional[ast.AST]) -> Optional[str]:
        """
        Get string representation of type annotation
        """
        if node is None:
            return None
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Subscript):
            return f"{self._get_type_annotation(node.value)}[{self._get_type_annotation(node.slice)}]"
        return str(node)
    
    async def create_data_dictionary(self, analysis_id: int, code: str) -> List[DataDictionary]:
        """
        Create data dictionary entries from code analysis
        """
        # Analyze code structure
        code_structure = self.extract_code_structure(code)
        
        # Get AI insights
        ai_analysis = await self.analyze_code(code)
        
        # Store code chunks
        await self.store_code_chunks(analysis_id, code)
        
        # Combine structural and AI analysis
        data_dictionaries = []
        
        # Process data structures
        for structure in code_structure["data_structures"]:
            for field in structure["fields"]:
                dd = DataDictionary(
                    analysis_id=analysis_id,
                    table_name=structure["name"],
                    column_name=field["name"],
                    data_type=field["type"],
                    description=self._get_ai_description(ai_analysis["results"], structure["name"], field["name"]),
                    valid_values=self._get_ai_valid_values(ai_analysis["results"], structure["name"], field["name"]),
                    relationships=self._get_ai_relationships(ai_analysis["results"], structure["name"], field["name"]),
                    source="code_analysis",
                    version="1.0"
                )
                data_dictionaries.append(dd)
                self.db.add(dd)  # Add each entry to the database session
        
        # Also process tables from AI analysis that weren't found in code structure
        for table in ai_analysis["results"]["tables"]:
            table_name = table["name"]
            # Skip if we already processed this table from code structure
            if not any(dd.table_name == table_name for dd in data_dictionaries):
                for field in table["fields"]:
                    dd = DataDictionary(
                        analysis_id=analysis_id,
                        table_name=table_name,
                        column_name=field["name"],
                        data_type=field["type"],
                        description=field.get("description"),
                        valid_values=self._get_ai_valid_values(ai_analysis["results"], table_name, field["name"]),
                        relationships=self._get_ai_relationships(ai_analysis["results"], table_name, field["name"]),
                        source="llm_analysis",
                        version="1.0"
                    )
                    data_dictionaries.append(dd)
                    self.db.add(dd)  # Add each entry to the database session
        
        try:
            self.db.commit()  # Commit all entries to the database
        except Exception as e:
            self.db.rollback()
            print(f"Error saving data dictionary entries: {str(e)}")
            raise
        
        return data_dictionaries
    
    def _get_ai_description(self, ai_analysis: Dict, table: str, column: str) -> Optional[str]:
        """
        Get AI-generated description for a field
        """
        try:
            # Look for field description in tables
            for table_info in ai_analysis.get("tables", []):
                if table_info["name"] == table:
                    for field in table_info.get("fields", []):
                        if field["name"] == column:
                            return field.get("description")
            return None
        except Exception as e:
            print(f"Error getting AI description: {str(e)}")
            return None
    
    def _get_ai_valid_values(self, ai_analysis: Dict, table: str, column: str) -> Optional[Dict]:
        """
        Get AI-suggested valid values for a field
        """
        try:
            # Look for valid values in tables and code snippets
            valid_values = {
                "constraints": [],
                "examples": [],
                "data_type_specific": {}
            }
            
            # Check tables for type information
            for table_info in ai_analysis.get("tables", []):
                if table_info["name"] == table:
                    for field in table_info.get("fields", []):
                        if field["name"] == column:
                            field_type = field.get("type", "").lower()
                            # Add type-specific constraints
                            if "int" in field_type or "float" in field_type or "decimal" in field_type:
                                valid_values["data_type_specific"]["numeric"] = True
                            elif "date" in field_type or "time" in field_type:
                                valid_values["data_type_specific"]["temporal"] = True
                            elif "bool" in field_type:
                                valid_values["data_type_specific"]["boolean"] = True
                                valid_values["constraints"].append("Values must be true/false")
                            
                            # Add any explicit constraints from description
                            if field.get("description"):
                                if "must be" in field["description"].lower():
                                    valid_values["constraints"].append(field["description"])
            
            return valid_values if valid_values["constraints"] or valid_values["data_type_specific"] else None
        except Exception as e:
            print(f"Error getting valid values: {str(e)}")
            return None
    
    def _get_ai_relationships(self, ai_analysis: Dict, table: str, column: str) -> Optional[Dict]:
        """Get relationships from AI analysis for a specific table and column"""
        if not ai_analysis or "relationships" not in ai_analysis:
            return None
        
        relationships = []
        for rel in ai_analysis["relationships"]:
            if rel["from_table"] == table and rel["from_field"] == column:
                relationships.append({
                    "type": rel["type"],
                    "target_table": rel["to_table"],
                    "target_field": rel["to_field"]
                })
            elif rel["to_table"] == table and rel["to_field"] == column:
                relationships.append({
                    "type": rel["type"],
                    "source_table": rel["from_table"],
                    "source_field": rel["from_field"]
                })
        
        return {"relationships": relationships} if relationships else None

    async def store_code_chunks(self, analysis_id: int, code: str) -> None:
        """
        Store code chunks in the database
        """
        try:
            # Parse the code into AST
            tree = ast.parse(code)
            
            # Extract classes and functions
            for node in ast.walk(tree):
                if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
                    # Get the code lines for this node
                    start_line = node.lineno
                    end_line = node.end_lineno
                    lines = code.split('\n')[start_line-1:end_line]
                    chunk_code = '\n'.join(lines)
                    
                    # Create code snippet
                    code_snippet = CodeSnippet(
                        analysis_id=analysis_id,
                        code=chunk_code,
                        language="python",
                        purpose=f"{'Class' if isinstance(node, ast.ClassDef) else 'Function'} definition: {node.name}",
                        dependencies=self._extract_dependencies(node)
                    )
                    self.db.add(code_snippet)
            
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            print(f"Error storing code chunks: {str(e)}")

    def _extract_dependencies(self, node: ast.AST) -> Dict:
        """
        Extract dependencies from an AST node
        """
        dependencies = {
            "imports": [],
            "calls": [],
            "attributes": []
        }
        
        for child in ast.walk(node):
            if isinstance(child, ast.Import):
                dependencies["imports"].extend(n.name for n in child.names)
            elif isinstance(child, ast.ImportFrom):
                dependencies["imports"].append(f"{child.module}.{child.names[0].name}")
            elif isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    dependencies["calls"].append(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    dependencies["attributes"].append(f"{child.func.value.id}.{child.func.attr}")
        
        return dependencies

    async def analyze_sql_with_llm(self, sql_code: str) -> Dict:
        """Analyze SQL code using LLM to extract schema information"""
        try:
            # First try to parse using SQL parser
            analysis_result = self.parse_sql(sql_code)
            if analysis_result["tables"]:
                return {
                    "result": {
                        **analysis_result,
                        "model_used": "SQL Parser",
                        "documentation_summary": "SQL schema analysis"
                    }
                }

            # If SQL parsing fails or finds no tables, try OpenAI
            try:
                response = await self.ai.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a SQL expert. Extract schema information from SQL code."},
                        {"role": "user", "content": f"""Analyze this SQL code and extract table and column information.
                        Return the response in the following JSON format:
                        {{
                            "tables": [
                                {{
                                    "name": "table_name",
                                    "fields": [
                                        {{
                                            "name": "field_name",
                                            "type": "field_type",
                                            "description": "field_description",
                                            "constraints": ["list_of_constraints"]
                                        }}
                                    ],
                                    "relationships": [
                                        {{
                                            "type": "foreign_key",
                                            "from_table": "source_table",
                                            "from_fields": ["source_fields"],
                                            "to_table": "target_table",
                                            "to_fields": ["target_fields"]
                                        }}
                                    ]
                                }}
                            ],
                            "type": "sql_analysis"
                        }}

                        Here's the SQL code to analyze:

                        {sql_code}"""}
                    ]
                )
                analysis_result = self._parse_ai_response(response.choices[0].message.content)
                return {
                    "result": {
                        **analysis_result,
                        "model_used": "OpenAI GPT-3.5 Turbo",
                        "documentation_summary": "SQL schema analysis"
                    }
                }
            except Exception as openai_error:
                print(f"OpenAI analysis failed: {str(openai_error)}, trying Gemini...")
                # Try Gemini as fallback
                try:
                    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
                    model = genai.GenerativeModel('gemini-1.5-pro')
                    response = model.generate_content(
                        f"""You are a SQL expert. Analyze this SQL code and extract table and column information.
                        Return the response in the following JSON format:
                        {{
                            "tables": [
                                {{
                                    "name": "table_name",
                                    "fields": [
                                        {{
                                            "name": "field_name",
                                            "type": "field_type",
                                            "description": "field_description",
                                            "constraints": ["list_of_constraints"]
                                        }}
                                    ],
                                    "relationships": [
                                        {{
                                            "type": "foreign_key",
                                            "from_table": "source_table",
                                            "from_fields": ["source_fields"],
                                            "to_table": "target_table",
                                            "to_fields": ["target_fields"]
                                        }}
                                    ]
                                }}
                            ],
                            "type": "sql_analysis"
                        }}

                        Here's the SQL code to analyze:

                        {sql_code}"""
                    )
                    analysis_result = self._parse_ai_response(response.text)
                    return {
                        "result": {
                            **analysis_result,
                            "model_used": "Google Gemini",
                            "documentation_summary": "SQL schema analysis"
                        }
                    }
                except Exception as gemini_error:
                    print(f"Gemini analysis failed: {str(gemini_error)}")
                    raise
        except Exception as e:
            print(f"Error analyzing SQL code: {str(e)}")
            return {
                "result": {
                    "tables": [],
                    "type": "sql_analysis",
                    "model_used": "Failed",
                    "documentation_summary": f"Error analyzing SQL code: {str(e)}"
                }
            }

    def extract_code_info(self, code: str) -> dict:
        """Extract basic information from code using AST."""
        try:
            tree = ast.parse(code)
            imports = []
            functions = []
            classes = []
            variables = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.extend(n.name for n in node.names)
                elif isinstance(node, ast.ImportFrom):
                    imports.append(f"{node.module}.{node.names[0].name}")
                elif isinstance(node, ast.FunctionDef):
                    functions.append(node.name)
                elif isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            variables.append(target.id)
            
            return {
                "imports": imports,
                "functions": functions,
                "classes": classes,
                "variables": variables
            }
        except Exception as e:
            return {"error": f"Failed to parse code: {str(e)}"}
    
    async def analyze_with_openai(self, code: str, code_info: dict) -> dict:
        """Analyze code using OpenAI's GPT model."""
        if not self.ai:
            raise ValueError("OpenAI client not configured")

        system_prompt = """You are an expert code analyst specializing in data dictionary creation and code analysis. 
        Analyze the provided code and extract the following information in JSON format:
        1. Tables and their structures (even if implied from code)
        2. Data relationships and dependencies
        3. Important code snippets with explanations
        4. Data sources and their descriptions
        5. Data transformations and cleaning steps
        6. Potential reuse opportunities
        7. Documentation summary"""

        context = f"""Code Analysis Context:
        - Imports: {', '.join(code_info['imports'])}
        - Functions: {', '.join(code_info['functions'])}
        - Classes: {', '.join(code_info['classes'])}
        
        Code to analyze:
        {code}
        """

        try:
            print("Attempting OpenAI API analysis...")
            response = self.ai.chat.completions.create(
                model="gpt-3.5-turbo-16k",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": context}
                ],
                temperature=0.7,
                max_tokens=4000
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"OpenAI API Error: {str(e)}")
            raise

    async def analyze_with_gemini(self, code: str, code_info: dict) -> dict:
        """Analyze code using Google's Gemini model."""
        if not self.google_api_key:
            raise ValueError("Gemini API key not configured")

        prompt = f"""As an expert code analyst, analyze this code and provide information in JSON format about:
        1. Tables and their structures (even if implied from code)
        2. Data relationships and dependencies
        3. Important code snippets with explanations
        4. Data sources and their descriptions
        5. Data transformations and cleaning steps
        6. Potential reuse opportunities
        7. Documentation summary

        Code Analysis Context:
        - Imports: {', '.join(code_info['imports'])}
        - Functions: {', '.join(code_info['functions'])}
        - Classes: {', '.join(code_info['classes'])}
        
        Code to analyze:
        {code}

        IMPORTANT: Return ONLY the JSON object without any markdown formatting or code blocks.
        """

        try:
            print("Attempting Gemini API analysis...")
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            generation_config = {
                "temperature": 0.3,
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 4000,
            }
            
            response = model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            if not response.text:
                raise ValueError("Empty response from Gemini API")
                
            # Clean up the response text
            response_text = response.text
            # Remove markdown code block if present
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            response_text = response_text.strip()
            
            print("Raw response:", response_text)
                
            try:
                # Try to parse the response as JSON
                result = json.loads(response_text)
                return result
            except json.JSONDecodeError as je:
                print(f"Failed to parse Gemini response as JSON: {str(je)}")
                print(f"Raw response: {response_text}")
                raise ValueError(f"Invalid JSON response from Gemini API: {str(je)}")
                
        except Exception as e:
            print(f"Gemini API Error: {str(e)}")
            raise

    async def analyze_code_with_llm(self, code: str) -> dict:
        """Analyze code using available LLM services with fallback."""
        code_info = self.extract_code_info(code)
        errors = []

        # Try OpenAI first if configured
        if self.ai:
            try:
                return await self.analyze_with_openai(code, code_info)
            except Exception as e:
                error_msg = str(e)
                print(f"OpenAI analysis failed: {error_msg}")
                errors.append(f"OpenAI Error: {error_msg}")

        # Try Gemini as fallback
        if self.google_api_key:
            try:
                return await self.analyze_with_gemini(code, code_info)
            except Exception as e:
                error_msg = str(e)
                print(f"Gemini analysis failed: {error_msg}")
                errors.append(f"Gemini Error: {error_msg}")

        # If both failed, raise error with details
        raise HTTPException(
            status_code=500,
            detail=f"LLM analysis failed with both services: {'; '.join(errors)}"
        ) 