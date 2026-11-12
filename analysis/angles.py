"""
Calcul d'angles articulaires à partir des keypoints.

Ce module fournit les outils pour mesurer les angles entre les
articulations du corps, essentiels pour évaluer l'amplitude
de mouvement (ROM = Range of Motion).
"""

import math
import numpy as np
from typing import Tuple, Optional

from pose_detection.keypoints import Keypoint


def calculate_angle(
    point_a: Tuple[float, float],
    point_b: Tuple[float, float],
    point_c: Tuple[float, float],
) -> float:
    """
    Calcule l'angle au point B formé par les segments BA et BC.

    L'angle est mesuré en degrés, entre 0° et 180°.

    Args:
        point_a: Coordonnées (y, x) du premier point.
        point_b: Coordonnées (y, x) du point central (le sommet de l'angle).
        point_c: Coordonnées (y, x) du troisième point.

    Returns:
        Angle en degrés au point B.

    Example:
        >>> # Angle au coude entre épaule, coude, poignet
        >>> angle = calculate_angle(shoulder, elbow, wrist)
    """
    a = np.array(point_a)
    b = np.array(point_b)
    c = np.array(point_c)

    # Vecteurs BA et BC
    ba = a - b
    bc = c - b

    # Produit scalaire et normes
    dot_product = np.dot(ba, bc)
    magnitude = np.linalg.norm(ba) * np.linalg.norm(bc)

    if magnitude < 1e-6:
        return 0.0

    # Angle en radians puis degrés
    cos_angle = np.clip(dot_product / magnitude, -1.0, 1.0)
    angle_rad = math.acos(cos_angle)
    angle_deg = math.degrees(angle_rad)

    return angle_deg


def get_joint_angle(
    keypoints: np.ndarray,
    kp_a: Keypoint,
    kp_b: Keypoint,
    kp_c: Keypoint,
    min_confidence: float = 0.3,
) -> Optional[float]:
    """
    Calcule l'angle à une articulation si les 3 keypoints sont visibles.

    Args:
        keypoints: Array (17, 3) des keypoints MoveNet.
        kp_a: Premier keypoint (ex: épaule).
        kp_b: Keypoint central / sommet (ex: coude).
        kp_c: Troisième keypoint (ex: poignet).
        min_confidence: Confiance minimale requise.

    Returns:
        Angle en degrés, ou None si un keypoint n'est pas assez visible.
    """
    for kp in [kp_a, kp_b, kp_c]:
        if keypoints[kp.value][2] < min_confidence:
            return None

    point_a = (keypoints[kp_a.value][0], keypoints[kp_a.value][1])
    point_b = (keypoints[kp_b.value][0], keypoints[kp_b.value][1])
    point_c = (keypoints[kp_c.value][0], keypoints[kp_c.value][1])

    return calculate_angle(point_a, point_b, point_c)


# ─── Angles articulaires prédéfinis ───────────────────────────────────────────

def elbow_angle_left(keypoints: np.ndarray) -> Optional[float]:
    """Angle au coude gauche (épaule → coude → poignet)."""
    return get_joint_angle(
        keypoints,
        Keypoint.LEFT_SHOULDER,
        Keypoint.LEFT_ELBOW,
        Keypoint.LEFT_WRIST,
    )


def elbow_angle_right(keypoints: np.ndarray) -> Optional[float]:
    """Angle au coude droit (épaule → coude → poignet)."""
    return get_joint_angle(
        keypoints,
        Keypoint.RIGHT_SHOULDER,
        Keypoint.RIGHT_ELBOW,
        Keypoint.RIGHT_WRIST,
    )


def shoulder_angle_left(keypoints: np.ndarray) -> Optional[float]:
    """Angle à l'épaule gauche (hanche → épaule → coude) – abduction/flexion."""
    return get_joint_angle(
        keypoints,
        Keypoint.LEFT_HIP,
        Keypoint.LEFT_SHOULDER,
        Keypoint.LEFT_ELBOW,
    )


def shoulder_angle_right(keypoints: np.ndarray) -> Optional[float]:
    """Angle à l'épaule droite (hanche → épaule → coude) – abduction/flexion."""
    return get_joint_angle(
        keypoints,
        Keypoint.RIGHT_HIP,
        Keypoint.RIGHT_SHOULDER,
        Keypoint.RIGHT_ELBOW,
    )


def knee_angle_left(keypoints: np.ndarray) -> Optional[float]:
    """Angle au genou gauche (hanche → genou → cheville)."""
    return get_joint_angle(
        keypoints,
        Keypoint.LEFT_HIP,
        Keypoint.LEFT_KNEE,
        Keypoint.LEFT_ANKLE,
    )


def knee_angle_right(keypoints: np.ndarray) -> Optional[float]:
    """Angle au genou droit (hanche → genou → cheville)."""
    return get_joint_angle(
        keypoints,
        Keypoint.RIGHT_HIP,
        Keypoint.RIGHT_KNEE,
        Keypoint.RIGHT_ANKLE,
    )


def hip_angle_left(keypoints: np.ndarray) -> Optional[float]:
    """Angle à la hanche gauche (épaule → hanche → genou)."""
    return get_joint_angle(
        keypoints,
        Keypoint.LEFT_SHOULDER,
        Keypoint.LEFT_HIP,
        Keypoint.LEFT_KNEE,
    )


def hip_angle_right(keypoints: np.ndarray) -> Optional[float]:
    """Angle à la hanche droite (épaule → hanche → genou)."""
    return get_joint_angle(
        keypoints,
        Keypoint.RIGHT_SHOULDER,
        Keypoint.RIGHT_HIP,
        Keypoint.RIGHT_KNEE,
    )


def trunk_lateral_angle(keypoints: np.ndarray) -> Optional[float]:
    """
    Inclinaison latérale du tronc.

    Mesure l'angle du tronc par rapport à la verticale en utilisant
    le milieu des épaules et le milieu des hanches.

    Returns:
        Angle d'inclinaison en degrés (0° = droit, positif = penché).
        None si les points ne sont pas visibles.
    """
    required = [
        Keypoint.LEFT_SHOULDER, Keypoint.RIGHT_SHOULDER,
        Keypoint.LEFT_HIP, Keypoint.RIGHT_HIP,
    ]
    for kp in required:
        if keypoints[kp.value][2] < 0.3:
            return None

    # Milieu des épaules
    mid_shoulder_y = (keypoints[Keypoint.LEFT_SHOULDER][0] +
                      keypoints[Keypoint.RIGHT_SHOULDER][0]) / 2
    mid_shoulder_x = (keypoints[Keypoint.LEFT_SHOULDER][1] +
                      keypoints[Keypoint.RIGHT_SHOULDER][1]) / 2

    # Milieu des hanches
    mid_hip_y = (keypoints[Keypoint.LEFT_HIP][0] +
                 keypoints[Keypoint.RIGHT_HIP][0]) / 2
    mid_hip_x = (keypoints[Keypoint.LEFT_HIP][1] +
                 keypoints[Keypoint.RIGHT_HIP][1]) / 2

    # Angle par rapport à la verticale
    dx = mid_shoulder_x - mid_hip_x
    dy = mid_shoulder_y - mid_hip_y

    if abs(dy) < 1e-6:
        return 90.0

    angle = math.degrees(math.atan2(abs(dx), abs(dy)))
    return angle
