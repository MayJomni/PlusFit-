"""
Exercices des membres inférieurs (hanches, genoux, chevilles).

3 exercices pour la rééducation des jambes :
1. Extension du genou (assis)
2. Flexion de la hanche (lever la cuisse)
3. Extension de la hanche (debout)
"""

import numpy as np
from typing import Optional, Dict

from exercises.base import Exercise, ExerciseCategory, ExerciseDifficulty
from analysis.angles import (
    knee_angle_left, knee_angle_right,
    hip_angle_left, hip_angle_right,
)
from pose_detection.keypoints import Keypoint


class KneeExtension(Exercise):
    """
    Extension du genou – tendre la jambe en position assise.

    Position de départ : genou plié (~90°)
    Position cible : jambe tendue (~160°)
    """

    def __init__(self, side: str = "left", target_reps: int = 10):
        self.side = side
        side_fr = "gauche" if side == "left" else "droit"
        super().__init__(
            name=f"Extension genou {side_fr}",
            description=f"Tendez la jambe {side_fr} devant vous (assis)",
            category=ExerciseCategory.LOWER_LIMB,
            difficulty=ExerciseDifficulty.EASY,
            target_reps=target_reps,
            angle_start=90.0,
            angle_target=160.0,
            tolerance=15.0,
        )

    def get_angle(self, keypoints: np.ndarray) -> Optional[float]:
        if self.side == "left":
            return knee_angle_left(keypoints)
        return knee_angle_right(keypoints)

    def get_instructions(self) -> str:
        side_fr = "gauche" if self.side == "left" else "droit"
        return f"Assis(e), tendez la jambe {side_fr} devant vous lentement"

    def get_visual_guide(self) -> Dict:
        if self.side == "left":
            return {
                "highlight_keypoints": [
                    Keypoint.LEFT_HIP, Keypoint.LEFT_KNEE, Keypoint.LEFT_ANKLE
                ],
                "angle_arc": (Keypoint.LEFT_HIP, Keypoint.LEFT_KNEE, Keypoint.LEFT_ANKLE),
            }
        return {
            "highlight_keypoints": [
                Keypoint.RIGHT_HIP, Keypoint.RIGHT_KNEE, Keypoint.RIGHT_ANKLE
            ],
            "angle_arc": (Keypoint.RIGHT_HIP, Keypoint.RIGHT_KNEE, Keypoint.RIGHT_ANKLE),
        }


class HipFlexion(Exercise):
    """
    Flexion de la hanche – lever la cuisse (assis ou debout).

    Position de départ : cuisse au repos (~170°)
    Position cible : cuisse levée (~90°)
    """

    def __init__(self, side: str = "left", target_reps: int = 10):
        self.side = side
        side_fr = "gauche" if side == "left" else "droit"
        super().__init__(
            name=f"Flexion hanche {side_fr}",
            description=f"Levez la cuisse {side_fr} vers la poitrine",
            category=ExerciseCategory.LOWER_LIMB,
            difficulty=ExerciseDifficulty.MEDIUM,
            target_reps=target_reps,
            angle_start=170.0,
            angle_target=90.0,
            tolerance=15.0,
        )

    def get_angle(self, keypoints: np.ndarray) -> Optional[float]:
        if self.side == "left":
            return hip_angle_left(keypoints)
        return hip_angle_right(keypoints)

    def get_instructions(self) -> str:
        side_fr = "gauche" if self.side == "left" else "droit"
        return f"Levez la cuisse {side_fr} le plus haut possible"

    def get_visual_guide(self) -> Dict:
        if self.side == "left":
            return {
                "highlight_keypoints": [
                    Keypoint.LEFT_SHOULDER, Keypoint.LEFT_HIP, Keypoint.LEFT_KNEE
                ],
                "angle_arc": (Keypoint.LEFT_SHOULDER, Keypoint.LEFT_HIP, Keypoint.LEFT_KNEE),
            }
        return {
            "highlight_keypoints": [
                Keypoint.RIGHT_SHOULDER, Keypoint.RIGHT_HIP, Keypoint.RIGHT_KNEE
            ],
            "angle_arc": (Keypoint.RIGHT_SHOULDER, Keypoint.RIGHT_HIP, Keypoint.RIGHT_KNEE),
        }


class KneeExtensionCognitive(Exercise):
    """
    Extension du genou avec double tâche cognitive.

    Même mouvement que KneeExtension, avec une tâche mentale :
    citer des noms d'animaux pendant les mouvements.
    """

    def __init__(self, side: str = "left", target_reps: int = 10):
        self.side = side
        side_fr = "gauche" if side == "left" else "droit"
        super().__init__(
            name=f"Extension genou {side_fr} + cognitif",
            description=f"Tendez la jambe {side_fr} en citant des animaux",
            category=ExerciseCategory.COGNITIVE_MOTOR,
            difficulty=ExerciseDifficulty.HARD,
            target_reps=target_reps,
            angle_start=90.0,
            angle_target=160.0,
            tolerance=15.0,
            has_cognitive_task=True,
            cognitive_instruction="Citez un nom d'animal à chaque répétition",
        )

    def get_angle(self, keypoints: np.ndarray) -> Optional[float]:
        if self.side == "left":
            return knee_angle_left(keypoints)
        return knee_angle_right(keypoints)

    def get_instructions(self) -> str:
        side_fr = "gauche" if self.side == "left" else "droit"
        return (f"Tendez la jambe {side_fr} et citez un animal "
                f"à chaque mouvement")

    def get_visual_guide(self) -> Dict:
        if self.side == "left":
            return {
                "highlight_keypoints": [
                    Keypoint.LEFT_HIP, Keypoint.LEFT_KNEE, Keypoint.LEFT_ANKLE
                ],
                "angle_arc": (Keypoint.LEFT_HIP, Keypoint.LEFT_KNEE, Keypoint.LEFT_ANKLE),
                "cognitive_task": self.cognitive_instruction,
            }
        return {
            "highlight_keypoints": [
                Keypoint.RIGHT_HIP, Keypoint.RIGHT_KNEE, Keypoint.RIGHT_ANKLE
            ],
            "angle_arc": (Keypoint.RIGHT_HIP, Keypoint.RIGHT_KNEE, Keypoint.RIGHT_ANKLE),
            "cognitive_task": self.cognitive_instruction,
        }
