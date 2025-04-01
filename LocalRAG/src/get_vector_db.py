import os
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from sympy.physics.units import ampere
from .utils.advanced_chroma import (
    RerankingChromaDB,
    QueryExpansionChromaDB,
    DynamicChunkingChromaDB,
    ChainOfThoughtChromaDB,
    FeedbackChromaDB,
    CachedChromaDB
)

CHROMA_PATH = os.getenv('CHROMA_PATH', 'chroma')
CHROMA_PATH2 = os.getenv('CHROMA_PATH', 'chroma')

allowedEmbeddingsModels = ['nomic-embed-text', 'snowflake-arctic-embed']
allowedModels = ['mistral', 'llama3.1:8b']
embeddingSizes = [1024, 768, 1024]

def get_vector_db(embedding_model, collection_name):
    embedding = OllamaEmbeddings(model=embedding_model)
    print("USING MODEL", embedding_model, collection_name)

    db = Chroma(
        collection_name=collection_name,
        persist_directory=CHROMA_PATH,
        embedding_function=embedding,
    )

    return db

def get_advanced_vector_db(collection_name, embedding_model):
    """Returns a dictionary of advanced ChromaDB instances with different functionalities"""
    return {
        'reranking': RerankingChromaDB(collection_name, embedding_model),
        'expansion': QueryExpansionChromaDB(collection_name, embedding_model),
        'chunking': DynamicChunkingChromaDB(collection_name, embedding_model),
        'cot': ChainOfThoughtChromaDB(collection_name, embedding_model),
        'feedback': FeedbackChromaDB(collection_name, embedding_model),
        'cached': CachedChromaDB(collection_name, embedding_model)
    }
