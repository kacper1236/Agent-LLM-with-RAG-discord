import os

from ..utils.get_databases import getDatabases

CHROMA_PATH = os.getenv('CHROMA_PATH', 'chroma')
LLM_MODEL = os.getenv('LLM_MODEL', 'mistral')


def deleteDocuments(document_name: str, namespace: str):
    chroma, _ = getDatabases(LLM_MODEL, namespace)

    collection = chroma.get_collection(namespace)
    results = collection.get()

    doc_to_delete = [
        doc_id for doc_id, metadata in zip(results["ids"], results["metadatas"])
        if metadata and metadata.get("namespace") == document_name
    ]

    if doc_to_delete:
        collection.delete(id = doc_to_delete)
        return True
    
    return False

#NEED TO VERIFY