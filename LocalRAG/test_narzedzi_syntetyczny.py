import os
import json
import datetime
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import traceback

# Importy z search_from_internet
from src.search_from_internet.search import searchToUser
from src.search_from_internet.google_search import GoogleSearchJsonAPI
from src.search_from_internet.stock_fetcher import StockFetcher
from src.search_from_internet.exchange_rate import ExchangeRate
from src.utils.local_database_search import search_local_database
from src.config import MODEL, MODEL_EMBEDDINGS
from src.utils import LLMProvider

@dataclass
class ToolTestScenario:
    """Klasa reprezentująca pojedynczy scenariusz testowy narzędzia."""
    id: str
    name: str
    description: str
    query: str
    expected_tool: str
    prompt_type: str  # "obvious", "unusual", "complex"
    expected_keywords: List[str]  # Słowa kluczowe oczekiwane w odpowiedzi
    should_succeed: bool = True
    category: str = "general"

class ToolsAgentTest:
    """Główna klasa testująca narzędzia i agenta."""
    
    def __init__(self, output_dir: str = "test_results"):
        self.output_dir = output_dir
        self.results = []
        os.makedirs(output_dir, exist_ok=True)
        
        # Inicjalizacja LLM
        self.llm, _ = LLMProvider.getLLM(MODEL)
        
    def create_test_scenarios(self) -> List[ToolTestScenario]:
        """Tworzy scenariusze testowe dla narzędzi."""
        scenarios = [
            # Test 1: Google Search - oczywisty
            ToolTestScenario(
                id="GOOGLE_OBVIOUS_001",
                name="Google Search - aktualne wydarzenia",
                description="Proste zapytanie o aktualne wydarzenia wymagające wyszukiwarki",
                query="Jakie są najnowsze wiadomości o sztucznej inteligencji w 2024 roku?",
                expected_tool="internet_search",
                prompt_type="obvious",
                expected_keywords=["sztuczna inteligencja", "AI", "2024", "wiadomości"],
                category="google_search"
            ),
            
            # Test 2: Wikipedia - oczywisty
            ToolTestScenario(
                id="WIKIPEDIA_OBVIOUS_001",
                name="Wikipedia Search - informacje historyczne",
                description="Zapytanie o podstawowe informacje historyczne dostępne w Wikipedii",
                query="Kim był Albert Einstein i jakie były jego najważniejsze odkrycia?",
                expected_tool="wikipedia_search",
                prompt_type="obvious",
                expected_keywords=["Einstein", "fizyka", "teoria względności", "Nobel"],
                category="wikipedia_search"
            ),
            
            # Test 3: Exchange Rate - oczywisty
            ToolTestScenario(
                id="EXCHANGE_OBVIOUS_001",
                name="Exchange Rate - kurs waluty",
                description="Proste zapytanie o aktualny kurs waluty",
                query="Jaki jest aktualny kurs dolara amerykańskiego?",
                expected_tool="exchange_search",
                prompt_type="obvious",
                expected_keywords=["USD", "dolar", "kurs", "PLN"],
                category="exchange_rate"
            ),
            
            # Test 4: Stock Search - nietypowy
            ToolTestScenario(
                id="STOCK_UNUSUAL_001",
                name="Stock Search - nietypowe zapytanie o surowce",
                description="Zapytanie o cenę surowca w kontekście inwestycyjnym",
                query="Ile kosztuje uncja złota teraz i czy warto inwestować?",
                expected_tool="stock_search",
                prompt_type="unusual",
                expected_keywords=["złoto", "gold", "cena", "uncja", "inwestycja"],
                category="stock_search"
            ),
            
            # Test 5: Złożone zapytanie - agent musi wybrać
            ToolTestScenario(
                id="AGENT_COMPLEX_001",
                name="Agent Decision - złożone zapytanie",
                description="Zapytanie wymagające od agenta wyboru odpowiedniego narzędzia",
                query="Potrzebuję informacji o firmie Apple - jej historii, aktualnym kursie akcji i najnowszych wiadomościach",
                expected_tool="multiple",  # Może użyć kilku narzędzi
                prompt_type="complex",
                expected_keywords=["Apple", "historia", "akcje", "kurs", "wiadomości"],
                category="complex_query"
            ),
            
            # Test 6: Local Database - nietypowy
            ToolTestScenario(
                id="LOCAL_UNUSUAL_001",
                name="Local Database - dokumenty lokalne",
                description="Zapytanie o informacje które mogą być w lokalnej bazie",
                query="Czy w dokumentach lokalnych są informacje o implementacji RAG?",
                expected_tool="local_database_search",
                prompt_type="unusual",
                expected_keywords=["RAG", "implementacja", "dokumenty", "lokalne"],
                category="local_database"
            ),
            
            # Test 7: Kurs waluty - złożony
            ToolTestScenario(
                id="EXCHANGE_COMPLEX_001",
                name="Exchange Rate - analiza trendu",
                description="Złożone zapytanie o trend walutowy",
                query="Jak zmieniał się kurs euro względem złotego w ostatnim miesiącu?",
                expected_tool="exchange_search",
                prompt_type="complex",
                expected_keywords=["EUR", "euro", "PLN", "złoty", "trend", "miesiąc"],
                category="exchange_rate"
            ),
            
            # Test 8: Google Search - nietypowy kontekst
            ToolTestScenario(
                id="GOOGLE_UNUSUAL_001",
                name="Google Search - specjalistyczne zapytanie",
                description="Nietypowe zapytanie wymagające internetowego wyszukiwania",
                query="Jakie są najnowsze regulacje prawne dotyczące dronów w Polsce?",
                expected_tool="internet_search",
                prompt_type="unusual",
                expected_keywords=["drony", "regulacje", "prawo", "Polska", "przepisy"],
                category="google_search"
            ),
            
            # Test 9: Stock - oczywisty
            ToolTestScenario(
                id="STOCK_OBVIOUS_001",
                name="Stock Search - kurs konkretnej firmy",
                description="Proste zapytanie o kurs akcji znanej firmy",
                query="Jaki jest aktualny kurs akcji Tesla?",
                expected_tool="stock_search",
                prompt_type="obvious",
                expected_keywords=["Tesla", "TSLA", "akcje", "kurs", "cena"],
                category="stock_search"
            ),
            
            # Test 10: Agent - decyzja przy dwuznaczności
            ToolTestScenario(
                id="AGENT_AMBIGUOUS_001",
                name="Agent Decision - dwuznaczne zapytanie",
                description="Zapytanie które może wymagać różnych narzędzi",
                query="Chcę wiedzieć więcej o Bitcoinie",
                expected_tool="multiple",  # Może użyć Wikipedia lub Google lub Stock
                prompt_type="complex",
                expected_keywords=["Bitcoin", "BTC", "kryptowaluta", "cena"],
                category="ambiguous_query"
            )
        ]
        
        return scenarios
    
    def run_tool_test(self, scenario: ToolTestScenario) -> Dict[str, Any]:
        """Wykonuje pojedynczy test narzędzia."""
        print(f"\n🔧 Wykonuję test narzędzia: {scenario.id} - {scenario.name}")
        print(f"📝 Zapytanie: {scenario.query}")
        print(f"🎯 Oczekiwane narzędzie: {scenario.expected_tool}")
        
        start_time = time.time()
        
        try:
            # Wykonanie zapytania przez agenta
            response = searchToUser(query=scenario.query, max_iterations=10)
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Analiza odpowiedzi
            analysis = self.analyze_response(scenario, response, execution_time)
            
            # Tworzenie wyniku testu
            result = {
                "test_id": scenario.id,
                "test_name": scenario.name,
                "timestamp": datetime.datetime.now().isoformat(),
                "execution_time_seconds": execution_time,
                "scenario": {
                    "description": scenario.description,
                    "query": scenario.query,
                    "expected_tool": scenario.expected_tool,
                    "prompt_type": scenario.prompt_type,
                    "category": scenario.category,
                    "expected_keywords": scenario.expected_keywords
                },
                "response": {
                    "content": str(response),
                    "length": len(str(response)) if response else 0
                },
                "analysis": analysis,
                "status": "completed"
            }
            
            return result
            
        except Exception as e:
            end_time = time.time()
            execution_time = end_time - start_time
            
            error_result = {
                "test_id": scenario.id,
                "test_name": scenario.name,
                "timestamp": datetime.datetime.now().isoformat(),
                "execution_time_seconds": execution_time,
                "error": str(e),
                "traceback": traceback.format_exc(),
                "status": "failed"
            }
            return error_result
    
    def analyze_response(self, scenario: ToolTestScenario, response: Any, execution_time: float) -> Dict[str, Any]:
        """Analizuje odpowiedź pod kątem jakości i poprawności."""
        analysis = {
            "quality_score": 0,
            "keyword_coverage": 0,
            "response_relevance": 0,
            "tool_selection_score": 0,
            "performance_score": 0,
            "overall_score": 0,
            "detailed_findings": {}
        }
        
        try:
            response_text = str(response).lower() if response else ""
            
            # 1. Sprawdzenie pokrycia słów kluczowych
            keywords_found = 0
            for keyword in scenario.expected_keywords:
                if keyword.lower() in response_text:
                    keywords_found += 1
            
            keyword_coverage = (keywords_found / len(scenario.expected_keywords)) * 100 if scenario.expected_keywords else 0
            analysis["keyword_coverage"] = keyword_coverage
            analysis["detailed_findings"]["keywords_found"] = f"{keywords_found}/{len(scenario.expected_keywords)}"
            
            # 2. Ocena jakości odpowiedzi
            if response and len(response_text) > 50:
                analysis["quality_score"] += 3
                if len(response_text) > 200:
                    analysis["quality_score"] += 2
                    analysis["detailed_findings"]["response_length"] = "Odpowiednia długość odpowiedzi"
                else:
                    analysis["detailed_findings"]["response_length"] = "Krótka odpowiedź"
            else:
                analysis["detailed_findings"]["response_length"] = "Zbyt krótka lub pusta odpowiedź"
            
            # 3. Sprawdzenie czy odpowiedź jest na temat
            relevance_indicators = ["błąd", "error", "nie udało", "nie znaleziono"]
            is_error_response = any(indicator in response_text for indicator in relevance_indicators)
            
            if not is_error_response and keyword_coverage > 30:
                analysis["response_relevance"] = 5
                analysis["detailed_findings"]["relevance"] = "Odpowiedź na temat"
            elif keyword_coverage > 10:
                analysis["response_relevance"] = 3
                analysis["detailed_findings"]["relevance"] = "Częściowo na temat"
            else:
                analysis["response_relevance"] = 1
                analysis["detailed_findings"]["relevance"] = "Odpowiedź nie na temat lub błędna"
            
            # 4. Ocena wydajności
            if execution_time < 10:
                analysis["performance_score"] = 5
                analysis["detailed_findings"]["performance"] = "Bardzo szybka odpowiedź"
            elif execution_time < 30:
                analysis["performance_score"] = 4
                analysis["detailed_findings"]["performance"] = "Szybka odpowiedź"
            elif execution_time < 60:
                analysis["performance_score"] = 3
                analysis["detailed_findings"]["performance"] = "Średnia szybkość"
            else:
                analysis["performance_score"] = 2
                analysis["detailed_findings"]["performance"] = "Wolna odpowiedź"
            
            # 5. Ocena wyboru narzędzia (heurystyczna)
            tool_selection_hints = {
                "internet_search": ["wyszukiwania", "znaleziono", "według", "strony"],
                "wikipedia_search": ["wikipedia", "artykuł", "encyklopedia"],
                "exchange_search": ["kurs", "waluta", "nbp", "złoty"],
                "stock_search": ["akcje", "symbol", "giełda", "ticker"],
                "local_database_search": ["dokumentach", "lokalnych", "baza"]
            }
            
            tool_hints_found = 0
            if scenario.expected_tool != "multiple":
                expected_hints = tool_selection_hints.get(scenario.expected_tool, [])
                for hint in expected_hints:
                    if hint in response_text:
                        tool_hints_found += 1
                
                if expected_hints:
                    tool_score = (tool_hints_found / len(expected_hints)) * 5
                    analysis["tool_selection_score"] = min(tool_score, 5)
                    analysis["detailed_findings"]["tool_selection"] = f"Znaleziono {tool_hints_found}/{len(expected_hints)} wskaźników narzędzia"
                else:
                    analysis["tool_selection_score"] = 3
                    analysis["detailed_findings"]["tool_selection"] = "Brak możliwości weryfikacji narzędzia"
            else:
                analysis["tool_selection_score"] = 3
                analysis["detailed_findings"]["tool_selection"] = "Zapytanie złożone - akceptowalny wybór narzędzi"
            
            # 6. Ogólna ocena
            analysis["overall_score"] = (
                analysis["quality_score"] + 
                (analysis["keyword_coverage"] / 20) +  # Normalizacja do 5
                analysis["response_relevance"] + 
                analysis["tool_selection_score"] + 
                analysis["performance_score"]
            ) / 5
            
            # 7. Dodatkowe sprawdzenia
            analysis["detailed_findings"]["execution_time"] = f"{execution_time:.2f} sekund"
            analysis["detailed_findings"]["response_size"] = f"{len(response_text)} znaków"
            
        except Exception as e:
            analysis["error"] = str(e)
            analysis["detailed_findings"]["analysis_error"] = f"Błąd podczas analizy: {e}"
        
        return analysis
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Uruchamia wszystkie testy narzędzi i agenta."""
        print(f"🚀 Rozpoczynam kompleksowe testy narzędzi i agenta")
        
        # Testowanie scenariuszy przez agenta
        scenarios = self.create_test_scenarios()
        agent_results = []
        
        print(f"\n🤖 Testowanie {len(scenarios)} scenariuszy przez agenta...")
        for scenario in scenarios:
            result = self.run_tool_test(scenario)
            agent_results.append(result)
            
            # Zapisz pojedynczy wynik
            self.save_single_result(result)
            
            # Podsumowanie testu
            if "analysis" in result:
                score = result["analysis"].get("overall_score", 0)
                time_taken = result.get("execution_time_seconds", 0)
                print(f"  ✅ {scenario.id}: {score:.1f}/5.0 ({time_taken:.1f}s)")
            else:
                print(f"  ❌ {scenario.id}: BŁĄD")
        
        # Kompletne wyniki
        complete_results = {
            "test_summary": {
                "total_agent_tests": len(agent_results),
                "timestamp": datetime.datetime.now().isoformat(),
                "test_duration": sum(r.get("execution_time_seconds", 0) for r in agent_results)
            },
            "agent_test_results": agent_results,
            "performance_analysis": self.analyze_overall_performance(agent_results),
        }
        
        # Zapisz wszystkie wyniki
        self.save_complete_results(complete_results)
        
        # Wygeneruj raporty
        self.generate_tool_reports(complete_results)
        
        return complete_results
    
    def analyze_overall_performance(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analizuje ogólną wydajność testów."""
        successful_tests = [r for r in results if r.get("status") == "completed" and "analysis" in r]
        
        if not successful_tests:
            return {"error": "Brak udanych testów do analizy"}
        
        scores = [r["analysis"]["overall_score"] for r in successful_tests]
        times = [r["execution_time_seconds"] for r in successful_tests]
        
        performance = {
            "total_tests": len(results),
            "successful_tests": len(successful_tests),
            "success_rate": (len(successful_tests) / len(results)) * 100,
            "average_score": sum(scores) / len(scores),
            "best_score": max(scores),
            "worst_score": min(scores),
            "average_time": sum(times) / len(times),
            "fastest_time": min(times),
            "slowest_time": max(times),
            "by_category": {}
        }
        
        # Analiza po kategoriach
        categories = {}
        for result in successful_tests:
            category = result["scenario"]["category"]
            if category not in categories:
                categories[category] = []
            categories[category].append(result["analysis"]["overall_score"])
        
        for category, scores in categories.items():
            performance["by_category"][category] = {
                "count": len(scores),
                "average_score": sum(scores) / len(scores),
                "best_score": max(scores),
                "worst_score": min(scores)
            }
        
        return performance
    
    def analyze_tool_reliability(self, agent_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analizuje niezawodność poszczególnych narzędzi."""
        reliability = {
            "total_tools_tested": len(agent_results),
            "tools_working": 0,
            "tools_failing": 0,
            "tool_status": {}
        }
        
        for test in agent_results:
            tool_name = test["tool"]
            status = test["status"]
            
            reliability["tool_status"][tool_name] = {
                "status": status,
                "response_size": test.get("response_length", 0),
                "error": test.get("error", None)
            }
            
            if status == "success":
                reliability["tools_working"] += 1
            else:
                reliability["tools_failing"] += 1
        
        reliability["reliability_percentage"] = (reliability["tools_working"] / reliability["total_tools_tested"]) * 100 if reliability["total_tools_tested"] > 0 else 0
        
        return reliability
    
    def save_single_result(self, result: Dict[str, Any]):
        """Zapisuje pojedynczy wynik testu."""
        filename = f"tool_test_{result['test_id']}.json"
        filepath = os.path.join(self.output_dir, "single_tool_tests", filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    
    def save_complete_results(self, results: Dict[str, Any]):
        """Zapisuje kompletne wyniki wszystkich testów."""
        filepath = os.path.join(self.output_dir, "all_tools_test_results.json")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
    
    def generate_tool_reports(self, results: Dict[str, Any]):
        """Generuje raporty z testów narzędzi."""
        # Raport JSON
        summary_filepath = os.path.join(self.output_dir, "tools_test_summary.json")
        summary = {
            "summary": results["test_summary"],
            "performance": results["performance_analysis"],
            "reliability": results["tool_reliability"],
            "recommendations": self.generate_recommendations(results)
        }
        
        with open(summary_filepath, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        # Raport tekstowy
        self.generate_text_tool_report(results)
        
        print(f"\n📋 Raporty z testów narzędzi zapisane w folderze: {self.output_dir}")
    
    def generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generuje rekomendacje na podstawie wyników testów."""
        recommendations = []
        
        performance = results["performance_analysis"]
        reliability = results["tool_reliability"]
        
        # Rekomendacje na podstawie wydajności
        if performance.get("success_rate", 0) < 80:
            recommendations.append("Niski wskaźnik sukcesu testów - należy poprawić stabilność systemu")
        
        if performance.get("average_time", 0) > 30:
            recommendations.append("Długi czas wykonywania - rozważ optymalizację wydajności")
        
        # Rekomendacje na podstawie niezawodności narzędzi
        if reliability.get("reliability_percentage", 0) < 100:
            failing_tools = [tool for tool, status in reliability["tool_status"].items() if status["status"] != "success"]
            recommendations.append(f"Niepracujące narzędzia: {', '.join(failing_tools)} - wymagają naprawy")
        
        # Rekomendacje na podstawie kategorii
        categories = performance.get("by_category", {})
        weak_categories = [cat for cat, stats in categories.items() if stats["average_score"] < 3]
        if weak_categories:
            recommendations.append(f"Słabe wyniki w kategoriach: {', '.join(weak_categories)} - wymagają poprawy")
        
        return recommendations
    
    def generate_text_tool_report(self, results: Dict[str, Any]):
        """Generuje tekstowy raport z testów narzędzi."""
        filepath = os.path.join(self.output_dir, "tools_test_report.txt")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("RAPORT Z TESTÓW NARZĘDZI I AGENTA\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Data wykonania: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            # Podsumowanie testów
            summary = results["test_summary"]
            f.write(f"Łączna liczba testów agenta: {summary['total_agent_tests']}\n")
            f.write(f"Liczba testów jednotek narzędzi: {summary['total_individual_tests']}\n")
            f.write(f"Łączny czas testów: {summary['test_duration']:.2f} sekund\n\n")
            
            # Wydajność agenta
            performance = results["performance_analysis"]
            f.write("WYDAJNOŚĆ AGENTA:\n")
            f.write("-" * 20 + "\n")
            f.write(f"Wskaźnik sukcesu: {performance.get('success_rate', 0):.1f}%\n")
            f.write(f"Średni wynik: {performance.get('average_score', 0):.2f}/5.0\n")
            f.write(f"Najlepszy wynik: {performance.get('best_score', 0):.2f}\n")
            f.write(f"Najgorszy wynik: {performance.get('worst_score', 0):.2f}\n")
            f.write(f"Średni czas wykonania: {performance.get('average_time', 0):.2f}s\n\n")
            
            # Wyniki po kategoriach
            f.write("WYNIKI PO KATEGORIACH:\n")
            f.write("-" * 25 + "\n")
            for category, stats in performance.get("by_category", {}).items():
                f.write(f"{category}:\n")
                f.write(f"  Liczba testów: {stats['count']}\n")
                f.write(f"  Średni wynik: {stats['average_score']:.2f}\n")
                f.write(f"  Najlepszy: {stats['best_score']:.2f}\n")
                f.write(f"  Najgorszy: {stats['worst_score']:.2f}\n\n")
            
            # Niezawodność narzędzi
            reliability = results["tool_reliability"]
            f.write("NIEZAWODNOŚĆ NARZĘDZI:\n")
            f.write("-" * 25 + "\n")
            f.write(f"Ogólna niezawodność: {reliability.get('reliability_percentage', 0):.1f}%\n")
            f.write(f"Pracujące narzędzia: {reliability.get('tools_working', 0)}\n")
            f.write(f"Niedziałające narzędzia: {reliability.get('tools_failing', 0)}\n\n")
            
            for tool, status in reliability.get("tool_status", {}).items():
                f.write(f"{tool}: {status['status']}")
                if status.get('error'):
                    f.write(f" - {status['error']}")
                f.write(f" (rozmiar odpowiedzi: {status.get('response_size', 0)} znaków)\n")
            
            f.write("\nREKOMENDACJE:\n")
            f.write("-" * 15 + "\n")
            recommendations = self.generate_recommendations(results)
            for i, rec in enumerate(recommendations, 1):
                f.write(f"{i}. {rec}\n")

def main():
    """Funkcja główna uruchamiająca testy narzędzi."""
    print("🔧 Test Syntetyczny #2: Ocena Działania Narzędzi i Agenta")
    print("=" * 60)
    
    # Inicjalizacja testu
    test = ToolsAgentTest(output_dir="test_results/tools")
    
    # Uruchomienie testów
    results = test.run_all_tests()
    
    print(f"\n✅ Testy narzędzi zakończone!")
    print(f"📊 Przetestowano {results['test_summary']['total_agent_tests']} scenariuszy agenta")
    print(f"⏱️ Łączny czas: {results['test_summary']['test_duration']:.2f} sekund")
    print(f"📁 Wyniki w folderze: test_results/tools")

if __name__ == "__main__":
    main() 