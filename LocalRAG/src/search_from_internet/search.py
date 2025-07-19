from llama_index.core.tools import FunctionTool
from llama_index.core.memory.chat_memory_buffer import ChatMemoryBuffer
from llama_index.core.tools import QueryEngineTool, ToolMetadata
import datetime
import wikipedia
from .llm_query_engine import LLMQueryEngine, ChatHistoryType
from .google_search import GoogleSearchJsonAPI, GoogleSearchWithSerpAPI
from .exchange_rate import ExchangeRate
from .stock_fetcher import StockFetcher
from ..get_vector_db import get_advanced_vector_db
from ..config import MODEL, MODEL_EMBEDDINGS
from typing import List

from ..utils import LLMProvider
from ..utils.local_database_search import search_local_database
from ..utils.simple_logged_agent import SimpleLoggedAgent

llm, isFormatted = LLMProvider.getLLM(model = MODEL)
memory = ChatMemoryBuffer.from_defaults(chat_history=[], llm=llm)

advanced_db = get_advanced_vector_db("advanced_search", MODEL_EMBEDDINGS)

def google_search(query):
    """Perform a Google search"""
    try:
        print(f"Using Google for {query}")
        llm, _ = LLMProvider.getLLM(MODEL)
        search = GoogleSearchJsonAPI(llm = (llm, False), collection_name = "google_search", embedding_model = MODEL_EMBEDDINGS).search(query)
        return search
    except Exception as e:
        print(e)
        return f"No search results found for the query '{query}'"

def google_search_serpapi(query):
    """Perform a Google search"""
    try:
        print(f"Using Google for {query}")
        llm, _ = LLMProvider.getLLM(MODEL)
        search = GoogleSearchWithSerpAPI(llm = (llm, False), collection_name = "google_search", embedding_model = MODEL_EMBEDDINGS).search(query)
        return search
    except Exception as e:
        print(e)
        return f"No search results found for the query '{query}'"

def wikipedia_search(query):
    """Perform a Wikipedia search"""
    try:
        print(f"Using Wikipedia for {query}")
        page = wikipedia.page(query, auto_suggest = False)
        summary = wikipedia.summary(query, sentences = 5, auto_suggest = False)
        return f"Wikipedia article: {page.title}\nSummary: {summary}\nURL: {page.url}"
    except Exception as e:
        print(e)
        return f"No Wikipedia page found for the query '{query}'"
    
def exchange_search(query):
    """Perform a search for exchange rate"""
    try:
        print(f"Using exchange rate for {query}")
        llm, _ = LLMProvider.getLLM(MODEL)
        exchange = ExchangeRate(llm = (llm, False), collection_name ="exchange_rate", embedding_model = MODEL_EMBEDDINGS)
        return exchange.search(query)
    except Exception as e:
        print(e)
        return f"No exchange rate found for the query '{query}'"
    
def stock_search(query):
    """Perform a search for stock company or raw material"""
    try:
        print(f"Using stock search for {query}")
        llm, _ = LLMProvider.getLLM(MODEL)
        stock = StockFetcher(llm = (llm, False), collection_name = "stock_search", embedding_model = 'nomic-embed-text')
        return stock.search(query)
    except Exception as e:
        print(e)
        return f"No stock found for the query '{query}'"


def provide_feedback(query: str, response: str, score: int, feedback_text: str = ""):
    """
    Provide feedback on a search response
    Args:
        query (str): Original query
        response (str): Response that was given
        score (int): Feedback score (1-5)
        feedback_text (str, optional): Additional feedback text
    """
    try:
        feedback_data = {
            "query": query,
            "response": response,
            "score": score,
            "feedback_text": feedback_text,
            "timestamp": datetime.datetime.now().isoformat()
        }
        advanced_db['feedback'].store_feedback(feedback_data)
        return True
    except Exception as e:
        print(f"Error storing feedback: {e}")
        return False

internet_search_tool = FunctionTool.from_defaults(google_search_serpapi, 
                                                name = "internet_search", 
                                                description = "Perform a Google search about a topic")

wikipedia_search_tool = FunctionTool.from_defaults(wikipedia_search,
                                                name = "wikipedia_search", 
                                                description = "Perform a Wikipedia search about a topic")

exchange_search_tool = FunctionTool.from_defaults(exchange_search,
                                                name = "exchange_search", 
                                                description = "Perform a search for exchange rate")

stock_search_tool = FunctionTool.from_defaults(stock_search,
                                                name = "stock_search", 
                                                description = "Perform a search for stock company or raw material")

feedback_tool = FunctionTool.from_defaults(provide_feedback,
                                         name = "provide_feedback",
                                         description = "Provide feedback for search results")

local_database_search_tool = FunctionTool.from_defaults(search_local_database,
                                                       name = "local_database_search",
                                                       description = "Search for information in the local database")

