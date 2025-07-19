#!/usr/bin/env python3
"""
Prosty logger agenta - zapisuje myśli i decyzje do pliku txt
"""

import datetime
from pathlib import Path
from typing import List

class SimpleAgentLogger:
    def __init__(self, log_dir: str = "agent_logs"):
        """Inicjalizacja prostego loggera"""
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.current_file = None
        self.step_count = 0
        
    def start_session(self, query: str):
        """Rozpocznij nową sesję logowania"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_query = "".join(c for c in query[:30] if c.isalnum() or c in (' ', '-', '_')).replace(' ', '_')
        
        filename = f"agent_{timestamp}_{safe_query}.txt"
        self.current_file = self.log_dir / filename
        self.step_count = 0
        
        # Zapisz nagłówek
        with open(self.current_file, 'w', encoding='utf-8') as f:
            f.write(f"=== Agent Myśli i Decyzje ===\n")
            f.write(f"Data: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Zapytanie: {query}\n")
            f.write(f"{'='*50}\n\n")
    
    def log_step(self, thought: str = "", action: str = "", observation: str = "", final_answer: str = ""):
        """Zapisz krok myślenia agenta"""
        if not self.current_file:
            return
            
        self.step_count += 1
        
        with open(self.current_file, 'a', encoding='utf-8') as f:
            f.write(f"--- Krok {self.step_count} ---\n")
            if thought:
                f.write(f"Myśl: {thought}\n")
            if action:
                f.write(f"Akcja: {action}\n")
            if observation:
                f.write(f"Obserwacja: {observation}\n")
            if final_answer:
                f.write(f"Odpowiedź: {final_answer}\n")
            f.write(f"Czas: {datetime.datetime.now().strftime('%H:%M:%S')}\n\n")
    
    def log_error(self, error: str):
        """Zapisz błąd"""
        if not self.current_file:
            return
            
        with open(self.current_file, 'a', encoding='utf-8') as f:
            f.write(f"BŁĄD: {error}\n")
            f.write(f"Czas: {datetime.datetime.now().strftime('%H:%M:%S')}\n\n")
    
    def end_session(self, final_result: str = ""):
        """Zakończ sesję"""
        if not self.current_file:
            return
            
        with open(self.current_file, 'a', encoding='utf-8') as f:
            f.write(f"{'='*50}\n")
            f.write(f"Sesja zakończona: {datetime.datetime.now().strftime('%H:%M:%S')}\n")
            if final_result:
                f.write(f"Wynik końcowy: {final_result}\n")
            f.write(f"Łączna liczba kroków: {self.step_count}\n")
        
        self.current_file = None
        self.step_count = 0
    
    def find_similar_sessions(self, query: str, limit: int = 3) -> List[str]:
        """Znajdź podobne sesje (proste wyszukiwanie słów kluczowych)"""
        query_words = set(query.lower().split())
        similar_files = []
        
        for log_file in self.log_dir.glob("agent_*.txt"):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read().lower()
                    
                # Sprawdź ile słów z zapytania występuje w pliku
                matches = sum(1 for word in query_words if word in content)
                if matches > 0:
                    similar_files.append((log_file, matches))
            except:
                continue
        
        # Sortuj po liczbie dopasowań
        similar_files.sort(key=lambda x: x[1], reverse=True)
        return [str(f[0]) for f in similar_files[:limit]]

# Globalny logger
simple_logger = SimpleAgentLogger() 