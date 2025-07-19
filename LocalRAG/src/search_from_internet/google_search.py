import requests
from bs4 import BeautifulSoup
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from playwright.sync_api import sync_playwright
import os
import json
import datetime
from html_to_markdown import convert_to_markdown
from langchain_community.document_loaders import PlaywrightURLLoader
import wikipedia
import re
from serpapi.google_search import GoogleSearch

from ..advanced_rag import AdvancedRAG
from ..utils import LLMProvider


class GoogleSearchJsonAPI():
    query: str

    def __init__(self, llm, collection_name: str = None, embedding_model: str = None):
        self.llm, self.isFormatted = llm
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.cse_id = os.getenv("GOOGLE_CUSTOM_SEARCH_ENGINE")
        
        if collection_name and embedding_model:
            self.embedding, self.isEFormatted = LLMProvider.getLLM(embedding_model)
            self.advanced_rag = AdvancedRAG(collection_name, embedding_model)
            print("AdvancedRAG utworzony dla GoogleSearch")
        else:
            self.advanced_rag = None

    def search_with_optimization(self, api_key = "", cse_id = "", query = "", **parameters):
        if api_key == "" or cse_id == "":
            return "Google Tool Search disabled try another tool."
        params = {
            'key': api_key,
            'cx': cse_id,
            'q': query,
            'num': parameters.get('num', 10),
            'start': parameters.get('start', 0),
            'searchType': parameters.get('searchType', None),
            'siteSearch': parameters.get('siteSearch'),
            'fileType': parameters.get('fileType'),
            'dateRestrict': parameters.get('dateRestrict'),
            'sort': parameters.get('sort')
        }
        
        if 'exact_phrase' in parameters:
            params['q'] += f' "{parameters["exact_phrase"]}"'
        
        if 'exclude_words' in parameters:
            params['q'] += f' -{parameters["exclude_words"]}'
        
        if 'required_words' in parameters:
            params['q'] += f' {parameters["required_words"]}'
        
        try:
            response = requests.get("https://www.googleapis.com/customsearch/v1", params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Błąd: {str(e)}")
            if hasattr(e, 'response') and hasattr(e.response, 'status_code') and e.response.status_code == 429:
                return 429
            if hasattr(e, 'response') and hasattr(e.response, 'status_code') and e.response.status_code > 299:
                return "Could not fetch results from Google Search tool."
            return None
        
    def download_text_from_url_classically(self, url):
        response = requests.get(url)
        if not response.ok:
            return ""
        soup = BeautifulSoup(response.text, 'lxml')
        with open("soup.txt", "w", encoding="utf-8") as f:
            f.write(soup.text)
        return convert_to_markdown(soup)
        # possible_containers = ["article", "main", "div", "section"]
        # for container in possible_containers:
        #     main_content = soup.find(container)
        #     if main_content:
        #         return main_content.get_text(separator="\n", strip=True)
        #
        # return soup.get_text(separator="\n", strip=True)
    
    def download_text_from_url_from_js(url):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                response = page.goto(url, wait_until = 'networkidle', timeout= 10000)
                assert response.ok
                
                html_content = response.content()
    
                soup = BeautifulSoup(html_content, 'html.parser')
                
                possible_containers = ["article", "main", "div", "section"]
                for container in possible_containers:
                    main_content = soup.find(container)
                    if main_content:
                        return main_content.get_text(separator="\n", strip=True)
                return "Nie udało się pobrać treści strony."
            except AssertionError:
                return ""
            except Exception as e:
                return f"Error has occur: {e}"
            finally:
                browser.close()

    def download_text_from_url_with_playwright(self, url):
        loader = PlaywrightURLLoader(urls=[url], remove_selectors=[
            # Ogólne struktury
            "header",            # Górny pasek
            "footer",            # Stopka
            "nav",               # Pasek nawigacji
            "aside",             # Dodatkowe panele

            # Wikipedia-specific
            ".mw-editsection",   # Linki "edytuj"
            "sup.reference",     # Przypisy [1], [2]
            ".reflist",          # Lista przypisów na dole
            ".infobox",          # Tabela z prawej (biografia, dane)
            ".mw-sidebar",       # Pasek boczny
            ".toc",              # Spis treści
            ".navbox",           # Panele nawigacyjne na dole (np. "Tesla, Inc.")
            ".hatnote",          # Linki "Zobacz też" nad artykułem
            ".metadata",         # Ukryte dane
            ".sistersitebox",    # Linki do siostrzanych projektów
            ".catlinks",         # Kategorie
            ".mw-jump",          # Skip to content
            ".printfooter",      # Stopka wersji do druku
            ".portal",           # Linki do portali tematycznych
            ".navbar",           # Nawigacja wewnętrzna

            # Ukryte lub techniczne
            "script",
            "style",
            "noscript",
        ])
        documents = loader.load()
        documents[0].page_content = documents[0].page_content.strip()
        return documents[0].page_content if documents else "Nie udało się pobrać treści strony."
    
    def download_text_from_url_with_wikipedia(self, url:str):
        # Wyciągnięcie nazwy artykułu z URL
        article_title = url.split('/')[-1]
        
        # Pobranie treści artykułu z Wikipedii
        contents = []
        try:
            content = wikipedia.search(article_title, results=2, suggestion=False)
            #print(f"Znaleziono artykuły: {content}")
            for i in content:
                contents.append(wikipedia.page(i, auto_suggest=False).content)
            return contents
        except wikipedia.exceptions.PageError:
            return "Nie udało się znaleźć artykułu na Wikipedii."
        except Exception as e:
            return f"Wystąpił błąd: {str(e)}"
    
    def split_text(self, text, max_dl = 2000):
        snippets = []
        words = text.split()
        while words:
            snippets.append(" ".join(words[:max_dl]))
            words = words[max_dl:]
        return snippets

    def total_text_ollama(self, text, link, user_query):
        snippets = self.split_text(text)
        print("snippets", text)
        summaries = []
        
        for snippet in snippets:
            reply = self.llm.chat(messages = [ChatMessage(role=MessageRole.SYSTEM, content=f"""
                <current_date>{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</current_date>
                Analyze the following text and summarize it in a concise way.
                Take into account the context of the user's query.
                Take into account the link to the text.
                Take into account the link with the context of the user's query.
                Try to understand what parts of the text are important and what are not - include only the most important parts related to the user's query and/or link.
                <context>Analyze the text and link to understand the user's query better.</context>
            """), ChatMessage(role=MessageRole.USER, content=f"""
                <text>{snippet}</text>
                <link>{link}</link>
                <user_query>{user_query}</user_query>
            """)])
            print("reply", reply.message.content)
            if reply.message.content is not None:
                print("reply", reply.message.content)
                summaries.append(reply.message.content)
        
        return " ".join(summaries)
    
    def llm_search_engine(self, query: str):
        params = {}
        if self.isFormatted:
            params['format'] = 'json'

        json_response = self.llm.chat(messages=[ChatMessage(role = MessageRole.SYSTEM, content = f"""
        You are a JSON generator. Return ONLY a JSON array (no markdown, no extra text) containing objects with this EXACT structure:
            {{
                "num": number, 
                "start": number,
                "searchType": string,
                "siteSearch": string,
                "fileType": string,
                "dateRestrict": string,
                "sort": string,
                "exact_phrase": string,
                "exclude_words": string,
                "required_words": string                                       
            }}
            You must always return valid JSON fenced by a markdown code block. Do not return any additional text.
            Follow this rules:
            1. Each request must contain ALL of the following fields, even if they are not required - then set them to the default value ("" for strings, 1 for numbers).
            2. The JSON format must be correct - no unnecessary commas and correct syntax.
            3. The num field specifies the number of result pages and MUST always be an integer equal to 3.
            4. The start field specifies the number of start to search pages and MUST be an integer (e.g. 0, 1, 2, 3).
            5. The searchType field MUST be None.
            6. The siteSearch field SHALL be a string and specifies a search for a specific domain. If not specified, set "".
            7. The fileType field MUST be None. 
            8. The dateRestrict field SHALL be a string specifying the time restriction of the results (e.g. d1 - last day, w1 - last week). If not specified, set "".
            9. The sort field SHALL be a string and specifies the method of sorting the results. If not specified, set "". You can use 'date' 
            10. The exact_phrase field MUST be a string and specifies the exact phrase to search for. If not specified, set to "". It must be a words, not a phrase.
            11. The exclude_words field MUST be a string and specifies the words to exclude from the search. If not specified, set to "". 
            12. The required_words field MUST be a string and specifies the required words in the results. If not specified, set to "".
            13. Fields that are empty strings ("") CANNOT be omitted - they must always be present in the query.
            14. Based on the user's query, decide which parameters are ideal for finding information on this topic. 
            15. The query should be optimised to return relevant results in a way that is natural to the user (e.g. searching for definitions rather than academic pages if the user's intent indicates this).
            16. If the user specifies an unusual query, the LLM should adapt it to the most likely search intent.
                                                        
            ACTUAL DATE {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        """),
        ChatMessage(role = MessageRole.USER, content = query)],  **params)
        return json_response.message.content.replace("```json", "").replace("```", "")
    
    def reformulate_query(self, query):
        response = self.llm.chat(messages=[
            ChatMessage(role=MessageRole.SYSTEM, content="Zmieniaj pytanie użytkownika, by było bardziej precyzyjne, zgodnie z jego intencją. Napisz je krótko i zwięźle."),
            ChatMessage(role=MessageRole.SYSTEM, content="Jeżeli pytanie jest trafne i nie wymaga zmian, **nie zmieniaj go**."),
            ChatMessage(role=MessageRole.SYSTEM, content="Jeżeli pytanie jest proste i zrozumiałe, **nie zmieniaj go**."),
            ChatMessage(role=MessageRole.SYSTEM, content=f"Aktualna data: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"),
            ChatMessage(role=MessageRole.USER, content=query)
        ])
        return response.message.content
    
    def search(self, query_user):
        print(f"Wyszukuję informacji o: {query_user}")
        
        # Pobierz kontekst z Advanced RAG jeśli dostępny
        context = ""
        if self.advanced_rag:
            try:
                similar_responses = self.advanced_rag.feedback_db.get_similar_responses(query_user)
                response_context = self._create_response_context(similar_responses)
                
                if response_context:
                    context += response_context + "\n"
                    print(f"Dodano kontekst z odpowiedzi: {len(similar_responses)} elementów")
                    
                if context.strip():
                    print(f"Łączny kontekst: {len(context)} znaków")
                else:
                    print("Brak kontekstu z Advanced RAG")
            except Exception as e:
                print(f"Błąd podczas pobierania kontekstu: {e}")
                context = ""
        
        total_summaries = []
        original_query = query_user
        while True:
            query = query_user
            #query = self.reformulate_query(query_user)
            try:
                json_response = self.llm_search_engine(query)
                search_params:dict = json.loads(json_response.replace("'", '\"'))

                if len(search_params) == 0:
                    continue
                elif len(search_params) >= 1 and search_params.__class__ == list:
                    print("zamiana")
                    search_params = search_params[0]
                print('-----------------')
                print(search_params)
                print('-----------------')
                print(search_params.__class__)
                print('-----------------')

                if search_params['searchType'] == "None" or search_params['searchType'] == "":
                    search_params['searchType'] = None
                if search_params['fileType'] == "" or search_params['fileType'] == "None":
                    search_params['fileType'] = None
                results = self.search_with_optimization(self.api_key, self.cse_id, query, **search_params)
                if results == 429:
                    return "Przekroczono limit zapytań do Google."

                #print("results class", results.__class__)
                #print("results", results)

                if results.__class__ != str:
                    # Sprawdź czy są jakiekolwiek wyniki
                    if 'items' not in results or not results['items']:
                        print("Brak wyników wyszukiwania")
                        total_summaries.append("Nie znaleziono żadnych wyników dla tego zapytania.")
                    else:
                        for item in results['items']:
                            link:str = item['link']
                            banned_links = ['.pdf', 'pdf', '.docx', 'docx', '.doc', 'doc', '.pptx', 'pptx', '.ppt', 'ppt', '.xls', 'xls', '.xlsx', 'xlsx']
                            if any(link.endswith(ext) for ext in banned_links):
                                continue
                            print(f"Przetwarzam: {link}")
                            if re.search(r'wikipedia', link, re.IGNORECASE):
                                text = self.download_text_from_url_with_wikipedia(link)
                            else:
                                text = self.download_text_from_url_with_playwright(link)
                            summary = self.total_text_ollama(text, link, query_user)
                            print("Podsumowanie:")
                            print(summary)
                            total_summaries.append(summary)
                break
            except KeyError as e:
                print(f"KeyError: {e}")
                continue
            except Exception as e:
                print(f"Error: {e}")
                if hasattr(e, 'response') and hasattr(e.response, 'status_code') and e.response.status_code > 299:
                    continue

        # Dodaj kontekst do system prompt jeśli dostępny
        system_content = f"""
        Na podstawie zapytania użytkownika i dołączonych streszczeń tekstów, odpowiedz na pytanie. 
        Odpowiedź musi być, krótka, zwięzła, logiczna i tylko na podstawie tekstów dołączonych.
        Teksty: {' '.join(total_summaries)}
        """
        
        if context.strip():
            system_content += f"\n\nKontekst z poprzednich wyszukiwań:\n{context}"
            system_content += "\nWykorzystaj ten kontekst do lepszego zrozumienia zapytania i unikania błędów z przeszłości."
        
        final_response = self.llm.chat(messages = [
            ChatMessage(role = MessageRole.SYSTEM, content = system_content),
            ChatMessage(role = MessageRole.USER, content = f"query: {query}")
        ]).message.content
        
        # Zapisz wynik wyszukiwania
        if self.advanced_rag:
            is_successful = self._validate_search_response(original_query, final_response, total_summaries)
            self._store_search_interaction(original_query, final_response, is_successful)
        
        return final_response

    def _create_response_context(self, similar_responses: list) -> str:
        """Tworzy kontekst z poprzednich odpowiedzi."""
        if not similar_responses:
            return ""
        context = "Poprzednie wyszukiwania:\n"
        for response in similar_responses[:3]:  # Ograniczamy do 3 najlepszych
            context += f"- Zapytanie: {response['query']}\n"
            context += f"  Odpowiedź: {response['response'][:200]}...\n"  # Skracamy odpowiedź
            status = "Sukces" if response.get('was_successful') else "Niepowodzenie"
            context += f"  Status: {status}\n"
        return context

    def _validate_search_response(self, query: str, response: str, summaries: list) -> bool:
        """Sprawdza czy wyszukiwanie się powiodło."""
        if not response or not summaries:
            return False
        
        # Sprawdź czy odpowiedź nie zawiera komunikatów o braku wyników
        failure_indicators = [
            "nie znaleziono",
            "brak wyników",
            "nie udało się",
            "przekroczono limit",
            "google tool search disabled"
        ]
        
        response_lower = response.lower()
        for indicator in failure_indicators:
            if indicator in response_lower:
                return False
        
        # Sprawdź czy mamy jakiekolwiek podsumowania
        if len(summaries) == 0:
            return False
            
        # Sprawdź czy podsumowania nie są tylko komunikatami o błędach
        valid_summaries = 0
        for summary in summaries:
            if summary and len(summary.strip()) > 20:  # Minimum 20 znaków
                summary_lower = summary.lower()
                is_error = any(indicator in summary_lower for indicator in failure_indicators)
                if not is_error:
                    valid_summaries += 1
        
        return valid_summaries > 0

    def _store_search_interaction(self, query: str, response: str, is_successful: bool):
        """Zapisuje interakcję wyszukiwania do bazy danych."""
        if not self.advanced_rag:
            return
        
        try:
            response_data = {
                "query": str(query),
                "response": str(response),
                "was_successful": "true" if is_successful else "false",  # Convert to string
                "timestamp": datetime.datetime.now().isoformat(),
                "search_type": "google_search",
                "type": "response"
            }
            
            self.advanced_rag.feedback_db.store_response(response_data)
            print(f"Zapisano wynik wyszukiwania: {'Sukces' if is_successful else 'Niepowodzenie'}")
            
        except Exception as e:
            print(f"Błąd podczas zapisywania wyszukiwania: {e}")


class GoogleSearchWithSerpAPI:
    """
    Zaawansowana klasa wyszukiwania Google z wykorzystaniem SerpAPI,
    AdvancedRAG i systemem prawdopodobieństwa cache'u.
    """
    
    def __init__(self, llm, collection_name: str = "serpapi_cache", embedding_model: str = None, 
                 similarity_threshold: float = 0.7):
        self.llm, self.isFormatted = llm
        self.serpapi_key = os.getenv("SERPAPI_API_KEY")
        
        if not self.serpapi_key:
            raise ValueError("SERPAPI_API_KEY nie jest ustawiony w zmiennych środowiskowych")
        
        # Inicjalizacja AdvancedRAG (zawiera CachedChromaDB)
        if collection_name and embedding_model:
            self.advanced_rag = AdvancedRAG(collection_name, embedding_model)
            # Ustaw próg podobieństwa dla cache
            self.advanced_rag.cached_db.similarity_threshold = similarity_threshold
            print("AdvancedRAG z CachedChromaDB zainicjalizowany dla GoogleSearchWithSerpAPI")
        else:
            self.advanced_rag = None
            
        # Dla kompatybilności wstecznej
        self.cached_db = self.advanced_rag.cached_db if self.advanced_rag else None
    
    def search_with_serpapi(self, query: str):
        try:
            # Przygotuj parametry wyszukiwania
            params = {
                "engine": "google",
                "q": query,
                "num": 3,
                "api_key": self.serpapi_key,
                "kl": "pl-pl"
            }

            # Wykonaj wyszukiwanie
            search = GoogleSearch(params)
            results = search.get_dict()
            return results

        except Exception as e:
            print(f"Błąd podczas wyszukiwania SerpAPI: {e}")
            return None

    def extract_and_process_results(self, search_results, query: str, max_results: int = 5):
        """
        Wyciąga i przetwarza wyniki wyszukiwania z SerpAPI.
        """
        if not search_results:
            return []
        
        summaries = []
        processed_count = 0
        
        # Pobierz organiczne wyniki z odpowiedzi SerpAPI
        organic_results = search_results.get("organic_results", [])
        
        if not organic_results:
            print("Brak organic_results w odpowiedzi SerpAPI")
            return []
        
        print(f"Znaleziono {len(organic_results)} wyników organicznych")
        
        for result in organic_results:
            if processed_count >= max_results:
                break
                
            link = result.get("link", "")
            title = result.get("title", "")
            snippet = result.get("snippet", "")
            
            if not link:
                continue
            
            # Pomiń pliki binarne
            banned_extensions = ['.pdf', '.docx', '.doc', '.pptx', '.ppt', '.xls', '.xlsx']
            if any(link.endswith(ext) for ext in banned_extensions):
                continue
            
            print(f"Przetwarzam: {title} - {link}")
            
            try:
                # Pobierz pełną treść strony
                if re.search(r'wikipedia', link, re.IGNORECASE):
                    text = self.download_text_from_url_with_wikipedia(link)
                else:
                    text = self.download_text_from_url_with_playwright(link)
                
                # Jeśli nie udało się pobrać treści, użyj snippet
                if not text or len(text.strip()) < 50:
                    text = f"{title}. {snippet}"
                    print(f"Używam snippet dla {link}")
                
                # Wygeneruj podsumowanie
                summary = self.generate_summary(text, link, query, title)
                if summary:
                    summaries.append(summary)
                    processed_count += 1
                    print(f"Dodano podsumowanie {processed_count}/{max_results}")
                    
            except Exception as e:
                print(f"Błąd podczas przetwarzania {link}: {e}")
                # Użyj snippet jako fallback
                if snippet:
                    fallback_summary = f"Z {title}: {snippet}"
                    summaries.append(fallback_summary)
                    processed_count += 1
                    print(f"Użyto fallback dla {link}")
        
        print(f"Przetworzono łącznie {len(summaries)} wyników")
        return summaries
    
    def download_text_from_url_with_playwright(self, url):
        """
        Pobiera tekst ze strony za pomocą Playwright.
        """
        try:
            loader = PlaywrightURLLoader(urls=[url], remove_selectors=[
                "header", "footer", "nav", "aside",
                ".mw-editsection", "sup.reference", ".reflist", ".infobox",
                ".mw-sidebar", ".toc", ".navbox", ".hatnote", ".metadata",
                ".sistersitebox", ".catlinks", ".mw-jump", ".printfooter",
                ".portal", ".navbar", "script", "style", "noscript",
            ])
            documents = loader.load()
            if documents:
                content = documents[0].page_content.strip()
                return content if len(content) > 20 else ""
            return ""
        except Exception as e:
            print(f"Błąd Playwright dla {url}: {e}")
            return ""
    
    def download_text_from_url_with_wikipedia(self, url):
        """
        Pobiera tekst z Wikipedii.
        """
        try:
            article_title = url.split('/')[-1]
            content = wikipedia.search(article_title, results=2, suggestion=False)
            print(f"Znaleziono artykuły: {content}")
            
            contents = []
            for i in content:
                page_content = wikipedia.page(i, auto_suggest=False).content
                contents.append(page_content)
            
            return " ".join(contents) if contents else ""
            
        except wikipedia.exceptions.PageError:
            return "Nie udało się znaleźć artykułu na Wikipedii."
        except Exception as e:
            return f"Wystąpił błąd: {str(e)}"
    
    def generate_summary(self, text: str, link: str, user_query: str, title: str = ""):
        """
        Generuje podsumowanie tekstu w kontekście zapytania użytkownika.
        """
        try:
            # Ogranicz długość tekstu
            max_length = 3000
            if len(text) > max_length:
                text = text[:max_length] + "..."
            
            params = {}
            if self.isFormatted:
                params['format'] = 'json'
            
            reply = self.llm.chat(messages=[
                ChatMessage(role=MessageRole.SYSTEM, content=f"""
                <current_date>{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</current_date>
                Przeanalizuj poniższy tekst i podsumuj go w zwięzły sposób.
                Weź pod uwagę kontekst zapytania użytkownika.
                Weź pod uwagę link do tekstu i tytuł.
                Spróbuj zrozumieć, które części tekstu są ważne, a które nie - uwzględnij tylko najważniejsze części związane z zapytaniem użytkownika i/lub linkiem.
                Odpowiedź powinna być konkretna i pomocna w odpowiedzi na zapytanie użytkownika.
                """),
                ChatMessage(role=MessageRole.USER, content=f"""
                <text>{text}</text>
                <link>{link}</link>
                <title>{title}</title>
                <user_query>{user_query}</user_query>
                """)
            ], **params)
            
            return reply.message.content if reply.message.content else ""
            
        except Exception as e:
            print(f"Błąd podczas generowania podsumowania: {e}")
            return f"Błąd podczas przetwarzania treści z {link}"
    
    def search(self, query: str, use_cache: bool = True, max_processed: int = 5, 
               use_advanced_features: bool = True):
        """
        Główna metoda wyszukiwania z wykorzystaniem AdvancedRAG i cache'u.
        
        Args:
            query: Zapytanie użytkownika
            use_cache: Czy używać cache'u (domyślnie True)
            num_results: Liczba wyników do pobrania z SerpAPI
            max_processed: Maksymalna liczba stron do przetworzenia
            use_advanced_features: Czy używać zaawansowanych funkcji AdvancedRAG
        """
        print(f"Wyszukuję informacji o: {query}")
        
        # 1. Sprawdź cache jeśli włączony i dostępny AdvancedRAG
        if use_cache and self.advanced_rag and self.advanced_rag.cached_db:
            try:
                is_similar, cached_response, similarity = self.advanced_rag.cached_db.check_similarity_cache(query)
                
                if is_similar and cached_response:
                    print(f"Używam odpowiedzi z cache (podobieństwo: {similarity:.3f})")
                    self.advanced_rag.cached_db.update_usage_count(query)
                    return cached_response
            except Exception as e:
                print(f"Błąd podczas sprawdzania cache: {e}")
        
        # 2. Rozszerzenie zapytania jeśli włączone zaawansowane funkcje
        queries_to_search = [query]
        if use_advanced_features and self.advanced_rag:
            try:
                expanded_queries = self.advanced_rag.query_expansion_db.expand_query(query, quick_mode=True)
                if len(expanded_queries) > 1:
                    queries_to_search = expanded_queries[:3]  # Ograniczamy do 3 zapytań
                    print(f"Rozszerzono zapytanie do {len(queries_to_search)} wariantów")
            except Exception as e:
                print(f"Błąd podczas rozszerzania zapytania: {e}")
        
        # 3. Pobierz kontekst z poprzednich wyszukiwań
        context = ""
        if self.advanced_rag:
            try:
                similar_responses = self.advanced_rag.feedback_db.get_similar_responses(query)
                if similar_responses:
                    context = self._create_response_context(similar_responses)
                    print(f"Dodano kontekst z Advanced RAG: {len(similar_responses)} elementów")
            except Exception as e:
                print(f"Błąd podczas pobierania kontekstu z Advanced RAG: {e}")
        
        # 4. Wykonaj wyszukiwania SerpAPI dla wszystkich zapytań
        all_summaries = []
        for search_query in queries_to_search:
            print(f"Wyszukuję dla: {search_query}")
            
            search_results = self.search_with_serpapi(search_query)
            
            if search_results:
                # Sprawdź status wyszukiwania
                search_metadata = search_results.get("search_metadata", {})
                status = search_metadata.get("status", "Unknown")
                print(f"Status wyszukiwania: {status}")
                
                if status == "Success":
                    summaries = self.extract_and_process_results(search_results, search_query, max_processed)
                    all_summaries.extend(summaries)
                else:
                    print(f"Wyszukiwanie nieudane dla: {search_query}")
            else:
                print(f"Brak wyników dla: {search_query}")
            
            # Ograniczamy łączną liczbę podsumowań
            if len(all_summaries) >= max_processed * 2:
                break
        
        if not all_summaries:
            no_results_msg = "Nie znaleziono żadnych użytecznych wyników dla tego zapytania."
            print(no_results_msg)
            return no_results_msg
        
        # 5. Rerankowanie wyników jeśli włączone zaawansowane funkcje
        if use_advanced_features and self.advanced_rag and len(all_summaries) > 1:
            try:
                reranked_summaries = self.advanced_rag.reranking_db.rerank_results(
                    query, all_summaries, top_k=min(len(all_summaries), max_processed)
                )
                if reranked_summaries:
                    all_summaries = reranked_summaries
                    print(f"Przerangowano wyniki do {len(all_summaries)} najlepszych")
            except Exception as e:
                print(f"Błąd podczas rerankowania: {e}")
        
        # 6. Wygeneruj finalną odpowiedź
        if use_advanced_features and self.advanced_rag:
            # Użyj Chain of Thought z AdvancedRAG
            try:
                final_response = self.advanced_rag.chain_of_thought_db.generate_with_cot(query, all_summaries)
            except Exception as e:
                print(f"Błąd podczas Chain of Thought: {e}")
                # Fallback do standardowej metody
                final_response = self._generate_standard_response(query, all_summaries, context)
        else:
            # Standardowa metoda generowania odpowiedzi
            final_response = self._generate_standard_response(query, all_summaries, context)
        
        # 7. Zapisz do cache i feedback
        if self.advanced_rag:
            # Zapisz do cache
            if self.advanced_rag.cached_db:
                try:
                    self.advanced_rag.cached_db.store_search_query_and_response(query, final_response)
                except Exception as e:
                    print(f"Błąd podczas zapisywania do cache: {e}")
            
            # Zapisz do feedback
            try:
                is_successful = self._validate_search_response(query, final_response, all_summaries)
                self._store_search_interaction(query, final_response, is_successful)
            except Exception as e:
                print(f"Błąd podczas zapisywania feedback: {e}")
        
        return final_response
    
    def _generate_standard_response(self, query: str, summaries: list, context: str = ""):
        """
        Generuje standardową odpowiedź bez Chain of Thought.
        """
        try:
            system_content = f"""
            Na podstawie zapytania użytkownika i dołączonych streszczeń tekstów, odpowiedz na pytanie. 
            Odpowiedź musi być krótka, zwięzła, logiczna i tylko na podstawie tekstów dołączonych.
            Teksty: {' '.join(summaries)}
            """
            
            if context.strip():
                system_content += f"\n\nKontekst z poprzednich wyszukiwań:\n{context}"
                system_content += "\nWykorzystaj ten kontekst do lepszego zrozumienia zapytania i unikania błędów z przeszłości."
            
            params = {}
            if self.isFormatted:
                params['format'] = 'json'
                
            final_response = self.llm.chat(messages=[
                ChatMessage(role=MessageRole.SYSTEM, content=system_content),
                ChatMessage(role=MessageRole.USER, content=f"Zapytanie: {query}")
            ], **params).message.content
            
            return final_response
            
        except Exception as e:
            error_msg = f"Błąd podczas generowania odpowiedzi: {e}"
            print(error_msg)
            return error_msg
    
    def _create_response_context(self, similar_responses: list) -> str:
        """Tworzy kontekst z poprzednich odpowiedzi."""
        if not similar_responses:
            return ""
        context = "Poprzednie wyszukiwania:\n"
        for response in similar_responses[:3]:  # Ograniczamy do 3 najlepszych
            context += f"- Zapytanie: {response['query']}\n"
            context += f"  Odpowiedź: {response['response'][:200]}...\n"  # Skracamy odpowiedź
            status = "Sukces" if response.get('was_successful') else "Niepowodzenie"
            context += f"  Status: {status}\n"
        return context
    
    def _validate_search_response(self, query: str, response: str, summaries: list) -> bool:
        """Sprawdza czy wyszukiwanie się powiodło."""
        if not response or not summaries:
            return False
        
        # Sprawdź czy odpowiedź nie zawiera komunikatów o braku wyników
        failure_indicators = [
            "nie znaleziono",
            "brak wyników", 
            "nie udało się",
            "błąd podczas",
            "serpapi"
        ]
        
        response_lower = response.lower()
        for indicator in failure_indicators:
            if indicator in response_lower:
                return False
        
        # Sprawdź czy mamy jakiekolwiek podsumowania
        if len(summaries) == 0:
            return False
            
        # Sprawdź czy podsumowania nie są tylko komunikatami o błędach
        valid_summaries = 0
        for summary in summaries:
            if summary and len(summary.strip()) > 20:  # Minimum 20 znaków
                summary_lower = summary.lower()
                is_error = any(indicator in summary_lower for indicator in failure_indicators)
                if not is_error:
                    valid_summaries += 1
        
        return valid_summaries > 0
    
    def _store_search_interaction(self, query: str, response: str, is_successful: bool):
        """Zapisuje interakcję wyszukiwania do bazy danych."""
        if not self.advanced_rag:
            return
        
        try:
            response_data = {
                "query": str(query),
                "response": str(response),
                "was_successful": "true" if is_successful else "false",
                "timestamp": datetime.datetime.now().isoformat(),
                "search_type": "serpapi_search",
                "type": "response"
            }
            
            save = self.advanced_rag.feedback_db.store_response(response_data)
            print(f"Zapisano wynik wyszukiwania SerpAPI: {'Sukces' if save else 'Niepowodzenie'}")
            
        except Exception as e:
            print(f"Błąd podczas zapisywania wyszukiwania SerpAPI: {e}")
    
    def provide_feedback(self, query: str, response: str, score: int, feedback_text: str = ""):
        """
        Pozwala użytkownikowi przekazać feedback o jakości wyszukiwania.
        """
        if not self.advanced_rag:
            print("AdvancedRAG nie jest dostępny - nie można zapisać feedback")
            return False
        
        feedback_data = {
            "query": query,
            "response": response,
            "score": score,
            "feedback_text": feedback_text,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        return self.advanced_rag.provide_feedback(feedback_data)
    
    def get_cache_stats(self):
        """Zwraca statystyki cache'u."""
        if self.advanced_rag and self.advanced_rag.cached_db:
            return self.advanced_rag.cached_db.get_cache_stats()
        return {"error": "Cache nie jest dostępny"}
    
    def get_feedback_stats(self):
        """Zwraca statystyki feedback."""
        if self.advanced_rag and self.advanced_rag.feedback_db:
            return self.advanced_rag.feedback_db.get_feedback_stats()
        return {"error": "Feedback DB nie jest dostępny"}
    
    def clear_cache(self):
        """Czyści cache."""
        if self.advanced_rag and self.advanced_rag.cached_db:
            self.advanced_rag.cached_db.clear_cache()
            print("Cache został wyczyszczony")
        else:
            print("Cache nie jest dostępny")
