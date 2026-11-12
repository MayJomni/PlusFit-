"""
Exercices d'équilibre assis et debout.

3 exercices d'équilibre :
1. Inclinaison latérale du tronc (assis)
2. Transfert de poids latéral (debout)
3. Transfert de poids + tâche cognitive
"""

import numpy as np
from typing import Optional, Dict

from exercises.base import Exercise, ExerciseCategory, ExerciseDifficulty
from analysis.angles import trunk_lateral_angle, get_joint_angle
from pose_detection.keypoints import Keypoint


class SeatedTrunkLean(Exercise):
    """
    Inclinaison latérale du tronc en position assise.

    L'utilisateur se penche lentement sur le côté puis revient au centre.
    Mesure la déviation latérale du tronc.

    Position de départ : tronc droit (~0° de déviation)
    Position cible : inclinaison latérale (~15-20°)
    """

    def __init__(self, side: str = "left", target_reps: int = 8):
        self.side = side
        side_fr = "gauche" if side == "left" else "droit"
        super().__init__(
            name=f"Inclinaison tronc {side_fr} (assis)",
            description=f"Penchez-vous doucement vers la {side_fr}",
            category=ExerciseCategory.BALANCE_SITTING,
            difficulty=ExerciseDifficulty.EASY,
            target_reps=target_reps,
            angle_start=0.0,
            angle_target=18.0,
            tolerance=5.0,
        )
        self._baseline_angle: Optional[float] = None

    def start(self, keypoints: np.ndarray):
        """Démarre et enregistre l'angle de base du tronc."""
        super().start(keypoints)
        self._baseline_angle = trunk_lateral_angle(keypoints) or 0.0

    def get_angle(self, keypoints: np.ndarray) -> Optional[float]:
        angle = trunk_lateral_angle(keypoints)
        if angle is None or self._baseline_angle is None:
            return None
        # Déviation par rapport à la posture initiale
        return abs(angle - self._baseline_angle)

    def get_instructions(self) -> str:
        side_fr = "gauche" if self.side == "left" else "droit"
        return f"Penchez-vous lentement vers la {side_fr}, puis revenez au centre"

    def get_visual_guide(self) -> Dict:
        return {
            "highlight_keypoints": [
                Keypoint.LEFT_SHOULDER, Keypoint.RIGHT_SHOULDER,
                Keypoint.LEFT_HIP, Keypoint.RIGHT_HIP,
            ],
            "angle_arc": None,
            "show_trunk_line": True,
        }


class StandingWeightShift(Exercise):
    """
    Transfert de poids latéral en position debout.

    L'utilisateur déplace son poids d'un pied à l'autre.
    On mesure le déplacement horizontal du centre des hanches.

    Position de départ : centré (~0 de déplacement)
    Position cible : déplacement latéral significatif
    """

    def __init__(self, target_reps: int = 8):
        super().__init__(
            name="Transfert de poids latéral (debout)",
            description="Déplacez votre poids d'un pied à l'autre",
            category=ExerciseCategory.BALANCE_STANDING,
            difficulty=ExerciseDifficulty.MEDIUM,
            target_reps=target_reps,
            angle_start=0.0,
            angle_target=12.0,
            tolerance=3.0,
        )
        self._baseline_hip_x: Optional[float] = None

    def start(self, keypoints: np.ndarray):
        super().start(keypoints)
        left_hip = keypoints[Keypoint.LEFT_HIP]
        right_hip = keypoints[Keypoint.RIGHT_HIP]
        if left_hip[2] > 0.3 and right_hip[2] > 0.3:
            self._baseline_hip_x = (left_hip[1] + right_hip[1]) / 2

    def get_angle(self, keypoints: np.ndarray) -> Optional[float]:
        """Retourne le 'déplacement' comme un pseudo-angle pour le compteur."""
        left_hip = keypoints[Keypoint.LEFT_HIP]
        right_hip = keypoints[Keypoint.RIGHT_HIP]

        if left_hip[2] < 0.3 or right_hip[2] < 0.3:
            return None
        if self._baseline_hip_x is None:
            return None

        current_x = (left_hip[1] + right_hip[1]) / 2
        # Convertir le déplacement normalisé en pseudo-degrés
        displacement = abs(current_x - self._baseline_hip_x)
        return displacement * 200  # Mise à l'échelle

    def get_instructions(self) -> str:
        return "Debout, transférez votre poids de gauche à droite lentement"

    def get_visual_guide(self) -> Dict:
        return {
            "highlight_keypoints": [
                Keypoint.LEFT_HIP, Keypoint.RIGHT_HIP,
                Keypoint.LEFT_ANKLE, Keypoint.RIGHT_ANKLE,
            ],
            "angle_arc": None,
            "show_center_line": True,
        }


class StandingWeightShiftCognitive(Exercise):
    """
    Transfert de poids + tâche cognitive.

    Même exercice que StandingWeightShift, avec une tâche mentale :
    citer les jours de la semaine à l'envers.
    """

    def __init__(self, target_reps: int = 8):
        super().__init__(
            name="Transfert de poids + cognitif",
            description="Transférez votre poids en récitant les jours à l'envers",
            category=ExerciseCategory.COGNITIVE_MOTOR,
            difficulty=ExerciseDifficulty.HARD,
            target_reps=target_reps,
            angle_start=0.0,
            angle_target=12.0,
            tolerance=3.0,
            has_cognitive_task=True,
            cognitive_instruction="Récitez les jours de la semaine à l'envers : Dimanche, Samedi…",
        )
        self._baseline_hip_x: Optional[float] = None

    def start(self, keypoints: np.ndarray):
        super().start(keypoints)
        left_hip = keypoints[Keypoint.LEFT_HIP]
        right_hip = keypoints[Keypoint.RIGHT_HIP]
        if left_hip[2] > 0.3 and right_hip[2] > 0.3:
            self._baseline_hip_x = (left_hip[1] + right_hip[1]) / 2

    def get_angle(self, keypoints: np.ndarray) -> Optional[float]:
        left_hip = keypoints[Keypoint.LEFT_HIP]
        right_hip = keypoints[Keypoint.RIGHT_HIP]

        if left_hip[2] < 0.3 or right_hip[2] < 0.3:
            return None
        if self._baseline_hip_x is None:
            return None

        current_x = (left_hip[1] + right_hip[1]) / 2
        displacement = abs(current_x - self._baseline_hip_x)
        return displacement * 200

    def get_instructions(self) -> str:
        return ("Transférez votre poids d'un côté à l'autre "
                "en récitant les jours à l'envers")

    def get_visual_guide(self) -> Dict:
        return {
            "highlight_keypoints": [
                Keypoint.LEFT_HIP, Keypoint.RIGHT_HIP,
                Keypoint.LEFT_ANKLE, Keypoint.RIGHT_ANKLE,
            ],
            "angle_arc": None,
            "show_center_line": True,
            "cognitive_task": self.cognitive_instruction,
        }
