from .utils.advanced_chroma import (
    RerankingChromaDB,
    QueryExpansionChromaDB,
    DynamicChunkingChromaDB,
    ChainOfThoughtChromaDB,
    FeedbackChromaDB,
    CachedChromaDB
)

class AdvancedRAG:
    def __init__(self, collection_name: str, embedding_model: str):
        self.reranking_db = RerankingChromaDB(collection_name, embedding_model)
        self.query_expansion_db = QueryExpansionChromaDB(collection_name, embedding_model)
        self.dynamic_chunking_db = DynamicChunkingChromaDB(collection_name, embedding_model)
        self.chain_of_thought_db = ChainOfThoughtChromaDB(collection_name, embedding_model)
        self.feedback_db = FeedbackChromaDB(collection_name, embedding_model)

    def advanced_search(self, query: str):
        # Rozszerzanie zapytania
        expanded_queries = self.query_expansion_db.expand_query(query)
        
        # Wyszukiwanie wyników
        all_results = []
        for q in expanded_queries:
            results = self.dynamic_chunking_db.collection.query(query_texts=[q])['documents']
            ranked_results = self.reranking_db.rerank_results(q, results)
            all_results.extend(ranked_results)
        
        # Generowanie odpowiedzi z Chain of Thought
        final_response = self.chain_of_thought_db.generate_with_cot(query, all_results)
        
        return final_response

    def provide_feedback(self, feedback_data: dict):
        return self.feedback_db.store_feedback(feedback_data) 