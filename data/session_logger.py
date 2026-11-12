"""
Enregistrement des données de session.

Sauvegarde les résultats de chaque session d'exercice
dans un fichier JSON pour le suivi longitudinal.
"""

import json
import os
import time
from datetime import datetime
from typing import List, Optional, Dict
from dataclasses import asdict

from exercises.base import ExerciseResult


class SessionLogger:
    """
    Enregistre les données des sessions d'exercice.

    Les fichiers sont sauvegardés au format JSON dans le dossier
    data/sessions/, avec un fichier par session.
    """

    def __init__(self, log_dir: str = "data/sessions", patient_id: str = "default"):
        self.log_dir = log_dir
        self.patient_id = patient_id
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results: List[Dict] = []
        self._start_time = time.time()

        os.makedirs(log_dir, exist_ok=True)

    def log_exercise(self, result: ExerciseResult):
        """Ajoute le résultat d'un exercice à la session."""
        self.results.append({
            "exercise_name": result.exercise_name,
            "total_reps": result.total_reps,
            "target_reps": result.target_reps,
            "avg_amplitude": round(result.avg_amplitude, 1),
            "max_amplitude": round(result.max_amplitude, 1),
            "compensations_count": result.compensations_count,
            "duration_seconds": result.duration_seconds,
            "score": result.score,
            "rep_details": result.rep_details,
            "compensation_summary": result.compensation_summary,
        })

    def save(self):
        """Sauvegarde la session complète dans un fichier JSON."""
        session_data = {
            "session_id": self.session_id,
            "patient_id": self.patient_id,
            "date": datetime.now().isoformat(),
            "total_duration_seconds": round(time.time() - self._start_time, 1),
            "exercises_completed": len(self.results),
            "avg_score": self._avg_score(),
            "exercises": self.results,
        }

        filepath = os.path.join(
            self.log_dir, f"session_{self.patient_id}_{self.session_id}.json"
        )
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)

        print(f"[Session] Données sauvegardées dans {filepath}")
        return filepath

    def _avg_score(self) -> float:
        """Score moyen de la session."""
        if not self.results:
            return 0.0
        return round(
            sum(r["score"] for r in self.results) / len(self.results), 1
        )

    def get_summary(self) -> str:
        """Résumé textuel de la session."""
        total_reps = sum(r["total_reps"] for r in self.results)
        total_comp = sum(r["compensations_count"] for r in self.results)
        duration = round(time.time() - self._start_time, 0)

        return (
            f"📊 Résumé de la session\n"
            f"─────────────────────────\n"
            f"Patient : {self.patient_id}\n"
            f"Exercices : {len(self.results)}\n"
            f"Répétitions totales : {total_reps}\n"
            f"Compensations : {total_comp}\n"
            f"Score moyen : {self._avg_score()}/100\n"
            f"Durée : {int(duration // 60)}min {int(duration % 60)}s\n"
        )
