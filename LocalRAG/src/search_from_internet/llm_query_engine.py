from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core.llms import LLM
from llama_index.core.query_engine import CustomQueryEngine
from llama_index.core.query_engine.custom import STR_OR_RESPONSE_TYPE
from typing import ClassVar, Optional
from ..advanced_rag import AdvancedRAG
from datetime import datetime
from typing_extensions import List, TypedDict, Optional, Union
import ast

class ChatMessageDict(TypedDict):
    role: MessageRole
    content: str

ChatHistoryType = List[Union[ChatMessage, ChatMessageDict]]
OptionalChatHistoryType = Optional[ChatHistoryType]

class LLMQueryEngine(CustomQueryEngine):
    """
    This is a generic language model which can answer any question not handled \
    by any other tool given. ALWAYS ask in complete questions.
    Args:
        query str: The query string to be answered.
    
    Return:
        str: The answer to the query.
    """

    system_prompt: ClassVar[str] = """\
        You are an advanced language model tasked with providing precise and comprehensive answers \
        to user questions. Your responses should be as brief as possible, while including all necessary \
        details to fully answer the question. Aim for clarity and completeness in every answer. \
        Use clear and direct language, avoiding unnecessary words. Here are the key instructions to follow:

        1. Understand the user's question thoroughly.
        2. Answer with the minimum number of words needed to fully and accurately address the question.
        3. Include all relevant details that are essential for a complete response.
        4. Avoid extra information that doesn't directly answer the question.
        5. Maintain a polite and professional tone.
        6. Always answer in the language of the given question.
        7. If user asks for current data or stock exchange information - DO NOT use feedback from the user to improve your answers!
        8. Answers from stock_search and exchange_search are FINAL!
        9. NEVER use Feedback context for actual or current data!

        Always answer in normal text mode and only use structured format if they are part of your answer.
        DO NOT prepend your answer with any label like 'assistant:' or 'answer:'.
        Normally, respond in plain text. Only return JSON objects when explicitly instructed by the user prompt.
    """
    llm: LLM
    advanced_rag: Optional[AdvancedRAG] = None
    history: ChatHistoryType = []
    chunk_selection_strategy: str = "llm"  # "llm", "top_k"
    max_chunks: int = 3
    similarity_threshold: float = 0.7
    use_feedback: bool = True
    enable_query_expansion: bool = True

    def __init__(self, model: LLM, collection_name: str = None, embedding_model: str = None, 
                 history: ChatHistoryType = [], chunk_selection_strategy: str = "llm", 
                 max_chunks: int = 3, similarity_threshold: float = 0.7, use_feedback: bool = True,
                 enable_query_expansion: bool = True):
        super().__init__(llm=model)
        self.llm = model
        self.use_feedback = use_feedback
        self.enable_query_expansion = enable_query_expansion
        if collection_name and embedding_model:
            self.advanced_rag = AdvancedRAG(collection_name, embedding_model)
            print("Advanced RAG initialized")
        self.history = history
        self.chunk_selection_strategy = chunk_selection_strategy
        self.max_chunks = max_chunks
        self.similarity_threshold = similarity_threshold

    def _select_relevant_chunks(self, query_str: str, chunks: list, max_chunks: int = 3) -> list:
        """Używa LLM do wyboru najbardziej relevantnych chunków dla zapytania."""
        if not chunks or len(chunks) <= max_chunks:
            return chunks
        
        # Przygotuj prompt do selekcji chunków
        selection_prompt = f"""
        Given the user question: "{query_str}"
        
        Please select the {max_chunks} most relevant text chunks from the following options that would best help answer the question.
        Return only the numbers (1, 2, 3, etc.) of the selected chunks, separated by commas.
        
        Available chunks:
        """
        
        for i, chunk in enumerate(chunks[:10], 1):  # Limit to first 10 chunks to avoid token limits
            # Truncate very long chunks
            truncated_chunk = chunk[:200] + "..." if len(chunk) > 200 else chunk
            selection_prompt += f"\n{i}. {truncated_chunk}\n"
        
        selection_prompt += f"\nSelect the {max_chunks} most relevant chunks (numbers only, comma-separated):"
        
        try:
            selection_messages = [
                ChatMessage(role=MessageRole.SYSTEM, content="You are a helpful assistant that selects the most relevant text chunks for answering questions. Return only numbers separated by commas."),
                ChatMessage(role=MessageRole.USER, content=selection_prompt)
            ]
            
            selection_response = self.llm.chat(selection_messages)
            
            # Extract response text
            if hasattr(selection_response, 'response'):
                response_text = selection_response.response
            elif hasattr(selection_response, 'message'):
                response_text = selection_response.message.content
            else:
                response_text = str(selection_response)
            
            # Parse selected chunk numbers
            selected_numbers = []
            for num_str in response_text.strip().split(','):
                try:
                    num = int(num_str.strip())
                    if 1 <= num <= len(chunks):
                        selected_numbers.append(num - 1)  # Convert to 0-based index
                except ValueError:
                    continue
            
            # Return selected chunks
            if selected_numbers:
                return [chunks[i] for i in selected_numbers[:max_chunks]]
            else:
                # Fallback to first chunks if parsing failed
                return chunks[:max_chunks]
                
        except Exception as e:
            print(f"Error in chunk selection: {e}")
            # Fallback to first chunks
            return chunks[:max_chunks]

    def _select_chunks_by_strategy(self, query_str: str, chunks: list) -> list:
        """Wybiera chunki według skonfigurowanej strategii."""
        if not chunks:
            return []
            
        if self.chunk_selection_strategy == "llm":
            return self._select_relevant_chunks(query_str, chunks, self.max_chunks)
        elif self.chunk_selection_strategy == "top_k":
            # Zwróć pierwsze max_chunks chunków (już są rerankowane)
            return chunks[:self.max_chunks]
        else:
            # Default fallback
            return chunks[:self.max_chunks]

    def _log_chunk_selection(self, query_str: str, total_chunks: int, selected_chunks: list):
        """Loguje informacje o selekcji chunków dla debugowania."""
        print(f"Query: {query_str[:50]}...")
        print(f"Strategy: {self.chunk_selection_strategy}")
        print(f"Total chunks available: {total_chunks}")
        print(f"Selected chunks: {len(selected_chunks)}")
        if selected_chunks:
            print("Selected chunk previews:")
            for i, chunk in enumerate(selected_chunks, 1):
                preview = chunk[:100] + "..." if len(chunk) > 100 else chunk
                print(f"  {i}. {preview}")
        print("-" * 50)

    def custom_query(self, query_str: str) -> STR_OR_RESPONSE_TYPE:
        """Run a custom query."""
        if query_str.startswith("{"):
            query = ast.literal_eval(query_str)
            query = {k: v.strip('"') for k, v in query.items()}
            try:
                query_str = query['query']
            except:
                return "Invalid format string. Can't be a JSON. Try one again."
        
        # Get enhanced feedback context with automatic evaluations
        feedback_context = ""
        if self.advanced_rag and self.use_feedback:
            feedback_context = self.get_feedback_enhanced_context(query_str, include_auto_eval=True)
        
        # Przygotuj prompt z kontekstem
        if feedback_context != "":
            enhanced_prompt = f"{self.system_prompt}\n\nFeedback context:\n{feedback_context}"
        else:
            enhanced_prompt = f"{self.system_prompt}"

        # Pobierz odpowiednie chunki z Advanced RAG
        relevant_chunks = []
        selected_chunks = []
        
        if self.advanced_rag:
            # Rozszerz zapytanie tylko jeśli włączone
            if self.enable_query_expansion:
                expanded_queries = self.advanced_rag.query_expansion_db.expand_query(query_str, quick_mode=False)
            else:
                expanded_queries = [query_str]  # Użyj tylko oryginalnego zapytania

            print("Expanded queries: ", expanded_queries)
            
            # Sprawdź czy mamy dokumenty w bazie
            try:
                collection_count = self.advanced_rag.dynamic_chunking_db.collection.count()
                print(f"Documents in knowledge base: {collection_count}")
                
                if collection_count == 0:
                    print("Warning: No documents found in knowledge base!")
                    # Możemy dodać informację do odpowiedzi
                    enhanced_prompt += "\n\nIMPORTANT: No documents are available in the knowledge base. Answer based on your general knowledge only."
            except Exception as e:
                print(f"Error checking collection count: {e}")
            
            # Zbierz chunki z rozszerzonych zapytań
            for q in expanded_queries:
                try:
                    chunks_result = self.advanced_rag.dynamic_chunking_db.collection.query(
                        query_texts=[q],
                        n_results=5  # Zwiększ liczbę wyników
                    )
                    # Spłaszcz zagnieżdżone listy dokumentów
                    if chunks_result['documents'] and len(chunks_result['documents']) > 0:
                        for doc_list in chunks_result['documents']:
                            if doc_list:  # Sprawdź czy lista nie jest pusta
                                relevant_chunks.extend(doc_list)
                except Exception as e:
                    print(f"Error querying for '{q}': {e}")
                    continue
            
            print(f"Total relevant chunks collected: {len(relevant_chunks)}")
            
            # Rerankuj chunki tylko jeśli mamy jakieś
            if relevant_chunks:
                # Usuń duplikaty
                unique_chunks = list(set(relevant_chunks))
                print(f"Unique chunks after deduplication: {len(unique_chunks)}")
                
                if unique_chunks:
                    ranked_chunks = self.advanced_rag.reranking_db.rerank_results(query_str, unique_chunks)
                    
                    # Użyj wybranej strategii do selekcji chunków
                    selected_chunks = self._select_chunks_by_strategy(query_str, ranked_chunks)
                    
                    # Loguj informacje o selekcji (opcjonalne - można wyłączyć w produkcji)
                    # self._log_chunk_selection(query_str, len(ranked_chunks), selected_chunks)
            else:
                print("No relevant chunks found - proceeding without context")
        
        # Generuj odpowiedź z użyciem LLM
        if isinstance(self.llm, LLM):
            messages = [
                ChatMessage(role=MessageRole.SYSTEM, content=enhanced_prompt),
            ]
            
            # Dodaj tylko wybrane chunki jako kontekst
            if selected_chunks:
                context_content = "Use the following relevant context to answer the question:\n\n"
                for i, chunk in enumerate(selected_chunks, 1):
                    context_content += f"Context {i}:\n{chunk}\n\n"
                
                messages.append(ChatMessage(
                    role=MessageRole.SYSTEM,
                    content=context_content
                ))

                print("Context content: ", context_content)
            else:
                print("No context available - answering based on general knowledge only")
                # Dodaj informację że odpowiadamy bez kontekstu
                messages.append(ChatMessage(
                    role=MessageRole.SYSTEM,
                    content="Note: No relevant context was found in the knowledge base. Please answer based on your general knowledge."
                ))

            # Dodaj historię zapytań i odpowiedzi
            for message in self.history:
                if isinstance(message, ChatMessage):
                    messages.append(ChatMessage(role=message.role, content=message.content))
                elif isinstance(message, dict):
                    messages.append(ChatMessage(role=message['role'], content=message['content']))

            # Dodaj aktualne zapytanie użytkownika
            messages.append(ChatMessage(role=MessageRole.USER, content=query_str))
            
            try:
                # Make the request to the LLM
                chat_response = self.llm.chat(messages)
                
                # Extract the string content from the response
                if hasattr(chat_response, 'response'):
                    response_text = chat_response.response
                    if isinstance(response_text, str):
                        # Store the response for future feedback analysis
                        if self.advanced_rag and self.use_feedback:
                            self.store_response_for_feedback(query_str, response_text, True)
                        return response_text
                    else:
                        if hasattr(response_text, 'content'):
                            final_response = str(response_text.content)
                        elif hasattr(response_text, 'text'):
                            final_response = str(response_text.text)
                        else:
                            final_response = str(response_text)
                        
                        # Store the response for future feedback analysis
                        if self.advanced_rag and self.use_feedback:
                            self.store_response_for_feedback(query_str, final_response, True)
                        return final_response
                elif hasattr(chat_response, 'message'):
                    final_response = str(chat_response.message.content)
                    if self.advanced_rag and self.use_feedback:
                        self.store_response_for_feedback(query_str, final_response, True)
                    return final_response
                elif hasattr(chat_response, 'content'):
                    final_response = str(chat_response.content)
                    if self.advanced_rag and self.use_feedback:
                        self.store_response_for_feedback(query_str, final_response, True)
                    return final_response
                elif hasattr(chat_response, 'text'):
                    final_response = str(chat_response.text)
                    if self.advanced_rag and self.use_feedback:
                        self.store_response_for_feedback(query_str, final_response, True)
                    return final_response
                elif hasattr(chat_response, 'generations'):
                    if chat_response.generations and len(chat_response.generations) > 0:
                        generation = chat_response.generations[0]
                        if hasattr(generation, 'text'):
                            final_response = str(generation.text)
                        elif hasattr(generation, 'message'):
                            final_response = str(generation.message.content)
                        else:
                            final_response = str(generation)
                        
                        if self.advanced_rag and self.use_feedback:
                            self.store_response_for_feedback(query_str, final_response, True)
                        return final_response
                else:
                    final_response = str(chat_response)
                    if self.advanced_rag and self.use_feedback:
                        self.store_response_for_feedback(query_str, final_response, True)
                    return final_response
            except Exception as e:
                print(f"Error processing LLM response: {e}")
                error_response = f"Error processing response: {str(e)}"
                if self.advanced_rag and self.use_feedback:
                    self.store_response_for_feedback(query_str, error_response, False)
                return error_response
            
        return "No response generated"

    def _create_feedback_context(self, similar_feedback: list) -> str:
        """Tworzy kontekst z podobnych feedbacków."""
        context = "Based on similar previous interactions:\n"
        for feedback in similar_feedback:
            context += f"- Question: {feedback['query']}\n"
            context += f"  Score: {feedback['score']}/5\n"
            if feedback.get('feedback_text'):
                context += f"  Feedback: {feedback['feedback_text']}\n"
        return context

    def store_feedback(self, query: str, response: str, score: int, feedback_text: str = ""):
        """Store feedback and use it for future responses."""
        if self.advanced_rag:
            feedback_data = {
                "query": query,
                "response": response,
                "score": score,
                "feedback_text": feedback_text,
                "timestamp": datetime.now().isoformat()
            }
            return self.advanced_rag.feedback_db.store_feedback(feedback_data)
        return False

    def get_feedback_stats(self):
        """Get feedback statistics from the database."""
        if self.advanced_rag:
            return self.advanced_rag.feedback_db.get_feedback_stats()
        return {"average_score": 0, "total_feedback": 0}

    def evaluate_response_automatically(self, query: str, response: str):
        """Automatically evaluate response quality using LLM."""
        if self.advanced_rag:
            return self.advanced_rag.feedback_db.evaluate_response(query, response)
        return {
            "accuracy": 1,
            "completeness": 1,
            "cohesion": 1,
            "comment": "Advanced RAG not available"
        }

    def get_similar_feedback_for_query(self, query: str, k: int = 3):
        """Get similar feedback entries for a given query."""
        if self.advanced_rag:
            return self.advanced_rag.feedback_db.get_similar_feedback(query, k)
        return []

    def store_response_for_feedback(self, query: str, response: str, was_successful: bool = True):
        """Store response for future feedback analysis."""
        if self.advanced_rag:
            response_data = {
                "query": query,
                "response": response,
                "was_successful": was_successful,
                "timestamp": datetime.now().isoformat(),
                "type": "response"
            }
            return self.advanced_rag.feedback_db.store_response(response_data)
        return False

    def provide_feedback_with_auto_eval(self, query: str, response: str, score: int, feedback_text: str = ""):
        """
        Comprehensive feedback method that combines user feedback with automatic evaluation.
        
        Args:
            query (str): Original query
            response (str): Response that was given
            score (int): User feedback score (1-5)
            feedback_text (str): Additional user feedback text
            
        Returns:
            dict: Combined feedback results including auto-evaluation
        """
        if not self.advanced_rag:
            return {"success": False, "error": "Advanced RAG not available"}
        
        try:
            # Get automatic evaluation
            auto_eval = self.evaluate_response_automatically(query, response)
            
            # Store user feedback
            feedback_success = self.store_feedback(query, response, score, feedback_text)
            
            # Store response for future analysis
            response_success = self.store_response_for_feedback(query, response, score >= 3)
            
            return {
                "success": feedback_success and response_success,
                "user_score": score,
                "user_feedback": feedback_text,
                "auto_evaluation": auto_eval,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error in comprehensive feedback: {str(e)}"
            }

    def get_feedback_enhanced_context(self, query: str, include_auto_eval: bool = True):
        """
        Get enhanced feedback context including both user feedback and automatic evaluations.
        
        Args:
            query (str): Query to find similar feedback for
            include_auto_eval (bool): Whether to include automatic evaluation data
            
        Returns:
            str: Enhanced context string for prompt
        """
        if not self.advanced_rag:
            return ""
        
        try:
            similar_feedback = self.get_similar_feedback_for_query(query, k=5)
            
            if not similar_feedback:
                return ""
            
            context = "Based on similar previous interactions and evaluations:\n"
            
            for i, feedback in enumerate(similar_feedback, 1):
                context += f"\n{i}. Question: {feedback.get('query', 'N/A')}\n"
                context += f"   User Score: {feedback.get('score', 'N/A')}/5\n"
                
                if feedback.get('feedback_text'):
                    context += f"   User Feedback: {feedback['feedback_text']}\n"
                
                if include_auto_eval:
                    context += f"   Auto Accuracy: {feedback.get('auto_accuracy', 'N/A')}/5\n"
                    context += f"   Auto Completeness: {feedback.get('auto_completeness', 'N/A')}/5\n"
                    context += f"   Auto Cohesion: {feedback.get('auto_cohesion', 'N/A')}/5\n"
                    
                    if feedback.get('auto_comment'):
                        context += f"   Auto Comment: {feedback['auto_comment']}\n"
            
            context += "\nUse this feedback to improve your response quality.\n"
            return context
            
        except Exception as e:
            print(f"Error getting enhanced feedback context: {e}")
            return ""

    def get_performance_metrics(self):
        """
        Get comprehensive performance metrics based on feedback data.
        
        Returns:
            dict: Performance metrics including scores, trends, and recommendations
        """
        if not self.advanced_rag:
            return {"error": "Advanced RAG not available"}
        
        try:
            stats = self.get_feedback_stats()
            
            # Get recent feedback for trend analysis
            recent_feedback = self.get_similar_feedback_for_query("", k=20)  # Get recent entries
            
            metrics = {
                "overall_stats": stats,
                "total_responses": len(recent_feedback),
                "performance_breakdown": {
                    "excellent": 0,  # 5 stars
                    "good": 0,       # 4 stars
                    "average": 0,    # 3 stars
                    "poor": 0,       # 2 stars
                    "very_poor": 0   # 1 star
                }
            }
            
            # Analyze score distribution
            for feedback in recent_feedback:
                score = int(feedback.get('score', 0))
                if score == 5:
                    metrics["performance_breakdown"]["excellent"] += 1
                elif score == 4:
                    metrics["performance_breakdown"]["good"] += 1
                elif score == 3:
                    metrics["performance_breakdown"]["average"] += 1
                elif score == 2:
                    metrics["performance_breakdown"]["poor"] += 1
                elif score == 1:
                    metrics["performance_breakdown"]["very_poor"] += 1
            
            # Calculate percentages
            total = metrics["total_responses"]
            if total > 0:
                for category in metrics["performance_breakdown"]:
                    count = metrics["performance_breakdown"][category]
                    metrics["performance_breakdown"][category] = {
                        "count": count,
                        "percentage": round((count / total) * 100, 2)
                    }
            
            # Add recommendations
            avg_score = stats.get("average_score", 0)
            if avg_score >= 4.5:
                metrics["recommendation"] = "Excellent performance! Keep up the good work."
            elif avg_score >= 4.0:
                metrics["recommendation"] = "Good performance with room for minor improvements."
            elif avg_score >= 3.0:
                metrics["recommendation"] = "Average performance. Consider analyzing feedback for improvement areas."
            else:
                metrics["recommendation"] = "Performance needs improvement. Review feedback patterns and adjust responses."
            
            return metrics
            
        except Exception as e:
            return {"error": f"Error calculating performance metrics: {str(e)}"}

#reference code: https://github.com/run-llama/llama_index/issues/14343