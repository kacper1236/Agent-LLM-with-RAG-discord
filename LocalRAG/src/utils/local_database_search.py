import os
from ..get_vector_db import getDatabases
from ..config import MODEL_EMBEDDINGS

def search_local_database(query: str, max_results: int = 5) -> str:
    """
    Wyszukuje w lokalnej bazie danych dokumentów, które zostały przetworzone przez doEmbeddings.
    
    Args:
        query: Zapytanie wyszukiwania
        max_results: Maksymalna liczba wyników
        
    Returns:
        str: Sformatowane wyniki wyszukiwania
    """
    try:
        # Użyj domyślnych ustawień
        model = MODEL_EMBEDDINGS
        namespace:str = os.getenv('NAMESPACE', 'user_files')
        
        # Pobierz bazę danych
        db = getDatabases(model, namespace)
        
        if db is None:
            return f"Nie można połączyć się z lokalną bazą danych"
        
        # Wykonaj wyszukiwanie podobieństwa
        results = db.similarity_search(query=query, k=max_results)
        
        if not results:
            return f"Nie znaleziono żadnych dokumentów w lokalnej bazie danych pasujących do zapytania: '{query}'"
        
        # Sformatuj wyniki
        formatted_output = f"Znaleziono {len(results)} dokumentów w lokalnej bazie danych pasujących do zapytania '{query}':\n\n"
        
        for i, doc in enumerate(results, 1):
            metadata = doc.metadata
            
            formatted_output += f"📄 **Dokument {i}:**\n"
            
            # Dodaj tytuł jeśli istnieje
            if metadata.get('title'):
                formatted_output += f"**Tytuł:** {metadata.get('title')}\n"
            
            # Dodaj plik źródłowy jeśli istnieje
            if metadata.get('file'):
                file_name = os.path.basename(metadata.get('file'))
                formatted_output += f"**Plik:** {file_name}\n"
            
            # Dodaj tagi jeśli istnieją
            if metadata.get('tags'):
                formatted_output += f"**Tagi:** {metadata.get('tags')}\n"
            
            # Dodaj summaryzację jeśli istnieje
            if metadata.get('summary'):
                formatted_output += f"**Streszczenie:** {metadata.get('summary')}\n"
            
            # Dodaj treść dokumentu (skróconą)
            content = doc.page_content
            if len(content) > 500:
                content = content[:500] + "..."
            formatted_output += f"**Treść:** {content}\n"
            
            # Dodaj finalną summaryzację jeśli istnieje
            if metadata.get('finalSummary'):
                final_summary = metadata.get('finalSummary')
                if len(final_summary) > 300:
                    final_summary = final_summary[:300] + "..."
                formatted_output += f"**Finalna summaryzacja:** {final_summary}\n"
            
            formatted_output += "-" * 50 + "\n\n"
        
        return formatted_output
        
    except Exception as e:
        return f"Błąd podczas wyszukiwania w lokalnej bazie danych: {str(e)}"

 