"""
Script de démonstration : génère des données de session factices
et un rapport PDF de démonstration.

Usage:
    python generate_sample_report.py
"""

import os
import sys
import json
import random
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

SESSIONS_DIR = "data/sessions"
os.makedirs(SESSIONS_DIR, exist_ok=True)

# ─── Exercices possibles ──────────────────────────────────────────────────────
EXERCISE_TEMPLATES = [
    {"name": "Flexion epaule gauche", "target_reps": 10, "angle_range": (80, 150)},
    {"name": "Flexion epaule droite", "target_reps": 10, "angle_range": (80, 150)},
    {"name": "Abduction epaule gauche", "target_reps": 10, "angle_range": (70, 140)},
    {"name": "Flexion coude droit", "target_reps": 10, "angle_range": (90, 130)},
    {"name": "Flexion bilaterale epaules", "target_reps": 10, "angle_range": (80, 145)},
    {"name": "Extension genou gauche", "target_reps": 10, "angle_range": (50, 120)},
    {"name": "Flexion hanche droite", "target_reps": 10, "angle_range": (40, 100)},
    {"name": "Inclinaison tronc gauche (assis)", "target_reps": 8, "angle_range": (10, 20)},
    {"name": "Transfert de poids lateral (debout)", "target_reps": 8, "angle_range": (5, 15)},
]


def generate_sample_exercise(template: dict, session_num: int) -> dict:
    """Génère un exercice avec des données réalistes."""
    # Simuler une amélioration progressive
    improvement = min(session_num * 2, 15)

    total_reps = min(template["target_reps"],
                     random.randint(template["target_reps"] - 3 + min(session_num, 3),
                                    template["target_reps"]))
    low, high = template["angle_range"]
    avg_amp = random.uniform(low + improvement, high + improvement * 0.5)
    max_amp = avg_amp + random.uniform(5, 20)
    comp_count = max(0, random.randint(0, 5) - session_num)

    # Score
    rep_score = (total_reps / template["target_reps"]) * 40
    amp_score = min(30, (avg_amp / (high - low)) * 30)
    comp_penalty = min(30, comp_count * 3)
    score = max(0, min(100, rep_score + amp_score + 30 - comp_penalty))

    comp_summary = {"total": comp_count, "types": {}}
    if comp_count > 0:
        comp_types = ["TRUNK_LEAN", "SHOULDER_ELEVATION", "HIP_SHIFT"]
        chosen = random.choice(comp_types)
        comp_summary["types"][chosen] = {
            "count": comp_count,
            "max_severity": random.choice(["mild", "moderate"]),
        }

    return {
        "exercise_name": template["name"],
        "total_reps": total_reps,
        "target_reps": template["target_reps"],
        "avg_amplitude": round(avg_amp, 1),
        "max_amplitude": round(max_amp, 1),
        "compensations_count": comp_count,
        "duration_seconds": round(random.uniform(30, 90), 1),
        "score": round(score, 1),
        "rep_details": [],
        "compensation_summary": comp_summary,
    }


def generate_sample_session(patient_id: str, date: datetime, session_num: int) -> dict:
    """Génère une session complète avec des données factices."""
    num_exercises = random.randint(4, 7)
    templates = random.sample(EXERCISE_TEMPLATES, min(num_exercises, len(EXERCISE_TEMPLATES)))

    exercises = [generate_sample_exercise(t, session_num) for t in templates]
    avg_score = sum(e["score"] for e in exercises) / len(exercises)
    total_duration = sum(e["duration_seconds"] for e in exercises) + random.uniform(60, 180)

    session_id = date.strftime("%Y%m%d_%H%M%S")

    return {
        "session_id": session_id,
        "patient_id": patient_id,
        "date": date.isoformat(),
        "total_duration_seconds": round(total_duration, 1),
        "exercises_completed": len(exercises),
        "avg_score": round(avg_score, 1),
        "exercises": exercises,
    }


def main():
    """Génère des sessions factices et un rapport PDF de démonstration."""
    print("=" * 50)
    print("  GENERATION DE DONNEES DE DEMONSTRATION")
    print("=" * 50)

    patients = ["patient001", "patient002", "patient003"]
    all_sessions = []

    for patient in patients:
        num_sessions = random.randint(5, 8)
        start_date = datetime.now() - timedelta(weeks=num_sessions * 2)

        print(f"\nPatient : {patient} ({num_sessions} sessions)")

        for i in range(num_sessions):
            date = start_date + timedelta(weeks=i, days=random.randint(0, 3),
                                          hours=random.randint(9, 16))
            session = generate_sample_session(patient, date, i)
            all_sessions.append(session)

            # Sauvegarder en JSON
            filename = f"session_{patient}_{session['session_id']}.json"
            filepath = os.path.join(SESSIONS_DIR, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(session, f, ensure_ascii=False, indent=2)
            print(f"  - {filename} (score: {session['avg_score']:.1f})")

    print(f"\n{len(all_sessions)} sessions generees dans {SESSIONS_DIR}/")

    # ── Générer un rapport PDF de démonstration ───────────────────────────
    try:
        from data.pdf_report import SessionReportPDF

        reporter = SessionReportPDF()

        # Rapport de la dernière session
        last = all_sessions[-1]
        pdf_session = os.path.join(SESSIONS_DIR, "sample_report_session.pdf")
        reporter.generate_session_report(last, pdf_session)

        # Rapport patient
        p1_sessions = [s for s in all_sessions if s["patient_id"] == "patient001"]
        pdf_patient = os.path.join(SESSIONS_DIR, "sample_report_patient.pdf")
        reporter.generate_patient_report("patient001", p1_sessions, pdf_patient)

        # Rapport global
        pdf_global = os.path.join(SESSIONS_DIR, "sample_report_global.pdf")
        reporter.generate_summary_report(all_sessions, pdf_global)

        print(f"\nRapports PDF generes :")
        print(f"  - {pdf_session}")
        print(f"  - {pdf_patient}")
        print(f"  - {pdf_global}")

    except ImportError:
        print("\n[!] fpdf2 non installe, rapports PDF ignores.")
        print("    Installez avec : pip install fpdf2")

    print("\nPour lancer le dashboard :")
    print("  streamlit run dashboard/app.py")


if __name__ == "__main__":
    main()
