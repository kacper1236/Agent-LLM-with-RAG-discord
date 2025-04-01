import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import ollama
import os
import json
import datetime

class GoogleSearch():
    query: str

    def __init__(self, local_model:str = 'mistral'):
        self.local_model = local_model
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.cse_id = os.getenv("GOOGLE_CUSTOM_SEARCH_ENGINE")

    def search_with_optimization(self, api_key, cse_id, query, **parameters):
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
            if hasattr(e.response, 'status_code') and e.response.status_code == 429:
                return 429
            return None
        
    def download_text_from_url_classically(self, url):
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        possible_containers = ["article", "main", "div", "section"]
        for container in possible_containers:
            main_content = soup.find(container)
            if main_content:
                return main_content.get_text(separator="\n", strip=True)
        
        return soup.get_text(separator="\n", strip=True)
    
    def download_text_from_url_from_js(self, url):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto(url, wait_until='networkidle')
                
                html_content = page.content()
                
                soup = BeautifulSoup(html_content, 'html.parser')
                
                possible_containers = ["article", "main", "div", "section"]
                for container in possible_containers:
                    main_content = soup.find(container)
                    if main_content:
                        return main_content.get_text(separator="\n", strip=True)
                        
                return "Nie udało się pobrać treści strony."
            
            except Exception as e:
                return f"Error has occur: {e}"

            finally:
                browser.close()
    
    def split_text(self, tekst, max_dl=2000):
        snippets = []
        words = tekst.split()
        while words:
            snippets.append(" ".join(words[:max_dl]))
            words = words[max_dl:]
        return snippets

    def total_text_ollama(self, tekst):
        snippets = self.split_text(tekst)
        summaries = []
        
        for snippet in snippets:
            reply = ollama.chat(model = self.local_model, messages = [{"role": "user", "content": f"Podsumuj: {snippet}"}]) #najpierw mistral potem llama3.1:8b
            summaries.append(reply["message"]["content"])
        
        return " ".join(summaries)
    
    def llm_search_engine(self, query: str):
        json_response = ollama.chat(self.local_model, [{"role": "system", "content": f"""
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
            3. The num field specifies the number of result pages and MUST always be an integer, greater than 1, smaller than 7 (2, 3, 4, 5, 6).
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
        """},
        {"role": 'user', 'content': query}], format = 'json')
        
        return json_response["message"]["content"]
    
    def reformulate_query(self, query):
        response = ollama.chat(model=self.local_model, messages=[
            {"role": "system", "content": "Zmieniaj pytanie użytkownika, by było bardziej precyzyjne, zgodnie z jego intencją. Napisz je któtko i zwięźle."},
            {"role": "system", "content": "Jeżeli pytanie jest trafne i nie wymaga zmian, **nie zmieniaj go**."},
            {"role": "system", "content": "Jeżeli pytanie jest proste i zrozumiałe, **nie zmieniaj go**."},
            {"role": "system", "content": f"Aktualna data: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"},
            {"role": "user", "content": query}
        ])
        return response["message"]["content"]
    
    def search(self, query_user):
        while True:
            query = query_user
            #query = self.reformulate_query(query_user)
            try:
                json_response = self.llm_search_engine(query)
                search_params = json.loads(json_response)
                print('-----------------')
                print(search_params)
                print('-----------------')
                if search_params['searchType'] == "None" or search_params['searchType'] == "":
                    search_params['searchType'] = None
                if search_params['fileType'] == "" or search_params['fileType'] == "None":
                    search_params['fileType'] = None
                
                results = self.search_with_optimization(self.api_key, self.cse_id, query, **search_params)
                if results == 429:
                    return "Przekroczono limit zapytań do Google."
                total_summaries = []

                for item in results['items']:
                    link = item['link']
                    if link.endswith('.pdf'):
                        continue
                    print(f"Przetwarzam: {link}")
                    text = self.download_text_from_url_classically(link)
                    if text == "":
                        text = self.download_text_from_url_from_js(link)
                    summary = self.total_text_ollama(text)
                    print("Podsumowanie:")
                    print(summary)
                    total_summaries.append(summary)
                break
            except Exception as e:
                print(f"Error: {e}")
                continue

        final_response = ollama.chat(model = self.local_model, messages = [{"role": "system", "content": f""" 
                                                                Na podstawie zapytania użytkownika i dołączonych streszczeń tekstów, odpowiedz na pytanie. 
                                                                Odpowiedź musi być, krótka, zwięzła, logiczna i tylko na podstawie tekstów dołączonych.
                                                                Teksty: {' '.join(total_summaries)}
                                                                """},
                                                                {"role": "user", "content": f"query: {query}"}])["message"]["content"]
        
        #print("Final response: ", final_response)
        return final_response


# if __name__ == "__main__":
#     query = "Kto to jest Elon Musk?"
#     google_search = GoogleSearch(query)
#     a = google_search.search(query)
#     print("Final response:")
#     print(a)