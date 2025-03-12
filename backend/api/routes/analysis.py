from fastapi import APIRouter, UploadFile, Form, HTTPException, Depends
from typing import Optional
import openai
from sqlalchemy.orm import Session
from core.database import get_db
import os
from dotenv import load_dotenv
import json

load_dotenv()

router = APIRouter()

# Configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

def analyze_code_with_llm(code: str) -> dict:
    """Analyze code using OpenAI's GPT model."""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a code analysis expert. Analyze the provided code and extract information about database tables, relationships, and important code snippets. Format your response as JSON with the following structure: {tables: [{name: string, fields: [{name: string, type: string, description: string}]}], relationships: [{from_table: string, to_table: string, type: string}], code_snippets: [{file: string, line: number, code: string, description: string}]}"},
                {"role": "user", "content": f"Analyze this code:\n\n{code}"}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        # Parse the response
        analysis = json.loads(response.choices[0].message.content)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Analysis failed: {str(e)}")

@router.post("/analyze")
async def analyze_code(
    file: Optional[UploadFile] = None,
    code: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    try:
        if file:
            content = await file.read()
            code_to_analyze = content.decode()
        elif code:
            code_to_analyze = code
        else:
            raise HTTPException(status_code=400, detail="No code provided")

        # Perform LLM analysis
        analysis_result = analyze_code_with_llm(code_to_analyze)
        
        return analysis_result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))