import yfinance as yf
import ollama
import datetime
from ..advanced_rag import AdvancedRAG

class StockFetcher:
    local_model: str

    def __init__(self, local_model = 'llama3.1:8b', collection_name: str = None, embedding_model: str = None):
        self.local_model = local_model
        print(f"Inicjalizacja StockFetcher:")
        print(f"- Model: {local_model}")
        print(f"- Collection name: {collection_name}")
        print(f"- Embedding model: {embedding_model}")
        
        if collection_name and embedding_model:
            print("Tworzę instancję AdvancedRAG")
            self.advanced_rag = AdvancedRAG(collection_name, embedding_model)
            print("AdvancedRAG utworzony")
        else:
            print("Brak parametrów do inicjalizacji AdvancedRAG")
            self.advanced_rag = None

    def fetch_data(self, stock_symbol: str = None):
        if not stock_symbol:
            return None
        data = yf.Ticker(stock_symbol).history(period="1d")
        return f"Stock: {stock_symbol.lower()}\nClose price: {data['Close'].iloc[0]}$"
    
    def correctName(self, query:str):
        search = yf.Search(query)
        if search.quotes == []:
            response = ollama.chat(self.local_model, [{'role': 'system', 'content': """
            Return only the name of the raw material in **English**.
            Do not add words like "price" or translations into other languages.
                                                       
            Good Examples:
                Gold
                Silver
                Iron
                Platinium
    
            Bad examples:
                Gold price
                Silver price
                Aktualny kurs żelaza
                Złoto
                Srebro
            """}, {'role': 'user', 'content': query}], stream = False)

            return response.message.content.lstrip()
        
        return query

    def _store_interaction(self, query: str, response: str, is_correct: bool, corrected_name: str = ""):
        """Zapisuje interakcję (odpowiedź, feedback i korektę) do bazy danych."""
        if not self.advanced_rag:
            print("Advanced RAG nie jest zainicjalizowany")
            return
        
        print(f"Zapisuję interakcję:")
        print(f"- Query: {query}")
        print(f"- Response: {response}")
        print(f"- Is correct: {is_correct}")
        print(f"- Corrected name: {corrected_name}")
        
        try:
            if corrected_name == "":
                print("Zapisuję odpowiedź bez korekty nazwy")
                result = self.advanced_rag.feedback_db.store_response({
                    "query": query,
                    "response": response,
                    "was_successful": is_correct,
                    "timestamp": datetime.datetime.now().isoformat()
                })
                print(f"Wynik zapisu odpowiedzi: {result}")
            else:
                print("Zapisuję odpowiedź z korektą nazwy")
                result1 = self.advanced_rag.feedback_db.store_response({
                    "query": query,
                    "response": response,
                    "was_successful": is_correct,
                    "timestamp": datetime.datetime.now().isoformat(),
                    "corrected_name": corrected_name if corrected_name != query else None
                })
                print(f"Wynik zapisu odpowiedzi: {result1}")
                
                print("Zapisuję feedback")
                result2 = self.advanced_rag.feedback_db.store_feedback({
                    "query": query,
                    "response": response,
                    "score": 5 if is_correct else 1,
                    "feedback_text": "Automatic validation",
                    "timestamp": datetime.datetime.now().isoformat()
                })
                print(f"Wynik zapisu feedbacku: {result2}")

                if corrected_name and corrected_name != query:
                    print("Zapisuję korektę nazwy")
                    result3 = self.advanced_rag.feedback_db.store_correction({
                        "original_name": query,
                        "corrected_name": corrected_name,
                        "timestamp": datetime.datetime.now().isoformat()
                    })
                    print(f"Wynik zapisu korekty: {result3}")
        except Exception as e:
            print(f"Błąd podczas zapisywania: {e}")
            
    def _validate_response(self, query: str, response: str) -> bool:
        """Sprawdza czy odpowiedź jest poprawna dla danego zapytania."""
        try:
            # Wyciągnij symbol z odpowiedzi
            symbol = response.split('\n')[0].split(': ')[1].strip()
            
            # Sprawdź czy symbol istnieje
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Sprawdź czy nazwa lub symbol pasują do zapytania
            query_lower = query.lower()
            if 'longName' in info:
                return query_lower in info['longName'].lower() or query_lower in symbol.lower()
            return query_lower in symbol.lower()
        except:
            return False

    def _create_feedback_context(self, similar_feedback: list) -> str:
        """Tworzy kontekst z podobnych feedbacków."""
        context = "Based on similar previous interactions:\n"
        for feedback in similar_feedback:
            context += f"- Question: {feedback['query']}\n"
            context += f"  Score: {feedback['score']}/5\n"
            if feedback.get('feedback_text'):
                context += f"  Feedback: {feedback['feedback_text']}\n"
        return context

    def _create_response_context(self, similar_responses: list) -> str:
        """Tworzy kontekst z poprzednich odpowiedzi."""
        context = "Previous responses to similar questions:\n"
        for response in similar_responses:
            context += f"- Question: {response['query']}\n"
            context += f"  Response: {response['response']}\n"
            if response.get('was_successful'):
                context += "  Result: Successful\n"
            else:
                context += "  Result: Failed\n"
        return context
            
    def search(self, company_name: str):
        # Pobierz podobne feedbacki i poprzednie odpowiedzi jeśli Advanced RAG jest dostępny
        feedback_context = ""
        previous_responses = ""
        if self.advanced_rag:
            similar_feedback = self.advanced_rag.feedback_db.get_similar_feedback(company_name)
            if similar_feedback:
                feedback_context = self._create_feedback_context(similar_feedback)
            
            # Pobierz poprzednie odpowiedzi na podobne pytania
            similar_responses = self.advanced_rag.feedback_db.get_similar_responses(company_name)
            if similar_responses:
                previous_responses = self._create_response_context(similar_responses)

        # Dodaj kontekst z feedbacku i poprzednich odpowiedzi do system prompt
        system_prompt = """
        Jesteś ekspertem od akcji i surowców. 
        Twoim zadaniem jest znalezienie odpowiedniej nazwy dla zapytania użytkownika.
        Jeżeli dostaniesz pełne zdanie, zwróć nazwę firmy lub waluty w **języku angielskim**.

        Przykłady dobrych zapytań:
        - Apple
        - Tesla
        - Amazon
        - Gold
        - Silver
        - Iron
        - Intel
        - Nvidia
        
        Zwróć dokładnie nazwę, nic więcej.
        """

        if feedback_context:
            system_prompt += f"\n\nKontekst z poprzednich interakcji:\n{feedback_context}"
        
        if previous_responses:
            system_prompt += f"\n\nPoprzednie odpowiedzi na podobne pytania:\n{previous_responses}"

        # Sprawdź czy symbol istnieje
        search = yf.Search(company_name)
        original_name = company_name
        corrected_name:str = ""
        
        if search.quotes == []:
            # Jeśli nie znaleziono, spróbuj poprawić nazwę
            while True:
                corrected_name = self.correctName(company_name)
                search = yf.Search(corrected_name)
                if search.quotes != []:
                    break

                self._store_interaction(original_name, corrected_name, False, corrected_name)
                
        # Pobierz dane
        response = self.fetch_data(search.quotes[0].get('symbol')) if search.quotes else None

        # Sprawdź poprawność odpowiedzi i zapisz ją
        if response and self.advanced_rag:
            is_correct = self._validate_response(original_name, response)
            self._store_interaction(original_name, response, is_correct, corrected_name)

        return response
