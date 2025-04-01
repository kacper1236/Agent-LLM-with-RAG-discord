from src.searchFromInternet.search import searchToUser, provide_feedback
import json
from datetime import datetime


def test_advanced_rag_interactive():
    print("Interaktywny test Advanced RAG (wpisz 'exit' aby zakończyć)")
    
    conversation_history = []
    
    while True:
        query = input("\nTwoje pytanie (lub 'exit'): ")
        if query.lower() == 'exit':
            break
            
        response = searchToUser(query)
        # Konwertujemy odpowiedź na string, jeśli jest obiektem Response
        response_text = str(response) if hasattr(response, 'content') else response
        print(f"\nOdpowiedź: {response_text}")
        
        try:
            # Zbieranie feedbacku
            while True:
                try:
                    feedback_score = int(input("Oceń odpowiedź (1-5): "))
                    if 1 <= feedback_score <= 5:
                        break
                    print("Proszę podać ocenę od 1 do 5")
                except ValueError:
                    print("Proszę podać liczbę od 1 do 5")
                    
            feedback_text = input("Dodaj komentarz do odpowiedzi: ")
            
            # Przekazanie feedbacku
            feedback_success = provide_feedback(
                query=query,
                response=response_text,
                score=feedback_score,
                feedback_text=feedback_text
            )
            
            if feedback_success:
                print("Feedback został zapisany pomyślnie")
            else:
                print("Wystąpił problem z zapisem feedbacku")
            
            # Zapisanie wyników - używamy tylko tekstowej wersji odpowiedzi
            conversation_history.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "query": query,
                "response": response_text,
                "feedback_score": feedback_score,
                "feedback_text": feedback_text
            })
            
        except Exception as e:
            print(f"Wystąpił błąd podczas zbierania feedbacku: {e}")
            
        # Opcjonalne ponowne zadanie pytania
        if input("\nCzy chcesz zadać to samo pytanie ponownie? (t/n): ").lower() == 't':
            new_response = searchToUser(query)
            new_response_text = str(new_response) if hasattr(new_response, 'content') else new_response
            print(f"\nNowa odpowiedź: {new_response_text}")
            conversation_history.append({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "query": query,
                "response": new_response_text,
                "type": "follow_up"
            })
        else:
            print("Koniec interakcji")
            break


if __name__ == "__main__":
    test_advanced_rag_interactive()
