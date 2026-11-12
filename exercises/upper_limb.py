"""
Exercices des membres supérieurs (épaules, coudes, poignets).

6 exercices pour la rééducation des bras :
1. Flexion de l'épaule (lever le bras devant)
2. Abduction de l'épaule (lever le bras sur le côté)
3. Flexion du coude
4. Extension du coude
5. Flexion bilatérale des épaules (les deux bras)
6. Flexion épaule + tâche cognitive (double tâche)
"""

import numpy as np
from typing import Optional, Dict

from exercises.base import Exercise, ExerciseCategory, ExerciseDifficulty
from analysis.angles import (
    shoulder_angle_left, shoulder_angle_right,
    elbow_angle_left, elbow_angle_right,
)
from pose_detection.keypoints import Keypoint


class ShoulderFlexion(Exercise):
    """
    Flexion de l'épaule – lever le bras devant soi.

    Position de départ : bras le long du corps (~20°)
    Position cible : bras levé devant (~150°)
    """

    def __init__(self, side: str = "left", target_reps: int = 10):
        self.side = side
        side_fr = "gauche" if side == "left" else "droit"
        super().__init__(
            name=f"Flexion épaule {side_fr}",
            description=f"Levez le bras {side_fr} devant vous lentement",
            category=ExerciseCategory.UPPER_LIMB,
            difficulty=ExerciseDifficulty.EASY,
            target_reps=target_reps,
            angle_start=20.0,
            angle_target=150.0,
            tolerance=15.0,
        )

    def get_angle(self, keypoints: np.ndarray) -> Optional[float]:
        if self.side == "left":
            return shoulder_angle_left(keypoints)
        return shoulder_angle_right(keypoints)

    def get_instructions(self) -> str:
        side_fr = "gauche" if self.side == "left" else "droit"
        return f"Levez le bras {side_fr} devant vous, paume vers le bas"

    def get_visual_guide(self) -> Dict:
        if self.side == "left":
            return {
                "highlight_keypoints": [
                    Keypoint.LEFT_SHOULDER, Keypoint.LEFT_ELBOW, Keypoint.LEFT_WRIST
                ],
                "angle_arc": (Keypoint.LEFT_HIP, Keypoint.LEFT_SHOULDER, Keypoint.LEFT_ELBOW),
            }
        return {
            "highlight_keypoints": [
                Keypoint.RIGHT_SHOULDER, Keypoint.RIGHT_ELBOW, Keypoint.RIGHT_WRIST
            ],
            "angle_arc": (Keypoint.RIGHT_HIP, Keypoint.RIGHT_SHOULDER, Keypoint.RIGHT_ELBOW),
        }


class ShoulderAbduction(Exercise):
    """
    Abduction de l'épaule – lever le bras sur le côté.

    Position de départ : bras le long du corps (~15°)
    Position cible : bras à l'horizontale ou au-dessus (~140°)
    """

    def __init__(self, side: str = "left", target_reps: int = 10):
        self.side = side
        side_fr = "gauche" if side == "left" else "droit"
        super().__init__(
            name=f"Abduction épaule {side_fr}",
            description=f"Levez le bras {side_fr} sur le côté",
            category=ExerciseCategory.UPPER_LIMB,
            difficulty=ExerciseDifficulty.EASY,
            target_reps=target_reps,
            angle_start=15.0,
            angle_target=140.0,
            tolerance=15.0,
        )

    def get_angle(self, keypoints: np.ndarray) -> Optional[float]:
        if self.side == "left":
            return shoulder_angle_left(keypoints)
        return shoulder_angle_right(keypoints)

    def get_instructions(self) -> str:
        side_fr = "gauche" if self.side == "left" else "droit"
        return f"Levez le bras {side_fr} sur le côté, paume vers le sol"

    def get_visual_guide(self) -> Dict:
        if self.side == "left":
            return {
                "highlight_keypoints": [
                    Keypoint.LEFT_SHOULDER, Keypoint.LEFT_ELBOW, Keypoint.LEFT_WRIST
                ],
                "angle_arc": (Keypoint.LEFT_HIP, Keypoint.LEFT_SHOULDER, Keypoint.LEFT_ELBOW),
            }
        return {
            "highlight_keypoints": [
                Keypoint.RIGHT_SHOULDER, Keypoint.RIGHT_ELBOW, Keypoint.RIGHT_WRIST
            ],
            "angle_arc": (Keypoint.RIGHT_HIP, Keypoint.RIGHT_SHOULDER, Keypoint.RIGHT_ELBOW),
        }


