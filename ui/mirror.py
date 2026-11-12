"""
Rendu miroir avec squelette superposé.

Ce module gère l'affichage de la caméra en mode miroir,
le dessin du squelette MoveNet, les indicateurs d'angle,
la barre de progression, et les messages de feedback.
"""

import cv2
import math
import numpy as np
from typing import Optional, Tuple, Dict, List

from pose_detection.keypoints import (
    Keypoint, SKELETON_CONNECTIONS, get_segment_color
)
from analysis.compensation import CompensationAlert
import config


def draw_mirror_frame(
    frame: np.ndarray,
    keypoints: Optional[np.ndarray],
    exercise_state: Optional[dict] = None,
    exercise_name: str = "",
    min_confidence: float = 0.3,
) -> np.ndarray:
    """
    Dessine le rendu miroir complet sur l'image.

    Args:
        frame: Image BGR de la webcam.
        keypoints: Array MoveNet (17, 3) ou None.
        exercise_state: État retourné par exercise.update().
        exercise_name: Nom de l'exercice en cours.
        min_confidence: Confiance minimum pour afficher un keypoint.

    Returns:
        Image BGR avec le squelette et les overlays dessinés.
    """
    # Miroir horizontal (effet miroir)
    display = cv2.flip(frame, 1)
    h, w = display.shape[:2]

    if keypoints is not None:
        # Dessiner le squelette
        display = _draw_skeleton(display, keypoints, h, w, min_confidence)

    if exercise_state:
        # Dessiner les overlays d'exercice
        display = _draw_exercise_overlay(display, exercise_state, exercise_name, h, w)

    # Toujours afficher le titre
    if exercise_name and not exercise_state:
        cv2.putText(
            display, exercise_name,
            (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2,
            (255, 255, 255), 2, cv2.LINE_AA,
        )

    return display


def _draw_skeleton(
    frame: np.ndarray,
    keypoints: np.ndarray,
    h: int,
    w: int,
    min_confidence: float,
) -> np.ndarray:
    """Dessine les segments et points du squelette."""
    # Comme l'image est en miroir, on inverse les coordonnées x
    mirrored_kps = keypoints.copy()
    mirrored_kps[:, 1] = 1.0 - mirrored_kps[:, 1]  # Miroir horizontal

    # Dessiner les segments
    for kp1, kp2 in SKELETON_CONNECTIONS:
        y1, x1, c1 = mirrored_kps[kp1.value]
        y2, x2, c2 = mirrored_kps[kp2.value]

        if c1 >= min_confidence and c2 >= min_confidence:
            pt1 = (int(x1 * w), int(y1 * h))
            pt2 = (int(x2 * w), int(y2 * h))
            color = get_segment_color(kp1, kp2)
            cv2.line(frame, pt1, pt2, color, 3, cv2.LINE_AA)

    # Dessiner les points
    for kp in Keypoint:
        y, x, conf = mirrored_kps[kp.value]
        if conf >= min_confidence:
            center = (int(x * w), int(y * h))
            # Point principal
            cv2.circle(frame, center, 6, (255, 255, 255), -1, cv2.LINE_AA)
            # Contour coloré
            cv2.circle(frame, center, 8, (0, 200, 255), 2, cv2.LINE_AA)

    return frame


def _draw_exercise_overlay(
    frame: np.ndarray,
    state: dict,
    exercise_name: str,
    h: int,
    w: int,
) -> np.ndarray:
    """Dessine les overlays de l'exercice (compteur, barre, feedback)."""

    # ─── Panneau supérieur : nom de l'exercice ─────────────────────────────
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 80), (30, 30, 50), -1)
    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

    cv2.putText(
        frame, exercise_name,
        (20, 55), cv2.FONT_HERSHEY_SIMPLEX, 1.5,
        (255, 255, 255), 3, cv2.LINE_AA,
    )

    # ─── Compteur de répétitions (coin supérieur droit) ────────────────────
    reps = state.get("reps", 0)
    target = state.get("target_reps", 10)
    rep_text = f"{reps}/{target}"

    # Fond du compteur
    text_size = cv2.getTextSize(rep_text, cv2.FONT_HERSHEY_SIMPLEX, 2.5, 4)[0]
    rx = w - text_size[0] - 40
    cv2.rectangle(frame, (rx - 20, 5), (w - 10, 75), (40, 40, 60), -1, cv2.LINE_AA)
    cv2.putText(
        frame, rep_text,
        (rx, 65), cv2.FONT_HERSHEY_SIMPLEX, 2.5,
        (100, 255, 100) if reps < target else (255, 215, 0),
        4, cv2.LINE_AA,
    )

    # ─── Barre de progression (bas de l'écran) ─────────────────────────────
    progress = state.get("progress_pct", 0.0)
    bar_y = h - 50
    bar_h = 30
    bar_w_max = w - 40

    # Fond de la barre
    cv2.rectangle(frame, (20, bar_y), (20 + bar_w_max, bar_y + bar_h),
                  (60, 60, 80), -1, cv2.LINE_AA)
    # Progression
    bar_w_current = int(bar_w_max * progress / 100)
    color = _progress_color(progress)
    cv2.rectangle(frame, (20, bar_y), (20 + bar_w_current, bar_y + bar_h),
                  color, -1, cv2.LINE_AA)
    # Texte pourcentage
    cv2.putText(
        frame, f"{int(progress)}%",
        (w // 2 - 30, bar_y + 24), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
        (255, 255, 255), 2, cv2.LINE_AA,
    )

    # ─── Angle actuel (coin gauche) ────────────────────────────────────────
    angle = state.get("angle")
    if angle is not None:
        angle_text = f"{int(angle)}°"
        cv2.putText(
            frame, angle_text,
            (30, h - 80), cv2.FONT_HERSHEY_SIMPLEX, 1.8,
            (200, 200, 255), 3, cv2.LINE_AA,
        )

    # ─── Message de feedback (centre) ──────────────────────────────────────
    message = state.get("feedback_message", "")
    if message:
        _draw_feedback_message(frame, message, state.get("feedback_color", "#FFFFFF"), h, w)

    # ─── Alertes de compensation (haut) ────────────────────────────────────
    compensations = state.get("compensations", [])
    if compensations:
        _draw_compensation_alerts(frame, compensations, h, w)

    return frame


def _draw_feedback_message(
    frame: np.ndarray,
    message: str,
    color_hex: str,
    h: int,
    w: int,
):
    """Affiche un message de feedback au centre de l'écran."""
    # Convertir la couleur hex en BGR
    color_bgr = _hex_to_bgr(color_hex)

    # Fond semi-transparent
    overlay = frame.copy()
    msg_y = h // 2 + 50
    cv2.rectangle(overlay, (40, msg_y - 50), (w - 40, msg_y + 20),
                  (20, 20, 30), -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

    # Texte du message
    font_scale = 1.2
    text_size = cv2.getTextSize(message, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 2)[0]
    text_x = (w - text_size[0]) // 2
    cv2.putText(
        frame, message,
        (text_x, msg_y), cv2.FONT_HERSHEY_SIMPLEX, font_scale,
        color_bgr, 2, cv2.LINE_AA,
    )


def _draw_compensation_alerts(
    frame: np.ndarray,
    alerts: List[CompensationAlert],
    h: int,
    w: int,
):
    """Affiche les alertes de compensation."""
    for i, alert in enumerate(alerts[:3]):  # Max 3 alertes affichées
        y = 100 + i * 40

        severity_colors = {
            "mild": (0, 165, 255),      # Orange
            "moderate": (0, 87, 255),    # Orange foncé
            "severe": (0, 0, 255),       # Rouge
        }
        color = severity_colors.get(alert.severity, (0, 165, 255))

        # Icône d'avertissement
        cv2.putText(
            frame, f"! {alert.message}",
            (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
            color, 2, cv2.LINE_AA,
        )


def _progress_color(pct: float) -> Tuple[int, int, int]:
    """Couleur de la barre de progression selon le pourcentage."""
    if pct < 30:
        return (80, 80, 200)    # Rouge
    elif pct < 70:
        return (0, 180, 255)    # Orange
    return (80, 200, 80)        # Vert


def _hex_to_bgr(hex_color: str) -> Tuple[int, int, int]:
    """Convertit une couleur hex (#RRGGBB) en BGR pour OpenCV."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return (255, 255, 255)
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return (b, g, r)


def draw_calibration_screen(
    frame: np.ndarray,
    keypoints: Optional[np.ndarray],
    countdown: int = 3,
    min_confidence: float = 0.3,
) -> np.ndarray:
    """
    Écran de calibration : montre le squelette et un compte à rebours.

    Demande au patient de se tenir en position neutre.
    """
    display = cv2.flip(frame, 1)
    h, w = display.shape[:2]

    if keypoints is not None:
        display = _draw_skeleton(display, keypoints, h, w, min_confidence)

    # Fond semi-transparent
    overlay = display.copy()
    cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.4, display, 0.6, 0, display)

    # Message principal
    msg = "Tenez-vous bien droit(e)"
    text_size = cv2.getTextSize(msg, cv2.FONT_HERSHEY_SIMPLEX, 1.5, 3)[0]
    text_x = (w - text_size[0]) // 2
    cv2.putText(
        display, msg,
        (text_x, h // 2 - 60), cv2.FONT_HERSHEY_SIMPLEX, 1.5,
        (255, 255, 255), 3, cv2.LINE_AA,
    )

    # Compte à rebours
    cv2.putText(
        display, str(countdown),
        (w // 2 - 30, h // 2 + 60), cv2.FONT_HERSHEY_SIMPLEX, 4.0,
        (0, 255, 255), 6, cv2.LINE_AA,
    )

    return display
