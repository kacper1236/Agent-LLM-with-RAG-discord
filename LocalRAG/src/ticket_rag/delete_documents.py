import os
import chromadb
from chromadb.config import Settings

from ..utils.llm import LLMProvider
from ..config import MODEL_EMBEDDINGS
from ..utils.advanced_chroma import ChromaDBEmbeddingWrapper

CHROMA_PATH = os.getenv('CHROMA_PATH', 'chroma')

def deleteDocuments(document_name: str, namespace: str):
    try:
        # Get embedding model
        embedding_model, _ = LLMProvider.getLLM(MODEL_EMBEDDINGS)
        wrapped_embedding_function = ChromaDBEmbeddingWrapper(embedding_model)
        
        # Initialize ChromaDB client
        client = chromadb.PersistentClient(
            path=f'{CHROMA_PATH}/dynamic-chunking',
            settings=Settings(
                persist_directory="dynamic-chunking",
                anonymized_telemetry=False,
            )
        )
        
        collection = client.get_or_create_collection(
            name=namespace,
            embedding_function=wrapped_embedding_function
        )
        
        # Get all documents in the collection
        results = collection.get()
        
        if not results or not results.get('ids') or not results.get('metadatas'):
            return False
        
        # Find documents to delete based on namespace
        doc_to_delete = [
            doc_id for doc_id, metadata in zip(results["ids"], results["metadatas"])
            if metadata and metadata.get("namespace") == document_name
        ]
        
        if doc_to_delete:
            collection.delete(ids=doc_to_delete)
            print(f"Deleted {len(doc_to_delete)} documents with namespace: {document_name}")
            return True
        
        print(f"No documents found with namespace: {document_name}")
        return False
        
    except Exception as e:
        print(f"Error in deleteDocuments: {e}")
        return False
