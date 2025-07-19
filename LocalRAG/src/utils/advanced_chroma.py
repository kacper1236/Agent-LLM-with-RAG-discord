from chromadb.config import Settings
import numpy as np
import chromadb
import json
import uuid
import datetime
from langchain_core.output_parsers import JsonOutputParser
from ..config import MODEL_EMBEDDINGS, MODEL
from .llm import LLMProvider
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings
from .llm_get_tags import clean_json_string
from llama_index.core.chat_engine.types import ChatMessage

model_embedding, _ = LLMProvider.getLLM(MODEL_EMBEDDINGS)
model, _ = LLMProvider.getLLM(MODEL)

class ChromaDBEmbeddingWrapper(EmbeddingFunction[Documents]):
    """
    Wrapper class to adapt LangChain embedding functions to ChromaDB's expected interface.
    """
    def __init__(self, langchain_embedding_function):
        self.langchain_ef = langchain_embedding_function
    
    def __call__(self, input: Documents) -> Embeddings:
        """
        ChromaDB expects this signature: __call__(self, input: Documents) -> Embeddings
        """
        try:
            # Use the LangChain embedding function's embed_documents method
            embeddings = self.langchain_ef.embed_documents(input)
            return embeddings
        except Exception as e:
            print(f"Error in embedding wrapper: {e}")
            # Fallback to a simple embedding if the main one fails
            return [[0.0] * 384 for _ in input]  # Return dummy embeddings

# Create the wrapped embedding function
wrapped_embedding_function = ChromaDBEmbeddingWrapper(model_embedding)

class RerankingChromaDB:
    def __init__(self, collection_name: str, embedding_model: str):
        self.ef = wrapped_embedding_function
        self.client = chromadb.PersistentClient(
            path = f'chroma/{MODEL + '__' + MODEL_EMBEDDINGS}/re-ranking',
            settings = Settings(
               persist_directory=f'{MODEL + '__' + MODEL_EMBEDDINGS}/re-ranking',
                anonymized_telemetry=False,
        ))
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.ef
        )
        self.llm = model

    def rerank_results(self, query: str, results: list, top_k: int = 5, score_weight: float = 0.2):
        """
        Rerankuje wyniki według podobieństwa do zapytania i oceny użytkownika.
        Dodatkowo filtruje wyniki przez LLM zgodny z llama_index (np. Ollama), bez użycia LangChain chainów.
        """
        if not results:
            return []

        try:
            query_embedding = model_embedding.embed_query(query)

            texts = []
            scores = []

            for r in results:
                if isinstance(r, dict):
                    texts.append(r.get('text', str(r)))
                    scores.append(float(r.get('user_score', 0)))
                elif isinstance(r, str):
                    texts.append(r)
                    scores.append(0)
                else:
                    texts.append(str(r))
                    scores.append(0)

            result_embeddings = model_embedding.embed_documents(texts)

            # Liczenie podobieństwa kosinusowego + waga za user_score
            similarities = []
            for i, result_embedding in enumerate(result_embeddings):
                similarity = np.dot(query_embedding, result_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(result_embedding)
                )
                weighted_similarity = similarity + (scores[i] * score_weight)
                similarities.append(weighted_similarity)

            # Sortowanie wyników
            ranked_results = list(zip(texts, similarities))
            ranked_results.sort(key=lambda x: x[1], reverse=True)

            reranked_texts = [text for text, _ in ranked_results[:top_k]]

            # Filtracja przez LLM (ręczna interakcja z self.llm – Ollama)
            filtered_results = []
            for text in reranked_texts:
                prompt_system:str = f"""
                You are an expert in text analysis and scoring similarity.
                Your task is to evaluate the relevance of the following text to the query.

                You only answer with 0 and 1, where:
                - 1 means the text is relevant to the query
                - 0 means the text is not relevant
                - If you're unsure, return 0.

                Answer only with 0 or 1.
                """
                prompt_user:str = f"""
                Query: {query}
                Text: {text}
                """

                try:
                    response = self.llm.chat(messages = [ChatMessage(role = "system", content = prompt_system), ChatMessage(role = "user", content = prompt_user)])
                    answer = response.message.content
                    if answer == "1":
                        filtered_results.append(text)
                except Exception as e:
                    print(f"LLM evaluation error for text: {text[:30]}... -> {e}")

            return filtered_results

        except Exception as e:
            print(f"Error in rerank_results: {e}")
            return []


