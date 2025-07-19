import yfinance as yf
import datetime
import json
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from ..advanced_rag import AdvancedRAG
from ..utils import LLMProvider
import ast

class StockFetcher:
    def __init__(self, llm, collection_name: str = None, embedding_model: str = None):
        self.model, self.isFormatted = llm
        
        if collection_name and embedding_model:
            self.embedding, self.isEFormatted = LLMProvider.getLLM(embedding_model)
            self.advanced_rag = AdvancedRAG(collection_name, embedding_model)
            print("AdvancedRAG utworzony")
        else:
            self.advanced_rag = None

    def search(self, company_name: str):
        """Główna metoda wyszukiwania akcji/surowców."""
        print(f"Szukam informacji o: {company_name}")
        
        # Pobierz kontekst z Advanced RAG jeśli dostępny
        context = ""
        if self.advanced_rag:
            try:
                similar_responses = self.advanced_rag.feedback_db.get_similar_responses(company_name)
                response_context = self._create_response_context(similar_responses)
                
                if response_context:
                    #print("response_context ",response_context)
                    context += response_context + "\n"
                    print(f"Dodano kontekst z odpowiedzi: {len(similar_responses)} elementów")
                    
                if context.strip():
                    print(f"Łączny kontekst: {len(context)} znaków")
                else:
                    print("Brak kontekstu z Advanced RAG")
            except Exception as e:
                print(f"Błąd podczas pobierania kontekstu: {e}")
                context = ""

        # Sprawdź czy symbol istnieje bezpośrednio
        try:
            search = yf.Search(company_name)
        except yf.exceptions.YFRateLimitError as e:
            return "Za dużo zapytań, spróbuj ponownie później."
        original_name = company_name
        corrected_name = ""
        
        if not search.quotes:
            print(f"Nie znaleziono bezpośrednio '{company_name}', próbuję poprawić nazwę...")
            # Jeśli nie znaleziono, spróbuj poprawić nazwę używając AI z kontekstem
            max_attempts = 3
            for attempt in range(max_attempts):
                # Przekaż kontekst do AI
                corrected_name = self.correctName(company_name, context)
                if corrected_name == company_name:
                    print(f"AI nie zaproponowało korekty, przerywam próby")
                    break
                    
                search = yf.Search(corrected_name)
                if search.quotes:
                    print(f"Znaleziono po korekcie: {corrected_name}")
                    company_name = corrected_name  # Użyj poprawionej nazwy
                    break
                else:
                    print(f"Próba {attempt + 1}/{max_attempts}: '{corrected_name}' też nie znaleziona")
                    if self.advanced_rag:
                        self._store_interaction(original_name, corrected_name, False, corrected_name)
            
            if not search.quotes:
                error_msg = f"Nie udało się znaleźć informacji o '{original_name}'"
                if corrected_name and corrected_name != original_name:
                    error_msg += f" ani o '{corrected_name}'"
                print(error_msg)
                return {"error": error_msg}

        # Pobierz dane o akcjach
        try:
            symbol = search.quotes[0].get('symbol')
            print(f"Pobieram dane dla symbolu: {symbol}")
            response = self.fetch_data(symbol)
            
            if response and self.advanced_rag:
                is_correct = self._validate_response(original_name, response)
                self._store_interaction(original_name, response, is_correct, corrected_name)
            
            return response
            
        except Exception as e:
            error_msg = f"Błąd podczas pobierania danych: {e}"
            print(error_msg)
            return {"error": error_msg}

    def fetch_data(self, stock_symbol: str = None):
        """Pobiera dane o akcjach dla danego symbolu."""
        if not stock_symbol:
            return None
        try:
            data = yf.Ticker(stock_symbol).history(period="1d")
            if data.empty:
                return None
            return {
                "stock": f'"{stock_symbol.upper()}"',
                "price": f'"{data["Close"].iloc[0]:.2f}"'
            }
        except Exception as e:
            print(f"Błąd podczas pobierania danych dla {stock_symbol}: {e}")
            return None

    def correctName(self, query: str, context: str = ""):
        """Poprawia nazwę firmy/surowca używając AI z kontekstem."""
        search = yf.Search(query)
        if search.quotes:
            return query
        
        # Przygotuj system prompt z kontekstem
        system_content = """
        Zwróć tylko nazwę firmy lub surowca w języku angielskim.
        Nie dodawaj słów takich jak "price", "kurs", "akcje" ani tłumaczeń.
        
        Przykłady poprawnych odpowiedzi:
            Apple
            Tesla
            Microsoft
            Gold
            Silver
            Iron
            Platinum
            Nvidia

        Przykłady błędnych odpowiedzi:
            Apple price
            Kurs Tesla
            Akcje Microsoft
            Złoto
            Srebro
        """
        
        # Dodaj kontekst jeśli dostępny
        if context.strip():
            system_content += f"\n\nKontekst z poprzednich interakcji:\n{context}"
            system_content += "\nWykorzystaj ten kontekst do lepszego zrozumienia zapytania."
            system_content += "\nJeżeli status jest niepowodzenie, to popraw nazwę tak, aby się zgadzała z nazwą firmy lub surowca."
        
        #print("system_content for correct_name ",system_content)
        # Użyj AI do korekty nazwy
        messages = [
            ChatMessage(role = MessageRole.SYSTEM, content = system_content),
            ChatMessage(role = MessageRole.USER, content = query)
        ]
        
        try:
            response = self.model.chat(messages)
            corrected_name = response.message.content.strip()
            print(f"AI poprawiło '{query}' na '{corrected_name}'" + (" (z kontekstem)" if context.strip() else ""))
            return corrected_name
        except Exception as e:
            print(f"Błąd podczas korekty nazwy: {e}")
            return query

    def _store_interaction(self, query: str, response: str, is_correct: bool, corrected_name: str = ""):
        """Zapisuje interakcję do bazy danych."""
        if not self.advanced_rag:
            return
        
        try:
            response_data = {
                "query": str(query),
                "response": str(response),
                "was_successful": "true" if is_correct else "false",
                "timestamp": datetime.datetime.now().isoformat(),
                "type": "response"
            }
            
            if corrected_name and corrected_name != query:
                response_data["corrected_name"] = str(corrected_name)
                
            self.advanced_rag.feedback_db.store_response(response_data)
            
            if corrected_name and corrected_name != query:
                self.advanced_rag.feedback_db.store_correction({
                    "original_name": str(query),
                    "corrected_name": str(corrected_name),
                    "timestamp": datetime.datetime.now().isoformat(),
                    "type": "correction"
                })
        except Exception as e:
            print(f"Błąd podczas zapisywania: {e}")
            
    def _validate_response(self, query: str, response: dict) -> bool:
        """Sprawdza czy odpowiedź jest poprawna."""
        if not response:
            return False
        try:
            symbol = response.get('stock', '').strip('"')
            if not symbol:
                return False
                
            # Sprawdź czy symbol istnieje
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            query_lower = query.lower()
            if 'longName' in info:
                return query_lower in info['longName'].lower() or query_lower in symbol.lower()
            return query_lower in symbol.lower()
        except:
            return False

    def _create_response_context(self, similar_responses: list) -> str:
        """Tworzy kontekst z poprzednich odpowiedzi."""
        if not similar_responses:
            return ""
        context = "Poprzednie odpowiedzi:\n"
        for response in similar_responses[:3]:  # Ograniczamy do 3 najlepszych
            potential_stock = response['response']
            context += f"- Pytanie: {response['query']}\n"
            
            # response['response'] jest stringiem, nie listą
            # Sprawdź czy to jest słownik w formacie string
            try:
                if isinstance(potential_stock, str):
                    # Spróbuj sparsować jako słownik JSON
                    if potential_stock.startswith('{') and potential_stock.endswith('}'):
                        try:
                            parsed_response = ast.literal_eval(potential_stock)
                            parsed_response = {k: v.strip('"') for k, v in parsed_response.items()}
                            
                            if isinstance(parsed_response, dict) and 'stock' in parsed_response:
                                context += f"  Odpowiedź: {parsed_response['stock']}\n"
                            else:
                                context += f"  Odpowiedź: {potential_stock}\n"
                        except json.JSONDecodeError:
                            # Jeśli JSON jest niepoprawny, użyj jako string
                            context += f"  Odpowiedź: {potential_stock}\n"
                    else:
                        context += f"  Odpowiedź: {potential_stock}\n"
                else:
                    # Jeśli response nie jest stringiem, spróbuj bezpośrednio
                    if isinstance(response['response'], dict) and 'stock' in response['response']:
                        context += f"  Odpowiedź: {response['response']['stock']}\n"
                    else:
                        context += f"  Odpowiedź: {str(response['response'])}\n"
            except Exception as e:
                # Jeśli cokolwiek pójdzie nie tak, użyj jako string
                print(f"Błąd podczas parsowania response: {e}")
                context += f"  Odpowiedź: {str(response['response'])}\n"
            
            status = "Sukces" if response.get('was_successful') else "Niepowodzenie"
            context += f"  Status: {status}\n"
        return context
