import ast
import re
from typing import Dict, List, Optional
from openai import OpenAI
from sqlalchemy.orm import Session
from datetime import datetime, time

from ...models.base import Analysis, DataDictionary, CodeSnippet, QueryExecution

class AnalysisService:
    def __init__(self, db_session: Session, openai_client: OpenAI):
        self.db = db_session
        self.ai = openai_client
        
    async def analyze_code(self, code: str, analysis_id: Optional[int] = None, user_id: Optional[int] = None) -> Dict:
        """
        Analyze code using OpenAI to extract data dictionary information and optionally store results
        """
        start_time = datetime.utcnow()
        execution_status = "success"
        error_message = None
        
        try:
            response = await self.ai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a code analysis expert. Extract data-related information from the code."},
                    {"role": "user", "content": f"Analyze this code and extract information about data structures, types, and relationships:\n\n{code}"}
                ]
            )
            
            analysis_result = self._parse_ai_response(response.choices[0].message.content)
            
            # If analysis_id is provided, store the results
            if analysis_id:
                await self.store_analysis_results(analysis_id, analysis_result)
            
            return analysis_result
        except Exception as e:
            execution_status = "failed"
            error_message = str(e)
            raise Exception(f"Error analyzing code: {str(e)}")
        finally:
            if analysis_id and user_id:
                end_time = datetime.utcnow()
                duration = int((end_time - start_time).total_seconds() * 1000)  # Convert to milliseconds
                
                # Record query execution
                query_execution = QueryExecution(
                    user_id=user_id,
                    analysis_id=analysis_id,
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
            # Parse the response into a structured format
            analysis_data = {
                "tables": [],
                "relationships": [],
                "code_snippets": [],
                "data_sources": [],
                "data_transformations": [],
                "potential_reuse_opportunities": [],
                "documentation_summary": ""
            }
            
            # Add actual parsing logic here based on the AI response format
            # This is a placeholder - implement proper parsing based on your AI model's output
            
            return analysis_data
        except Exception as e:
            raise Exception(f"Error parsing AI response: {str(e)}")
    
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
                    description=self._get_ai_description(ai_analysis, structure["name"], field["name"]),
                    valid_values=self._get_ai_valid_values(ai_analysis, structure["name"], field["name"]),
                    relationships=self._get_ai_relationships(ai_analysis, structure["name"], field["name"]),
                    source="code_analysis",
                    version="1.0"
                )
                data_dictionaries.append(dd)
        
        return data_dictionaries
    
    def _get_ai_description(self, ai_analysis: Dict, table: str, column: str) -> Optional[str]:
        """
        Get AI-generated description for a field
        """
        # Implement logic to extract relevant description from AI analysis
        return None
    
    def _get_ai_valid_values(self, ai_analysis: Dict, table: str, column: str) -> Optional[Dict]:
        """
        Get AI-suggested valid values for a field
        """
        # Implement logic to extract valid values from AI analysis
        return None
    
    def _get_ai_relationships(self, ai_analysis: Dict, table: str, column: str) -> Optional[Dict]:
        """
        Get AI-detected relationships for a field
        """
        # Implement logic to extract relationships from AI analysis
        return None 