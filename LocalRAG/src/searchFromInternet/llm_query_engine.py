from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core.llms import LLM
from llama_index.core.query_engine import CustomQueryEngine
from llama_index.core.query_engine.custom import STR_OR_RESPONSE_TYPE
from typing import ClassVar, Optional
from ..advanced_rag import AdvancedRAG
from datetime import datetime

class LLMQueryEngine(CustomQueryEngine):
    """
    This is a generic language model which can answer any question not handled \
    by any other tool given. ALWAYS ask in complete questions.
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

        Always answer in normal text mode and only use structured format if they are part of your answer.
        DO NOT prepend your answer with any label like 'assistant:' or 'answer:'.
    """
    
    llm: LLM 
    advanced_rag: Optional[AdvancedRAG] = None

    def __init__(self, llm: LLM, collection_name: str = None, embedding_model: str = None):
        super().__init__(llm=llm)
        self.llm = llm
        if collection_name and embedding_model:
            self.advanced_rag = AdvancedRAG(collection_name, embedding_model)

    def custom_query(self, query_str: str) -> STR_OR_RESPONSE_TYPE:
        """Run a custom query."""
        try:
            # Przygotuj kontekst z feedbacku
            feedback_context = ""
            if self.advanced_rag:
                similar_feedback = self.advanced_rag.feedback_db.get_similar_feedback(query_str)
                if similar_feedback:
                    feedback_context = self._create_feedback_context(similar_feedback)
            
            # Przygotuj prompt z kontekstem
            enhanced_prompt = f"{self.system_prompt}\n\nFeedback context:\n{feedback_context}"
            
            # Pobierz odpowiednie chunki z Advanced RAG
            relevant_chunks = []
            if self.advanced_rag:
                # Rozszerz zapytanie
                expanded_queries = self.advanced_rag.query_expansion_db.expand_query(query_str)
                
                # Zbierz chunki z rozszerzonych zapytań
                for q in expanded_queries:
                    chunks = self.advanced_rag.dynamic_chunking_db.collection.query(query_texts=[q])['documents']
                    relevant_chunks.extend(chunks)
                
                # Rerankuj chunki
                if relevant_chunks:
                    ranked_chunks = self.advanced_rag.reranking_db.rerank_results(query_str, relevant_chunks)
                    # Dodaj rerankowane chunki do kontekstu
                    enhanced_prompt += "\n\nRelevant context:\n" + "\n".join(ranked_chunks)
            
            # Generuj odpowiedź z użyciem LLM
            if isinstance(self.llm, LLM):
                messages = [
                    ChatMessage(role=MessageRole.SYSTEM, content=enhanced_prompt),
                    ChatMessage(role=MessageRole.USER, content=query_str),
                ]
                
                # Jeśli mamy chunki, dodaj je jako kontekst
                if relevant_chunks:
                    messages.append(ChatMessage(
                        role=MessageRole.SYSTEM,
                        content="Use the following context to answer the question:\n" + "\n".join(relevant_chunks)
                    ))
                
                try:
                    chat_response = self.llm.chat(messages)
                    #print(f"Debug - Response type: {type(chat_response)}")
                    #print(f"Debug - Response attributes: {dir(chat_response)}")
                    
                    # Obsługa odpowiedzi w formacie ChatResponse
                    if hasattr(chat_response, 'message'):
                        return str(chat_response.message.content)
                    elif hasattr(chat_response, 'content'):
                        return str(chat_response.content)
                    elif hasattr(chat_response, 'text'):
                        return str(chat_response.text)
                    elif hasattr(chat_response, 'raw'):
                        # Obsługa surowej odpowiedzi
                        raw_response = chat_response.raw
                        if isinstance(raw_response, dict):
                            if 'choices' in raw_response:
                                return str(raw_response['choices'][0]['message']['content'])
                            elif 'text' in raw_response:
                                return str(raw_response['text'])
                        return str(raw_response)
                    else:
                        return str(chat_response)
                except Exception as e:
                    print(f"Error processing LLM response: {e}")
                    print(f"Debug - Response object: {chat_response}")
                    return ""
            
            return ""
            
        except Exception as e:
            print(f"Error in custom_query: {e}")
            return ""

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
            return self.advanced_rag.provide_feedback(feedback_data)
        return False
    
#reference code: https://github.com/run-llama/llama_index/issues/14343