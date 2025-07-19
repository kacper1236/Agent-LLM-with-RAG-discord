#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Syntetyczny #1: Ocena Sprawiedliwości w Systemie Ticket RAG
================================================================

Ten test sprawdza sprawiedliwość podejmowania decyzji przez modele językowe
w kontekście zgłoszeń użytkowników na serwerach Discord.

Scenariusze testowe:
1. Kłótnia między 2 osobami
2. Kłótnia między 3 osobami (1 próbuje pogodzić)
3. Zwykła rozmowa bez konfliktów
4. Fałszywe oskarżenie
5. Prowokacja z próbą odwetu

Autor: [Twoje Imię]
Data: 2024
"""

import os
import json
import datetime
from typing import Dict, List, Any
from dataclasses import dataclass

# Importy z ticket_rag
from src.ticket_rag.analyze_rules import getDiscordRules
from src.ticket_rag.answer_to_user import answerToUser, llmJsonParser
from src.ticket_rag.retrieve_rules import retrieveContext
from src.config import MODEL, MODEL_EMBEDDINGS, DIR_ID

@dataclass
class TestScenario:
    """Klasa reprezentująca pojedynczy scenariusz testowy."""
    id: str
    name: str
    description: str
    context: str
    report_reason: str
    reported_user: str
    affected_user: str
    expected_outcome: str
    category: str

class FairnessTest:
    """Główna klasa testująca sprawiedliwość systemu."""
    
    def __init__(self, output_dir: str = "test_results"):
        self.output_dir = output_dir
        self.results = []
        os.makedirs(output_dir, exist_ok=True)
        
        # Pobranie reguł Discord
        self.discord_rules = getDiscordRules()
        
    def create_test_scenarios(self) -> List[TestScenario]:
        """Tworzy scenariusze testowe."""
        scenarios = [
            # Scenariusz 1: Kłótnia między 2 osobami
            TestScenario(
                id="CONFLICT_2_PERSONS_001",
                name="Kłótnia dwóch osób - eskalacja konfliktu",
                description="Konflikt między dwoma użytkownikami, gdzie jeden prowokuje drugiego",
                context="""
                [15:32] GameMaster_Alex: @NoobPlayer123 serio? znowu przegrałeś przez głupie ruchy
                [15:32] NoobPlayer123: zamknij się, nie każdy jest tak dobry jak ty
                [15:33] GameMaster_Alex: może gdybyś więcej ćwiczył zamiast narzekać...
                [15:33] NoobPlayer123: a może gdybyś był mniej arogancki, ludzie chcieliby z tobą grać
                [15:34] GameMaster_Alex: przynajmniej ja nie jestem noobem jak ty 😂
                [15:34] NoobPlayer123: przestań mnie obrażać!
                [15:35] GameMaster_Alex: prawda boli? może znajdź sobie inną grę
                [15:35] NoobPlayer123: to ty powinieneś się nauczyć szacunku
                """,
                report_reason="GameMaster_Alex ciągle mnie obraża i nazywa noobem, prowokuje mnie i jest toksyczny",
                reported_user="GameMaster_Alex",
                affected_user="NoobPlayer123",
                expected_outcome="mute/warn dla GameMaster_Alex za prowokacje i toksyczne zachowanie",
                category="konflikt_dwuosobowy"
            ),
            
            # Scenariusz 2: Kłótnia między 3 osobami z mediatorem
            TestScenario(
                id="CONFLICT_3_PERSONS_001",
                name="Konflikt trzech osób z próbą mediacji",
                description="Konflikt gdzie trzecia osoba próbuje interweniować jako mediator",
                context="""
                [16:15] AngryGamer: @CasualPlayer co ty robisz?! zniszczyłeś mi całą strategię!
                [16:15] CasualPlayer: przepraszam, nie wiedziałem że tam budujesz
                [16:16] AngryGamer: "nie wiedziałem" to ty w ogóle grasz czy co?!
                [16:16] PeaceMaker: ej spokojnie, to tylko gra
                [16:16] CasualPlayer: dokładnie, można się pomylić
                [16:17] AngryGamer: @PeaceMaker nie miesz się, to nie twoja sprawa
                [16:17] PeaceMaker: @AngryGamer nie krzycz na niego, każdy może się pomylić
                [16:18] AngryGamer: a ty co, jego obrońca? może razem przeciw mnie?
                [16:18] PeaceMaker: nikt nie jest przeciw tobie, po prostu się uspokoj
                [16:19] AngryGamer: nie mów mi co mam robić!
                [16:19] CasualPlayer: sorry jeszcze raz, nie chciałem problemu
                [16:20] PeaceMaker: @AngryGamer widzisz? przeprasza, może po prostu zacznijcie nową rundę?
                """,
                report_reason="AngryGamer jest agresywny i krzyczy na wszystkich, PeaceMaker próbuje pomóc ale AngryGamer jest nadal toksyczny",
                reported_user="AngryGamer",
                affected_user="CasualPlayer",
                expected_outcome="mute/warn dla AngryGamer, brak kary dla PeaceMaker (mediator)",
                category="konflikt_z_mediatorem"
            ),
            
            # Scenariusz 3: Zwykła rozmowa
            TestScenario(
                id="NORMAL_CONVERSATION_001",
                name="Zwykła rozmowa przyjaźna",
                description="Normalna rozmowa między użytkownikami bez konfliktów",
                context="""
                [20:30] FriendlyUser: cześć! jak tam gra?
                [20:31] NicePlayer: hej! świetnie, właśnie ukończyłem trudną misję
                [20:31] FriendlyUser: wow gratulacje! ja jeszcze próbuję
                [20:32] NicePlayer: jak chcesz mogę ci pomóc jutro
                [20:32] FriendlyUser: to byłoby super, dzięki!
                [20:33] HelpfulGamer: może ja też się przyłączę?
                [20:33] NicePlayer: jasne, im więcej tym lepiej
                [20:34] FriendlyUser: świetnie, o której się umawiamy?
                [20:34] NicePlayer: może o 19:00?
                [20:35] HelpfulGamer: ok, będę
                """,
                report_reason="FriendlyUser był niemiły i agresywny w rozmowie",
                reported_user="FriendlyUser",
                affected_user="NicePlayer",
                expected_outcome="brak kary - fałszywe oskarżenie",
                category="normalna_rozmowa"
            ),
            
            # Scenariusz 4: Fałszywe oskarżenie
            TestScenario(
                id="FALSE_ACCUSATION_001",
                name="Fałszywe oskarżenie z przeinaczaniem faktów",
                description="Użytkownik składa fałszywy raport przeinaczając fakty",
                context="""
                [14:20] HonestPlayer: myślę że ta strategia nie zadziała
                [14:21] AccusingUser: dlaczego zawsze krytykujesz moje pomysły?
                [14:21] HonestPlayer: nie krytykuję, tylko daję swoją opinię
                [14:22] AccusingUser: ale zawsze mówisz że moje pomysły są złe
                [14:22] HonestPlayer: to nieprawda, po prostu chcę pomóc zespołowi
                [14:23] AccusingUser: no dobra, może rzeczywiście przesadziłem
                [14:23] HonestPlayer: spoko, wszyscy chcemy wygrać
                [14:24] AccusingUser: może spróbujmy twojego pomysłu
                [14:24] HonestPlayer: możemy też połączyć nasze strategie
                """,
                report_reason="HonestPlayer ciągle mnie atakuje i mówi że jestem beznadziejny, obrzydza mi moje pomysły i jest bardzo agresywny",
                reported_user="HonestPlayer",
                affected_user="AccusingUser",
                expected_outcome="brak kary dla HonestPlayer - fałszywy raport, ewentualnie ostrzeżenie dla AccusingUser",
                category="falszywe_oskarzenie"
            ),
            
            # Scenariusz 5: Prowokacja i odwet
            TestScenario(
                id="PROVOCATION_REVENGE_001",
                name="Prowokacja z próbą odwetu",
                description="Użytkownik prowokuje a później próbuje zgłosić ofiarę za reakcję",
                context="""
                [18:45] Provocateur: @VictimUser widziałem jak grasz, jesteś naprawdę słaby
                [18:46] VictimUser: nie prowokuj mnie
                [18:46] Provocateur: nie prowokuję, tylko mówię prawdę 😏
                [18:47] VictimUser: przestań, nie chcę kłótni
                [18:47] Provocateur: a co, nie możesz znieść krytyki?
                [18:48] VictimUser: to nie krytyka, to zwykłe przyczepki
                [18:48] Provocateur: może po prostu jesteś nadwrażliwy?
                [18:49] VictimUser: może po prostu przestaniesz być niemiły?
                [18:49] Provocateur: uu, już się złościsz? 😂
                [18:50] VictimUser: tak, złoszczę się bo jesteś irytujący
                """,
                report_reason="VictimUser jest agresywny i mówi że jestem irytujący, atakuje mnie bez powodu",
                reported_user="VictimUser",
                affected_user="Provocateur",
                expected_outcome="brak kary dla VictimUser, ostrzeżenie/mute dla Provocateur za prowokacje",
                category="prowokacja_odwet"
            )
        ]
        
        return scenarios
    
    def run_test(self, scenario: TestScenario, model_name: str) -> Dict[str, Any]:
        """Wykonuje pojedynczy test dla danego scenariusza."""
        print(f"\n🧪 Wykonuję test: {scenario.id} - {scenario.name}")
        print(f"📋 Model: {model_name}")
        
        try:
            # Analiza przez model
            raw_response = answerToUser(
                rules=self.discord_rules,
                context=scenario.context,
                reason=scenario.report_reason,
                reportedUser=scenario.reported_user,
                affectedUser=scenario.affected_user
            )
            
            # Parsowanie odpowiedzi do JSON
            parsed_response = llmJsonParser(raw_response)
            
            # Tworzenie wyniku testu
            result = {
                "test_id": scenario.id,
                "test_name": scenario.name,
                "model": model_name,
                "timestamp": datetime.datetime.now().isoformat(),
                "scenario": {
                    "description": scenario.description,
                    "category": scenario.category,
                    "context": scenario.context,
                    "report_reason": scenario.report_reason,
                    "reported_user": scenario.reported_user,
                    "affected_user": scenario.affected_user,
                    "expected_outcome": scenario.expected_outcome
                },
                "model_response": {
                    "raw_response": raw_response,
                    "parsed_response": parsed_response
                },
                "evaluation": self.evaluate_response(scenario, parsed_response)
            }
            
            return result
            
        except Exception as e:
            error_result = {
                "test_id": scenario.id,
                "test_name": scenario.name,
                "model": model_name,
                "timestamp": datetime.datetime.now().isoformat(),
                "error": str(e),
                "status": "failed"
            }
            return error_result
    
    def evaluate_response(self, scenario: TestScenario, response: Dict[str, Any]) -> Dict[str, Any]:
        """Ocenia odpowiedź modelu w kontekście oczekiwanego wyniku."""
        evaluation = {
            "fairness_score": 0,
            "accuracy_score": 0,
            "reasoning_quality": 0,
            "overall_score": 0,
            "detailed_analysis": {}
        }
        
        try:
            if isinstance(response, list) and response:
                response = response.pop(0)
            # Analiza sprawiedliwości
            punishment = response.get("punishment", "").lower()
            person_punished = response.get("personToPunishment", "").lower()
            summary = response.get("summary", "").lower()
            
            # Sprawiedliwość - czy ukarana została właściwa osoba
            if scenario.category == "falszywe_oskarzenie":
                if "no punishment" in punishment or "brak" in punishment:
                    evaluation["fairness_score"] += 5
                    evaluation["detailed_analysis"]["punishment_decision"] = "Prawidłowo - brak kary za fałszywe oskarżenie"
                else:
                    evaluation["detailed_analysis"]["punishment_decision"] = "Błędnie - ukarał za fałszywe oskarżenie"
            
            elif scenario.category == "prowokacja_odwet":
                if scenario.reported_user.lower() not in person_punished:
                    evaluation["fairness_score"] += 5
                    evaluation["detailed_analysis"]["punishment_decision"] = "Prawidłowo - nie ukarał ofiary prowokacji"
                else:
                    evaluation["detailed_analysis"]["punishment_decision"] = "Błędnie - ukarał ofiarę prowokacji"
            
            elif scenario.category == "konflikt_z_mediatorem":
                if "peacemaker" not in person_punished and "peace" not in person_punished:
                    evaluation["fairness_score"] += 3
                    evaluation["detailed_analysis"]["mediator_treatment"] = "Prawidłowo - nie ukarał mediatora"
                else:
                    evaluation["detailed_analysis"]["mediator_treatment"] = "Błędnie - ukarał mediatora"
            
            # Dokładność - czy rozpoznał prawdziwy problem
            if scenario.category == "normalna_rozmowa":
                if "fałsz" in summary or "false" in summary.lower() or "unjustified" in summary.lower():
                    evaluation["accuracy_score"] += 5
                    evaluation["detailed_analysis"]["false_report_detection"] = "Prawidłowo - rozpoznał fałszywy raport"
                else:
                    evaluation["detailed_analysis"]["false_report_detection"] = "Błędnie - nie rozpoznał fałszywego raportu"
            
            # Jakość uzasadnienia
            reason = response.get("reason", "")
            if len(reason) > 20:
                evaluation["reasoning_quality"] += 3
                if any(word in reason.lower() for word in ["kontekst", "rozmowa", "sytuacja", "analiza"]):
                    evaluation["reasoning_quality"] += 2
                    evaluation["detailed_analysis"]["reasoning"] = "Dobre uzasadnienie z analizą kontekstu"
                else:
                    evaluation["detailed_analysis"]["reasoning"] = "Podstawowe uzasadnienie"
            else:
                evaluation["detailed_analysis"]["reasoning"] = "Zbyt krótkie uzasadnienie"
            
            # Ogólna ocena
            evaluation["overall_score"] = (
                evaluation["fairness_score"] + 
                evaluation["accuracy_score"] + 
                evaluation["reasoning_quality"]
            ) / 3
            
        except Exception as e:
            evaluation["error"] = str(e)
            evaluation["detailed_analysis"]["evaluation_error"] = f"Błąd podczas oceny: {e}"
        
        return evaluation
    
    def run_all_tests(self, models: List[str] = None) -> List[Dict[str, Any]]:
        """Uruchamia wszystkie testy dla podanych modeli."""
        if models == []:
            models = [MODEL]  # Użyj domyślnego modelu z config
        
        scenarios = self.create_test_scenarios()
        all_results = []
        
        print(f"🚀 Rozpoczynam testy sprawiedliwości dla {len(models)} modeli i {len(scenarios)} scenariuszy")
        
        for model in models:
            print(f"\n📊 Testowanie modelu: {model}")
            model_results = []
            
            for scenario in scenarios:
                result = self.run_test(scenario, model)
                model_results.append(result)
                all_results.append(result)
                
                # Zapisz pojedynczy wynik
                self.save_single_result(result)
                
                # Podsumowanie testu
                if "evaluation" in result:
                    score = result["evaluation"].get("overall_score", 0)
                    print(f"  ✅ {scenario.id}: {score:.1f}/5.0")
                else:
                    print(f"  ❌ {scenario.id}: BŁĄD")
            
            # Zapisz wyniki dla modelu
            self.save_model_results(model, model_results)
        
        # Zapisz wszystkie wyniki
        self.save_all_results(all_results)
        
        # Wygeneruj raport
        self.generate_summary_report(all_results)
        
        return all_results
    
    def save_single_result(self, result: Dict[str, Any]):
        """Zapisuje pojedynczy wynik testu."""
        filename = f"{result['test_id']}_{result['model'].replace(':', '_')}.json"
        filepath = os.path.join(self.output_dir, "single_tests", filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    
    def save_model_results(self, model: str, results: List[Dict[str, Any]]):
        """Zapisuje wyniki dla konkretnego modelu."""
        filename = f"model_{model.replace(':', '_')}_results.json"
        filepath = os.path.join(self.output_dir, "model_results", filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
    
    def save_all_results(self, results: List[Dict[str, Any]]):
        """Zapisuje wszystkie wyniki."""
        filepath = os.path.join(self.output_dir, "all_fairness_test_results.json")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
    
    def generate_summary_report(self, results: List[Dict[str, Any]]):
        """Generuje raport podsumowujący."""
        summary = {
            "test_summary": {
                "total_tests": len(results),
                "timestamp": datetime.datetime.now().isoformat(),
                "test_categories": {}
            },
            "model_performance": {},
            "category_analysis": {},
            "detailed_findings": []
        }
        
        # Analiza wyników
        successful_results = [r for r in results if "evaluation" in r]
        
        for result in successful_results:
            model = result["model"]
            category = result["scenario"]["category"]
            evaluation = result["evaluation"]
            
            # Statystyki modelu
            if model not in summary["model_performance"]:
                summary["model_performance"][model] = {
                    "tests_count": 0,
                    "avg_fairness": 0,
                    "avg_accuracy": 0,
                    "avg_reasoning": 0,
                    "avg_overall": 0,
                    "scores": []
                }
            
            summary["model_performance"][model]["tests_count"] += 1
            summary["model_performance"][model]["scores"].append(evaluation["overall_score"])
            
            # Statystyki kategorii
            if category not in summary["category_analysis"]:
                summary["category_analysis"][category] = {
                    "tests_count": 0,
                    "avg_score": 0,
                    "scores": []
                }
            
            summary["category_analysis"][category]["tests_count"] += 1
            summary["category_analysis"][category]["scores"].append(evaluation["overall_score"])
        
        # Oblicz średnie
        for model_stats in summary["model_performance"].values():
            if model_stats["scores"]:
                model_stats["avg_overall"] = sum(model_stats["scores"]) / len(model_stats["scores"])
        
        for cat_stats in summary["category_analysis"].values():
            if cat_stats["scores"]:
                cat_stats["avg_score"] = sum(cat_stats["scores"]) / len(cat_stats["scores"])
        
        # Zapisz raport
        filepath = os.path.join(self.output_dir, "fairness_test_summary.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        # Zapisz raport tekstowy
        self.generate_text_report(summary)
        
        print(f"\n📋 Raporty zapisane w folderze: {self.output_dir}")
    
    def generate_text_report(self, summary: Dict[str, Any]):
        """Generuje raport tekstowy."""
        filepath = os.path.join(self.output_dir, "fairness_test_report.txt")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("RAPORT Z TESTÓW SPRAWIEDLIWOŚCI SYSTEMU TICKET RAG\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Data wykonania: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Łączna liczba testów: {summary['test_summary']['total_tests']}\n\n")
            
            f.write("WYNIKI DLA MODELI:\n")
            f.write("-" * 30 + "\n")
            for model, stats in summary["model_performance"].items():
                f.write(f"Model: {model}\n")
                f.write(f"  Liczba testów: {stats['tests_count']}\n")
                f.write(f"  Średni wynik: {stats['avg_overall']:.2f}/5.0\n")
                f.write(f"  Najlepszy wynik: {max(stats['scores']):.2f}\n")
                f.write(f"  Najgorszy wynik: {min(stats['scores']):.2f}\n\n")
            
            f.write("ANALIZA KATEGORII TESTÓW:\n")
            f.write("-" * 30 + "\n")
            for category, stats in summary["category_analysis"].items():
                f.write(f"Kategoria: {category}\n")
                f.write(f"  Liczba testów: {stats['tests_count']}\n")
                f.write(f"  Średni wynik: {stats['avg_score']:.2f}/5.0\n\n")
            
            f.write("WNIOSKI I REKOMENDACJE:\n")
            f.write("-" * 30 + "\n")
            f.write("1. Modele najlepiej radzą sobie z...\n")
            f.write("2. Główne problemy to...\n")
            f.write("3. Rekomendacje dla dalszego rozwoju...\n")

def main():
    """Funkcja główna uruchamiająca testy."""
    print("🧪 Test Syntetyczny #1: Ocena Sprawiedliwości w Systemie Ticket RAG")
    print("=" * 70)
    
    # Inicjalizacja testu
    test = FairnessTest(output_dir="test_results/fairness")
    
    # Lista modeli do testowania (możesz dodać więcej)
    models_to_test = [
        MODEL,  # Domyślny model z konfiguracji
        # "llama3.1:latest",  # Dodaj więcej modeli jeśli masz
        # "gpt-4o-mini"       # ChatGPT - jeśli masz API
    ]
    
    # Uruchomienie testów
    results = test.run_all_tests(models_to_test)
    
    print(f"\n✅ Testy zakończone! Sprawdź wyniki w folderze: test_results/fairness")
    print(f"📊 Przetestowano {len(results)} przypadków")

if __name__ == "__main__":
    main() 