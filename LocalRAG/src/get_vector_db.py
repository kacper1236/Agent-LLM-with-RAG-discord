import os
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from .utils.advanced_chroma import (
    RerankingChromaDB,
    QueryExpansionChromaDB,
    DynamicChunkingChromaDB,
    ChainOfThoughtChromaDB,
    FeedbackChromaDB,
    CachedChromaDB
)
from .utils.llm import LLMProvider
from .config import MODEL, MODEL_EMBEDDINGS

allowedEmbeddingsModels = LLMProvider.list_ollama_models() + LLMProvider.list_openai_models()
allowedModels = LLMProvider.list_ollama_models() + LLMProvider.list_openai_models()
embeddingSizes = [1024, 768, 1024]

def auto_embed_default_pdf(db, embedding_model, collection_name):
    """
    Sprawdza czy baza danych jest pusta i jeśli tak, automatycznie embedduje licencjat.pdf
    """
    try:
        # Sprawdź czy baza danych jest pusta
        results = db.get()
        if results and results.get('ids') and len(results['ids']) > 0:
            print(f"Baza danych {collection_name} już zawiera {len(results['ids'])} dokumentów")
            return
        
        # Sprawdź czy plik licencjat.pdf istnieje
        pdf_path = 'licencjat.pdf'
        if not os.path.exists(pdf_path):
            print(f"Plik {pdf_path} nie został znaleziony w katalogu głównym")
            return
        
        print(f"Baza danych {collection_name} jest pusta. Automatyczne embeddowanie {pdf_path}...")
        
        # Załaduj i podziel PDF
        loader = PyPDFLoader(file_path=pdf_path)
        data = loader.load()
        print(f"Załadowano {len(data)} stron z {pdf_path}")
        
        # Podziel tekst na chunki
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=4096, chunk_overlap=256)
        chunks = text_splitter.split_documents(data)
        print(f"Podzielono na {len(chunks)} chunków")
        
        # Dodaj chunki do bazy danych
        # Aktualizuj metadane każdego chunku
        for chunk in chunks:
            chunk.metadata.update({
                "type": "documents", 
                "file": "licencjat.pdf",
                "source": "auto_embedded"
            })
        
        db.add_documents(chunks)
        
        print(f"Automatycznie zaembeddowano {len(chunks)} chunków z {pdf_path}")
        
    except Exception as e:
        print(f"Błąd podczas automatycznego embeddowania {pdf_path}: {e}")

def get_vector_db(embedding_model, collection_name):
    # Get embedding model from LLMProvider
    embedding, _ = LLMProvider.getLLM(embedding_model)
    print("USING MODEL", embedding_model, collection_name)

    db = Chroma(
        collection_name=collection_name,
        persist_directory=f'chroma/{MODEL + '__' + MODEL_EMBEDDINGS}/documents',
        embedding_function=embedding,
    )

    # Sprawdź czy baza danych jest pusta i zaembedduj licencjat.pdf jeśli trzeba
    auto_embed_default_pdf(db, embedding_model, collection_name)

    return db

def get_advanced_vector_db(collection_name, embedding_model):
    """Returns a dictionary of advanced ChromaDB instances with different functionalities, using LLMProvider for embeddings."""
    # Pass the embedding model name, so each advanced DB uses LLMProvider
    return {
        'reranking': RerankingChromaDB(collection_name, embedding_model),
        'expansion': QueryExpansionChromaDB(collection_name, embedding_model),
        'chunking': DynamicChunkingChromaDB(collection_name, embedding_model),
        'cot': ChainOfThoughtChromaDB(collection_name, embedding_model),
        'feedback': FeedbackChromaDB(collection_name, embedding_model),
        'cached': CachedChromaDB(collection_name, embedding_model)
    }

def getDatabases(model, namespace):
    if (model is None): model = 'nomic-embed-text'

    db = get_vector_db(model, f'str_{namespace}')

    return db
