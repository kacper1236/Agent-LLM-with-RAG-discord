import os
import uuid
from ..config import MODEL_EMBEDDINGS
from ..utils.advanced_chroma import DynamicChunkingChromaDB


CHROMA_PATH = os.getenv('CHROMA_PATH', 'chroma')

def saveToDatabase(text: str, namespace: str):
    try:
        # Use DynamicChunkingChromaDB for better chunking
        chunking_db = DynamicChunkingChromaDB(namespace, MODEL_EMBEDDINGS)
        
        # Create document with metadata
        document = {
            'id': str(uuid.uuid4()),
            'text': text,
            'metadata': {
                'title': 'RULES',
                'namespace': namespace,
                'timestamp': str(uuid.uuid4())
            }
        }
        
        # Add document with dynamic chunking
        chunking_db.add_documents_with_chunking([document])
        
        return True
    except Exception as e:
        print(f"Error in saveToDatabase: {e}")
        return False