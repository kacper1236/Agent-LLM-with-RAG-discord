from llama_index.core.agent.react.base import ReActAgent
from llama_index.core.tools import FunctionTool
from llama_index.core.memory.chat_memory_buffer import ChatMemoryBuffer
from llama_index.llms.ollama import Ollama
from llama_index.core.tools import QueryEngineTool, ToolMetadata
import datetime
import wikipedia
from .llm_query_engine import LLMQueryEngine
from .google_search import GoogleSearch
from .exchange_rate import exchangeRate
from .stock_fetcher import StockFetcher
from ..get_vector_db import get_advanced_vector_db

model = "llama3.1:8b"
llm = Ollama(model = model)
memory = ChatMemoryBuffer.from_defaults(chat_history=[], llm=llm)

advanced_db = get_advanced_vector_db("advanced_search", model)

def google_search(query):
    """Perform a Google search"""
    try:
        print(f"Using Google for {query}")
        search = GoogleSearch(local_model = model).search(query)
        return search
    except Exception as e:
        print(e)
        return f"No search results found for the query '{query}'"

def wikipedia_search(query):
    """Perform a Wikipedia search"""
    try:
        print(f"Using Wikipedia for {query}")
        page = wikipedia.page(query)
        summary = wikipedia.summary(query, sentences=5, auto_suggest=False)
        return f"Wikipedia article: {page.title}\nSummary: {summary}\nURL: {page.url}"
    except Exception as e:
        print(e)
        return f"No Wikipedia page found for the query '{query}'"
    
def exchange_search(query):
    """Perform a search for exchange rate"""
    try:
        print(f"Using exchange rate for {query}")
        exchange = exchangeRate(collection_name = "exchange_rate", embedding_model = 'nomic-embed-text')
        return exchange.search(query)
    except Exception as e:
        print(e)
        return f"No exchange rate found for the query '{query}'"
    
def stock_search(query):
    """Perform a search for stock company or raw material"""
    try:
        print(f"Using stock search for {query}")
        stock = StockFetcher(collection_name="stock_search", embedding_model='nomic-embed-text')
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

internet_search_tool = FunctionTool.from_defaults(google_search, 
                                                name = "internet_search", 
                                                description = "use this to search about a topic on the internet")

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

def searchToUser(query:str, max_iterations: int = 50):
    try:
        agent = ReActAgent.from_tools(
            tools = [
                QueryEngineTool(
                    query_engine = LLMQueryEngine(llm = llm, collection_name="generic_llm", embedding_model='nomic-embed-text'),
                    metadata = ToolMetadata(
                        name = "generic_llm",
                        description = str(LLMQueryEngine.__doc__),
                    ),
                ),
                internet_search_tool, 
                wikipedia_search_tool,
                exchange_search_tool,
                stock_search_tool,
                feedback_tool
            ],
            llm = llm,
            system_prompt = f"""
            Jesteś inteligentnym asystentem pomagającym w wyszukiwaniu informacji.
            - Jeśli użytkownik pyta o wiedzę **którą wiesz i jest aktualna**, to użyj `knowledge_tool`.
                Jeśli używasz `knowledge_tool`, upewnij się, że **zadajesz to samo pytanie**, które zadał użytkownik.
            - Jeśli nie wiesz, to wykonaj jedną z poniższych poleceń.
                - Jeśli użytkownik pyta o **najnowsze informacje** (np. polityka, sport, wydarzenia), używaj `internet_search`.
                    Jeśli używasz `internet_search`, upewnij się, że **query jest poprawnym, pełnym pytaniem** w języku użytkownika.
                - Jeśli użytkownik szuka **ogólnej wiedzy**, użyj `wikipedia_search`.
                - Jeśli użytkownik pyta o **kursy walut**, użyj `exchange_search`.
                    Wykorzystuj tę metodę do wyszukiwania odpowiedniej waluty.
                    Przykład: PLN, USD, EUR, GBP itp.
                    **Nie wolno** wyszukiwać ci cen surowców ani akcji w tej metodzie.
                    Podczas używania tego narzędzia **nie wolno** zmieniać ci pytania.
                - Jeśli użytkownik pyta o kurs akcji firmy lub wartość, użyj funkcji `stock_search`.
                    Zwróć tylko nazwę firmy, bez dodatkowych słów, zdań ani znaków interpunkcyjnych.
                    Nie dodawaj przedrostków takich jak "firma", "spółka" itp.
                        Przykłady:
                        ✅ Apple
                        ❌ Firma Apple Inc.
                        ❌ Apple jest spółką technologiczną.

                    Jeśli użytkownik pyta o kurs surowców, również użyj `stock_search`.
                    Zwróć tylko nazwę surowca w **języku angielskim**.
                    Nie dodawaj słów typu "cena" ani tłumaczenia na inne języki.
                        Przykłady:
                        ✅ Gold
                        ❌ Cena złota
                        ❌ Złoto

                    Dozwolonym jest, abyś odpowiadał użytkownikowi w innej walucie niż jest zapytanie. Najlepiej podawaj w $.
                        Po otrzymaniu wyniku, napisz go.
                    **Nie szukaj ceny surowca w `exchange_search`.**

                    
            - Jeśli użytkownik chce wyrazić opinię o jakości odpowiedzi, użyj `provide_feedback`.
                Feedback powinien być liczbą od 1 do 5, gdzie:
                - 1 oznacza bardzo złą odpowiedź
                - 5 oznacza bardzo dobrą odpowiedź

            Jeżeli otrzymałeś odpowiedź od funkcji, od razu ją zwróć.
            Nie twórz dodatkowych detali.
            Nie dodawaj dodatkowych zmiennych. Używaj tylko i wyłącznie 'query'.
            Unikaj literówek i dziwnych znaków w `query`.
            Nie używaj narzędzi, których nie potrzebujesz.
            Aktualna data: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}.
            Jeżeli odpowiedź **jest przedawniona, stara lub nieaktualna**, **nie używaj `generic_llm`**.
            Jeżeli możesz użyć innego narzędzia do znalezienia odpowiedzi, to zrób to i nie używaj `generic_llm`.
            """,
            memory = memory,
            max_iterations = max_iterations,
            verbose = True
        )

        try:
            print("\n=== Executing Agent Query ===")
            response = agent.query(query)
            print("\n=== Agent Response ===")
            return response
        except Exception as e:
            print("\n=== Agent Error ===")
            print(f"Error during agent execution: {type(e).__name__}")
            print(f"Error message: {str(e)}")
            print(f"Error location: {e.__traceback__.tb_frame.f_code.co_filename}:{e.__traceback__.tb_lineno}")
            raise 

    except Exception as e:
        print("\n=== General Error ===")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        return e