class ElbowFlexion(Exercise):
    """
    Flexion du coude – plier le bras.

    Position de départ : bras tendu (~160°)
    Position cible : bras plié (~40°)
    """

    def __init__(self, side: str = "left", target_reps: int = 10):
        self.side = side
        side_fr = "gauche" if side == "left" else "droit"
        super().__init__(
            name=f"Flexion coude {side_fr}",
            description=f"Pliez le coude {side_fr} vers l'épaule",
            category=ExerciseCategory.UPPER_LIMB,
            difficulty=ExerciseDifficulty.EASY,
            target_reps=target_reps,
            angle_start=160.0,
            angle_target=40.0,
            tolerance=15.0,
        )

    def get_angle(self, keypoints: np.ndarray) -> Optional[float]:
        if self.side == "left":
            return elbow_angle_left(keypoints)
        return elbow_angle_right(keypoints)

    def get_instructions(self) -> str:
        side_fr = "gauche" if self.side == "left" else "droit"
        return f"Pliez le coude {side_fr} en amenant la main vers l'épaule"

    def get_visual_guide(self) -> Dict:
        if self.side == "left":
            return {
                "highlight_keypoints": [
                    Keypoint.LEFT_SHOULDER, Keypoint.LEFT_ELBOW, Keypoint.LEFT_WRIST
                ],
                "angle_arc": (Keypoint.LEFT_SHOULDER, Keypoint.LEFT_ELBOW, Keypoint.LEFT_WRIST),
            }
        return {
            "highlight_keypoints": [
                Keypoint.RIGHT_SHOULDER, Keypoint.RIGHT_ELBOW, Keypoint.RIGHT_WRIST
            ],
            "angle_arc": (Keypoint.RIGHT_SHOULDER, Keypoint.RIGHT_ELBOW, Keypoint.RIGHT_WRIST),
        }


class ElbowExtension(Exercise):
    """
    Extension du coude – tendre le bras depuis une position fléchie.

    Position de départ : bras plié (~40°)
    Position cible : bras tendu (~160°)
    """

    def __init__(self, side: str = "left", target_reps: int = 10):
        self.side = side
        side_fr = "gauche" if side == "left" else "droit"
        super().__init__(
            name=f"Extension coude {side_fr}",
            description=f"Tendez le bras {side_fr} complètement",
            category=ExerciseCategory.UPPER_LIMB,
            difficulty=ExerciseDifficulty.EASY,
            target_reps=target_reps,
            angle_start=40.0,
            angle_target=160.0,
            tolerance=15.0,
        )

    def get_angle(self, keypoints: np.ndarray) -> Optional[float]:
        if self.side == "left":
            return elbow_angle_left(keypoints)
        return elbow_angle_right(keypoints)

    def get_instructions(self) -> str:
        side_fr = "gauche" if self.side == "left" else "droit"
        return f"Tendez le bras {side_fr} devant vous complètement"

    def get_visual_guide(self) -> Dict:
        if self.side == "left":
            return {
                "highlight_keypoints": [
                    Keypoint.LEFT_SHOULDER, Keypoint.LEFT_ELBOW, Keypoint.LEFT_WRIST
                ],
                "angle_arc": (Keypoint.LEFT_SHOULDER, Keypoint.LEFT_ELBOW, Keypoint.LEFT_WRIST),
            }
        return {
            "highlight_keypoints": [
                Keypoint.RIGHT_SHOULDER, Keypoint.RIGHT_ELBOW, Keypoint.RIGHT_WRIST
            ],
            "angle_arc": (Keypoint.RIGHT_SHOULDER, Keypoint.RIGHT_ELBOW, Keypoint.RIGHT_WRIST),
        }


