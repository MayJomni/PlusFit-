"""
Mode démonstration du Miroir de Rééducation PlusFit.

Lance une simulation complète d'une session de rééducation
dans le terminal, sans webcam ni TensorFlow requis.

Usage:
    python run_demo.py
"""

import sys
import os
import time
import random
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from exercises.catalog import get_all_exercises

# ─── Couleurs terminal ───────────────────────────────────────────────────────
try:
    from colorama import Fore, Style, init
    init()
except ImportError:
    class Fore:
        GREEN = YELLOW = RED = CYAN = BLUE = MAGENTA = WHITE = ""
    class Style:
        BRIGHT = RESET_ALL = ""


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def print_banner():
    """Affiche le bandeau du projet."""
    print(f"\n{Fore.CYAN}{'═' * 60}")
    print(f"  🪞  MIROIR DE RÉÉDUCATION — PlusFit")
    print(f"  Mode démonstration (simulation sans webcam)")
    print(f"{'═' * 60}{Style.RESET_ALL}\n")


def print_progress_bar(current, total, width=30, label=""):
    """Affiche une barre de progression."""
    pct = current / total if total > 0 else 0
    filled = int(width * pct)
    bar = "█" * filled + "░" * (width - filled)
    color = Fore.GREEN if pct >= 0.8 else Fore.YELLOW if pct >= 0.5 else Fore.RED
    print(f"  {label} {color}[{bar}] {pct*100:.0f}%{Style.RESET_ALL}")


def print_score_badge(score):
    """Affiche un badge coloré selon le score."""
    if score >= 90:
        return f"{Fore.GREEN}{Style.BRIGHT}★ EXCELLENT ({score:.0f}/100){Style.RESET_ALL}"
    elif score >= 75:
        return f"{Fore.YELLOW}{Style.BRIGHT}● BON ({score:.0f}/100){Style.RESET_ALL}"
    else:
        return f"{Fore.RED}{Style.BRIGHT}▲ À AMÉLIORER ({score:.0f}/100){Style.RESET_ALL}"


def simulate_exercise(exercise, exercise_num, total_exercises):
    """Simule un exercice complet avec affichage en temps réel."""
    name = exercise.name
    target_reps = exercise.target_reps
    target_angle = 120  # angle cible par défaut

    print(f"\n{Fore.BLUE}{'─' * 60}")
    print(f"  EXERCICE {exercise_num}/{total_exercises} : {name.upper()}")
    print(f"{'─' * 60}{Style.RESET_ALL}")
    print(f"  Objectif : {target_reps} répétitions")
    print(f"  Angle cible : {target_angle}°")
    print()

    # Simuler les répétitions
    comp_types = ["TRUNK_LEAN", "SHOULDER_ELEVATION", "HIP_SHIFT"]
    comp_labels = {
        "TRUNK_LEAN": "⚠️  Inclinaison du tronc détectée !",
        "SHOULDER_ELEVATION": "⚠️  Élévation de l'épaule détectée !",
        "HIP_SHIFT": "⚠️  Déplacement de la hanche détecté !",
    }

    reps_done = 0
    compensations = 0
    amplitudes = []
    start_time = time.time()

    for rep in range(target_reps):
        # Simuler le mouvement (montée)
        angle = 30
        steps = random.randint(8, 15)
        max_angle = random.uniform(target_angle * 0.7, target_angle * 1.1)

        for step in range(steps):
            angle = 30 + (max_angle - 30) * (step / steps)
            progress = min(1.0, (angle - 30) / (target_angle - 30))

            # Affichage en temps réel
            bar_width = 25
            filled = int(bar_width * progress)
            bar = "█" * filled + "░" * (bar_width - filled)
            color = Fore.GREEN if progress >= 0.8 else Fore.YELLOW if progress >= 0.5 else Fore.WHITE

            status = f"  Rep {rep+1}/{target_reps}  {color}[{bar}] {angle:.0f}°/{target_angle}°{Style.RESET_ALL}"
            print(f"\r{status}", end="", flush=True)
            time.sleep(0.03)

        # Résultat de la rep
        amplitudes.append(max_angle)
        reps_done += 1

        # Compensation aléatoire (plus probable au début)
        if random.random() < max(0, 0.3 - rep * 0.03):
            comp = random.choice(comp_types)
            compensations += 1
            print(f"\r  Rep {rep+1}/{target_reps}  {Fore.YELLOW}{comp_labels[comp]}{Style.RESET_ALL}          ")
        else:
            print(f"\r  Rep {rep+1}/{target_reps}  {Fore.GREEN}✓ Mouvement correct (amplitude: {max_angle:.0f}°){Style.RESET_ALL}          ")

        time.sleep(0.15)

    # Résumé de l'exercice
    duration = time.time() - start_time
    avg_amp = sum(amplitudes) / len(amplitudes) if amplitudes else 0
    rep_score = (reps_done / target_reps) * 40
    amp_score = min(30, (avg_amp / target_angle) * 30)
    comp_penalty = min(30, compensations * 5)
    score = max(0, min(100, rep_score + amp_score + 30 - comp_penalty))

    print(f"\n  {Fore.CYAN}┌─────────────────────────────────────┐")
    print(f"  │  Résultat : {name:<24s}│")
    print(f"  ├─────────────────────────────────────┤")
    print(f"  │  Répétitions : {reps_done}/{target_reps}                    │")
    print(f"  │  Amplitude moy. : {avg_amp:.0f}°                │")
    print(f"  │  Compensations : {compensations}                     │")
    print(f"  │  Durée : {duration:.1f}s                        │")
    print(f"  │  Score : {print_score_badge(score):>42s} │")
    print(f"  └─────────────────────────────────────┘{Style.RESET_ALL}")

    return {
        "exercise_name": name,
        "total_reps": reps_done,
        "target_reps": target_reps,
        "avg_amplitude": round(avg_amp, 1),
        "max_amplitude": round(max(amplitudes), 1) if amplitudes else 0,
        "compensations_count": compensations,
        "duration_seconds": round(duration, 1),
        "score": round(score, 1),
        "rep_details": [],
        "compensation_summary": {"total": compensations, "types": {}},
    }