def searchToUser(query:str, max_iterations: int = 50, history: List[ChatHistoryType] = []):
    try:
        agent = SimpleLoggedAgent(
            tools = [
                QueryEngineTool(
                    query_engine = LLMQueryEngine(
                        model = llm, 
                        collection_name="generic_llm", 
                        embedding_model='nomic-embed-text', 
                        history=history,
                        use_feedback=True,
                        enable_query_expansion=False  # Disable for faster performance
                    ),
                    metadata = ToolMetadata(
                        name = "generic_llm",
                        description = str(LLMQueryEngine.__doc__),
                    ),
                ),
                internet_search_tool, 
                wikipedia_search_tool,
                exchange_search_tool,
                stock_search_tool,
                local_database_search_tool
            ],
            llm = llm,
            memory = memory,
            system_prompt = f"""
            Jesteś inteligentnym asystentem do wyszukiwania informacji, który działa zgodnie z metodą ReAct.

            Zawsze postępuj według poniższych zasad:
            **Nie wolno zmieniać pytania użytkownika w `query`.**

            1. Jeśli znasz odpowiedź i jest ona aktualna — użyj tylko `generic_llm`.
            Jeśli użytkownik zadaje ogólne pytanie (np. o Twoje możliwości, Twoją tożsamość, powitanie itp.), odpowiedz od razu przy pomocy Final Answer, bez wykonywania żadnej akcji i bez używania narzędzi.
            Nie szukaj dodatkowego kontekstu i nie zadawaj dodatkowych pytań sam sobie.

            2. Jeśli nie wiesz — wybierz odpowiednie narzędzie w zależności od pytania:

            - 📰 Jeśli użytkownik pyta o **najnowsze informacje** (np. polityka, sport, wydarzenia) — użyj `internet_search`.
            `query` musi być dokładnym pytaniem użytkownika w języku polskim zachowując poprawną składnię językową.

            - 📚 Jeśli użytkownik szuka **ogólnej wiedzy** — użyj `wikipedia_search`.

            - 💱 Jeśli użytkownik pyta o **kursy walut** — użyj `exchange_search`.
            `query` to kod waluty: np. `USD`, `EUR`, `PLN`.
            **Nie używaj tego narzędzia do surowców ani akcji.**

            - 📈 Jeśli użytkownik pyta o **kursy akcji lub surowców** — użyj `stock_search`.
            `query` musi być tylko:
            - nazwą firmy (np. `Apple`)
            - lub nazwą surowca po angielsku (np. `Gold`)
            - bez dodatkowych słów (np. "firma", "akcje", "spółka", "kurs").

            - 📁 Jeśli użytkownik pyta o **informacje z lokalnych dokumentów** lub ich summaryzacje — użyj `local_database_search`.
            `query` powinno być dokładnym pytaniem użytkownika.

            📌 Zasady ogólne:
            - Nigdy nie używaj więcej niż jednego narzędzia.
            - Nie używaj `generic_llm`, jeśli informacja może być nieaktualna.
            - Jeśli użyjesz narzędzia i otrzymasz wynik — od razu go zwróć, bez komentarzy, opinii czy tłumaczeń.
            - Nie zmieniaj pytania użytkownika w `query`.
            - Nie używaj narzędzi, jeśli nie są potrzebne.

            ⚙️ Metodologia pracy:
            - Po każdym Thought MUSISZ napisać albo Action, albo Final Answer — nigdy nie kończ tylko na Thought.
            - Jeśli użyjesz Action, po Observation przejdź od razu do Final Answer — nie wykonuj kolejnych akcji.
            - Nigdy nie zadawaj pytań sam sobie.
            - Jeśli użytkownik zadaje powitanie, ogólne pytanie, pytanie o Ciebie lub Twoje możliwości — od razu użyj Final Answer, bez narzędzi.

            Aktualna data: {{datetime.now}}.
            Twoja historia: {{historyContent}}.
            Jeżeli historia nie jest pusta, możesz dodać ją do odpowiedzi, aby poprawić jakość odpowiedzi.

            Zabronione:
            - NIE zwracaj schematów JSON, obiektów JSON ani innego ustrukturyzowanego formatu danych.
            - NIE zwracaj bloków kodu ani formatowania markdown.
            - NIE generuj żadnych prefixów typu 'assistant:', 'answer:' — tylko czysty tekst.

            Format odpowiedzi:
            {{
                "thought": "Twoje przemyślenie",
                "action": "Action[tool_name('argument')]" | "brak akcji",
                "observation": "Twoja obserwacja", # tylko jeśli używasz Action
                "final_answer": "Twoja ostateczna odpowiedź"
            }}
            """,
            max_iterations = max_iterations,
            verbose = True
        )

        try:
            print("\n=== Executing Agent Query ===")
            response = agent.query(query)
            return response
        except Exception as e:
            print("\n=== Agent Error ===")
            print(f"Error during agent execution: {type(e).__name__}")
            print(f"Error message: {str(e)}")
            print(f"Error location: {e.__traceback__.tb_frame.f_code.co_filename}:{e.__traceback__.tb_lineno}")
            raise e
    except Exception as e:
        print("\n=== General Error ===")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        return e
