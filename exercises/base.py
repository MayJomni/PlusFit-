"""
Classe de base pour les exercices de rééducation.

Chaque exercice hérite de cette classe et définit :
- Les keypoints nécessaires
- Les angles à mesurer
- Les seuils de validation
- Les compensations à surveiller
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple
from enum import Enum, auto
import time
import numpy as np

from analysis.repetitions import RepCounter
from analysis.compensation import CompensationDetector, CompensationAlert


class ExerciseCategory(Enum):
    """Catégories d'exercices."""
    UPPER_LIMB = auto()      # Membres supérieurs
    LOWER_LIMB = auto()      # Membres inférieurs
    BALANCE_SITTING = auto() # Équilibre assis
    BALANCE_STANDING = auto()# Équilibre debout
    COGNITIVE_MOTOR = auto() # Double tâche cognitivo-motrice


class ExerciseDifficulty(Enum):
    """Niveaux de difficulté."""
    EASY = auto()
    MEDIUM = auto()
    HARD = auto()


@dataclass
class ExerciseResult:
    """Résultats d'une session d'exercice."""
    exercise_name: str
    total_reps: int
    target_reps: int
    avg_amplitude: float
    max_amplitude: float
    compensations_count: int
    duration_seconds: float
    rep_details: List[dict]
    compensation_summary: dict
    score: float  # Note sur 100