def main():
    """Lance la démonstration complète."""
    clear_screen()
    print_banner()

    # Choisir un patient
    patient_id = "demo_patient"
    print(f"  {Fore.WHITE}{Style.BRIGHT}Patient : {patient_id}{Style.RESET_ALL}")
    print(f"  Date : {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    # Sélectionner 5 exercices du catalogue
    all_exercises = get_all_exercises()
    selected = random.sample(all_exercises, min(5, len(all_exercises)))

    print(f"\n  {Fore.MAGENTA}Programme de la session ({len(selected)} exercices) :{Style.RESET_ALL}")
    for i, ex in enumerate(selected, 1):
        cat_str = str(ex.category.value) if hasattr(ex.category, 'value') else str(ex.category)
        cat_icon = {"upper_limb": "💪", "lower_limb": "🦵", "balance": "⚖️"}.get(cat_str, "🏋️")
        cog = " 🧠" if ex.has_cognitive_task else ""
        print(f"    {i}. {cat_icon} {ex.name}{cog}")

    print(f"\n  {Fore.YELLOW}Démarrage dans 3 secondes...{Style.RESET_ALL}")
    time.sleep(2)

    # Lancer les exercices
    results = []
    session_start = time.time()

    for i, ex in enumerate(selected, 1):
        result = simulate_exercise(ex, i, len(selected))
        results.append(result)

        if i < len(selected):
            print(f"\n  {Fore.YELLOW}⏸  Pause de 2s avant l'exercice suivant...{Style.RESET_ALL}")
            time.sleep(1.5)

    # ─── Résumé de la session ─────────────────────────────────────────────
    total_duration = time.time() - session_start
    avg_score = sum(r["score"] for r in results) / len(results)
    total_reps = sum(r["total_reps"] for r in results)
    total_comp = sum(r["compensations_count"] for r in results)

    print(f"\n\n{Fore.CYAN}{'═' * 60}")
    print(f"  📊  RÉSUMÉ DE LA SESSION")
    print(f"{'═' * 60}{Style.RESET_ALL}")
    print(f"""
  Patient           : {patient_id}
  Exercices réalisés: {len(results)}/{len(selected)}
  Répétitions total : {total_reps}
  Compensations     : {total_comp}
  Durée totale      : {total_duration:.0f}s ({total_duration/60:.1f} min)
  Score moyen       : {print_score_badge(avg_score)}
""")

    # Classement des exercices
    print(f"  {Fore.WHITE}{Style.BRIGHT}Classement par score :{Style.RESET_ALL}")
    for r in sorted(results, key=lambda x: x["score"], reverse=True):
        badge = "🥇" if r["score"] >= 95 else "🥈" if r["score"] >= 85 else "🥉"
        print(f"    {badge} {r['exercise_name']:<35s} {r['score']:.0f}/100")

    # Sauvegarder la session en JSON
    save_dir = os.path.join("data", "sessions")
    os.makedirs(save_dir, exist_ok=True)

    session_data = {
        "session_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "patient_id": patient_id,
        "date": datetime.now().isoformat(),
        "total_duration_seconds": round(total_duration, 1),
        "exercises_completed": len(results),
        "avg_score": round(avg_score, 1),
        "exercises": results,
    }

    session_file = os.path.join(save_dir, f"session_{patient_id}_{session_data['session_id']}.json")
    with open(session_file, "w", encoding="utf-8") as f:
        json.dump(session_data, f, ensure_ascii=False, indent=2)
    print(f"\n  {Fore.GREEN}💾 Session sauvegardée : {session_file}{Style.RESET_ALL}")

    # Générer un rapport PDF si fpdf2 est disponible
    try:
        from data.pdf_report import SessionReportPDF

        pdf_path = os.path.join(save_dir, "demo_report.pdf")
        reporter = SessionReportPDF()
        reporter.generate_session_report(session_data, pdf_path)
        print(f"  {Fore.GREEN}📄 Rapport PDF généré : {pdf_path}{Style.RESET_ALL}")
    except Exception as e:
        print(f"  {Fore.YELLOW}⚠ PDF non généré : {e}{Style.RESET_ALL}")

    print(f"\n{Fore.CYAN}{'═' * 60}")
    print(f"  ✅ Session de démonstration terminée !")
    print(f"{'═' * 60}{Style.RESET_ALL}\n")


if __name__ == "__main__":
    main()