class QueryExpansionChromaDB:
    def __init__(self, collection_name: str, embedding_model: str):
        self.ef = wrapped_embedding_function
        self.client = chromadb.PersistentClient(
            path = f'chroma/{MODEL + '__' + MODEL_EMBEDDINGS}/query-expansion',
            settings = Settings(
                persist_directory=f'{MODEL + '__' + MODEL_EMBEDDINGS}/query-expansion',
                anonymized_telemetry=False,
        ))
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.ef
        )
        self.llm = model
        
    def expand_query(self, query: str, quick_mode: bool = True):
        try:
            print(f"Expanding query: '{query[:50]}...'")
            
            # Najpierw sprawdź czy mamy już podobne rozszerzenia w bazie
            cached_expansions = self._get_cached_expansions(query)
            if cached_expansions:
                print(f"Using cached expansions for: {query[:50]}...")
                return cached_expansions
            
            # W trybie szybkim, zwróć tylko oryginalne zapytanie
            if quick_mode:
                print("Quick mode enabled - skipping query expansion")
                return [query]
            
            print("No cached expansions found, generating new ones...")
            
            # Generuj nowe rozszerzenia przez LLM
            expanded_queries = [query]  # Zawsze dołącz oryginalne zapytanie
            
            # Uproszczony prompt dla szybszego działania
            prompt_system:str = f"""
            Generate 2 alternative ways to ask question from user.
            
            Return ONLY a JSON array of strings. No explanations.
            Example: ["alternative 1", "alternative 2"]
            """

            prompt_user:str = f"""
            Question: {query}
            """
            try:
                print("Generating variants (simplified)...")
                variants_response = self.llm.chat(messages = [ChatMessage(role = "system", content = prompt_system), ChatMessage(role = "user", content = prompt_user)])
                variants = json.loads(str(variants_response.message.content))
                
                if isinstance(variants, list) and len(variants) > 0:
                    for variant in variants[:2]:  # Limit to 2 variants
                        if isinstance(variant, str) and variant.strip():
                            expanded_queries.append(variant.strip())
                    print(f"Successfully generated {len(variants)} variants")
                else:
                    print("No valid variants generated")
                        
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Failed to generate variants: {e}")
            
            # Jeśli nie udało się wygenerować wariantów, użyj tylko oryginalnego zapytania
            if len(expanded_queries) == 1:
                print(f"Using original query only")
            else:
                print(f"Successfully expanded to {len(expanded_queries)} queries")
            
            # Zapisz rozszerzone zapytania do bazy dla przyszłego użycia
            if len(expanded_queries) > 1:
                self._store_expansions(query, expanded_queries)
            
            return expanded_queries
            
        except Exception as e:
            print(f"Error in Query Expansion: {e}")
            return [query]  # Fallback do oryginalnego zapytania

    def _get_cached_expansions(self, query: str, similarity_threshold: float = 0.85):
        """Sprawdza czy mamy już podobne rozszerzenia w bazie."""
        try:
            # Najpierw sprawdź czy w ogóle mamy jakieś dane w kolekcji
            collection_count = self.collection.count()
            if collection_count == 0:
                print("No cached expansions available - collection is empty")
                return None
            
            # Wyszukaj podobne zapytania
            results = self.collection.query(
                query_texts=[query],
                n_results=3  # Pobierz więcej wyników aby znaleźć podobne
            )
            
            if not results['documents'] or len(results['documents'][0]) == 0:
                print("No similar queries found in cache")
                return None
            
            # Sprawdź każdy wynik pod kątem podobieństwa
            for _, (_, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
                if not metadata:
                    continue
                    
                original_query = metadata.get('original_query', '')
                stored_expansions = metadata.get('expansions', '')
                
                # Sprawdź podobieństwo zapytań (prosty check długości i słów kluczowych)
                if self._queries_are_similar(query, original_query, similarity_threshold):
                    print(f"Found similar cached query: '{original_query[:50]}...'")
                    
                    if stored_expansions:
                        try:
                            expansions = json.loads(stored_expansions) if isinstance(stored_expansions, str) else stored_expansions
                            if isinstance(expansions, list) and len(expansions) > 1:
                                print(f"Using {len(expansions)} cached expansions")
                                return expansions
                        except json.JSONDecodeError:
                            print("Error parsing cached expansions JSON")
                            continue
            
            print("No sufficiently similar cached expansions found")
            return None
                    
        except Exception as e:
            print(f"Error getting cached expansions: {e}")
            return None

    def _queries_are_similar(self, query1: str, query2: str, threshold: float = 0.85) -> bool:
        """Sprawdza czy dwa zapytania są podobne."""
        if not query1 or not query2:
            return False
            
        # Normalizuj zapytania
        q1_words = set(query1.lower().split())
        q2_words = set(query2.lower().split())
        
        # Oblicz podobieństwo Jaccard
        intersection = len(q1_words.intersection(q2_words))
        union = len(q1_words.union(q2_words))
        
        if union == 0:
            return False
            
        similarity = intersection / union
        return similarity >= threshold

    def _store_expansions(self, original_query: str, expanded_queries: list):
        """Zapisuje rozszerzone zapytania do bazy."""
        try:
            import uuid
            
            # Przygotuj metadane
            metadata = {
                'original_query': original_query,
                'expansions': json.dumps(expanded_queries),
                'expansion_count': len(expanded_queries),
                'timestamp': str(uuid.uuid4())
            }
            
            # Zapisz do bazy - użyj oryginalnego zapytania jako dokumentu
            self.collection.add(
                documents=[original_query],
                metadatas=[metadata],
                ids=[f"expansion_{hash(original_query)}_{uuid.uuid4().hex[:8]}"]
            )
            
            print(f"Stored expansions for query: {original_query[:50]}...")
            
        except Exception as e:
            print(f"Error storing expansions: {e}")

    def get_expansion_stats(self):
        """Zwraca statystyki dotyczące rozszerzeń zapytań."""
        try:
            # Pobierz wszystkie rekordy
            results = self.collection.query(
                query_texts=[""],
                n_results=1000  # Duża liczba aby pobrać wszystkie
            )
            
            total_expansions = len(results['documents'][0]) if results['documents'] else 0
            
            return {
                'total_stored_expansions': total_expansions,
                'collection_name': self.collection.name
            }
            
        except Exception as e:
            print(f"Error getting expansion stats: {e}")
            return {'total_stored_expansions': 0, 'error': str(e)}

class DynamicChunkingChromaDB:
    def __init__(self, collection_name: str, embedding_model: str):
        self.ef = wrapped_embedding_function
        self.client = chromadb.PersistentClient(
            path = f'chroma/{MODEL + '__' + MODEL_EMBEDDINGS}/dynamic-chunking',
            settings = Settings(
                persist_directory=f'{MODEL + '__' + MODEL_EMBEDDINGS}/dynamic-chunking',
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
        self.ef = wrapped_embedding_function
        self.client = chromadb.PersistentClient(
            path = f'chroma/{MODEL + '__' + MODEL_EMBEDDINGS}/chain-of-thought',
            settings = Settings(
                persist_directory=f'{MODEL + '__' + MODEL_EMBEDDINGS}/chain-of-thought',
                anonymized_telemetry=False,
        ))
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.ef
        )
        self.llm = model
        
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
            thought = self.llm.chat(messages = [ChatMessage(role = "user", content = thought_prompt)])
            thoughts.append(thought.message.content)
            
        final_prompt = f"""
        Based on these thoughts:
        {thoughts}
        
        Provide a final answer to: {query}
        """
        
        return self.llm.chat(messages = [ChatMessage(role = "user", content = final_prompt)]).message.content
    
class FeedbackChromaDB:
    def __init__(self, collection_name: str, embedding_model: str):
        self.ef = wrapped_embedding_function
        self.client = chromadb.PersistentClient(
            path = f'chroma/{MODEL + '__' + MODEL_EMBEDDINGS}/feedback',
            settings = Settings(
                persist_directory=f'{MODEL + '__' + MODEL_EMBEDDINGS}/feedback',
                anonymized_telemetry=False,
        ))
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.ef
        )
        self.llm = model
        
    def evaluate_response(self, query: str, response: str):
        """
        Automatycznie ocenia jakość odpowiedzi
        """
        try:
            prompt_system:str = f"""
            Oceń jakość tej odpowiedzi na pytanie użytkownika.

            Zwróć tylko liczby 1-5 dla każdej kategorii w następującym formacie bez dodatkowego tekstu, w formacie JSON:
            {{
                "accuracy": [liczba],
                "completeness": [liczba],
                "cohesion": [liczba],
                "comment": "krótkie uzasadnienie w jednej linii"
            }}
            """
            prompt_user:str = f"""
            Pytanie: {query}
            Odpowiedź: {response}
            """

            raw_response = self.llm.chat(messages = [ChatMessage(role = "system", content = prompt_system), 
                                                     ChatMessage(role = "user", content = prompt_user)]) 
            json_result = clean_json_string(raw_response.message.content)
            parsed = JsonOutputParser().parse(json_result)

            return parsed

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
            query_embedding = model_embedding.embed_query(query_text)
         
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
        try:
            # Get all results and filter manually since ChromaDB doesn't support $exists
            results = self.collection.query(
                query_texts=[""],
                n_results=1000  # Get more results for better statistics
            )
            
            if not results or not results.get('metadatas') or not results['metadatas'][0]:
                return {
                    'average_score': 0,
                    'total_feedback': 0
                }
            
            # Extract scores from metadata - filter for feedback entries
            scores = []
            for metadata in results['metadatas'][0]:
                # Check if this is a feedback entry (has user_score)
                if 'user_score' in metadata and metadata['user_score']:
                    try:
                        score = float(metadata.get('user_score', 0))
                        if score > 0:  # Only include valid scores
                            scores.append(score)
                    except (ValueError, TypeError):
                        continue
            
            return {
                'average_score': sum(scores) / len(scores) if scores else 0,
                'total_feedback': len(scores)
            }
            
        except Exception as e:
            print(f"Error in get_feedback_stats: {e}")
            return {
                'average_score': 0,
                'total_feedback': 0
            }

    def get_similar_feedback(self, query: str, k: int = 3):
        """
        Retrieve similar feedback entries for a given query
        """
        try:
            # Get all results and filter manually since ChromaDB doesn't support $exists
            results = self.collection.query(
                query_texts=[query],
                n_results=k * 3  # Get more results to filter from
            )
            
            if not results or not results.get('metadatas') or not results['metadatas'][0]:
                return []
            
            # Filter for feedback entries and return the metadata
            feedback_entries = []
            for metadata in results['metadatas'][0]:
                # Check if this is a feedback entry (has user_score)
                if 'user_score' in metadata and metadata['user_score']:
                    feedback_entry = {
                        'query': metadata.get('query', ''),
                        'response': metadata.get('response', ''),
                        'score': metadata.get('user_score', '0'),
                        'feedback_text': metadata.get('feedback_text', ''),
                        'timestamp': metadata.get('timestamp', ''),
                        'auto_accuracy': metadata.get('auto_accuracy', ''),
                        'auto_completeness': metadata.get('auto_completeness', ''),
                        'auto_cohesion': metadata.get('auto_cohesion', ''),
                        'auto_comment': metadata.get('auto_comment', '')
                    }
                    feedback_entries.append(feedback_entry)
                    
                    # Stop when we have enough feedback entries
                    if len(feedback_entries) >= k:
                        break
            
            return feedback_entries
            
        except Exception as e:
            print(f"Error in get_similar_feedback: {e}")
            return []

    def get_similar_responses(self, query: str, k: int = 3) -> list:
        """Pobiera podobne poprzednie odpowiedzi dla danego zapytania."""
        try:
            # Get all results and filter manually since ChromaDB doesn't support complex where clauses
            results = self.collection.query(
                query_texts=[query],
                n_results=k * 3  # Get more results to filter from
            )
            
            if not results or not results.get('metadatas') or not results['metadatas'][0]:
                return []
            
            # Filter for response entries and return the data
            responses = []
            for i, metadata in enumerate(results['metadatas'][0]):
                # Check if this is a response entry (has type = "response")
                if metadata.get('type') == 'response':
                    response = {
                        "query": metadata.get('query', ''),
                        "response": results['documents'][0][i] if i < len(results['documents'][0]) else metadata.get('response', ''),
                        "was_successful": metadata.get('was_successful', False),
                        "timestamp": metadata.get('timestamp', '')
                    }
                    responses.append(response)
                    
                    # Stop when we have enough response entries
                    if len(responses) >= k:
                        break
            
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
            documents = [str(response_data['response'])]
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
    def __init__(self, collection_name: str, embedding_model: str, similarity_threshold: float = 0.7):
        self.ef = wrapped_embedding_function
        self.client = chromadb.PersistentClient(
            path = 'chroma/cache',
            settings = Settings(
                persist_directory="cache",
                anonymized_telemetry=False,
        ))
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.ef
        )
        self.cache = {}
        self.similarity_threshold = similarity_threshold
        self.embedding_model = model_embedding
        
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
    
    def check_similarity_cache(self, query: str, n_results: int = 3):
        """
        Sprawdza czy istnieje podobne zapytanie w cache z prawdopodobieństwem >= similarity_threshold.
        Zwraca (is_similar, cached_response, similarity_score) lub (False, None, 0.0)
        """
        try:
            # Pobierz wszystkie zapisane zapytania z cache
            all_results = self.collection.query(
                query_texts=[query],
                n_results=20  # Pobierz więcej wyników do porównania
            )
            
            if not all_results or not all_results.get('documents') or not all_results['documents'][0]:
                return False, None, 0.0
            
            # Generuj embedding dla aktualnego zapytania
            query_embedding = self.embedding_model.embed_query(query)
            
            # Sprawdź podobieństwo z każdym zapisanym zapytaniem
            for _, (document, metadata) in enumerate(zip(
                all_results['documents'][0], 
                all_results.get('metadatas', [{}])[0] if all_results.get('metadatas') else [{}]
            )):
                if not metadata:
                    continue
                    
                # Sprawdź czy to jest zapytanie (nie odpowiedź)
                if metadata.get('type') != 'search_query':
                    continue
                
                # Pobierz embedding zapisanego zapytania
                if 'embedding' in metadata:
                    try:
                        cached_embedding = json.loads(metadata['embedding'])
                    except:
                        continue
                else:
                    # Jeśli nie ma zapisanego embeddingu, wygeneruj go
                    cached_query = metadata.get('original_query', document)
                    cached_embedding = self.embedding_model.embed_query(cached_query)
                
                # Oblicz podobieństwo cosinusowe
                similarity = np.dot(query_embedding, cached_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(cached_embedding)
                )
                
                print(f"Podobieństwo zapytania '{query[:50]}...' do '{metadata.get('original_query', document)[:50]}...': {similarity:.3f}")
                
                # Jeśli podobieństwo >= threshold, zwróć cached response
                if similarity >= self.similarity_threshold:
                    cached_response = metadata.get('cached_response', '')
                    print(f"Znaleziono podobne zapytanie w cache (podobieństwo: {similarity:.3f})")
                    return True, cached_response, similarity
            
            return False, None, 0.0
            
        except Exception as e:
            print(f"Błąd podczas sprawdzania cache: {e}")
            return False, None, 0.0
    
    def store_search_query_and_response(self, query: str, response: str):
        """
        Zapisuje zapytanie i odpowiedź do cache dla przyszłych porównań.
        """
        try:
            # Generuj embedding dla zapytania
            query_embedding = self.embedding_model.embed_query(query)
            
            # Przygotuj metadane
            metadata = {
                'type': 'search_query',
                'original_query': query,
                'cached_response': response,
                'embedding': json.dumps(query_embedding),
                'timestamp': datetime.datetime.now().isoformat(),
                'usage_count': 1
            }
            
            # Generuj unikalny ID
            search_id = str(uuid.uuid4())
            
            # Zapisz do bazy
            self.collection.add(
                documents=[query],
                metadatas=[metadata],
                ids=[search_id]
            )
            
            print(f"Zapisano zapytanie do cache: '{query[:50]}...'")
            return True
            
        except Exception as e:
            print(f"Błąd podczas zapisywania do cache: {e}")
            return False
    
    def update_usage_count(self, query: str):
        """
        Aktualizuje licznik użycia dla podobnego zapytania.
        """
        try:
            # Znajdź podobne zapytanie
            results = self.collection.query(
                query_texts=[query],
                n_results=1
            )
            
            if results and results.get('metadatas') and results['metadatas'][0]:
                metadata = results['metadatas'][0][0]
                if metadata.get('type') == 'search_query':
                    # Zwiększ licznik użycia
                    current_count = int(metadata.get('usage_count', 0))
                    metadata['usage_count'] = current_count + 1
                    
                    # Aktualizuj w bazie (ChromaDB nie ma bezpośredniej metody update, więc usuwamy i dodajemy ponownie)
                    doc_id = results['ids'][0][0]
                    self.collection.delete(ids=[doc_id])
                    self.collection.add(
                        documents=[results['documents'][0][0]],
                        metadatas=[metadata],
                        ids=[doc_id]
                    )
                    
                    print(f"Zaktualizowano licznik użycia dla zapytania (nowa wartość: {metadata['usage_count']})")
                    
        except Exception as e:
            print(f"Błąd podczas aktualizacji licznika użycia: {e}")
    
    def get_cache_stats(self):
        """
        Zwraca statystyki cache'u.
        """
        try:
            # Pobierz wszystkie wpisy
            all_results = self.collection.query(
                query_texts=[""],
                n_results=1000
            )
            
            if not all_results or not all_results.get('metadatas'):
                return {
                    'total_queries': 0,
                    'total_usage': 0,
                    'average_usage': 0
                }
            
            search_queries = []
            total_usage = 0
            
            for metadata in all_results['metadatas'][0]:
                if metadata and metadata.get('type') == 'search_query':
                    search_queries.append(metadata)
                    total_usage += int(metadata.get('usage_count', 0))
            
            return {
                'total_queries': len(search_queries),
                'total_usage': total_usage,
                'average_usage': total_usage / len(search_queries) if search_queries else 0
            }
            
        except Exception as e:
            print(f"Błąd podczas pobierania statystyk cache: {e}")
            return {
                'total_queries': 0,
                'total_usage': 0,
                'average_usage': 0
            }
        
    def clear_cache(self):
        self.cache.clear()
        # Opcjonalnie można też wyczyścić całą kolekcję ChromaDB
        # self.collection.delete()

