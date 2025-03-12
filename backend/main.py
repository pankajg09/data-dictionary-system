from fastapi import FastAPI, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict
from openai import OpenAI, OpenAIError
import google.generativeai as genai
import os
from dotenv import load_dotenv
import json
import ast
import re
import datetime

load_dotenv()

app = FastAPI(
    title="Data Dictionary System",
    description="A system for managing data dictionaries and code analysis",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002"
    ],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure OpenAI client
openai_api_key = os.getenv("OPENAI_API_KEY")
openai_client = None
if openai_api_key:
    try:
        openai_client = OpenAI(api_key=openai_api_key)
    except Exception as e:
        print(f"Failed to initialize OpenAI client: {str(e)}")

# Configure Gemini client
google_api_key = os.getenv("GOOGLE_API_KEY")
if google_api_key:
    try:
        genai.configure(api_key=google_api_key)
    except Exception as e:
        print(f"Failed to initialize Gemini client: {str(e)}")

def extract_code_info(code: str) -> dict:
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

async def analyze_with_openai(code: str, code_info: dict) -> dict:
    """Analyze code using OpenAI's GPT model."""
    if not openai_client:
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
        response = openai_client.chat.completions.create(
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

async def analyze_with_gemini(code: str, code_info: dict) -> dict:
    """Analyze code using Google's Gemini model."""
    if not google_api_key:
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

async def analyze_code_with_llm(code: str, code_info: dict) -> dict:
    """Analyze code using available LLM services with fallback."""
    errors = []

    # Try OpenAI first if configured
    if openai_client:
        try:
            return await analyze_with_openai(code, code_info)
        except Exception as e:
            error_msg = str(e)
            print(f"OpenAI analysis failed: {error_msg}")
            errors.append(f"OpenAI Error: {error_msg}")

    # Try Gemini as fallback
    if google_api_key:
        try:
            return await analyze_with_gemini(code, code_info)
        except Exception as e:
            error_msg = str(e)
            print(f"Gemini analysis failed: {error_msg}")
            errors.append(f"Gemini Error: {error_msg}")

    # If both failed, raise error with details
    raise HTTPException(
        status_code=500,
        detail=f"LLM analysis failed with both services: {'; '.join(errors)}"
    )

@app.post("/api/analysis/analyze")
async def analyze_code(
    file: Optional[UploadFile] = None,
    code: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None)
):
    try:
        if file:
            content = await file.read()
            code_to_analyze = content.decode()
        elif code:
            code_to_analyze = code
        else:
            raise HTTPException(status_code=400, detail="No code provided")

        # Check if any API key is configured
        if not openai_api_key and not google_api_key:
            raise HTTPException(
                status_code=500, 
                detail="No API keys configured. Please set either OPENAI_API_KEY or GOOGLE_API_KEY environment variable"
            )

        try:
            # Extract basic code information
            code_info = extract_code_info(code_to_analyze)
            if "error" in code_info:
                raise HTTPException(status_code=400, detail=code_info["error"])
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid code format: {str(e)}")
        
        try:
            # Perform LLM analysis with fallback
            analysis_result = await analyze_code_with_llm(code_to_analyze, code_info)
            
            # Add metadata
            analysis_result["metadata"] = {
                "title": title or "Untitled Analysis",
                "description": description or "No description provided",
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "version": "1.0",
                "status": "pending_review"
            }
            
            return analysis_result
            
        except HTTPException as he:
            raise he
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@app.get("/")
async def root():
    return {"message": "Welcome to Data Dictionary System API"} 