class BilateralShoulderFlexion(Exercise):
    """
    Flexion bilatérale des épaules – lever les deux bras en même temps.

    Utilise la moyenne des angles des deux épaules.
    """

    def __init__(self, target_reps: int = 10):
        super().__init__(
            name="Flexion bilatérale épaules",
            description="Levez les deux bras devant vous en même temps",
            category=ExerciseCategory.UPPER_LIMB,
            difficulty=ExerciseDifficulty.MEDIUM,
            target_reps=target_reps,
            angle_start=20.0,
            angle_target=150.0,
            tolerance=15.0,
        )

    def get_angle(self, keypoints: np.ndarray) -> Optional[float]:
        left = shoulder_angle_left(keypoints)
        right = shoulder_angle_right(keypoints)
        if left is not None and right is not None:
            return (left + right) / 2
        return left or right

    def get_instructions(self) -> str:
        return "Levez les deux bras devant vous, paumes vers le bas"

    def get_visual_guide(self) -> Dict:
        return {
            "highlight_keypoints": [
                Keypoint.LEFT_SHOULDER, Keypoint.LEFT_ELBOW, Keypoint.LEFT_WRIST,
                Keypoint.RIGHT_SHOULDER, Keypoint.RIGHT_ELBOW, Keypoint.RIGHT_WRIST,
            ],
            "angle_arc": None,  # Deux arcs, gérés spécialement
        }


class ShoulderFlexionCognitive(Exercise):
    """
    Flexion de l'épaule avec double tâche cognitive.

    Même mouvement que ShoulderFlexion, mais avec une tâche mentale
    en parallèle (ex: compter à rebours, citer des mots).
    """

    def __init__(self, side: str = "left", target_reps: int = 10):
        self.side = side
        side_fr = "gauche" if side == "left" else "droit"
        super().__init__(
            name=f"Flexion épaule {side_fr} + cognitif",
            description=f"Levez le bras {side_fr} en comptant à rebours depuis 20",
            category=ExerciseCategory.COGNITIVE_MOTOR,
            difficulty=ExerciseDifficulty.HARD,
            target_reps=target_reps,
            angle_start=20.0,
            angle_target=150.0,
            tolerance=15.0,
            has_cognitive_task=True,
            cognitive_instruction="Comptez à rebours depuis 20 : 20, 19, 18…",
        )

    def get_angle(self, keypoints: np.ndarray) -> Optional[float]:
        if self.side == "left":
            return shoulder_angle_left(keypoints)
        return shoulder_angle_right(keypoints)

    def get_instructions(self) -> str:
        side_fr = "gauche" if self.side == "left" else "droit"
        return (f"Levez le bras {side_fr} tout en comptant "
                f"à rebours depuis 20")

    def get_visual_guide(self) -> Dict:
        if self.side == "left":
            return {
                "highlight_keypoints": [
                    Keypoint.LEFT_SHOULDER, Keypoint.LEFT_ELBOW, Keypoint.LEFT_WRIST
                ],
                "angle_arc": (Keypoint.LEFT_HIP, Keypoint.LEFT_SHOULDER, Keypoint.LEFT_ELBOW),
                "cognitive_task": self.cognitive_instruction,
            }
        return {
            "highlight_keypoints": [
                Keypoint.RIGHT_SHOULDER, Keypoint.RIGHT_ELBOW, Keypoint.RIGHT_WRIST
            ],
            "angle_arc": (Keypoint.RIGHT_HIP, Keypoint.RIGHT_SHOULDER, Keypoint.RIGHT_ELBOW),
            "cognitive_task": self.cognitive_instruction,
        }
