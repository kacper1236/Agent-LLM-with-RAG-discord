from chromadb.config import Settings
import numpy as np
import chromadb
from langchain_ollama import ChatOllama
import json
import uuid
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_ollama import OllamaEmbeddings

class OllamaEmbeddingFunctionWrapper:
    def __init__(self, model: str):
        self.embeddings = OllamaEmbeddings(model=model)
    
    def __call__(self, input: list[str]) -> list[list[float]]:
        return self.embeddings.embed_documents(input)

class RerankingChromaDB:
    def __init__(self, collection_name: str, embedding_model: str):
        self.ef = OllamaEmbeddingFunctionWrapper(embedding_model)
        self.client = chromadb.PersistentClient(
            path = 'chroma',
            settings = Settings(
                persist_directory="chroma",
                anonymized_telemetry=False,
        ))
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.ef
        )
        
    def rerank_results(self, query: str, results: list, top_k: int = 5):
        query_embedding = self.ef([query])[0]
        result_embeddings = self.ef([r['text'] for r in results])
        
        similarities = [
            np.dot(query_embedding, result_embedding) / 
            (np.linalg.norm(query_embedding) * np.linalg.norm(result_embedding))
            for result_embedding in result_embeddings
        ]
        
        ranked_results = list(zip(results, similarities))
        ranked_results.sort(key=lambda x: x[1], reverse=True)
        
        return [r[0] for r in ranked_results[:top_k]]

class QueryExpansionChromaDB:
    def __init__(self, collection_name: str, embedding_model: str):
        self.ef = OllamaEmbeddingFunctionWrapper(embedding_model)
        self.client = chromadb.PersistentClient(
            path = 'chroma',
            settings = Settings(
                persist_directory="chroma",
                anonymized_telemetry=False,
        ))
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.ef
        )
        self.llm = ChatOllama(model="llama3.1:8b")
        
    def expand_query(self, query: str):
        expanded_queries = [query]
        
        prompt = f"Generate 3 different ways to ask this question: {query}"
        variants = self.llm.invoke(prompt).content.split('\n')
        expanded_queries.extend(variants)
        
        all_results = []
        for q in expanded_queries:
            results = self.collection.query(
                query_texts=[q],
                n_results=3
            )
            all_results.extend(results['documents'][0])
            
        return list(set(all_results))

class DynamicChunkingChromaDB:
    def __init__(self, collection_name: str, embedding_model: str):
        self.ef = OllamaEmbeddingFunctionWrapper(embedding_model)
        self.client = chromadb.PersistentClient(
            path = 'chroma',
            settings = Settings(
                persist_directory="chroma",
                anonymized_telemetry=False,
        ))
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.ef
        )
        
    def dynamic_chunk(self, text: str, max_chunk_size: int = 512):
        sentences = text.split('.')
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence_size = len(sentence.split())
            
            if current_size + sentence_size > max_chunk_size:
                chunks.append(' '.join(current_chunk))
                current_chunk = [sentence]
                current_size = sentence_size
            else:
                current_chunk.append(sentence)
                current_size += sentence_size
                
        if current_chunk:
            chunks.append(' '.join(current_chunk))
            
        return chunks
        
    def add_documents_with_chunking(self, documents: list):
        for doc in documents:
            chunks = self.dynamic_chunk(doc['text'])
            
            for i, chunk in enumerate(chunks):
                self.collection.add(
                    documents=[chunk],
                    metadatas=[{
                        **doc['metadata'],
                        'chunk_index': i,
                        'total_chunks': len(chunks)
                    }],
                    ids=[f"{doc['id']}_{i}"]
                )

class ChainOfThoughtChromaDB:
    def __init__(self, collection_name: str, embedding_model: str):
        self.ef = OllamaEmbeddingFunctionWrapper(embedding_model)
        self.client = chromadb.PersistentClient(
            path = 'chroma',
            settings = Settings(
                persist_directory="chroma",
                anonymized_telemetry=False,
        ))
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.ef
        )
        self.llm = ChatOllama(model="llama3.1:8b")
        
    def generate_with_cot(self, query: str, reranked_results: list = None):
        if reranked_results == []:
            results = self.collection.query(
                query_texts=[query],
                n_results=3
            )
            reranked_results = results['documents'][0]
        
        thoughts = []
        for doc in reranked_results:
            thought_prompt = f"""
            Based on this context: {doc}
            Think step by step about how to answer: {query}
            """
            thought = self.llm.invoke(thought_prompt).content
            thoughts.append(thought)
            
        final_prompt = f"""
        Based on these thoughts:
        {thoughts}
        
        Provide a final answer to: {query}
        """
        
        return self.llm.invoke(final_prompt).content
    