class Exercise(ABC):
    """
    Classe de base abstraite pour tous les exercices.

    Chaque exercice concret doit implémenter :
    - get_angle() : calcul de l'angle principal
    - get_instructions() : texte d'instructions pour l'utilisateur
    """

    def __init__(
        self,
        name: str,
        description: str,
        category: ExerciseCategory,
        difficulty: ExerciseDifficulty,
        target_reps: int = 10,
        angle_start: float = 20.0,
        angle_target: float = 160.0,
        tolerance: float = 15.0,
        has_cognitive_task: bool = False,
        cognitive_instruction: str = "",
    ):
        self.name = name
        self.description = description
        self.category = category
        self.difficulty = difficulty
        self.target_reps = target_reps
        self.has_cognitive_task = has_cognitive_task
        self.cognitive_instruction = cognitive_instruction

        # Modules d'analyse
        self.rep_counter = RepCounter(
            angle_start=angle_start,
            angle_target=angle_target,
            tolerance=tolerance,
        )
        self.compensation_detector = CompensationDetector()

        # État
        self._started = False
        self._start_time: Optional[float] = None
        self._current_angle: Optional[float] = None
        self._current_alerts: List[CompensationAlert] = []
        self._feedback_message = ""
        self._feedback_color = "#FFFFFF"

        # Tracking de fatigue
        self._rep_amplitudes: list = []

    @abstractmethod
    def get_angle(self, keypoints: np.ndarray) -> Optional[float]:
        """
        Calcule l'angle principal de l'exercice.

        Args:
            keypoints: Array MoveNet (17, 3).

        Returns:
            Angle en degrés, ou None si non calculable.
        """
        pass

    @abstractmethod
    def get_instructions(self) -> str:
        """Retourne les instructions textuelles pour l'utilisateur."""
        pass

    @abstractmethod
    def get_visual_guide(self) -> Dict:
        """
        Retourne les données pour afficher un guide visuel.

        Returns:
            Dict avec les keypoints à mettre en surbrillance,
            les arcs d'angle à dessiner, etc.
        """
        pass

    def start(self, keypoints: np.ndarray):
        """Démarre l'exercice et calibre la posture de référence."""
        self.rep_counter.reset()
        self.compensation_detector.calibrate(keypoints)
        self._started = True
        self._start_time = time.time()
        self._rep_amplitudes = []
        print(f"[Exercice] '{self.name}' démarré.")

    def update(self, keypoints: np.ndarray) -> dict:
        """
        Met à jour l'exercice avec la frame courante.

        Args:
            keypoints: Array MoveNet (17, 3).

        Returns:
            Dict avec l'état actuel :
            {
                "angle": float | None,
                "reps": int,
                "target_reps": int,
                "progress_pct": float,
                "new_rep": bool,
                "compensations": List[CompensationAlert],
                "feedback_message": str,
                "feedback_color": str,
                "completed": bool,
            }
        """
        if not self._started:
            return self._empty_state()

        # Calculer l'angle
        angle = self.get_angle(keypoints)
        self._current_angle = angle

        # Compter les reps
        new_rep = self.rep_counter.update(angle)

        # Stocker l'amplitude de la nouvelle rep
        if new_rep is not None and self.rep_counter.rep_history:
            last_rep = self.rep_counter.rep_history[-1]
            self._rep_amplitudes.append(last_rep["amplitude"])

        # Vérifier les compensations
        alerts = self.compensation_detector.check(keypoints)
        self._current_alerts = alerts

        # Générer le feedback
        self._update_feedback(angle, new_rep, alerts)

        completed = self.rep_counter.count >= self.target_reps

        result = {
            "angle": angle,
            "reps": self.rep_counter.count,
            "target_reps": self.target_reps,
            "progress_pct": self.rep_counter.get_progress_pct(angle),
            "new_rep": new_rep is not None,
            "compensations": alerts,
            "feedback_message": self._feedback_message,
            "feedback_color": self._feedback_color,
            "completed": completed,
        }

        # Ajouter fatigue_info seulement après au moins 4 reps
        if len(self._rep_amplitudes) >= 4:
            fatigue_info = self.detect_fatigue()
            if fatigue_info["fatigue"]:
                result["fatigue_info"] = fatigue_info

        return result

    def _update_feedback(
        self,
        angle: Optional[float],
        new_rep: Optional[int],
        alerts: List[CompensationAlert],
    ):
        """Met à jour le message de feedback."""
        if alerts:
            # Priorité aux alertes de compensation
            worst = max(alerts, key=lambda a: {"mild": 0, "moderate": 1, "severe": 2}[a.severity])
            self._feedback_message = worst.message
            severity_colors = {
                "mild": "#FF9800",
                "moderate": "#FF5722",
                "severe": "#F44336",
            }
            self._feedback_color = severity_colors[worst.severity]
        elif new_rep is not None:
            self._feedback_message = f"✅ Bravo ! Répétition {new_rep}/{self.target_reps}"
            self._feedback_color = "#4CAF50"
        elif angle is not None:
            progress = self.rep_counter.get_progress_pct(angle)
            if progress > 80:
                self._feedback_message = "Presque ! Encore un peu…"
                self._feedback_color = "#8BC34A"
            elif progress > 40:
                self._feedback_message = "Bien, continuez le mouvement"
                self._feedback_color = "#CDDC39"
            else:
                self._feedback_message = self.get_instructions()
                self._feedback_color = "#FFFFFF"
        else:
            self._feedback_message = "Placez-vous face à la caméra"
            self._feedback_color = "#FF9800"

    def detect_fatigue(self) -> dict:
        """
        Détecte la fatigue en analysant la baisse d'amplitude sur les reps.

        Compare l'amplitude moyenne des 3 premières vs 3 dernières reps.
        Retourne un dict avec niveau de fatigue et message.
        """
        amps = self._rep_amplitudes
        if len(amps) < 4:
            return {"fatigue": False, "niveau": "none", "message": "", "suggestion": ""}

        premiers = sum(amps[:3]) / 3
        derniers  = sum(amps[-3:]) / 3

        if premiers == 0:
            return {"fatigue": False, "niveau": "none", "message": "", "suggestion": ""}

        ratio = derniers / premiers

        if ratio < 0.60:
            return {
                "fatigue": True,
                "niveau": "severe",
                "message": "Vous semblez très fatigué(e), votre amplitude a beaucoup baissé.",
                "suggestion": "Je vous recommande d'arrêter et de vous reposer.",
            }
        elif ratio < 0.75:
            return {
                "fatigue": True,
                "niveau": "moderee",
                "message": "Votre amplitude diminue, signe de fatigue.",
                "suggestion": "Faites une pause de 30 secondes avant de continuer.",
            }
        return {"fatigue": False, "niveau": "none", "message": "", "suggestion": ""}

    def get_result(self) -> ExerciseResult:
        """Génère le résultat final de l'exercice."""
        duration = time.time() - self._start_time if self._start_time else 0
        comp_summary = self.compensation_detector.get_compensation_summary()

        # Score basé sur : reps complétées, amplitude, compensations
        rep_score = min(100, (self.rep_counter.count / self.target_reps) * 100) * 0.4
        amp_score = min(100, (self.rep_counter.get_avg_amplitude() /
                              abs(self.rep_counter.angle_target - self.rep_counter.angle_start)) * 100) * 0.3
        comp_penalty = min(30, comp_summary["total"] * 3) if comp_summary["total"] > 0 else 0
        score = max(0, rep_score + amp_score + 30 - comp_penalty)

        return ExerciseResult(
            exercise_name=self.name,
            total_reps=self.rep_counter.count,
            target_reps=self.target_reps,
            avg_amplitude=self.rep_counter.get_avg_amplitude(),
            max_amplitude=max((r["amplitude"] for r in self.rep_counter.rep_history), default=0),
            compensations_count=comp_summary["total"],
            duration_seconds=round(duration, 1),
            rep_details=self.rep_counter.rep_history,
            compensation_summary=comp_summary,
            score=round(score, 1),
        )

    def _empty_state(self) -> dict:
        """État vide quand l'exercice n'a pas encore démarré."""
        return {
            "angle": None,
            "reps": 0,
            "target_reps": self.target_reps,
            "progress_pct": 0.0,
            "new_rep": False,
            "compensations": [],
            "feedback_message": "Appuyez sur DÉMARRER quand vous êtes prêt(e)",
            "feedback_color": "#FFFFFF",
            "completed": False,
        }
