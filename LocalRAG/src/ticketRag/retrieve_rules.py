import os

from ..utils.get_databases import getDatabases

LLM_MODEL = os.getenv('LLM_MODEL', 'mistral')

allowedEmbeddingsModels = ['nomic-embed-text', 'mxbai-embed-large', 'snowflake-arctic-embed']
embeddingSizes = [1024, 768, 1024]

def retrieveContext(serverId: str, text: str, namespace: str):
    result_list = []
    chroma, _ = getDatabases(LLM_MODEL, namespace)
    results = chroma.similarity_search(text, k = 1, filter = serverId, namespace = namespace)
    result_list.append(results)
    results = chroma.similarity_search("Guidelines for community servers", k = 1)
    result_list.append(results)
    return "\n".join([doc.page_content for doc in result] for result in result_list)

# idc czy działa 
# 1 regulamin i wytyczne dla społeczności
