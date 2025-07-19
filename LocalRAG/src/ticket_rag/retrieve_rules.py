import os

from ..utils.llm import LLMProvider
from ..config import MODEL_EMBEDDINGS, MODEL
from ..utils.advanced_chroma import QueryExpansionChromaDB, RerankingChromaDB, CachedChromaDB
import chromadb
from chromadb.config import Settings
from ..utils.advanced_chroma import ChromaDBEmbeddingWrapper

def retrieveContext(serverId: str, text: str, namespace: str):
    try:
        # Initialize advanced RAG components
        query_expansion_db = QueryExpansionChromaDB(namespace, MODEL_EMBEDDINGS)
        reranking_db = RerankingChromaDB(namespace, MODEL_EMBEDDINGS)
        cached_db = CachedChromaDB(namespace, MODEL_EMBEDDINGS)
        
        # Check cache first
        is_cached, cached_response, similarity = cached_db.check_similarity_cache(text)
        if is_cached:
            print(f"Using cached response (similarity: {similarity:.3f})")
            return cached_response
        
        # Expand query for better search results
        expanded_queries = query_expansion_db.expand_query(text, quick_mode=True)
        
        # Initialize ChromaDB client for basic search
        client = chromadb.PersistentClient(
            path=f'chroma/{MODEL + '__' + MODEL_EMBEDDINGS}/dynamic-chunking',
            settings=Settings(
                persist_directory=f'chroma/{MODEL + '__' + MODEL_EMBEDDINGS}/dynamic-chunking',
                anonymized_telemetry=False,
            )
        )
        
        # Get embedding model
        embedding_model, _ = LLMProvider.getLLM(MODEL_EMBEDDINGS)
        wrapped_embedding_function = ChromaDBEmbeddingWrapper(embedding_model)
        
        collection = client.get_or_create_collection(
            name=namespace,
            embedding_function=wrapped_embedding_function
        )
        
        # Search for results using expanded queries
        all_results = []
        for query in expanded_queries:
            try:
                results = collection.query(
                    query_texts=[query],
                    n_results=3,
                    where={"namespace": serverId} if serverId else None
                )
                
                if results and results['documents'] and results['documents'][0]:
                    for doc in results['documents'][0]:
                        all_results.append({'text': doc, 'user_score': 0})
                        
            except Exception as e:
                print(f"Error searching for query '{query}': {e}")
                continue
        
        # Also search for general Discord guidelines
        try:
            guidelines_results = collection.query(
                query_texts=["Guidelines for community servers"],
                n_results=2
            )
            
            if guidelines_results and guidelines_results['documents'] and guidelines_results['documents'][0]:
                for doc in guidelines_results['documents'][0]:
                    all_results.append({'text': doc, 'user_score': 0})
                    
        except Exception as e:
            print(f"Error searching for guidelines: {e}")
        
        # Rerank results for better relevance
        if all_results:
            reranked_results = reranking_db.rerank_results(text, all_results, top_k=5)
            final_context = "\n".join(reranked_results)
        else:
            final_context = "No relevant context found."
        
        # Store in cache for future use
        if final_context and final_context != "No relevant context found.":
            cached_db.store_search_query_and_response(text, final_context)
        
        return final_context
        
    except Exception as e:
        print(f"Error in retrieveContext: {e}")
        return "Error retrieving context."

# idc czy działa 
# 1 regulamin i wytyczne dla społeczności