class FeedbackChromaDB:
    def __init__(self, collection_name: str, embedding_model: str):
        self.ef = OllamaEmbeddingFunctionWrapper(embedding_model)
        self.client = chromadb.PersistentClient(
            path = 'chroma',
            settings = Settings(
                persist_directory="chroma",
                anonymized_telemetry=False,
        ))
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.ef
        )
        self.llm = ChatOllama(model = "llama3.1:8b",
                            temperature = 0,
                            cache = False,
                            format = 'json')
        
    def evaluate_response(self, query: str, response: str):
        """
        Automatycznie ocenia jakość odpowiedzi
        """
        try:
            prompt = PromptTemplate(
                input_variables=["query", "response"],
                template = """
                Oceń jakość tej odpowiedzi na pytanie użytkownika.
                
                Pytanie: {query}
                Odpowiedź: {response}
                
                Zwróć tylko liczby 1-5 dla każdej kategorii w następującym formacie bez dodatkowego tekstu, w formacie JSON:
                {{
                    "accuracy": [liczba], //to jest trafność
                    "completeness": [liczba], //to jest kompletność
                    "cohesion": [liczba], //to jest spójność
                    "comment": "krótkie uzasadnienie w jednej linii"
                }}
                """
            )

            from .llm_get_tags import clean_json_string

            chain = (
                prompt
                | self.llm
                | (lambda x: clean_json_string(x.content))
                | JsonOutputParser()
            )

            eval_results = chain.invoke({
                "query": query,
                "response": response
            })

            return eval_results

        except Exception as e:
            print(f"Error in evaluate_response: {e}")
            return {
                "accuracy": "1",
                "completeness": "1",
                "cohesion": "1",
                "comment": f"Błąd evaluacji: {str(e)}"
            }
        
    def store_feedback(self, feedback_data: dict):
        try:
            auto_evaluation = self.evaluate_response(
                query=feedback_data["query"],
                response=feedback_data["response"]
            )
            
            metadata = {
                "query": str(feedback_data["query"]),
                "response": str(feedback_data["response"]),
                "user_score": str(feedback_data["score"]),
                "feedback_text": str(feedback_data["feedback_text"]),
                "timestamp": str(feedback_data["timestamp"]),
                "auto_accuracy": str(auto_evaluation["accuracy"]),
                "auto_completeness": str(auto_evaluation["completeness"]),
                "auto_cohesion": str(auto_evaluation["cohesion"]),
                "auto_comment": str(auto_evaluation["comment"])
            }
            # Tworzymy embedding dla query - poprawiona wersja
            query_text = str(feedback_data["query"]).strip()
            query_embedding = self.ef([query_text])[0]
         
            self.collection.add(
                embeddings=[query_embedding],
                documents=[str(metadata["response"])],
                metadatas=[metadata],
                ids=[str(uuid.uuid4())]
            )
            return True
            
        except Exception as e:
            print(f"Error in store_feedback: {e}")
            return False

    def get_feedback_stats(self):
        results = self.collection.query(
            query_texts=[""],
            where={"feedback_score": {"$exists": True}},
            n_results=100
        )
        
        scores = [r['metadata']['feedback_score'] for r in results['metadatas']]
        return {
            'average_score': sum(scores) / len(scores) if scores else 0,
            'total_feedback': len(scores)
        }

    def get_similar_feedback(self, query: str, k: int = 3):
        """
        Retrieve similar feedback entries for a given query
        """
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=k
            )
            if results == None:
                return []
            return [json.loads(doc) for doc in results['documents'][0]]
        except Exception as e:
            print(f"Error in get_similar_feedback: {e}")
            return []

    def get_similar_responses(self, query: str, k: int = 3) -> list:
        """Pobiera podobne poprzednie odpowiedzi dla danego zapytania."""
        try:
            # Pobierz podobne odpowiedzi z bazy
            results = self.collection.query(
                query_texts=[query],
                n_results=k,
                where={"type": "response"}  # Filtruj tylko odpowiedzi
            )
            
            # Przekształć wyniki w listę odpowiedzi
            responses = []
            for i in range(len(results['documents'][0])):
                response = {
                    "query": results['metadatas'][0][i].get('query', ''),
                    "response": results['documents'][0][i],
                    "was_successful": results['metadatas'][0][i].get('was_successful', False),
                    "timestamp": results['metadatas'][0][i].get('timestamp', '')
                }
                responses.append(response)
            
            return responses
        except Exception as e:
            print(f"Error getting similar responses: {e}")
            return []

    def store_response(self, response_data: dict) -> bool:
        """Zapisuje odpowiedź do bazy danych."""
        try:
            # Dodaj typ odpowiedzi do metadanych
            response_data['type'] = 'response'
            
            # Generuj unikalny ID
            response_id = str(uuid.uuid4())
            
            # Przygotuj dane do zapisania
            documents = [response_data['response']]
            metadatas = [response_data]
            ids = [response_id]
            
            # Zapisz do bazy
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )

            return True
        except Exception as e:
            print(f"Error storing response: {e}")
            return False

    def store_correction(self, correction_data: dict) -> bool:
        """Zapisuje informację o korekcie nazwy."""
        try:
            # Dodaj typ korekty do metadanych
            correction_data['type'] = 'correction'
            
            # Generuj unikalny ID
            correction_id = str(uuid.uuid4())
            
            # Przygotuj dane do zapisania
            documents = [f"Name correction: {correction_data['original_name']} -> {correction_data['corrected_name']}"]
            metadatas = [correction_data]
            ids = [correction_id]
            
            # Zapisz do bazy
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            return True
        except Exception as e:
            print(f"Error storing correction: {e}")
            return False

class CachedChromaDB:
    def __init__(self, collection_name: str, embedding_model: str):
        self.ef = OllamaEmbeddingFunctionWrapper(embedding_model)
        self.client = chromadb.PersistentClient(
            path = 'chroma',
            settings = Settings(
                persist_directory="chroma",
                anonymized_telemetry=False,
        ))
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.ef
        )
        self.cache = {}
        
    def query_with_cache(self, query: str, n_results: int = 5):
        cache_key = f"{query}_{n_results}"
        if cache_key in self.cache:
            return self.cache[cache_key]
            
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        self.cache[cache_key] = results
        
        return results
        
    def clear_cache(self):
        self.cache.clear() 

