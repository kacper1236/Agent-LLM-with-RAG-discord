#!/usr/bin/env python3
"""
Prosty logged agent - przechwytuje output i zapisuje do pliku
"""

import sys
import io
from llama_index.core.agent.react.base import ReActAgent
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from .simple_agent_logger import simple_logger


class SimpleLoggedAgent:
    def __init__(self, tools, llm, memory, system_prompt="", max_iterations=10, verbose=True):
        """Prosty agent z logowaniem"""
        self.tools = tools
        self.llm = llm
        self.memory = memory
        self.system_prompt = system_prompt
        self.max_iterations = max_iterations
        self.verbose = verbose
    
    def _capture_verbose_output(self, agent, query):
        """Przechwytuje verbose output z agenta BEZ blokowania printów"""
        # Stwórz wrapper który będzie przechwytywał i przekazywał dalej
        old_stdout = sys.stdout
        
        class TeeOutput:
            def __init__(self, original_stdout):
                self.original = original_stdout
                self.captured = io.StringIO()
            
            def write(self, text):
                # Zapisz do oryginalnego stdout (zachowaj printy)
                self.original.write(text)
                # Zapisz też do przechwytywania
                self.captured.write(text)
            
            def flush(self):
                self.original.flush()
                self.captured.flush()
        
        tee = TeeOutput(old_stdout)
        
        try:
            sys.stdout = tee
            response = agent.query(query)
            sys.stdout = old_stdout
            
            # Parsuj przechwycony output
            output_text = tee.captured.getvalue()
            self._parse_and_log_output(output_text)
            
            return response
            
        except Exception as e:
            sys.stdout = old_stdout
            simple_logger.log_error(f"Błąd agenta: {str(e)}")
            
            # Spróbuj fallback
            return self._simple_fallback(query)
    
    def _parse_and_log_output(self, output_text):
        """Parsuj output i zapisz kroki"""
        lines = output_text.split('\n')
        current_thought = ""
        current_action = ""
        current_observation = ""
        step_started = False
        
        for line in lines:
            line = line.strip()
            
            # Wykryj rozpoczęcie kroku
            if "Running step" in line or "Step" in line:
                step_started = True
                continue
            
            if line.startswith('Thought:'):
                current_thought = line[8:].strip()
                step_started = True
            elif line.startswith('Action:'):
                current_action = line[7:].strip()
            elif line.startswith('Observation:'):
                current_observation = line[12:].strip()
                
                # Zapisz krok gdy mamy myśl i akcję
                if step_started and (current_thought or current_action):
                    simple_logger.log_step(
                        thought=current_thought,
                        action=current_action,
                        observation=current_observation
                    )
                    current_thought = ""
                    current_action = ""
                    current_observation = ""
                    step_started = False
            
            elif 'Answer:' in line or 'Final Answer:' in line:
                final_answer = line[line.find(':')+7:].strip()
                if final_answer:
                    simple_logger.log_step(final_answer=final_answer)
            
            # Kontynuacja wieloliniowego tekstu
            elif step_started and line and not line.startswith('>'):
                if current_thought and not current_action:
                    current_thought += " " + line
                elif current_action and not current_observation:
                    current_action += " " + line
                elif current_observation:
                    current_observation += " " + line
        
        # Zapisz ostatni krok jeśli nie został zapisany
        if step_started and (current_thought or current_action):
            simple_logger.log_step(
                thought=current_thought,
                action=current_action,
                observation=current_observation
            )
    
    def _simple_fallback(self, query):
        """Prosty fallback gdy agent nie działa"""
        simple_logger.log_error("Używam fallback reasoning")
        
        # Znajdź podobne sesje
        similar_files = simple_logger.find_similar_sessions(query, limit=2)
        
        if similar_files:
            # Przeczytaj podobne sesje i stwórz odpowiedź
            context = "Podobne poprzednie odpowiedzi:\n"
            for file_path in similar_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Wyciągnij ostatnią odpowiedź
                        if "Wynik końcowy:" in content:
                            result = content.split("Wynik końcowy:")[-1].split("\n")[0].strip()
                            context += f"- {result}\n"
                except:
                    continue
            
            # Użyj LLM do stworzenia odpowiedzi na podstawie kontekstu
            try:
                messages = [
                    ChatMessage(role=MessageRole.SYSTEM, content="Odpowiedz na pytanie na podstawie podobnych poprzednich odpowiedzi."),
                    ChatMessage(role=MessageRole.USER, content=f"{context}\n\nPytanie: {query}")
                ]
                
                response = self.llm.chat(messages)
                fallback_answer = response.message.content if hasattr(response, 'message') else str(response)
                
                simple_logger.log_step(
                    thought="Używam fallback reasoning z podobnych sesji",
                    final_answer=fallback_answer
                )
                
                return fallback_answer
                
            except Exception as e:
                simple_logger.log_error(f"Błąd fallback: {str(e)}")
                return f"Przepraszam, nie mogę odpowiedzieć na: {query}"
        
        return f"Potrzebuję więcej informacji aby odpowiedzieć na: {query}"
    
    def query(self, query):
        """Główna metoda do zadawania pytań"""
        # Rozpocznij sesję logowania
        simple_logger.start_session(query)
        print(f"📝 [Logowanie aktywne] Zapisuję myśli agenta do pliku...")
        
        try:
            # Stwórz agenta
            agent = ReActAgent.from_tools(
                tools=self.tools,
                llm=self.llm,
                system_prompt=self.system_prompt,
                max_iterations=self.max_iterations,
                verbose=self.verbose
            )
            
            # Wykonaj zapytanie z przechwytywaniem
            response = self._capture_verbose_output(agent, query)
            
            # Zakończ sesję
            simple_logger.end_session(str(response))
            print(f"✅ [Logowanie zakończone] Myśli zapisane w agent_logs/")
            
            return response
            
        except Exception as e:
            simple_logger.log_error(f"Krytyczny błąd: {str(e)}")
            simple_logger.end_session(f"Błąd: {str(e)}")
            return f"Wystąpił błąd: {str(e)}" 