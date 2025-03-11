import ast
import re
from typing import Dict, List, Optional
from openai import OpenAI
from sqlalchemy.orm import Session

from ...models.base import Analysis, DataDictionary, CodeSnippet

class AnalysisService:
    def __init__(self, db_session: Session, openai_client: OpenAI):
        self.db = db_session
        self.ai = openai_client
        
    async def analyze_code(self, code: str) -> Dict:
        """
        Analyze code using OpenAI to extract data dictionary information
        """
        try:
            response = await self.ai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a code analysis expert. Extract data-related information from the code."},
                    {"role": "user", "content": f"Analyze this code and extract information about data structures, types, and relationships:\n\n{code}"}
                ]
            )
            
            return self._parse_ai_response(response.choices[0].message.content)
        except Exception as e:
            raise Exception(f"Error analyzing code: {str(e)}")
    
    def _parse_ai_response(self, response: str) -> Dict:
        """
        Parse the AI response into structured data dictionary information
        """
        # This is a placeholder for the actual parsing logic
        # You would implement more sophisticated parsing here
        return {
            "tables": [],
            "columns": [],
            "relationships": [],
            "data_types": []
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