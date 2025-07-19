import os, re
from langchain_community.document_loaders import PlaywrightURLLoader

from ..utils.llm import LLMProvider
from ..config import MODEL, MODEL_EMBEDDINGS
from ..utils.advanced_chroma import ChromaDBEmbeddingWrapper
from llama_index.core.chat_engine.types import ChatMessage
import chromadb
from chromadb.config import Settings

# Get LLM and embedding models from LLMProvider
llm, _ = LLMProvider.getLLM(MODEL)
embedding_model, _ = LLMProvider.getLLM(MODEL_EMBEDDINGS)

# Create wrapped embedding function for ChromaDB
wrapped_embedding_function = ChromaDBEmbeddingWrapper(embedding_model)

# Initialize ChromaDB client
client = chromadb.PersistentClient(
    path=f'chroma/{MODEL + '__' + MODEL_EMBEDDINGS}/discord_rules',
    settings=Settings(
        persist_directory=f'chroma/{MODEL + '__' + MODEL_EMBEDDINGS}/discord_rules',
        anonymized_telemetry=False,
    )
)

db = client.get_or_create_collection(
    name="llm_discordRules",
    embedding_function=wrapped_embedding_function
)

def getDiscordRules():
    try:
        results = db.get(where={'type': 'modifiedAt'})
        if results and results['documents']:
            return results['documents'][0]
        else:
            return ingestDiscordRules()
    except:
        return ingestDiscordRules()

def ingestDiscordRules():
    
    urls = ["https://discord.com/guidelines"]

    loader = PlaywrightURLLoader(urls=urls, headless=True, remove_selectors=['.link-terms', '.link-terms > *', '.menu-numbers', '[data-animation="over-right"]', 'div.dropdown-language-name', '#onetrust-policy-text > *', '#onetrust-consent-sdk > *', '#locale-dropdown > *', '#locale-dropdown', '.locale-container', 'iframe', 'script', '* > .language', 'div.language', '.language > *', '.archived-link', '.footer-black > *', '.link-terms', '#localize-widget', '#localize-widget > *'])

    data = loader.load()

    d = data[0].page_content.split('\n\n')

    newModifiedAt = ""

    for i in d:
        if i.startswith("Last Updated:"):
            newModifiedAt = i.replace("Last Updated: ", "")
            break

    try:
        results = db.get(where={'type': 'modifiedAt'})
        if results and results['metadatas'] and results['metadatas'][0].get('modifiedAt') == newModifiedAt:
            return results['documents'][0]
    except:
        pass
    
    # Reset collection
    try:
        client.delete_collection("llm_discordRules")
        db = client.create_collection(
            name="llm_discordRules",
            embedding_function=wrapped_embedding_function
        )
    except:
        pass

    expPoint = r"\d+\. "
    expNawias = r"(.*)(\([^\)]+\))$"

    points = []
    started = False
    for line in d:
        if len(line) == 0: continue
        du = re.match(expPoint, line)
        if line[0] == 'б': break
        if line == 'Follow the Law': continue
        if line == 'Respect Discord': continue
        if line == 'Respect Each Other': continue
        if line.startswith('For more information '): continue
        if du is not None:
            if (started == True):
                ma = re.match(expNawias, points[len(points)-1], re.MULTILINE)
                if ma is not None:
                    points[len(points)-1] = points[len(points)-1].replace(ma.group(2), '')
                points[len(points)-1] = points[len(points)-1].strip()

            started = True
            points.append(line + '\n')
        else:
            if started == True:
                if (line.startswith("If you see any")):
                    ma = re.match(expNawias, points[len(points) - 1], re.MULTILINE)
                    if ma is not None:
                        points[len(points) - 1] = points[len(points) - 1].replace(ma.group(2), '')
                    points[len(points) - 1] = points[len(points) - 1].strip()

                    break
                points[len(points)-1] = points[len(points)-1].strip() + line + '\n'
    i = 0
    for point in points:
        points[i] = point.strip();
        i = i +1

    content = '\n\n'.join(point for point in points)

    # Add to ChromaDB
    import uuid
    db.add(
        documents=[content],
        metadatas=[{'type': 'modifiedAt', "modifiedAt": newModifiedAt}],
        ids=[str(uuid.uuid4())]
    )

    return content

def analyzeRules(rules: str):
    prompt_system = """
    You are master rules.
    Your job is to understand the rules in order to be a helpful person or group of people.
    Don't add any points to rules. Act only within the given rules.

    Provide a structured understanding of these rules.
    """
    
    prompt_user = f"Here is your rules:\n{rules}"
    
    try:
        response = llm.chat(messages=[
            ChatMessage(role="system", content=prompt_system),
            ChatMessage(role="user", content=prompt_user)
        ])
        return response.message.content
    except Exception as e:
        print(f"Error in analyzeRules: {e}")
        return "Error analyzing rules"
