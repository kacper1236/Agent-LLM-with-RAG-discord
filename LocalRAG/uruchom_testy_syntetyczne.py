import os
import sys
import json
import datetime
import traceback
from pathlib import Path
import sys

# Ustawienie kodowania stdout na UTF-8
sys.stdout.reconfigure(encoding='utf-8')
# Dodaj ścieżkę do projektu
sys.path.append(str(Path(__file__).parent))

# Importy testów
from test_sprawiedliwosci_syntetyczny import FairnessTest
from test_narzedzi_syntetyczny import ToolsAgentTest
from src.config import MODEL, MODEL_EMBEDDINGS, DIR_ID

class MasterThesisTestSuite:
    """Główna klasa zarządzająca wszystkimi testami syntetycznymi."""
    
    def __init__(self, output_base_dir: str ):
        self.output_base_dir = output_base_dir
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = os.path.join(self.output_base_dir, f"session_{self.timestamp}")

        # Utwórz foldery
        os.makedirs(self.session_dir, exist_ok=True)
        
        self.results = {
            "session_info": {
                "timestamp": datetime.datetime.now().isoformat(),
                "session_id": self.timestamp,
                "model_tested": MODEL,
                "tests_planned": ["fairness_test", "tools_test"]
            },
            "test_results": {},
            "summary": {},
            "errors": []
        }
    
    def run_fairness_test(self) -> dict:
        """Uruchamia test sprawiedliwości."""
        print("\n" + "="*80)
        print("🧪 URUCHAMIANIE TESTU #1: SPRAWIEDLIWOŚĆ SYSTEMU TICKET RAG")
        print("="*80)
        
        try:
            fairness_output_dir = os.path.join(self.session_dir, "fairness_test")
            fairness_test = FairnessTest(output_dir=fairness_output_dir)
            
            # Lista modeli - możesz rozszerzyć
            models_to_test = [
                MODEL,  # Domyślny model z konfiguracji
                # Dodaj więcej modeli jeśli dostępne:
                # "llama3.1:latest",
                # "gpt-4o-mini"
            ]
            
            print(f"📋 Testowane modele: {models_to_test}")
            
            # Uruchom testy
            results = fairness_test.run_all_tests(models_to_test)
            
            # Podsumowanie
            successful_tests = [r for r in results if "evaluation" in r]
            avg_score = sum(r["evaluation"]["overall_score"] for r in successful_tests) / len(successful_tests) if successful_tests else 0
            
            summary = {
                "test_name": "Sprawiedliwość Ticket RAG",
                "total_tests": len(results),
                "successful_tests": len(successful_tests),
                "average_score": avg_score,
                "models_tested": models_to_test,
                "output_directory": fairness_output_dir,
                "status": "completed"
            }
            
            print(f"\n✅ Test sprawiedliwości zakończony!")
            print(f"📊 Wykonano: {len(results)} testów")
            print(f"📈 Średni wynik: {avg_score:.2f}/5.0")
            print(f"📁 Wyniki w: {fairness_output_dir}")
            
            return {
                "summary": summary,
                "detailed_results": results
            }
            
        except Exception as e:
            error_info = {
                "test": "fairness_test",
                "error": str(e),
                "traceback": traceback.format_exc(),
                "timestamp": datetime.datetime.now().isoformat()
            }
            self.results["errors"].append(error_info)
            
            print(f"\n❌ Błąd w teście sprawiedliwości: {e}")
            return {
                "summary": {"status": "failed", "error": str(e)},
                "detailed_results": []
            }
    
    def run_tools_test(self) -> dict:
        """Uruchamia test narzędzi i agenta."""
        print("\n" + "="*80)
        print("🔧 URUCHAMIANIE TESTU #2: DZIAŁANIE NARZĘDZI I AGENTA")
        print("="*80)
        
        try:
            tools_output_dir = os.path.join(self.session_dir, "tool_test")
            tools_test = ToolsAgentTest(output_dir=tools_output_dir)
            
            print("🚀 Rozpoczynam test narzędzi...")
            
            # Uruchom testy
            results = tools_test.run_all_tests()
            
            # Podsumowanie
            performance = results.get("performance_analysis", {})
            reliability = results.get("tool_reliability", {})
            
            summary = {
                "test_name": "Narzędzia i Agent",
                "total_agent_tests": results["test_summary"]["total_agent_tests"],
                "total_tool_tests": results["test_summary"]["total_individual_tests"],
                "success_rate": performance.get("success_rate", 0),
                "average_score": performance.get("average_score", 0),
                "tool_reliability": reliability.get("reliability_percentage", 0),
                "output_directory": tools_output_dir,
                "status": "completed"
            }
            
            print(f"\n✅ Test narzędzi zakończony!")
            print(f"📊 Testów agenta: {summary['total_agent_tests']}")
            print(f"🔧 Testów narzędzi: {summary['total_tool_tests']}")
            print(f"📈 Wskaźnik sukcesu: {summary['success_rate']:.1f}%")
            print(f"🛠️ Niezawodność narzędzi: {summary['tool_reliability']:.1f}%")
            print(f"📁 Wyniki w: {tools_output_dir}")
            
            return {
                "summary": summary,
                "detailed_results": results
            }
            
        except Exception as e:
            error_info = {
                "test": "tools_test",
                "error": str(e),
                "traceback": traceback.format_exc(),
                "timestamp": datetime.datetime.now().isoformat()
            }
            self.results["errors"].append(error_info)
            
            print(f"\n❌ Błąd w teście narzędzi: {e}")
            return {
                "summary": {"status": "failed", "error": str(e)},
                "detailed_results": {}
            }
    
    def run_all_tests(self):
        """Uruchamia wszystkie testy syntetyczne."""
        print("🎓 TESTY SYNTETYCZNE DLA PRACY MAGISTERSKIEJ")
        print("=" * 60)
        print(f"📅 Data: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🤖 Model: {MODEL}")
        print(f"📁 Katalog wyników: {self.session_dir}")
        print("=" * 60)
        
        # Test 1: Sprawiedliwość
        fairness_results = self.run_fairness_test()
        self.results["test_results"]["fairness_test"] = fairness_results
        
        # Test 2: Narzędzia
        tools_results = self.run_tools_test()
        self.results["test_results"]["tools_test"] = tools_results
        
        # Generuj raport końcowy
        self.generate_final_report()
        
        # Zapisz kompletne wyniki
        self.save_complete_results()
        
        print("\n" + "="*80)
        print("🎉 WSZYSTKIE TESTY ZAKOŃCZONE!")
        print("="*80)
        print(f"📁 Wszystkie wyniki dostępne w: {self.session_dir}")
        print("📋 Pliki do analizy:")
        print(f"   • {os.path.join(self.session_dir, 'complete_results.json')}")
        print(f"   • {os.path.join(self.session_dir, 'final_report.txt')}")
        print(f"   • {os.path.join(self.session_dir, 'summary_for_thesis.json')}")
        
        if self.results["errors"]:
            print(f"\n⚠️  Wystąpiły błędy: {len(self.results['errors'])}")
            print("   Sprawdź szczegóły w pliku complete_results.json")
    
    def generate_final_report(self):
        """Generuje końcowy raport z wszystkich testów."""
        fairness_summary = self.results["test_results"]["fairness_test"]["summary"]
        tools_summary = self.results["test_results"]["tools_test"]["summary"]
        
        # Oblicz ogólne statystyki
        total_tests = 0
        if fairness_summary.get("status") == "completed":
            total_tests += fairness_summary.get("total_tests", 0)
        if tools_summary.get("status") == "completed":
            total_tests += tools_summary.get("total_agent_tests", 0)
        
        self.results["summary"] = {
            "total_tests_executed": total_tests,
            "fairness_test_status": fairness_summary.get("status", "failed"),
            "tools_test_status": tools_summary.get("status", "failed"),
            "model_tested": MODEL,
            "session_duration": "computed_during_save",
            "key_findings": self.extract_key_findings()
        }
        
        # Raport tekstowy
        report_path = os.path.join(self.session_dir, "final_report.txt")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("RAPORT KOŃCOWY - TESTY SYNTETYCZNE DLA PRACY MAGISTERSKIEJ\n")
            f.write("=" * 70 + "\n\n")
            f.write(f"Data wykonania: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Model testowany: {MODEL}\n")
            f.write(f"Łączna liczba testów: {total_tests}\n")
            f.write(f"Identyfikator sesji: {self.timestamp}\n\n")
            
            # Test sprawiedliwości
            f.write("TEST #1: SPRAWIEDLIWOŚĆ SYSTEMU TICKET RAG\n")
            f.write("-" * 50 + "\n")
            if fairness_summary.get("status") == "completed":
                f.write(f"Status: ✅ ZAKOŃCZONY POMYŚLNIE\n")
                f.write(f"Liczba testów: {fairness_summary.get('total_tests', 0)}\n")
                f.write(f"Udane testy: {fairness_summary.get('successful_tests', 0)}\n")
                f.write(f"Średni wynik: {fairness_summary.get('average_score', 0):.2f}/5.0\n")
                f.write(f"Modele testowane: {', '.join(fairness_summary.get('models_tested', []))}\n")
            else:
                f.write(f"Status: ❌ NIEPOWODZENIE\n")
                f.write(f"Błąd: {fairness_summary.get('error', 'Nieznany')}\n")
            f.write("\n")
            
            # Test narzędzi
            f.write("TEST #2: DZIAŁANIE NARZĘDZI I AGENTA\n")
            f.write("-" * 50 + "\n")
            if tools_summary.get("status") == "completed":
                f.write(f"Status: ✅ ZAKOŃCZONY POMYŚLNIE\n")
                f.write(f"Testy agenta: {tools_summary.get('total_agent_tests', 0)}\n")
                f.write(f"Testy narzędzi: {tools_summary.get('total_tool_tests', 0)}\n")
                f.write(f"Wskaźnik sukcesu: {tools_summary.get('success_rate', 0):.1f}%\n")
                f.write(f"Średni wynik: {tools_summary.get('average_score', 0):.2f}/5.0\n")
                f.write(f"Niezawodność narzędzi: {tools_summary.get('tool_reliability', 0):.1f}%\n")
            else:
                f.write(f"Status: ❌ NIEPOWODZENIE\n")
                f.write(f"Błąd: {tools_summary.get('error', 'Nieznany')}\n")
            f.write("\n")
            
            # Kluczowe ustalenia
            f.write("KLUCZOWE USTALENIA DLA PRACY MAGISTERSKIEJ\n")
            f.write("-" * 50 + "\n")
            key_findings = self.extract_key_findings()
            for i, finding in enumerate(key_findings, 1):
                f.write(f"{i}. {finding}\n")
            f.write("\n")
        
        # Uproszczony raport dla pracy magisterskiej
        thesis_summary = {
            "meta": {
                "test_date": datetime.datetime.now().isoformat(),
                "model": MODEL,
                "session_id": self.timestamp,
                "total_tests": total_tests
            },
            "fairness_test": {
                "status": fairness_summary.get("status"),
                "scenarios_tested": 5,  # Jak określono w zadaniu
                "average_score": fairness_summary.get("average_score", 0),
                "key_metrics": {
                    "conflict_resolution_accuracy": "computed_from_detailed_results",
                    "false_accusation_detection": "computed_from_detailed_results",
                    "mediator_protection": "computed_from_detailed_results"
                }
            },
            "tools_test": {
                "status": tools_summary.get("status"),
                "agent_scenarios_tested": tools_summary.get("total_agent_tests", 0),
                "tool_reliability": tools_summary.get("tool_reliability", 0),
                "decision_accuracy": tools_summary.get("average_score", 0),
                "performance_metrics": {
                    "avg_response_time": "computed_from_detailed_results",
                    "success_rate": tools_summary.get("success_rate", 0),
                    "tool_selection_accuracy": "computed_from_detailed_results"
                }
            },
            "conclusions": key_findings
        }
        
        thesis_summary_path = os.path.join(self.session_dir, "summary_for_thesis.json")
        with open(thesis_summary_path, 'w', encoding='utf-8') as f:
            json.dump(thesis_summary, f, ensure_ascii=False, indent=2)
    
    def extract_key_findings(self) -> list:
        """Wyciąga kluczowe ustalenia z testów."""
        findings = []
        
        fairness_summary = self.results["test_results"]["fairness_test"]["summary"]
        tools_summary = self.results["test_results"]["tools_test"]["summary"]
        
        # Ustalenia z testu sprawiedliwości
        if fairness_summary.get("status") == "completed":
            avg_score = fairness_summary.get("average_score", 0)
            if avg_score > 4:
                findings.append("Model wykazuje wysoką sprawiedliwość w ocenie konfliktów")
            elif avg_score > 3:
                findings.append("Model wykazuje umiarkowaną sprawiedliwość z możliwością poprawy")
            else:
                findings.append("Model wymaga znacznej poprawy w zakresie sprawiedliwości ocen")
        
        # Ustalenia z testu narzędzi
        if tools_summary.get("status") == "completed":
            success_rate = tools_summary.get("success_rate", 0)
            reliability = tools_summary.get("tool_reliability", 0)
            
            if success_rate > 80:
                findings.append("Agent wykazuje wysoką skuteczność w wyborze narzędzi")
            else:
                findings.append("Agent wymaga poprawy w zakresie doboru narzędzi")
            
            if reliability > 90:
                findings.append("Narzędzia wykazują wysoką niezawodność")
            elif reliability > 70:
                findings.append("Narzędzia są w większości niezawodne z pewnymi problemami")
            else:
                findings.append("Narzędzia wymagają znacznej poprawy niezawodności")
        
        # Błędy
        if self.results["errors"]:
            findings.append(f"Wykryto {len(self.results['errors'])} błędów podczas testowania")
        
        return findings
    
    def save_complete_results(self):
        """Zapisuje kompletne wyniki do pliku JSON."""
        # Dodaj informacje o czasie trwania
        self.results["session_info"]["completed_at"] = datetime.datetime.now().isoformat()
        
        results_path = os.path.join(self.session_dir, "complete_results.json")
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)

def main():
    """Funkcja główna."""
    print("Temat: Ocena sprawiedliwości i działania narzędzi w systemach LLM")
    print()
    
    # Sprawdź czy wymagane pliki istnieją
    required_files = [
        "src/config.py",
        "src/ticket_rag/__init__.py",
        "src/search_from_internet/__init__.py"
    ]
    
    missing_files = [f for f in required_files if not os.path.exists(f)]
    if missing_files:
        print("❌ Brakujące pliki:")
        for f in missing_files:
            print(f"   • {f}")
        print("\nUpewnij się, że jesteś w głównym folderze projektu.")
        return
    
    try:
        # Uruchom testy
        test_suite = MasterThesisTestSuite(os.path.join(f"runs/run____{MODEL}__{DIR_ID}"))
        test_suite.run_all_tests()
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Testy przerwane przez użytkownika")
    except Exception as e:
        print(f"\n\n❌ Krytyczny błąd: {e}")
        print("Szczegóły:")
        traceback.print_exc()

if __name__ == "__main__":
    main() 