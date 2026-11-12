"""
Chargement des données de session depuis les fichiers JSON.

Scanne le dossier data/sessions/ et charge toutes les sessions
dans des DataFrames pandas pour le tableau de bord.
"""

import os
import json
import pandas as pd
from typing import List
from datetime import datetime


def load_all_sessions(sessions_dir: str = "data/sessions") -> pd.DataFrame:
    """
    Charge toutes les sessions depuis le dossier JSON.

    Returns:
        DataFrame avec une ligne par session.
    """
    sessions = []
    if not os.path.exists(sessions_dir):
        return pd.DataFrame()

    for filename in sorted(os.listdir(sessions_dir)):
        if not filename.endswith(".json"):
            continue
        filepath = os.path.join(sessions_dir, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            sessions.append({
                "session_id": data.get("session_id", ""),
                "patient_id": data.get("patient_id", "inconnu"),
                "date": pd.to_datetime(data.get("date", "")),
                "exercises_completed": data.get("exercises_completed", len(data.get("exercises", []))),
                "avg_score": data.get("avg_score", 0),
                "total_duration_seconds": data.get("total_duration_seconds", 0),
                "_raw": data,
            })
        except (json.JSONDecodeError, KeyError) as e:
            print(f"[DataLoader] Erreur lecture {filename}: {e}")

    if not sessions:
        return pd.DataFrame()
    return pd.DataFrame(sessions).sort_values("date").reset_index(drop=True)


def load_all_exercises(sessions_dir: str = "data/sessions") -> pd.DataFrame:
    """
    Charge tous les exercices de toutes les sessions.

    Returns:
        DataFrame avec une ligne par exercice.
    """
    exercises = []
    if not os.path.exists(sessions_dir):
        return pd.DataFrame()

    for filename in sorted(os.listdir(sessions_dir)):
        if not filename.endswith(".json"):
            continue
        filepath = os.path.join(sessions_dir, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            session_id = data.get("session_id", "")
            patient_id = data.get("patient_id", "inconnu")
            date = pd.to_datetime(data.get("date", ""))
            for ex in data.get("exercises", []):
                exercises.append({
                    "session_id": session_id,
                    "patient_id": patient_id,
                    "date": date,
                    "exercise_name": ex.get("exercise_name", ""),
                    "total_reps": ex.get("total_reps", 0),
                    "target_reps": ex.get("target_reps", 10),
                    "avg_amplitude": ex.get("avg_amplitude", 0),
                    "max_amplitude": ex.get("max_amplitude", 0),
                    "compensations_count": ex.get("compensations_count", 0),
                    "score": ex.get("score", 0),
                    "duration_seconds": ex.get("duration_seconds", 0),
                    "compensation_summary": ex.get("compensation_summary", {}),
                })
        except (json.JSONDecodeError, KeyError) as e:
            print(f"[DataLoader] Erreur lecture {filename}: {e}")

    if not exercises:
        return pd.DataFrame()
    return pd.DataFrame(exercises).sort_values("date").reset_index(drop=True)


def get_patient_sessions(patient_id: str, sessions_dir: str = "data/sessions") -> pd.DataFrame:
    """Filtre les sessions pour un patient donné."""
    df = load_all_sessions(sessions_dir)
    if df.empty:
        return df
    return df[df["patient_id"] == patient_id].reset_index(drop=True)


def get_patient_exercises(patient_id: str, sessions_dir: str = "data/sessions") -> pd.DataFrame:
    """Filtre les exercices pour un patient donné."""
    df = load_all_exercises(sessions_dir)
    if df.empty:
        return df
    return df[df["patient_id"] == patient_id].reset_index(drop=True)


def get_exercise_stats(exercise_name: str, sessions_dir: str = "data/sessions") -> pd.DataFrame:
    """Filtre les données pour un exercice spécifique."""
    df = load_all_exercises(sessions_dir)
    if df.empty:
        return df
    return df[df["exercise_name"] == exercise_name].reset_index(drop=True)


def get_patient_list(sessions_dir: str = "data/sessions") -> List[str]:
    """Retourne la liste des patients uniques."""
    df = load_all_sessions(sessions_dir)
    if df.empty:
        return []
    return sorted(df["patient_id"].unique().tolist())


def get_exercise_list(sessions_dir: str = "data/sessions") -> List[str]:
    """Retourne la liste des exercices uniques."""
    df = load_all_exercises(sessions_dir)
    if df.empty:
        return []
    return sorted(df["exercise_name"].unique().tolist())
