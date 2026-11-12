"""
Tests unitaires pour le module data.session_logger.

5 tests couvrant l'enregistrement, la sauvegarde,
la validité JSON, le résumé et le multi-exercice.
"""

import os
import json
import pytest

from data.session_logger import SessionLogger
from exercises.base import ExerciseResult


def _make_result(name: str = "Test exercice", reps: int = 8,
                 target: int = 10, score: float = 75.0) -> ExerciseResult:
    """Crée un ExerciseResult factice pour les tests."""
    return ExerciseResult(
        exercise_name=name,
        total_reps=reps,
        target_reps=target,
        avg_amplitude=120.0,
        max_amplitude=145.0,
        compensations_count=2,
        duration_seconds=45.0,
        rep_details=[
            {"rep_number": i + 1, "amplitude": 120.0, "duration_seconds": 5.0}
            for i in range(reps)
        ],
        compensation_summary={"total": 2, "types": {"TRUNK_LEAN": {"count": 2, "max_severity": "mild"}}},
        score=score,
    )


class TestSessionLogger:
    """Tests du logger de session."""

    def test_log_exercise(self, tmp_session_dir):
        """log_exercise() ajoute un résultat à la liste."""
        logger = SessionLogger(log_dir=tmp_session_dir, patient_id="test001")
        result = _make_result()

        logger.log_exercise(result)

        assert len(logger.results) == 1, "Devrait avoir 1 résultat"
        assert logger.results[0]["exercise_name"] == "Test exercice"

    def test_save_creates_file(self, tmp_session_dir):
        """save() crée un fichier JSON dans le dossier."""
        logger = SessionLogger(log_dir=tmp_session_dir, patient_id="test001")
        logger.log_exercise(_make_result())

        filepath = logger.save()

        assert os.path.exists(filepath), f"Le fichier {filepath} devrait exister"
        assert filepath.endswith(".json")

    def test_save_valid_json(self, tmp_session_dir):
        """Le fichier sauvegardé est du JSON valide avec les bonnes clés."""
        logger = SessionLogger(log_dir=tmp_session_dir, patient_id="test001")
        logger.log_exercise(_make_result())

        filepath = logger.save()

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        required_keys = [
            "session_id", "patient_id", "date",
            "total_duration_seconds", "exercises_completed",
            "avg_score", "exercises",
        ]
        for key in required_keys:
            assert key in data, f"Clé '{key}' manquante dans le JSON"

        assert data["patient_id"] == "test001"
        assert data["exercises_completed"] == 1
        assert len(data["exercises"]) == 1

    def test_summary_format(self, tmp_session_dir):
        """get_summary() retourne un string formaté lisible."""
        logger = SessionLogger(log_dir=tmp_session_dir, patient_id="test001")
        logger.log_exercise(_make_result())

        summary = logger.get_summary()

        assert isinstance(summary, str)
        assert "test001" in summary
        assert "session" in summary.lower() or "resume" in summary.lower() \
            or "Résumé" in summary or "Resume" in summary

    def test_multiple_exercises_logged(self, tmp_session_dir):
        """3 exercices loggés → 3 entrées dans results et dans le JSON."""
        logger = SessionLogger(log_dir=tmp_session_dir, patient_id="test001")

        logger.log_exercise(_make_result("Exercice A", reps=10, score=90.0))
        logger.log_exercise(_make_result("Exercice B", reps=7, score=65.0))
        logger.log_exercise(_make_result("Exercice C", reps=5, score=50.0))

        assert len(logger.results) == 3

        filepath = logger.save()
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["exercises_completed"] == 3
        assert len(data["exercises"]) == 3
        # Score moyen : (90 + 65 + 50) / 3 ≈ 68.3
        assert data["avg_score"] == pytest.approx(68.3, abs=0.2)
