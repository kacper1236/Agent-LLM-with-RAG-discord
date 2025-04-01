import os
from langchain.globals import set_llm_cache
from langchain_community.cache import SQLiteCache
from langchain_ollama import ChatOllama
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate

LLM_MODEL = os.getenv('LLM_MODEL', 'mistral')

set_llm_cache(SQLiteCache(database_path=".langchain.db"))
llm = ChatOllama(model=LLM_MODEL, 
                 temperature=0, 
                 cache=False,
                 format="json", #jak się okaże że to to, to wyskakuje przez okno
                 )

def clean_json_string(text: str) -> str:
    # Remove markdown code block markers and trim whitespace
    text = text.replace("```markdown", "").replace("```json", "").replace("```", "").strip()
    # Remove "json" prefix if present
    text = text.replace("json\n", "").strip()
    return text

def llmGetTags(text: str):
    prompt = PromptTemplate(
        input_variables=["document"],
        template="""
            You are a JSON generator. Return ONLY a JSON array (no markdown, no extra text) containing objects with this EXACT structure:
            {{
                "chunk": number | null,
                "chapter": number | null,
                "tags": string[],
                "isSummary": boolean
            }}
            You must always return valid JSON fenced by a markdown code block. Do not return any additional text.
            Follow this rules:
            1. Every object MUST have ALL fields
            2. NO trailing commas
            3. The response must be valid JSON
            4. The "isSummary" field must always be included and be boolean
            5. If chunks/chapters don't exist, use null for those fields
            
            TEXT TO ANALYZE:
            {document}
        """
    )

    chain = (
        prompt
        | llm
        | (lambda x: clean_json_string(x.content))  # Clean the string before parsing
        | JsonOutputParser()
    )

    response = chain.invoke({
        "document": text,
    })
    
    return response
