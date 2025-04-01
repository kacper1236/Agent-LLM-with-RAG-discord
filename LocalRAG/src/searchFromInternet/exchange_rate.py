import requests
import ollama
import datetime
from ..advanced_rag import AdvancedRAG

class exchangeRate():
    def __init__(self, local_model = 'llama3.1:8b', collection_name: str = None, embedding_model: str = None):
        self.local_model = local_model
        if collection_name and embedding_model:
            self.advanced_rag = AdvancedRAG(collection_name, embedding_model)
        else:
            self.advanced_rag = None

    def get_exchange_rates(self, table='A'):
        url = f"https://api.nbp.pl/api/exchangerates/tables/{table}?format=json"
        response = requests.get(url)
        return response.json() if response.status_code == 200 else None

    def get_currency_rate(self, currency, date=None, last=None):
        if last:
            url = f"https://api.nbp.pl/api/exchangerates/rates/A/{currency}/last/{last}?format=json"
        elif date:
            url = f"https://api.nbp.pl/api/exchangerates/rates/A/{currency}/{date}?format=json"
        else:
            url = f"https://api.nbp.pl/api/exchangerates/rates/A/{currency}?format=json"
        
        response = requests.get(url)
        return response.json() if response.status_code == 200 else None

    def get_gold_price(self, date=None):
        url = "https://api.nbp.pl/api/cenyzlota"
        if date:
            url += f"/{date}"
        url += "?format=json"
        
        response = requests.get(url)
        return response.json() if response.status_code == 200 else None
    
    def search(self, query:str = None):
        # Pobierz podobne feedbacki i poprzednie odpowiedzi jeśli Advanced RAG jest dostępny
        feedback_context = ""
        previous_responses = ""
        if self.advanced_rag:
            similar_feedback = self.advanced_rag.feedback_db.get_similar_feedback(query)
            if similar_feedback:
                feedback_context = self._create_feedback_context(similar_feedback)
            
            # Pobierz poprzednie odpowiedzi na podobne pytania
            similar_responses = self.advanced_rag.feedback_db.get_similar_responses(query)
            if similar_responses:
                previous_responses = self._create_response_context(similar_responses)

        # Dodaj kontekst z feedbacku i poprzednich odpowiedzi do system prompt
        system_prompt = f"""
        Jesteś profesjonalnym ekspertem od kursów walut. 
        Twoją rolą jest odpowiedzieć na podstawie pytania o jaką walutę użytkownik pyta.
        
        Przykład: 
        - Jaki jest kurs waluty dolara?
        Twoją odpowiedzią jest użycie metody `get_currency_rate("USD")`
        Dozwolonym jest użycie metody `get_exchange_rates()`
        
        - Jaki jest kurs złota?
        Twoją odpowiedzią jest użycie metody `get_gold_price()`
        Tej metody możesz użyć **tylko dla złota**.
                                                   
        - Jaki jest kurs waluty euro z dnia 2022-01-01?
        Twoją odpowiedzią jest użycie metody `get_currency_rate("EUR", date="2022-01-01")` Data **musi** być formatu: RRRR-MM-DD
    
        - Jaki jest obecny kurs walut?
        Twoją odpowiedzią jest użycie metody `get_exchange_rates()`
                                                   
        Zwróć wynik w postaci prostej i łatwej do zrozumienia dla użytkownika.
        Zwróć także wynik w złotówkach, jeżeli użytkownik pyta o kurs walut.
        
        Tam gdzie to możliwe, jeżeli użytkownik nie poda daty, użyj obecnej daty.
        Jeżeli nie ma odpowiedniego narzędzia, zwróć None.
        Obecna data to: {datetime.datetime.now().strftime("%Y-%m-%d")}
        """

        if feedback_context:
            system_prompt += f"\n\nKontekst z poprzednich interakcji:\n{feedback_context}"
        
        if previous_responses:
            system_prompt += f"\n\nPoprzednie odpowiedzi na podobne pytania:\n{previous_responses}"

        response = ollama.chat(self.local_model, [
            {'role': 'system', 'content': system_prompt}, 
            {'role': 'user', 'content': query}
        ], tools = [self.get_exchange_rates, self.get_currency_rate, self.get_gold_price], stream = False)
        
        tool_results = []
        for tool_call in response.message.tool_calls:
            function_name = tool_call.function.name
            arguments = tool_call.function.arguments
            result = None

            if function_name == "get_gold_price":
                result = self.get_gold_price()
            elif function_name == "get_currency_rate":
                currency = arguments.get("currency", "USD")
                date = arguments.get("date", None)
                result = self.get_currency_rate(currency, date)
            elif function_name == "get_exchange_rates":
                result = self.get_exchange_rates()

            tool_results.append({
                "function_name": function_name,
                "result": result
            })

        if tool_results:
            formatted_results = "\n".join(
                [f"Funkcja: {res['function_name']}, wynik: {res['result']}" for res in tool_results]
            )
            final_response = ollama.chat(
                self.local_model,
                [
                    {'role': 'system', 'content': "Twoim zadaniem jest przekazanie wyników użytkownikowi w przystępny sposób."},
                    {'role': 'system', 'content': "Odpowiedz na pytanie użytkownika, krótko i zwięźle."},
                    {'role': 'user', 'content': f"Oto wynik operacji:\n{formatted_results}\nOdpowiedz użytkownikowi."}
                ]
            )
            response_text = final_response.message.content

            # Zapisz odpowiedź i feedback jeśli Advanced RAG jest dostępny
            if self.advanced_rag:
                self.store_response(query, response_text, tool_results)
                self.store_feedback(query, response_text)

            return response_text
        else:
            return "Nie znaleziono odpowiedniego narzędzia do odpowiedzi na to pytanie."

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
            context += f"  Used tools: {response['used_tools']}\n"
            if response.get('was_successful'):
                context += "  Result: Successful\n"
            else:
                context += "  Result: Failed\n"
        return context

    def store_response(self, query: str, response: str, tool_results: list):
        """Store the model's response and used tools for future reference."""
        if self.advanced_rag:
            response_data = {
                "query": query,
                "response": response,
                "used_tools": [res['function_name'] for res in tool_results],
                "timestamp": datetime.datetime.now().isoformat(),
                "was_successful": True  # Domyślnie zakładamy sukces, feedback może to zmienić
            }
            return self.advanced_rag.feedback_db.store_response(response_data)
        return False

    def store_feedback(self, query: str, response: str, score: int = 5, feedback_text: str = ""):
        """Store feedback and use it for future responses."""
        if self.advanced_rag:
            feedback_data = {
                "query": query,
                "response": response,
                "score": score,
                "feedback_text": feedback_text,
                "timestamp": datetime.datetime.now().isoformat()
            }
            return self.advanced_rag.provide_feedback(feedback_data)
        return False
