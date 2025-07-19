import json, re

from .llm import LLMProvider
from ..config import MODEL
from llama_index.core.chat_engine.types import ChatMessage

# Get LLM from LLMProvider
llm, _ = LLMProvider.getLLM(MODEL)

def clean_json_string(text: str):
    # Usuń prefiksy Markdown / formatowania
    for prefix in ["```markdown", "```json", "```", "json\n"]:
        text = text.replace(prefix, "")
    
    text = text.strip()

    # Zamień zapisane znaki specjalne (\n, \") na prawdziwe znaki
    decoded_text = bytes(text, "utf-8").decode("unicode_escape")
    
    decoded_text = re.sub(r'(?<=[:\s])None(?=[,\s}])', '\"None\"', decoded_text)

    return decoded_text

def llmGetTags(text: str):
    prompt_system = """
    You are a JSON generator. Return ONLY a JSON array (no markdown, no extra text) containing objects with this EXACT structure:
    {
        "chunk": number | null,
        "chapter": number | null,
        "tags": string[],
        "isSummary": boolean
    }
    You must always return valid JSON fenced by a markdown code block. Do not return any additional text.
    Follow this rules:
    1. Every object MUST have ALL fields
    2. NO trailing commas
    3. The response must be valid JSON
    4. The "isSummary" field must always be included and be boolean
    5. If chunks/chapters don't exist, use null for those fields
    """
    
    prompt_user = f"TEXT TO ANALYZE:\n{text}"
    
    try:
        response = llm.chat(messages=[
            ChatMessage(role="system", content=prompt_system),
            ChatMessage(role="user", content=prompt_user)
        ])
        
        # Clean the string before parsing
        cleaned_response = clean_json_string(response.message.content)
        parsed_response = json.loads(cleaned_response)
        
        return parsed_response
        
    except Exception as e:
        print(f"Error in llmGetTags: {e}")
        # Return a default structure in case of error
        return [{
            "chunk": None,
            "chapter": None,
            "tags": [],
            "isSummary": False
        }]
