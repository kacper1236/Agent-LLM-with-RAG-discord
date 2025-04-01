import os

from langchain.docstore.document import Document
from langchain.text_splitter import CharacterTextSplitter

from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings, ChatOllama

from langchain_community.cache import SQLiteCache
from langchain_core.globals import set_llm_cache

CHROMA_PATH = os.getenv('CHROMA_PATH', 'chroma')
LLM_MODEL = os.getenv('LLM_MODEL', 'mistral')
set_llm_cache(SQLiteCache(database_path='.langchain.db'))
llm = ChatOllama(model = LLM_MODEL, temperature = 0.3, cache = False)

def saveToDatabase(text: str, namespace:str):
    try:
        splitter = CharacterTextSplitter(chunk_size = 500, chunk_overlap = 100) #wymaga koniecznej wymiany na inne parametry
        docs = [Document(page_content = x, metadata = {'title': 'RULES'}) for x in splitter.split_text(text)] #dodać metadata
        
        embedding = OllamaEmbeddings(model=LLM_MODEL)

        db = Chroma(
            collection_name=namespace,
            persist_directory=CHROMA_PATH,
            embedding_function=embedding,
        )

        db.add_documents(docs)
        
        return True
    except: return False