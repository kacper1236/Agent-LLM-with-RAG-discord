import requests
import datetime

from llama_index.core.agent import FunctionCallingAgent
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.core.tools import FunctionTool

from ..advanced_rag import AdvancedRAG
from ..utils import LLMProvider

from typing import Optional, Any

def get_exchange_rates(table: str = 'A') -> Optional[Any]:
    """Get exchange rates for a given table."""
    url = f"https://api.nbp.pl/api/exchangerates/tables/{table}?format=json"
    response = requests.get(url)
    return response.json() if response.status_code == 200 else None

def get_currency_rate(currency: str, date: Optional[str] = None, last: Optional[int] = None) -> Optional[Any]:
    """Get the currency rate for a given currency, with optional date or last."""
    if last:
        url = f"https://api.nbp.pl/api/exchangerates/rates/A/{currency}/last/{last}?format=json"
    elif date:
        url = f"https://api.nbp.pl/api/exchangerates/rates/A/{currency}/{date}?format=json"
    else:
        url = f"https://api.nbp.pl/api/exchangerates/rates/A/{currency}?format=json"

    response = requests.get(url)
    return response.json() if response.status_code == 200 else None

def get_gold_price(date: Optional[str] = None) -> Optional[Any]:
    """Get gold price, optionally for a specific date."""
    url = "https://api.nbp.pl/api/cenyzlota"
    if date:
        url += f"/{date}"
    url += "?format=json"

    response = requests.get(url)
    return response.json() if response.status_code == 200 else None


class ExchangeRate():
    def __init__(self, llm, embedding_model: str = None, collection_name: str = None):
        self.llm, self.isFormatted = llm
        if embedding_model:
            self.embedding, self.isEFormatted = LLMProvider.getLLM(embedding_model)
        if collection_name and embedding_model:
            self.advanced_rag = AdvancedRAG(collection_name, embedding_model)
        else:
            self.advanced_rag = None

        # Define tools
        self.tools = [
            FunctionTool.from_defaults(fn=get_exchange_rates),
            FunctionTool.from_defaults(fn=get_currency_rate),
            FunctionTool.from_defaults(fn=get_gold_price),
        ]

        # System prompt setup
        self.system_prompt = (
            "Jesteś profesjonalnym ekspertem od kursów walut. "
            "Twoją rolą jest odpowiedzieć na podstawie pytania o jaką walutę użytkownik pyta.\n"
            "Przykład:\n"
            "- Jaki jest kurs waluty dolara? Użyj get_currency_rate('USD')\n"
            "- Jaki jest kurs złota? Użyj get_gold_price()\n"
            "- Jaki jest kurs waluty euro z dnia 2022-01-01? Użyj get_currency_rate('EUR', date='2022-01-01')\n"
            "- Jaki jest obecny kurs walut? Użyj get_exchange_rates()\n"
            "Jeżeli nie możesz znaleźć odpowiedzi na pytanie, zwróć --N/A--.\n"
            "Obecna data to: " + datetime.datetime.now().strftime("%Y-%m-%d")
        )

        # Setup agent
        self.agent = FunctionCallingAgent.from_tools(
            tools=self.tools,
            llm=self.llm,
            system_prompt=self.system_prompt
        )

    def search(self, query: str = None):
        # Gather RAG context as before (if needed)
        context = ""
        if self.advanced_rag:
            previous_responses = ""
            try:
                similar_responses = self.advanced_rag.feedback_db.get_similar_responses(query)
                if similar_responses:
                    previous_responses = self._create_response_context(similar_responses)
                if previous_responses:
                    context += f"\nPoprzednie odpowiedzi na podobne pytania:\n{previous_responses}"
            except Exception as e:
                print(f"Error getting similar responses: {e}")

        # Run agent
        # NOTE: Attach context to query, or prepend to system prompt, your choice.
        if context:
            prompt = f"{context}\n{query}"
        else:
            prompt = query

        # Now run the agent
        try:
            response = self.agent.chat(prompt)
            
            # Store the response for future feedback analysis
            if self.advanced_rag:
                self.store_response(query, str(response), [])
            
            return response
        except Exception as e:
            print(f"Error in exchange rate search: {e}")
            return f"Error processing exchange rate query: {str(e)}"

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

    def store_response(self, query: str, response: str, tool_results: list):
        """Store the model's response and used tools for future reference."""
        if self.advanced_rag:
            # Convert tool_results to a string to avoid list metadata error
            used_tools_str = ", ".join([res.get('function_name', 'unknown') for res in tool_results]) if tool_results else ""
            
            response_data = {
                "query": str(query),
                "response": str(response),
                "used_tools": used_tools_str,  # Convert to string
                "timestamp": datetime.datetime.now().isoformat(),
                "was_successful": "true",  # Convert to string
                "type": "response"
            }
            return self.advanced_rag.feedback_db.store_response(response_data)
        return False
