"""
Définition des keypoints MoveNet et utilitaires associés.

MoveNet détecte 17 points du corps humain. Ce module fournit
les constantes, les connexions entre points (squelette), et
des fonctions utilitaires pour y accéder facilement.
"""

from enum import IntEnum
from typing import Dict, List, Tuple


class Keypoint(IntEnum):
    """Les 17 keypoints détectés par MoveNet, indexés de 0 à 16."""
    NOSE = 0
    LEFT_EYE = 1
    RIGHT_EYE = 2
    LEFT_EAR = 3
    RIGHT_EAR = 4
    LEFT_SHOULDER = 5
    RIGHT_SHOULDER = 6
    LEFT_ELBOW = 7
    RIGHT_ELBOW = 8
    LEFT_WRIST = 9
    RIGHT_WRIST = 10
    LEFT_HIP = 11
    RIGHT_HIP = 12
    LEFT_KNEE = 13
    RIGHT_KNEE = 14
    LEFT_ANKLE = 15
    RIGHT_ANKLE = 16


# Connexions pour dessiner le squelette à l'écran
SKELETON_CONNECTIONS: List[Tuple[Keypoint, Keypoint]] = [
    # Tête
    (Keypoint.LEFT_EAR, Keypoint.LEFT_EYE),
    (Keypoint.LEFT_EYE, Keypoint.NOSE),
    (Keypoint.NOSE, Keypoint.RIGHT_EYE),
    (Keypoint.RIGHT_EYE, Keypoint.RIGHT_EAR),
    # Torse
    (Keypoint.LEFT_SHOULDER, Keypoint.RIGHT_SHOULDER),
    (Keypoint.LEFT_SHOULDER, Keypoint.LEFT_HIP),
    (Keypoint.RIGHT_SHOULDER, Keypoint.RIGHT_HIP),
    (Keypoint.LEFT_HIP, Keypoint.RIGHT_HIP),
    # Bras gauche
    (Keypoint.LEFT_SHOULDER, Keypoint.LEFT_ELBOW),
    (Keypoint.LEFT_ELBOW, Keypoint.LEFT_WRIST),
    # Bras droit
    (Keypoint.RIGHT_SHOULDER, Keypoint.RIGHT_ELBOW),
    (Keypoint.RIGHT_ELBOW, Keypoint.RIGHT_WRIST),
    # Jambe gauche
    (Keypoint.LEFT_HIP, Keypoint.LEFT_KNEE),
    (Keypoint.LEFT_KNEE, Keypoint.LEFT_ANKLE),
    # Jambe droite
    (Keypoint.RIGHT_HIP, Keypoint.RIGHT_KNEE),
    (Keypoint.RIGHT_KNEE, Keypoint.RIGHT_ANKLE),
]

# Couleurs par segment corporel (BGR pour OpenCV)
SEGMENT_COLORS: Dict[str, Tuple[int, int, int]] = {
    "head": (255, 200, 100),       # Bleu clair
    "torso": (200, 200, 200),      # Gris
    "left_arm": (100, 255, 100),   # Vert
    "right_arm": (100, 100, 255),  # Rouge
    "left_leg": (255, 255, 100),   # Cyan
    "right_leg": (100, 255, 255),  # Jaune
}


def get_segment_color(kp1: Keypoint, kp2: Keypoint) -> Tuple[int, int, int]:
    """Retourne la couleur appropriée pour un segment du squelette."""
    head_kps = {Keypoint.NOSE, Keypoint.LEFT_EYE, Keypoint.RIGHT_EYE,
                Keypoint.LEFT_EAR, Keypoint.RIGHT_EAR}
    torso_kps = {Keypoint.LEFT_SHOULDER, Keypoint.RIGHT_SHOULDER,
                 Keypoint.LEFT_HIP, Keypoint.RIGHT_HIP}

    if kp1 in head_kps or kp2 in head_kps:
        return SEGMENT_COLORS["head"]
    if kp1 in torso_kps and kp2 in torso_kps:
        return SEGMENT_COLORS["torso"]
    if kp1 in {Keypoint.LEFT_SHOULDER, Keypoint.LEFT_ELBOW, Keypoint.LEFT_WRIST}:
        if kp2 in {Keypoint.LEFT_SHOULDER, Keypoint.LEFT_ELBOW, Keypoint.LEFT_WRIST}:
            return SEGMENT_COLORS["left_arm"]
    if kp1 in {Keypoint.RIGHT_SHOULDER, Keypoint.RIGHT_ELBOW, Keypoint.RIGHT_WRIST}:
        if kp2 in {Keypoint.RIGHT_SHOULDER, Keypoint.RIGHT_ELBOW, Keypoint.RIGHT_WRIST}:
            return SEGMENT_COLORS["right_arm"]
    if kp1 in {Keypoint.LEFT_HIP, Keypoint.LEFT_KNEE, Keypoint.LEFT_ANKLE}:
        if kp2 in {Keypoint.LEFT_HIP, Keypoint.LEFT_KNEE, Keypoint.LEFT_ANKLE}:
            return SEGMENT_COLORS["left_leg"]
    if kp1 in {Keypoint.RIGHT_HIP, Keypoint.RIGHT_KNEE, Keypoint.RIGHT_ANKLE}:
        if kp2 in {Keypoint.RIGHT_HIP, Keypoint.RIGHT_KNEE, Keypoint.RIGHT_ANKLE}:
            return SEGMENT_COLORS["right_leg"]

    return (200, 200, 200)  # Défaut gris


# Noms français des keypoints pour l'affichage
KEYPOINT_NAMES_FR: Dict[Keypoint, str] = {
    Keypoint.NOSE: "Nez",
    Keypoint.LEFT_EYE: "Œil gauche",
    Keypoint.RIGHT_EYE: "Œil droit",
    Keypoint.LEFT_EAR: "Oreille gauche",
    Keypoint.RIGHT_EAR: "Oreille droite",
    Keypoint.LEFT_SHOULDER: "Épaule gauche",
    Keypoint.RIGHT_SHOULDER: "Épaule droite",
    Keypoint.LEFT_ELBOW: "Coude gauche",
    Keypoint.RIGHT_ELBOW: "Coude droit",
    Keypoint.LEFT_WRIST: "Poignet gauche",
    Keypoint.RIGHT_WRIST: "Poignet droit",
    Keypoint.LEFT_HIP: "Hanche gauche",
    Keypoint.RIGHT_HIP: "Hanche droite",
    Keypoint.LEFT_KNEE: "Genou gauche",
    Keypoint.RIGHT_KNEE: "Genou droit",
    Keypoint.LEFT_ANKLE: "Cheville gauche",
    Keypoint.RIGHT_ANKLE: "Cheville droite",
}
